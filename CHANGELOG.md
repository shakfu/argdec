# Changelog

All notable changes to argdec will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

### Changed

- Build backend switched from setuptools to `uv_build`. The wheel and sdist
  contents are unchanged apart from `LICENSE`, which is now declared via
  `license-files` and shipped in `dist-info/licenses/`.
- **Minimum Python is now 3.10.** 3.9 reached end of life in October 2025 and
  the dev toolchain (mypy 2.x, twine 7.x) no longer supports it. Annotations
  in `argdec` now use the `X | None` union syntax and import `Callable` from
  `collections.abc`.
- Dev dependencies updated to mypy 2.3.1, pytest-cov 7.1.0, ruff 0.16.6 and
  twine 7.0.0. Ruff's `target-version` is now `py310`.
- Python 3.14 is now declared as supported and covered by CI.

## [0.3.0]

A correctness release. Four defects found in review made hierarchical and
inherited commands unreliable; fixing them required small behavioural changes,
so this is a minor version bump rather than a patch.

### Fixed

- **Commands are now inherited.** `MetaCommander` scanned only the new class's
  own namespace and then overwrote `_argparse_subcmds`, so subclassing a
  `Commander` subclass silently discarded every command defined by the base.
  Commands now accumulate down the MRO, and a subclass may override an
  inherited command by redefining the method. `_command_prefix` is inherited
  too, which previously reverted to `do_` in subclasses.
- **Sibling command branches no longer collide.** The hierarchy was keyed by
  bare path segment, so `do_build_test_x` and `do_deploy_test_y` fought over
  `test`: one command was grafted onto the wrong parent and became unreachable
  (`error: invalid choice: 'test'`). Keys are now full dotted paths.
- **`cmdline()` may be called more than once.** Hierarchy state persisted across
  calls while the parser was rebuilt each time, so a second call raised
  `ArgDecError: conflicting subparser`. State is now reset per build.
- **`_argparse_levels` honours its value.** It was documented as a depth count
  but implemented as an on/off switch — any non-zero value nested on every
  underscore. A name is now split on at most `_argparse_levels` underscores.
- **Subcommand help shows defaults.** `ArgumentDefaultsHelpFormatter` was set
  only on the root parser, where no options live, so defaults were never shown.
- **Leaf commands no longer advertise an empty subcommands section.** Child
  subparsers are created lazily, only when a deeper command needs them.
- **Command name validation catches malformed names at class-definition time.**
  `do__foo` and `do_foo_` passed validation and then failed later with a
  misleading `Invalid parent command name: ''`. Each segment is now validated,
  and the error names the configured prefix rather than hard-coding `do_`.
- **`LICENSE` contained GPL-3.0 text** while the package metadata and README
  declared MIT. Replaced with the MIT license text.
- **Author email** was the placeholder `me@example.com`.

### Added

- **`cmdline(argv=None)`** accepts an explicit argument list instead of always
  reading `sys.argv`, for tests and embedding.
- **`build_parser()`** exposes the configured `ArgumentParser` without executing.
- **PEP 561 support** — the module is now a package shipping a `py.typed`
  marker, so downstream type checkers can see the annotations. The import path
  is unchanged.
- **`__all__`** declaring the public API.
- **Continuous integration** — GitHub Actions running tests on Python 3.9-3.13
  plus lint, typecheck, coverage, and a distribution check.
- **`[project.urls]`** metadata for the PyPI page.
- **42 new tests** (43 -> 85) covering inheritance, branch isolation, hierarchy
  depth, instance reuse, parent-command help, help formatting, name validation,
  undocumented commands, standalone `MetaCommander` use, parser-construction
  failures, and smoke tests for the shipped examples.
- **100% statement and branch coverage**, enforced by `fail_under = 100`. Line
  coverage alone sat at 94% while every defect fixed in this release lived in a
  covered line, so branch coverage is now measured too and anything excluded
  must carry a `pragma: no cover` explaining why it is unreachable.
- **`make fix`** applies ruff's fixes; `make lint` is now read-only, so
  `make all` no longer rewrites source as a side effect.
- **`make distclean`** removes the virtualenv. `make clean` no longer does,
  which previously tore down the environment midway through `make all`.
- **`archive/README.md`** noting that the archived original is unmaintained.

### Changed

- **Invoking an application with no subcommand** prints help to stderr and exits
  with status 2 (the argparse convention) instead of raising
  `CommandExecutionError`. **Breaking** for callers catching that exception.
- **Invoking an intermediate command** with no subcommand prints its help and
  exits 2, instead of silently succeeding.
- **`Commander.name` now sets the program name** in usage output; it was
  documented and set in every example but read nowhere. Its default changed from
  `"app name"` to `""` (meaning argparse's default, the script filename).
  **Breaking** for anyone reading the old default.
- **Multi-line docstrings** render properly: the first line becomes the short
  help in command listings, the full docstring the subcommand description.
  Commands with no docstring are handled without error.
- **Flat and hierarchical commands share one registration path**, removing a
  branch in `build_parser` that made `_split_command`'s flat case dead code.
- **Intermediate command levels use a single help-printing function** rather
  than a placeholder whose body was never executed.
- **`add_parser` catches only what argparse raises**
  (`ArgumentError`, `TypeError`, `ValueError`) instead of every exception,
  while still naming the offending command, which argparse's own message omits.
- **Minimum Python is now 3.9**, matching the mypy configuration. 3.7 and 3.8
  were claimed in the classifiers but never tested and are both end-of-life.
- Tests no longer mutate global `sys.argv`.

## [0.2.2]

### Added

- **new error condition tests** improving coverage from 88% to 94%
  - `test_empty_command_name_raises_error`
  - `test_invalid_identifier_raises_error`
  - `test_command_execution_failure`
  - `test_invalid_parent_command_name`
  - `test_no_command_specified`

### Fixed

- **Documentation placeholders** in README.md
  - Updated installation instructions (removed "Coming soon to PyPI")
  - Fixed example file reference path
- **Type checking** compatibility with mypy 1.4+
  - Updated `python_version` to 3.9 (mypy dropped 3.7 support)
  - Added proper type parameters to generic types

## [0.2.1]

### Changed

- **Project renamed to `argdec`** to differentiate from an earlier version of the project which was pushed to pypi by another person, and to emphasize the use of decorators in `argdec` to configure `argparse`.
- **Updated packaging** for PyPI publication
  - SPDX license format (`license = "MIT"`)
  - Added `[tool.setuptools]` configuration
  - Added Python 3.13 to classifiers
  - Added Makefile targets: `build`, `check`, `publish`, `publish-test`

## [0.2.0]

### Added

- **Comprehensive test suite** with 43 tests covering all functionality
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

### Validation

> Corrected in 0.3.0: this section was originally headed "Security" and claimed
> the validation "prevents injection-style attacks". It does not. Command names
> come from Python method identifiers in the developer's own source, never from
> user input, so there is no injection surface. The checks catch developer
> mistakes at class-definition time.

- Added input validation to reject invalid command names
- Duplicate detection to prevent accidental command overwrites

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

- [Repository](https://github.com/shakfu/argdec)
- [Bug Reports](https://github.com/shakfu/argdec/issues)
- [PyPI](https://pypi.org/project/argdec/)
- [Original Recipe](http://code.activestate.com/recipes/576935-argdeclare-declarative-interface-to-argparse)

---

## Contributors

Thanks to all contributors who helped make argdec better!

<!-- Add contributors as project grows -->
