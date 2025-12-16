#!/usr/bin/env python3

from argdec import Commander, option, option_group

# ----------------------------------------------------------------------------
# Commandline interface

common_options = option_group(
    option("--dump", action="store_true", help="dump project and product vars"),
    option("-d",
           "--download",
           action="store_true",
           help="download python build/downloads"),
    option("-r", "--reset", action="store_true", help="reset python build"),
    option("-i",
           "--install",
           action="store_true",
           help="install python to build/lib"),
    option("-b",
           "--build",
           action="store_true",
           help="build python in build/src"),
    option("-c",
           "--clean",
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
    _argparse_levels = 2


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
