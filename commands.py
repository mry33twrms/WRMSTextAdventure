import asyncio
import random
from mobs import mob, mob_dict
from rooms import room_dict
from npcs import npc_dict
from weapons import weapon_dict
from equipment import equipment_lookup, consumables_dict, materials_dict
from room_features import features_dict
from config import XP_BASE, XP_EXPONENT
import game_state

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


async def _run_convo_action(player, entry):
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
    resp = entry["text"] if isinstance(entry, dict) else entry
    await player.send(f"{npc_name}: {resp}")

    if isinstance(entry, dict) and "action" in entry:
        await _run_convo_action(player, entry)


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
        npc = npc_dict[npc_key]
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
    if not args:
        await player.send("Usage: change room <room name>")
        return
    if args not in room_dict:
        await player.send(f"Room '{args}' not found.")
        return
    old_room = player.current_room
    await broadcast_room(old_room, f"{player.name} vanishes into thin air.", exclude=player)
    player.current_room = args
    await broadcast_room(args, f"{player.name} appears out of thin air.", exclude=player)
    await display_room(args, player)


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
    room = room_dict[player.current_room]
    exits = room.get("exits", {})
    if direction not in exits:
        await player.send("You can't go that way.")
        return

    new_room_key = exits[direction]
    if new_room_key not in room_dict:
        await player.send("That passage leads nowhere. (Missing room)")
        return

    old_room = player.current_room
    player.talking_to = None
    player.pending_transaction = None

    if direction in DIR_NAMES:
        await broadcast_room(old_room, f"{player.name} leaves to the {DIR_NAMES[direction]}.", exclude=player)
        await broadcast_room(new_room_key, f"{player.name} arrives from the {OPPOSITE_DIR[direction]}.", exclude=player)

    player.current_room = new_room_key
    await display_room(new_room_key, player)

async def _respawn_mob(room_name, mob_key, delay):
    await asyncio.sleep(delay)
    info = mob_dict[mob_key]
    new_mob = mob(mob_key, info)
    game_state.room_mobs.setdefault(room_name, []).append(new_mob)
    await broadcast_room(room_name, f"A {info['name']} has appeared!")


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
    """Restore HP, clear state, broadcast defeat, and teleport to respawn point."""
    player.hp = player.max_hp
    player.talking_to = None
    player.pending_transaction = None
    cause_str = f" by the {cause}" if cause else ""
    await broadcast_room(room_name, f"{player.name} was defeated{cause_str}!", exclude=player)
    player.current_room = player.respawn_point
    respawn_name = room_dict[player.respawn_point]["name"]
    await player.send(f"You have been defeated{cause_str} and wake up at the {respawn_name}.")
    await display_room(player.respawn_point, player)


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


async def cmd_attack(player, args, _gs):
    if not args:
        await player.send("Usage: attack <mob name>")
        return

    room_name = player.current_room
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

    mob_info = mob_dict[target.name]
    mob_display = mob_info["name"]

    # Player attacks mob
    damage, evaded, is_crit = _do_combat_hit(
        player.attack, player.crit_chance, player.crit_power,
        target.evasion, target.defense,
    )
    if evaded:
        await player.send(f"You swing at the {mob_display} but they dodge!")
        await broadcast_room(room_name, f"{player.name} swings at the {mob_display} but misses!", exclude=player)
    else:
        died = target.take_damage(damage)
        crit_str = " Critical hit!" if is_crit else ""
        await player.send(f"You attack the {mob_display} for {damage} damage!{crit_str} ({target.hp}/{target.max_hp} HP)")
        await broadcast_room(room_name, f"{player.name} attacks the {mob_display}!", exclude=player)

        if died:
            live_mobs.remove(target)
            gold = mob_info.get("gold", 0)
            player.gold += gold
            defeat_msg = f"You defeated the {mob_display}!"
            if gold:
                defeat_msg += f" You find {gold} gold."
            loot_key = choose_loot(target.name)
            if loot_key:
                room_dict[room_name].setdefault("items", []).append(loot_key)
                defeat_msg += f" The {mob_display} drops {_item_display_name(loot_key)}."
            await player.send(defeat_msg)
            await broadcast_room(room_name, f"The {mob_display} has been defeated by {player.name}!", exclude=player)
            await gain_xp(player, mob_info.get("xp", 0))
            respawn_time = mob_info.get("respawn_time", 60)
            asyncio.create_task(_respawn_mob(room_name, target.name, respawn_time))
            return

    # Mob counterattacks (whether player hit or missed)
    mob_damage, mob_evaded, mob_crit = _do_combat_hit(
        target.attack, target.crit_chance, target.crit_power,
        player.evasion, player.defense,
    )
    if mob_evaded:
        await player.send(f"The {mob_display} swings at you but you dodge!")
    else:
        crit_str = " Critical hit!" if mob_crit else ""
        player.hp -= mob_damage
        await player.send(f"The {mob_display} hits you for {mob_damage} damage!{crit_str} ({player.hp}/{player.max_hp} HP)")
        if player.hp <= 0:
            await player_death(player, room_name, cause=mob_display)

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
    if not player.inventory and not any(player.equipped_items.values()):
        lines.append("  (empty)")
    lines.append(f"Gold: {player.gold}  HP: {player.hp}/{player.max_hp}  ATK: {player.attack}  DEF: {player.defense}")
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
    "change room": {"func": cmd_change_room, "desc": "Teleport to a room: change room <name>"},
    "bonk":        {"func": cmd_bonk,        "desc": "Bonk a mob: bonk <mob name>"},
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
    "broadcast":   {"func": cmd_broadcast,   "desc": "Send a message to all players: broadcast [delay_seconds] <message>"},
    "set respawn": {"func": cmd_set_respawn, "desc": "Set your respawn point to the current room (requires a respawn point feature)."},
    "character":   {"func": cmd_character,   "desc": "View your stats and spend stat points: character [stat]"},
    "char":        {"func": cmd_character,   "desc": "Alias for character."},
    "c":           {"func": cmd_character,   "desc": "Alias for character."},
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

    await player.send("Invalid input. Type 'help' for a command list.")
