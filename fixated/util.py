def nmea_coord_to_dec_deg(coord, nsew):
    '''
    Converts a GPS coordinate string into decimal degrees.

    Parameters:
      coord - The coordinate string
      nsew - The ordinal character

    Example:
      # 72 degrees, 50.1234 minutes
      > print nmea_coord_to_dec_deg('07250.1234', 'E')
      72.83539
    '''
    # Split the string by the decimal point
    min_idx = coord.index('.') - 2

    degree = int(coord[0:min_idx])
    minute = float(coord[min_idx:])

    nsew = nsew.upper()

    return (degree + (minute / 60.0)) * (1 if nsew in ['N', 'E'] else -1)

def ion(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

def flon(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
