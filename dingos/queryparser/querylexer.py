#!/usr/bin/env python

# --------------------------------------
# querylexer.py
#
# tokenizer for the query language
#---------------------------------------
import ply.lex as lex

class QueryLexer:
    # Reserved words
    reserved = {
        "contains" : "CONTAINS",
        "regexp" : "REGEXP",
    }

    # Tokens
    tokens = ["FIELD","AND","OR","OPEN","CLOSE","EQUALS","VALUE","FILTER", "FACTTERM"] + list(reserved.values())

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
    t_FILTER = (r"\|")
    t_FACTTERM = (r"\[[a-zA-Z0-9]*\/[a-zA-Z0-9]*\]")

    # Ignore whitespaces
    t_ignore = "\t\n\r "

    def __init__(self):
        self.lexer = lex.lex(module=self)

    # Error handling
    def t_error(self, t):
        illegal_char = t.value[0].encode("string-escape")
        lineno = t.lexer.lineno
        print "Illegal character: %s" % illegal_char
        print "t: %s"
        t.lexer.skip(1)

    # Build lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # Test method
    def test(self, data):
        self.lexer.input(data)
        for token in iter(self.lexer.token, None):
            print token

