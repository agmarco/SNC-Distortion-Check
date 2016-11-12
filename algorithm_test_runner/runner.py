import os
import sys
import pydoc

from algorithm_test_runner.util import print_error, repository_root, find_here_or_in_parents
from algorithm_test_runner.result_store import ResultStore


def suite_id_to_class_map(directory):
    suite_classes = collect_suite_classes(directory)
    mapping = {}
    for suite in suite_classes:
        name = suite.name()
        if name in mapping:
            print_error('Duplicate suite name "{}"'.format(name))
        else:
            mapping[name] = suite
    return mapping


def collect_suite_classes(directory):
    suites_filename = find_here_or_in_parents(directory, '.algtr')
    if suites_filename is None:
        raise ValueError('Unable to locate a ".algtr" file')

    suite_classes = []
    with open(suites_filename, 'r') as suites_file:
        for line in suites_file:
            class_location = line.strip()
            try:
                test_suite_class = pydoc.locate(class_location)
            except pydoc.ErrorDuringImport as e:
                print_error(e)
                test_suite_class = None

            if test_suite_class is None:
                msg = 'Unable to import test suite "{}"'
                print_error(msg.format(class_location))
            else:
                suite_classes.append(test_suite_class)

    return suite_classes


def initialize_stores(start_directory):
    repo_store_location = os.path.join(repository_root(start_directory), '.algtrstore')
    repo_store = ResultStore(repo_store_location)
    return [repo_store]
