# Changelog

All notable changes to argdec will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1]

### Changed

- **Project renamed to `argdec`** to differentiate from an earlire version of my project which was pushed to pypi by another person, and to emphasize the use of decorators in `argdec` to configure `argparse`.

## [0.2.0]

### Added
- **Comprehensive test suite** with 38 tests covering all functionality
  - Test coverage for decorators, metaclass, Commander variants, parsing, edge cases, and integration
  - 100% test pass rate
- **Custom exception hierarchy** for better error handling
  - `ArgDecError` - Base exception class
  - `InvalidCommandNameError` - For invalid command names
  - `DuplicateCommandError` - For duplicate command registration
  - `CommandExecutionError` - For command execution failures
- **Comprehensive docstrings** on all public APIs with examples
- **Full type hints** throughout the codebase using Python typing module
- **Logging infrastructure** using standard library `logging` module
  - Debug logging for command registration and parsing
- **Input validation** at metaclass and runtime levels
  - Command name validation
  - Duplicate command detection
  - Parent command validation
- **Configurable command prefix** via `_command_prefix` class attribute
  - Default remains `"do_"` for backward compatibility
  - Users can now use `cmd_`, `action_`, or any custom prefix
  - Includes filtering to exclude dunder methods and non-callables
- **Modern Python packaging** with `pyproject.toml`
  - Support for Python 3.7+
  - Development dependencies configuration
  - Tool configuration (pytest, ruff, mypy)
- **Build system** with Makefile
  - `make test` - Run test suite
  - `make coverage` - Run tests with coverage report
  - `make lint` - Run ruff linter
  - `make typecheck` - Run mypy type checker
  - `make all` - Run all checks
- **Example files**
  - `example_custom_prefix.py` - Demonstrates custom command prefix usage
- **Documentation**
  - `CODE_REVIEW.md` - Comprehensive code review analysis
  - `IMPLEMENTATION_SUMMARY.md` - Detailed implementation notes
  - `CHANGELOG.md` - This file

### Changed
- **Refactored `parse_subparsers` to be fully recursive**
  - Cleaner implementation following functional recursion pattern
  - Extracted `_ensure_parent_parser` helper method
  - Better separation of concerns
- **Fixed state management bug**
  - Moved `_argparse_structure` from class variable to instance variable
  - Prevents cross-contamination between Commander instances
- **Enhanced metaclass with validation**
  - Validates command names at class definition time
  - Checks for duplicates early
  - Only processes callable methods
  - Excludes dunder methods automatically
- **Improved error handling throughout**
  - Parser creation errors now have context
  - Command execution failures provide detailed messages
  - All exceptions maintain proper exception chaining

### Fixed
- **Lambda closure bug** in `_ensure_parent_parser`
  - Replaced problematic lambda with proper function object
  - Function is now picklable and has correct behavior
- **State isolation bug**
  - Each Commander instance now has isolated `_argparse_structure`
  - No more shared state between instances
- **Hard-coded command prefix**
  - Now configurable via `_command_prefix` class attribute

### Security
- Added input validation to prevent invalid command names
- Command name validation prevents injection-style attacks
- Duplicate detection prevents accidental command overwrites

## [0.1.0] - Initial Release

### Added
- Basic Commander class with metaclass-based command discovery
- `@option` decorator for adding argparse options
- `@option_group` for reusable option collections
- `arg` alias for `option` decorator
- Support for hierarchical commands via `_argparse_levels`
- Automatic command discovery via `do_` prefix
- Integration with Python's argparse module
- Default help and version flags
- Configurable default arguments
- Demo application showing usage

### Features
- Declarative command-line interface definition
- Automatic subcommand registration
- Hierarchical command structures (e.g., `python build static`)
- Option decorator stacking
- Reusable option groups

---

## Version Numbering

- **Major version (X.0.0)**: Incompatible API changes
- **Minor version (0.X.0)**: New features, backward compatible
- **Patch version (0.0.X)**: Bug fixes, backward compatible

---

## Upgrade Guide

### Migrating from 0.1.0 to 0.2.0

**Good news:** Version 0.2.0 is **fully backward compatible** with 0.1.0!

All existing code will continue to work without modifications. The changes are purely additive (new features) and internal improvements (bug fixes, better error handling).

#### What You Get Automatically
- Better error messages if something goes wrong
- Protection against state bugs (if you were creating multiple Commander instances)
- Input validation on command names

#### Optional New Features You Can Use

**Custom Command Prefix:**
```python
# Old way (still works)
class MyApp(Commander):
    def do_build(self, args):
        pass

# New way (optional)
class MyApp(Commander):
    _command_prefix = "cmd_"  # Use any prefix you want

    def cmd_build(self, args):
        pass
```

**Better Error Handling:**
```python
from argdec import ArgDecError, CommandExecutionError

try:
    app.cmdline()
except CommandExecutionError as e:
    print(f"Command failed: {e}")
except ArgDecError as e:
    print(f"Configuration error: {e}")
```

**Type Hints (if using mypy):**
All public APIs now have complete type hints, so mypy will provide better checking.

#### No Breaking Changes
- All existing decorators work the same (`@option`, `@option_group`, `@arg`)
- All Commander attributes work the same (`name`, `version`, `epilog`, etc.)
- Hierarchical commands (`_argparse_levels`) work identically
- The `do_` prefix still works as default

---

## Links

- [Repository](https://github.com/yourusername/argdec) <!-- Update with actual repo -->
- [Bug Reports](https://github.com/yourusername/argdec/issues) <!-- Update with actual repo -->
- [Original Recipe](http://code.activestate.com/recipes/576935-argdec-declarative-interface-to-argparse)

---

## Contributors

Thanks to all contributors who helped make argdec better!

<!-- Add contributors as project grows -->
