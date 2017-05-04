# CIRS Geometric Distortion Platform

## System Dependencies

- Python 3.6
- Redis
- Postgres
- Linux utilities (e.g. Make)
- Lib HDF5

You can install all of these using homebrew pretty easily on mac.

## Hot Module Replacement

You can enable hot module replacement using:

    yarn run build:hot

## Interactive Algorithm Work

You will need to swap out the matplotlib backend for interactive algorithm
work; see `matplotlibrc` for details.
