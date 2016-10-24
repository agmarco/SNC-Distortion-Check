'''
# How to Test Image Processing Algorithms

Testing image processing algorithms is difficult and time consuming, but is
critical to developing and maintaining robust software in the face of highly
varied outputs.

This article describes why testing image processing algorithms is challenging,
and then discusses several testing tools and techniques that work especially
well with image processing algorithms.

## The Problem

First, lets discuss in more detail why image processing algorithms require a
unique approach to testing.

Developing and testing image processing algorithms is challenging for the
following reasons:

- inputs have high dimensionality (e.g. a 512x512x80 array of MR voxels)
- too few input datasets are available initially
- the outputs have high dimensionality and must be verified manually
- the outputs are unstable
- the algorithms are computationally intensive, and are thus slow.

The high dimensionality of your input dataset means that it is impossible to
enumerate even a small portion of the input space.  When dealing with more
structured data (e.g. a JSON file) you can validate and reject bad inputs. When
working with images and volume, it is often difficult to identify and reject
bad inputs.  For example, imagine you are building a tool that segments
the liver from abdominal MRI datasets.  How can you identify and reject an MRI
dataset of the head?

Typically when developing image processing algorithms, you will only have a
few sample inputs to work with.  As a result, your initial implementation will
likely be overfit to a small portion of the input space.  As you collect more
datasets (e.g. from bug reports provided by customers) you will need to make
your algorithm handle the new cases, while also not breaking how it handles the
old cases.

The outputs from the algorithm often also have high-dimensionality.  In the
MRI segmentation algorithm the output may be a binary volumes array and a
confidence interval.  It is difficult to write simple assertions
about what the output is expected to look like.  In fact, in many cases there
is no "gold standard" to compare against, and thus the correct output for any
given input can only be verified manually.  Manual verification is
time-consuming and error prone.

A further problem with the outputs generated from image processing algorithms
is that they are unstable.  Almost any change to the algorithm will cause all
of the outputs to change slightly.  This instability makes testing difficult
because simple assertions about the algorithm's output will cause the tests
to fail after every change.  Tests that fail after every change are nearly
useless.

Finally, many image processing algorithms are slow because they are dealing
with large amounts of data.  Slow tests are extremely problematic for many
reasons.  They increase the length of time that tickets remain open, which
forces developers to jump between many tasks while waiting for their tests to
complete and also increases the chances of merge conflicts.

## Core Concepts

The central idea is to use a testing framework that

- Provides tools to streamline the manual verification process
- Minimizes how frequently outputs need to be manually verified
- Makes it easy to add new test cases
- Avoids unnecessary test runs using historical data.

In the following sections, we will describe how to setup a testing system that
accomplishes all of this.

## Easy Manual Verification

Ideally, software can be automatically tested with no human input.  This is how
we test most aspects of software.  Unit tests verify individual functions and
classes; integration tests verify how modules interact; user interface tests
simulate clicking through the UI.  The cost of developing and maintaining these
tests increases at each level of abstraction, but typically all of them are
deemed worthwhile because the development cost is lower than the cost of
maintain software without them.

In the case of image processing algorithms, writing fully automatic tests can be
more difficult than developing the algorithm itself!  In fact, it is often
impossible to automate the tests because the test *is* the algorithm.  For
example, verifying that the MRI segmentation algorithm works is more or less
equivalent to writing the algorithm in the first place.

For these reasons, manual verification is often unavoidable.

Manual verification of algorithm output is slow and error prone, so we should
develop tools that make it extremely simple to visualize and verify the output
of an algorithm run.  For example, in the MRI segmentation algorithm, we may
want to display the ROI as an overlay on the input dataset.  Metadata about the
input scan (e.g certain DICOM tags) should be accessible.  Also, derived
quantities, such as the volume of the ROI, should be displayed as well.  All of
this visualization should be accessible very easily, ideally by running a single
command.

It should also be easy to compare two sets of output, so that previous runs
can be compared to new runs after the algorithm has been changed.

## Historical Comparison

Streamlining manual verification is a good first step, however even so, manual
verification should be avoided whenever possible.

The key to accomplishing this is to:

1. Run the algorithm against an input dataset
2. Manually verify the output
3. Record the output
4. Compare future runs against this input to the manually verified output.

A crude way to accomplish this is to manually run and verify the algorithm, and
then to copy and paste the result into a test case.  There are a number of
major problems with this approach.

First of all, adding new test cases involves writing code.  It also many invovle

'''


def compare(output, case, spec):
    return


'''
Given JSON output from a function,

a case containing:

- (JSON input)
- (JSON output)
- a series of case-specific "specs",

global specs

Determine if the test "passes".

A pass means that every spec was satisfied.

A spec contains:

    - A JSON pointer to a "number"
    - One of:
        - "same"
        - "max_decrease" min
        - "max_increase" max
        - "max_percent_increase" percent relative to prev
        - "max_percent_decrease" percent relative to prev
        - "within" change
        - "within_percent" percent relative to prev

The result will be:

    - "large improvement"
    - "improvement" (for at_least or at_most, is better than the orig value
    - "pass"
    - "too large"
    - "too small"
    - "missing"
    - "appeared"
    - "changed"
    - "exception"

It would be nice if our tool did:

    1. clustering analysis
    2. historical analysis? would need more than just one run
    3. would let you quickly iterate through all of the cases
'''

case = {
    "input": [1, 2, 10],
    "output": {
        "max": 10,
    }
}

spec = {
    "max": {"same"},
}


def runner(cases, func):
    # TODO: validate spec first
    # TODO: validate cases one-by-one first
    outputs = {}
    for name, case in cases.items():
        try:
            new_output = func(case['input'])
        except:
            # TODO: add more details
            continue
        outputs[name] = new_output
    return outputs


def validate_assertions(old_output, spec):


def validate_case(old_output, spec):



def comparator(old_output, new_output, spec):
    results = {}
    for key, assertions in spec.items():
        if key in old_output and key not in new_output:
            results[key] = {"result": "missing"}
            continue

        if key not in old_output and key in new_output:
            results[key] = {"result": "appeared"}
            continue

        old = old_output[key]
        new = new_output[key]


def comparator_same(old, new, _):
    return 'pass' if old == new else 'changed'


def comparator_within(old, new, change):
    return 'pass' if abs(new - old) < change else 'changed'


def comparator_within_relative(old, new, relative_change):
    return 'pass' if abs(new - old) < abs(old)*relative_change else 'changed'


def comparator_at_least(old, new, change):
    if new < old - change:
        return 'too small'
    elif new <= old:
        return 'pass'
    else:
        return 'improved'


def comparator_at_most(old, new, change):
    if new > old + change:
        return 'too large'
    elif new >= old:
        return 'pass'
    else:
        return 'improved'


def comparator_at_most_relative(old, new, relative_change):
    if new > old + change:
        return 'too large'
    elif new >= old:
        return 'pass'
    else:
        return 'improved'
