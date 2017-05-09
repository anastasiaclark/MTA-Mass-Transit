'''
-------------------------------------------------------------------------------------------
Purpose: This script processes GTFS feeds to create shapefiles representing bus routes.
         The script assumes the naming conventions of the folders, containing the feeds
         in txt format to remain identical to those in the past.                                            
                                                                          
Created on : Oct, 2016                                            
------------------------------------------------------------------------------------------
'''
import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point, LineString

path=r'\\bctc-nas\LibShare\Shared\Divisions\Graduate\GEODATA\MASS_Transit'# this path is assumed to stay the same
folder_name=input('Type in the name of the folder (ex: Oct2016) where the original data for each MTA service is stored')

local_service='bus_routes_nyc_{}'.format(folder_name)# names for shapefiles
express_service='express_bus_routes_nyc_{}'.format(folder_name)

boroughs=[ boro for boro in os.listdir(os.path.join(path,folder_name)) if boro.endswith('bus')] # create list of files with bus feeds

###--------this part reads and processes bus company files---------###
routes_raw=pd.read_csv(os.path.join(path,folder_name,'bus_company','routes.txt'))
routes=pd.DataFrame(routes_raw,columns=['route_id','route_short_name','route_long_name','route_color'])
routes.columns=['route_id','route_short','route_long','color']

shapes_raw=pd.read_csv(os.path.join(path,folder_name,'bus_company','shapes.txt'))
shapes=pd.DataFrame(shapes_raw,columns=['shape_id','shape_pt_lat','shape_pt_lon'])# select needed columns
shapes.columns=['shape_id','lat','lon']#rename columns

trips_raw=pd.read_csv(os.path.join(path,folder_name,'bus_company','trips.txt'))
trips=pd.DataFrame(trips_raw,columns=['route_id','direction_id','shape_id'])
trips.columns=['route_id','dir_id','shape_id']
trips=trips.drop_duplicates()
shapes=shapes.merge(trips,on='shape_id') #table join
shapes=shapes.merge(routes,on='route_id')#table join

local=shapes['route_id'].str.match(r'\w\d+|BX\d+') # creates a boolean mask with True values for local services
local_routes=shapes[local] # applies the mask to get local routes
express_routes=shapes[~local] # applies the inverse of mask to get express routes

local_geometry = [Point(xy) for xy in zip(local_routes.lon, local_routes.lat)]# create points using Shapely's Point
express_geometry=[Point(xy) for xy in zip(express_routes.lon, express_routes.lat)]

loc_gdf=gpd.GeoDataFrame(local_routes,geometry=local_geometry)# create GeoDataFrame using df and created points as geometry
exp_gdf=gpd.GeoDataFrame(express_routes,geometry=express_geometry)

##------create lines from points-------##
local_gdf = loc_gdf.groupby(['shape_id'])['geometry'].apply(lambda x: LineString(x.tolist())).reset_index()
express_gdf = exp_gdf.groupby(['shape_id'])['geometry'].apply(lambda x: LineString(x.tolist())).reset_index()

local_gdf = gpd.GeoDataFrame(local_gdf, geometry='geometry')
express_gdf = gpd.GeoDataFrame(express_gdf, geometry='geometry')

local_gdf=local_gdf.merge(trips,on='shape_id')
express_gdf=express_gdf.merge(trips,on='shape_id')
local_gdf=local_gdf.merge(routes,on='route_id')#table join
express_gdf=express_gdf.merge(routes,on='route_id')#table join
local_gdf['route_dir']=local_gdf.route_id.astype(str).str.cat(local_gdf.dir_id.astype(str), sep='_')# creates new column as concatenation of route_id and direction_id
express_gdf['route_dir']=express_gdf.route_id.astype(str).str.cat(express_gdf.dir_id.astype(str), sep='_')# creates new column as concatenation of route_id and direction_id
local_gdf=local_gdf.dissolve(by='route_dir', as_index=False)# dissolves on route_dir
express_gdf=express_gdf.dissolve(by='route_dir', as_index=False)# dissolves on route_dir
express_gdf=gpd.GeoDataFrame(express_gdf,columns=['route_id','dir_id','route_dir','geometry','route_short','route_long','color'])
local_gdf.crs={'init' :'epsg:4269'} # NAD83
express_gdf.crs={'init' :'epsg:4269'} # NAD83
local_gdf=local_gdf.to_crs(epsg=2263)# reproject to LI_NY_StatePlane(ft)
express_gdf=express_gdf.to_crs(epsg=2263)# reproject to LI_NY_StatePlane(ft)

print ('Local and express bus services are extracted from Bus Company routes')

