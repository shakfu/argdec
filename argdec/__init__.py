"""argdec: general commandline interface module

Provides a declarative argparse-based class to be inherited
by applications wishing to provide a basic commandline interface.

This is based on my old `argdeclare` code
    see: http://code.activestate.com/recipes/576935-argdec-declarative-interface-to-argparse

"""
import argparse
import inspect
import logging
import sys
from collections.abc import Callable, Sequence
from typing import Any, cast

__version__ = "0.3.0"

__all__ = [
    "ArgDecError",
    "Commander",
    "CommandExecutionError",
    "DuplicateCommandError",
    "InvalidCommandNameError",
    "MetaCommander",
    "arg",
    "option",
    "option_group",
]

# ------------------------------------------------------------------------------
# Custom Exceptions

class ArgDecError(Exception):
    """Base exception for argdec errors."""
    pass


class InvalidCommandNameError(ArgDecError):
    """Raised when a command name is invalid."""
    pass


class DuplicateCommandError(ArgDecError):
    """Raised when attempting to register a duplicate command."""
    pass


class CommandExecutionError(ArgDecError):
    """Raised when command execution fails."""
    pass


# ------------------------------------------------------------------------------
# Logging setup

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Generic utility functions and classes for commandline ops


OptionSpec = tuple[tuple[Any, ...], dict[str, Any]]
DecoratorFunc = Callable[[Callable[..., Any]], Callable[..., Any]]


def option(*args: Any, **kwds: Any) -> DecoratorFunc:
    """Decorator to add argparse options to command methods.

    Use this decorator to declaratively add command-line options to your
    command methods. The arguments are passed directly to argparse's
    add_argument() method.

    Args:
        *args: Positional arguments for argparse (e.g., "-v", "--verbose")
        **kwds: Keyword arguments for argparse (e.g., action="store_true", help="...")

    Returns:
        Decorator function that adds the option to the method's options list

    Example:
        @option("-v", "--verbose", action="store_true", help="enable verbose output")
        @option("-f", "--file", type=str, help="input file")
        def do_build(self, args):
            if args.verbose:
                print(f"Building from {args.file}")
    """

    def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        _option: OptionSpec = (args, kwds)
        if hasattr(func, "options"):
            cast(Any, func).options.append(_option)
        else:
            cast(Any, func).options = [_option]
        return func

    return _decorator


# Alias for option decorator
arg = option


def option_group(*options: DecoratorFunc) -> DecoratorFunc:
    """Combine multiple option decorators into a reusable group.

    This is useful when you have common options that should be applied to
    multiple commands. Instead of repeating decorators, create a group once
    and apply it to multiple commands.

    Args:
        *options: Variable number of option decorators to group together

    Returns:
        Decorator function that applies all options to the method

    Example:
        # Define common options once
        common_opts = option_group(
            option("-v", "--verbose", action="store_true"),
            option("-d", "--debug", action="store_true"),
        )

        # Apply to multiple commands
        @common_opts
        def do_build(self, args):
            pass

        @common_opts
        def do_test(self, args):
            pass
    """

    def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        for opt in options:
            func = opt(func)
        return func

    return _decorator


def _help_texts(func: Callable[..., Any]) -> tuple[str | None, str | None]:
    """Derive argparse help and description text from a command's docstring.

    The first line of the docstring becomes the short `help` shown in command
    listings; the full (dedented) docstring becomes the subparser `description`
    shown by `<cmd> --help`.

    Args:
        func: The command function whose docstring should be used

    Returns:
        Tuple of (summary, description), either of which may be None
    """
    doc = inspect.getdoc(func)
    if not doc:
        return None, None
    summary = doc.splitlines()[0].strip() or None
    return summary, doc


