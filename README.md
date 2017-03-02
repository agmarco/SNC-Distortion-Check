# CIRS Geometric Distortion Platform

## System Dependencies

- Python 3.6
- Redis
- Postgres
- Linux utilities (e.g. Make)
- Lib HDF5

You can install all of these using homebrew pretty easily on mac.

## Installation

Once have met all the system dependencies (and you are in a virtual environment, if you want one):

    make devsetup

and it should install a Postgres database all your python dependencies, etc.

## Run Server

You can run the celery task runner and the web server using:

    honcho start

## Tests

Run tests using

    PYTHONPATH=. py.test
