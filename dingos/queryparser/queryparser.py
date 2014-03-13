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
import ply.yacc as Yacc
from querylexer import QueryLexer
from querytree import FilterCollection, Expression, Condition, QueryParserException


class QueryParser:
    def __init__(self):
        self.lexer = QueryLexer()
        self.tokens = self.lexer.tokens
        self.parser = Yacc.yacc(module=self)

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

    '''
        QUERY LANGUAGE GRAMMAR
        ======================
        request:    query
        request:    query FORMATSIGN CSV OPEN formatargs CLOSE
        formatargs: colspecs COMMA miscargs
        formatargs: colspecs
        colspecs:   COLSPEC COMMA colspecs
        colspecs:   COLSPEC
        miscargs:
        miscarg:    FIELD EQUALS BOOL
        query:
        query:      expr
        query:      expr PIPE query
        query:      FILTER COLON expr
                    | EXCLUDE COLON expr
        query:      MARKED_BY COLON OPEN query CLOSE
        query:      NOT MARKED_BY COLON OPEN query CLOSE
        query:      FILTER COLON expr PIPE query
                    | EXCLUDE COLON expr PIPE query
        query:      MARKED_BY COLON OPEN query CLOSE PIPE query
        query:      NOT MARKED_BY COLON OPEN query CLOSE PIPE query
        expr:       OPEN expr CLOSE
        expr:       expr AND expr
                    |expr OR expr
        expr:       key comp value
        expr:       key NOT comp value
        comp:       EQUALS
                    | CONTAINS
                    | ICONTAINS
                    | REGEXP
                    | IREGEXP
                    | STARTSWITH
                    | ISTARTSWITH
                    | ENDSWITH
                    | IENDSWITH
                    | LOWERTHAN
                    | RANGE
                    | YOUNGER
        value:      VALUE
        key:        FIELD
                    | FACTTERM
    '''

    def p_query_empty(self, p):
        """query :"""
        p[0] = FilterCollection()

    def p_query_expr(self, p):
        """query : expr"""
        p[0] = FilterCollection()
        p[0].add_new_filter({'type': 'filter', 'expression': p[1]})

    def p_query_pipe(self, p):
        """query : expr PIPE query"""
        p[0] = p[3]
        p[0].add_new_filter({'type': 'filter', 'expression': p[1]})

    def p_query_expr_filter_type(self, p):
        """query : FILTER COLON expr
                | EXCLUDE COLON expr"""
        p[0] = FilterCollection()
        p[0].add_new_filter({'type': p[1], 'expression': p[3]})

    def p_query_expr_subquery_type(self, p):
        """query : MARKED_BY COLON OPEN query CLOSE"""
        p[0] = FilterCollection()
        p[0].add_new_filter({'type': p[1], 'query': p[4], 'negation': False})

    def p_query_expr_subquery_not_type(self, p):
        """query : NOT MARKED_BY COLON OPEN query CLOSE"""
        p[0] = FilterCollection()
        p[0].add_new_filter({'type': p[2], 'query': p[5], 'negation': True})

    def p_query_pipe_filter_type(self, p):
        """query : FILTER COLON expr PIPE query
                | EXCLUDE COLON expr PIPE query"""
        p[0] = p[5]
        p[0].add_new_filter({'type': p[1], 'expression': p[3]})

    def p_query_pipe_subquery_type(self, p):
        """query : MARKED_BY COLON OPEN query CLOSE PIPE query"""
        p[0] = p[7]
        p[0].add_new_filter({'type': p[1], 'query': p[4], 'negation': False})

    def p_query_pipe_subquery_not_type(self, p):
        """query : NOT MARKED_BY COLON OPEN query CLOSE PIPE query"""
        p[0] = p[8]
        p[0].add_new_filter({'type': p[2], 'query': p[5], 'negation': True})

    def p_expr_brackets(self, p):
        """expr : OPEN expr CLOSE"""
        p[0] = p[2]

    def p_expr_boolop(self, p):
        """expr : expr AND expr
                | expr OR expr"""
        p[0] = Expression(p[1], p[2], p[3])

    def p_expr_condition(self, p):
        """expr : key comp value"""
        p[0] = Condition(p[1], False, p[2], p[3])

    def p_expr_not_condition(self, p):
        """expr : key NOT comp value"""
        p[0] = Condition(p[1], True, p[3], p[4])

    def p_comp(self, p):
        """comp : EQUALS
                | CONTAINS
                | ICONTAINS
                | REGEXP
                | IREGEXP
                | STARTSWITH
                | ISTARTSWITH
                | ENDSWITH
                | IENDSWITH
                | LOWERTHAN
                | RANGE
                | YOUNGER"""
        p[0] = p[1]

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

    def p_key_field_factterm(self, p):
        """key : FIELD
                | FACTTERM"""
        p[0] = p[1]
