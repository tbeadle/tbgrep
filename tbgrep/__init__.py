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
# Copyright (C) 2011-2013 Luke Macken <lmacken@redhat.com>

import re
from collections import defaultdict, deque
from operator import itemgetter

tb_head = "Traceback (most recent call last):"
line_number_placeholder = "==TBGREP LINE NUMBER=="
exc_value_placeholder = "==TBGREP EXC VALUE=="


class TracebackGrep:
    exc_value_regex = re.compile(r": .*")
    line_number_regex = re.compile(r'(", line )(?:\d+)(, in )')

    def __init__(
        self,
        stats=False,
        ignore_line_numbers=False,
        ignore_exception_values=False,
    ):
        self.stats = stats
        self.ignore_line_numbers = ignore_line_numbers
        self.ignore_exception_values = ignore_exception_values
        self.tb = self.index = None
        self.firstline = self.prefix = False
        self.tracebacks = defaultdict(int)

    def process(self, line):
        if self.tb:
            if line:
                line = line[self.index :]
                self.tb.append(line)
                if line and line[0] != " ":
                    retval = "".join(self.tb)
                    if self.stats:
                        if self.ignore_exception_values:
                            self.tb[-1] = self.exc_value_regex.sub(
                                f": {exc_value_placeholder}", self.tb[-1], count=1
                            )
                        if self.ignore_line_numbers:
                            for idx in range(1, len(self.tb) - 1):
                                self.tb[idx] = self.line_number_regex.sub(
                                    rf"\1{line_number_placeholder}\2",
                                    self.tb[idx],
                                )

                        self.tracebacks["".join(self.tb)] += 1
                    self.tb = None
                    return retval
        elif tb_head in line:
            self.index = line.index(tb_head)
            self.tb = [line[self.index :]]

    def get_stats(self):
        return sorted(self.tracebacks.items(), key=itemgetter(1))

    def print_stats(self):
        header = lambda x: "== %s %s" % (x, "=" * (76 - len(x)))
        pluralize = lambda val, name: val == 1 and name or name + "s"
        stats = self.get_stats()
        for tb, num in stats:
            print(header("%d %s" % (num, pluralize(num, "occurence"))))
            print("")
            print(self.sanitize_tb(tb))
        print("=" * 80)
        num = len(stats)
        print("%d unique %s extracted" % (num, pluralize(num, "traceback")))

    def sanitize_tb(self, tb):
        if self.ignore_line_numbers:
            tb = tb.replace(line_number_placeholder, "###")
        if self.ignore_exception_values:
            tb = tb.replace(exc_value_placeholder, "***")
        return tb


def tracebacks_from_lines(lines_iter):
    """Generator that yields tracebacks found in a lines iterator

    The lines iterator can be:

    - a file-like object
    - a list (or deque) of lines.
    - any other iterable sequence of strings
    """

    tbgrep = TracebackGrep()

    for line in lines_iter:
        tb = tbgrep.process(line)
        if tb:
            yield tb


def tracebacks_from_file(fileobj, reverse=False):
    """Generator that yields tracebacks found in a file object

    With reverse=True, searches backwards from the end of the file.
    """

    if reverse:
        lines = deque()

        for line in BackwardsReader(fileobj):
            lines.appendleft(line)
            if tb_head in line:
                yield next(tracebacks_from_lines(lines))
                lines.clear()
    else:
        for traceback in tracebacks_from_lines(fileobj):
            yield traceback


def last_traceback_from_file(fileobj):
    """Returns the last traceback found in a file object."""

    for traceback in tracebacks_from_file(fileobj, reverse=True):
        return traceback


# From Raymond Hettinger at
# http://code.activestate.com/recipes/439045-read-a-text-file-backwards-yet-another-implementat/
def BackwardsReader(file, BLKSIZE=4096):
    """Read a file line by line, backwards"""

    buf = ""

    file.seek(0, 2)
    lastchar = file.read(1)
    trailing_newline = lastchar == "\n"

    while 1:
        newline_pos = buf.rfind("\n")
        pos = file.tell()
        if newline_pos != -1:
            # Found a newline
            line = buf[newline_pos + 1 :]
            buf = buf[:newline_pos]
            if pos or newline_pos or trailing_newline:
                line += "\n"
            yield line
        elif pos:
            # Need to fill buffer
            toread = min(BLKSIZE, pos)
            file.seek(pos - toread, 0)
            buf = file.read(toread) + buf
            file.seek(pos - toread, 0)
            if pos == toread:
                buf = "\n" + buf
        else:
            # Start-of-file
            return
