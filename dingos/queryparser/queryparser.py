#!/usr/bin/env python

# --------------------------------------
# queryparser.py
#
# parser for the query language
#---------------------------------------
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

    def p_query_1(self, p):
        "query :"
        p[0] = FilterCollection()

    def p_query_2(self, p):
        "query : expr"
        p[0] = FilterCollection()
        p[0].add_new_filter(p[1])

    def p_query_3(self, p):
        "query : expr FILTER query"
        p[0] = p[3]
        p[0].add_new_filter(p[1])

    def p_expr_1(self, p):
        "expr : OPEN expr CLOSE"
        p[0] = p[2]

    def p_expr_2(self, p):
        "expr : expr boolop expr"
        p[0] = Expression(p[1], p[2], p[3])

    def p_expr_3(self, p):
        "expr : key EQUALS value"
        p[0] = Condition(p[1], Comparator.EQUALS, p[3])

    def p_expr_4(self, p):
        "expr : key CONTAINS value"
        p[0] = Condition(p[1], Comparator.CONTAINS, p[3])

    def p_expr_5(self, p):
        "expr : key REGEXP value"
        p[0] = Condition(p[1], Comparator.REGEXP, p[3])

    def p_value_1(self, p):
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

    def p_key_1(self, p):
        """key : FIELD
                | FACTTERM"""
        p[0] = p[1]

    '''def p_key_1(self, p):
        "key : FIELD"
        p[0] = p[1]

    def p_key_1(self, p):
        "key : FACTTERM"
        p[0] = p[1]'''

    def p_boolop_1(self, p):
        "boolop : AND"
        p[0] = Operator.AND

    def p_boolop_2(self, p):
        "boolop : OR"
        p[0] = Operator.OR


# Main
if __name__ == "__main__":
    parser = QueryParser()
    with open('query_tests.txt') as query_file:
        for i, line in enumerate(query_file):
            print "%s:\tQuery:\t%s" % (i+1, line.strip())
            print "\tObject:\t%s" % parser.parse(line)