###---------this part reads and processes bus lines for each borough---------###
for borough in boroughs:
    print ('working on ',borough)
    routes_raw=pd.read_csv(os.path.join(path,folder_name,'{}'.format(borough),'routes.txt'))
    routes=pd.DataFrame(routes_raw,columns=['route_id','route_short_name','route_long_name','route_color'])
    routes.columns=['route_id','route_short','route_long','color']

    shapes_raw=pd.read_csv(os.path.join(path,folder_name,'{}'.format(borough),'shapes.txt'))
    shapes=pd.DataFrame(shapes_raw,columns=['shape_id','shape_pt_lat','shape_pt_lon'])# select needed columns
    shapes.columns=['shape_id','lat','lon']#rename columns

    trips_raw=pd.read_csv(os.path.join(path,folder_name,'{}'.format(borough),'trips.txt'))
    trips=pd.DataFrame(trips_raw,columns=['route_id','direction_id','shape_id'])
    trips.columns=['route_id','dir_id','shape_id']
    trips=trips.drop_duplicates()

    geometry = [Point(xy) for xy in zip(shapes.lon, shapes.lat)]# create points using Shapely's Point

    gdf=gpd.GeoDataFrame(shapes,geometry=geometry)# create GeoDataFrame using df and created points as geometry
    gdf = gpd.GeoDataFrame(gdf.groupby(['shape_id'])['geometry'].apply(lambda x: LineString(x.tolist())).reset_index())
    gdf=gdf.merge(trips,on='shape_id')
    gdf=gdf.merge(routes,on='route_id')#table join
    gdf['route_dir']=gdf.route_id.astype(str).str.cat(gdf.dir_id.astype(str), sep='_')# creates new column as concatenation of route_id and direction_id

    if borough=='bk_bus':
        bk_gdf=gdf.dissolve(by='route_dir', as_index=False)# dissolves on route_dir
        bk_gdf.crs={'init' :'epsg:4269'} # NAD83
        bk_gdf=bk_gdf.to_crs(epsg=2263)# reproject to LI_NY_StatePlane(ft)        
    elif borough=='bx_bus':
        bx_gdf=gdf.dissolve(by='route_dir', as_index=False)# dissolves on route_dir
        bx_gdf.crs={'init' :'epsg:4269'} # NAD83
        bx_gdf=bx_gdf.to_crs(epsg=2263)# reproject to LI_NY_StatePlane(ft)
    elif borough=='mn_bus':
        mn_gdf=gdf.dissolve(by='route_dir', as_index=False)# dissolves on route_dir
        mn_gdf.crs={'init' :'epsg:4269'} # NAD83
        mn_gdf=mn_gdf.to_crs(epsg=2263)# reproject to LI_NY_StatePlane(ft)
    elif borough=='qn_bus':
        qn_gdf=gdf.dissolve(by='route_dir', as_index=False)# dissolves on route_dir
        qn_gdf.crs={'init' :'epsg:4269'} # NAD83
        qn_gdf=qn_gdf.to_crs(epsg=2263)# reproject to LI_NY_StatePlane(ft)
    elif borough=='si_bus':
        si_gdf=gdf.dissolve(by='route_dir', as_index=False)# dissolves on route_dir
        si_gdf.crs={'init' :'epsg:4269'} # NAD83
        si_gdf=si_gdf.to_crs(epsg=2263)# reproject to LI_NY_StatePlane(ft)

print ('Separating local and express services in MTA Bus stops')
       
local_mask=si_gdf['route_id'].str.match(r'[^X\.*?]') ## regex to match any character that is not X; X indicates express service in MTA Bus routes
local_si=si_gdf[local_mask]
express_si=si_gdf[~local_mask]

local_mask=qn_gdf['route_id'].str.match(r'[^X\.*?]')
local_gn=qn_gdf[local_mask]
express_qn=qn_gdf[~local_mask]

local_mask=mn_gdf['route_id'].str.match(r'[^X\.*?]')
local_mn=mn_gdf[local_mask] 
express_mn=mn_gdf[~local_mask]

local_mask=bk_gdf['route_id'].str.match(r'[^X\.*?]')
local_bk=bk_gdf[local_mask]
express_bk=bk_gdf[~local_mask]

local_mask=bx_gdf['route_id'].str.match(r'[^X\.*?]')
local_bx=bx_gdf[local_mask]
express_bx=bx_gdf[~local_mask]

express_nyc=gpd.GeoDataFrame(pd.concat([express_si,express_qn,express_mn,express_bk,express_bx,express_gdf],ignore_index=True))# merges all express services into a single gdf  
express_nyc=gpd.GeoDataFrame(express_nyc, columns=['route_id','dir_id','route_dir','geometry','route_short','route_long','color'])
express_nyc.crs={'init' :'epsg:2263'}

nyc_bus=gpd.GeoDataFrame(pd.concat([local_bk,local_bx,local_mn,local_gn,local_si,local_gdf], ignore_index=True)) # merges all local services into a single gdf  
nyc_bus=gpd.GeoDataFrame(nyc_bus,columns=['route_id','dir_id','route_dir','geometry','route_short','route_long','color'])
nyc_bus.crs={'init' :'epsg:2263'}

nyc_bus.to_file(os.path.join(path,folder_name,'shapes','{}.shp'.format(local_service)))# save gdfs to shapefiles
express_nyc.to_file(os.path.join(path,folder_name,'shapes','{}.shp'.format(express_service)))

print ('All done')       
   
    

