import sqlite3
import json
import bcrypt

DB_PATH = "wrms.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            name          TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            email         TEXT DEFAULT '',
            role          TEXT NOT NULL DEFAULT 'player',
            created_at    TEXT DEFAULT (datetime('now')),
            last_login    TEXT
        );
        CREATE TABLE IF NOT EXISTS player_data (
            name              TEXT PRIMARY KEY,
            gold              INTEGER DEFAULT 0,
            inventory         TEXT    DEFAULT '[]',
            equipped_items    TEXT    DEFAULT '{}',
            strength          INTEGER DEFAULT 3,
            agility           INTEGER DEFAULT 3,
            intelligence      INTEGER DEFAULT 3,
            vitality          INTEGER DEFAULT 3,
            level             INTEGER DEFAULT 1,
            xp                INTEGER DEFAULT 0,
            stat_points       INTEGER DEFAULT 0,
            bonus_attack      INTEGER DEFAULT 0,
            bonus_defense     INTEGER DEFAULT 0,
            hp                INTEGER DEFAULT 0,
            mp                INTEGER DEFAULT 0,
            current_room      TEXT    DEFAULT 'front admin',
            respawn_point     TEXT    DEFAULT 'front admin',
            quests            TEXT    DEFAULT '{}',
            quest_items       TEXT    DEFAULT '[]',
            received_npc_items TEXT   DEFAULT '[]',
            FOREIGN KEY (name) REFERENCES accounts(name)
        );
    """)
    conn.commit()
    conn.close()


def has_any_admin():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM accounts WHERE role = 'admin' LIMIT 1")
    result = c.fetchone() is not None
    conn.close()
    return result


def account_exists(name):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM accounts WHERE name = ? COLLATE NOCASE", (name,))
    result = c.fetchone() is not None
    conn.close()
    return result


def get_canonical_name(name):
    """Return the stored name (preserving original casing) for a case-insensitive match."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT name FROM accounts WHERE name = ? COLLATE NOCASE", (name,))
    row = c.fetchone()
    conn.close()
    return row["name"] if row else None


def create_account(name, password, email, role="player"):
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO accounts (name, password_hash, email, role) VALUES (?, ?, ?, ?)",
        (name, pw_hash, email, role),
    )
    c.execute("INSERT INTO player_data (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def verify_password(name, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT password_hash FROM accounts WHERE name = ? COLLATE NOCASE", (name,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return False
    return bcrypt.checkpw(password.encode(), row["password_hash"].encode())


def get_role(name):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT role FROM accounts WHERE name = ? COLLATE NOCASE", (name,))
    row = c.fetchone()
    conn.close()
    return row["role"] if row else "player"


def load_player_data(name):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM player_data WHERE name = ? COLLATE NOCASE", (name,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def save_player_data(player):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE player_data SET
            gold               = ?,
            inventory          = ?,
            equipped_items     = ?,
            strength           = ?,
            agility            = ?,
            intelligence       = ?,
            vitality           = ?,
            level              = ?,
            xp                 = ?,
            stat_points        = ?,
            bonus_attack       = ?,
            bonus_defense      = ?,
            hp                 = ?,
            mp                 = ?,
            current_room       = ?,
            respawn_point      = ?,
            quests             = ?,
            quest_items        = ?,
            received_npc_items = ?
        WHERE name = ?
    """, (
        player.gold,
        json.dumps(player.inventory),
        json.dumps(player.equipped_items),
        player.strength,
        player.agility,
        player.intelligence,
        player.vitality,
        player.level,
        player.xp,
        player.stat_points,
        player.bonus_attack,
        player.bonus_defense,
        player.hp,
        player.mp,
        player.current_room,
        player.respawn_point,
        json.dumps(player.quests),
        json.dumps(player.quest_items),
        json.dumps(list(player.received_npc_items)),
        player.name,
    ))
    conn.commit()
    conn.close()


def reset_password(name, new_password):
    pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE accounts SET password_hash = ? WHERE name = ? COLLATE NOCASE",
        (pw_hash, name),
    )
    conn.commit()
    conn.close()


def update_last_login(name):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE accounts SET last_login = datetime('now') WHERE name = ? COLLATE NOCASE",
        (name,),
    )
    conn.commit()
    conn.close()
