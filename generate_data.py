#!/usr/bin/env python
from subprocess import call

from test_utils import get_test_data_generators

data_generators = get_test_data_generators()
make_rules = [data_generator.make_rule for data_generator in data_generators]
all_targets = {target for rule in make_rules for target in rule.targets}
with open('data.mk', 'w') as makefile:
    makefile.write('all: '+' '.join(all_targets))
    makefile.write('\n')
    for rule in make_rules:
        makefile.write('\n')
        makefile.write(str(rule))
        makefile.write('\n')

call(['make', '-j8', '-f', 'data.mk'])
