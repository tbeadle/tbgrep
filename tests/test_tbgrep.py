import re
import sys
import types
from io import StringIO

import pytest

from tbgrep import TracebackGrep

traceback_re = re.compile(
    r'Traceback \(most recent call last\):\n  File "<stdin>", line \d+, in <module>\nException: .*\n',
    re.M,
)

variations = [
    """
foo
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
Exception: baz
bar
""",
    """
    foo
    Traceback (most recent call last):
      File "<stdin>", line 2, in <module>
    Exception: baz
    bar
""",
    """
prefix    foo
prefix    Traceback (most recent call last):
prefix      File "<stdin>", line 2, in <module>
prefix    Exception: bazzy
prefix    bar
""",
]


def get_input_file():
    input_file = StringIO()
    input_file.write(
        """
a
b
c
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
Exception
d
e
f
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
IndexError: list index out of range
g
h
i
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
KeyError: 'foo'
j
k
l
""".strip()
    )
    input_file.seek(0)
    return input_file


input_lines = get_input_file().readlines()


def test_tbgrep():
    extractor = TracebackGrep()
    for variation in variations:
        found = False
        for line in variation.split("\n"):
            tb = extractor.process(line + "\n")
            if tb:
                found = True
                assert traceback_re.match(tb), repr(tb)
        assert found, "Couldn't extract traceback from: " + repr(variation)


@pytest.mark.parametrize(
    "ignore_line_numbers,ignore_exception_values,count",
    [
        (False, False, 3),
        (True, False, 2),
        (False, True, 2),
        (True, True, 1),
    ],
)
def test_tbgrep_stats(capsys, ignore_line_numbers, ignore_exception_values, count):
    extractor = TracebackGrep(
        stats=True,
        ignore_line_numbers=ignore_line_numbers,
        ignore_exception_values=ignore_exception_values,
    )
    for variation in variations:
        for line in variation.split("\n"):
            extractor.process(line + "\n")
    stats = extractor.get_stats()
    assert len(stats) == count, stats
    extractor.print_stats()
    captured = capsys.readouterr()
    assert (
        f"{count} unique traceback{'s' if count > 1 else ''} extracted" in captured.out
    )


@pytest.mark.parametrize("variation", variations)
def test_command(monkeypatch, capsys, variation):
    from tbgrep.commands import main

    tmpstdin = StringIO(variation)
    monkeypatch.setattr(sys, "stdin", tmpstdin)
    main(["--stats"])
    captured = capsys.readouterr()
    assert "1 unique traceback extracted" in captured.out


def test_tracebacks_from_lines():
    from tbgrep import tracebacks_from_lines

    tracebacks = tracebacks_from_lines(get_input_file())

    assert isinstance(tracebacks, types.GeneratorType)
    assert next(tracebacks) == "".join(input_lines[3:6])
    assert next(tracebacks) == "".join(input_lines[9:12])
    assert next(tracebacks) == "".join(input_lines[15:18])

    with pytest.raises(StopIteration):
        next(tracebacks)


def test_tracebacks_from_file():
    from tbgrep import tracebacks_from_file

    tracebacks = tracebacks_from_file(get_input_file())

    assert isinstance(tracebacks, types.GeneratorType)
    assert next(tracebacks) == "".join(input_lines[3:6])
    assert next(tracebacks) == "".join(input_lines[9:12])
    assert next(tracebacks) == "".join(input_lines[15:18])

    with pytest.raises(StopIteration):
        next(tracebacks)


def test_tracebacks_from_file_reverse():
    from tbgrep import tracebacks_from_file

    tracebacks = tracebacks_from_file(get_input_file(), reverse=True)
    assert next(tracebacks) == "".join(input_lines[15:18])
    assert next(tracebacks) == "".join(input_lines[9:12])
    assert next(tracebacks) == "".join(input_lines[3:6])

    with pytest.raises(StopIteration):
        next(tracebacks)


def test_last_traceback_from_file():
    from tbgrep import last_traceback_from_file

    traceback = last_traceback_from_file(get_input_file())
    assert traceback == "".join(input_lines[15:18])
