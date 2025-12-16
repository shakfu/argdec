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
