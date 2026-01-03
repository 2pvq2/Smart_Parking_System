#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test user creation functionality"""

from core.db_manager import DBManager
from database import hash_password

db = DBManager()

# Test: Add a new user
result = db.add_user(
    username='testuser999',
    password=hash_password('pass123'),
    full_name='Test User',
    role='STAFF'
)

print(f'Add user result: {result}')

# Test: Check if we can login with the new user
login_result = db.check_login('testuser999', 'pass123')
print(f'Login result: {login_result}')

# Clean up
users = db.get_all_users()
for u in users:
    if u[1] == 'testuser999':
        deleted = db.delete_user(u[0])
        print(f'Test user deleted: {deleted}')
