'''
--------------------------------------------------------------------------------------
Purpose: This script creates shapefiles from text containing information on
         NYC subway entrances. 
         
        The data is accessed from: http://web.mta.info/developers/data/nyct/subway/StationEntrances.csv
                          
Created on : Oct, 2016                                            
-------------------------------------------------------------------------------------
'''
import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point

path_name = os.getcwd()
folder_name = input(
    'Type in the name of the folder (ex: Oct2016) where the original data for each MTA service is stored: ')

shape_name = 'subway_entrances_' + folder_name + '.shp'

# read the entrances data directly from MTA's website
entrances = pd.read_csv('http://web.mta.info/developers/data/nyct/subway/StationEntrances.csv')

# write out the entrances data for archivial purposes
entrances.to_csv(os.path.join(path_name, folder_name, 'StationEntrances.csv'))

# get counties to use in spatial join
counties = gpd.read_file(os.path.join(path_name, 'counties_bndry.geojson'), driver='GeoJSON')
counties = counties.to_crs(epsg=2263)  # reproject counties to NY State Plane

# give shorter names to columns
entrances.columns = ['division', 'line', 'stn_name', 'stn_Lat',  # give the columns short names
                     'stn_Lon', 'route_1', 'route_2', 'route_3', 'route_4',
                     'route_5', 'route_6', 'route_7', 'route_8', 'route_9', 'route_10',
                     'route_11', 'entr_type', 'entry', 'exit_only', 'vending',
                     'staffing', 'staff_hour', 'ada', 'ada_notes', 'free_cross',
                     'n_s_Street', 'e_w_Street', 'corner', 'lat',
                     'lon']

# one of the longtitudes is missing negative sign
# multiply longtitude by -1 where it is positive (in US it will always be negative)
entrances.update(entrances.loc[entrances['lon'] > 0, 'lon'].mul(-1))  

# create a geometry object from lat, lon coordinates
geometry = [Point(xy) for xy in
            zip(entrances.lon, entrances.lat)]  

gdf = gpd.GeoDataFrame(entrances, geometry=geometry)  # create dGeoDataframe
gdf.crs = {'init': 'epsg:4269'}  # initiatre CRS: NAD83

gdf = gdf.to_crs(epsg=2263)  # reproject to NY State Plane

gdf = gpd.sjoin(gdf, counties, how="inner", op='intersects')  # spatially join entraces to counties layer
gdf = gdf.drop('index_right', 1)  ## drop unnecessay column that resulted from join

gdf['ada'] = gdf['ada'].astype(str)  ## change the data type of the ADA and free_cross columns
gdf['free_cross'] = gdf['free_cross'].astype(
    str)  # boolean fields can't be written into shapefile

gdf.to_file(os.path.join(path_name, folder_name, 'shapes', shape_name))  # write geodataframe into a shapefile

print('All done')
