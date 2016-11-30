# CIRS Geometric Distortion Platform

## System Dependencies

- [Conda](http://conda.pydata.org/docs/install/quick.html)
- Linux utilities (e.g. Make)


## Installation

Once have met all the system dependencies, run:

    make .CONDABUILD
    . activate cirs
    make

and it should install everything.

## Tests

Run tests using

    PYTHONPATH=. py.test
