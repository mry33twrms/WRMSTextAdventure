import asyncio
import random
from mobs import mob, mob_dict
from rooms import room_dict
from npcs import npc_dict
from weapons import weapon_dict
from equipment import equipment_lookup, consumables_dict, materials_dict, quest_items_dict, keys_dict
from room_features import features_dict
from config import XP_BASE, XP_EXPONENT
import game_state
import database as db

DIR_ALIASES = {
    "north": "n", "south": "s", "east": "e",
    "west": "w", "up": "u", "down": "d",
}

DIR_NAMES = {
    "n": "north", "s": "south", "e": "east",
    "w": "west", "u": "up", "d": "down",
}

OPPOSITE_DIR = {
    "n": "south", "s": "north", "e": "west",
    "w": "east", "u": "below", "d": "above",
}

DIRECTIONS = set(DIR_NAMES)  # {"n", "s", "e", "w", "u", "d"}

GREETINGS = {"hi", "hello", "greetings", "hey", "howdy"}
FAREWELLS  = {"bye", "goodbye", "farewell", "cya", "later"}

COMBAT_ROUND_DURATION = 4   # seconds between auto-attack rounds
COMBAT_WARNING_DELAY  = 5   # seconds of warning before hostile mobs engage
LOCK_OPEN_DELAY       = 10  # seconds a key-unlocked door stays open


class Party:
    MAX_SIZE = 4

    def __init__(self, leader):
        self.leader  = leader   # Player object
        self.members = [leader] # ordered list of Player objects


class CombatSession:
    def __init__(self, room_name):
        self.room_name       = room_name
        self.players         = []   # Player objects currently in this combat
        self.damage_dealt    = {}   # player.name -> total damage dealt to mobs
        self.gold_pool       = 0    # gold accumulated from defeated mobs
        self.taunt_target    = None # Player object mobs will prefer to attack
        self.taunt_cooldowns = {}   # player.name -> rounds remaining on cooldown
        self.task            = None # asyncio.Task running the combat loop
        self.pending_join    = set() # player names with a warning task running


def _item_info(item_key):
    """Return the info dict for an item key across all lookup dicts, or None."""
    if item_key in weapon_dict:
        return weapon_dict[item_key]
    if item_key in equipment_lookup:
        return equipment_lookup[item_key]
    if item_key in consumables_dict:
        return consumables_dict[item_key]
    if item_key in materials_dict:
        return materials_dict[item_key]
    if item_key in quest_items_dict:
        return quest_items_dict[item_key]
    if item_key in keys_dict:
        return keys_dict[item_key]
    return None

def _item_display_name(item_key):
    info = _item_info(item_key)
    return info["name"] if info else item_key


def _find_item(query, item_keys):
    """Match a player's typed query against a list of item keys.

    Returns (matched_key, error_string). If matched_key is None and error_string
    is None, nothing was found. If error_string is set, there were multiple matches.
    """
    q = query.casefold().strip()
    # 1. Exact key match
    if q in item_keys:
        return q, None
    # 2. Exact display-name match
    for key in item_keys:
        info = _item_info(key)
        if info and info["name"].casefold() == q:
            return key, None
    # 3. Partial match against key or display name
    matches = []
    for key in item_keys:
        info = _item_info(key)
        display = info["name"].casefold() if info else key
        if q in key or q in display:
            matches.append(key)
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        names = ", ".join(_item_display_name(k) for k in matches)
        return None, f"'{query}' matches multiple items: {names}. Be more specific."
    return None, None


def _find_mob(query, mob_list):
    """Match a typed query against a list of live mob instances."""
    q = query.casefold().strip()
    # Exact key match
    exact = next((m for m in mob_list if m.name == q), None)
    if exact:
        return exact
    # Partial match against key or display name
    matches = [
        m for m in mob_list
        if q in m.name or q in mob_dict[m.name]["name"].casefold()
    ]
    return matches[0] if len(matches) == 1 else None


def _find_special_exit(query, room_name):
    """Fuzzy-match a query against non-directional exit names in a room.

    Returns the exit key string, or None if nothing matched (or ambiguous).
    """
    exits = room_dict[room_name].get("exits", {})
    specials = [k for k in exits if k not in DIRECTIONS]
    q = query.casefold().strip()
    # Exact match
    if q in specials:
        return q
    # Partial match
    matches = [k for k in specials if q in k]
    return matches[0] if len(matches) == 1 else None


def _find_room_keyword(query, room_name):
    """Return the matching keyword entry for a player's input, or None.

    Tries exact match first, then substring (longest keyword wins).
    """
    keywords = room_dict[room_name].get("keywords", {})
    if not keywords:
        return None
    q = query.casefold().strip()
    if q in keywords:
        return keywords[q]
    matches = [(kw, entry) for kw, entry in keywords.items() if kw in q]
    if matches:
        return max(matches, key=lambda x: len(x[0]))[1]
    return None


async def _handle_keyword_action(player, room_name, entry):
    """Execute a room keyword — plain string (description) or action dict."""
    if isinstance(entry, str):
        await player.send(entry)
        return

    action = entry.get("action")

    if action == "give_quest_item":
        item_key      = entry["item_key"]
        requires_quest = entry.get("requires_quest")

        if requires_quest and requires_quest not in player.quests:
            await player.send(entry.get("no_quest_text", entry.get("text", "Nothing happens.")))
            return
        if item_key in player.quest_items:
            await player.send(entry.get("already_text", "You've already done that."))
            return

        player.quest_items.append(item_key)
        await player.send(entry.get("text", f"You obtain the {_item_display_name(item_key)}."))
        await player.send(f"[Quest Item obtained: {_item_display_name(item_key)}]")
    else:
        await player.send(entry.get("text", "Nothing happens."))


def tier_weight(tier):
    """Higher tiers are exponentially rarer. Tier 1 = 1.0, tier 2 = 0.5, tier 3 = 0.25, etc."""
    return 1 / (2 ** (tier - 1))


def _item_tier(item_key):
    """Return the tier of an item key, defaulting to 1 if not set."""
    for lookup in (weapon_dict, equipment_lookup, consumables_dict, materials_dict):
        if item_key in lookup and "tier" in lookup[item_key]:
            return lookup[item_key]["tier"]
    return 1


def choose_loot(mob_name):
    """Roll loot_chance first; if it passes, pick one item weighted by tier. Returns None on no drop."""
    info = mob_dict[mob_name]
    if random.random() > info.get("loot_chance", 1.0):
        return None
    loot = info.get("loot", [])
    if not loot:
        return None
    weights = [tier_weight(_item_tier(item_key)) for item_key in loot]
    return random.choices(loot, weights=weights, k=1)[0]


def _conversable_npc(room_name):
    """Return the key of the first NPC in the room that has a convos dict, or None."""
    for npc_key in room_dict[room_name].get("npcs", []):
        if "convos" in npc_dict.get(npc_key, {}):
            return npc_key
    return None


async def _run_convo_action(player, npc_name, entry):
    """Execute the action attached to a convo entry dict."""
    action = entry.get("action")
    if action == "transport":
        cost = entry.get("cost", 0)
        if cost and player.gold < cost:
            await player.send(f"You need {cost} gold for that.")
            return
        if cost:
            player.gold -= cost
            await player.send(entry.get("cost_msg", f"You hand over {cost} gold."))
        dest = entry.get("destination")
        if dest and dest in room_dict:
            player.talking_to = None
            player.current_room = dest
            await display_room(dest, player)

    elif action == "give_item":
        item_key = entry["item_key"]
        if entry.get("once"):
            player.received_npc_items.add(item_key)
        if len(player.inventory) >= player.max_inventory:
            await player.send(f"{npc_name}: Your pack is full! Come back when you have room.")
            return
        player.inventory.append(item_key)
        await player.send(f"You receive: {_item_display_name(item_key)}.")

    elif action == "give_quest":
        quest_id = entry["quest_id"]
        player.quests[quest_id] = {
            "name":   entry["quest_name"],
            "desc":   entry["quest_desc"],
            "status": "active",
        }
        await player.send(f"[Quest Added: {entry['quest_name']}]")
        await player.send(f"  {entry['quest_desc']}")

    elif action == "complete_quest":
        quest_id     = entry["quest_id"]
        requires_key = entry.get("requires_quest_item")
        player.quests[quest_id]["status"] = "completed"
        if requires_key and requires_key in player.quest_items:
            player.quest_items.remove(requires_key)
        reward = entry.get("reward_item")
        if reward:
            if len(player.inventory) < player.max_inventory:
                player.inventory.append(reward)
                await player.send(f"You receive: {_item_display_name(reward)}!")
            else:
                room_dict[player.current_room].setdefault("items", []).append(reward)
                await player.send(f"Your pack is full! {_item_display_name(reward)} dropped to the ground.")
        await player.send(f"[Quest Completed: {player.quests[quest_id]['name']}]")


