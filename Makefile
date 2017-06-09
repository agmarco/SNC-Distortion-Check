SHELL := /bin/bash
.SUFFIXES:
.DEFAULT:

all: $(patsubst data/dicom/%.zip,tmp/%-voxels.mat,$(wildcard data/dicom/*))

tmp/%-voxels.mat: data/dicom/%.zip
	./process/dicom2voxels $< $@


.PHONY: freezedeps

freezedeps:
	pip-compile requirements.in > requirements.txt
	pip-compile dev-requirements.in > dev-requirements.txt
