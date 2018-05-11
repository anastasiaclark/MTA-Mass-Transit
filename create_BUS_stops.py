'''
------------------------------------------------------------------------------------------
Purpose: This script processes GTFS feeds to create shapefiles representing bus stops.
         The script assumes the naming conventions of the folders, containing the feeds
         in txt format to remain identical to those in the past.                                             
                                                                          
Created on : Oct, 2016                                            
-----------------------------------------------------------------------------------------
'''
import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point

path_name = '/Users/anastasiaclark/MyStaff/Git_Work/MTA-Mass-Transit'
folder_name = input(
    'Type in the name of the folder (ex: Oct2016) where the original data for each MTA service is stored: ')
local_service = 'bus_stops_nyc_{}.shp'.format(folder_name)
express_service = 'express_bus_stops_nyc_{}.shp'.format(folder_name)

boroughs = [boro for boro in os.listdir(os.path.join(path_name, folder_name)) if boro.endswith('bus')]
counties = gpd.read_file(os.path.join(path_name, 'counties_bndry.geojson'), driver='GeoJSON')
counties = counties.to_crs(epsg=2263)
counties.crs = {'init': 'epsg:2263'}

# --------------this part reads and processes bus company files---------------------#
stops_raw = pd.read_csv(os.path.join(path_name, folder_name, 'bus_company', 'stops.txt'))
stops = pd.DataFrame(stops_raw, columns=['stop_id', 'stop_name', 'stop_lat', 'stop_lon'])
print(len(stops))
stop_times = pd.read_csv(os.path.join(path_name, folder_name, 'bus_company', 'stop_times.txt'))
trips = pd.read_csv(os.path.join(path_name, folder_name, 'bus_company', 'trips.txt'))

stops = pd.merge(stops, stop_times, on='stop_id', how='outer')  # table join to get trip_id
stops = stops.merge(trips, on='trip_id',
                    how='outer')  # table join to get route_id; Note: multiple routes stop at the same stop=> outer join
