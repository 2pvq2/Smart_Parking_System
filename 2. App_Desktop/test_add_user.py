#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test adding a new user"""

import sys
sys.path.insert(0, '.')

from core.db_manager import DBManager
from database import hash_password

# Reset the class variable to allow PRAGMA to be set again
DBManager._pragma_initialized = False

db = DBManager()

# Test add user
username = "test_user"
password = "test123"
full_name = "Test User"
role = "STAFF"

print(f"[TEST] Adding user: {username}")
ok, msg = db.add_user(
    username=username,
    password=hash_password(password),
    full_name=full_name,
    role=role
)

print(f"[RESULT] Success: {ok}, Message: {msg}")

if ok:
    # Test login
    print(f"[TEST] Testing login with {username}/{password}")
    user = db.check_login(username, password)
    if user:
        print(f"[LOGIN SUCCESS] User: {user}")
    else:
        print(f"[LOGIN FAILED]")
