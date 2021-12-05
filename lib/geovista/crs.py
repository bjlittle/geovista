from pyproj import CRS

__all__ = [
    "PlateCarree",
    "TransverseMercator",
    "WGS84",
]


#
# Geodetic (Geographic) Coordinate Reference Systems
#

WGS84 = CRS.from_user_input("epsg:4326")


#
# Projected Coordinate Reference Systems
#

# WGS 84 / Plate Carree (Equidistant Cylindrical)
PlateCarree = CRS.from_user_input("epsg:32662")

# WGS 84 / Transverse Mercator
TransverseMercator = CRS.from_user_input(
    "+proj=tmerc +lat_0=0 +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs +type=crs"
)
