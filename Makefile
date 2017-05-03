SHELL := /bin/bash
.SUFFIXES:
.DEFAULT:


.PRECIOUS: tmp/%-voxels.mat tmp/%-unregistered-points.mat tmp/%-matched-points.mat tmp/%-registration.matk

all: $(patsubst data/dicom/%.zip,tmp/%-report.pdf,$(wildcard data/dicom/*))

voxels: $(patsubst data/dicom/%.zip,tmp/%-voxels.mat,$(wildcard data/dicom/*))

unregistered-points: $(patsubst data/dicom/%.zip,tmp/%-unregistered-points.mat,$(wildcard data/dicom/*))


tmp/%-voxels.mat: data/dicom/%.zip
	./process/dicom2voxels $< $@

tmp/%-unregistered-points.mat: tmp/%-voxels.mat
	./process/feature_detection $< $@

tmp/%-matched-points.mat: tmp/%-voxels.mat tmp/%-unregistered-points.mat
	./process/register_golden $< $(word 2,$^) $@

tmp/%-report.pdf: tmp/%-matched-points.mat
	./process/report $< $@

tmp/%-distortion.mat: tmp/%-voxels.mat tmp/%-matched-points.mat
	./process/interpolate $< $(word 2,$^) $@


.PHONY: freezedeps

freezedeps:
	pip-compile requirements.in > requirements.txt
	pip-compile dev-requirements.in > dev-requirements.txt
