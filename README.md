# argdec

A decorator-based, declarative interface to Python's argparse for building hierarchical CLI applications.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

**argdec** (formerly [argdeclare](http://code.activestate.com/recipes/576935-argdeclare-declarative-interface-to-argparse)) provides two complementary approaches to configuring argparse:

1. **Decorator-based configuration** - Use `@option` and `@option_group` decorators to attach argparse arguments directly to command methods, keeping argument definitions co-located with the code that uses them.

2. **Declarative class structure** - Define CLI applications as classes where methods become commands, docstrings become help text, and class attributes configure parser behavior.

This combination eliminates boilerplate while preserving full access to argparse's capabilities.

## Features

- **Decorator-driven options** - Configure argparse arguments with `@option` and `@option_group` decorators directly on methods

- **Declarative command structure** - Methods prefixed with `do_` automatically become subcommands

- **Hierarchical commands** - Build nested command structures (e.g., `git remote add`) using underscore-separated method names, to a depth you control

- **Reusable option groups** - Define common options once, apply to multiple commands with `@option_group`

- **Full argparse compatibility** - All argparse features available through decorator parameters

- **Customizable** - Configure command prefix, hierarchy levels, and more

- **Inheritance-friendly** - Share commands across applications with a common base class

- **Typed** - Comprehensive test suite, inline type hints, explicit error handling

- **Single module** - One dependency-free file, so it can be vendored by copying `argdec.py`

## Installation

```bash
pip install argdec
```

Or install from source:

```bash
git clone https://github.com/shakfu/argdec.git
cd argdec
pip install .
```

argdec is a single module with no dependencies. To vendor it, copy `argdec.py` into your project instead of installing.

### Type checking

`argdec.py` is annotated. pyright and Pylance read those annotations from the installed source, so decorated commands keep their signatures:

```
App.do_build  ->  (self: App, args: Unknown) -> None
```

mypy honours inline annotations only from a package shipping a `py.typed` marker. PEP 561 has no equivalent for a top-level module, so mypy reports `import-untyped` and treats the module as `Any`. Silence it with an override:

```toml
[[tool.mypy.overrides]]
module = ["argdec"]
ignore_missing_imports = true
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

The `_argparse_levels` attribute controls how deep the command hierarchy goes. A method name is split on **at most** `_argparse_levels` underscores, so the leaf command keeps whatever underscores remain:

| `_argparse_levels` | `do_python_shared_pkg` is invoked as |
| --- | --- |
| `0` (default) | `app python_shared_pkg` |
| `1` | `app python shared_pkg` |
| `2` | `app python shared pkg` |

With `_argparse_levels = 0`:

```text
$ python3 demo.py
usage: builder [-h] [-v]  ...

builder: builds the py-js max external and python from source.

options:
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

With `_argparse_levels = 1`:

```text
$ python3 demo.py
usage: builder [-h] [-v]  ...

builder: builds the py-js max external and python from source.

options:
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

### Option Order

Stacked `@option` decorators register in source order, top to bottom. For positionals this sets the binding order:

```python
class App(Commander):
    @option("src")
    @option("dst")
    def do_cp(self, args):
        print(args.src, "->", args.dst)
```

```bash
$ python app.py cp a b
a -> b
```

`option_group` keeps the order of its arguments in the same way.

### Sharing Commands Between Applications

Commands are inherited, so a common base class can supply commands to several applications. Plain mixin classes, without `Commander` as a base, can supply `do_` methods too. A subclass may override an inherited command by redefining the method under the same name. Resolution follows the class MRO, as for any Python method.

```python
class CommonCommands(Commander):
    def do_version_info(self, args):
        """show build information"""
        print("...")

class MyApp(CommonCommands):
    """My application."""
    def do_build(self, args):
        """Build the project."""
        print("building")

# MyApp now has both `build` and `version_info`
```

### Driving the CLI Programmatically

`cmdline()` reads `sys.argv[1:]` by default, but accepts an explicit argument list -- useful in tests, in a REPL, or when embedding the CLI in a larger program. A `Commander` instance can be invoked repeatedly.

```python
app = MyApp()
app.cmdline(argv=["build", "--verbose"])
app.cmdline(argv=["build"])
```

`build_parser()` is also public, if you want the configured `argparse.ArgumentParser` without executing anything.

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

The prefix is inherited by subclasses. A subclass that sets its own prefix applies it to every class in its MRO, so commands defined under the old prefix are no longer inherited.

See `examples/custom_prefix.py` for more examples.

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

Argparse conventions are preserved: `--help`, `--version`, argparse errors and a missing subcommand all raise `SystemExit` rather than an `ArgDecError`. With no arguments, an application runs `default_args`; the default `['--help']` prints help and exits with status 0. An intermediate command with no subcommand, or an application with `default_args = []`, prints help to stderr and exits with status 2.

## Examples

Can be found in the `examples` directory:

- `basic.py` - Basic example application

- `hierarchical.py` - Full-featured example application

- `custom_prefix.py` - Custom prefix demonstrations

## Development

### Running Tests

```bash
make test           # Run test suite
make coverage       # Run with coverage report
make lint           # Run ruff linter (read-only)
make fix            # Run ruff linter and apply fixes
make typecheck      # Run mypy type checker
make all            # Run all checks
```

### Requirements

- Python 3.10+

- No external dependencies (uses stdlib only)

- Development: pytest, ruff, mypy (optional)

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Credits

Based on the original [argdeclare recipe](http://code.activestate.com/recipes/576935-argdeclare-declarative-interface-to-argparse) from ActiveState.

## Contributing

Contributions welcome! Please:

1. Run tests: `make test`

2. Check types: `make typecheck`

3. Lint code: `make lint`

4. Add tests for new features

The suite is kept at 100% statement and branch coverage (`make coverage`). Coverage once sat at 94% while several real defects were in covered lines. Add tests that check *behaviour* as well as lines.