class MetaCommander(type):
    """Metaclass to provide argparse boilerplate features to its instance class.

    Automatically discovers methods starting with the command prefix (default 'do_')
    and registers them as subcommands. Captures any options added via the @option decorator.

    Commands are inherited: a subclass keeps every command defined by its base
    classes and may override one by redefining the method under the same name.

    The command prefix can be customized by setting the _command_prefix class attribute;
    it too is inherited by subclasses.
    """

    def __new__(
        cls,
        classname: str,
        bases: tuple[type, ...],
        classdict: dict[str, Any]
    ) -> type:
        # Get command prefix from class dict, then bases, then default to 'do_'
        command_prefix: str | None = classdict.get('_command_prefix')
        if command_prefix is None:
            for base in bases:
                inherited = getattr(base, '_command_prefix', None)
                if inherited is not None:
                    command_prefix = inherited
                    break
        if command_prefix is None:
            command_prefix = 'do_'
        prefix_len = len(command_prefix)

        # Inherit commands from base classes, following MRO precedence: later
        # bases win over earlier ones, and this class's own commands win over all.
        subcmds: dict[str, dict[str, Any]] = {}
        for base in reversed(bases):
            subcmds.update(getattr(base, '_argparse_subcmds', {}))

        own: dict[str, dict[str, Any]] = {}
        for name, func in list(classdict.items()):
            # Only process callable methods that start with the command prefix
            # Skip special Python attributes (dunder methods) and non-callables
            if (name.startswith(command_prefix) and
                callable(func) and
                not (name.startswith('__') and name.endswith('__'))):
                cmd_name = name[prefix_len:]

                # Validate command name
                if not cmd_name:
                    raise InvalidCommandNameError(
                        f"Method '{name}' has no command name after "
                        f"the '{command_prefix}' prefix"
                    )
                # Validate each underscore-separated segment: in hierarchical
                # mode every segment becomes its own subcommand, so an empty
                # segment (from a leading or doubled underscore) is invalid.
                if not all(segment.isidentifier() for segment in cmd_name.split("_")):
                    raise InvalidCommandNameError(
                        f"Invalid command name '{cmd_name}' from method '{name}'"
                    )

                # Defensive: method names within a class body are unique, so
                # two commands in `own` cannot currently collide. The guard
                # stays to keep that invariant explicit if name mapping ever
                # becomes less direct.
                if cmd_name in own:  # pragma: no cover
                    raise DuplicateCommandError(
                        f"Duplicate command '{cmd_name}' found in class '{classname}'"
                    )

                subcmd: dict[str, Any] = {
                    "name": cmd_name,
                    "func": func,
                    "options": [],
                }
                if hasattr(func, "options"):
                    subcmd["options"] = func.options
                own[cmd_name] = subcmd
                logger.debug(f"Registered command: {cmd_name}")

        subcmds.update(own)
        classdict["_argparse_subcmds"] = subcmds
        return type.__new__(cls, classname, bases, classdict)


