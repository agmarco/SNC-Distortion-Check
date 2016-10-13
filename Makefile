SHELL := /bin/bash
.SHELLFLAGS := -e
.SUFFIXES:
.DEFAULT:

tmp/%.mat: data/% | tmp
	./dicom2mat $@ $</*

tmp:
	mkdir -p $@


.PHONY: clean

clean:
	rm -rf tmp
