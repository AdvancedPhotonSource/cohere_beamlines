import numpy as np

def get_max_crop_slice(data, max_crop, scan_axis):
    def is_on_edge(maxindx):
        onedge = False
        for i in range(len(maxindx)):
            if maxindx[i] == 0 or maxindx[i] > data.shape[i] - 1:
                onedge = True
                break
        return onedge

    # check if the max value is bad pixel. If so zero it and get the next max value.
    maxpos = np.unravel_index(data.argmax(), data.shape)
    # remove the index of scan_axis to leave only frame
    maxpos.pop(scan_axis)

    while (is_on_edge(maxpos) or
           data[maxpos[0] + 1, maxpos[1], maxpos[2]] == 0
           and data[maxpos[0] - 1, maxpos[1], maxpos[2]] == 0
           or data[maxpos[0], maxpos[1] + 1, maxpos[2]] == 0
           and data[maxpos[0], maxpos[1] - 1, maxpos[2]] == 0):
        data[maxpos] = 0.0
        maxpos = np.unravel_index(data.argmax(), data.shape)
        # remove the index of scan_axis to leave only frame
        maxpos.pop(scan_axis)

    mc0 = max_crop[0] // 2
    mc1 = max_crop[1] // 2
    maxslice = np.s_[::,
               max(0, maxpos[1] - mc0): min(maxpos[1] + mc0, data.shape[1]),
               max(0, maxpos[2] - mc1): min(maxpos[2] + mc1, data.shape[2])]
    data = data[maxslice]
    # print(data.shape, "shape", maxpos, "maxpos")
    return data
