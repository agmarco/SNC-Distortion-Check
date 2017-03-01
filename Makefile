SHELL := /bin/bash
.SUFFIXES:
.DEFAULT:


.PRECIOUS: tmp/%-voxels.mat tmp/%-unregistered-points.mat tmp/%-matched-points.mat tmp/%-registration.matk

all: $(patsubst data/dicom/%.zip,tmp/%-report.pdf,$(wildcard data/dicom/*))

voxels: $(patsubst data/dicom/%.zip,tmp/%-voxels.mat,$(wildcard data/dicom/*))

unregistered-points: $(patsubst data/dicom/%.zip,tmp/%-unregistered-points.mat,$(wildcard data/dicom/*))


.PYTHONDEPS: requirements.txt dev-requirements.txt
	pip install -r requirements.txt
	pip-sync requirements.txt dev-requirements.txt
	nbstripout --install --attributes .gitattributes
	touch $@


tmp/%-voxels.mat: data/dicom/%.zip .CONDABUILD
	./dicom2voxels $< $@

tmp/%-unregistered-points.mat: tmp/%-voxels.mat .CONDABUILD
	./feature_detection $< $@

tmp/%-matched-points.mat: tmp/%-voxels.mat tmp/%-unregistered-points.mat .CONDABUILD
	./register_golden $< $(word 2,$^) $@

tmp/%-report.pdf: tmp/%-matched-points.mat .CONDABUILD
	./report $< $@


tmp/%-distortion.mat: tmp/%-voxels.mat tmp/%-matched-points.mat .CONDABUILD
	./interpolate $< $(word 2,$^) $@


.PHONY: clean devsetup

devsetup: .PYTHONDEPS
	cp .sample.env .env
	./createdb

clean:
	git clean -fqx tmp
