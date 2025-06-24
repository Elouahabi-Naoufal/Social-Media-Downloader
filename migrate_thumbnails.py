#!/usr/bin/env python3
import sqlite3

# Update blogs table for binary thumbnails
conn = sqlite3.connect('downloads.db')
cursor = conn.cursor()

try:
    # Drop old thumbnail column and add new ones
    cursor.execute("ALTER TABLE blogs DROP COLUMN thumbnail;")
    cursor.execute("ALTER TABLE blogs ADD COLUMN thumbnail_data BLOB;")
    cursor.execute("ALTER TABLE blogs ADD COLUMN thumbnail_mime_type VARCHAR(100);")
    conn.commit()
    print("Successfully updated blogs table for binary thumbnails")
except sqlite3.OperationalError as e:
    if "no such column" in str(e):
        # Column doesn't exist, just add new ones
        try:
            cursor.execute("ALTER TABLE blogs ADD COLUMN thumbnail_data BLOB;")
            cursor.execute("ALTER TABLE blogs ADD COLUMN thumbnail_mime_type VARCHAR(100);")
            conn.commit()
            print("Successfully added thumbnail columns")
        except Exception as e2:
            print(f"Error adding columns: {e2}")
    else:
        print(f"Error: {e}")

conn.close()