stops = pd.DataFrame(stops, columns=['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'route_id'])
unique_routes_at_stops = stops.drop_duplicates()  # keep unique combination of stop and the route at the stop
local = unique_routes_at_stops['route_id'].str.match(
    r'\w\d+|BX\d+')  # creates a booleaen mask for local routes in Bus Co
local_stops = unique_routes_at_stops[local]  # filters out only local stops
express_stops = unique_routes_at_stops[~local]  # filters out only express stops
express_stops = express_stops.drop_duplicates(
    ['stop_id', 'stop_lat', 'stop_lon'])  # we only one point for each local route's stop
local_stops = local_stops.drop_duplicates(
    ['stop_id', 'stop_lat', 'stop_lon'])  # only one point for each express route's stop

local_stops = pd.DataFrame(local_stops, columns=['stop_id', u'stop_name', u'stop_lat',
                                                 u'stop_lon'])  # create df with selected columns
local_stops.reset_index()
express_stops = pd.DataFrame(express_stops, columns=['stop_id', u'stop_name', u'stop_lat', u'stop_lon'])
express_stops.reset_index()

geometry_local = [Point(xy) for xy in zip(local_stops.stop_lon, local_stops.stop_lat)]
geometry_express = [Point(xy) for xy in zip(express_stops.stop_lon, express_stops.stop_lat)]
gdf_local = gpd.GeoDataFrame(local_stops, geometry=geometry_local)
gdf_express = gpd.GeoDataFrame(express_stops, geometry=geometry_express)
gdf_local.crs = {'init': 'epsg:4269'}  # NAD83
gdf_local = gdf_local.to_crs(epsg=2263)  # reproject to LI_NY_StatePlane(ft)
gdf_express.crs = {'init': 'epsg:4269'}  # NAD83
gdf_express = gdf_express.to_crs(epsg=2263)  # reproject to LI_NY_StatePlane(ft)

print('Local and express bus services are extracted from Bus Company stops')

# ---------this part reads and processes bus stops for each borough---------###
all_local_buses = []
all_local_buses.append(gdf_local)
all_express_buses = []
all_express_buses.append(gdf_express)

for borough in boroughs:
    stops_raw = pd.read_csv(os.path.join(path_name, folder_name, '{}'.format(borough), 'stops.txt'))
    stops = pd.DataFrame(stops_raw, columns=['stop_id', 'stop_name', 'stop_lat', 'stop_lon'])
    stop_times = pd.read_csv(os.path.join(path_name, folder_name, '{}'.format(borough), 'stop_times.txt'))
    trips = pd.read_csv(os.path.join(path_name, folder_name, '{}'.format(borough), 'trips.txt'))
    stops = pd.merge(stops, stop_times, on='stop_id', how='outer')  # table join to get trip_id
    stops = stops.merge(trips, on='trip_id', how='outer')  # table join to get route_id
    stops = pd.DataFrame(stops, columns=['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'route_id'])
    unique_routes_at_stops = stops.drop_duplicates()

    local = unique_routes_at_stops['route_id'].str.match(
        r'[^X\.*?]')  # creates a booleaen mask local routes in MTA's Bus Routes
    local_stops = unique_routes_at_stops[local]  # filters out only local stops
    express_stops = unique_routes_at_stops[~local]  # filters out only express stops
    express_stops = express_stops.drop_duplicates(['stop_id', 'stop_lat', 'stop_lon'])
    local_stops = local_stops.drop_duplicates(['stop_id', 'stop_lat', 'stop_lon'])

    local_stops = pd.DataFrame(local_stops, columns=['stop_id', u'stop_name', u'stop_lat',
                                                     u'stop_lon'])  # create df with selected columns
    local_stops.reset_index()
    express_stops = pd.DataFrame(express_stops, columns=['stop_id', u'stop_name', u'stop_lat', u'stop_lon'])
    express_stops.reset_index()

    geometry_local = [Point(xy) for xy in zip(local_stops.stop_lon, local_stops.stop_lat)]
    geometry_express = [Point(xy) for xy in zip(express_stops.stop_lon, express_stops.stop_lat)]

    gdf_local = gpd.GeoDataFrame(local_stops, geometry=geometry_local)
    gdf_express = gpd.GeoDataFrame(express_stops, geometry=geometry_express)
    gdf_local.crs = {'init': 'epsg:4269'}  # NAD83
    gdf_local = gdf_local.to_crs(epsg=2263)  # reproject to LI_NY_StatePlane(ft)
    gdf_express.crs = {'init': 'epsg:4269'}  # NAD83
    gdf_express = gdf_express.to_crs(epsg=2263)  # reproject to LI_NY_StatePlane(ft)
    all_local_buses.append(gdf_local)
    all_express_buses.append(gdf_express)
    print('done with ', borough)

nyc_bus = gpd.GeoDataFrame(
    pd.concat(all_local_buses, ignore_index=True))  # merges all local services into a single gdf
nyc_bus = gpd.GeoDataFrame(nyc_bus, columns=['stop_id', 'geometry', 'stop_name', 'stop_lat', 'stop_lon'])
nyc_bus.crs = {'init': 'epsg:2263'}

express_nyc = gpd.GeoDataFrame(
    pd.concat(all_express_buses, ignore_index=True))  # merges all express services into a single gdf
express_nyc = gpd.GeoDataFrame(express_nyc, columns=['stop_id', 'geometry', 'stop_name', 'stop_lat', 'stop_lon'])
express_nyc.crs = {'init': 'epsg:2263'}

print("Doing spatial join")
nyc_bus = gpd.sjoin(nyc_bus, counties, how="inner", op='intersects')
nyc_bus = nyc_bus.drop('index_right', 1)

express_nyc = gpd.sjoin(express_nyc, counties, how="inner", op='intersects')
express_nyc = express_nyc.drop('index_right', 1)

print("Writing to shapefile")
nyc_bus.to_file(
    os.path.join(path_name, folder_name, 'shapes', '{}'.format(local_service)))  # write local stops to shapefile
express_nyc.to_file(
    os.path.join(path_name, folder_name, 'shapes', '{}'.format(express_service)))  # write expres stops to shapefile

print('All done')