def _sell_price(item_key, shop):
    """Return the gold an NPC will pay for an item (buy_dict price, or 50% of base)."""
    if item_key in shop.get("buy_dict", {}):
        return shop["buy_dict"][item_key]
    info = _item_info(item_key)
    if info and "price" in info:
        return max(1, info["price"] // 2)
    return 0


async def _shop_list_sell(player, npc_name, shop):
    sell_dict = shop.get("sell_dict", {})
    if not sell_dict:
        await player.send(f"{npc_name}: I don't have anything for sale right now.")
        return
    lines = [f"{npc_name} sells:"]
    for key, price in sell_dict.items():
        lines.append(f"  {_item_display_name(key)} - {price} gold")
    lines.append("Say 'buy <item>' to purchase.")
    await player.send("\n".join(lines))


async def _shop_list_buy(player, npc_name, shop):
    buy_dict = shop.get("buy_dict", {})
    lines = [f"{npc_name} will buy most items at half their value."]
    if buy_dict:
        lines.append("Set prices for:")
        for key, price in buy_dict.items():
            lines.append(f"  {_item_display_name(key)} - {price} gold")
    lines.append("Say 'sell <item>' to sell something from your inventory.")
    await player.send("\n".join(lines))


async def _shop_buy_item(player, npc_name, shop, item_query):
    sell_dict = shop.get("sell_dict", {})
    if not sell_dict:
        await player.send(f"{npc_name}: I don't have anything for sale.")
        return
    item_key, err = _find_item(item_query, list(sell_dict.keys()))
    if err:
        await player.send(f"{npc_name}: {err}")
        return
    if item_key is None:
        await player.send(f"{npc_name}: I'm afraid I don't carry '{item_query}'.")
        return
    price = sell_dict[item_key]
    name = _item_display_name(item_key)
    player.pending_transaction = {"type": "buy", "item_key": item_key, "price": price}
    await player.send(f"{npc_name}: That'll be {price} gold for the {name}. Say 'yes' to buy or 'no' to cancel.")


async def _shop_sell_item(player, npc_name, shop, item_query):
    item_key, err = _find_item(item_query, player.inventory)
    if err:
        await player.send(f"{npc_name}: {err}")
        return
    if item_key is None:
        await player.send(f"{npc_name}: You don't seem to have that.")
        return
    if item_key in player.equipped_items.values():
        await player.send(f"{npc_name}: You'll need to unequip the {_item_display_name(item_key)} before selling it.")
        return
    price = _sell_price(item_key, shop)
    if price == 0:
        await player.send(f"{npc_name}: Sorry, I'm not interested in that.")
        return
    name = _item_display_name(item_key)
    player.pending_transaction = {"type": "sell", "item_key": item_key, "price": price}
    await player.send(f"{npc_name}: I'll give you {price} gold for your {name}. Say 'yes' to sell or 'no' to cancel.")


async def _complete_transaction(player, npc_name, pt):
    if pt["type"] == "buy":
        if player.gold < pt["price"]:
            await player.send(f"{npc_name}: You only have {player.gold} gold — you need {pt['price']} gold for that.")
        elif len(player.inventory) >= player.max_inventory:
            await player.send(f"{npc_name}: Your pack is full! Make some room first.")
        else:
            player.gold -= pt["price"]
            player.inventory.append(pt["item_key"])
            name = _item_display_name(pt["item_key"])
            await player.send(f"{npc_name}: Enjoy your {name}! (Gold: {player.gold})")
    elif pt["type"] == "sell":
        if pt["item_key"] not in player.inventory:
            await player.send(f"{npc_name}: It looks like you no longer have that.")
        else:
            player.inventory.remove(pt["item_key"])
            player.gold += pt["price"]
            name = _item_display_name(pt["item_key"])
            await player.send(f"{npc_name}: Pleasure doing business! (Gold: {player.gold})")
    player.pending_transaction = None


async def handle_npc_convo(player, text, npc_key):
    """Parse player text against an NPC's convo keywords and respond."""
    npc = npc_dict[npc_key]
    convos = npc.get("convos", {})
    npc_name = npc["name"]
    shop = npc.get("shop")
    lower_text = text.casefold()
    words = lower_text.split()

    # Pending transaction: yes / no / remind
    if player.pending_transaction:
        if any(w in {"yes", "yeah", "yep"} for w in words):
            await _complete_transaction(player, npc_name, player.pending_transaction)
        elif any(w in {"no", "nope", "cancel"} for w in words):
            player.pending_transaction = None
            await player.send(f"{npc_name}: No problem, just let me know if you change your mind!")
        else:
            await player.send(f"{npc_name}: Say 'yes' to confirm or 'no' to cancel.")
        return

    # Farewell ends the conversation
    if any(w in FAREWELLS for w in words):
        player.talking_to = None
        entry = convos.get("farewell", "Goodbye!")
        resp = entry["text"] if isinstance(entry, dict) else entry
        await player.send(f"{npc_name}: {resp}")
        return

    # Shop interactions (only if NPC has a shop)
    if shop:
        idx = lower_text.find("buy ")
        if idx != -1:
            await _shop_buy_item(player, npc_name, shop, lower_text[idx + 4:].strip())
            return

        idx = lower_text.find("sell ")
        if idx != -1:
            await _shop_sell_item(player, npc_name, shop, lower_text[idx + 5:].strip())
            return

        if "buy" in words or "for sale" in lower_text or "what do you have" in lower_text:
            await _shop_list_sell(player, npc_name, shop)
            return

        if "sell" in words:
            await _shop_list_buy(player, npc_name, shop)
            return

    # Normal keyword matching
    matched_key = next(
        (key for key in convos
         if key not in ("greeting", "farewell", "default") and key in lower_text),
        None
    )
    entry = convos.get(matched_key) if matched_key else convos.get("default", "...")

    # Pre-checks for actions that can short-circuit before sending NPC text
    if isinstance(entry, dict):
        action = entry.get("action")
        if action == "give_item" and entry.get("once"):
            if entry["item_key"] in player.received_npc_items:
                await player.send(f"{npc_name}: {entry.get('once_msg', 'Sorry, I have no more of those.')}")
                return
        elif action == "give_quest":
            if entry["quest_id"] in player.quests:
                await player.send(f"{npc_name}: {entry.get('already_given_msg', 'Any progress on that?')}")
                return
        elif action == "complete_quest":
            if entry["quest_id"] not in player.quests:
                msg = entry.get("no_quest_msg", "I'm not sure what you mean.")
                await player.send(f"{npc_name}: {msg}")
                return
            requires_key = entry.get("requires_quest_item")
            if requires_key and requires_key not in player.quest_items:
                msg = entry.get("no_item_msg", "You haven't done that yet.")
                await player.send(f"{npc_name}: {msg}")
                return

    resp = entry["text"] if isinstance(entry, dict) else entry
    await player.send(f"{npc_name}: {resp}")

    if isinstance(entry, dict) and "action" in entry:
        await _run_convo_action(player, npc_name, entry)


async def broadcast_room(room_name, msg, exclude=None):
    for p in game_state.players.values():
        if p.current_room == room_name and p is not exclude:
            await p.send(msg)


def _get_room_mobs(room_name):
    """Return the live mob list for a room, initialising it from room_dict if needed."""
    if room_name not in game_state.room_mobs:
        game_state.room_mobs[room_name] = [
            mob(key, mob_dict[key])
            for key in room_dict[room_name].get("mobs", [])
            if key in mob_dict
        ]
    return game_state.room_mobs[room_name]


async def display_room(room_name, player):
    room = room_dict[room_name]
    lines = [room["name"], "", room["desc"], ""]

    visible = []
    for npc_key in room.get("npcs", []):
        npc = npc_dict.get(npc_key)
        if npc:
            visible.append(f"- {npc['name']}: {npc['desc']}")
    for m in _get_room_mobs(room_name):
        info = mob_dict[m.name]
        visible.append(f"- {info['name']}: {info['desc']}")
    for p in game_state.players.values():
        if p.current_room == room_name and p is not player:
            visible.append(f"- {p.name} is here.")
    for item_key in room.get("items", []):
        visible.append(f"- {_item_display_name(item_key)} is on the ground.")
    if visible:
        lines.append("You see:")
        lines.extend(visible)
        lines.append("")

    cardinal = [DIR_NAMES[ex].capitalize() for ex in room.get("exits", {}) if ex in DIR_NAMES]
    special  = [ex.capitalize()           for ex in room.get("exits", {}) if ex not in DIRECTIONS]

    if cardinal:
        lines.append("Exits: " + ", ".join(cardinal))
    if special:
        lines.append("Special exits: " + ", ".join(special))

    room_features = [
        features_dict[f]["name"]
        for f in room.get("features", [])
        if f in features_dict
    ]
    if room_features:
        lines.append("Features: " + ", ".join(room_features))

    await player.send("\n".join(lines))


async def cmd_look(player, args, gs):
    if not args:
        await display_room(player.current_room, player)
        return
    target = args.casefold()
    for npc_key in room_dict[player.current_room].get("npcs", []):
        if target in npc_key.casefold() or target in npc_dict[npc_key]["name"].casefold():
            await player.send(npc_dict[npc_key]["desc"])
            return
    for p in gs.players.values():
        if p.current_room == player.current_room and target in p.name.casefold():
            await player.send(f"{p.name} is a player adventuring through WRMS.")
            return
    for m in _get_room_mobs(player.current_room):
        if target in m.name.casefold():
            await player.send(mob_dict[m.name]["desc"])
            return
    await player.send(f"You don't see '{args}' here.")


async def cmd_quit(player, _args, _gs):
    await player.send("Goodbye!")
    player.quitting = True


async def cmd_help(player, _args, _gs):
    lines = [f"{key} - {info['desc']}" for key, info in commands_dict.items()]
    await player.send("\n".join(lines))


async def cmd_go(player, args, gs):
    if not args:
        exits = room_dict[player.current_room].get("exits", {})
        specials = [k for k in exits if k not in DIRECTIONS]
        if specials:
            await player.send("Go where? Special exits here: " + ", ".join(specials))
        else:
            await player.send("There are no special exits here. Use n/s/e/w/u/d to move.")
        return
    exit_key = _find_special_exit(args, player.current_room)
    if exit_key is None:
        await player.send(f"No special exit matching '{args}' here.")
        return
    await cmd_move(player, exit_key, gs)


async def cmd_say(player, args, _gs):
    if not args:
        await player.send("Say what?")
        return

    words = args.casefold().split()

    # Mid-conversation: route through NPC convo handler
    if player.talking_to:
        await player.send(f'You say: "{args}"')
        await broadcast_room(player.current_room, f'{player.name} says: "{args}"', exclude=player)
        if player.talking_to in room_dict[player.current_room].get("npcs", []):
            await handle_npc_convo(player, args, player.talking_to)
        else:
            player.talking_to = None
            await player.send("They don't seem to be here anymore.")
        return

    # Greeting in a room with a conversable NPC → initiate conversation
    if any(w in GREETINGS for w in words):
        npc_key = _conversable_npc(player.current_room)
        if npc_key:
            player.talking_to = npc_key
            npc_name = npc_dict[npc_key]["name"]
            greeting = npc_dict[npc_key]["convos"].get("greeting", "Hello.")
            await player.send(f'You say: "{args}"')
            await broadcast_room(player.current_room, f'{player.name} says: "{args}"', exclude=player)
            resp = greeting["text"] if isinstance(greeting, dict) else greeting
            await player.send(f"{npc_name}: {resp}")
            return

    # Normal say
    await player.send(f'You say: "{args}"')
    await broadcast_room(player.current_room, f'{player.name} says: "{args}"', exclude=player)


async def cmd_list_rooms(player, args, gs):
    lines = ["Rooms:"] + [f"  {key} - {room['name']}" for key, room in room_dict.items()]
    await player.send("\n".join(lines))


async def cmd_change_room(player, args, gs):
    if player.role != "admin":
        await player.send("You don't have permission to use that command.")
        return
    if not args:
        await player.send("Usage: change room <room name>")
        return
    if args not in room_dict:
        await player.send(f"Room '{args}' not found.")
        return
    old_room = player.current_room
    player.talking_to         = None
    player.pending_transaction = None

    # Teleporting clears follow state — followers are not dragged
    _follow_clear(player)
    for follower_name in list(player.followers):
        follower = game_state.players.get(follower_name)
        if follower:
            follower.following = None
            await follower.send(f"{player.name} teleports away. You are no longer following them.")
    player.followers.clear()

    await broadcast_room(old_room, f"{player.name} vanishes into thin air.", exclude=player)
    player.current_room = args
    await broadcast_room(args, f"{player.name} appears out of thin air.", exclude=player)
    await display_room(args, player)
    # Hostile encounter check (same as cmd_move)
    live_mobs = _get_room_mobs(args)
    if live_mobs and _is_hostile_encounter(args):
        session = game_state.combat_sessions.get(args)
        if session:
            if player.name not in session.pending_join:
                session.pending_join.add(player.name)
                asyncio.create_task(_warn_and_join(player, session))
        else:
            session = CombatSession(args)
            game_state.combat_sessions[args] = session
            asyncio.create_task(_trigger_hostile_warning(args))


async def cmd_bonk(player, args, gs):
    if not args:
        await player.send("Usage: bonk <mob name>")
        return
    live_mobs = _get_room_mobs(player.current_room)
    target = _find_mob(args, live_mobs)
    if target:
        live_mobs.remove(target)
        await player.send(f"You bonk the {args} on the head. It wanders off confused.")
        await broadcast_room(player.current_room, f"{player.name} bonks the {args} on the head!", exclude=player)
    else:
        await player.send(f"There is no '{args}' here to bonk.")


async def cmd_who(player, args, gs):
    if not gs.players:
        await player.send("No one is connected.")
        return
    lines = ["Players online:"]
    for p in gs.players.values():
        marker = " (you)" if p is player else ""
        lines.append(f"  {p.name} - {room_dict[p.current_room]['name']}{marker}")
    await player.send("\n".join(lines))


async def cmd_move(player, direction, gs):
    if player.in_combat:
        await player.send("You can't move while in combat! Use 'flee' or 'run' to escape.")
        return

    room = room_dict[player.current_room]
    exits = room.get("exits", {})
    if direction not in exits:
        await player.send("You can't go that way.")
        return

    new_room_key = exits[direction]
    if new_room_key not in room_dict:
        await player.send("That passage leads nowhere. (Missing room)")
        return

    # Guarded exit: live mobs must be defeated before using this exit
    guarded = room.get("guarded", [])
    if direction in guarded:
        live_mobs = _get_room_mobs(player.current_room)
        if live_mobs:
            mob_names = " and ".join(dict.fromkeys(mob_dict[m.name]["name"] for m in live_mobs))
            plural = len(live_mobs) > 1
            await player.send(
                f"The {mob_names} block{'s' if not plural else ''} your path! "
                f"Defeat {'them' if plural else 'it'} first."
            )
            return

    # Locked exit: requires key item; unlocks for LOCK_OPEN_DELAY seconds
    locked_dir = room.get("locked")
    if locked_dir == direction and (player.current_room, direction) not in game_state.unlocked_exits:
        required_key = room.get("requires_key")
        if required_key not in player.inventory:
            key_name = _item_display_name(required_key) if required_key else "a key"
            dir_label = DIR_NAMES.get(direction, direction)
            await player.send(f"The door to the {dir_label} is locked. You need the {key_name} to open it.")
            return
        # Player has the key — unlock and schedule re-lock
        game_state.unlocked_exits.add((player.current_room, direction))
        dir_label = DIR_NAMES.get(direction, direction)
        await broadcast_room(
            player.current_room,
            f"{player.name} unlocks the door to the {dir_label}! It will lock again in {LOCK_OPEN_DELAY} seconds."
        )
        asyncio.create_task(_relock_exit(player.current_room, direction))

    old_room = player.current_room
    player.talking_to = None
    player.pending_transaction = None

    # Moving clears your own follow (you chose a direction)
    _follow_clear(player)

    if direction in DIR_NAMES:
        await broadcast_room(old_room, f"{player.name} leaves to the {DIR_NAMES[direction]}.", exclude=player)
        await broadcast_room(new_room_key, f"{player.name} arrives from the {OPPOSITE_DIR[direction]}.", exclude=player)

    player.current_room = new_room_key
    await display_room(new_room_key, player)

    # Check for hostile encounter in the new room
    live_mobs = _get_room_mobs(new_room_key)
    if live_mobs and _is_hostile_encounter(new_room_key):
        session = game_state.combat_sessions.get(new_room_key)
        if session:
            if player.name not in session.pending_join:
                session.pending_join.add(player.name)
                asyncio.create_task(_warn_and_join(player, session))
        else:
            session = CombatSession(new_room_key)
            game_state.combat_sessions[new_room_key] = session
            asyncio.create_task(_trigger_hostile_warning(new_room_key))

    # Drag followers who were in old_room
    for follower_name in list(player.followers):
        follower = game_state.players.get(follower_name)
        if not follower or follower.current_room != old_room or follower.in_combat:
            continue
        follower.talking_to = None
        follower.pending_transaction = None
        if direction in DIR_NAMES:
            await broadcast_room(old_room, f"{follower.name} follows {player.name} to the {DIR_NAMES[direction]}.", exclude=follower)
            await broadcast_room(new_room_key, f"{follower.name} arrives following {player.name}.", exclude=follower)
        follower.current_room = new_room_key
        await display_room(new_room_key, follower)
        follower_mobs = _get_room_mobs(new_room_key)
        if follower_mobs and _is_hostile_encounter(new_room_key):
            fsession = game_state.combat_sessions.get(new_room_key)
            if fsession:
                if follower.name not in fsession.pending_join:
                    fsession.pending_join.add(follower.name)
                    asyncio.create_task(_warn_and_join(follower, fsession))
            else:
                fsession = CombatSession(new_room_key)
                game_state.combat_sessions[new_room_key] = fsession
                asyncio.create_task(_trigger_hostile_warning(new_room_key))

    # Auto-follow: wire party members to follow when in the same room as leader
    if player.party:
        party = player.party
        if party.leader is not player and party.leader.current_room == new_room_key:
            if player.following != party.leader.name:
                _follow_clear(player)
                player.following = party.leader.name
                party.leader.followers.add(player.name)
                await player.send(f"You are now following {party.leader.name} (party leader).")
                await party.leader.send(f"{player.name} is now following you.")
        elif party.leader is player:
            for m in party.members:
                if m is player or m.current_room != new_room_key:
                    continue
                if m.following != player.name:
                    _follow_clear(m)
                    m.following = player.name
                    player.followers.add(m.name)
                    await m.send(f"You are now following {player.name} (party leader).")
                    await player.send(f"{m.name} is now following you.")

async def _relock_exit(room_name, direction):
    await asyncio.sleep(LOCK_OPEN_DELAY)
    game_state.unlocked_exits.discard((room_name, direction))
    dir_label = DIR_NAMES.get(direction, direction)
    await broadcast_room(room_name, f"The door to the {dir_label} locks again with a click.")


async def _respawn_mob(room_name, mob_key, delay):
    await asyncio.sleep(delay)
    info = mob_dict[mob_key]
    new_mob = mob(mob_key, info)
    game_state.room_mobs.setdefault(room_name, []).append(new_mob)
    await broadcast_room(room_name, f"A {info['name']} has appeared!")
    # If the respawned mob is hostile and players are present, trigger combat
    if info.get("hostile", False) and room_name not in game_state.combat_sessions:
        players_here = [p for p in game_state.players.values() if p.current_room == room_name]
        if players_here:
            session = CombatSession(room_name)
            game_state.combat_sessions[room_name] = session
            asyncio.create_task(_trigger_hostile_warning(room_name))


def _do_combat_hit(attacker_attack, attacker_crit_chance, attacker_crit_power,
                   target_evasion, target_defense):
    """Return (damage, evaded, is_crit). damage=0 when evaded."""
    if random.randint(1, 100) <= target_evasion:
        return 0, True, False
    damage = max(1, attacker_attack - target_defense)
    is_crit = random.randint(1, 100) <= attacker_crit_chance
    if is_crit:
        damage = int(damage * (1 + attacker_crit_power / 100))
    return damage, False, is_crit


async def player_death(player, room_name, cause=None):
    """Restore HP, clear state, remove from combat, broadcast defeat, teleport."""
    _exit_combat(player)
    player.hp = player.max_hp
    player.talking_to = None
    player.pending_transaction = None
    cause_str = f" by the {cause}" if cause else ""
    await broadcast_room(room_name, f"{player.name} was defeated{cause_str}!", exclude=player)
    player.current_room = player.respawn_point
    respawn_name = room_dict[player.respawn_point]["name"]
    await player.send(f"You have been defeated{cause_str} and wake up at the {respawn_name}.")
    await display_room(player.respawn_point, player)


# ── Combat system ─────────────────────────────────────────────────────────────

def _is_hostile_encounter(room_name):
    """True if the room itself or any live mob in it is flagged hostile."""
    if room_dict[room_name].get("hostile", False):
        return True
    return any(mob_dict[m.name].get("hostile", False) for m in _get_room_mobs(room_name))


def _exit_combat(player):
    """Remove a player from their combat session and clear their combat state."""
    room_name = player.combat_room or player.current_room
    session = game_state.combat_sessions.get(room_name)
    if session:
        if player in session.players:
            session.players.remove(player)
        if session.taunt_target is player:
            session.taunt_target = None
        session.pending_join.discard(player.name)
    player.in_combat   = False
    player.combat_room = None


async def _join_combat(player, session):
    if player not in session.players:
        session.players.append(player)
    player.in_combat   = True
    player.combat_room = session.room_name


async def _end_combat(session):
    room_name  = session.room_name
    live_mobs  = _get_room_mobs(room_name)
    survivors  = [p for p in session.players if p.current_room == room_name]

    if not live_mobs and session.gold_pool > 0 and survivors:
        total_dmg = sum(session.damage_dealt.values()) or 1
        await broadcast_room(room_name,
            f"Combat over! Distributing {session.gold_pool} gold by damage dealt.")
        for p in survivors:
            share = round(session.gold_pool * session.damage_dealt.get(p.name, 0) / total_dmg)
            if share:
                p.gold += share
                pct = int(session.damage_dealt.get(p.name, 0) * 100 // total_dmg)
                await p.send(f"You receive {share} gold ({pct}% of damage dealt).")
    elif not live_mobs:
        await broadcast_room(room_name, "Combat has ended.")
    else:
        await broadcast_room(room_name, "The last combatant flees — the fighting stops.")

    for p in session.players:
        p.in_combat   = False
        p.combat_room = None
    game_state.combat_sessions.pop(room_name, None)


async def _execute_round(session):
    room_name = session.room_name
    live_mobs = _get_room_mobs(room_name)
    present   = [p for p in session.players
                 if p.current_room == room_name and p.hp > 0]

    if not live_mobs or not present:
        return

    # Decrement taunt cooldowns and notify on refresh
    for p in present:
        if session.taunt_cooldowns.get(p.name, 0) > 0:
            session.taunt_cooldowns[p.name] -= 1
            if session.taunt_cooldowns[p.name] == 0:
                await p.send("Your taunt has refreshed.")

    # Sort all participants by agility descending
    participants = (
        [("player", p) for p in present] +
        [("mob",    m) for m in list(live_mobs)]
    )
    participants.sort(key=lambda x: x[1].agility, reverse=True)

    for kind, entity in participants:

        if kind == "mob":
            if entity not in _get_room_mobs(room_name):
                continue  # already killed earlier this round
            alive_players = [p for p in session.players
                             if p.current_room == room_name and p.hp > 0]
            if not alive_players:
                break

            if session.taunt_target and session.taunt_target in alive_players:
                target_p = session.taunt_target
            else:
                target_p = random.choice(alive_players)

            mob_display = mob_dict[entity.name]["name"]
            dmg, evaded, crit = _do_combat_hit(
                entity.attack, entity.crit_chance, entity.crit_power,
                target_p.evasion, target_p.defense,
            )
            if evaded:
                await broadcast_room(room_name,
                    f"The {mob_display} swings at {target_p.name} but misses!")
            else:
                crit_str = " Critical hit!" if crit else ""
                target_p.hp -= dmg
                await broadcast_room(room_name,
                    f"The {mob_display} hits {target_p.name} for {dmg} damage!{crit_str} "
                    f"({target_p.hp}/{target_p.max_hp} HP)")
                if target_p.hp <= 0:
                    await player_death(target_p, room_name, cause=mob_display)

        else:  # player
            if entity.hp <= 0 or entity.current_room != room_name:
                continue
            current_mobs = _get_room_mobs(room_name)
            if not current_mobs:
                break

            target_m    = random.choice(current_mobs)
            mob_info    = mob_dict[target_m.name]
            mob_display = mob_info["name"]
            dmg, evaded, crit = _do_combat_hit(
                entity.attack, entity.crit_chance, entity.crit_power,
                target_m.evasion, target_m.defense,
            )
            if evaded:
                await broadcast_room(room_name,
                    f"{entity.name} swings at the {mob_display} but misses!")
            else:
                died = target_m.take_damage(dmg)
                crit_str = " Critical hit!" if crit else ""
                session.damage_dealt[entity.name] = (
                    session.damage_dealt.get(entity.name, 0) + dmg
                )
                await broadcast_room(room_name,
                    f"{entity.name} hits the {mob_display} for {dmg} damage!{crit_str} "
                    f"({target_m.hp}/{target_m.max_hp} HP)")
                if died:
                    _get_room_mobs(room_name).remove(target_m)
                    gold = mob_info.get("gold", 0)
                    session.gold_pool += gold
                    defeat_msg = f"The {mob_display} has been defeated!"
                    if gold:
                        defeat_msg += f" ({gold} gold added to the pool)"
                    loot_key = choose_loot(target_m.name)
                    if loot_key:
                        room_dict[room_name].setdefault("items", []).append(loot_key)
                        defeat_msg += f" The {mob_display} drops {_item_display_name(loot_key)}."
                    await broadcast_room(room_name, defeat_msg)
                    await gain_xp(entity, mob_info.get("xp", 0))
                    asyncio.create_task(_respawn_mob(
                        room_name, target_m.name, mob_info.get("respawn_time", 60)
                    ))


async def _run_combat_loop(session):
    try:
        while True:
            await asyncio.sleep(COMBAT_ROUND_DURATION)
            live_mobs = _get_room_mobs(session.room_name)
            present   = [p for p in session.players
                         if p.current_room == session.room_name and p.hp > 0]
            if not live_mobs or not present:
                break
            await _execute_round(session)
    except asyncio.CancelledError:
        pass
    finally:
        if session.room_name in game_state.combat_sessions:
            await _end_combat(session)


async def _warn_and_join(player, session):
    """Personal 5-second warning for a player who enters a room mid-combat.

    The player can move back out during the countdown. If they're still present
    when it expires they are added to the active combat session.
    """
    room_name = session.room_name
    live_mobs = _get_room_mobs(room_name)
    if not live_mobs:
        session.pending_join.discard(player.name)
        return
    mob_names = " and ".join(dict.fromkeys(mob_dict[m.name]["name"] for m in live_mobs))
    await player.send(
        f"The {mob_names} turn{'s' if len(live_mobs) == 1 else ''} on you! "
        f"Combat starts in {COMBAT_WARNING_DELAY} seconds! Move back to escape!"
    )
    await asyncio.sleep(COMBAT_WARNING_DELAY)
    session.pending_join.discard(player.name)
    if (player.current_room == room_name
            and not player.in_combat
            and room_name in game_state.combat_sessions):
        await _join_combat(player, session)
        await player.send("You are now in combat!")


async def _trigger_hostile_warning(room_name):
    """5-second countdown then pull everyone in the room into combat."""
    session = game_state.combat_sessions.get(room_name)
    live_mobs = _get_room_mobs(room_name)
    if not live_mobs or not session:
        game_state.combat_sessions.pop(room_name, None)
        return
    # Mark all players already in the room as pending so the check loop
    # doesn't issue a second _warn_and_join for them.
    for p in list(game_state.players.values()):
        if p.current_room == room_name:
            session.pending_join.add(p.name)
    mob_names = " and ".join(dict.fromkeys(mob_dict[m.name]["name"] for m in live_mobs))
    await broadcast_room(room_name,
        f"The {mob_names} look{'s' if len(live_mobs) == 1 else ''} hostile! "
        f"Combat begins in {COMBAT_WARNING_DELAY} seconds! Type 'flee' to escape!")
    await asyncio.sleep(COMBAT_WARNING_DELAY)

    session = game_state.combat_sessions.get(room_name)
    if not session:
        return
    live_mobs = _get_room_mobs(room_name)
    if not live_mobs:
        game_state.combat_sessions.pop(room_name, None)
        return
    session.pending_join.clear()
    for p in list(game_state.players.values()):
        if p.current_room == room_name:
            await _join_combat(p, session)
    if not session.players:
        game_state.combat_sessions.pop(room_name, None)
        return
    await broadcast_room(room_name, "Combat has begun!")
    session.task = asyncio.create_task(_run_combat_loop(session))


async def _hostile_check_loop():
    """Background task: every 3 s scan all visited rooms for hostile encounters.

    Two jobs:
    1. Start new combat sessions for hostile rooms with players but no session.
    2. Pull any players already in a combat room into the active session.

    New mobs (summons, respawns) landing in an active-session room are picked up
    automatically by _execute_round's dynamic _get_room_mobs() call — no extra
    tracking needed here.
    """
    while True:
        await asyncio.sleep(3)

        # Pull any out-of-combat players into existing sessions (with personal warning)
        for room_name, session in list(game_state.combat_sessions.items()):
            for p in list(game_state.players.values()):
                if (p.current_room == room_name
                        and not p.in_combat
                        and p.name not in session.pending_join):
                    session.pending_join.add(p.name)
                    asyncio.create_task(_warn_and_join(p, session))

        # Start new hostile encounters for rooms with no session yet
        for room_name in list(game_state.room_mobs):
            if room_name in game_state.combat_sessions:
                continue
            live_mobs = [m for m in game_state.room_mobs[room_name] if m.hp > 0]
            if not live_mobs:
                continue
            is_hostile = (
                room_dict[room_name].get("hostile", False) or
                any(mob_dict[m.name].get("hostile", False) for m in live_mobs)
            )
            if not is_hostile:
                continue
            players_here = [p for p in game_state.players.values()
                            if p.current_room == room_name and not p.in_combat]
            if not players_here:
                continue
            session = CombatSession(room_name)
            game_state.combat_sessions[room_name] = session
            asyncio.create_task(_trigger_hostile_warning(room_name))


# ── End combat system ──────────────────────────────────────────────────────────

def _xp_to_next_level(level):
    return int(XP_BASE * level ** XP_EXPONENT)


async def gain_xp(player, amount):
    if amount <= 0:
        return
    player.xp += amount
    await player.send(f"You gain {amount} XP. ({player.xp}/{_xp_to_next_level(player.level)})")
    while player.xp >= _xp_to_next_level(player.level):
        player.xp -= _xp_to_next_level(player.level)
        player.level += 1
        player.stat_points += 1
        player.recalculate_stats()
        await player.send(
            f"*** Level up! You are now level {player.level}. "
            f"You have {player.stat_points} unspent stat point(s). "
            f"Use 'character <stat>' to assign them. ***"
        )


STAT_NAMES = {"strength", "agility", "intelligence", "vitality"}


async def cmd_character(player, args, _gs):
    if not args:
        nxt = _xp_to_next_level(player.level)
        lines = [
            f"--- {player.name} ---",
            f"Level: {player.level}  XP: {player.xp}/{nxt}  Unspent points: {player.stat_points}",
            "",
            "Primary Stats:",
            f"  Strength:     {player.strength}  (ATK +{player.strength}, Crit Power +{player.strength}%)",
            f"  Agility:      {player.agility}  (Evasion +{player.agility}%, Crit Chance +{player.agility}%)",
            f"  Intelligence: {player.intelligence}  (Magic DMG +{player.intelligence}, Magic Res +{player.intelligence * 3})",
            f"  Vitality:     {player.vitality}  (Max HP +{player.vitality * 5})",
            "",
            "Derived Stats:",
            f"  HP: {player.hp}/{player.max_hp}  ATK: {player.attack}  DEF: {player.defense}",
            f"  Crit Chance: {player.crit_chance}%  Crit Power: {player.crit_power}%  Evasion: {player.evasion}%",
            f"  Magic DMG: {player.magic_damage}  Magic Resist: {player.magic_resist}",
            f"  Fire Resist: {player.fire_resist}  Ice Resist: {player.ice_resist}  Shock Resist: {player.shock_resist}",
        ]
        if player.stat_points:
            lines.append("")
            lines.append("Type 'character <stat>' to spend a point (e.g. 'character strength').")
        await player.send("\n".join(lines))
        return

    stat = args.casefold().strip()
    if stat not in STAT_NAMES:
        await player.send(f"Unknown stat '{args}'. Choose: strength, agility, intelligence, vitality.")
        return
    if player.stat_points <= 0:
        await player.send("You have no unspent stat points.")
        return
    player.stat_points -= 1
    setattr(player, stat, getattr(player, stat) + 1)
    player.recalculate_stats()
    await player.send(f"{stat.capitalize()} is now {getattr(player, stat)}. ({player.stat_points} point(s) remaining)")


async def cmd_attack(player, args, gs):
    if not args:
        await player.send("Usage: attack <mob name>")
        return

    room_name  = player.current_room
    lower_args = args.casefold()

    # Friendly fire: NPCs
    for npc_key in room_dict[room_name].get("npcs", []):
        npc = npc_dict[npc_key]
        if lower_args in npc_key.casefold() or lower_args in npc["name"].casefold():
            await player.send(f"You can't attack {npc['name']}. They're on your side!")
            return
    # Friendly fire: other players
    for p in game_state.players.values():
        if p is not player and p.current_room == room_name and lower_args in p.name.casefold():
            await player.send(f"You can't attack {p.name}. They're on your side!")
            return

    live_mobs = _get_room_mobs(room_name)
    target = _find_mob(args, live_mobs)
    if target is None:
        await player.send(f"There is no '{args}' here to attack.")
        return

    if player.in_combat:
        await player.send("You're already in combat! Use 'flee' or 'run' to escape.")
        return

    session = game_state.combat_sessions.get(room_name)
    if session:
        # Combat already running — join it
        await _join_combat(player, session)
        await player.send("You join the ongoing combat!")
    else:
        # Player-initiated: start immediately, no warning
        session = CombatSession(room_name)
        game_state.combat_sessions[room_name] = session
        for p in list(game_state.players.values()):
            if p.current_room == room_name:
                await _join_combat(p, session)
        mob_display = mob_dict[target.name]["name"]
        await broadcast_room(room_name,
            f"Combat begins! {player.name} attacks the {mob_display}!")
        session.task = asyncio.create_task(_run_combat_loop(session))

async def cmd_use(player, args, _gs):
    if not args:
        await player.send("Usage: use <item name>")
        return
    item_key, err = _find_item(args, player.inventory)
    if err:
        await player.send(err); return
    if item_key is None:
        await player.send(f"You don't have '{args}'."); return
    if item_key not in consumables_dict:
        await player.send(f"'{args}' can't be used that way. Try 'equip' instead.")
        return
    info = consumables_dict[item_key]
    if "heal" in info:
        healed = min(info["heal"], player.max_hp - player.hp)
        player.hp += healed
        await player.send(f"You use the {info['name']} and restore {healed} HP. ({player.hp}/{player.max_hp} HP)")
    elif info.get("name") == "Recall Scroll":
        player.talking_to = None
        player.pending_transaction = None
        player.current_room = player.respawn_point
        respawn_name = room_dict[player.respawn_point]["name"]
        await player.send(f"The scroll glows and you are whisked to {respawn_name}.")
        await display_room(player.respawn_point, player)
    else:
        await player.send(f"You use the {info['name']}. (effect not yet implemented)")
    player.inventory.remove(item_key)


async def cmd_get(player, args, _gs):
    if not args:
        await player.send("Usage: get <item name>")
        return
    items = room_dict[player.current_room].get("items", [])
    item_key, err = _find_item(args, items)
    if err:
        await player.send(err); return
    if item_key is None:
        await player.send(f"There is no '{args}' here."); return
    if len(player.inventory) >= player.max_inventory:
        await player.send("Your inventory is full."); return
    items.remove(item_key)
    player.inventory.append(item_key)
    name = _item_display_name(item_key)
    await player.send(f"You pick up the {name}.")
    await broadcast_room(player.current_room, f"{player.name} picks up the {name}.", exclude=player)


async def cmd_drop(player, args, _gs):
    if not args:
        await player.send("Usage: drop <item name>")
        return
    item_key, err = _find_item(args, player.inventory)
    if err:
        await player.send(err); return
    if item_key is None:
        await player.send(f"You don't have '{args}'."); return
    equipped_count = sum(1 for k in player.equipped_items.values() if k == item_key)
    if equipped_count >= player.inventory.count(item_key):
        await player.send(f"Unequip '{_item_display_name(item_key)}' before dropping it.")
        return
    player.inventory.remove(item_key)
    room_dict[player.current_room].setdefault("items", []).append(item_key)
    name = _item_display_name(item_key)
    await player.send(f"You drop the {name}.")
    await broadcast_room(player.current_room, f"{player.name} drops the {name}.", exclude=player)


async def cmd_inventory(player, _args, _gs):
    # Build a copy of inventory, then remove one occurrence per equipped slot so
    # duplicates (e.g. two leather armors when one is equipped) are shown correctly.
    remaining = list(player.inventory)
    lines = [f"Inventory ({len(player.inventory)}/{player.max_inventory}):"]
    for slot, key in player.equipped_items.items():
        if key:
            lines.append(f"  [{slot}] {_item_display_name(key)} (equipped)")
            if key in remaining:
                remaining.remove(key)
    for key in remaining:
        lines.append(f"  {_item_display_name(key)}")
    if player.quest_items:
        lines.append("")
        lines.append("Quest Items (no slot used):")
        for key in player.quest_items:
            lines.append(f"  [Quest Item] {_item_display_name(key)}")
    if not player.inventory and not any(player.equipped_items.values()) and not player.quest_items:
        lines.append("  (empty)")
    lines.append(f"Gold: {player.gold}  HP: {player.hp}/{player.max_hp}  ATK: {player.attack}  DEF: {player.defense}")
    await player.send("\n".join(lines))


async def cmd_quests(player, _args, _gs):
    if not player.quests:
        await player.send("You have no quests. Talk to NPCs to find some!")
        return
    active    = {k: v for k, v in player.quests.items() if v["status"] == "active"}
    completed = {k: v for k, v in player.quests.items() if v["status"] == "completed"}
    lines = []
    if active:
        lines.append("--- Active Quests ---")
        for q in active.values():
            lines.append(f"  {q['name']}: {q['desc']}")
    else:
        lines.append("--- No Active Quests ---")
    if completed:
        lines.append("")
        lines.append("--- Completed Quests ---")
        for q in completed.values():
            lines.append(f"  {q['name']} (done)")
    await player.send("\n".join(lines))


async def cmd_equip(player, args, _gs):
    if not args:
        await player.send("Usage: equip <item name>")
        return
    item_key, err = _find_item(args, player.inventory)
    if err:
        await player.send(err); return
    if item_key is None:
        await player.send(f"You don't have '{args}'."); return
    if item_key in weapon_dict:
        info = weapon_dict[item_key]
        slot = "weapon"
    elif item_key in equipment_lookup:
        info = equipment_lookup[item_key]
        slot = info["slot"]
    else:
        await player.send(f"'{args}' can't be equipped. Use 'use' for consumables.")
        return
    if player.equipped_items[slot]:
        current = _item_display_name(player.equipped_items[slot])
        await player.send(f"You already have {current} in your {slot} slot. Unequip it first.")
        return
    player.equipped_items[slot] = item_key
    if "damage" in info:
        player.bonus_attack += info["damage"]
    if "defense" in info:
        player.bonus_defense += info["defense"]
    player.recalculate_stats()
    await player.send(f"You equip the {info['name']}.  ATK: {player.attack}  DEF: {player.defense}")


async def cmd_unequip(player, args, _gs):
    if not args:
        await player.send("Usage: unequip <item name>")
        return
    equipped_keys = [k for k in player.equipped_items.values() if k]
    item_key, err = _find_item(args, equipped_keys)
    if err:
        await player.send(err); return
    if item_key is None:
        await player.send(f"You don't have '{args}' equipped."); return
    slot = next(s for s, k in player.equipped_items.items() if k == item_key)
    if item_key in weapon_dict:
        player.bonus_attack -= weapon_dict[item_key]["damage"]
    elif item_key in equipment_lookup:
        info = equipment_lookup[item_key]
        if "defense" in info:
            player.bonus_defense -= info["defense"]
    player.equipped_items[slot] = None
    player.recalculate_stats()
    await player.send(f"You unequip the {_item_display_name(item_key)}.  ATK: {player.attack}  DEF: {player.defense}")


async def cmd_flee(player, _args, _gs):
    if not player.in_combat:
        await player.send("You're not in combat.")
        return

    room_name = player.current_room
    live_mobs = _get_room_mobs(room_name)

    # Flee success chance: player agility vs highest mob agility
    if live_mobs:
        max_mob_agi  = max(m.agility for m in live_mobs)
        flee_chance  = player.agility / (player.agility + max_mob_agi)
    else:
        flee_chance = 1.0

    if random.random() > flee_chance:
        # Failed — take a free hit from a random mob
        await player.send("You try to flee but can't get away!")
        await broadcast_room(room_name, f"{player.name} tries to flee!", exclude=player)
        if live_mobs:
            punisher    = random.choice(live_mobs)
            mob_display = mob_dict[punisher.name]["name"]
            dmg, evaded, crit = _do_combat_hit(
                punisher.attack, punisher.crit_chance, punisher.crit_power,
                player.evasion, player.defense,
            )
            if not evaded:
                crit_str = " Critical hit!" if crit else ""
                player.hp -= dmg
                await broadcast_room(room_name,
                    f"The {mob_display} strikes {player.name} as they try to escape for {dmg} damage!{crit_str} "
                    f"({player.hp}/{player.max_hp} HP)")
                if player.hp <= 0:
                    await player_death(player, room_name, cause=mob_display)
        return

    # Success — remove from session and move to a random adjacent room
    _exit_combat(player)
    exits     = room_dict[room_name].get("exits", {})
    dir_exits = [(k, v) for k, v in exits.items()
                 if k in DIRECTIONS and v in room_dict]
    if dir_exits:
        flee_dir, flee_dest = random.choice(dir_exits)
        await broadcast_room(room_name,
            f"{player.name} flees to the {DIR_NAMES[flee_dir]}!", exclude=player)
        await player.send(f"You successfully flee to the {DIR_NAMES[flee_dir]}!")
        player.current_room = flee_dest
        await display_room(flee_dest, player)
    else:
        await player.send("You break free from combat!")
        await broadcast_room(room_name,
            f"{player.name} breaks free from combat!", exclude=player)


async def cmd_taunt(player, _args, _gs):
    if not player.in_combat:
        await player.send("You can only taunt in combat.")
        return

    session = game_state.combat_sessions.get(player.current_room)
    if not session:
        await player.send("No active combat here.")
        return

    cooldown = session.taunt_cooldowns.get(player.name, 0)
    if cooldown > 0:
        await player.send(f"Taunt is on cooldown for {cooldown} more round(s).")
        return

    session.taunt_target              = player
    session.taunt_cooldowns[player.name] = 2
    await broadcast_room(player.current_room,
        f"{player.name} lets out a battle cry! All enemies focus on {player.name}!")
    await player.send("You draw all enemy attention to yourself for the next round. (2-round cooldown)")


async def cmd_broadcast(player, args, _gs):
    if not args:
        await player.send("Usage: broadcast [delay_seconds] <message>")
        return

    parts = args.split(None, 1)
    delay = 0
    message = args

    try:
        delay = float(parts[0])
        if len(parts) < 2 or not parts[1].strip():
            await player.send("Usage: broadcast [delay_seconds] <message>")
            return
        message = parts[1].strip()
    except ValueError:
        delay = 0
        message = args

    async def _send():
        if delay > 0:
            await asyncio.sleep(delay)
        full_msg = f"[Broadcast] {message}"
        for p in list(game_state.players.values()):
            await p.send(full_msg)

    if delay > 0:
        asyncio.create_task(_send())
        await player.send(f"Broadcast scheduled in {delay:g} second(s): {message}")
    else:
        await _send()


async def cmd_set_respawn(player, _args, _gs):
    features = room_dict[player.current_room].get("features", [])
    if "respawn point" not in features:
        await player.send("There is no respawn point here.")
        return
    player.respawn_point = player.current_room
    room_name = room_dict[player.current_room]["name"]
    await player.send(f"Your respawn point is now set to {room_name}.")


# ── Party system ───────────────────────────────────────────────────────────────

def _follow_clear(player):
    """Remove player from their leader's follower set and clear player.following."""
    if player.following:
        leader = game_state.players.get(player.following)
        if leader:
            leader.followers.discard(player.name)
        player.following = None


async def _follow_cleanup(player):
    """Called on disconnect: clear all follow state for this player."""
    _follow_clear(player)
    for follower_name in list(player.followers):
        follower = game_state.players.get(follower_name)
        if follower:
            follower.following = None
            await follower.send(f"*** {player.name} has disconnected. You are no longer following them.")
    player.followers.clear()


async def _party_leave_cleanup(player):
    """Remove a player from their party; transfer leadership or disband as needed.

    Called both by cmd_party and by main.py on disconnect so cleanup is shared.
    """
    if player.party is None:
        return
    party = player.party
    party.members.remove(player)
    player.party = None
    if not party.members:
        return  # last member; party object is orphaned, GC'd
    leader_changed = party.leader is player
    if leader_changed:
        party.leader = party.members[0]
    for m in party.members:
        if leader_changed:
            await m.send(f"*** {player.name} has left the party. {party.leader.name} is now the leader.")
        else:
            await m.send(f"*** {player.name} has left the party.")


async def cmd_party(player, args, gs):
    sub = args.casefold().strip() if args else ""

    # Status display (no sub-command)
    if not sub:
        if player.party is None:
            await player.send(
                "You are not in a party.\n"
                "  party start          — create a new party\n"
                "  party join <player>  — join an existing party"
            )
        else:
            party = player.party
            lines = [f"--- Party (Leader: {party.leader.name}) [{len(party.members)}/{Party.MAX_SIZE}] ---"]
            for m in party.members:
                tag = " [Leader]" if m is party.leader else ""
                room_name = room_dict[m.current_room]["name"]
                lines.append(f"  {m.name}{tag}  HP: {m.hp}/{m.max_hp}  MP: {m.mp}/{m.max_mp}  [{room_name}]")
            await player.send("\n".join(lines))
        return

    if sub == "start":
        if player.party is not None:
            await player.send("You are already in a party. Type 'party leave' first.")
            return
        player.party = Party(player)
        await player.send(f"You have started a party! Others can join with: party join {player.name}")

    elif sub.startswith("join "):
        target_name = args[5:].strip()   # preserve case for lookup
        target = next(
            (p for p in gs.players.values() if p.name.casefold() == target_name.casefold()),
            None
        )
        if target is None:
            await player.send(f"No player named '{target_name}' is online.")
            return
        if target is player:
            await player.send("Use 'party start' to create your own party.")
            return
        if player.party is not None:
            await player.send("You are already in a party. Type 'party leave' first.")
            return
        if target.party is None:
            await player.send(f"{target.name} is not in a party. They need to start one first.")
            return
        if len(target.party.members) >= Party.MAX_SIZE:
            await player.send(f"That party is full ({Party.MAX_SIZE} players max).")
            return
        party = target.party
        party.members.append(player)
        player.party = party
        await player.send(f"You joined {party.leader.name}'s party!")
        for m in party.members:
            if m is not player:
                await m.send(f"{player.name} has joined the party!")

    elif sub == "leave":
        if player.party is None:
            await player.send("You are not in a party.")
            return
        if len(player.party.members) == 1:
            player.party = None
            await player.send("You disband the party.")
        else:
            await player.send("You leave the party.")
            await _party_leave_cleanup(player)

    else:
        await player.send("Unknown party command. Use: party, party start, party join <player>, party leave.")


async def cmd_party_say(player, args, _gs):
    if not args:
        await player.send("Usage: psay <message>  — send a message to your party")
        return
    if player.party is None:
        await player.send("You are not in a party.")
        return
    msg = f"[Party] {player.name}: {args}"
    for m in player.party.members:
        await m.send(msg)


# ── Private messaging ──────────────────────────────────────────────────────────

async def cmd_tell(player, args, gs):
    if not args:
        await player.send("Usage: tell <player> <message>")
        return
    parts = args.split(None, 1)
    if len(parts) < 2:
        await player.send("Usage: tell <player> <message>")
        return
    target_name, message = parts
    target = next(
        (p for p in gs.players.values() if p.name.casefold() == target_name.casefold()),
        None
    )
    if target is None:
        await player.send(f"No player named '{target_name}' is online.")
        return
    if target is player:
        await player.send("You can't message yourself.")
        return
    target.last_sender = player.name
    await target.send(f"[Tell] {player.name} -> you: {message}")
    await player.send(f"[Tell] you -> {target.name}: {message}")


async def cmd_reply(player, args, _gs):
    if not args:
        await player.send("Usage: reply <message>")
        return
    if not player.last_sender:
        await player.send("No one has sent you a message yet.")
        return
    target = game_state.players.get(player.last_sender)
    if target is None:
        await player.send(f"{player.last_sender} is no longer online.")
        player.last_sender = None
        return
    target.last_sender = player.name
    await target.send(f"[Tell] {player.name} -> you: {args}")
    await player.send(f"[Tell] you -> {target.name}: {args}")


async def cmd_follow(player, args, gs):
    sub = args.casefold().strip() if args else ""
    if not sub or sub == "stop":
        if player.following:
            leader_name = player.following
            _follow_clear(player)
            await player.send(f"You stop following {leader_name}.")
        else:
            await player.send("You are not following anyone.")
        return
    target = next((p for p in gs.players.values() if p.name.casefold() == sub), None)
    if target is None:
        await player.send(f"No player named '{args}' is online.")
        return
    if target is player:
        await player.send("You can't follow yourself.")
        return
    if target.current_room != player.current_room:
        await player.send(f"{target.name} is not in this room.")
        return
    if player.following == target.name:
        await player.send(f"You are already following {target.name}.")
        return
    _follow_clear(player)
    player.following = target.name
    target.followers.add(player.name)
    await player.send(f"You begin following {target.name}. Type a direction or 'follow stop' to stop.")
    await target.send(f"{player.name} is now following you.")


async def _handle_reset_input(player, text):
    """Process one line of input during an interactive password reset."""
    mode = player.reset_mode
    if mode["step"] == "new":
        if len(text) < 4:
            await player.send("Password must be at least 4 characters. New password: ")
            return
        mode["pending"] = text
        mode["step"] = "confirm"
        await player.send("Confirm new password: ")
    elif mode["step"] == "confirm":
        if text != mode["pending"]:
            await player.send("Passwords do not match. Try again. New password: ")
            mode["step"] = "new"
            mode["pending"] = None
        else:
            db.reset_password(mode["target"], text)
            await player.send(f"Password for '{mode['target']}' has been reset.")
            player.reset_mode = None


async def cmd_reset_password(player, args, gs):
    if player.role != "admin":
        await player.send("You don't have permission to use that command.")
        return
    if not args:
        await player.send("Usage: reset password <account name>")
        return
    target_name = args.strip()
    canonical = db.get_canonical_name(target_name)
    if canonical is None:
        await player.send(f"No account named '{target_name}'.")
        return
    player.reset_mode = {"target": canonical, "step": "new", "pending": None}
    await player.send(f"Resetting password for '{canonical}'. New password: ")


commands_dict = {
    "quit":        {"func": cmd_quit,        "desc": "Disconnect from the MUD."},
    "help":        {"func": cmd_help,        "desc": "List all commands."},
    "look":        {"func": cmd_look,        "desc": "Look at the room, or 'look <name>' to examine something."},
    "l":           {"func": cmd_look,        "desc": "Alias for look."},
    "say":         {"func": cmd_say,         "desc": "Say something to everyone in the room."},
    "who":         {"func": cmd_who,         "desc": "List all connected players."},
    "go":          {"func": cmd_go,           "desc": "Use a special exit: go <exit name>"},
    "enter":       {"func": cmd_go,           "desc": "Alias for go."},
    "list rooms":  {"func": cmd_list_rooms,  "desc": "List all rooms in the game."},
    "attack":      {"func": cmd_attack,      "desc": "Attack a mob: attack <mob name>"},
    "use":       {"func": cmd_use,       "desc": "Use a consumable: use <item name>"},
    "get":       {"func": cmd_get,       "desc": "Pick up an item from the room: get <item name>"},
    "take":      {"func": cmd_get,       "desc": "Alias for get."},
    "pick up":   {"func": cmd_get,       "desc": "Alias for get."},
    "drop":      {"func": cmd_drop,      "desc": "Drop an item: drop <item name>"},
    "inventory": {"func": cmd_inventory, "desc": "Show your inventory, stats, and equipped items."},
    "inv":       {"func": cmd_inventory, "desc": "Alias for inventory."},
    "i":         {"func": cmd_inventory, "desc": "Alias for inventory."},
    "equip":       {"func": cmd_equip,       "desc": "Equip an item to its slot: equip <item name>"},
    "unequip":     {"func": cmd_unequip,     "desc": "Unequip an item: unequip <item name>"},
    "flee":        {"func": cmd_flee,        "desc": "Attempt to flee from combat (agility-based chance)."},
    "run":         {"func": cmd_flee,        "desc": "Alias for flee."},
    "taunt":       {"func": cmd_taunt,       "desc": "Draw all enemy attention to yourself for one round (2-round cooldown)."},
    "broadcast":   {"func": cmd_broadcast,   "desc": "Send a message to all players: broadcast [delay_seconds] <message>"},
    "set respawn": {"func": cmd_set_respawn, "desc": "Set your respawn point to the current room (requires a respawn point feature)."},
    "character":   {"func": cmd_character,   "desc": "View your stats and spend stat points: character [stat]"},
    "char":        {"func": cmd_character,   "desc": "Alias for character."},
    "c":           {"func": cmd_character,   "desc": "Alias for character."},
    "quests":      {"func": cmd_quests,      "desc": "List your active and completed quests."},
    "quest":       {"func": cmd_quests,      "desc": "Alias for quests."},
    "party say":   {"func": cmd_party_say,   "desc": "Send a message to your party: party say <message>"},
    "party":       {"func": cmd_party,       "desc": "Party commands: party start | party join <player> | party leave | party (status)"},
    "psay":        {"func": cmd_party_say,   "desc": "Alias for party say."},
    "tell":        {"func": cmd_tell,        "desc": "Send a private message: tell <player> <message>"},
    "msg":         {"func": cmd_tell,        "desc": "Alias for tell."},
    "message":     {"func": cmd_tell,        "desc": "Alias for tell."},
    "reply":       {"func": cmd_reply,       "desc": "Reply to the last player who messaged you: reply <message>"},
    "r":           {"func": cmd_reply,       "desc": "Alias for reply."},
    "follow":           {"func": cmd_follow,          "desc": "Follow a player: follow <player> | follow stop"},
    "reset password":   {"func": cmd_reset_password,  "desc": "[Admin] Reset an account password: reset password <name>"},
    "change room":      {"func": cmd_change_room,     "desc": "[Admin] Teleport to a room: change room <name>"},
    "bonk":             {"func": cmd_bonk,            "desc": "[Admin] Remove a mob from the room: bonk <mob name>"},
    "n":  {"func": lambda p, a, gs: cmd_move(p, "n", gs),  "desc": "Move north."},
    "s":  {"func": lambda p, a, gs: cmd_move(p, "s", gs),  "desc": "Move south."},
    "e":  {"func": lambda p, a, gs: cmd_move(p, "e", gs),  "desc": "Move east."},
    "w":  {"func": lambda p, a, gs: cmd_move(p, "w", gs),  "desc": "Move west."},
    "u":  {"func": lambda p, a, gs: cmd_move(p, "u", gs),  "desc": "Move up."},
    "d":  {"func": lambda p, a, gs: cmd_move(p, "d", gs),  "desc": "Move down."},
}


async def handle_command(raw_input, player, gs):
    text = raw_input.strip()
    if not text:
        return

    # Interactive password-reset mode intercepts all input
    if player.reset_mode is not None:
        await _handle_reset_input(player, text)
        return

    lower = text.casefold()

    # Resolve direction aliases (north -> n, etc.)
    first_word = lower.split()[0]
    if first_word in DIR_ALIASES:
        lower = DIR_ALIASES[first_word]

    # Longest prefix match against commands_dict
    best_key = None
    best_args = ""
    for cmd_key in commands_dict:
        if lower == cmd_key:
            if best_key is None or len(cmd_key) >= len(best_key):
                best_key = cmd_key
                best_args = ""
        elif lower.startswith(cmd_key + " "):
            if best_key is None or len(cmd_key) > len(best_key):
                best_key = cmd_key
                best_args = text[len(cmd_key):].strip()

    if best_key is not None:
        await commands_dict[best_key]["func"](player, best_args, gs)
        return

    # Allow typing a special exit name directly (e.g. "portal", "start")
    exit_key = _find_special_exit(lower, player.current_room)
    if exit_key is not None:
        await cmd_move(player, exit_key, gs)
        return

    # Room keyword check (clues, quest triggers, etc.)
    kw_entry = _find_room_keyword(lower, player.current_room)
    if kw_entry is not None:
        await _handle_keyword_action(player, player.current_room, kw_entry)
        return

    await player.send("Invalid input. Type 'help' for a command list.")
