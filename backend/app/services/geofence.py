from math import radians, sin, cos, asin, sqrt
from typing import Iterable

EARTH_RADIUS_KM = 6371.0


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in meters between two lat/lon points."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = EARTH_RADIUS_KM * c
    return km * 1000.0


def inside_radius(lat1: float, lon1: float, lat2: float, lon2: float, radius_m: float) -> bool:
    return haversine_distance_m(lat1, lon1, lat2, lon2) <= radius_m
