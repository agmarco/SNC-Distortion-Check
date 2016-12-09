SHELL := /bin/bash
.SUFFIXES:
.DEFAULT:

IN_ENV := . activate cirs &&

reports := $(patsubst data/dicom/%.zip,tmp/%-report.pdf,$(wildcard data/dicom/*))

.PRECIOUS: tmp/%-voxels.mat tmp/%-unregistered-points.mat tmp/%-points.mat tmp/%-registration.mat

all: reports

voxels: $(patsubst data/dicom/%.zip,tmp/%-voxels.mat,$(wildcard data/dicom/*))

unregistered-points: $(patsubst data/dicom/%.zip,tmp/%-unregistered-points.mat,$(wildcard data/dicom/*))

.CONDABUILD: environment.yml
	conda env create --force --file $<
	$(IN_ENV) nbstripout --install --attributes .gitattributes
	git rev-parse HEAD > $@

tmp/%-voxels.mat: data/dicom/%.zip .CONDABUILD
	./dicom2mat $< $@

tmp/%-unregistered-points.mat: tmp/%-voxels.mat .CONDABUILD
	./detect_features $< $@

tmp/%-registration.mat: tmp/%-unregistered-points.mat .CONDABUILD
	./register ./data/points/603A_CAD.mat $< $@

tmp/%-points.mat: tmp/%-registration.mat tmp/%-unregistered-points.mat .CONDABUILD
	./applyaffine $< $(word 2,$^) $@

tmp/%-report.pdf: tmp/%-points.mat .CONDABUILD
	./report ./data/points/603A_CAD.mat $< $@


.PHONY: clean cleanall freezedeps

clean:
	git clean -fqx tmp

cleanall: clean
	. deactivate && conda remove -y --name cirs --all
	rm .CONDABUILD

freezedeps:
	conda env export | sed '/^prefix: /d' > environment.yml
