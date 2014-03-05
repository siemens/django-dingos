# Copyright (c) Siemens AG, 2014
#
# This file is part of MANTIS.  MANTIS is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or(at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import ply.lex as Lex


class QueryLexerException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class QueryLexer:
    # Reserved words
    reserved = {
        "contains": "CONTAINS",
        "icontains": "ICONTAINS",
        "regexp": "REGEXP",
        "iregexp": "IREGEXP",
        "startswith": "STARTSWITH",
        "istartswith": "ISTARTSWITH",
        "endswith": "ENDSWITH",
        "iendswith": "IENDSWITH",
        "filter": "FILTER",
        "exclude": "EXCLUDE",
    }

    # Tokens
    tokens = ["FIELD", "AND", "OR", "OPEN", "CLOSE", "EQUALS", "VALUE", "PIPE", "FACTTERM", "COLON"]\
             + list(reserved.values())

    def t_FIELD(self, t):
        r"[a-zA-Z][\w]*"
        # Check for reserved words
        t.type = self.reserved.get(t.value, 'FIELD')
        return t

    t_AND = (r"\&\&")
    t_OR = (r"\|\|")
    t_OPEN = (r"\(")
    t_CLOSE = (r"\)")
    t_EQUALS = (r"\=")
    t_VALUE = (r"(\"[^\"]*\"|\'[^\']*\')")
    t_PIPE = (r"\|")
    t_FACTTERM = (r"\[[^\/\@\]]+(\/[^\/\@\]]+)*(\@[^\]]*)?\]")
    t_COLON = (r"\:")

    # Ignore whitespaces
    t_ignore = "\t\n\r "

    def __init__(self):
        self.lexer = Lex.lex(module=self)

    # Error handling
    def t_error(self, t):
        illegal_char = t.value[0].encode("string-escape")
        t.lexer.skip(1)
        raise QueryLexerException("Illegal character: \"%s\"" % illegal_char)

    # Build lexer
    def build(self, **kwargs):
        self.lexer = Lex.lex(module=self, **kwargs)

    # Test method
    def test(self, data):
        self.lexer.input(data)
        for token in iter(self.lexer.token, None):
            print token
