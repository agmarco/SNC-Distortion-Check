SHELL := /bin/bash
.SUFFIXES:
.DEFAULT:

IN_ENV := . activate cirs &&

test_data := $(patsubst data/dicom/%,tmp/%-report.pdf,$(wildcard data/dicom/*))

.PRECIOUS: tmp/%-voxels.mat tmp/%-unregistered-points.mat tmp/%-points.mat tmp/%-registration.mat

all: $(test_data)

.CONDABUILD: environment.yml
	conda env create --force --file $<
	$(IN_ENV) nbstripout --install --attributes .gitattributes
	git rev-parse HEAD > $@

tmp/%-voxels.mat: data/dicom/% .CONDABUILD
	$(IN_ENV) ./dicom2mat $</* $@

tmp/%-unregistered-points.mat: tmp/%-voxels.mat .CONDABUILD
	$(IN_ENV) ./detect_features $< $@

tmp/%-registration.mat: tmp/%-unregistered-points.mat .CONDABUILD
	$(IN_ENV) ./register ./data/points/603A_CAD.mat $< $@

tmp/%-points.mat: tmp/%-registration.mat tmp/%-unregistered-points.mat .CONDABUILD
	$(IN_ENV) ./applyaffine $< $(word 2,$^) $@

tmp/%-report.pdf: tmp/%-points.mat .CONDABUILD
	$(IN_ENV) ./report ./data/points/603A_CAD.mat $< $@


.PHONY: clean cleanall freezedeps

clean:
	git clean -fqx tmp

cleanall: clean
	. deactivate && conda remove -y --name cirs --all
	rm .CONDABUILD

freezedeps:
	$(IN_ENV) conda env export | sed '/^prefix: /d' > environment.yml
