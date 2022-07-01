#!/usr/bin/env python
# tbgrep - Python Traceback Extractor
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2011 Luke Macken <lmacken@redhat.com>

import argparse
import sys

import tbgrep


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="Report unique tracebacks and the number of occurrences.",
    )
    parser.add_argument(
        "--ignore-line-numbers",
        action="store_true",
        default=False,
        help=(
            "When reporting unique tracebacks, treat stack traces with varying line "
            "numbers as the same."
        ),
    )
    parser.add_argument(
        "--ignore-exception-values",
        action="store_true",
        default=False,
        help=(
            "When reporting unique tracebacks, treat stack traces with varying values "
            "for the exception as the same."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=argparse.FileType("r"),
        help="The files to process.",
    )
    args = parser.parse_args(argv)
    if not args.files:
        args.files = [sys.stdin]

    extractor = tbgrep.TracebackGrep(
        stats=args.stats,
        ignore_line_numbers=args.ignore_line_numbers,
        ignore_exception_values=args.ignore_exception_values,
    )

    for file in args.files:
        for line in file:
            tb = extractor.process(line)
            if not args.stats and tb:
                print(tb)

    if args.stats:
        extractor.print_stats()


if __name__ == "__main__":
    main()
