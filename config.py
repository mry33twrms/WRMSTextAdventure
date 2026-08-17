# Stat scaling constants — edit these to rebalance gameplay

# Strength: damage and crit power
DAMAGE_PER_STR      = 1    # attack added per STR point
CRIT_POWER_PER_STR  = 1    # crit damage % added per STR point

# Agility: evasion and crit chance
EVASION_PER_AGI     = 1    # evasion % added per AGI point
CRIT_CHANCE_PER_AGI = 1    # crit chance % added per AGI point

# Intelligence: magic damage and resistance
MAGIC_DAMAGE_PER_INT = 1   # magic damage added per INT point
MAGIC_RESIST_PER_INT = 3   # magic resistance added per INT point

# Intelligence: mana
MP_PER_INT  = 5            # max MP added per INT point

# Vitality: health
HP_PER_VIT = 5             # max HP added per VIT point

# Base stats before primary stat contribution
BASE_HP     = 5
BASE_MP     = 5
BASE_ATTACK = 2

# Starting primary stat values for new players
STARTING_STAT  = 3
STARTING_LEVEL = 1

# XP curve: xp_to_next = int(XP_BASE * current_level ** XP_EXPONENT)
XP_BASE     = 10
XP_EXPONENT = 1.5
