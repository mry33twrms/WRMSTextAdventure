# WRMS MUD — Version Log

---

## v0.19 — Equip Fixes, Password Masking & Admin Create

### Bug fixes
- **`KeyError: 'weapon'` crash on equip**: new accounts had `equipped_items` saved as `{}` in the DB default; on load the dict was empty, so `player.equipped_items["weapon"]` crashed. Fixed by merging loaded data with the full default slot structure in `_load_player_from_db`.
- **Equip did not remove item from inventory**: `cmd_equip` set the slot but left the item in `player.inventory`. Fixed — item is now removed on equip.
- **Unequip did not return item to inventory**: `cmd_unequip` cleared the slot but discarded the item. Fixed — item is now appended back to inventory.
- **Inventory display hid second copy of equipped item**: `cmd_inventory` was written for the old system where equipped items stayed in inventory and one copy was subtracted from the display. Now that equip removes the item, the subtraction was consuming a legitimately separate item. Fixed — equipped items are displayed above the inventory list with no subtraction logic.
- **Legacy save normalization**: accounts saved before the equip fix may have an item duplicated in both `equipped_items` and `inventory`. On load, any equipped item found in `inventory` is now removed to normalize the state.

### Password masking (client + server)
- Defined `PWD_SIGNAL = "\x1bPWD"` in `config.py` — a byte sequence prepended by the server to any password prompt
- `_prompt()` in `main.py` accepts `password=True`; all login and account-creation password prompts tagged
- Password reset prompts in `commands.py` (`cmd_reset_password`, `_handle_reset_input`) also tagged
- `client.py` detects `\x1bPWD` in received data, strips it before display, sets `password_mode = True`; subsequent keystrokes echo `*` until Enter is pressed, which resets the mode

### Admin `create` command
- **`create <item name>`** — admin-only; spawns any item by its key name directly into the admin's inventory; unknown item names give a clear error; non-admins are denied

### Admin `tpto` fix
- Player lookup was case-sensitive (`game_state.players.get(args)`); `tpto dean` would fail if the account was stored as `Dean`. Fixed to use case-insensitive search matching all other commands. Added self-teleport guard ("You're already there.").

---

## v0.18 — SQLite Accounts & World Persistence

### Account system (`database.py`)
- SQLite3 database (`wrms.db`) initialised at server start via `db.init_db()`
- `accounts` table: `name`, `password_hash` (bcrypt), `email`, `role` (`"player"` | `"admin"`), `created_at`, `last_login`
- `player_data` table: full player state — gold, inventory, equipment, all primary stats, level/xp, HP/MP, room, respawn point, quests, quest items, received NPC items
- Passwords encrypted with **bcrypt** (`bcrypt.hashpw` / `bcrypt.checkpw`)
- Case-insensitive account lookup (`COLLATE NOCASE`) preserving original casing

### Login flow (`main.py`)
- **First run**: if no admin accounts exist, the first connection triggers interactive admin setup (name → password → confirm → email); no further connections can proceed until this completes
- **Returning account**: prompts for password; up to 3 attempts before disconnect; duplicate login (same account already online) is rejected
- **New account**: prompts for password (×2 to confirm) and email; account created as `"player"` role
- Player state is fully loaded from DB after successful login; current room validated against `room_dict` (falls back to `"front admin"` if room was removed)
- Player state saved to DB on disconnect (in `finally` block, before party/follow cleanup)
- Admin/player role label broadcast to other players on entry

### Admin commands
- `change room <name>` — admin only; non-admins get "You don't have permission to use that command."
- `bonk <mob>` — admin only (same guard)
- `reset password <account>` — admin only; interactive two-step prompt (new password → confirm) intercepted at the top of `handle_command` via `player.reset_mode` state; minimum 4-character length enforced

### Player changes
- Added `player.role` (`"player"` | `"admin"`) — set from DB on login
- Added `player.reset_mode` (None or state dict) — drives interactive password-reset input

---

## v0.17 — Guarded & Locked Exits

