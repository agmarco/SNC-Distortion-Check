import os
import sys
import pydoc


def collect_suite_classes(directory):
    suites_filename = find_file_here_or_in_parents(directory, '.algtr')
    if suites_filename is None:
        print('Unable to locate a ".algtr" file', file=sys.stderr)
        sys.exit(1)

    suite_classes = []
    with open(suites_filename, 'r') as suites_file:
        for line in suites_file:
            class_location = line.strip()
            try:
                test_suite_class = pydoc.locate(class_location)
            except pydoc.ErrorDuringImport as e:
                test_suite_class = None

            if test_suite_class is None:
                msg = 'Unable to import test suite "{}"'
                print(msg.format(class_location), file=sys.stderr)
            else:
                suite_classes.append(test_suite_class)

    return suite_classes


def find_file_here_or_in_parents(start_directory, filename):
    current_directory = os.path.abspath(start_directory)

    while current_directory != '/':
        test_filename = os.path.join(current_directory, filename)
        if os.path.isfile(test_filename):
            return test_filename
        else:
            current_directory = os.path.dirname(current_directory)

    return None
