import pyopencl as cl
import numpy as np

def find_peaks(voxels, search_neighborhood):
    offset_around_center = np.where(search_neighborhood) - ((np.array(search_neighborhood.shape) - 1) / 2).reshape(3, 1)
    search_offsets = np.vstack(offset_around_center).T.astype(np.int32)

    ctx = cl.create_some_context(interactive=True)
    queue = cl.CommandQueue(ctx)
    mf = cl.mem_flags
    hostbuf = voxels.astype(np.float32)
    source_g = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=np.ascontiguousarray(hostbuf))
    offsets_g = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=np.ascontiguousarray(search_offsets))
    res_np = np.zeros_like(hostbuf)
    res_g = cl.Buffer(ctx, mf.WRITE_ONLY, size=res_np.nbytes)
    prg = cl.Program(ctx, """
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
    """).build()
    prg.find_peaks(queue, voxels.shape, None, source_g, res_g, offsets_g, np.int32(search_offsets.shape[0]))
    cl.enqueue_copy(queue, res_np, res_g)
    return res_np
