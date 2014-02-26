#!/usr/bin/env python

# --------------------------------------
# querytree.py
#
# query object hierarchy
#---------------------------------------
class Operator:
    OR = "|"
    AND = "&"

class Comparator:
    EQUALS = "="
    CONTAINS = "contains"
    REGEXP = "regexp"

class FilterCollection:
    def __init__(self):
        self.filterList = []

    def addNewFilter(self, newFilter):
        self.filterList.insert(0, newFilter)

    def __repr__(self):
        result = "{"
        for i, cur in enumerate(self.filterList):
            if i != 0:
                result += " --> "
            result += str(cur)
        result += "}"
        return result

class Expression:
    def __init__(self, leftExpression, operator, rightExpression):
        self.left = leftExpression
        self.op = operator
        self.right = rightExpression
    def __repr__(self):
        return "(%s %s %s)" % (self.left, self.op, self.right)

class Condition:
    def __init__(self, key, comparator, value):
        self.key = key
        self.comparator = comparator
        self.value = value
    def __repr__(self):
        return "%s %s %s" % (self.key, self.comparator, self.value)

if __name__ == "__main__":
    # Example: (key1="val1" || (key2="val2" && key3="val3")) && ((key4="val4" && key5="val5") || key6="val6")
    #   - Expression (type: AND)
    #       - Expression (type: OR)
    #           - Condition (key: "key1", comparator: EQ, value: "val1")
    #           - Expression (type: AND)
    #               - Condition (key: "key2", comparator: EQ, value: "val2")
    #               - Condition (key: "key3", comparator: EQ, value: "val3")
    #       - Expression (type: OR)
    #           - Expression (type: AND)
    #               - Condition (key: "key4", comparator: EQ, value: "val4")
    #               - Condition (key: "key5", comparator: EQ, value: "val5")
    #           - Condition (key: "key6", comparator: EQ, value: "val6")

    # First branch
    cond2 = Condition("key2", Comparator.EQUALS, "val2")
    cond3 = Condition("key3", Comparator.EQUALS, "val3")
    expr1 = Expression(cond2, Operator.AND, cond3)
    cond1 = Condition("key1", Comparator.EQUALS, "val1")
    expr2 = Expression(cond1, Operator.OR, expr1)

    # Second branch
    cond4 = Condition("key4", Comparator.EQUALS, "val4")
    cond5 = Condition("key5", Comparator.EQUALS, "val5")
    expr3 = Expression(cond4, Operator.AND, cond5)
    cond6 = Condition("key6", Comparator.EQUALS, "val6")
    expr4 = Expression(expr3, Operator.OR, cond6)

    # Whole query
    expr5 = Expression(expr2, Operator.AND, expr4)

    # Build a silly filter for test issues
    test = FilterCollection()
    test.addNewFilter(expr5)
    test.addNewFilter(expr4)
    test.addNewFilter(expr3)
    test.addNewFilter(expr2)
    test.addNewFilter(expr1)
    print test

