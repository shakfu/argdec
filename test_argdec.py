"""Test suite for argdec module."""
import argparse

import pytest

from argdec import (
    ArgDecError,
    Commander,
    CommandExecutionError,
    InvalidCommandNameError,
    MetaCommander,
    option,
    option_group,
)


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
        """Multiple option decorators should keep source (top-to-bottom) order."""
        @option("-v", "--verbose", action="store_true")
        @option("-q", "--quiet", action="store_true")
        def func():
            pass

        assert len(func.options) == 2
        assert func.options[0] == (("-v", "--verbose"), {"action": "store_true"})
        assert func.options[1] == (("-q", "--quiet"), {"action": "store_true"})

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

    def test_stacked_positionals_keep_source_order(self):
        """Positional @option decorators should bind in top-to-bottom source order."""
        captured = {}

        class App(Commander):
            @option("src")
            @option("dst")
            def do_cp(self, args):
                captured["src"] = args.src
                captured["dst"] = args.dst

        App().cmdline(argv=["cp", "from", "to"])
        assert captured == {"src": "from", "dst": "to"}
        assert [o[0] for o in App.do_cp.options] == [("src",), ("dst",)]


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
        assert app.name == ""
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
        with pytest.raises(SystemExit):
            app.cmdline(argv=[])

        captured = capsys.readouterr()
        assert "build" in captured.out
        assert "test" in captured.out

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
        app.cmdline(argv=["build", "-v"])

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
        with pytest.raises(SystemExit):
            app.cmdline(argv=[])

        captured = capsys.readouterr()
        assert "python" in captured.out

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
        with pytest.raises(SystemExit):
            app.cmdline(argv=[])

        captured = capsys.readouterr()
        assert "build" in captured.out

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
        app.cmdline(argv=["python", "build", "-v"])

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
        app.cmdline(argv=["build", "python", "static", "--type", "release"])

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
        # A leaf gets no subparsers of its own until something needs to nest under it
        assert "build" in app._argparse_parsers
        assert "build" not in app._argparse_structure

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
        # Keys are full dotted paths, so sibling branches cannot collide
        assert "build" in app._argparse_structure
        assert "build.python" in app._argparse_structure


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
        app.cmdline(argv=["build", "-v"])

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
        app.cmdline(argv=["python", "build"])

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

    def test_empty_prefix_skips_private_methods(self):
        """With an empty prefix, _private helpers must not become commands."""
        class TestApp(Commander):
            _command_prefix = ""

            def build(self, args):
                self._helper()

            def _helper(self):
                pass

        assert set(TestApp._argparse_subcmds) == {"build"}
        TestApp().cmdline(argv=["build"])

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
        with pytest.raises(SystemExit):
            app.cmdline(argv=[])

        captured = capsys.readouterr()
        assert "subcommands" in captured.out

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
        with pytest.raises(SystemExit):
            app.cmdline(argv=["--version"])

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
        app.cmdline(argv=["build", "app", "-v", "-d"])

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
        app.cmdline(argv=["deploy", "prod", "docker"])

        assert "deploy_prod_docker" in results


class TestErrorConditions:
    """Tests for error conditions and exception handling."""

    def test_empty_command_name_raises_error(self):
        """Method with prefix but no command name should raise InvalidCommandNameError."""
        with pytest.raises(InvalidCommandNameError, match="has no command name"):
            class BadApp(Commander):
                def do_(self, args):
                    """Empty command name"""
                    pass

    def test_invalid_identifier_raises_error(self):
        """Command name that's not a valid identifier should raise error."""
        with pytest.raises(InvalidCommandNameError, match="Invalid command name"):
            class BadApp(Commander):
                def do_123invalid(self, args):
                    """Starts with number"""
                    pass

    def test_command_execution_failure(self):
        """Command that raises exception should be wrapped in CommandExecutionError."""
        class FailingApp(Commander):
            def do_fail(self, args):
                """Command that fails"""
                raise ValueError("Something went wrong")

        app = FailingApp()
        with pytest.raises(CommandExecutionError, match="failed"):
            app.cmdline(argv=["fail"])

    def test_invalid_parent_command_name(self):
        """Invalid parent command name should raise InvalidCommandNameError."""
        app = Commander()
        app._argparse_structure = {}

        # Create a mock subparsers object
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        # Empty string should fail
        with pytest.raises(InvalidCommandNameError, match="Invalid parent command name"):
            app._ensure_parent_parser(subparsers, "")

        # Non-identifier should fail
        with pytest.raises(InvalidCommandNameError, match="Invalid parent command name"):
            app._ensure_parent_parser(subparsers, "123invalid")

    def test_no_command_specified(self):
        """Calling app without specifying a subcommand should raise error."""
        class TestApp(Commander):
            default_args = []  # Override default --help behavior

            def do_build(self, args):
                """Build command"""
                pass

        app = TestApp()

        # Follows argparse convention: usage on stderr, exit code 2
        with pytest.raises(SystemExit) as excinfo:
            app.cmdline(argv=[])

        assert excinfo.value.code == 2


