# WRMSTextAdventure
A Text Adventure program based around WRMS school for the blind. This text adventure will be playable by screen reader.

# Developed with lots of help from Chat GPT and Claude

# Context Instructions:

- Update version number by 0.01 each time we add a system and test it.
- Complete requests.
- Test new functions.
- Review command functions and dictionary to make sure that we have both entries for new commands.
- Review Help Command to make sure all commands have entries.
- Stop last sessions
- Launch server for user testing.


Todo:

DONE - Add Version number and updates in server/client start

DONE - Add inventory system to pick up and drop items

DONE - Allow items to be equipped to slots

DONE - Use /context to read readme

DONE - special exits

DONE - mobs drop loot

DONE - loot table system

DONE - a shop system where users can see items, prices and buy and sell

DONE - Character menu to display stats

DONE - Level system allowing players to improve stats when leveling up

DONE - A NPC conversation system that allows users to type keywords that lead to dialogue. Keywords may trigger the next steps in quests or result in the exchange of items.

DONE - Add checks to the attack command to check if the player is trying to target an NPC or another player. Respond with, "You can't attack <target>. They're on your side."

- Make a toggleable mode to reduce text. If a user has been to a room before, the description won't be displayed upon entry. The look command will always show the full description.

- Short and Full descriptions

DONE - Description keywords for things like signs

DONE - Critical hit system

DONE - use armor in attack system calculations

DONE - Dodging/Evasion system

DONE - Party & Follow system

DONE - Teleport to command for admin.

DONE - Hiding password on client.

Done - Admin command to create items: create <item name>

- Magical items and damage types

- buff pool on items

DONE - hostile mob system. Upon entering player will be warned that one mob is about to attack, giving them a chance to retreat.

DONE - a property for rooms called guarded allowing a list of exits to be blocked until a mob is defeated.

DONE - locked doors that require keys to open. The unlock/open should be aliases that tries to use the use command with the key.

- special states for rooms such as when dark, flooded, on fire, full of smoke

- features for rooms that enable the use of items such as water to fish in, ores to mine, and trees to gather food. These features have limited uses that respawn over time. 

- Water fountain room features that restore health.

- special combat items such as throwables. eg: Goalball

- WHEN STABLE:
    - Add database to implement account creation, saving, logging in and out. -sqllite
    - Leaderboards for kills, gold, and other milestones
    - Awards for playing seasons & school years
    - Account types such as player, mod, admin that give different permissions. Mods and Admins can teleport, create monsters and items.
    - Log system for chat, player movements, items created/destroyed.  -MONGODB?
    - SSH deployment
    - Auto Backup of database to another server
    - Randomized instances, parties can fight through till they perish. Roguelike buff elements.
    - Dueling




