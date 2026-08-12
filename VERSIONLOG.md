# WRMS MUD — Version Log

---

## v0.01 — MUD Conversion
- Rewrote single-player loop as asyncio TCP server (`main.py`)
- Added `game_state.py` — shared `players` dict for live world state
- Updated `player.py` — added `StreamWriter`, async `send()`, `quitting` flag
- Added `client.py` — Python telnet replacement for macOS
- Refactored `commands.py` to async; all commands take `(player, args, gs)`
- Added `broadcast_room()` — sends messages to all players in a room
- `display_room()` shows other players in the "You see:" list alongside NPCs
- Added `say <msg>` — broadcasts to everyone in the room
- Added `who` — lists connected players and their locations
- Added `look <name>` — examine an NPC or another player
- Movement broadcasts arrival/departure direction to others in the room

---

## v0.02 — Combat System
- Added `Player` stats: `hp`, `max_hp`, `attack`, `defense`, `gold`, `inventory`, `max_inventory`
- Added `game_state.room_mobs` — tracks live mob instances per room
- Added `_get_room_mobs()` — lazily initialises mob instances from `room_dict` on first access
- Added `cmd_attack` — player hits mob for `player.attack` damage; mob retaliates
- Mob defeat awards gold; player defeat restores HP and teleports to front admin
- Added `_respawn_mob()` — `asyncio.create_task` schedules mob reappearance after `respawn_time` seconds
- Fixed `mobs.py`: `take_damage()` returns bool (died), `deal_damage()` returns int, removed broken `del(self)`
- Added `gold` and `respawn_time` fields to all entries in `mob_dict`
- Added `name` and `desc` fields to `mob_dict` entries
- Fixed `display_room` mob section — was broken (iterated wrong dict, used undefined `mob_key`)
- Fixed `cmd_look` mob branch — was using `m.desc` (doesn't exist); now uses `mob_dict[m.name]["desc"]`
- Fixed `cmd_bonk` — was reading from `room_dict` directly; now uses live `game_state.room_mobs`

---

## v0.03 — Equipment & Inventory System
- Added `equipment.py` — `armor_dict`, `helmets_dict`, `legs_dict`, `boots_dict`, `gloves_dict`, `tools_dict`, `consumables_dict`
- Added `equipment_lookup` — combined dict mapping every equippable item key to its info + `"slot"` field
- Added `Player.equipped_items` — slots: `head`, `body`, `legs`, `feet`, `weapon`, `shield`, `accessory`, `tool`
- Added `cmd_get` / `cmd_drop` — pick up and drop items; ground items shown in room description
- Added `cmd_inventory` (`inventory`) — shows equipped slots, unequipped items, gold, HP, ATK, DEF
- Added `cmd_equip` — routes item to correct slot via `equipment_lookup["slot"]`; applies stat changes
- Added `cmd_unequip` — finds slot by searching `equipped_items`, reverses stat changes, clears slot
- Added `cmd_use` — consumes potions/food; recall scroll teleports to front admin
- Prevent dropping an equipped item (must unequip first)
- Fixed `equipment.py` bad import (`from asyncio import tools` → removed)
- Fixed `cmd_equip` dead-code branches where head/legs slots were unreachable (all routed to body)
- Fixed `cmd_unequip` not checking if item was equipped, not clearing slot
- Added ground item display to `display_room`
- Added test items to front admin room (`leather`, `short sword`, `health potion`)
- Added `VERSION` constant to `main.py`; printed on server start and player connect

---

## v0.04 — Command Aliases & Fuzzy Matching
- Added `_find_item(query, item_keys)` — matches typed input against item keys and display names; exact → partial; returns ambiguity error if multiple matches
- Added `_find_mob(query, mob_list)` — same approach for mob targeting
- All item commands (`get`, `drop`, `equip`, `unequip`, `use`) use fuzzy matching — "get leather armor" and "get armor" both work
- `attack` and `bonk` use fuzzy mob matching — "attack orc" finds `orc guard`
- Added command aliases: `inv` / `i` → inventory; `l` → look; `take` / `pick up` → get

---

## v0.05 — Special Exits System
- Replaced one-off `start` command with general `go` / `enter` commands for special (non-directional) exits
- Added `DIRECTIONS` constant (`{"n","s","e","w","u","d"}`) to cleanly separate special exits from directional ones
- Added `_find_special_exit(query, room_name)` — fuzzy helper: exact match → partial substring match; returns `None` if ambiguous
- `go <name>` / `enter <name>` fuzzy-match and traverse any special exit in the current room
- `go` / `enter` with no argument lists available special exits
- Typing an exit name directly (e.g. `portal`) also works via fallback at the bottom of `handle_command`
- `display_room` now shows cardinal exits and special exits on separate lines ("Exits:" / "Special exits:")
- Removed the `start` command from `commands_dict`; `start` still works via the direct-exit fallback

---

## v0.06 — Loot Drop System
- Added `tier_weight(tier)` — returns `1 / (2 ** (tier - 1))`; higher tiers drop exponentially less often
- Added `_item_tier(item_key)` — looks up `"tier"` field across all item dicts, defaults to 1
- Added `choose_loot(mob_name)` — picks one item from the mob's loot list using `random.choices` with tier-based weights
- `cmd_attack`: on mob defeat, calls `choose_loot` and drops the result to the room floor; announces the drop to the player
- Fixed `cmd_attack` defeat block: was using raw typed args for `mob_dict` lookups (broke fuzzy-matched names); now uses `target.name`
- Added `"cloth shirt"` to `armor_dict` (tier 1) — referenced in mob loot tables but was missing
- Added `gloves_dict` to `equipment_lookup` with slot `"gloves"`; added `"gloves"` slot to `Player.equipped_items`
- Expanded `_item_info` to also check `materials_dict` for proper display names on material drops

---

## v0.07 — NPC Conversation System
- Added `Player.talking_to` — tracks the NPC key the player is currently in conversation with
- Added `GREETINGS` and `FAREWELLS` constant sets for trigger word detection
- Added `_conversable_npc(room_name)` — returns the first NPC in the room that has a `convos` dict
- Added `handle_npc_convo(player, text, npc_key)` — matches player message against convo keywords (substring search), falls back to `"default"`, ends conversation on farewell words
- Added `_run_convo_action(player, entry)` — action dispatcher for convo entries that are dicts; currently supports `"transport"` (charges optional gold cost, moves player to destination)
- Updated `cmd_say`: greeting words in a room with a conversable NPC initiate conversation; subsequent `say` commands route through the convo system; normal say otherwise
- Moving rooms automatically clears `player.talking_to`
- Convo entries support plain strings or action dicts: `{"text": "...", "action": "transport", "cost": 10, "destination": "room_key", "cost_msg": "..."}`
- Fixed `rooms.py` syntax error: `campus corner` `shop` property was written as a mixed list/dict — corrected to a proper dict

---

## v0.08 — NPC Shop System
- Moved shop data from `rooms.py` to the NPC entry in `npcs.py` — shop travels with the NPC, not the room
- `shop` dict on an NPC has two keys: `sell_dict` (items NPC sells → price player pays) and `buy_dict` (set prices NPC pays when buying from player)
- Added `Player.pending_transaction` — holds `{"type": "buy"/"sell", "item_key": ..., "price": ...}` while awaiting confirmation
- Added `_sell_price(item_key, shop)` — returns `buy_dict` price if listed, otherwise 50% of item base price (min 1)
- Added `_shop_list_sell` / `_shop_list_buy` — display sell and buy menus
- Added `_shop_buy_item` / `_shop_sell_item` — look up item, validate, set pending transaction with quoted price
- Added `_complete_transaction` — executes on "yes": checks gold/inventory, transfers item and gold, clears pending
- Shop is triggered inside `handle_npc_convo` when the NPC has a `shop` key: "buy" / "for sale" → list; "buy <item>" → quote + confirm; "sell" → buy menu; "sell <item>" → quote + confirm
- Saying anything other than yes/no while a transaction is pending reminds the player to confirm or cancel
- Moving rooms clears both `talking_to` and `pending_transaction`
- Equipped items cannot be sold (must unequip first)
- Items with no price (price = 0) are refused by the NPC
