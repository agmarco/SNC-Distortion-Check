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


tmp/%-voxels.mat: data/dicom/%.zip .PYTHONDEPS
	./process/dicom2voxels $< $@

tmp/%-unregistered-points.mat: tmp/%-voxels.mat .PYTHONDEPS
	./process/feature_detection $< $@

tmp/%-matched-points.mat: tmp/%-voxels.mat tmp/%-unregistered-points.mat .PYTHONDEPS
	./process/register_golden $< $(word 2,$^) $@

tmp/%-report.pdf: tmp/%-matched-points.mat .PYTHONDEPS
	./process/report $< $@


tmp/%-distortion.mat: tmp/%-voxels.mat tmp/%-matched-points.mat .PYTHONDEPS
	./process/interpolate $< $(word 2,$^) $@


.PHONY: clean cleandev dev freezedeps

clientdev:
	cd client/landing; yarn; gulp dev:webpack
	cd client/machine-sequences; yarn; gulp dev:webpack
	cd client/add-phantom; yarn; gulp dev:webpack
	cd client/upload-scan; yarn; gulp dev:webpack

client:
	cd client/landing; yarn; gulp prod
	cd client/machine-sequences; yarn; gulp prod
	cd client/add-phantom; yarn; gulp prod
	cd client/upload-scan; yarn; gulp prod

dev: .PYTHONDEPS
	cp .sample.env .env
	./createdb
	python server/manage.py generate_dev_data
	make clientdev
	python server/manage.py collectstatic --noinput

freezedeps:
	pip-compile requirements.in > requirements.txt
	pip-compile dev-requirements.in > dev-requirements.txt

clean:
	git clean -fqx tmp
	git clean -fqx .hdattarchive

cleandev:
	./dropdb
	git clean -fqx
