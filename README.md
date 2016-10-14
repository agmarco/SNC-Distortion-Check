# CIRS Geometric Distortion Platform

## Installation

You will first need to [install conda](http://conda.pydata.org/docs/install/quick.html), and then setup and enter a virtual environment.

Once you have installed conda, run:

    conda create -n cirs && . activate cirs

You can then build the environment using:

    make

## Tests

Run tests using

    py.test

## Developer Notes

We use ipython notebooks for some of the algorithm development.  In order to
avoid committing the output of these notebooks, a [git
filter](https://github.com/kynan/nbstripout) is automatically setup as part of
the build process that filters out the unwanted parts of the notebooks.
