SHELL := /bin/bash
.SUFFIXES:
.DEFAULT:

IN_ENV := . activate cirs &&


.PRECIOUS: tmp/%-voxels.mat tmp/%-unregistered-points.mat tmp/%-matched-points.mat tmp/%-registration.matk

all: $(patsubst data/dicom/%.zip,tmp/%-report.pdf,$(wildcard data/dicom/*))

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

tmp/%-matched-points.mat: tmp/%-unregistered-points.mat .CONDABUILD
	./register ./data/points/603A_CAD.mat $< $@

tmp/%-report.pdf: tmp/%-matched-points.mat .CONDABUILD
	./report $< $@


tmp/%-distortion.mat: tmp/%-voxels.mat tmp/%-matched-points.mat .CONDABUILD
	./interpolate $< $(word 2,$^) $@


.PHONY: clean cleanall freezedeps

clean:
	git clean -fqx tmp

cleanall: clean
	. deactivate && conda remove -y --name cirs --all
	rm .CONDABUILD

freezedeps:
	conda env export | sed '/^prefix: /d' > environment.yml
