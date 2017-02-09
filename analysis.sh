#!/bin/bash

make voxels

for radius in 1 0.85 0.7
do
    for spacing in 1.2 1 0.6
    do
        mkdir -p ~/1540/radius-$radius-spacing-$spacing
        GRID_RADIUS=$radius GRID_SPACING=$spacing PYOPENCL_CTX=':' make unregistered-points
        mv tmp/*-unregistered-points.mat ~/1540/radius-$radius-spacing-$spacing/
    done
done
