# Logging Value Quoting Implementation Plan

## Audit Results

### Current State
- **55 uses of `error_msg=str(e)`** - All need quoting (exceptions contain spaces, colons, parens)
- **3 uses of `task=` field** - User-provided text with spaces
- **~20 uses of `path=` field** - URLs/paths with slashes and hyphens
- **No quoting implemented** - All values output as-is

### Actual Examples Found in Code

```python
# task_router.py:183
kvlog(logger, logging.NOTICE, automation='task_router', event='start', task=task_text)
# task_text = "Fix bug in leaving_home.py"
# Output: task=Fix bug in leaving_home.py
# Problem: Breaks parsing (where does task end?)

# All error handlers (55 occurrences)
kvlog(logger, logging.ERROR, automation='leaving_home', device='nest',
      action='set_temp', error_type=type(e).__name__, error_msg=str(e))
# error_msg might be: "HTTPSConnectionPool(host=api.nest.com, port=443): Max retries exceeded"
# Output: error_msg=HTTPSConnectionPool(host=api.nest.com, port=443): Max retries exceeded
# Problem: Colons, parens, commas break parsing

# routes.py:49
kvlog(logger, logging.ERROR, event='script_not_found', script=script_name, path=script_path)
# path = "/home/user/py_home/automations/leaving_home.py"
# Output: path=/home/user/py_home/automations/leaving_home.py
# Parsing works BUT inconsistent with other quoted values
```

### Real Exception Messages We'll See

From test run simulation:
- `HTTPSConnectionPool(host=api.nest.com, port=443): Max retries exceeded`
- `Connection timeout after 10s`
- `Authentication failed: Invalid credentials`
- `Device not found: 192.168.1.50`

All contain spaces, colons, or special characters.

---

## Standard Solution (RFC 5424 + Common Practice)

### Quoting Rules

**Quote values containing ANY of:**
- Space: ` `
- Double quote: `"`
- Equals: `=`
- Colon: `:`
- Newline: `\n`
- Tab: `\t`

**Escape within quoted values:**
- Backslash: `\` → `\\`
- Double quote: `"` → `\"`

**Result:**
- Simple values: `status=200` (no quotes)
- Complex values: `error_msg="Connection timeout after 10s"`
- With quotes: `task="Fix \"critical\" bug"`

---

## Implementation

### Single File Change

**File:** `lib/logging_config.py`
**Lines changed:** ~15 lines (add helper function, modify kvlog)

### Code Change

```python
def _format_value(v):
    """
    Format value for key=value logging with RFC 5424-compatible quoting.

    Simple values (no special chars): returned as-is
    Complex values: quoted and escaped

    Examples:
        200 → 200
        "OK" → OK
        "Connection timeout" → "Connection timeout"
        'Say "hello"' → "Say \"hello\""
    """
    s = str(v)

    # Check if quoting is needed
    needs_quotes = any(c in s for c in ' ":=\n\t')

    if needs_quotes:
        # Escape backslashes and quotes (RFC 5424 compatible)
        s = s.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{s}"'

    return s


def kvlog(logger, level, **kwargs):
    """
    Log structured key=value pairs with automatic quoting.

    Usage:
        kvlog(logger, logging.NOTICE, automation='leaving_home', event='start')
        kvlog(logger, logging.INFO, device='nest', action='set_temp', result='ok', duration_ms=234)
        kvlog(logger, logging.ERROR, device='nest', error_type='ConnectionError', error_msg='timeout: failed after 10s')

    Args:
        logger: Python logger instance
        level: Log level (DEBUG, INFO, NOTICE, WARNING, ERROR, CRITICAL)
        **kwargs: Key-value pairs to log

    Notes:
        - Values with spaces/special chars are automatically quoted
        - Quotes and backslashes within values are escaped
        - Simple values (numbers, single words) stay unquoted for readability
    """
    msg = ' '.join(f'{k}={_format_value(v)}' for k, v in kwargs.items())
    logger.log(level, msg)
```

---

## Testing Strategy

### Test Cases

