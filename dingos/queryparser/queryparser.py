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
from querytree import FilterCollection, Expression, Condition, QueryParserException, FormattedFilterCollection, ReferencedByFilterCollection

import logging

logger = logging.getLogger(__name__)

class QueryParser:
    def __init__(self):
        self.lexer = QueryLexer()
        self.tokens = self.lexer.tokens
        self.parser = Yacc.yacc(module=self,errorlog=logger,debug=0)

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
        refbyrequest: request
        refbyrequest: REFERENCED_BY COLON OPEN request CLOSE REFBYSIGN request
        request:    query
        request:    query FORMATSIGN ID OPEN formatargs CLOSE
        formatargs: formatarg COMMA formatargs
        formatargs: formatarg
        formatarg:  VALUE
        formatarg:  ID EQUALS TRUE
                    | ID EQUALS FALSE
                    | ID EQUALS VALUE
        query:
        query:      expr
        query:      expr PIPE query
        query:      FILTER COLON expr
                    | FACTFILTER COLON expr
                    | MARKED_BY COLON OPEN query CLOSE
        query:      query PIPE FILTER COLON expr
                    | query PIPE FACTFILTER COLON expr
                    | query PIPE MARKED_BY COLON OPEN query CLOSE
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
        key:        ID
                    | FACTTERM
    '''

    def p_simple_refby_request(self, p):
        """refbyrequest : request"""
        p[0] = ReferencedByFilterCollection(p[1])

    def p_refby_request(self, p):
        """refbyrequest : REFERENCED_BY COLON OPEN request CLOSE REFBYSIGN request"""
        p[0] = ReferencedByFilterCollection(p[7], p[4])

    def p_simple_request(self, p):
        """request : query"""
        p[0] = FormattedFilterCollection(p[1])

    def p_request(self, p):
        """request : query FORMATSIGN ID OPEN formatargs CLOSE"""
        p[0] = FormattedFilterCollection(p[1], p[5], p[3])

    def p_formatargs(self, p):
        """formatargs : formatarg COMMA formatargs"""
        p[0] = [p[1]] + p[3]

    def p_formatargs_one(self, p):
        """formatargs : formatarg"""
        p[0] = [p[1]]

    def p_formatarg_value(self, p):
        """formatarg : VALUE"""
        p[0] = p[1][1:-1]

    def p_formatarg_miscarg(self, p):
        """formatarg : ID EQUALS TRUE
                        | ID EQUALS FALSE
                        | ID EQUALS VALUE"""
        p[0] = {'key': p[1], 'value': p[3]}

    def p_query_empty(self, p):
        """query :"""
        p[0] = FilterCollection()

    def p_query_expr_filter_type(self, p):
        """query : FILTER COLON expr
                 | FACTFILTER COLON expr
                 | MARKED_BY COLON OPEN query CLOSE"""
        p[0] = FilterCollection()
        if p[1] == 'marked_by':
            p[0].add_new_filter({'type': p[1], 'expr_or_query': p[4], 'negation': False})
        else:
            p[0].add_new_filter({'type': p[1], 'expr_or_query': p[3], 'negation': False})

    #def p_query_expr_filter_not_type(self, p):
    #    """query : NOT FILTER COLON expr
    #             | NOT FACTFILTER COLON expr
    #             | NOT MARKED_BY COLON OPEN query CLOSE"""
    #    p[0] = FilterCollection()
    #    if p[2] == 'marked_by':
    #        p[0].add_new_filter({'type': p[2], 'expr_or_query': p[5], 'negation': True})
    #    else:
    #        p[0].add_new_filter({'type': p[2], 'expr_or_query': p[4], 'negation': True})

    def p_pipe_query_expr_filter_type(self, p):
        """query : query PIPE FILTER COLON expr
                 | query PIPE FACTFILTER COLON expr
                 | query PIPE MARKED_BY COLON OPEN query CLOSE"""
        p[0] = p[1]
        if p[3] == 'marked_by':
            p[0].add_new_filter({'type': p[3], 'expr_or_query': p[6], 'negation': False})
        else:
            p[0].add_new_filter({'type': p[3], 'expr_or_query': p[5], 'negation': False})

    #def p_pipe_query_expr_filter_not_type(self, p):
    #    """query : query PIPE NOT FILTER COLON expr
    #             | query PIPE NOT FACTFILTER COLON expr
    #             | query PIPE NOT MARKED_BY COLON OPEN query CLOSE"""
    #    p[0] = p[1]
    #    if p[4] == 'marked_by':
    #        p[0].add_new_filter({'type': p[4], 'expr_or_query': p[7], 'negation': True})
    #    else:
    #        p[0].add_new_filter({'type': p[4], 'expr_or_query': p[6], 'negation': True})


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
        """key : ID
                | FACTTERM"""
        p[0] = p[1]
