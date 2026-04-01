import pandas as pd
from geopy.distance import geodesic

def spocitej_km(moje_gps, gps_doktora):
    """Vypočítá vzdálenost pro GPS formát oddělený mezerou."""
    if pd.isna(gps_doktora) or str(gps_doktora).strip() == "":
        return 9999.0
    try:
        parts = str(gps_doktora).strip().split()
        if len(parts) != 2:
            return 9999.0
        lat = float(parts[0])
        lon = float(parts[1])
        return geodesic(moje_gps, (lat, lon)).km
    except:
        return 9999.0