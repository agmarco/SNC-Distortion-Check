import os
import sys
import operator
import types



def print_error(message):
    print(message, file=sys.stderr)


def find_here_or_in_parents(start_directory, entryname):
    current_directory = os.path.abspath(start_directory)

    while current_directory != '/':
        test_entryname = os.path.join(current_directory, entryname)
        if os.path.exists(test_entryname):
            return test_entryname
        else:
            current_directory = os.path.dirname(current_directory)

    return None


def repository_root(start_directory):
    git_directory = find_here_or_in_parents(start_directory, '.git')
    if git_directory is None:
        raise ValueError('Not in a git repository')
    else:
        return os.path.dirname(git_directory)


def is_manually_verified(result):
    for stamp in result['stamps']:
        if stamp['accepted'] and stamp['verified_against'] is None:
            return True
    return False


def deep_equal(_v1, _v2):
    """
    Tests for deep equality between two python data structures recursing
    into sub-structures if necessary. Works with all python types including
    iterators and generators. This function was dreampt up to test API responses
    but could be used for anything. Be careful. With deeply nested structures
    you may blow the stack.
    """
    def _deep_dict_eq(d1, d2):
        k1 = sorted(d1.keys())
        k2 = sorted(d2.keys())
        if k1 != k2: # keys should be exactly equal
            return False
        return sum(deep_eq(d1[k], d2[k]) for k in k1) == len(k1)

    def _deep_iter_eq(l1, l2):
        if len(l1) != len(l2):
            return False
        return sum(deep_eq(v1, v2) for v1, v2 in zip(l1, l2)) == len(l1)

    op = operator.eq
    c1, c2 = (_v1, _v2)

    # guard against strings because they are also steerable
    # and will consistently cause a RuntimeError (maximum recursion limit reached)
    for t in types.StringTypes:
        if isinstance(_v1, t):
            break
    else:
        if isinstance(_v1, types.DictType):
            op = _deep_dict_eq
        else:
            try:
                c1, c2 = (list(iter(_v1)), list(iter(_v2)))
            except TypeError:
                c1, c2 = _v1, _v2
            else:
                op = _deep_iter_eq

    return op(c1, c2)