class TestInheritance:
    """Commands and configuration should be inherited by subclasses."""

    def test_subclass_keeps_base_commands(self):
        """A subclass must not lose the commands defined by its base."""
        class Base(Commander):
            def do_build(self, args):
                """build"""

        class Child(Base):
            def do_test(self, args):
                """test"""

        assert set(Child._argparse_subcmds) == {"build", "test"}
        assert set(Base._argparse_subcmds) == {"build"}

    def test_inherited_command_executes(self):
        """An inherited command should be runnable from the subclass."""
        executed = []

        class Base(Commander):
            def do_build(self, args):
                """build"""
                executed.append("build")

        class Child(Base):
            def do_test(self, args):
                """test"""
                executed.append("test")

        Child().cmdline(argv=["build"])
        assert executed == ["build"]

    def test_subclass_can_override_base_command(self):
        """Redefining a command in a subclass should replace the base version."""
        executed = []

        class Base(Commander):
            def do_build(self, args):
                """build"""
                executed.append("base")

        class Child(Base):
            def do_build(self, args):
                """build better"""
                executed.append("child")

        Child().cmdline(argv=["build"])
        assert executed == ["child"]

    def test_deep_inheritance_chain(self):
        """Commands should accumulate across a multi-level hierarchy."""
        class A(Commander):
            def do_a(self, args):
                """a"""

        class B(A):
            def do_b(self, args):
                """b"""

        class C(B):
            def do_c(self, args):
                """c"""

        assert set(C._argparse_subcmds) == {"a", "b", "c"}

    def test_command_prefix_is_inherited(self):
        """A subclass should inherit _command_prefix from its base."""
        class Base(Commander):
            _command_prefix = "cmd_"

            def cmd_build(self, args):
                """build"""

        class Child(Base):
            def cmd_test(self, args):
                """test"""

        assert set(Child._argparse_subcmds) == {"build", "test"}

    def test_multiple_inheritance_merges_commands(self):
        """Commands from several bases should all be present."""
        class BuildMixin(Commander):
            def do_build(self, args):
                """build"""

        class TestMixin(Commander):
            def do_test(self, args):
                """test"""

        class App(BuildMixin, TestMixin):
            def do_deploy(self, args):
                """deploy"""

        assert set(App._argparse_subcmds) == {"build", "test", "deploy"}

    def test_diamond_inheritance_follows_mro(self):
        """In a diamond, dispatch must match Python's MRO, not a flattened merge."""
        executed = []

        class A(Commander):
            def do_x(self, args):
                executed.append("A")

        class C(A):
            def do_x(self, args):
                executed.append("C")

        class B(A):
            pass

        class D(B, C):
            pass

        assert D.do_x is C.do_x
        D().cmdline(argv=["x"])
        assert executed == ["C"]

    def test_plain_mixin_commands_are_registered(self):
        """do_* methods on a plain mixin should be commands and win over bases."""
        executed = []

        class Mix:
            def do_x(self, args):
                executed.append("Mix.x")

            def do_y(self, args):
                executed.append("Mix.y")

        class Base(Commander):
            def do_x(self, args):
                executed.append("Base.x")

        class M(Mix, Base):
            pass

        assert set(M._argparse_subcmds) == {"x", "y"}
        M().cmdline(argv=["x"])
        M().cmdline(argv=["y"])
        assert executed == ["Mix.x", "Mix.y"]


