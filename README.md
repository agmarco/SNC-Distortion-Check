# CIRS Geometric Distortion Platform

## System Dependencies

- Python 3.6
- Redis
- Postgres
- Linux utilities (e.g. Make)


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
