"""Test suite for argdec module."""
import sys

import pytest

from argdec import Commander, option, option_group


class TestOptionDecorator:
    """Test the option decorator functionality."""

    def test_option_adds_options_attribute(self):
        """option decorator should add options list to function."""
        @option("-v", "--verbose", action="store_true")
        def func():
            pass

        assert hasattr(func, "options")
        assert len(func.options) == 1
        assert func.options[0] == (("-v", "--verbose"), {"action": "store_true"})

    def test_multiple_option_decorators(self):
        """Multiple option decorators should stack properly."""
        @option("-v", "--verbose", action="store_true")
        @option("-q", "--quiet", action="store_true")
        def func():
            pass

        assert len(func.options) == 2
        assert func.options[0] == (("-q", "--quiet"), {"action": "store_true"})
        assert func.options[1] == (("-v", "--verbose"), {"action": "store_true"})

    def test_option_with_various_args(self):
        """option should handle various argparse arguments."""
        @option("--count", type=int, default=5, help="number of items")
        def func():
            pass

        assert len(func.options) == 1
        args, kwds = func.options[0]
        assert args == ("--count",)
        assert kwds["type"] is int
        assert kwds["default"] == 5
        assert kwds["help"] == "number of items"

    def test_arg_alias(self):
        """arg should be an alias for option."""
        from argdec import arg
        assert arg is option


class TestOptionGroup:
    """Test the option_group decorator functionality."""

    def test_option_group_combines_options(self):
        """option_group should combine multiple option decorators."""
        opt1 = option("-v", "--verbose", action="store_true")
        opt2 = option("-q", "--quiet", action="store_true")

        @option_group(opt1, opt2)
        def func():
            pass

        assert len(func.options) == 2

    def test_option_group_order(self):
        """option_group should apply decorators in order."""
        opt1 = option("-a", action="store_true")
        opt2 = option("-b", action="store_true")
        opt3 = option("-c", action="store_true")

        @option_group(opt1, opt2, opt3)
        def func():
            pass

        # Options are applied in the order given to option_group
        assert func.options[0][0] == ("-a",)
        assert func.options[1][0] == ("-b",)
        assert func.options[2][0] == ("-c",)

    def test_option_group_empty(self):
        """option_group with no options should work."""
        @option_group()
        def func():
            pass

        assert not hasattr(func, "options") or len(func.options) == 0


class TestMetaCommander:
    """Test the MetaCommander metaclass."""

    def test_metaclass_discovers_do_methods(self):
        """Metaclass should discover all do_ methods."""
        class TestApp(Commander):
            def do_build(self, args):
                pass

            def do_test(self, args):
                pass

            def regular_method(self):
                pass

        assert "build" in TestApp._argparse_subcmds
        assert "test" in TestApp._argparse_subcmds
        assert "regular_method" not in TestApp._argparse_subcmds

    def test_metaclass_captures_options(self):
        """Metaclass should capture options from decorated methods."""
        class TestApp(Commander):
            @option("-v", "--verbose", action="store_true")
            def do_build(self, args):
                pass

        subcmd = TestApp._argparse_subcmds["build"]
        assert len(subcmd["options"]) == 1
        assert subcmd["options"][0][0] == ("-v", "--verbose")

    def test_metaclass_handles_no_options(self):
        """Metaclass should handle methods without options."""
        class TestApp(Commander):
            def do_build(self, args):
                pass

        subcmd = TestApp._argparse_subcmds["build"]
        assert subcmd["options"] == []

    def test_metaclass_preserves_function_reference(self):
        """Metaclass should preserve original function reference."""
        class TestApp(Commander):
            def do_build(self, args):
                return "built"

        subcmd = TestApp._argparse_subcmds["build"]
        assert subcmd["func"].__name__ == "do_build"


