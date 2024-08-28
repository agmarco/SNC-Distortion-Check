SHELL := /bin/bash
.SUFFIXES:
.DEFAULT:

# Set the PYTHONPATH to include the root of the project
export PYTHONPATH := $(shell pwd):$(PYTHONPATH)

all: $(patsubst data/dicom/%.zip,tmp/%-voxels.mat,$(wildcard data/dicom/*))

tmp/%-voxels.mat: data/dicom/%.zip
	./bin/dicom2voxels $< $@


.PHONY: freezedeps

freezedeps:
	pip-compile requirements.in > requirements.txt
	pip-compile dev-requirements.in > dev-requirements.txt
