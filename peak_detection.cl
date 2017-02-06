int index_clamped(int3 coord, int3 sizes){
    int x_clamped = clamp(coord.x, 0, sizes.x - 1);
    int y_clamped = clamp(coord.y, 0, sizes.y - 1);
    int z_clamped = clamp(coord.z, 0, sizes.z - 1);
    return z_clamped + y_clamped*sizes.z + x_clamped*sizes.z*sizes.y;
}

__kernel void find_peaks(
        __global const float *source_g,
        __global float *result_g,
        __global int *neighborhood_offsets,
        int neighbor_size) {

    int3 coord_v = (int3)(get_global_id(0), get_global_id(1), get_global_id(2));
    int3 sizes_v = (int3)(get_global_size(0), get_global_size(1), get_global_size(2));
    int index = index_clamped(coord_v, sizes_v);
    float center_value = source_g[index];
    int neighbor_index;
    float neighbor_value;
    float neighborhood_min = INFINITY;
    for (int i = 0; i < neighbor_size; i++){
        int3 offset = vload3(i, neighborhood_offsets);
        neighbor_index = index_clamped(coord_v + offset, sizes_v);
        neighbor_value = source_g[neighbor_index];
        if (neighbor_value > center_value){
            result_g[index] = 0;
            return;
        }
        neighborhood_min = min(neighborhood_min, neighbor_value);
    }
    result_g[index] = center_value - neighborhood_min;
}
