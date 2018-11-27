'''
-------------------------------------------------------------------------------------------
Purpose: This script processes GTFS feeds to create shapefiles representing bus routes.
         The data has to be downloaded prior to running this script. If not done so, 
         run the get_mta_gtfs_data.py to download the data.
                                                                         
Created on : Oct, 2016
Last Update: Nov, 2018                                            
------------------------------------------------------------------------------------------
'''
import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point, LineString

path = os.getcwd()
folder_name = input(
    'Type in the name of the folder (ex: Oct2016) where the original data for each MTA service is stored: ')

local_service = 'bus_routes_nyc_{}'.format(folder_name)  # names for shapefiles
express_service = 'express_bus_routes_nyc_{}'.format(folder_name)

boroughs = [boro for boro in os.listdir(os.path.join(path, folder_name)) if
            boro.endswith('bus')]  # create list of files with bus feeds

bus_co_routes = pd.read_csv(os.path.join(path, folder_name, 'bus_company', 'routes.txt'))
bus_co_routes = pd.DataFrame(bus_co_routes, columns=['route_id', 'route_short_name', 'route_long_name', 'route_color'])
bus_co_routes.columns = ['route_id', 'route_short', 'route_long', 'color']

bus_co_shapes = pd.read_csv(os.path.join(path, folder_name, 'bus_company', 'shapes.txt'))
bus_co_shapes = pd.DataFrame(bus_co_shapes, columns=['shape_id', 'shape_pt_lat', 'shape_pt_lon'])  # select needed columns
bus_co_shapes.columns = ['shape_id', 'lat', 'lon']  # rename columns

bus_co_trips = pd.read_csv(os.path.join(path, folder_name, 'bus_company', 'trips.txt'))
bus_co_trips = pd.DataFrame(bus_co_trips, columns=['route_id', 'direction_id', 'shape_id'])
bus_co_trips.columns = ['route_id', 'dir_id', 'shape_id']
bus_co_trips = bus_co_trips.drop_duplicates()

bus_co_shapes = bus_co_shapes.merge(bus_co_trips, on='shape_id')  # table join
bus_co_shapes = bus_co_shapes.merge(bus_co_routes, on='route_id')  # table join

local = bus_co_shapes['route_id'].str.match(r'\w\d+|BX\d+')  # creates a boolean mask with True values for local services
local_routes = bus_co_shapes[local]  # applies mask to get local routes
express_routes = bus_co_shapes[~local]  # applies the inverse of mask to get express routes

local_geometry = [Point(xy) for xy in zip(local_routes.lon, local_routes.lat)]  # create points using Shapely's Point
express_geometry = [Point(xy) for xy in zip(express_routes.lon, express_routes.lat)]

loc_gdf = gpd.GeoDataFrame(local_routes,
                           geometry=local_geometry)  # create GeoDataFrame using df and created points as geometry
exp_gdf = gpd.GeoDataFrame(express_routes, geometry=express_geometry)

# ------create lines from points------- #
local_gdf = loc_gdf.groupby(['shape_id'])['geometry'].apply(lambda x: LineString(x.tolist())).reset_index()
express_gdf = exp_gdf.groupby(['shape_id'])['geometry'].apply(lambda x: LineString(x.tolist())).reset_index()

local_gdf = gpd.GeoDataFrame(local_gdf, geometry='geometry')
express_gdf = gpd.GeoDataFrame(express_gdf, geometry='geometry')

local_gdf = local_gdf.merge(bus_co_trips, on='shape_id', how='left')
express_gdf = express_gdf.merge(bus_co_trips, on='shape_id', how='left')

local_gdf = local_gdf.merge(bus_co_routes, on='route_id', how='left')  # table join
express_gdf = express_gdf.merge(bus_co_routes, on='route_id', how='left')  # table join

local_gdf['route_dir'] = local_gdf.route_id.astype(str).str.cat(local_gdf.dir_id.astype(str),
                                                                sep='_')  # creates new column as concatenation of route_id and direction_id
express_gdf['route_dir'] = express_gdf.route_id.astype(str).str.cat(express_gdf.dir_id.astype(str),
                                                                    sep='_')  # creates new column as concatenation of route_id and direction_id

local_gdf = local_gdf.dissolve(by='route_dir', as_index=False)  # dissolves on route_dir
express_gdf = express_gdf.dissolve(by='route_dir', as_index=False)  # dissolves on route_dir

