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

.JSDEPS: client/yarn.lock
	npm install yarn
	cd client; yarn
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

.env:
	cp .sample.env $@


.PHONY: clean cleandev dev freezedeps static

dev: .PYTHONDEPS .JSDEPS static | .env
	./createdb
	python server/manage.py generate_dev_data

static: .PYTHONDEPS .JSDEPS
	cd client; yarn webpack:dev
	python server/manage.py collectstatic --noinput

freezedeps:
	pip-compile requirements.in > requirements.txt
	pip-compile dev-requirements.in > dev-requirements.txt

clean:
	git clean -fqx tmp
	git clean -fqx .hdattarchive
	rm -fr collected_static
	rm -fr client/dist

cleandev: clean
	./droppostgresdb || echo 'Unable to drop Postgres DB'
	./dropredisdb || echo 'Unable to drop Redis DB'
	git clean -fqx
