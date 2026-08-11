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
