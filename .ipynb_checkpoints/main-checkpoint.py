import os
import datetime

from mta_gtfs_data_getter import download_gtfs_data
from mta_gtfs_shapefiles_maker import make_bus_routes_shapefiles, make_bus_stops_shapefiles, make_rail_routes_shapefiles, make_rail_stops_shapefiles, make_subway_entrances_shapefiles

path_name = os.getcwd()
# folder = "July2019"
folder = input(
    'Type in the name of the folder (ex: Oct2016) where the original data for each MTA service is stored: ')

rails = ["LIRR", "metro_north", "nyc_subway"]

download_gtfs_data(folder)
for rail in rails:
    make_rail_routes_shapefiles(path=path_name, folder=folder, rail=rail)
    make_rail_stops_shapefiles(path=path_name, folder=folder, rail=rail)
    
make_bus_routes_shapefiles(path=path_name, folder=folder)
make_bus_stops_shapefiles(path=path_name, folder=folder)
make_subway_entrances_shapefiles(path=path_name, folder=folder)