class Commander(metaclass=MetaCommander):
    """Base class for creating command-line applications with declarative syntax.

    Subclass this and define methods starting with the command prefix (default 'do_')
    to create subcommands. Use the @option decorator to add command-line options
    to your commands.

    Attributes:
        name: Program name shown in usage (defaults to "", i.e. argparse's default)
        epilog: Text to display after help (defaults to "")
        version: Application version (defaults to "0.1")
        default_args: Arguments to use when none provided (defaults to ["--help"])
        _command_prefix: Prefix for command methods (defaults to "do_")
        _argparse_levels: Depth of the command hierarchy (0 = flat). See below.

    Command hierarchy:
        With _argparse_levels = 0 (the default) each method maps to one flat
        command, underscores included: `do_python_shared_pkg` -> `python_shared_pkg`.

        With _argparse_levels = N (N >= 1) the method name is split on at most N
        underscores, giving up to N parent levels plus a leaf whose name may
        itself contain underscores:

            _argparse_levels = 1 -> do_python_shared_pkg -> `python shared_pkg`
            _argparse_levels = 2 -> do_python_shared_pkg -> `python shared pkg`

    Example:
        # Using default 'do_' prefix
        class MyApp(Commander):
            def do_build(self, args):
                pass

        # Using custom prefix
        class MyApp(Commander):
            _command_prefix = "cmd_"

            def cmd_build(self, args):
                pass
    """

    name: str = ""
    epilog: str = ""
    version: str = "0.1"
    default_args: list[str] = ["--help"]
    _command_prefix: str = "do_"  # Prefix for command methods
    _argparse_subcmds: dict[str, dict[str, Any]]  # Populated by metaclass with discovered commands
    _argparse_levels: int = 0  # 0 = flat commands, N >= 1 = at most N levels of nesting

    def __init__(self) -> None:
        """Initialize Commander instance with fresh state."""
        # Both are keyed by the full dotted command path ("deploy.prod") so that
        # sibling branches sharing a segment name cannot collide.
        self._argparse_structure: dict[str, Any] = {}  # path -> subparsers action
        self._argparse_parsers: dict[str, argparse.ArgumentParser] = {}  # path -> parser

    def add_parser(
        self,
        subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
        subcmd: dict[str, Any],
        name: str | None = None
    ) -> argparse.ArgumentParser:
        """Add a subcommand parser with its options.

        Args:
            subparsers: The argparse subparsers object to add to
            subcmd: Dictionary containing command metadata (name, func, options)
            name: Optional override for command name (uses subcmd["name"] if None)

        Returns:
            The created subparser object

        Raises:
            ArgDecError: If parser creation fails
        """
        if not name:
            name = subcmd["name"]

        summary, description = _help_texts(subcmd["func"])

        try:
            subparser = subparsers.add_parser(
                name,
                help=summary,
                description=description,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            )

            for args, kwds in subcmd["options"]:
                subparser.add_argument(*args, **kwds)
            subparser.set_defaults(func=subcmd["func"])
            logger.debug(f"Added parser for command: {name}")
            return subparser
        except (argparse.ArgumentError, TypeError, ValueError) as e:
            # argparse's own message doesn't say which command was at fault
            raise ArgDecError(f"Failed to create parser for command '{name}': {e}") from e

    def _split_command(self, name: str) -> list[str]:
        """Split a command name into path segments, honouring _argparse_levels.

        Args:
            name: The full command name (e.g. 'python_shared_pkg')

        Returns:
            List of path segments; a single-element list when the hierarchy is flat
        """
        if not self._argparse_levels:
            return [name]
        return name.split("_", self._argparse_levels)

    def _ensure_parent_parser(
        self,
        subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
        head: str,
        path: tuple[str, ...] = (),
    ) -> "argparse._SubParsersAction[argparse.ArgumentParser]":
        """Ensure a parent level exists in the structure, creating it if needed.

        When building hierarchical commands, intermediate levels may not have
        explicit command implementations. This method creates dummy parent
        commands as needed. A dummy parent invoked on its own prints its help.

        If a real command already occupies this path (e.g. `do_test` alongside
        `do_test_unit`), its parser is reused and its behaviour left untouched.

        Args:
            subparsers: The argparse subparsers object to add to
            head: The name of the parent command level
            path: Ancestor segments of `head`, used to key the structure

        Returns:
            The subparsers object for the parent level

        Raises:
            InvalidCommandNameError: If head is not a valid command name
        """
        if not head or not head.isidentifier():
            raise InvalidCommandNameError(f"Invalid parent command name: '{head}'")

        key = ".".join((*path, head))
        if key in self._argparse_structure:
            return cast(
                "argparse._SubParsersAction[argparse.ArgumentParser]",
                self._argparse_structure[key]
            )

        parent_parser = self._argparse_parsers.get(key)
        if parent_parser is None:
            # An intermediate level has no behaviour of its own, so invoking it
            # without a subcommand shows what it can do rather than silently
            # succeeding. Its parser is built from this function, so the
            # reference back to the parser is filled in immediately after.
            holder: list[argparse.ArgumentParser] = []

            def show_help(instance: Any, args: argparse.Namespace) -> None:
                holder[0].print_help(sys.stderr)
                raise SystemExit(2)

            show_help.__name__ = f"{head}_help"
            show_help.__doc__ = f"{head} commands"

            parent_subcmd: dict[str, Any] = {
                'name': head,
                'func': show_help,
                'options': [],
            }
            parent_parser = self.add_parser(subparsers, parent_subcmd, name=head)
            holder.append(parent_parser)
            self._argparse_parsers[key] = parent_parser
            logger.debug(f"Created parent parser: {key}")

        self._argparse_structure[key] = parent_parser.add_subparsers(
            title=f"{head} subcommands",
            description=f"{head} commands",
            help='additional help',
            metavar='',
        )

        return cast(
            "argparse._SubParsersAction[argparse.ArgumentParser]",
            self._argparse_structure[key]
        )

    def parse_subparsers(
        self,
        subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
        subcmd: dict[str, Any],
        name: str
    ) -> argparse.ArgumentParser:
        """Add a command, building the hierarchy implied by its name.

        Command names like 'build_python_static' are split on underscores
        (up to _argparse_levels times) and recursively processed to create
        nested subcommands.

        Args:
            subparsers: The argparse subparsers object to add to
            subcmd: Dictionary containing command metadata
            name: The full command name (may contain underscores for hierarchy)

        Returns:
            The created subparser object

        Examples:
            - 'build' creates a single command
            - 'python_build' creates 'python' parent with 'build' child
            - 'deploy_prod_docker' creates deploy -> prod -> docker hierarchy
        """
        return self._add_command(subparsers, subcmd, self._split_command(name), ())

    def _add_command(
        self,
        subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
        subcmd: dict[str, Any],
        segments: list[str],
        path: tuple[str, ...],
    ) -> argparse.ArgumentParser:
        """Recursively attach a command at the location given by `segments`.

        Args:
            subparsers: The subparsers object for the current level
            subcmd: Dictionary containing command metadata
            segments: Remaining path segments; the last one names the command
            path: Segments already consumed, used to key the structure

        Returns:
            The created subparser object
        """
        head, *tail = segments
        logger.debug(f"Adding command segment: {head} (path={path}, tail={tail})")

        # Base case: leaf command. Its own subparsers are created lazily, only
        # if a deeper command later needs to hang off it.
        if not tail:
            subparser = self.add_parser(subparsers, subcmd, name=head)
            self._argparse_parsers[".".join((*path, head))] = subparser
            return subparser

        # Recursive case: ensure parent exists, then recurse on the remainder
        parent_subparsers = self._ensure_parent_parser(subparsers, head, path)
        return self._add_command(parent_subparsers, subcmd, tail, (*path, head))

    def build_parser(self) -> argparse.ArgumentParser:
        """Build the fully populated argument parser for this application.

        Discards any hierarchy state from a previous build, so this may be
        called repeatedly on the same instance.

        Returns:
            The root ArgumentParser, with all subcommands registered

        Raises:
            ArgDecError: If parser setup fails
        """
        self._argparse_structure = {}
        self._argparse_parsers = {}

        parser = argparse.ArgumentParser(
            prog=self.name or None,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description=self.__doc__,
            epilog=self.epilog,
        )

        parser.add_argument(
            "-v", "--version", action="version", version="%(prog)s " + self.version
        )

        subparsers = parser.add_subparsers(
            title="subcommands",
            description="valid subcommands",
            help="additional help",
            metavar="",
        )

        # Sorted order is load-bearing, not cosmetic: a command that is the
        # prefix of another ('test' vs 'test_unit') must be registered first so
        # that the deeper command attaches to the real parser rather than
        # colliding with a generated parent.
        # With _argparse_levels == 0 every name is a single segment, so this
        # same path produces a flat set of commands.
        for name in sorted(self._argparse_subcmds.keys()):
            self.parse_subparsers(subparsers, self._argparse_subcmds[name], name)

        return parser

    def cmdline(self, argv: Sequence[str] | None = None) -> None:
        """Main commandline function to process commandline arguments and options.

        This method:
        1. Builds the argument parser with version info and all subcommands
        2. Parses command-line arguments
        3. Executes the selected command

        Args:
            argv: Arguments to parse, excluding the program name. Defaults to
                sys.argv[1:]. Pass an explicit list to drive the application
                from tests or from an embedding process.

        Raises:
            CommandExecutionError: If command execution fails
            ArgDecError: If parser setup fails
            SystemExit: On --help, --version, argparse errors, and when no
                subcommand was given (exit code 2, following argparse convention)
        """
        try:
            parser = self.build_parser()

            args = list(sys.argv[1:] if argv is None else argv)
            if not args:
                logger.debug("No arguments provided, using defaults")
                args = list(self.default_args)

            options = parser.parse_args(args)

            # Execute command
            if not hasattr(options, 'func'):
                parser.print_help(sys.stderr)
                raise SystemExit(2)

            try:
                logger.debug(f"Executing command: {options.func.__name__}")
                options.func(self, options)
            except Exception as e:
                raise CommandExecutionError(
                    f"Command '{options.func.__name__}' failed: {e}"
                ) from e

        except ArgDecError:
            # Covers CommandExecutionError too
            raise
        except SystemExit:
            # Let sys.exit calls pass through (--help, --version, errors)
            raise
        except Exception as e:
            raise ArgDecError(f"Unexpected error in cmdline: {e}") from e
