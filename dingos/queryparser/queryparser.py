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
import ply.yacc as yacc
from querylexer import QueryLexer
from querytree import *


class QueryParserException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class QueryParser:
    def __init__(self):
        self.lexer = QueryLexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self)

    def parse(self, data):
        if data:
            return self.parser.parse(data, self.lexer.lexer)
        else:
            return []

    def p_error(self, p):
        if p is not None:
            raise QueryParserException("Syntax error: \"%s\"" % p.value)
        else:
            raise QueryParserException("Syntax error: Cannot parse anything.")

    def p_query_empty(self, p):
        "query :"
        p[0] = FilterCollection()

    def p_query_expr(self, p):
        "query : expr"
        p[0] = FilterCollection()
        p[0].add_new_filter(p[1])

    def p_query_filter(self, p):
        "query : expr FILTER query"
        p[0] = p[3]
        p[0].add_new_filter(p[1])

    def p_expr_brackets(self, p):
        "expr : OPEN expr CLOSE"
        p[0] = p[2]

    def p_expr_boolop(self, p):
        '''expr : expr AND expr
                | expr OR expr'''
        # TODO The following comment works but is not recursive
        #if isinstance(p[1], Condition) and isinstance(p[3], Condition):
        #    if p[1].key_is_fact_term() and p[3].key_is_fact_term():
        #        raise QueryParserException("Boolean operation \"%s\" with two fact terms is not possible. Use filter chaining." % Operator.AND)
        p[0] = Expression(p[1], p[2], p[3])

    def p_expr_condition(self, p):
        "expr : key comp value"
        p[0] = Condition(p[1], p[2], p[3])

    def p_comp(self, p):
        '''comp : EQUALS
                | CONTAINS
                | ICONTAINS
                | REGEXP
                | IREGEXP
                | STARTSWITH
                | ISTARTSWITH
                | ENDSWITH
                | IENDSWITH'''
        p[0] = p[1]

    def p_value_with_quotes(self, p):
        "value : VALUE"
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

    def p_key_field_factterm(self, p):
        """key : FIELD
                | FACTTERM"""
        p[0] = p[1]
