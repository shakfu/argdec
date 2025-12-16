"""argdec: general commandline interface module

Provides a declarative argparse-based class to be inherited
by applications wishing to provide a basic commandline interface.

This is based on my old `argdeclare` code
    see: http://code.activestate.com/recipes/576935-argdec-declarative-interface-to-argparse

"""
import argparse
import logging
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

__version__ = "0.2.2"

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


OptionSpec = Tuple[Tuple[Any, ...], Dict[str, Any]]
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


class MetaCommander(type):
    """Metaclass to provide argparse boilerplate features to its instance class.

    Automatically discovers methods starting with the command prefix (default 'do_')
    and registers them as subcommands. Captures any options added via the @option decorator.

    The command prefix can be customized by setting the _command_prefix class attribute.
    """

    def __new__(
        cls,
        classname: str,
        bases: Tuple[type, ...],
        classdict: Dict[str, Any]
    ) -> type:
        # Get command prefix from class dict or default to 'do_'
        command_prefix = classdict.get('_command_prefix', 'do_')
        prefix_len = len(command_prefix)

        subcmds: Dict[str, Dict[str, Any]] = {}
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
                        f"Method '{name}' has no command name after 'do_' prefix"
                    )
                if not cmd_name.replace("_", "").isidentifier():
                    raise InvalidCommandNameError(
                        f"Invalid command name '{cmd_name}' from method '{name}'"
                    )

                # Check for duplicates
                if cmd_name in subcmds:
                    raise DuplicateCommandError(
                        f"Duplicate command '{cmd_name}' found in class '{classname}'"
                    )

                subcmd: Dict[str, Any] = {
                    "name": cmd_name,
                    "func": func,
                    "options": [],
                }
                if hasattr(func, "options"):
                    subcmd["options"] = func.options
                subcmds[cmd_name] = subcmd
                logger.debug(f"Registered command: {cmd_name}")

        classdict["_argparse_subcmds"] = subcmds
        return type.__new__(cls, classname, bases, classdict)