class TestPositionalParent:
    """A command that takes positionals cannot also have subcommands."""

    def test_positional_parent_with_child_rejected(self):
        """The child would be shadowed by the parent's positional."""
        class App(Commander):
            _argparse_levels = 1

            @option("name")
            def do_test(self, args):
                pass

            def do_test_unit(self, args):
                pass

        with pytest.raises(ArgDecError, match="'test' takes positional arguments"):
            App().cmdline(argv=["test", "unit"])

    def test_optional_only_parent_with_child_allowed(self):
        """Optional arguments on the parent do not shadow the child."""
        executed = []

        class App(Commander):
            _argparse_levels = 1

            @option("--name")
            def do_test(self, args):
                executed.append("test")

            def do_test_unit(self, args):
                executed.append("unit")

        App().cmdline(argv=["test", "unit"])
        App().cmdline(argv=["test", "--name", "x"])
        assert executed == ["unit", "test"]

    def test_positional_leaf_without_children_allowed(self):
        """A positional on a command with no children is unaffected."""
        captured = []

        class App(Commander):
            _argparse_levels = 1

            @option("name")
            def do_test_unit(self, args):
                captured.append(args.name)

        App().cmdline(argv=["test", "unit", "x"])
        assert captured == ["x"]


class TestHierarchyIsolation:
    """Sibling branches sharing a segment name must stay independent."""

    def test_shared_segment_does_not_collide(self):
        """Two branches with a common middle segment should both be reachable."""
        executed = []

        class App(Commander):
            _argparse_levels = 2

            def do_build_test_x(self, args):
                """bx"""
                executed.append("build_test_x")

            def do_deploy_test_y(self, args):
                """dy"""
                executed.append("deploy_test_y")

        app = App()
        app.cmdline(argv=["deploy", "test", "y"])
        app.cmdline(argv=["build", "test", "x"])

        assert executed == ["deploy_test_y", "build_test_x"]

    def test_shared_segment_keys_are_distinct(self):
        """The structure should key each branch by its full path."""
        class App(Commander):
            _argparse_levels = 2

            def do_build_test_x(self, args):
                """bx"""

            def do_deploy_test_y(self, args):
                """dy"""

        app = App()
        app.build_parser()

        assert "build.test" in app._argparse_structure
        assert "deploy.test" in app._argparse_structure

    def test_command_that_is_also_a_parent(self):
        """A leaf command may also host deeper commands."""
        executed = []

        class App(Commander):
            _argparse_levels = 1

            def do_test(self, args):
                """run all tests"""
                executed.append("test")

            def do_test_unit(self, args):
                """run unit tests"""
                executed.append("test_unit")

        app = App()
        app.cmdline(argv=["test"])
        app.cmdline(argv=["test", "unit"])

        assert executed == ["test", "test_unit"]

    def test_registration_order_does_not_matter(self):
        """A parent defined after its child should still work."""
        executed = []

        class App(Commander):
            _argparse_levels = 1

            def do_test_unit(self, args):
                """run unit tests"""
                executed.append("test_unit")

            def do_test(self, args):
                """run all tests"""
                executed.append("test")

        app = App()
        app.cmdline(argv=["test", "unit"])
        app.cmdline(argv=["test"])

        assert executed == ["test_unit", "test"]


class TestArgparseLevels:
    """_argparse_levels should cap the nesting depth."""

    def test_levels_zero_is_flat(self):
        """Level 0 keeps underscores in the command name."""
        executed = []

        class App(Commander):
            _argparse_levels = 0

            def do_python_shared_pkg(self, args):
                """build"""
                executed.append("run")

        App().cmdline(argv=["python_shared_pkg"])
        assert executed == ["run"]

    def test_levels_one_nests_once(self):
        """Level 1 gives one parent and a leaf that may contain underscores."""
        executed = []

        class App(Commander):
            _argparse_levels = 1

            def do_python_shared_pkg(self, args):
                """build"""
                executed.append("run")

        App().cmdline(argv=["python", "shared_pkg"])
        assert executed == ["run"]

    def test_levels_two_nests_twice(self):
        """Level 2 gives two parents and a leaf."""
        executed = []

        class App(Commander):
            _argparse_levels = 2

            def do_python_shared_pkg(self, args):
                """build"""
                executed.append("run")

        App().cmdline(argv=["python", "shared", "pkg"])
        assert executed == ["run"]

    def test_levels_one_rejects_deeper_path(self):
        """Level 1 should not accept a level-2 invocation."""
        class App(Commander):
            _argparse_levels = 1

            def do_python_shared_pkg(self, args):
                """build"""

        with pytest.raises(SystemExit):
            App().cmdline(argv=["python", "shared", "pkg"])

    def test_levels_deeper_than_name(self):
        """A name with fewer underscores than levels stays a shallow command."""
        executed = []

        class App(Commander):
            _argparse_levels = 3

            def do_build(self, args):
                """build"""
                executed.append("run")

        App().cmdline(argv=["build"])
        assert executed == ["run"]


