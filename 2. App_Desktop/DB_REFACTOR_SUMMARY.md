# Database Refactoring Summary - Short-Lived Connections Architecture

## Problem Identified
SQLite database was getting locked frequently because:
- Background threads (dashboard updates every 2s, sensor polling) opened connections and kept them open
- SELECT queries with open connections blocked subsequent writes from UI threads
- Global write lock alone couldn't prevent contention from long-lived read connections

## Solution Implemented
Complete refactoring of DBManager to use **short-lived context manager connections** for ALL operations.

### Key Changes

#### 1. **Context Manager Support for All Connections**
```python
# Before:
conn = self.connect()
cursor = conn.cursor()
cursor.execute(...)
conn.close()

# After:
with self.connect() as conn:
    cursor = conn.cursor()
    cursor.execute(...)
# Connection automatically closes
```

#### 2. **All SELECT Operations (READ) - Auto-close**
Refactored all read operations to use context managers:
- `check_login()` - Login validation
- `get_setting()` - Configuration retrieval
- `get_all_monthly_tickets()` - Monthly ticket listing
- `get_all_parking_slots()` - Parking map data
- `get_parking_statistics()` - Dashboard statistics (called every 2 seconds)
- `get_parking_history()` - History page data
- `get_all_users()` - User management
- `get_user_permissions()` - Permission lookup
- `has_permission()` - Permission checking
- `get_revenue_by_date_range()` - Revenue calculations
- And 10+ more read operations

**Benefit**: Connections close immediately after query execution, freeing up SQLite locks.

#### 3. **All WRITE Operations (INSERT/UPDATE/DELETE) - Serialized + Auto-close**
Refactored all write operations with global lock AND context managers:
- `save_setting()` - Configuration updates
- `add_monthly_ticket()` - Add monthly parking pass
- `delete_monthly_ticket()` - Remove parking pass
- `extend_monthly_ticket()` - Extend parking pass
- `update_slot_status()` - Sensor updates
- `record_entry()` - Vehicle entry (with dedup check)
- `record_exit()` - Vehicle exit
- `add_user()` - User creation (with retry)
- `delete_user()` - User deletion
- `set_user_permissions()` - Permission updates
- `add_user_permission()` / `remove_user_permission()` - Permission management

**Architecture**:
```python
with _db_write_lock:  # Global RLock serializes writes
    with self.connect() as conn:  # Short-lived connection
        cursor = conn.cursor()
        cursor.execute(...)
        conn.commit()
    # conn.close() automatic
```

#### 4. **Two-Layer Retry Strategy**
**Layer 1 (SQLite Internal)**: 
- `PRAGMA busy_timeout=60000` - SQLite auto-retries for 60 seconds
- Applied during `_init_pragma()` at startup

**Layer 2 (Python Application)**:
- `_execute_with_retry()` helper with exponential backoff
- `max_retries=5` (increased from 3)
- `initial_wait=0.05s` (decreased from 0.1s) → exponential: 0.05 → 0.1 → 0.2 → 0.4 → 0.8s
- Applied to all write operations

#### 5. **Connection Timeout Optimization**
- Increased from: `timeout=30.0s`
- Increased to: `timeout=60.0s`
- Applied in both `_init_pragma()` and `connect()` methods
- Gives SQLite more time to acquire locks during high contention

### Methods Refactored: 90+ methods across categories

**Dashboard/Statistics (Heavy traffic - 2s interval)**:
- `get_parking_statistics()` - Now closes immediately after execution
- `get_available_slots_for_guests()` - Efficient short query

**Monthly Ticket Management**:
- `get_all_monthly_tickets()` - List with optional search
- `add_monthly_ticket()` - Create with slot reservation
- `get_monthly_ticket_info()` - Lookup by card_id
- `get_ticket_detail()` - Get ticket data

**Parking Operations**:
- `find_available_slot()` - Find empty parking space
- `record_entry()` - Vehicle entry recording
- `record_exit()` - Vehicle exit + slot liberation
- `get_parking_session()` - Session lookup

**User Management**:
- `get_all_users()` - List all staff
- `add_user()` - Create new user
- `delete_user()` - Remove user
- `get_user_permissions()` - List permissions
- `set_user_permissions()` - Update all permissions

**History & Reporting**:
- `get_parking_history()` - Filtered query (largest result set)
- `get_revenue_by_date_range()` - Revenue reporting

## Expected Improvements

### Before Refactoring:
```
[DB-RETRY] Database locked, retry 1/3 after 0.10s...
[DB-RETRY] Database locked, retry 2/3 after 0.20s...
[DB-RETRY] Database locked, retry 3/3 after 0.40s...
```
Occurring frequently due to:
- Kept-open read connections blocking writes
- 2-second dashboard timer creating connection pools
- Sensor polling holding connections

### After Refactoring:
- **Significantly reduced lock contention** - reads release locks immediately
- **Dashboard updates (2s interval) now non-blocking** - short-lived queries
- **Concurrent writes safer** - global RLock + shorter lock hold time
- **Better timeout handling** - 60s SQLite + 5 retries in Python

## Database Configuration Summary

**SQLite PRAGMAs** (Set once in `_init_pragma()`):
```python
PRAGMA journal_mode=WAL                  # Write-Ahead Logging for concurrency
PRAGMA synchronous=NORMAL                # Balance speed & safety
PRAGMA cache_size=10000                  # 10K page cache
PRAGMA temp_store=MEMORY                 # Temporary tables in RAM
PRAGMA busy_timeout=60000                # Auto-retry for 60s on lock
```

**Connection Parameters**:
```python
timeout=60.0                             # 60s socket timeout
check_same_thread=False                  # Allow multi-threaded access
```

**Retry Logic**:
```python
max_retries=5                            # Up to 5 attempts
initial_wait=0.05s                       # Start with 50ms
exponential_backoff=2x                   # Double each attempt
```

## Testing Recommendations

1. **Monitor log output**:
   - Look for fewer `[DB-RETRY]` messages
   - Check that `[STATS]` updates appear regularly without errors

2. **Stress test**:
   - Leave dashboard refresh running (2s interval)
   - Add/delete users in parallel
   - Record vehicle entries/exits
   - Check if operations still succeed

3. **Performance**:
   - Dashboard should remain responsive
   - Statistics should update every 2s without delays
   - User operations should complete in <2s

## Files Modified
- `core/db_manager.py` - Complete refactor (886 lines)
- Database queries now use context managers throughout
- No API changes - all method signatures remain compatible

## Backward Compatibility
✅ All changes are internal to DBManager
✅ No changes to method signatures
✅ No changes to return types
✅ Existing error handling preserved
✅ Logging messages enhanced for debugging

---
**Status**: Refactoring complete. Ready for testing with reduced database lock frequency expected.