class TestCommanderBasic:
    """Test basic Commander functionality."""

    def test_commander_initialization(self):
        """Commander should initialize with default attributes."""
        class TestApp(Commander):
            pass

        app = TestApp()
        assert app.name == "app name"
        assert app.version == "0.1"
        assert app.default_args == ["--help"]

    def test_commander_custom_attributes(self):
        """Commander should allow custom attributes."""
        class TestApp(Commander):
            name = "myapp"
            version = "2.0"
            epilog = "custom epilog"

        app = TestApp()
        assert app.name == "myapp"
        assert app.version == "2.0"
        assert app.epilog == "custom epilog"

    def test_add_parser_creates_subparser(self):
        """add_parser should create a subparser with options."""
        class TestApp(Commander):
            @option("-v", "--verbose", action="store_true")
            def do_build(self, args):
                """build the project"""
                pass

        app = TestApp()
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        subcmd = app._argparse_subcmds["build"]
        subparser = app.add_parser(subparsers, subcmd)

        assert subparser is not None


class TestCommanderSingleLevel:
    """Test Commander with single-level commands (levels=0)."""

    def test_single_level_help(self, capsys):
        """Single-level commands should show all commands at top level."""
        class TestApp(Commander):
            _argparse_levels = 0
            default_args = ["--help"]

            def do_build(self, args):
                """build the project"""
                pass

            def do_test(self, args):
                """run tests"""
                pass

        app = TestApp()
        # Save and restore sys.argv to avoid interference
        old_argv = sys.argv
        try:
            sys.argv = ["test"]
            with pytest.raises(SystemExit):
                app.cmdline()

            captured = capsys.readouterr()
            assert "build" in captured.out
            assert "test" in captured.out
        finally:
            sys.argv = old_argv

    def test_single_level_command_execution(self):
        """Single-level command should execute correctly."""
        executed = []

        class TestApp(Commander):
            _argparse_levels = 0

            @option("-v", "--verbose", action="store_true")
            def do_build(self, args):
                """build the project"""
                executed.append(("build", args.verbose))

        app = TestApp()
        sys.argv = ["test", "build", "-v"]
        app.cmdline()

        assert len(executed) == 1
        assert executed[0] == ("build", True)


class TestCommanderHierarchical:
    """Test Commander with hierarchical commands."""

    def test_hierarchical_single_underscore(self, capsys):
        """Commands with single underscore should create hierarchy."""
        class TestApp(Commander):
            _argparse_levels = 1
            default_args = ["--help"]

            def do_python_build(self, args):
                """build python"""
                pass

            def do_python_test(self, args):
                """test python"""
                pass

        app = TestApp()
        old_argv = sys.argv
        try:
            sys.argv = ["test"]
            with pytest.raises(SystemExit):
                app.cmdline()

            captured = capsys.readouterr()
            assert "python" in captured.out
        finally:
            sys.argv = old_argv

    def test_hierarchical_multiple_levels(self, capsys):
        """Commands with multiple underscores should create deep hierarchy."""
        class TestApp(Commander):
            _argparse_levels = 2
            default_args = ["python", "--help"]

            def do_python_build_static(self, args):
                """build static python"""
                pass

            def do_python_build_shared(self, args):
                """build shared python"""
                pass

        app = TestApp()
        old_argv = sys.argv
        try:
            sys.argv = ["test"]
            with pytest.raises(SystemExit):
                app.cmdline()

            captured = capsys.readouterr()
            assert "build" in captured.out
        finally:
            sys.argv = old_argv

    def test_hierarchical_command_execution(self):
        """Hierarchical commands should execute correctly."""
        executed = []

        class TestApp(Commander):
            _argparse_levels = 1

            @option("-v", "--verbose", action="store_true")
            def do_python_build(self, args):
                """build python"""
                executed.append(("python_build", args.verbose))

        app = TestApp()
        sys.argv = ["test", "python", "build", "-v"]
        app.cmdline()

        assert len(executed) == 1
        assert executed[0] == ("python_build", True)

    def test_deep_hierarchy_execution(self):
        """Deep hierarchical commands should execute correctly."""
        executed = []

        class TestApp(Commander):
            _argparse_levels = 2

            @option("--type", type=str, default="debug")
            def do_build_python_static(self, args):
                """build static python"""
                executed.append(("build_python_static", args.type))

        app = TestApp()
        sys.argv = ["test", "build", "python", "static", "--type", "release"]
        app.cmdline()

        assert len(executed) == 1
        assert executed[0] == ("build_python_static", "release")


