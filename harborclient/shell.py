"""
Command-line interface to the Harbor API.
"""

from __future__ import print_function
import argparse

import logging
import sys
import utils

from oslo_utils import encodeutils
from oslo_utils import importutils


__defined_modules__ = ('submodule',)

logger = logging.getLogger(__name__)


class HarborClientArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(HarborClientArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.
        """
        self.print_usage(sys.stderr)
        # FIXME(lzyeval): if changes occur in argparse.ArgParser._check_value
        choose_from = ' (choose from'
        progparts = self.prog.partition(' ')
        self.exit(2,
                  ("error: %(errmsg)s\nTry '%(mainp)s help %(subp)s'"
                   " for more information.\n") % {
                       'errmsg': message.split(choose_from)[0],
                       'mainp': progparts[0],
                       'subp': progparts[2]})

    def _get_option_tuples(self, option_string):
        """returns (action, option, value) candidates for an option prefix

        Returns [first candidate] if all candidates refers to current and
        deprecated forms of the same options parsing succeed.
        """
        option_tuples = (super(HarborClientArgumentParser, self)
                         ._get_option_tuples(option_string))
        if len(option_tuples) > 1:
            normalizeds = [
                option.replace('_', '-')
                for action, option, value in option_tuples
            ]
            if len(set(normalizeds)) == 1:
                return option_tuples[:1]
        return option_tuples


class HarborShell(object):
    def get_base_parser(self):
        parser = HarborClientArgumentParser(
            prog='harbor',
            description=__doc__.strip(),
            epilog='See "harbor help COMMAND" '
            'for help on a specific command.',
            add_help=False,
            formatter_class=HarborHelpFormatter, )

        # Global arguments
        parser.add_argument(
            '-h',
            '--help',
            action='store_true',
            help=argparse.SUPPRESS, )

        parser.add_argument(
            '--debug',
            default=False,
            action='store_true',
            help="Print debugging output.")

        return parser

    def get_subcommand_parser(self):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        for module in __defined_modules__:
            actions_module = importutils.import_module(module)
            self._find_actions(subparsers, actions_module)
        self._find_actions(subparsers, self)
        self._add_bash_completion_subparser(subparsers)

        return parser

    def _add_bash_completion_subparser(self, subparsers):
        subparser = subparsers.add_parser(
            'bash_completion',
            add_help=False,
            formatter_class=HarborHelpFormatter)
        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hyphen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''

            action_help = desc.strip()
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(
                command,
                help=action_help,
                description=desc,
                add_help=False,
                formatter_class=HarborHelpFormatter)
            subparser.add_argument(
                '-h',
                '--help',
                action='help',
                help=argparse.SUPPRESS, )
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                kw = kwargs.copy()
                subparser.add_argument(*args, **kw)
            subparser.set_defaults(func=callback)

    def setup_debugging(self, debug):
        if not debug:
            return
        streamformat = "%(levelname)s (%(module)s:%(lineno)d) %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=streamformat)
        logging.getLogger('iso8601').setLevel(logging.WARNING)

    def main(self, argv):
        # Parse args once to find version and debug settings
        parser = self.get_base_parser()
        (args, args_list) = parser.parse_known_args(argv)
        self.setup_debugging(args.debug)
        do_help = ('help' in argv) or ('--help' in argv) or (
            '-h' in argv) or not argv

        # bash-completion should not require authentication

        subcommand_parser = self.get_subcommand_parser()
        self.parser = subcommand_parser

        if args.help or not argv:
            subcommand_parser.print_help()
            return 0

        args = subcommand_parser.parse_args(argv)

        # Short-circuit and deal with help right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion(args)
            return 0

        args.func(args)


    def do_bash_completion(self, _args):
        """Print bash completion

        Prints all of the commands and options to stdout so that the
        harbor.bash_completion script doesn't have to hard code them.
        """
        commands = list()
        options = list()
        for sc_str, sc in self.subcommands.items():
            commands.append(sc_str)
            for option in sc._optionals._option_string_actions.keys():
                options.append(option)

        options.extend(self.parser._option_string_actions.keys())
        print(' '.join(set(commands + options)))

    @utils.arg(
        'command',
        metavar='<subcommand>',
        nargs='?',
        help='Display help for <subcommand>.')
    def do_help(self, args):
        """Display help about this program or one of its subcommands."""
        if args.command:
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise Exception(
                    ("'%s' is not a valid subcommand") % args.command)
        else:
            self.parser.print_help()


# I'm picky about my shell help.
class HarborHelpFormatter(argparse.HelpFormatter):
    def __init__(self,
                 prog,
                 indent_increment=2,
                 max_help_position=32,
                 width=None):
        super(HarborHelpFormatter, self).__init__(prog, indent_increment,
                                                  max_help_position, width)

    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(HarborHelpFormatter, self).start_section(heading)


def main():

    try:
        argv = sys.argv[1:]
        HarborShell().main(argv)
    except KeyboardInterrupt:
        print("... terminating harbor client", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print("CommandError: %s" % e)
        sys.exit(127)


if __name__ == "__main__":
    main()
