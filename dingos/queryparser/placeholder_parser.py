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
import ply.yacc as Yacc
import logging

logger = logging.getLogger(__name__)


class PlaceholderLexer:
    # Reserved words
    reserved = {}

    # Tokens
    tokens = ["ID",
              "ID_WITH_WITHSPACE",
              "OPEN",
              "CLOSE",
              "VALUE",
              "COLON",
              "COMMA"] + list(reserved.values())

    def t_ID(self, t):
        r"[a-zA-Z0-9_\.]+"
        # Check for reserved words
        t.type = self.reserved.get(t.value, 'ID')
        return t

    t_OPEN = (r"\(")
    t_CLOSE = (r"\)")
    t_VALUE = (r"(\"[^\"]*\"|\'[^\']*\')")
    t_COLON = (r"\:")
    t_COMMA = (r"\,")

    # Ignore whitespaces (tab, newline, carriage return, blank)
    t_ignore = "\t\n\r "

    def __init__(self):
        self.lexer = Lex.lex(module=self)

    # Error handling
    def t_error(self, t):
        illegal_char = str(t.value[0]).encode("string-escape")
        t.lexer.skip(1)
        raise PlaceholderException("Illegal character: \"%s\"" % illegal_char)

    # Build lexer
    def build(self, **kwargs):
        self.lexer = Lex.lex(module=self, **kwargs)

    # Test method
    def test(self, data):
        self.lexer.input(data)
        for token in iter(self.lexer.token, None):
            print token


class PlaceholderParser:
    def __init__(self):
        self.lexer = PlaceholderLexer()
        self.tokens = self.lexer.tokens
        self.parser = Yacc.yacc(module=self, errorlog=logger, debug=0)

    def parse(self, data):
        if data:
            return self.parser.parse(data, self.lexer.lexer)
        else:
            return []

    def p_error(self, p):
        if p is not None:
            raise PlaceholderException("Syntax error: \"%s\"" % p.value)
        else:
            raise PlaceholderException("Syntax error: Cannot parse anything.")

    def p_placeholder(self, p):
        """placeholder : ID OPEN value CLOSE COLON params"""
        params = p[6]
        params['field_name'] = p[1]
        params['human_readable'] = p[3]
        p[0] = params

    def p_params(self, p):
        """params : param COMMA params"""
        p[0] = dict(p[1].items() + p[3].items())

    def p_params_one(self, p):
        """params : param"""
        p[0] = p[1]

    def p_param(self, p):
        """param : ID COLON value"""
        p[0] = {p[1]: p[3]}

    def p_value_with_quotes(self, p):
        """value : VALUE"""
        # The quotes need to be removed here in the parser
        # because the lexer cannot cover the following
        # examples with regular expressions conveniently.
        # Legal:
        #     'fo"o' => fo"o
        #     "b'ar" => f'oo
        # Illegal:
        #     'foo" => FAILURE!
        #     "bar' => FAILURE!
        p[0] = p[1][1:-1]


class PlaceholderException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
