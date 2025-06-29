#!/usr/bin/env python3
"""Simple script to view the SQLite database contents."""

import sqlite3
import os
from datetime import datetime

def view_database():
    db_path = 'web-app/instance/llm_seo.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT id, email, name, created_at FROM user")
    users = cursor.fetchall()
    
    print("=== USER DATA ===")
    print(f"Total users: {len(users)}")
    print()
    
    for user in users:
        user_id, email, name, created_at = user
        print(f"ID: {user_id}")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Created: {created_at}")
        print("-" * 30)
    
    conn.close()

if __name__ == "__main__":
    view_database()
