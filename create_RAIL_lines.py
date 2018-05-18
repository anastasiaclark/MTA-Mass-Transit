'''
--------------------------------------------------------------------------------------
Purpose: This script creates shapefiles representing routes fot the MTA    
         rail services: nyc subway, Metro-North and LIRR. 

         The data has to be downloaded prior to running this script. 
         If not done so, run the get_mta_gtfs_data.py to download the data.                                            
                                                                          
Created on : Oct, 2016                                            
-------------------------------------------------------------------------------------
'''
import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point, LineString

path_name = '/Users/anastasiaclark/MyStaff/Git_Work/MTA-Mass-Transit'  # this path is assumed to stay the same
rails = ['LIRR', 'metro_north', 'nyc_subway']

## the month and the year will be appended to the names of the resulted shapefiles
## for Python 3 change raw_input() to input()
folder_name = input(
    'Type in the name of the folder (ex: Oct2016) where the original data for each MTA service is stored: ')


## In the feeds, MTA subway trips.txt is missing route_id for train 1; this
## results in the loss of the train 1 after the route_id field is obtained
## via join with trips table. This function is a workaround to get route_id
## without the table join.
def get_route_id(shape_id):  # function to get route id out of shape id (Ex: from N..20R gets N)
    route_id = shape_id.split('.')[0]
    return route_id


## these are segments that represent unusual service (rush hour etc;)
## and don't appear on MTA map.
segments_to_remove = ['E..N55R', 'E..S56R', 'E..S04R', 'E..N05R', 'N..N20R', 'N..S20R', '2..N03R',
                      '2..S03R', '4..S01R', '4..S02R', '4..S03R', '4..S13R', '4..N01R', '4..N02R',
                      '4..N03R', '4..N13R', '4..S40R', '5..S18R', '5..N18R', '5..N13R', '5..N06R',
                      '5..N07R', '5..N20R', '5..N22R', '5..S06R', '5..S07R', '5..S15R', '5..S21R']

# this is to add a 'group' column to use for MTA's subway map-like coloring of the routes
d = {'FS': 'S', 'GS': 'S', '1': '123', '3': '123', '2': '123', '5': '456', '4': '456', '7': '7',
     '6': '456', 'A': 'ACE', 'C': 'ACE', 'E': 'ACE', 'B': 'BDFM', 'D': 'BDFM', 'G': 'G',
     'F': 'BDFM', 'H': 'S', 'J': 'JZ', 'M': 'BDFM', 'L': 'L', 'N': 'NQR', 'Q': 'NQR', 'R': 'NQR', 'SI': 'SIR'}

# create a list of keys,values and turn it into df
groups = pd.DataFrame([[key, value] for key, value in d.items()], columns=['route_id', 'group'])

for rail in rails:
    shape_name = 'routes_{}_{}.shp'.format(rail, folder_name)  # naming convention
    routes_raw = pd.read_csv(os.path.join(path_name, folder_name, '{}'.format(rail), 'routes.txt'))
    routes = pd.DataFrame(routes_raw, columns=['route_id', 'route_short_name', 'route_long_name', 'route_color'])
    routes.columns = ['route_id', 'route_short', 'route_long', 'color']  # rename columns

    shapes_raw = pd.read_csv(os.path.join(path_name, folder_name, '{}'.format(rail), 'shapes.txt'))
    shapes = pd.DataFrame(shapes_raw, columns=['shape_id', 'shape_pt_lat', 'shape_pt_lon'])  # select needed columns
    shapes.columns = ['shape_id', 'lat', 'lon']  # rename columns
    if rail == 'nyc_subway':
        shapes = shapes[~shapes.shape_id.isin(
            segments_to_remove)]  # create new df that doesn't contain unusual service for MTA

    trips_raw = pd.read_csv(os.path.join(path_name, folder_name, '{}'.format(rail), 'trips.txt'))
    trips = pd.DataFrame(trips_raw, columns=['route_id', 'service_id', 'shape_id'])
    trips = trips.drop_duplicates()
    if rail == 'metro_north':
        trips = trips[
            trips.service_id == 1]  # filter by service id; metro_north feeds have some extra non-metro-north points

    geometry = [Point(xy) for xy in zip(shapes.lon, shapes.lat)]  # create geometry points using Shapely's Point
    gdf = gpd.GeoDataFrame(shapes, geometry=geometry)  # create GeoDataFrame using df and created points as geometry
    gdf = gdf.groupby(['shape_id'])['geometry'].apply(
        lambda x: LineString(x.tolist())).reset_index()  # create lines from points grouped by same id
    gdf_to_dis = gpd.GeoDataFrame(gdf, geometry='geometry')

    if rail == 'nyc_subway':
        gdf_to_dis['route_id'] = gdf_to_dis['shape_id'].apply(lambda x: get_route_id(x))
        gdf = gdf_to_dis.dissolve(by='route_id',
                                  as_index=False)  # dissolves on common id; note:if index isn't set to False, route_id will become gdf's index
    else:
        gdf = gdf_to_dis.merge(trips, on='shape_id')  # table join
        gdf = gdf.dissolve(by='route_id',
                           as_index=False)  # dissolves on common id; note:if index isn't set to False, route_id will become gdf's index

    gdf = gdf.merge(routes, on='route_id')  # table join for routes
    if rail == 'nyc_subway':
        gdf = gdf.merge(groups, on='route_id')  # table join for groups (subway only)
        # add missing colors for S and SIR lines of the subway
        gdf.loc[gdf['route_id'] == 'FS', 'color'] = '808183'
        gdf.loc[gdf['route_id'] == 'H', 'color'] = '808183'
        gdf.loc[gdf['route_id'] == 'SI', 'color'] = '053159'
        # and make route_short equal to JZ rather than J
        gdf.loc[gdf['route_id'] == 'J', 'route_short'] = 'JZ'

    else:
        print(rail, 'removing "route short"')
        gdf = gdf.drop('route_short', 1)  ## metro-north and LIRR don't have any records in route_short field

    if rail == 'nyc_subway':
        gdf = gdf.drop('shape_id', 1)  ## shape_id column is no longer neeed, remove it before saving to shapefile
    else:
        gdf = gdf.drop(['shape_id', 'service_id'],
                       1)  # shape_id and service id column is no longer neeed, remove it before saving to shapefile
    gdf.crs = {'init': 'epsg:4269'}  # NAD83
    gdf = gdf.to_crs(epsg=2263)  # reproject to State Plane
    gdf.to_file(os.path.join(path_name, folder_name, 'shapes', '{}'.format(shape_name)))  # save gdf to shapefile
    print('Done with ', rail)

print('All done')
