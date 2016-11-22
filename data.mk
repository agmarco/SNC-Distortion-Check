decimation_factors := 2 3 4
decimated_data_paths := $(foreach decimation_factor, $(decimation_factors), $(addsuffix  -$(decimation_factor).mat,$(patsubst data/dicom/%,tmp/%-voxels-decimated,$(wildcard data/dicom/*))))

tmp/%-voxels-decimated-2.mat: tmp/%-voxels.mat .CONDABUILD
	./testing/decimate_slices.py $< $@ 2

tmp/%-voxels-decimated-3.mat: tmp/%-voxels.mat .CONDABUILD
	./testing/decimate_slices.py $< $@ 3

tmp/%-voxels-decimated-4.mat: tmp/%-voxels.mat .CONDABUILD
	./testing/decimate_slices.py $< $@ 4



distortion_factors := 0.01 0.04 0.08
distortion_paths := $(foreach distortion_factor, $(distortion_factors), $(addsuffix  -$(distortion_factor).mat,$(patsubst data/dicom/%,tmp/%-voxels-distorted,$(wildcard data/dicom/*))))

tmp/%-voxels-distorted-0.01.mat: tmp/%-voxels.mat .CONDABUILD
	./testing/distort_voxel.py $< $@ --distort_factor 0.01

tmp/%-voxels-distorted-0.04.mat: tmp/%-voxels.mat .CONDABUILD
	./testing/distort_voxel.py $< $@ --distort_factor 0.04

tmp/%-voxels-distorted-0.08.mat: tmp/%-voxels.mat .CONDABUILD
	./testing/distort_voxel.py $< $@ --distort_factor 0.08

data: $(decimated_data_paths) $(distortion_paths)
