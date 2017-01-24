int calc_index_clamped(int3 coord, int3 sizes){
    int x_clamped = clamp(coord.x, 0, sizes.x-1);
    int y_clamped = clamp(coord.y, 0, sizes.y-1);
    int z_clamped = clamp(coord.z, 0, sizes.z-1);
    return z_clamped + y_clamped*sizes.z + x_clamped*sizes.z*sizes.y;
}

bool is_first(){
    return get_global_id(0) == 0 && get_global_id(1) == 0 && get_global_id(2) == 0;
}

__kernel void find_peaks(__global const float *source_g, __global float *res_g, __global int *offsets, int offset_length){
    int3 coord_v =(int3)(get_global_id(0), get_global_id(1), get_global_id(2));
    int3 sizes_v = (int3)(get_global_size(0),  get_global_size(1), get_global_size(2));
    int index = calc_index_clamped(coord_v, sizes_v);
    float value = source_g[index];
    int subindex;
    float subvalue;
    float found_min = INFINITY;
    for(int i=0; i<offset_length; i++){
        int3 offset = vload3(i, offsets);
        subindex = calc_index_clamped(coord_v + offset, sizes_v);
        subvalue = source_g[subindex];
        if(subvalue > value){
            res_g[index] = 0;
            return;
        }
        found_min = min(found_min, subvalue);
    }
    res_g[index] = value-found_min;
}
