# This is the original python-dotenv parser with minor changes to work in clean-dotenv
# Find the copyright and license below:
# Copyright (c) 2014, Saurabh Kumar (python-dotenv), 2013, Ted Tieken (django-dotenv-rw), 2013, Jacob Kaplan-Moss (django-dotenv)
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# - Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# - Neither the name of django-dotenv nor the names of its contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import codecs
import re
from collections.abc import Iterator
from collections.abc import Sequence
from re import Match
from re import Pattern
from typing import IO
from typing import NamedTuple
from typing import Optional


def make_regex(string: str, extra_flags: int = 0) -> Pattern[str]:
    return re.compile(string, re.UNICODE | extra_flags)


_newline = make_regex(r'(\r\n|\n|\r)')
_multiline_whitespace = make_regex(r'(\s*)', extra_flags=re.MULTILINE)
_whitespace = make_regex(r'([^\S\r\n]*)')
_export = make_regex(r'(export[^\S\r\n]+)?')
_single_quoted_key = make_regex(r"'([^']+)'")
_unquoted_key = make_regex(r'([^=\#\s]+)')
_equal_sign = make_regex(r'(=[^\S\r\n]*)')
_single_quoted_value = make_regex(r"'((?:\\'|[^'])*)'")
_double_quoted_value = make_regex(r'"((?:\\"|[^"])*)"')
_unquoted_value = make_regex(r'([^\r\n]*)')
_comment = make_regex(r'([^\S\r\n]*#[^\r\n]*)?')
_end_of_line = make_regex(r'[^\S\r\n]*(\r\n|\n|\r|$)')
_rest_of_line = make_regex(r'[^\r\n]*(?:\r|\n|\r\n)?')
_double_quote_escapes = make_regex(r"\\[\\'\"abfnrtv]")
_single_quote_escapes = make_regex(r"\\[\\']")


class Original(NamedTuple):
    string: str
    line: int


class Binding(NamedTuple):
    multiline_whitespace: Optional[str]
    export: Optional[str]
    key: Optional[str]
    value: Optional[str]
    separator: Optional[str]
    original: Original
    comment: Optional[str]
    end_of_line: Optional[str]
    error: bool


class Position:
    def __init__(self, chars: int, line: int) -> None:
        self.chars = chars
        self.line = line

    @classmethod
    def start(cls) -> 'Position':
        return cls(chars=0, line=1)

    def set(self, other: 'Position') -> None:
        self.chars = other.chars
        self.line = other.line

    def advance(self, string: str) -> None:
        self.chars += len(string)
        self.line += len(re.findall(_newline, string))


class Error(Exception):
    pass


class Reader:
    def __init__(self, stream: IO[str]) -> None:
        self.string = stream.read()
        self.position = Position.start()
        self.mark = Position.start()

    def has_next(self) -> bool:
        return self.position.chars < len(self.string)

    def set_mark(self) -> None:
        self.mark.set(self.position)

    def get_marked(self) -> Original:
        return Original(
            string=self.string[self.mark.chars : self.position.chars],
            line=self.mark.line,
        )

    def peek(self, count: int) -> str:
        return self.string[self.position.chars : self.position.chars + count]

    def read(self, count: int) -> str:
        result = self.string[self.position.chars : self.position.chars + count]
        if len(result) < count:
            raise Error('read: End of string')
        self.position.advance(result)
        return result

    def read_regex(self, regex: Pattern[str]) -> Sequence[str]:
        match = regex.match(self.string, self.position.chars)
        if match is None:
            raise Error('read_regex: Pattern not found')
        self.position.advance(self.string[match.start() : match.end()])
        return match.groups()


def decode_escapes(regex: Pattern[str], string: str) -> str:
    def decode_match(match: Match[str]) -> str:
        return codecs.decode(match.group(0), 'unicode-escape')  # type: ignore

    return regex.sub(decode_match, string)


def parse_key(reader: Reader) -> Optional[str]:
    char = reader.peek(1)
    if char == '#':
        return None
    elif char == "'":
        (key,) = reader.read_regex(_single_quoted_key)
    else:
        (key,) = reader.read_regex(_unquoted_key)
    return key


def parse_unquoted_value(reader: Reader) -> str:
    (part,) = reader.read_regex(_unquoted_value)
    return re.sub(r'\s+#.*', '', part).rstrip()


def parse_value(reader: Reader) -> tuple[str, str]:
    char = reader.peek(1)
    if char == "'":
        (value,) = reader.read_regex(_single_quoted_value)
        return decode_escapes(_single_quote_escapes, value), "'"
    elif char == '"':
        (value,) = reader.read_regex(_double_quoted_value)
        return decode_escapes(_double_quote_escapes, value), '"'
    elif char in ('', '\n', '\r'):
        return '', ''
    else:
        return parse_unquoted_value(reader), ''


def parse_binding(reader: Reader) -> Binding:
    reader.set_mark()
    try:
        (multiline_whitespace,) = reader.read_regex(_multiline_whitespace)
        if not reader.has_next():
            return Binding(
                multiline_whitespace=multiline_whitespace,
                export=None,
                key=None,
                value=None,
                separator=None,
                comment=None,
                end_of_line=None,
                original=reader.get_marked(),
                error=False,
            )
        (export,) = reader.read_regex(_export)
        key = parse_key(reader)
        reader.read_regex(_whitespace)
        if reader.peek(1) == '=':
            reader.read_regex(_equal_sign)
            value, separator = parse_value(reader)
        else:
            value = None
            separator = None
        (comment,) = reader.read_regex(_comment)
        (end_of_line,) = reader.read_regex(_end_of_line)
        return Binding(
            multiline_whitespace=multiline_whitespace,
            export=export,
            key=key,
            value=value,
            separator=separator,
            comment=comment,
            end_of_line=end_of_line,
            original=reader.get_marked(),
            error=False,
        )
    except Error:
        reader.read_regex(_rest_of_line)
        return Binding(
            multiline_whitespace=None,
            export=export,
            key=None,
            value=None,
            separator=None,
            comment=None,
            original=reader.get_marked(),
            end_of_line=None,
            error=True,
        )


def parse_stream(stream: IO[str]) -> Iterator[Binding]:
    reader = Reader(stream)
    while reader.has_next():
        yield parse_binding(reader)
