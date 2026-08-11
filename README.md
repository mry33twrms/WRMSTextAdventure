# WRMSTextAdventure
A Text Adventure program based around WRMS school for the blind. This text adventure will be playable by screen reader.

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

- Make a toggleable mode to reduce text. If a user has been to a room before, the description won't be displayed upon entry. The look command will always show the full description.

DONE - Add inventory system to pick up and drop items

DONE - Allow items to be equipped to slots

DONE - Use /context to read readme

- A NPC conversation system that allows users to type keywords that lead to dialogue. Keywords may trigger the next steps in quests or result in the exchange of items.

- a shop system where users can see items, prices and buy and sell

- special states for rooms such as when dark, flooded, on fire, full of smoke

- features for rooms that enable the use of items such as water to fish in, ores to mine, and trees to gather food. These features have limited uses that respawn over time.

- WHEN STABLE:
    - Add database to implement account creation, saving, logging in and out.
    - Leaderboards for kills, gold, and other milestones
    - Account types such as player, mod, admin that give different permissions. Mods and Admins can teleport, create monsters and items.