class Commander(metaclass=MetaCommander):
    """Base class for creating command-line applications with declarative syntax.

    Subclass this and define methods starting with the command prefix (default 'do_')
    to create subcommands. Use the @option decorator to add command-line options
    to your commands.

    Attributes:
        name: Application name (defaults to "app name")
        epilog: Text to display after help (defaults to "")
        version: Application version (defaults to "0.1")
        default_args: Arguments to use when none provided (defaults to ["--help"])
        _command_prefix: Prefix for command methods (defaults to "do_")
        _argparse_levels: Number of hierarchy levels for subcommands (0 = flat, 1+ = hierarchical)

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

    name: str = "app name"
    epilog: str = ""
    version: str = "0.1"
    default_args: List[str] = ["--help"]
    _command_prefix: str = "do_"  # Prefix for command methods
    _argparse_subcmds: Dict[str, Dict[str, Any]]  # Populated by metaclass with discovered commands
    _argparse_levels: int = 0  # 0 = flat commands, 1+ = hierarchical based on underscores

    def __init__(self) -> None:
        """Initialize Commander instance with fresh state."""
        self._argparse_structure: Dict[str, Any] = {}  # Tracks subparser hierarchy per instance

    def add_parser(
        self,
        subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
        subcmd: Dict[str, Any],
        name: Optional[str] = None
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

        try:
            subparser = subparsers.add_parser(name, help=subcmd["func"].__doc__)

            for args, kwds in subcmd["options"]:
                subparser.add_argument(*args, **kwds)
            subparser.set_defaults(func=subcmd["func"])
            logger.debug(f"Added parser for command: {name}")
            return subparser
        except Exception as e:
            raise ArgDecError(f"Failed to create parser for command '{name}': {e}") from e

    def _ensure_parent_parser(
        self,
        subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
        head: str
    ) -> "argparse._SubParsersAction[argparse.ArgumentParser]":
        """Ensure parent parser exists in structure, creating dummy if needed.

        When building hierarchical commands, intermediate levels may not have
        explicit command implementations. This method creates dummy parent
        commands as needed.

        Args:
            subparsers: The argparse subparsers object to add to
            head: The name of the parent command level

        Returns:
            The subparsers object for the parent level

        Raises:
            InvalidCommandNameError: If head is not a valid command name
        """
        if not head or not head.isidentifier():
            raise InvalidCommandNameError(f"Invalid parent command name: '{head}'")

        if head not in self._argparse_structure:
            def dummy_func(self: Any, args: argparse.Namespace) -> None:
                """Placeholder function for intermediate hierarchy level."""
                pass
            dummy_func.__doc__ = f"{head} commands"

            dummy_subcmd: Dict[str, Any] = {
                'name': head,
                'func': dummy_func,
                'options': [],
            }
            parent_parser = self.add_parser(subparsers, dummy_subcmd, name=head)
            self._argparse_structure[head] = parent_parser.add_subparsers(
                title=f"{head} subcommands",
                description=dummy_func.__doc__,
                help='additional help',
                metavar='',
            )
            logger.debug(f"Created parent parser: {head}")

        return cast(
            "argparse._SubParsersAction[argparse.ArgumentParser]",
            self._argparse_structure[head]
        )

    def parse_subparsers(
        self,
        subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
        subcmd: Dict[str, Any],
        name: str
    ) -> argparse.ArgumentParser:
        """Recursively parse command hierarchy from underscore-separated name.

        This is the core recursive method that builds hierarchical command structures.
        Command names like 'build_python_static' are split on underscores and
        recursively processed to create nested subcommands.

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
        head, *tail = name.split("_", 1)
        logger.debug(f"Parsing command: {name} (head={head}, tail={tail})")

        # Base case: no hierarchy, just add the command
        if not tail:
            subparser = self.add_parser(subparsers, subcmd, name=head)
            # Prepare for potential children by creating subparsers
            if head not in self._argparse_structure:
                self._argparse_structure[head] = subparser.add_subparsers(
                    title=f"{head} subcommands",
                    description=subcmd["func"].__doc__,
                    help="additional help",
                    metavar="",
                )
            return subparser

        # Recursive case: ensure parent exists, then recurse on tail
        parent_subparsers = self._ensure_parent_parser(subparsers, head)
        return self.parse_subparsers(parent_subparsers, subcmd, tail[0])


    def cmdline(self) -> None:
        """Main commandline function to process commandline arguments and options.

        This method:
        1. Creates the main argument parser with version info
        2. Registers all discovered subcommands (flat or hierarchical based on _argparse_levels)
        3. Parses command-line arguments
        4. Executes the selected command

        Raises:
            CommandExecutionError: If command execution fails
            ArgDecError: If parser setup fails
        """
        try:
            parser = argparse.ArgumentParser(
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

            # Register all subcommands
            for name in sorted(self._argparse_subcmds.keys()):
                subcmd = self._argparse_subcmds[name]
                if not self._argparse_levels:
                    # Flat structure: all commands at top level
                    self.add_parser(subparsers, subcmd)
                else:
                    # Hierarchical structure: parse based on underscores
                    self.parse_subparsers(subparsers, subcmd, name)

            # Parse arguments
            if len(sys.argv) <= 1:
                logger.debug("No arguments provided, using defaults")
                options = parser.parse_args(self.default_args)
            else:
                options = parser.parse_args()

            # Execute command
            if not hasattr(options, 'func'):
                parser.print_help()
                raise CommandExecutionError("No command specified")

            try:
                logger.debug(f"Executing command: {options.func.__name__}")
                options.func(self, options)
            except Exception as e:
                raise CommandExecutionError(
                    f"Command '{options.func.__name__}' failed: {e}"
                ) from e

        except CommandExecutionError:
            raise
        except ArgDecError:
            raise
        except SystemExit:
            # Let argparse's sys.exit calls pass through (--help, --version, errors)
            raise
        except Exception as e:
            raise ArgDecError(f"Unexpected error in cmdline: {e}") from e
