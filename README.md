# CIRS Geometric Distortion Platform

## Installation

You will first need to [install conda](http://conda.pydata.org/docs/install/quick.html), and then setup and enter a virtual environment.

Once you have installed conda, run:

    make

and it should install everything.  You may want to enter the conda environment
(e.g. so you can run tests).  You can do this using

    . activate cirs

## Tests

Run tests using

    py.test

## Developer Notes

We use ipython notebooks for some of the algorithm development.  In order to
avoid committing the output of these notebooks, a [git
filter](https://github.com/kynan/nbstripout) is automatically setup as part of
the build process that filters out the unwanted parts of the notebooks.
