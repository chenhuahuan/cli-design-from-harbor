import utils

@utils.arg(
    '--submodule-func',
    metavar='<submodule-func>',
    help='Display help for <subcommand>.')
def do_submodule(args):
    """Display help about this program or one of its subcommands."""
    if args.submodule_func:
        print('do_submodule_func...%s' % args.submodule_func)