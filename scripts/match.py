#! /usr/bin/env python

"""Testing tool that parses PAD rule set files and runs a match against message.

Prints out any matching rules.
"""

from __future__ import print_function

import os
import sys
import glob
import optparse

import pad
import pad.config
import pad.errors
import pad.message
import pad.rules.parser


def main():
    usage = "usage: %prog [options] pad_rules_glob message_file"
    opt = optparse.OptionParser(description=__doc__, version=pad.__version__,
                                usage=usage)
    opt.add_option("-n", "--nice", dest="nice", type="int",
                   help="'nice' level", default=0)
    opt.add_option("--paranoid", action="store_true", default=False,
                   dest="paranoid", help="if errors are found in the ruleset "
                   "stop processing")
    opt.add_option("-k", "--revoke", dest="revoke", type="bool",
                   default="False", help="Revoke the given message")
    opt.add_option("-r", "--report", dest="report", type="bool",
                   default="False", help="Report the given message")
    opt.add_option("-d", "--debug", action="store_true", default=False,
                   dest="debug", help="enable debugging output")
    options, (rule_glob, msg_file) = opt.parse_args()
    os.nice(options.nice)

    logger = pad.config.setup_logging("pad-logger", debug=options.debug)

    try:
        ruleset = pad.rules.parser.parse_pad_rules(glob.glob(rule_glob),
                                                   options.paranoid)
    except pad.errors.MaxRecursionDepthExceeded as e:
        print(e.recursion_list, file=sys.stderr)
        sys.exit(1)
    except pad.errors.ParsingError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    with open(msg_file) as msgf:
        raw_msg = msgf.read()
    msg = pad.message.Message(ruleset.ctxt, raw_msg)

    ruleset.match(msg)

    for name, result in msg.rules_checked.items():
        if result:
            print(ruleset.get_rule(name))

    if options['revoke']:
        ruleset.context.hook_revoke(raw_msg)
    if options['report']:
        ruleset.context.hook_report(raw_msg)

if __name__ == "__main__":
    main()

