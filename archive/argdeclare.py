import argparse
import sys


# option decorator
def option(*args, **kwds):
    def _decorator(func):
        _option = (args, kwds)
        if hasattr(func, 'options'):
            func.options.append(_option)
        else:
            func.options = [_option]
        return func
    return _decorator

# arg decorator
arg = option

# combines option decorators
def option_group(*options):
    def _decorator(func):
        for option in options:
            func = option(func)
        return func
    return _decorator


class MetaCommander(type):
    def __new__(cls, classname, bases, classdict):
        classdict = dict(classdict)
        subcmds = {}
        for name, func in list(classdict.items()):
            if name.startswith('do_'):
                name = name[3:]
                subcmd = {
                    'name': name,
                    'func': func,
                    'options': []
                }
                if hasattr(func, 'options'):
                    subcmd['options'] = func.options
                subcmds[name] = subcmd
        classdict['_argparse_subcmds'] = subcmds
        return type.__new__(cls, classname, bases, classdict)



class Commander(metaclass=MetaCommander):
    name = 'app'
    description = 'a description'
    version = '0.0'
    epilog = ''
    default_args = ['--help']

    def parse_args(self):
        parser = argparse.ArgumentParser(
            # prog = self.name,
            formatter_class = argparse.RawDescriptionHelpFormatter,
            description=self.__doc__,
            epilog = self.epilog,
        )

        return parser

    def cmdline(self):
        self.parser = self.parse_args()

        self.parser.add_argument('-v', '--version', action='version',
                            version = '%(prog)s '+ self.version)

        subparsers = self.parser.add_subparsers(
            title='subcommands',
            description='valid subcommands',
            help='additional help',
            metavar="",
        )

        for name in sorted(self._argparse_subcmds.keys()):
            subcmd = self._argparse_subcmds[name]
            subparser = subparsers.add_parser(subcmd['name'],
                                     help=subcmd['func'].__doc__)
            for args, kwds in subcmd['options']:
                subparser.add_argument(*args, **kwds)
            subparser.set_defaults(func=subcmd['func'])

        if len(sys.argv) <= 1:
            options = self.parser.parse_args(self.default_args)
        else:
            options = self.parser.parse_args()

        self.options = options
        options.func(self, options)


