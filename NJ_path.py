'''
--------------------------------------------------------------------------------------
Purpose: This script creates shapefiles representing routes for the NJ Path   
         rail service. The script assumes the naming conventions of the folders,
         containing original shapefiles to be the same as used in the past.                                           
                                                                          
Created on : Oct, 2016                                            
-------------------------------------------------------------------------------------
'''
import geopandas as gpd
import pandas as pd
import os

routes_name='NJ_PATH_routes.shp' # naming conventions for the shapes that will be created
stations_name='NJ_PATH_stations.shp'

station_gdf=gpd.GeoDataFrame.from_file(r'\\bctc-nas\LibShare\Shared\Divisions\Graduate\GEODATA\MASS_Transit\NJ_Rail_shp\Tran_railroad_station.shp')
rail_gdf=gpd.GeoDataFrame.from_file(r'\\bctc-nas\LibShare\Shared\Divisions\Graduate\GEODATA\MASS_Transit\NJ_Rail_shp\Tran_railroad_passenger.shp')
counties=gpd.GeoDataFrame.from_file(r'\\bctc-nas\LibShare\Shared\Divisions\Graduate\GEODATA\MASS_Transit\NJ_PATH\counties\county_boundaries.shp')
counties=counties.to_crs(epsg=2263)# reproject counties to NY State Plane

route_short_dic={'NEWARK - WORLD TRADE CENTER':"NWK-WTC",'HOBOKEN - WORLD TRADE CENTER':"HOB-WTC", # create short names for the routes
                 'HOBOKEN - 33 STREET':"HOB-33",'JOURNAL SQUARE - 33 STREET':"JSQ-33",
                 'JOURNAL SQUARE - 33 STREET VIA HOBOKEN':"JSQ-33 via HOB"}

color_dic={'NWK-WTC':'EF3941','HOB-WTC':'009E58','JSQ-33':'FDB827','JSQ-33 via HOB':'FDB827','HOB-33':'0082C6'} # colors to be used for mapping

obj1=pd.Series(route_short_dic) # create a series object
obj2=pd.Series(color_dic)
id_df=pd.DataFrame({'route_long':obj1.index,'route_short':obj1.values},dtype=str) # create dataframes
color_df=pd.DataFrame({'route_short':obj2.index,'color':obj2.values},dtype=str)
df=pd.merge(color_df,id_df, on='route_short') # join two dataframes together

path_rail=rail_gdf[rail_gdf['RAIL_LINE']=='PATH'] # select a subset of rail lines that belong to PATH service
path_rail=path_rail.to_crs(epsg=2263)# reproject to NY State Plan
path_rail=path_rail.drop('DATE_STAMP',1) # remove DATE STAMP column
path_rail.columns=['rail_line','route_long','geometry'] # rename columns with lowercase anmes
path_rail['service']='operates: daytime weekdays' # add new column indicating service and populate it with initial values
path_rail.loc[path_rail['route_long']=='JOURNAL SQUARE - 33 STREET VIA HOBOKEN','service']='operates: nighttime weekdays and weekends'# update nightime service
path_rail.loc[path_rail['route_long']=='NEWARK - WORLD TRADE CENTER','service']='operates: daytime weekdays, nighttime weekdays, weekends'# update service
path_rail=path_rail.merge(df, on='route_long')# merge extracted paths with table containing colors and short names for routes
path_rail=gpd.GeoDataFrame(path_rail,columns=['route_short','route_long','geometry','rail_line','service','color'],geometry='geometry') # re-order columns
path_rail.crs={'init': 'epsg:2263'} ## initiate CRS since the creation of gdf didn't carry it over

path_station=station_gdf[station_gdf['RAIL_LINE']=='PATH']# select a subset of rail stations that belong to PATH service
path_station=path_station.to_crs(epsg=2263)# reproject to NY State Plane
path_station=path_station.drop('AMTRAK',1)# drop column that indicates that the service is not an AMTRAK service
path_station.columns=['station_id','county','lat','lon','mun_label','rail_line','station','geometry']# rename columns
path_station=gpd.sjoin(path_station, counties, how="inner", op='intersects')# spatially join stations with counties layer
path_station=path_station.drop(['index_right','county'],1) # drop the unnecessary column that the spatial join has created

path_rail.to_file(r'\\bctc-nas\LibShare\Shared\Divisions\Graduate\GEODATA\MASS_Transit\NJ_PATH\{}'.format(routes_name))# save PATH services as new shapefile
path_station.to_file(r'\\bctc-nas\LibShare\Shared\Divisions\Graduate\GEODATA\MASS_Transit\NJ_PATH\{}'.format(stations_name))

print('all done')