express_gdf = gpd.GeoDataFrame(express_gdf,
                               columns=['route_id', 'dir_id', 'route_dir', 'geometry', 'route_short', 'route_long',
                                        'color'])

local_gdf = gpd.GeoDataFrame(local_gdf,
                               columns=['route_id', 'dir_id', 'route_dir', 'geometry', 'route_short', 'route_long',
                                        'color'])

local_gdf.crs = {'init': 'epsg:4269'}  # NAD83
express_gdf.crs = {'init': 'epsg:4269'}  # NAD83

local_gdf = local_gdf.to_crs(epsg=2263)  # reproject to LI_NY_StatePlane(ft)
express_gdf = express_gdf.to_crs(epsg=2263)  # reproject to LI_NY_StatePlane(ft)

print('Local and express bus services are extracted from Bus Company routes')


express_services=[]
express_services.append(express_gdf)
local_services=[]
local_services.append(local_gdf)
for borough in boroughs:
    print('working on ', borough)
    routes_raw = pd.read_csv(os.path.join(path, folder_name, '{}'.format(borough), 'routes.txt'))
    routes = pd.DataFrame(routes_raw, columns=['route_id',
                                               'route_short_name',
                                               'route_long_name', 
                                               'route_color'])
    
    routes.columns = ['route_id', 'route_short', 'route_long', 'color']
    
    shapes_raw = pd.read_csv(os.path.join(path, folder_name, '{}'.format(borough), 'shapes.txt'))
    shapes = pd.DataFrame(shapes_raw, columns=['shape_id', 'shape_pt_lat', 'shape_pt_lon'])  # select needed columns
    shapes.columns = ['shape_id', 'lat', 'lon']  # rename columns
    
    trips_raw = pd.read_csv(os.path.join(path, folder_name, '{}'.format(borough), 'trips.txt'))
    trips = pd.DataFrame(trips_raw, columns=['route_id', 'direction_id', 'shape_id'])
    trips.columns = ['route_id', 'dir_id', 'shape_id']
    trips = trips.drop_duplicates()
    
    geometry = [Point(xy) for xy in zip(shapes.lon, shapes.lat)]  # create points using Shapely's Point
    
    gdf = gpd.GeoDataFrame(shapes, geometry=geometry)  # create GeoDataFrame using df and created points as geometry
    gdf = gpd.GeoDataFrame(gdf.groupby(['shape_id'])['geometry'].apply(lambda x: LineString(x.tolist())).reset_index())
    gdf = gdf.merge(trips, on='shape_id')
    gdf = gdf.merge(routes, on='route_id')  # table join
    gdf['route_dir'] = gdf.route_id.astype(str).str.cat(gdf.dir_id.astype(str),
                                                        sep='_')  # creates new column as concatenation of route_id and direction_id
    gdf = gdf.dissolve(by='route_dir', as_index=False)  # dissolves on route_dir
    gdf.crs = {'init': 'epsg:4269'}  # NAD83
    gdf = gdf.to_crs(epsg=2263)  # reproject to LI_NY_StatePlane(ft)
    
    
    # regex to match any character that is not X and not SIM; X indicates express service in MTA Bus routes
    local_mask = gdf['route_id'].str.match(r'(?!^X\.*?)(?!SIM\.*?)')  
    local = gdf[local_mask]
    express = gdf[~local_mask]
    express_services.append(express)
    local_services.append(local)

# merges all express services into a single gdf    
express_nyc = gpd.GeoDataFrame(pd.concat(express_services,
                                         ignore_index=True))  

express_nyc = gpd.GeoDataFrame(express_nyc,
                               columns=['route_id', 
                                        'dir_id', 
                                        'route_dir', 
                                        'geometry', 
                                        'route_short', 
                                        'route_long',
                                        'color'])
express_nyc.crs = {'init': 'epsg:2263'}

# merges all local services into a single gdf
nyc_bus = gpd.GeoDataFrame(pd.concat(local_services,
                                     ignore_index=True))  

nyc_bus = gpd.GeoDataFrame(nyc_bus, columns=['route_id', 
                                        'dir_id', 
                                        'route_dir', 
                                        'geometry', 
                                        'route_short', 
                                        'route_long',
                                        'color'])
nyc_bus.crs = {'init': 'epsg:2263'}

# save gtfs to shapefiles
nyc_bus.to_file(os.path.join(path, folder_name, 'shapes', '{}.shp'.format(local_service)))  
express_nyc.to_file(os.path.join(path, folder_name, 'shapes', '{}.shp'.format(express_service)))

print('All done')    