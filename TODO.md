# TODO

## Critical

## High

## Medium

## Low

- [x] A `%` in `Commander.version` crashes `--version` `version = '1.0-100%'`: `cmdline(['--version'])` raises `ArgDecError: Unexpected error in cmdline: incomplete format`. Cause: `'%(prog)s ' + self.version` is %-formatted by argparse unescaped (argdec.py:509-510).

- [x] A child command is unreachable under a parent that takes a positional `_argparse_levels = 1`, `@option('name')` on `do_test`, and `do_test_unit`: `test unit` runs `do_test` with `name='unit'`. `do_test_unit` is reachable only as `test <name> unit`, and nothing fails at build time. Cause: the parent's parser is reused and its subparsers are added after its positionals (argdec.py:391-421).

- [ ] A child command's option defaults overwrite a parent option with the same dest `_argparse_levels = 1`; `do_test` and `do_test_unit` both declare `--verbose` (`store_true`). `test --verbose unit` runs `do_test_unit` with `verbose=False`; `test unit --verbose` gives `True`. Cause: argparse copies the child namespace, defaults included, over the parent's. `option_group` encourages sharing options this way.

- [x] An option with dest `func` replaces the dispatch target `@option('--func')` on `do_f`: `f --func z` never runs `do_f` and raises `ArgDecError: Unexpected error in cmdline: 'str' object has no attribute '__name__'`. Cause: the handler is stored as namespace attribute `func` (argdec.py:335), which user dests share.

- [x] `staticmethod` commands crash and `classmethod` commands are dropped `@staticmethod def do_s(a)`: `s` raises `CommandExecutionError: ... takes 1 positional argument but 2 were given`. `@classmethod def do_c(cls, a)` is not registered: `c` is an invalid choice. Cause: `callable()` on raw classdict values registers a `staticmethod` and skips a `classmethod` (argdec.py:203-204); dispatch calls `func(self, options)` (argdec.py:567).

- [x] An empty `_command_prefix` fails class creation on any `_helper` method `_command_prefix = ''` with `def _helper(self)` raises `InvalidCommandNameError: Invalid command name '_helper'`. Every other method also becomes a command. Cause: every name starts with `''`, only dunders are skipped (argdec.py:203-204), and `_helper` splits into an empty segment (argdec.py:217).

- [x] Flat mode rejects method names whose segments start with a digit (won't fix) With the default `_argparse_levels = 0`, `def do_py_3` raises `InvalidCommandNameError: Invalid command name 'py_3'` at class creation. Won't fix: names must stay valid when split, so they keep working if `_argparse_levels` changes. `test_invalid_identifier_raises_error`, `test_double_underscore_rejected` and `test_trailing_underscore_rejected` enforce this.
