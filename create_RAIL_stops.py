'''
--------------------------------------------------------------------------------------
Purpose: This script creates shapefiles representing stops the MTA    
         rail services: nyc subway, Metro-North and LIRR. 
         
         The data has to be downloaded prior to running this script. 
         If not done so, run the get_mta_gtfs_data.py to download the data.                                            
                                                                          
Created on : Oct, 2016                                            
-------------------------------------------------------------------------------------
'''
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import os

rails = ['LIRR', 'metro_north', 'nyc_subway']  # these are the services, for which the shapes are created in this script
path_name = os.getcwd()
folder_name = input(
    'Type in the name of the folder (ex: Oct2016) where the original data for each MTA service is stored: ')

counties = gpd.read_file(os.path.join(path_name, 'counties_bndry.geojson'), driver='GeoJSON')
counties = counties.to_crs(epsg=2263)

# read-in file that idicates which train stops at which stations
trains_at_stops = pd.read_csv('http://web.mta.info/developers/data/nyct/subway/Stations.csv',
                              usecols=['GTFS Stop ID', 'Daytime Routes', 'Structure'])

trains_at_stops.columns = ['stop_id', 'trains', 'structure']  # rename columns

for rail in rails:
    print('working on ', rail)
    shape_name = 'stops_{0}_{1}.shp'.format(rail, folder_name)
    stops_raw = pd.read_csv(os.path.join(path_name, folder_name, '{}'.format(rail), 'stops.txt'))
    stops = pd.DataFrame(stops_raw, columns=['stop_id', 'stop_name', 'stop_lat', 'stop_lon'])
    stops.columns = ['stop_id', 'stop_name', 'stop_lat', 'stop_lon']  # rename columns
    if rail == 'nyc_subway':
        unique_stops = []
        for stop in stops.stop_id:
            if stop.endswith('S'):
                pass
            elif stop.endswith('N'):
                pass
            else:
                unique_stops.append(stop)

        stops = stops[stops.stop_id.isin(unique_stops)]  # remove stops that end in 'S' or 'N' from dataframe

        # correct coordinates of the station with id='H01' and update name of the 138 station
        stops.loc[stops['stop_id'] == 'H01', 'stop_lat'] = 40.672086
        stops.loc[stops['stop_id'] == 'H01', 'stop_lon'] = -73.835914
        stops.loc[stops['stop_id'] == '138', 'stop_name'] = stops.stop_name + ' (Closed)'
        
        df = stops.loc[stops.duplicated(subset=['stop_lat', 'stop_lon'])][['stop_lat', 'stop_lon', 'stop_id']] # get the duplciate stations only; columns specified
        
        df.rename(columns={'stop_id': 'stop_id2'}, inplace=True)  # rename the last column; it will be used as stop_id2 to reference the removed duplicates
        
        stops = stops.merge(trains_at_stops, on='stop_id', how='outer')      
        stops = stops.drop_duplicates(['stop_lat', 'stop_lon'],
                                      keep='first')  # removes stations where both lat and lon are the same
        
        stops = pd.merge(stops, df, on=['stop_lat', 'stop_lon'], how='outer', suffixes=('old', 'new'))


        # check if there are new stops that didn't exist before
        new_subway_stops = stops[stops.trains.isnull()]
        if len(new_subway_stops) > 0:
            print('----------------------------------------------------------', '\n',
                  """Warning: either new subway stops have been created since
                  the last release or the information for some stops is missing 
                  in http://web.mta.info/developers/data/nyct/subway/Stations.csv file.
                  Consider updating the missing train information manually in the shapefiles""", '\n',
                  '-----------------------------------------------------------')

    elif rail == 'metro_north':
        metro_bus_shape = rail + '_bx_bus_' + folder_name + '.shp'
        metro_north_rail_stops = stops[(stops['stop_id'] < 500) | (stops['stop_id'] == 622)]
        metro_north_rail_stops.reset_index()

        rail_stops_with_bus = stops[(stops['stop_id'] == 14) | (
        stops['stop_id'] == 16)]  # these are rail stops, but the shuttle bus stops there as well

        metro_north_bus_stops = stops[(stops['stop_id'] > 500) & (stops['stop_id'] != 622) & (stops['stop_id'] < 1000)]
        metro_north_bus_stops.reset_index()
        metro_north_bus_stops = metro_north_bus_stops.append(rail_stops_with_bus)

        geometry_rail = [Point(xy) for xy in zip(metro_north_rail_stops.stop_lon, metro_north_rail_stops.stop_lat)]
        geometry_bus = [Point(xy) for xy in zip(metro_north_bus_stops.stop_lon, metro_north_bus_stops.stop_lat)]

        gdf_rail = gpd.GeoDataFrame(metro_north_rail_stops, geometry=geometry_rail)
        gdf_rail.crs = {'init': 'epsg:4269'}  # NAD83
        gdf_rail = gdf_rail.to_crs(epsg=2263)
        gdf_rail = gpd.sjoin(gdf_rail, counties, how="inner", op='intersects')
        gdf_rail = gdf_rail.drop('index_right', 1)
        gdf_rail.to_file(os.path.join(path_name, folder_name, 'shapes',
                                      '{}'.format(shape_name)))  # save metro-north rail stops to shapefile

        gdf_bus = gpd.GeoDataFrame(metro_north_bus_stops, geometry=geometry_bus)
        gdf_bus.crs = {'init': 'epsg:4269'}  # NAD83
        gdf_bus = gdf_bus.to_crs(epsg=2263)
        gdf_bus = gpd.sjoin(gdf_bus, counties, how="inner", op='intersects')
        gdf_bus = gdf_bus.drop('index_right', 1)
        gdf_bus.to_file(os.path.join(path_name, folder_name, 'shapes',
                                     '{}'.format(metro_bus_shape)))  # save metro-north bus stops to shapefile

    if rail != 'metro_north':
        geometry = [Point(xy) for xy in zip(stops.stop_lon, stops.stop_lat)]
        gdf = gpd.GeoDataFrame(stops, geometry=geometry)
        gdf.crs = {'init': 'epsg:4269'}  # NAD83
        gdf = gdf.to_crs(epsg=2263)
        gdf = gpd.sjoin(gdf, counties, how="inner", op='intersects')
        gdf = gdf.drop('index_right', 1)
        gdf.to_file(os.path.join(path_name, folder_name, 'shapes', '{}'.format(shape_name)))  # save gdf to shapefile
        print('done', rail)
    else:
        print(rail, 'created')

print('All done')
