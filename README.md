# CIRS Geometric Distortion Platform

## System Dependencies

- Python 3.6
- Redis
- Postgres
- Linux utilities (e.g. Make)
- Lib HDF5
- Yarn

You can install all of these using homebrew pretty easily on mac.

## Everything

Use this command to install a new dev setup, run all the tests, and then start
all the processes:

    make dev && pytest && honcho start

## Installation

Once have met all the system dependencies (and you are in a virtual environment, if you want one):

    make dev

and it should install a Postgres database all your python dependencies, etc.

You may need to customize your `.env` file to point to your Redis and Postgres installs.

## Clean devsetup

You can remove all temporary files, and drop your development database using:

    make cleandev

You can just clean normal stuff using:

    make clean

See the makefile for details.

## Run Server

You can run the celery task runner and the web server using:

    honcho start

## Tests

Run tests using

    pytest

## Hot Module Replacement

To enable hot module replacement, cd into the `client` directory and run:

    yarn webpack:hot