```python
# Test 1: Simple values (no change)
kvlog(logger, INFO, status=200, method='GET')
# Output: status=200 method=GET

# Test 2: Values with spaces (quoted)
kvlog(logger, ERROR, error_msg='Connection timeout after 10s')
# Output: error_msg="Connection timeout after 10s"

# Test 3: Values with colons (quoted)
kvlog(logger, ERROR, error_msg='HTTPSConnectionPool(host=api.nest.com, port=443): Max retries')
# Output: error_msg="HTTPSConnectionPool(host=api.nest.com, port=443): Max retries"

# Test 4: Values with quotes (quoted and escaped)
kvlog(logger, INFO, task='Fix "critical" bug in parser')
# Output: task="Fix \"critical\" bug in parser"

# Test 5: Paths (usually no special chars needing quotes)
kvlog(logger, ERROR, path='/automation/leaving-home')
# Output: path=/automation/leaving-home (no quotes needed, no spaces)

# Test 6: Mixed
kvlog(logger, NOTICE, automation='test', event='start', dry_run=False, task='Review PR #123')
# Output: automation=test event=start dry_run=False task="Review PR #123"
```

### Parsing Verification

```bash
# After fix, these should work:
grep 'error_msg=' test.log | grep -o 'error_msg="[^"]*"' | cut -d'"' -f2
grep 'task=' test.log | grep -o 'task="[^"]*"' | cut -d'"' -f2

# Simple values still work as before:
grep 'status=' test.log | awk -F'status=' '{print $2}' | awk '{print $1}'
```

---

## Implementation Steps

### Step 1: Update lib/logging_config.py
- Add `_format_value()` helper function (10 lines)
- Update `kvlog()` to use `_format_value()` (1 line change)
- Update docstring with quoting behavior

### Step 2: Test with edge cases
- Create test script with all test cases above
- Verify output format matches expected
- Test parsing with grep/awk

### Step 3: Run existing test suite
- Verify no breakage (29/30 tests should still pass)
- Review new log output format
- Confirm readability

### Step 4: Update documentation
- Add quoting behavior to docs/LOGGING.md
- Update query examples if needed
- Add parsing examples for quoted values

### Step 5: Commit
- Commit message: "Add RFC 5424-compatible value quoting to structured logging"
- Include before/after examples in commit message

---

## Impact Analysis

### What Changes in Logs

**Before:**
```
2025-10-08 15:20:33 test[1234] ERROR automation=leaving_home device=nest action=set_temp error_type=ConnectionError error_msg=HTTPSConnectionPool(host=api.nest.com, port=443): Max retries exceeded
```

**After:**
```
2025-10-08 15:20:33 test[1234] ERROR automation=leaving_home device=nest action=set_temp error_type=ConnectionError error_msg="HTTPSConnectionPool(host=api.nest.com, port=443): Max retries exceeded"
```

**Differences:**
- Complex values now have quotes
- Simple values unchanged (automation=leaving_home stays as-is)
- More parseable with standard tools

### Backward Compatibility

**Existing grep queries:**
- ✅ `grep "automation=leaving_home"` - Still works
- ✅ `grep "status=200"` - Still works
- ✅ `grep "error_msg="` - Still works (finds both quoted and unquoted)

**New parsing capabilities:**
- ✅ Can now extract full error messages with spaces
- ✅ Can parse task text properly
- ✅ Compatible with log aggregation tools

### Performance Impact

**Minimal:**
- One conditional check per value (any() with 5 characters)
- String replacement only when quotes needed
- Estimated: <1 microsecond overhead per kvlog call
- Negligible for our use case (~10 log calls per automation run)

---

## Alternative Considered: Always Quote

### Option: Quote ALL values
```python
# Always quote everything
msg = ' '.join(f'{k}="{v}"' for k, v in kwargs.items())
```

**Pros:**
- Simpler code (no conditional)
- Uniform format
- Easier parsing (always look for quotes)

**Cons:**
- Less readable: `status="200" method="GET"` vs `status=200 method=GET`
- Not standard practice (wastes bytes on simple values)
- Doesn't match journalctl output style

**Decision:** Quote only when needed (better readability + standard practice)

---

## Risk Assessment

### Low Risk
- Single file change (lib/logging_config.py)
- Backward compatible (existing queries still work)
- No changes to call sites (55 error_msg uses stay as-is)
- Tested before deploy

### Mitigation
- Test suite verification (29/30 tests)
- Manual testing of edge cases
- Gradual rollout (can revert single file if issues)

---

## Success Criteria

1. ✅ All 55 error_msg values properly quoted
2. ✅ Task text with spaces parseable
3. ✅ Simple values (status, method, device) stay unquoted
4. ✅ Test suite passes (29/30)
5. ✅ grep/awk parsing works for complex values
6. ✅ No performance degradation
7. ✅ Logs remain human-readable

---

## Estimated Time

- Code changes: 15 minutes
- Testing: 15 minutes
- Documentation: 10 minutes
- Commit: 5 minutes

**Total: 45 minutes**
