#!/usr/bin/env python3
import sqlite3

# Add thumbnail column to blogs table
conn = sqlite3.connect('downloads.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE blogs ADD COLUMN thumbnail VARCHAR(500);")
    conn.commit()
    print("Successfully added thumbnail column to blogs table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Thumbnail column already exists")
    else:
        print(f"Error: {e}")

conn.close()