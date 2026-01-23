# Linting & Code Quality

This project uses **Ruff** for comprehensive linting and formatting. It catches unused imports, style issues, performance problems, and 15+ categories of code quality issues.

## Quick Start

### Check for issues
```bash
stockrhythm lint
```

### Auto-fix issues
```bash
stockrhythm lint --fix
```

### Show detailed statistics
```bash
stockrhythm lint --stats
```

### Lint specific path
```bash
stockrhythm lint --path packages/stockrhythm-sdk/src
```

## What Gets Checked

| Category | Code | Example |
|----------|------|---------|
| **Unused Imports** | F401 | `import os  # never used` |
| **Undefined Names** | F821 | `print(undefined_var)` |
| **Import Sorting** | I001 | Mixed import order |
| **Style Issues** | E, W | Trailing whitespace, line breaks |
| **Async/Await** | ASYNC | Missing awaits, blocking calls in async |
| **Datetime** | DTZ | Timezone-naive datetime objects |
| **Performance** | PERF | Manual list comprehensions, anti-patterns |
| **Simplification** | SIM | Unnecessary conditionals, complex logic |
| **Modern Python** | UP | Old-style type hints, deprecated imports |
| **Builtins** | A | Shadowing Python builtins |
| **Comprehensions** | C4 | Inefficient comprehensions |
| **Print Statements** | T20 | Debug print() calls (caught in production code) |
| **Pytest** | PT | Pytest best practices |
| **Logging** | LOG | Logging best practices |

## Rules Overview

### Hard Errors (Must Fix)
- `F401` - Unused imports (clutters namespace)
- `F821` - Undefined names (runtime errors)
- `F841` - Unused variables (dead code)
- `E` series - Style/syntax (formatting issues)

### Warnings (Should Fix)
- `W291` - Trailing whitespace
- `W293` - Blank line with whitespace
- `DTZ001` - Timezone-naive datetime (can cause bugs with DST)
- `I001` - Unsorted imports (consistency)
- `T201` - Print statements in production code

### Modernization (Nice to Have)
- `UP006` - Use `list[...]` instead of `List[...]`
- `UP045` - Use `type | None` instead of `Optional[type]`
- `UP035` - Use `dict.get()` instead of deprecated patterns

## Configuration

Configuration is in `pyproject.toml` under `[tool.ruff]`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
    "E", "W", "F",  # Core errors
    "I",            # Import sorting
    "UP",           # Modern Python
    "ASYNC",        # Async best practices
    # ... 12+ more categories
]

ignore = [
    "E501",  # Line too long (let formatter decide)
    "A003",  # Builtin shadowing (common in classes)
]
```

### Per-File Ignores
- `tests/**` - Allows `T201` (print in tests)
- `**/conftest.py` - Allows `F401` (fixtures may import but not use)

## Pre-commit Hooks (Optional)

To automatically lint before commits:

```bash
pre-commit install
```

This will run ruff on every commit. Configured in `.pre-commit-config.yaml`.

## Exit Codes

- `0` - No issues found
- `1` - Issues found (non-blocking, use `--fix` to auto-fix)

## Auto-fixing

Run with `--fix` to automatically correct:
- Import sorting
- Trailing whitespace
- Blank line whitespace
- Unused imports
- F-string formatting
- Type hint modernization
- And 380+ other fixable issues

**Note**: Not all issues are auto-fixable. Review changes after running `--fix`.

## Common Issues & Solutions

### Issue: `F401 - unused-import`
```python
# ❌ Bad
import os  # never used
x = 1

# ✅ Good
x = 1
```

### Issue: `I001 - unsorted-imports`
```python
# ❌ Bad
from os import path
import sys
import asyncio

# ✅ Good
import asyncio
import sys
from os import path
```

### Issue: `DTZ001 - call-datetime-without-tzinfo`
```python
# ❌ Bad (non-deterministic across timezones)
now = datetime.datetime.now()

# ✅ Good
import datetime
now = datetime.datetime.now(datetime.timezone.utc)
```

### Issue: `T201 - print statement in production`
```python
# ❌ Bad (debug print in strategy)
def on_tick(self, tick):
    print(f"Price: {tick.price}")  # Allowed in tests only

# ✅ Good
def on_tick(self, tick):
    logger.info(f"Price: {tick.price}")
```

### Issue: `PERF401 - manual-list-comprehension`
```python
# ❌ Bad
items = []
for x in data:
    items.append(x * 2)

# ✅ Good
items = [x * 2 for x in data]
```

## Integration with Tools

- **IDE**: Most editors (VSCode, PyCharm) integrate with Ruff
- **CI/CD**: Add `stockrhythm lint` to your pipeline
- **Pre-commit**: Use `.pre-commit-config.yaml` for Git hooks
- **Format**: Ruff also handles formatting with `ruff format`

## Statistics

See current project state:
```bash
stockrhythm lint --stats
```

Typical output shows:
- Total errors found
- Fixable vs manual fixes
- Breakdown by rule category