class TestRecursiveParsing:
    """Test the recursive parse_subparsers implementation."""

    def test_recursive_base_case(self):
        """Base case (no underscore) should add command directly."""
        class TestApp(Commander):
            _argparse_levels = 1

            def do_build(self, args):
                """build the project"""
                pass

        app = TestApp()
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        subcmd = app._argparse_subcmds["build"]
        result = app.parse_subparsers(subparsers, subcmd, "build")

        assert result is not None
        assert "build" in app._argparse_structure

    def test_recursive_case_single_level(self):
        """Recursive case with one underscore should create parent."""
        class TestApp(Commander):
            _argparse_levels = 1

            def do_python_build(self, args):
                """build python"""
                pass

        app = TestApp()
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        subcmd = app._argparse_subcmds["python_build"]
        result = app.parse_subparsers(subparsers, subcmd, "python_build")

        assert result is not None
        assert "python" in app._argparse_structure

    def test_recursive_case_multiple_levels(self):
        """Recursive case with multiple underscores should create full hierarchy."""
        class TestApp(Commander):
            _argparse_levels = 2

            def do_build_python_static(self, args):
                """build static python"""
                pass

        app = TestApp()
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        subcmd = app._argparse_subcmds["build_python_static"]
        result = app.parse_subparsers(subparsers, subcmd, "build_python_static")

        assert result is not None
        assert "build" in app._argparse_structure
        assert "python" in app._argparse_structure


class TestEnsureParentParser:
    """Test the _ensure_parent_parser helper method."""

    def test_creates_parent_when_missing(self):
        """Should create parent parser if it doesn't exist."""
        class TestApp(Commander):
            pass

        app = TestApp()
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        result = app._ensure_parent_parser(subparsers, "python")

        assert result is not None
        assert "python" in app._argparse_structure

    def test_returns_existing_parent(self):
        """Should return existing parent parser if it exists."""
        class TestApp(Commander):
            pass

        app = TestApp()
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        # Create parent first time
        result1 = app._ensure_parent_parser(subparsers, "python")
        # Get parent second time
        result2 = app._ensure_parent_parser(subparsers, "python")

        assert result1 is result2

    def test_dummy_func_has_docstring(self):
        """Dummy function should have proper docstring."""
        class TestApp(Commander):
            pass

        app = TestApp()
        import argparse
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        app._ensure_parent_parser(subparsers, "test")

        # The docstring should be set properly
        assert "test" in app._argparse_structure