- **Guarded exits** (`"guarded": [<direction>, ...]` in room dict): if any live mobs are present, listed exit directions are blocked with "The [mob] blocks your path! Defeat it first." Once all mobs are defeated the exit opens normally. Implemented in `cmd_move` before movement is committed.
- **Locked exits** (`"locked": <direction>`, `"requires_key": <item_key>` in room dict): the listed exit is locked until a player with the required key item uses it. The key-holder triggers an unlock, broadcasts "X unlocks the door to the [direction]! It will lock again in 10 seconds." Other players in the room can pass freely for that window. After `LOCK_OPEN_DELAY` (10s) the `_relock_exit` task fires, removes the exit from `game_state.unlocked_exits`, and broadcasts "The door to the [direction] locks again with a click."
- Added `game_state.unlocked_exits` — a `set` of `(room_name, direction)` tuples tracking currently open locked doors
- Added `LOCK_OPEN_DELAY = 10` constant in commands.py
- Added `_relock_exit(room_name, direction)` async helper
- Added `"principal key"` to `equipment.py` `keys_dict`; added `keys_dict` to commands.py import and `_item_info` lookup so key items display names correctly
- Added `Cindi` NPC stub to `npcs.py` (was referenced in west admin's npcs list but undefined, causing a crash on room display); made `display_room` skip unknown NPC keys instead of raising `KeyError`
- Added `"principal key"` to back admin's test items so the locked door can be tested

---

## v0.16 — Follow System

- Added `player.following` (name of leader being followed, or None) and `player.followers` (set of follower names)
- Added `_follow_clear(player)` — removes player from their leader's `followers` set and clears `player.following`
- Added `_follow_cleanup(player)` — called on disconnect; clears follow state and notifies any followers they've lost their target
- **`follow <player>`** — start following a player in the same room; sets mutual follow state and notifies both parties
- **`follow stop`** / **`follow`** (no args) — stop following; notifies player
- **`cmd_move` follower drag** — when a player moves, all followers in the same room are automatically dragged to the new room (skipped if follower is in combat); broadcasted with "follows … to …" / "arrives following …" messages; hostile encounter checks run per dragged follower
- **`cmd_move` auto-follow** — when a party member arrives in the party leader's room, they auto-follow the leader; when the leader arrives where members are, those members auto-follow; both parties notified
- **`cmd_move` follow clear** — moving under your own direction clears your own follow (direction = interrupt)
- **`cmd_change_room` teleport** — teleporting clears the player's follow and notifies all their followers; followers are not dragged on teleport
- **`party` status** — room name added to each member line: `[Room Name]`
- `_follow_cleanup` imported in `main.py` and called in disconnect `finally` block before party cleanup

---

## v0.15 — Party System & Private Messaging

- Added `Party` class (`MAX_SIZE = 4`): tracks `leader` and `members` list; shared by reference across all member players
- Added `player.party` (Party object or None) and `player.last_sender` (name of last tell sender, for reply)
- Added `player.mp` / `player.max_mp` and `BASE_MP` / `MP_PER_INT` constants — mana now scales with Intelligence (matching the existing mana potions in the item system); `recalculate_stats` computes and clamps mp alongside hp
- **`party`** — no args shows party status (name, [Leader] tag, HP, MP per member) or help if not in a party
- **`party start`** — creates a new party with the player as leader; others join with `party join <player>`
- **`party join <player>`** — case-insensitive player lookup; validates not already in a party, target has a party, party has room; notifies all existing members
- **`party leave`** — removes player; if last member disbands, otherwise transfers leadership to next member and notifies remaining members
- **`party say`** / **`psay`** — sends a `[Party]` prefixed message to all party members
- **`tell`** / **`msg`** / **`message`** — sends a `[Tell]` private message to a named online player; sets `last_sender` on recipient
- **`reply`** / **`r`** — replies to the last player who sent you a tell; updates `last_sender` bi-directionally
- Added `_party_leave_cleanup(player)` helper — shared by `party leave` command and `main.py` disconnect handler so leaving on disconnect notifies remaining members and transfers leadership correctly

---

## v0.14 — Quest System & NPC Item Gifts

- Added `player.quests` — dict of `quest_id → {name, desc, status}` tracking active and completed quests
- Added `player.quest_items` — separate list for quest items; quest items never consume inventory space
- Added `player.received_npc_items` — set of item keys gifted by NPCs; used to enforce one-time gifts
- Added `quest_items_dict` to `equipment.py` (already present); imported into `commands.py` so `_item_info` and `_item_display_name` work for quest items
- **NPC convo actions** — `_run_convo_action` now handles three new action types:
  - `give_item`: gives a regular item from inventory; `"once": true` + `"once_msg"` enforces one-time gift tracking via `received_npc_items`
  - `give_quest`: adds a quest to `player.quests`; `"already_given_msg"` fires if quest already active
  - `complete_quest`: checks `requires_quest_item` in `player.quest_items`, removes it, gives `reward_item`, marks quest completed
- `handle_npc_convo` pre-checks action conditions before sending NPC text so `once_msg`, `already_given_msg`, `no_quest_msg`, and `no_item_msg` short-circuit correctly
- **Room keywords** — `_find_room_keyword(query, room_name)` does exact then substring match against `room["keywords"]` dict; `_handle_keyword_action` dispatches plain string (description) or action dict
  - `give_quest_item` action: checks `requires_quest` on player, guards against duplicate pickup with `already_text`, gives quest item and broadcasts `[Quest Item obtained]`
- `handle_command` now checks room keywords after special exits, before "Invalid input"
- **`cmd_quests`** — lists active quests with description and completed quests with `(done)` label; aliased as both `quests` and `quest`
- `cmd_inventory` shows quest items in a separate "Quest Items (no slot used):" section with `[Quest Item]` label
- Updated Kristi NPC: `help` gives a one-time health potion; `quest` starts the Missing Homework quest; `homework` completes it (requires quest item) and rewards an apple
- Updated courtyard `ring bell` keyword to action dict: gives `missing homework` quest item if quest is active, shows neutral flavour text otherwise, and guards against re-pickup
- Fixed `cmd_change_room` not clearing `talking_to` / `pending_transaction` on teleport (mirroring `cmd_move`)

---

## v0.13 — Combat Robustness: Periodic Check & Mid-Combat Entry

- Added `_hostile_check_loop()` — background task started at server boot (every 3 s); scans all visited rooms for hostile mobs + present players with no active combat session and triggers a new `CombatSession` + warning; catches any room-entry path not handled by `cmd_move` or `cmd_change_room` (recall scrolls, future teleport commands, etc.)
- Added `_warn_and_join(player, session)` — personal 5-second warning for players who enter a room while combat is already underway; player can move back out during the countdown; if still present when it expires they are added to the active session
- Added `CombatSession.pending_join` set — tracks player names with an active `_warn_and_join` task to prevent double-warnings from both the entry path and the periodic loop
- `_trigger_hostile_warning` now marks all players present at the start of the countdown in `pending_join` so the check loop does not issue a redundant personal warning for them
- `_exit_combat` now also removes the player from `session.pending_join` so a fleeing player is not auto-joined when their countdown expires
- Added hostile-encounter check to `cmd_change_room` (was only in `cmd_move`); both paths now issue the same warning/join logic
- `_hostile_check_loop` also sweeps active combat sessions each tick and issues `_warn_and_join` for any players in the room who are not yet in combat (handles players who arrived via paths that bypass both `cmd_move` and `cmd_change_room`)
- New mobs appearing in a room with an active session (respawns, future summons) are automatically included in the next round via `_execute_round`'s dynamic `_get_room_mobs()` call — no extra tracking needed

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

---

## v0.12 — Round-Based Combat System

- Added `CombatSession` class tracking players, per-player damage dealt, gold pool, taunt state, and cooldowns
- Added `combat_sessions` dict to `game_state`; added `in_combat` and `combat_room` fields to `Player`
- **Hostile flag**: rooms (`room_dict`) and mobs (`mob_dict`) can have `"hostile": True`; entering a hostile room with live mobs triggers a 5-second warning broadcast then starts combat automatically; hostile mob respawn near players also triggers the warning
- **Round loop** (`_run_combat_loop` / `_execute_round`): every 4 seconds all participants act in descending agility order — players auto-attack a random mob, mobs attack the taunted player or a random player
- **Gold distribution**: gold from defeated mobs pools during combat; on victory it is distributed proportionally to damage dealt
- **XP** awarded to the player who lands the killing blow
- `cmd_attack` now starts or joins a `CombatSession` rather than resolving a single hit; players cannot move normally while in combat
- Added `cmd_flee` / `run`: flee success chance = `player.agility / (player.agility + max_mob_agility)`; failure deals a free punishment hit; success randomly moves the player to an adjacent room
- Added `cmd_taunt`: directs all mobs to attack the taunting player for one round; 2-round cooldown tracked per-player in the session
- `player_death` now removes the player from their combat session before teleporting

---

## v0.11 — Global Broadcast & Input Protection

- Added `cmd_broadcast` — sends a `[Broadcast]` message to every connected player; optional first numeric argument schedules it with `asyncio.create_task` + `asyncio.sleep`; immediate broadcasts also reach the sender
- Added `"broadcast"` to `commands_dict`
- Rewrote `client.py` — switches stdin to raw mode (`tty.setraw`) so input is read character-by-character via a daemon thread feeding an asyncio queue; on any server message the current input line is cleared (`\r\033[K`), the message is printed, and the prompt + partial input are restored; backspace, Ctrl+C, Ctrl+D, and arrow-key escape sequences handled cleanly

---

## v0.10 — Stats, Leveling & Character Menu

- Added `config.py` — all gameplay-tuning constants: stat scaling (`DAMAGE_PER_STR`, `CRIT_POWER_PER_STR`, `EVASION_PER_AGI`, `CRIT_CHANCE_PER_AGI`, `MAGIC_DAMAGE_PER_INT`, `MAGIC_RESIST_PER_INT`, `HP_PER_VIT`), base stats (`BASE_HP`, `BASE_ATTACK`), and XP curve params (`XP_BASE`, `XP_EXPONENT`)
- Rewrote `player.py`: primary stats (strength, agility, intelligence, vitality) start at `STARTING_STAT`; all derived stats computed by `recalculate_stats()`; added `level`, `xp`, `stat_points`; added elemental resistances (`fire_resist`, `ice_resist`, `shock_resist`); constructor no longer takes `attack`/`hp`/`max_hp`/`defense` params
- Added `_xp_to_next_level(level)` — exponential XP curve: `int(XP_BASE * level ** XP_EXPONENT)`
- Added `gain_xp(player, amount)` — accumulates XP, handles level-up loop, awards 1 stat point per level, calls `recalculate_stats()`
- Added `cmd_character` (`character` / `char` / `c`): no args shows full stat sheet (primary stats, derived stats, elemental resists, XP progress); with stat name arg spends one unspent stat point on that stat
- `cmd_attack` defeat block now calls `await gain_xp(player, mob_info.get("xp", 0))`
- Fixed `cmd_equip`: now applies item bonuses via `player.bonus_attack`/`bonus_defense` + `recalculate_stats()` instead of direct `player.attack` mutation
- Fixed `cmd_unequip`: same fix — reverses via `bonus_attack`/`bonus_defense` + `recalculate_stats()`; unequipping no longer permanently alters base attack
- Added `xp` field to all mob_dict entries (goblin 10, troll 30, skeleton 20, orc guard 8)

---

## v0.09 — Room Features & Respawn System
- Added `room_features.py` — `features_dict` defining interactive room elements (respawn point, fishing hole, ore vein, herb patch), each with action, success rate, reward, and cooldown fields ready for future implementation
- Imported `features_dict` into `commands.py`; `display_room` now appends a "Features:" line listing any features present in the room
- Added `player.respawn_point` (default `"front admin"`) — already set by user in `player.py`
- Added `player_death(player, room_name, cause=None)` — centralised death handler: restores HP, clears `talking_to` and `pending_transaction`, broadcasts defeat to room, teleports to `player.respawn_point`, displays new room
- `cmd_attack` death block replaced with single `await player_death(...)` call
- Added `cmd_set_respawn` — sets `player.respawn_point` to current room only if it has a `"respawn point"` feature; fails gracefully otherwise
- Added `"set respawn"` to `commands_dict`
- Fixed `cmd_use` recall scroll: now uses `player.respawn_point` (was hardcoded), clears `talking_to`/`pending_transaction` before teleporting, and uses the room's display name in the message
