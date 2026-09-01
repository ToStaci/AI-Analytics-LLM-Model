import os
import sqlite3

def init_db():
    os.makedirs("data", exist_ok=True)
    db_path = "data/telemetry.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
 
    cursor.execute("DROP TABLE IF EXISTS player_matches")
    cursor.execute("DROP TABLE IF EXISTS weapon_stats")
 
    cursor.execute('''
    CREATE TABLE player_matches (
        match_id TEXT,
        player_id TEXT,
        map_name TEXT,
        duration_seconds INTEGER,
        kills INTEGER,
        deaths INTEGER,
        win BOOLEAN
    )
    ''')
 
    cursor.execute('''
    CREATE TABLE weapon_stats (
        match_id TEXT,
        weapon_name TEXT,
        damage_dealt REAL,
        shots_fired INTEGER,
        shots_hit INTEGER
    )
    ''')
 
    cursor.executemany('INSERT INTO player_matches VALUES (?, ?, ?, ?, ?, ?, ?)', [
        ('m1', 'player_101', 'Chernarus', 1200, 5, 2, True),
        ('m1', 'player_102', 'Chernarus', 1200, 2, 5, False),
        ('m2', 'player_101', 'Livonia', 900, 8, 1, True),
        ('m2', 'player_103', 'Livonia', 900, 1, 4, False),
        ('m3', 'player_104', 'Chernarus', 1500, 0, 1, False),
    ])

    cursor.executemany('INSERT INTO weapon_stats VALUES (?, ?, ?, ?, ?)', [
        ('m1', 'M4A1', 450.0, 120, 45),
        ('m1', 'AKM', 200.0, 50, 15),
        ('m2', 'M4A1', 750.0, 180, 70),
        ('m2', 'SVD', 300.0, 10, 8),
        ('m3', 'M4A1', 50.0, 30, 2),
    ])

    conn.commit()
    conn.close()
    print(f"Success: Database initialized and populated at {db_path}")

if __name__ == "__main__":
    init_db()