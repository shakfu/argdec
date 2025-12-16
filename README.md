# argdec

A decorator-based, declarative interface to Python's argparse for building hierarchical CLI applications.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

**argdec** (formerly [argdeclare](http://code.activestate.com/recipes/576935-argdeclare-declarative-interface-to-argparse)) provides two complementary approaches to configuring argparse:

1. **Decorator-based configuration** - Use `@option` and `@option_group` decorators to attach argparse arguments directly to command methods, keeping argument definitions co-located with the code that uses them.

2. **Declarative class structure** - Define CLI applications as classes where methods become commands, docstrings become help text, and class attributes configure parser behavior.

This combination eliminates boilerplate while preserving full access to argparse's capabilities.

## Features

- **Decorator-driven options** - Configure argparse arguments with `@option` and `@option_group` decorators directly on methods
- **Declarative command structure** - Methods prefixed with `do_` automatically become subcommands
- **Hierarchical commands** - Build nested command structures (e.g., `git remote add`) using underscore-separated method names
- **Reusable option groups** - Define common options once, apply to multiple commands with `@option_group`
- **Full argparse compatibility** - All argparse features available through decorator parameters
- **Customizable** - Configure command prefix, hierarchy levels, and more
- **Production ready** - Comprehensive test suite, type hints, error handling

## Installation

```bash
# Coming soon to PyPI
pip install argdec

# For now, use directly from source
git clone https://github.com/yourusername/argdec.git
cd argdec
```

## Quick Start

```python
from argdec import Commander, option

class MyApp(Commander):
    """My awesome CLI application."""
    name = 'myapp'
    version = '1.0'

    @option("-v", "--verbose", action="store_true", help="verbose output")
    def do_build(self, args):
        """Build the project."""
        print(f"Building... (verbose={args.verbose})")

if __name__ == '__main__':
    app = MyApp()
    app.cmdline()
```

```bash
$ python myapp.py build --verbose
Building... (verbose=True)
```

## Declarative Format Example

```python
#!/usr/bin/env python3

from argdec import Commander, option, option_group

# ----------------------------------------------------------------------------
# Commandline interface

common_options = option_group(
    option("--dump", action="store_true", help="dump project and product vars"),
    option("-d","--download",
           action="store_true",
           help="download python build/downloads"),
    option("-r", "--reset", action="store_true", help="reset python build"),
    option("-i","--install",
           action="store_true",
           help="install python to build/lib"),
    option("-b","--build",
           action="store_true",
           help="build python in build/src"),
    option("-c","--clean",
           action="store_true",
           help="clean python in build/src"),
    option("-z", "--ziplib", action="store_true", help="zip python library"),
    option("-p", "--py-version", type=str,
           help="set required python version to download and build"),
)

class Application(Commander):
    """builder: builds the py-js max external and python from source."""
    name = 'builder'
    epilog = ''
    version = '0.1'
    default_args = ['--help']
    _argparse_levels = 1


# ----------------------------------------------------------------------------
# python builder methods

    # def do_python(self, args):
    #     "download and build python from src"

    @common_options
    def do_python_static(self, args):
        """build static python"""
        print(args)

    @common_options
    def do_python_shared(self, args):
        """build shared python"""
        print(args)

    @common_options
    def do_python_shared_pkg(self, args):
        """build shared python to embed in package"""
        print(args)

    @common_options
    def do_python_framework(self, args):
        """build framework python"""
        print(args)

    @common_options
    def do_python_framework_pkg(self, args):
        """build framework python to embed in a package"""
        print(args)


# ----------------------------------------------------------------------------
# utility methods

    # def do_check(self, args):
    #     """check reference utilities"""
    #     print(args)

    @common_options    
    def do_check_log_day(self, args):
        """analyze log day"""
        print(args)

    @common_options    
    def do_check_log_week(self, args):
        """analyze log week"""
        print(args)

    @common_options
    def do_check_sys_month(self, args):
        """analyze sys month"""
        print(args)

    @common_options
    def do_check_sys_def(self, args):
        """analyze sys def"""
        print(args)

    @common_options
    def do_check_sys_xyz(self, args):
        """analyze sys xyz"""
        print(args)

    @common_options
    def do_test(self, args):
        """test suite"""
        print(args)


    @common_options
    def do_test_app(self, args):
        """test app"""
        print(args)

    @common_options
    def do_test_functions(self, args):
        """test functions"""
        print(args)

if __name__ == '__main__':
    app = Application()
    app.cmdline()
```

`with levels=0` gives:


```text
$ python3 demo.py
usage: demo.py [-h] [-v]  ...

builder: builds the py-js max external and python from source.

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit

subcommands:
  valid subcommands

                        additional help
    check_log_day       analyze log day
    check_log_week      analyze log week
    check_sys_def       analyze sys def
    check_sys_month     analyze sys month
    check_sys_xyz       analyze sys xyz
    python_framework    build framework python
    python_framework_pkg
                        build framework python to embed in a package
    python_shared       build shared python
    python_shared_pkg   build shared python to embed in package
    python_static       build static python
    test                test suite
    test_app            test app
    test_functions      test functions
```

`with levels=1` gives:

```text

$ python3 demo.py
usage: demo.py [-h] [-v]  ...

builder: builds the py-js max external and python from source.

optional arguments:
  -h, --help     show this help message and exit
  -v, --version  show program's version number and exit

subcommands:
  valid subcommands

                 additional help
    check        check commands
    python       python commands
    test         test suite
```

## Advanced Features

### Custom Command Prefix

By default, methods starting with `do_` become commands. You can customize this:

```python
class MyApp(Commander):
    _command_prefix = "cmd_"  # Use 'cmd_' instead of 'do_'

    def cmd_build(self, args):
        """Build the project."""
        pass

    def cmd_deploy(self, args):
        """Deploy the project."""
        pass
```

See `example_custom_prefix.py` for more examples.

### Error Handling

Version 0.2.0+ includes comprehensive error handling:

```python
from argdec import ArgDecError, CommandExecutionError

try:
    app.cmdline()
except CommandExecutionError as e:
    print(f"Command failed: {e}")
except ArgDecError as e:
    print(f"Configuration error: {e}")
```

## Examples

Can be found in the `examples` directory:

- `basic.py` - Basic example application
- `hierarchical.py` - Full-featured example application
- `custom_prefix.py` - Custom prefix demonstrations

## Development

### Running Tests

```bash
make test           # Run test suite (38 tests)
make coverage       # Run with coverage report
make lint           # Run ruff linter
make typecheck      # Run mypy type checker
make all            # Run all checks
```

### Requirements

- Python 3.7+
- No external dependencies (uses stdlib only)
- Development: pytest, ruff, mypy (optional)

## Version History

- **v0.2.1** (2025-12-16) - Renamed to `argdec`
- **v0.2.0** (2025-11-07) - Release with tests, type hints, error handling, and configurable prefix
- **v0.1.0** - Initial release with basic functionality

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Credits

Based on the original [argdec recipe](http://code.activestate.com/recipes/576935-argdec-declarative-interface-to-argparse) from ActiveState.

## Contributing

Contributions welcome! Please:
1. Run tests: `make test`
2. Check types: `make typecheck`
3. Lint code: `make lint`
4. Add tests for new features

```
