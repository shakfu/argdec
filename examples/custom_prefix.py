#!/usr/bin/env python3
"""Example demonstrating custom command prefix in argdec.

By default, argdec discovers methods starting with 'do_' as commands.
You can customize this by setting the _command_prefix class attribute.
"""

from argdec import Commander, option


# Example 1: Using custom 'cmd_' prefix
class MyApp(Commander):
    """Example app using 'cmd_' prefix instead of 'do_'."""

    name = 'myapp'
    version = '1.0'
    _command_prefix = 'cmd_'  # Custom prefix
    _argparse_levels = 1

    @option("-v", "--verbose", action="store_true", help="verbose output")
    def cmd_build(self, args):
        """build the application"""
        print(f"Building... (verbose={args.verbose})")

    @option("-f", "--force", action="store_true", help="force deployment")
    def cmd_deploy_production(self, args):
        """deploy to production"""
        print(f"Deploying to production... (force={args.force})")

    @option("-c", "--coverage", action="store_true", help="with coverage")
    def cmd_test_unit(self, args):
        """run unit tests"""
        print(f"Running unit tests... (coverage={args.coverage})")


# Example 2: Using 'action_' prefix for a more domain-specific naming
class TaskRunner(Commander):
    """Task runner using 'action_' prefix for semantic clarity."""

    name = 'taskrunner'
    version = '1.0'
    _command_prefix = 'action_'
    _argparse_levels = 0

    def action_lint(self, args):
        """lint the codebase"""
        print("Linting code...")

    def action_format(self, args):
        """format the codebase"""
        print("Formatting code...")

    def action_analyze(self, args):
        """analyze code quality"""
        print("Analyzing code quality...")


# Example 3: Empty prefix (discovers all methods - use with caution!)
class MinimalApp(Commander):
    """Example with empty prefix - all methods become commands."""

    name = 'minimal'
    version = '1.0'
    _command_prefix = ''  # Empty prefix
    _argparse_levels = 0
    default_args = ['--help']

    def build(self, args):
        """build command"""
        print("Building...")

    def test(self, args):
        """test command"""
        print("Testing...")

    # Note: This will also discover __init__, etc. unless they're filtered
    # The metaclass filters out dunder methods automatically


if __name__ == '__main__':
    import sys

    print("=" * 70)
    print("Custom Prefix Examples")
    print("=" * 70)
    print()
    print("Try these commands:")
    print("  python example_custom_prefix.py myapp")
    print("  python example_custom_prefix.py myapp --help")
    print("  python example_custom_prefix.py myapp build -v")
    print("  python example_custom_prefix.py myapp deploy production -f")
    print("  python example_custom_prefix.py myapp test unit -c")
    print()
    print("  python example_custom_prefix.py taskrunner")
    print("  python example_custom_prefix.py taskrunner lint")
    print()
    print("  python example_custom_prefix.py minimal")
    print("=" * 70)
    print()

    if len(sys.argv) < 2:
        print("Please specify which app to run: myapp, taskrunner, or minimal")
        sys.exit(1)

    app_name = sys.argv[1]
    sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove app selector from args

    if app_name == 'myapp':
        app = MyApp()
    elif app_name == 'taskrunner':
        app = TaskRunner()
    elif app_name == 'minimal':
        app = MinimalApp()
    else:
        print(f"Unknown app: {app_name}")
        print("Available apps: myapp, taskrunner, minimal")
        sys.exit(1)

    app.cmdline()
