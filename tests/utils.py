from django import test
from dingos.models import *
from dingos.core.datastructures import DingoObjDict

from dingos.import_handling import DingoImportHandling \
    , EXIST_PLACEHOLDER \
    , EXIST_ID_AND_EXACT_TIMESTAMP \
    , EXIST_ID_AND_NEWER_TIMESTAMP \
    , EXIST_ID_AND_OLDER_TIMESTAMP

import dingos.core.datastructures as datastructures

import pprint

pp = pprint.PrettyPrinter(indent=2)

from dingos.models import dingos_class_map


def object_counter():
    """
    Returns a tuple that contains counts of how many objects of each model
    defined in dingos.models are in the database.
    """
    class_names = dingos_class_map.keys()
    class_names.sort()
    result = []
    for class_name in class_names:
        result.append((class_name, len(dingos_class_map[class_name].objects.all())))
    return result


def object_count_delta(count1, count2):
    """
    Calculates the difference between to object counts.
    """
    result = []
    for i in range(0, len(count1)):
        if (count2[i][1] - count1[i][1]) != 0:
            result.append((count1[i][0], count2[i][1] - count1[i][1]))
    return result


def deltaCalc(func):
    """
    This is a decorator that wraps functions for test purposes with
    a count of objects in the database. It returns the
    delta of the objects for each model class along with
    the result of the tested function.
    """

    def inner(*args, **kwargs):
        count_pre = object_counter()
        #print "PRE"
        #pp.pprint(count_pre)
        result = func(*args, **kwargs)
        count_post = object_counter()
        #print "POST"
        #pp.pprint(count_post)
        delta = object_count_delta(count_pre, count_post)
        #print "DELTA"
        #pp.pprint(delta)
        return (delta, result)

    return inner


def assertEquality(tuple_one, tuple_two):
    tuple_one_keys = []
    tuple_one_attr = []
    flag = True
    list_flag = False
    if type(tuple_one) is str:
        return True

    for tuple in tuple_one:
        if type(tuple) is not type(('one', 'two')):
            #print "Its a list!!"
            list_flag = True
        else:
            if tuple[0][0] == "@":
                tuple_one_keys.append(tuple[0])
            else:
                #print tupl
                #print "$$$$$$$$"
                tuple_one_attr.append(tuple[0])
    tuple_one_keys.sort()
    tuple_one_attr.sort()

    tuple_two_keys = []
    tuple_two_attr = []
    for tuple in tuple_two:
        if type(tuple) is not type(('one', 'two')):
            #print "Its a list!!"
            list_flag = True
        else:
            if tuple[0][0] == '@':
                tuple_two_keys.append(tuple[0])
            else:
                tuple_two_attr.append(tuple[0])
    tuple_two_keys.sort()
    tuple_two_attr.sort()
    if list_flag == True:
        return (assertEquality(tuple_one[1], tuple_two[1]))


    # Key comparison
    if set(tuple_one_keys) == set(tuple_two_keys):
        for x in tuple_one_keys:
            if dict(tuple_one)[x] == dict(tuple_two)[x]:
                flag = True
            else:
                print "Error! Value are not equal for %s" % x
                flag = False
    else:
        print"Error! keys are not equal for %s and %s" % (tuple_one_keys, tuple_two_keys)
        flag = False

    if set(tuple_one_attr) == set(tuple_two_attr):
        for x in tuple_one_attr:
            assertEquality(dict(tuple_one)[x], dict(tuple_two)[x])
    else:
        print "Error! Attributes are not equal for %s and %s" % (tuple_one_attr, tuple_two_attr)
        print "dict one"
        print (dict(tuple_one))
        print "dict two"
        print (dict(tuple_two))

        print"\n\n"
        flag = False

    if flag == True:
        return True
    else:
        return False


