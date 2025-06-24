#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('downloads.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE blogs ADD COLUMN thumbnail_style VARCHAR(20) DEFAULT 'cover';")
    cursor.execute("ALTER TABLE blogs ADD COLUMN thumbnail_height INTEGER DEFAULT 192;")
    conn.commit()
    print("Successfully added thumbnail style columns")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")

conn.close()