class TestReusability:
    """A Commander instance should be reusable."""

    def test_cmdline_can_be_called_repeatedly(self):
        """Calling cmdline() more than once must not raise."""
        executed = []

        class App(Commander):
            _argparse_levels = 1

            def do_python_build(self, args):
                """build python"""
                executed.append("run")

        app = App()
        for _ in range(3):
            app.cmdline(argv=["python", "build"])

        assert executed == ["run", "run", "run"]

    def test_build_parser_is_repeatable(self):
        """build_parser() should reset hierarchy state on each call."""
        class App(Commander):
            _argparse_levels = 1

            def do_python_build(self, args):
                """build python"""

        app = App()
        first = app.build_parser()
        second = app.build_parser()

        assert first is not second
        assert set(app._argparse_structure) == {"python"}

    def test_instances_do_not_share_state(self):
        """Two instances of the same class should build independently."""
        class App(Commander):
            _argparse_levels = 1

            def do_python_build(self, args):
                """build python"""

        a, b = App(), App()
        a.build_parser()
        b.build_parser()

        assert a._argparse_structure is not b._argparse_structure


class TestParentCommands:
    """Invoking an intermediate level should show its help."""

    def test_bare_parent_prints_help_and_exits(self, capsys):
        """A parent command with no subcommand should not silently succeed."""
        class App(Commander):
            _argparse_levels = 1

            def do_python_build(self, args):
                """build python"""

        with pytest.raises(SystemExit) as excinfo:
            App().cmdline(argv=["python"])

        assert excinfo.value.code == 2
        assert "build" in capsys.readouterr().err

    def test_parent_help_lists_children(self, capsys):
        """The parent's help should list its subcommands."""
        class App(Commander):
            _argparse_levels = 1

            def do_python_build(self, args):
                """build python"""

            def do_python_test(self, args):
                """test python"""

        with pytest.raises(SystemExit):
            App().cmdline(argv=["python", "--help"])

        out = capsys.readouterr().out
        assert "build" in out
        assert "test" in out


class TestHelpFormatting:
    """Help output details."""

    def test_subcommand_help_shows_defaults(self, capsys):
        """ArgumentDefaultsHelpFormatter should apply to subparsers too."""
        class App(Commander):
            @option("--count", type=int, default=7, help="how many")
            def do_build(self, args):
                """build the project"""

        with pytest.raises(SystemExit):
            App().cmdline(argv=["build", "--help"])

        assert "default: 7" in capsys.readouterr().out

    def test_leaf_help_has_no_empty_subcommand_section(self, capsys):
        """A leaf command should not advertise subcommands it doesn't have."""
        class App(Commander):
            _argparse_levels = 1

            def do_python_build(self, args):
                """build python"""

        with pytest.raises(SystemExit):
            App().cmdline(argv=["python", "build", "--help"])

        assert "subcommands" not in capsys.readouterr().out

    def test_multiline_docstring_summary_used_as_help(self, capsys):
        """Only the first docstring line should appear in the command listing."""
        class App(Commander):
            default_args = ["--help"]

            def do_build(self, args):
                """build the project

                A much longer explanation that should not appear
                in the top-level command listing.
                """

        with pytest.raises(SystemExit):
            App().cmdline(argv=[])

        out = capsys.readouterr().out
        assert "build the project" in out
        assert "much longer explanation" not in out

    def test_percent_in_docstring_does_not_break_parser(self, capsys):
        """A literal % in a command docstring must not make argparse choke."""
        executed = []

        class App(Commander):
            def do_cov(self, args):
                """Report 100% coverage"""
                executed.append("cov")

            def do_ok(self, args):
                """Fine"""
                executed.append("ok")

        App().cmdline(argv=["ok"])
        App().cmdline(argv=["cov"])
        assert executed == ["ok", "cov"]

        with pytest.raises(SystemExit):
            App().cmdline(argv=["--help"])
        assert "100% coverage" in capsys.readouterr().out

        with pytest.raises(SystemExit):
            App().cmdline(argv=["cov", "--help"])
        out = capsys.readouterr().out
        assert "100% coverage" in out
        assert "%%" not in out

    def test_prog_name_uses_name_attribute(self, capsys):
        """The `name` attribute should set the program name in usage output."""
        class App(Commander):
            name = "myapp"
            version = "1.0"

        with pytest.raises(SystemExit):
            App().cmdline(argv=["--version"])

        assert "myapp 1.0" in capsys.readouterr().out

    def test_percent_in_version(self, capsys):
        """A literal % in the version must print, not crash argparse."""
        class App(Commander):
            name = "myapp"
            version = "1.0-100%"

        with pytest.raises(SystemExit):
            App().cmdline(argv=["--version"])

        assert "myapp 1.0-100%" in capsys.readouterr().out


