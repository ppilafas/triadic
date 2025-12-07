# Auto-Run Logic Issues Analysis

## Critical Problems Identified

### Issue 1: Blocking `time.sleep()` Inside Fragment
**Location**: `app.py` lines 295-301

**Problem**:
- `time.sleep()` is called INSIDE `@st.fragment` decorated function
- This blocks the entire fragment execution
- Fragment is supposed to be non-blocking for performance
- After sleep, `st.rerun()` is called, but this happens inside fragment context

**Impact**: High - Can cause UI freezing and unpredictable behavior

### Issue 2: Execution Order Mismatch
**Location**: `app.py` lines 235-301

**Problem**:
1. `should_execute_auto` is calculated at line 235-239 (BEFORE container)
2. Turn is executed at line 287-290 (INSIDE container)
3. Delay check happens at line 295-301 (AFTER container, but still in fragment)
4. The check at line 295 uses `should_execute_auto` which was calculated BEFORE execution
5. After `execute_turn()` runs, `turn_in_progress` becomes `True`
6. But the delay check at line 295 checks `not turn_in_progress`, which will be `False` after execution

**Impact**: Critical - Auto-run won't continue because the delay check fails

### Issue 3: No Immediate Rerun After Execution
**Location**: `app.py` line 290

**Problem**:
- `execute_turn()` is called but there's no immediate `st.rerun()` to show streaming
- The delay happens first, then rerun
- User won't see streaming until after delay completes

**Impact**: Medium - Poor UX, streaming not visible

### Issue 4: Fragment Context for Blocking Operations
**Location**: `app.py` line 187 (`@st.fragment`)

**Problem**:
- Fragment is meant for isolated, non-blocking UI updates
- Blocking `time.sleep()` defeats the purpose
- Can cause fragment to not update properly

**Impact**: High - Fragment behavior becomes unpredictable

## Root Cause

The original working implementation had `time.sleep()` OUTSIDE the fragment, but the current code has it INSIDE. Additionally, the execution flow is:

1. Calculate `should_execute_auto` (before container)
2. Execute turn (inside container) - sets `turn_in_progress = True`
3. Check delay (after container) - but `turn_in_progress` is now `True`, so condition fails

## Solution

The delay check should happen AFTER `execute_turn()` completes and `turn_in_progress` is cleared. The flow should be:

1. Check if auto-run should execute
2. Execute turn (sets `turn_in_progress = True`, then clears it when done)
3. After turn completes, wait for delay
4. Rerun to continue

But the current code checks the delay condition BEFORE the turn completes, so it never triggers.