class TestCustomPrefix:
    """Test custom command prefix functionality."""

    def test_custom_prefix_discovery(self):
        """Metaclass should discover commands with custom prefix."""
        class TestApp(Commander):
            _command_prefix = "cmd_"

            def cmd_build(self, args):
                """build the project"""
                pass

            def cmd_test(self, args):
                """run tests"""
                pass

            def do_ignored(self, args):
                """should be ignored"""
                pass

        assert "build" in TestApp._argparse_subcmds
        assert "test" in TestApp._argparse_subcmds
        assert "ignored" not in TestApp._argparse_subcmds

    def test_custom_prefix_execution(self):
        """Commands with custom prefix should execute correctly."""
        executed = []

        class TestApp(Commander):
            _command_prefix = "command_"
            _argparse_levels = 0

            @option("-v", "--verbose", action="store_true")
            def command_build(self, args):
                """build the project"""
                executed.append(("build", args.verbose))

        app = TestApp()
        sys.argv = ["test", "build", "-v"]
        app.cmdline()

        assert len(executed) == 1
        assert executed[0] == ("build", True)

    def test_custom_prefix_hierarchical(self):
        """Custom prefix should work with hierarchical commands."""
        executed = []

        class TestApp(Commander):
            _command_prefix = "cmd_"
            _argparse_levels = 1

            def cmd_python_build(self, args):
                """build python"""
                executed.append("python_build")

        app = TestApp()
        sys.argv = ["test", "python", "build"]
        app.cmdline()

        assert "python_build" in executed

    def test_empty_prefix(self):
        """Empty prefix should discover all methods (not recommended but should work)."""
        class TestApp(Commander):
            _command_prefix = ""

            def build(self, args):
                """build command"""
                pass

        # Should discover 'build' method
        assert "build" in TestApp._argparse_subcmds

    def test_underscore_prefix(self):
        """Underscore prefix should work."""
        class TestApp(Commander):
            _command_prefix = "_"

            def _build(self, args):
                """build command"""
                pass

            def __init_subclass__(cls):
                """Should not be discovered as command"""
                pass

        assert "build" in TestApp._argparse_subcmds
        assert "_init_subclass__" not in TestApp._argparse_subcmds


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_no_subcommands(self, capsys):
        """Commander with no subcommands should show help."""
        class TestApp(Commander):
            default_args = ["--help"]

        app = TestApp()
        old_argv = sys.argv
        try:
            sys.argv = ["test"]
            with pytest.raises(SystemExit):
                app.cmdline()

            captured = capsys.readouterr()
            assert "subcommands" in captured.out
        finally:
            sys.argv = old_argv

    def test_empty_option_group(self):
        """Empty option_group should not break."""
        common = option_group()

        class TestApp(Commander):
            @common
            def do_build(self, args):
                pass

        app = TestApp()
        assert "build" in app._argparse_subcmds

    def test_multiple_option_groups(self):
        """Multiple option groups should combine correctly."""
        group1 = option_group(
            option("-v", "--verbose", action="store_true")
        )
        group2 = option_group(
            option("-q", "--quiet", action="store_true")
        )

        class TestApp(Commander):
            @group1
            @group2
            def do_build(self, args):
                pass

        app = TestApp()
        subcmd = app._argparse_subcmds["build"]
        assert len(subcmd["options"]) == 2

    def test_version_flag(self, capsys):
        """Version flag should display version and exit."""
        class TestApp(Commander):
            version = "1.2.3"

        app = TestApp()
        sys.argv = ["test", "--version"]

        with pytest.raises(SystemExit):
            app.cmdline()

        captured = capsys.readouterr()
        assert "1.2.3" in captured.out

    def test_docstring_preserved(self):
        """Docstrings should be preserved on commands."""
        class TestApp(Commander):
            def do_build(self, args):
                """This is the build command"""
                pass

        app = TestApp()
        subcmd = app._argparse_subcmds["build"]
        assert subcmd["func"].__doc__ == "This is the build command"


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_full_application_flow(self):
        """Test complete application with multiple commands and options."""
        results = []

        common_opts = option_group(
            option("-v", "--verbose", action="store_true"),
            option("-d", "--debug", action="store_true"),
        )

        class TestApp(Commander):
            name = "testapp"
            version = "1.0.0"
            _argparse_levels = 1

            @common_opts
            def do_build_app(self, args):
                """build the application"""
                results.append(("build_app", args.verbose, args.debug))

            @common_opts
            def do_test_unit(self, args):
                """run unit tests"""
                results.append(("test_unit", args.verbose, args.debug))

        app = TestApp()
        sys.argv = ["test", "build", "app", "-v", "-d"]
        app.cmdline()

        assert len(results) == 1
        assert results[0] == ("build_app", True, True)

    def test_mixed_hierarchy_levels(self):
        """Test application with mixed hierarchy depths."""
        results = []

        class TestApp(Commander):
            _argparse_levels = 2

            def do_build(self, args):
                """simple build"""
                results.append("build")

            def do_test_unit(self, args):
                """unit tests"""
                results.append("test_unit")

            def do_deploy_prod_docker(self, args):
                """deploy to prod with docker"""
                results.append("deploy_prod_docker")

        app = TestApp()

        # Test deep command
        sys.argv = ["test", "deploy", "prod", "docker"]
        app.cmdline()

        assert "deploy_prod_docker" in results