class TestNameValidation:
    """Command name validation happens at class definition time."""

    def test_double_underscore_rejected(self):
        """A doubled underscore yields an empty path segment and is invalid."""
        with pytest.raises(InvalidCommandNameError, match="Invalid command name"):
            class BadApp(Commander):
                def do__foo(self, args):
                    """leading underscore"""

    def test_trailing_underscore_rejected(self):
        """A trailing underscore yields an empty trailing segment."""
        with pytest.raises(InvalidCommandNameError, match="Invalid command name"):
            class BadApp(Commander):
                def do_foo_(self, args):
                    """trailing underscore"""

    def test_error_message_names_the_custom_prefix(self):
        """The empty-name error should quote the configured prefix."""
        with pytest.raises(InvalidCommandNameError, match="'cmd_' prefix"):
            class BadApp(Commander):
                _command_prefix = "cmd_"

                def cmd_(self, args):
                    """no name"""


class TestExamples:
    """Smoke tests for the shipped example applications."""

    @pytest.mark.parametrize("module", ["basic", "hierarchical", "custom_prefix"])
    def test_example_imports(self, module):
        """Each example should import cleanly."""
        import importlib.util
        import pathlib

        path = pathlib.Path(__file__).parent / "examples" / f"{module}.py"
        spec = importlib.util.spec_from_file_location(f"example_{module}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

    def test_hierarchical_example_runs(self):
        """The hierarchical example should execute a deep command."""
        import importlib.util
        import pathlib

        path = pathlib.Path(__file__).parent / "examples" / "hierarchical.py"
        spec = importlib.util.spec_from_file_location("example_hierarchical", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        mod.Application().cmdline(argv=["python", "framework", "pkg"])


class TestUndocumentedCommands:
    """Commands without docstrings should still work."""

    def test_command_without_docstring(self, capsys):
        """A command with no docstring gets no help text, but still registers."""
        class App(Commander):
            default_args = ["--help"]

            def do_build(self, args):
                pass

        with pytest.raises(SystemExit):
            App().cmdline(argv=[])

        assert "build" in capsys.readouterr().out

    def test_undocumented_command_executes(self):
        """A command with no docstring should run normally."""
        executed = []

        class App(Commander):
            def do_build(self, args):
                executed.append("build")

        App().cmdline(argv=["build"])
        assert executed == ["build"]

    def test_undocumented_command_help(self, capsys):
        """`<cmd> --help` should work without a docstring to describe it."""
        class App(Commander):
            def do_build(self, args):
                pass

        with pytest.raises(SystemExit):
            App().cmdline(argv=["build", "--help"])

        assert "usage:" in capsys.readouterr().out


class TestMetaCommanderStandalone:
    """MetaCommander should be usable without inheriting from Commander."""

    def test_metaclass_defaults_to_do_prefix(self):
        """A class using the metaclass directly gets the default 'do_' prefix."""
        class Standalone(metaclass=MetaCommander):
            def do_build(self, args):
                """build"""

            def helper(self):
                """not a command"""

        assert set(Standalone._argparse_subcmds) == {"build"}

    def test_metaclass_honours_explicit_prefix(self):
        """An explicit prefix still wins on a standalone class."""
        class Standalone(metaclass=MetaCommander):
            _command_prefix = "cmd_"

            def cmd_build(self, args):
                """build"""

            def do_ignored(self, args):
                """ignored"""

        assert set(Standalone._argparse_subcmds) == {"build"}

    def test_prefix_lookup_skips_bases_without_one(self):
        """A plain mixin ahead of Commander should not hide the prefix."""
        class PlainMixin:
            """Not a Commander, carries no _command_prefix."""

        class App(PlainMixin, Commander):
            def do_build(self, args):
                """build"""

        assert set(App._argparse_subcmds) == {"build"}


class TestParserConstructionErrors:
    """Failures while building the parser should name the offending command."""

    def test_invalid_option_kwarg(self):
        """A bad argparse keyword should raise ArgDecError naming the command."""
        class App(Commander):
            @option("--count", bogus_keyword=True)
            def do_build(self, args):
                """build"""

        with pytest.raises(ArgDecError, match="Failed to create parser for command 'build'"):
            App().build_parser()

    def test_conflicting_option_strings(self):
        """Two options sharing a flag should be reported against the command."""
        class App(Commander):
            @option("-v", "--verbose", action="store_true")
            @option("-v", "--vociferous", action="store_true")
            def do_build(self, args):
                """build"""

        with pytest.raises(ArgDecError, match="Failed to create parser for command 'build'"):
            App().build_parser()

    def test_error_is_not_a_command_execution_error(self):
        """A setup failure is a configuration error, not an execution failure."""
        class App(Commander):
            @option("--count", bogus_keyword=True)
            def do_build(self, args):
                """build"""

        with pytest.raises(ArgDecError) as excinfo:
            App().cmdline(argv=["build"])

        assert not isinstance(excinfo.value, CommandExecutionError)


class TestUnexpectedParsingErrors:
    """Errors argparse does not handle should surface as ArgDecError."""

    def test_unexpected_error_during_parse(self):
        """A `type=` callable raising an unhandled exception is wrapped."""
        def exploding_type(value):
            raise KeyError("boom")

        class App(Commander):
            @option("--count", type=exploding_type)
            def do_build(self, args):
                """build"""

        with pytest.raises(ArgDecError, match="Unexpected error in cmdline"):
            App().cmdline(argv=["build", "--count", "1"])

    def test_argparse_handled_error_still_exits(self):
        """A `type=` raising ValueError stays argparse's business (exit 2)."""
        class App(Commander):
            @option("--count", type=int)
            def do_build(self, args):
                """build"""

        with pytest.raises(SystemExit) as excinfo:
            App().cmdline(argv=["build", "--count", "not-a-number"])

        assert excinfo.value.code == 2


class TestDispatch:
    """Handlers are bound through the instance and stored under a private dest."""

    def test_option_with_dest_func(self):
        """A user option named --func must not replace the command handler."""
        captured = {}

        class App(Commander):
            @option("--func")
            def do_f(self, args):
                captured["func"] = args.func

        App().cmdline(argv=["f", "--func", "z"])
        assert captured == {"func": "z"}

    def test_staticmethod_command(self):
        """A staticmethod command receives only the parsed args."""
        executed = []

        class App(Commander):
            @staticmethod
            @option("--n", type=int)
            def do_s(args):
                executed.append(args.n)

        App().cmdline(argv=["s", "--n", "3"])
        assert executed == [3]

    def test_option_outside_staticmethod(self):
        """@option applied on top of @staticmethod still registers."""
        executed = []

        class App(Commander):
            @option("--n", type=int)
            @staticmethod
            def do_s(args):
                executed.append(args.n)

        App().cmdline(argv=["s", "--n", "4"])
        assert executed == [4]

    def test_classmethod_command(self):
        """A classmethod command is registered and receives the class."""
        executed = []

        class App(Commander):
            @classmethod
            def do_c(cls, args):
                executed.append(cls)

        App().cmdline(argv=["c"])
        assert executed == [App]
