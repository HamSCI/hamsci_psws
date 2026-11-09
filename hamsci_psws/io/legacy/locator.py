import string
import numpy as np
import pandas as pd
import tqdm

# Standard numpy string arrays (replaces deprecated np.char.array)
alpha_upper = np.array(list(string.ascii_uppercase))
alpha_lower = np.array(list(string.ascii_lowercase))
nr_str      = np.array([str(x) for x in range(10)])

def inx_alpha(inx):
    """Determine if a string position should be alpha in a grid square."""
    if (inx % 2): inx -= 1
    alpha = not bool((inx/2) % 2)
    return alpha

@np.vectorize
def grid_valid(grid):
    """Determine if a gridsquare is valid."""
    global pbar
    pbar.update(1)
    try:
        gs_len = len(grid)
    except:
        return False

    if gs_len == 0 or gs_len % 2:
        return False

    for inx, char in enumerate(grid):
        should_be_alpha = inx_alpha(inx)
        valid = not should_be_alpha ^ char.isalpha()
        if not valid:
            return False
    return True

def latlon2gridsquare(lat, lon, precision=6):
    """Calculates gridsquares from lat,lon pairs."""
    lats_0 = np.array(lat)
    lons_0 = np.array(lon)

    lats_1 = lats_0.flatten()
    lons_1 = lons_0.flatten()

    lat_lon_good_tf = np.logical_and(np.isfinite(lats_1), np.isfinite(lons_1))

    lats = lats_1[lat_lon_good_tf]
    lons = lons_1[lat_lon_good_tf]

    tf = lons > 180.
    lons[tf] -= 360.

    zLats = lats +  90.
    zLons = lons + 180.

    base = 18.
    container_size_lat = 180.
    container_size_lon = 360.
    subdivide_size_lat = container_size_lat / base
    subdivide_size_lon = container_size_lon / base

    zLats_rem = zLats % container_size_lat
    zLons_rem = zLons % container_size_lon

    lat_code_inx = np.array(np.floor(zLats_rem / subdivide_size_lat), dtype=int)
    lon_code_inx = np.array(np.floor(zLons_rem / subdivide_size_lon), dtype=int)

    lon_code  = alpha_upper[lon_code_inx]
    lat_code  = alpha_upper[lat_code_inx]
    this_code = np.char.add(lon_code, lat_code)

    grid_square = this_code
    curr_prec   = 2

    while curr_prec < precision:
        alpha = not bool((curr_prec/2) % 2)
        if alpha:
            base     = 24
            str_code = alpha_lower
        else:
            base     = 10.
            str_code = nr_str

        container_size_lat = subdivide_size_lat
        container_size_lon = subdivide_size_lon
        subdivide_size_lat = container_size_lat / base
        subdivide_size_lon = container_size_lon / base

        zLats_rem = zLats_rem % container_size_lat
        zLons_rem = zLons_rem % container_size_lon

        lat_code_inx = np.array(np.floor(zLats_rem / subdivide_size_lat), dtype=int)
        lon_code_inx = np.array(np.floor(zLons_rem / subdivide_size_lon), dtype=int)

        lon_code    = str_code[lon_code_inx]
        lat_code    = str_code[lat_code_inx]
        this_code   = np.char.add(lon_code, lat_code)
        grid_square = np.char.add(grid_square, this_code)
        curr_prec  += 2

    ret_arr                  = np.zeros([lats_1.size], dtype=grid_square.dtype)
    ret_arr[lat_lon_good_tf] = grid_square
    return ret_arr.reshape(lats_0.shape)