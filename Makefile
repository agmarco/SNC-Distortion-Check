SHELL := /bin/bash
.SUFFIXES:
.DEFAULT:

IN_ENV := . activate cirs &&

test_data := $(patsubst data/%,tmp/%-unregistered-points.mat,$(wildcard data/*))

.PRECIOUS: tmp/%-voxels.mat tmp/%-unregistered-points.mat tmp/%-points.mat

all: $(test_data)

BUILD_INFO: environment.yml
	conda env create --force --file $<
	$(IN_ENV) nbstripout --install --attributes .gitattributes
	git rev-parse HEAD > $@

tmp/%-voxels.mat: data/% BUILD_INFO
	$(IN_ENV) ./dicom2mat $</* $@

tmp/%-unregistered-points.mat: tmp/%-voxels.mat BUILD_INFO
	$(IN_ENV) ./detect_features $< $@

tmp/%-points.mat: tmp/%-unregistered-points.mat BUILD_INFO
	$(IN_ENV) ./register $< $@


.PHONY: clean cleanall freezedeps

clean:
	git clean -fqx tmp

cleanall: clean
	. deactivate && conda remove -y --name cirs --all
	rm BUILD_INFO

freezedeps:
	$(IN_ENV) conda env export | sed '/^prefix: /d' > environment.yml
