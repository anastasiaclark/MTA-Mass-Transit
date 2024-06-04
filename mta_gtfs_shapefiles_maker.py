import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point, LineString
# from fiona.crs import from_epsg
from pyproj import CRS
import logging
import datetime

# configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler("error_log.log")
handler.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# these are the segments that represent unusual service (rush hour etc;)
# and don't appear on MTA map.
subway_segments_to_remove = [
    "E..N55R",
    "E..S56R",
    "E..S04R",
    "E..N05R",
    "N..N20R",
    "N..S20R",
    "2..N03R",
    "2..S03R",
    "4..S01R",
    "4..S02R",
    "4..S03R",
    "4..S13R",
    "4..N01R",
    "4..N02R",
    "4..N03R",
    "4..N13R",
    "4..S40R",
    "5..S18R",
    "5..N18R",
    "5..N13R",
    "5..N06R",
    "5..N07R",
    "5..N20R",
    "5..N22R",
    "5..S06R",
    "5..S07R",
    "5..S15R",
    "5..S21R",
]

# this is to add a 'group' column to use for MTA's subway map-like coloring of the routes
d = {
    "FS": "S",
    "GS": "S",
    "1": "123",
    "3": "123",
    "2": "123",
    "5": "456",
    "4": "456",
    "7": "7",
    "6": "456",
    "A": "ACE",
    "C": "ACE",
    "E": "ACE",
    "B": "BDFM",
    "D": "BDFM",
    "G": "G",
    "F": "BDFM",
    "H": "S",
    "J": "JZ",
    "M": "BDFM",
    "L": "L",
    "N": "NQRW",
    "Q": "NQRW",
    "R": "NQRW",
    "SI": "SIR",
    "W": "NQRW",
}

# list of old and non-passanger stations
# Stations S10 and S12 on the SIR no longer exist, they were demolished. 
# Station 140 South Ferry Loop is a non-passenger station, 
# it’s a couple of old platforms where the 1 train turns around to go back up. 
# H19 Broad Channel is an extra test track where trains are kept for maintenance 
# (the actual station is H04 Broad Channel)
non_existent_stops=['140', 'H19', 'S10', 'S12']


# create a dataframe from group dictionary
route_groups = pd.DataFrame(
    [[key, value] for key, value in d.items()], columns=["route_id", "group"]
)

# read-in file that indicates which trains stop at which stations
trains_at_stops = pd.read_csv(
    "http://web.mta.info/developers/data/nyct/subway/Stations.csv",
    usecols=["GTFS Stop ID", "Daytime Routes", "Structure"],
)

trains_at_stops.rename(
    columns={
        "GTFS Stop ID": "stop_id",
        "Daytime Routes": "trains",
        "Structure": "structure",
    },
    inplace=True,
)

# monthYear is appended to all shapefiles names
today = datetime.datetime.today()
month = today.strftime("%B")
year = today.year
monthYear = f"{month}{year}"


def pre_process_stops(path, folder, bus_service):
    """Read, join and process stop tables.
    Given three tables produce a single table
    with routes association for each stop.
    
    return example:
    
    stop_id|stop name                     |lat       |lon       |route_id
    -------|------------------------------|--------- |----------|--------
     100048|GRAND CONCOURSE/E 196 ST      |40.867955 |-73.892642|BXM4
     100058|SEDGWICK AV/VAN CORTLANDT AV W|40.882828 |-73.893138|BXM3
     100060|SEDGWICK AV/GILES PL          |40.880924 |-73.896698|BXM3
     100071|HENRY HUDSON PKY E/W 239 ST   |40.889520 |-73.908064|BXM18
     100071|HENRY HUDSON PKY E/W 239 ST   |40.889520 |-73.908064|BXM1
     100071|HENRY HUDSON PKY E/W 239 ST   |40.889520 |-73.908064|BXM2

    """
    stops = pd.read_csv(
        os.path.join(path, folder, bus_service, "stops.txt"),
        usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"],
    )
    stop_times = pd.read_csv(os.path.join(path, folder, bus_service, "stop_times.txt"))
    trips = pd.read_csv(os.path.join(path, folder, bus_service, "trips.txt"))
    df = stop_times.merge(trips, on="trip_id")
    routes_for_stops = pd.DataFrame(
        df.groupby("stop_id")["route_id"].agg(lambda x: list(set(x)))
    ).reset_index()
    stop_id_route = (
        routes_for_stops.route_id.apply(pd.Series)
        .merge(routes_for_stops, left_index=True, right_index=True)
        .drop(["route_id"], axis=1)
        .melt(id_vars="stop_id", value_name="route_id")
        .drop("variable", axis=1)
        .dropna()
    )
    return stops.merge(stop_id_route, on="stop_id")


def read_lines_tables(path, folder, service):
    """Read tables containing route, individual shape (ponts along the route), and trips data
    
    Returns: routes, shapes, trips (tuple): DataFrames for routes, shapes, and trips
    """
    routes = pd.read_csv(
        os.path.join(path, folder, f"{service}", "routes.txt"), dtype={"route_id": str}
    )
    routes = pd.DataFrame(
        routes,
        columns=["route_id", "route_short_name", "route_long_name", "route_color"],
    )

    routes.rename(
        columns={
            "route_short_name": "route_short",
            "route_long_name": "route_long",
            "route_color": "color",
        },
        inplace=True,
    )

    shapes = pd.read_csv(
        os.path.join(path, folder, f"{service}", "shapes.txt"),
        usecols=["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"],
        dtype={"shape_id": str},
    )

    shapes.rename(columns={"shape_pt_lat": "lat", "shape_pt_lon": "lon"}, inplace=True)

    shapes.sort_values(["shape_id", "shape_pt_sequence"], inplace=True)

    trips = pd.read_csv(
        os.path.join(path, folder, f"{service}", "trips.txt"),
        usecols=["route_id", "direction_id", "shape_id"],
        dtype={"shape_id": str, "route_id": str},
    )
    trips = trips.rename(columns={"direction_id": "dir_id"}).drop_duplicates()
    return routes, shapes, trips


def create_line_segments(df, x="lon", y="lat", epsg=4269):
    """Creates a GeodataFrame of line segments from the 
        shapes dataframe (CRS is NAD83)
        
       Params:
            df (DataFrame): pandas DataFrame 
            x, y (str, optional) Default values x="lon", y="lat", 
            column names for x and y coordinates
            epsg (int): Default value epsg=4269; EPSG value for x,y coordinate system
        Returns: 
            gdf: (GeoDataFrame) Line GeoDataFrame in passed Coordinate System 
    """

    if df[x].isna().sum() > 0 or df[y].isna().sum() > 0:
        raise f"DataFrame contains Null coordinates; consider removing rows with Null {x,y} values"

    points = [Point(xy) for xy in zip(df[x], df[y])]
    gdf = gpd.GeoDataFrame(df.copy(), geometry=points)
    line_segments = (
        gdf.groupby(["shape_id"])["geometry"]
        .apply(lambda x: LineString(x.tolist()))
        .reset_index()
    )

    gdf_out = gpd.GeoDataFrame(line_segments, geometry="geometry", crs=CRS.from_epsg(epsg))
    return gdf_out


def create_point_shapes(df, x="stop_lon", y="stop_lat", epsg=4269):
    """ Create a point GeodataFrame from DataFrame with x,y coordinates
        in NAD83 coordinate system
        
        Params:
            df (DataFrame): pandas DataFrame 
            x, y (str, optional) Default values x="stop_lon", y="stop_lat", 
            column names for x and y coordinates
            epsg (int): Default value epsg=4269; EPSG value for x,y coordinate system
        Returns: 
            gdf: (GeoDataFrame) Point GeoDataFrame in NAD83 Coordinate System
    """
    if df[x].isna().sum() > 0 or df[y].isna().sum() > 0:
        raise Exception(f'''DataFrame contains Null coordinates; 
                        consider removing rows with Null {x,y} values''')

    points = [Point(xy) for xy in zip(df[x], df[y])]
    gdf = gpd.GeoDataFrame(df, geometry=points, crs=CRS.from_epsg(epsg))
    return gdf


def write_feature_report(path, folder, feature, feature_name):
    """Write feature count to text file
       Params:
           path(str): Path to the directory where GTFS data is stored
           folder (str): Name of the folder where the GTFS data is stored
           feature (GeoDataFrame): GeoDataFrame object for which to write feature count
           feature_name (str): Output name of the feture
        
    """
    with open(os.path.join(path, folder, "feature_report.txt"), "a") as report_file:
        report_file.write(f"Feature count for {feature_name} = {feature.shape[0]}\n")


def make_rail_stops_shapefiles(path, folder, rail):
    """ Create stops shapefiles for the given rail service
    
        Params:
            path(str): Path to the directory where GTFS data is stored
            folder (str): Name of the folder where the GTFS data is stored
            rail: (str): name of rail service; one of "LIRR", "metro_north" or "nyc_subway"
            
        Created shapefiels are stored in the 'shapes' folder in the same directory as 
        as the the input parameters.
    """
    try:
        counties = gpd.read_file(
            os.path.join(path, "counties_bndry.geojson"), driver="GeoJSON"
        )
        # reproject to NY State Plane
        counties = counties.to_crs(epsg=2263)

        stops = pd.read_csv(
            os.path.join(path, folder, f"{rail}", "stops.txt"),
            usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"],
        )

        stops = stops.loc[
            stops["stop_id"].isin(
                stops.stop_id.astype(str)
                .str.rstrip("N")
                .str.rstrip("S")
                .unique()
                .tolist()
            )
        ]

        # correct coordinates of the station with id='H01'
        stops.loc[stops["stop_id"] == "H01", "stop_lat"] = 40.672086
        stops.loc[stops["stop_id"] == "H01", "stop_lon"] = -73.835914

        df = stops.loc[stops.duplicated(subset=["stop_lat", "stop_lon"])][
            ["stop_lat", "stop_lon", "stop_id"]
        ]  # get the duplicate stations only; columns specified
        df.rename(
            columns={"stop_id": "stop_id2"}, inplace=True
        )  # rename the last column; it will be used as stop_id2 to reference the removed duplicates

        if rail == "nyc_subway":
            stops = (
                stops.merge(trains_at_stops, on="stop_id", how="outer")
                .drop_duplicates(["stop_lat", "stop_lon"], keep="first")
                .merge(df, on=["stop_lat", "stop_lon"], how="left")
            )
            stops=stops.loc[~stops['stop_id'].isin(non_existent_stops), :]
            
        elif rail == "metro_north":
            # these are stops where shuttle bus make stops
            metro_north_bus_stops = stops.loc[
                (stops["stop_id"] > 500)
                & (stops["stop_id"] != 622)
                & (stops["stop_id"] < 1000)
                | (stops["stop_id"] == 14)
                | (stops["stop_id"] == 16)
            ].copy()
            stops = stops.loc[
                (stops["stop_id"] < 500) | (stops["stop_id"] == 622)
            ].copy()
            stops = stops.drop_duplicates(["stop_lat", "stop_lon"], keep="first")
            bus_stops_geo = create_point_shapes(metro_north_bus_stops)
            bus_stops_geo = bus_stops_geo.to_crs(
                CRS.from_epsg(2263)
            )  # reproject to NY State Plane (ft)
            bus_stops_geo = gpd.sjoin(
                bus_stops_geo, counties, how="inner", predicate="intersects"
            ).drop("index_right", axis=1)
            # save shuttle bus GeoDataframe to shapefiles
            bus_stops_geo.to_file(
                os.path.join(
                    path, folder, "shapes", f"{rail}_bx_bus_{monthYear.lower()}.shp"
                )
            )
            write_feature_report(
                path=path,
                folder=folder,
                feature=bus_stops_geo,
                feature_name=f"{rail}_bx_bus_{monthYear.lower()}.shp",
            )

        else:
            stops = stops.drop_duplicates(["stop_lat", "stop_lon"], keep="first")

        stops_geo = create_point_shapes(stops)
        stops_geo = stops_geo.to_crs(
            CRS.from_epsg(2263)
        )  # reproject to NY State Plane (ft)
        stops_geo = gpd.sjoin(stops_geo, counties, how="inner", predicate="intersects").drop(
            "index_right", axis=1
        )
        # save GeoDataframe to shapefiles
        stops_geo.to_file(
            os.path.join(
                path, folder, "shapes", f"stops_{rail}_{monthYear.lower()}.shp"
            )
        )

        write_feature_report(
            path=path,
            folder=folder,
            feature=stops_geo,
            feature_name=f"stops_{rail}_{monthYear.lower()}.shp",
        )
        print(f"Created stop shapefiles for {rail}")

    except Exception as e:
        logger.exception("Unexpected exception occurred")
        raise


def make_rail_routes_shapefiles(path, folder, rail):
    """ Create route shapefiles for the given rail service
    
        Params:
            path(str): Path to the directory where GTFS data is stored
            folder (str): Name of the folder where the GTFS data is stored
            rail: (str): name of rail service; one of "LIRR", "metro_north" or "nyc_subway"
            
            Created shapefiels are stored in the 'shapes' folder in the same directory as 
            as the the input parameters.
    """
    try:
        routes, shapes, trips = read_lines_tables(
            path=path, folder=folder, service=rail
        )
        # create new df that doesn't contain unusual service for MTA (applies to subway only)

        if rail == "nyc_subway":
            shapes = shapes.loc[~shapes["shape_id"].isin(subway_segments_to_remove)].copy()

        if rail == "metro_north":
            # these shape_ids are from the generalized version of the routes
            shapes = shapes.loc[~shapes["shape_id"].isin(["52", "51", "33", "34"])].copy()

        shapes = shapes.merge(
            trips[["route_id", "shape_id"]], on="shape_id", how="left"
        ).drop_duplicates()
        
        points_per_shape_id=shapes.groupby('shape_id')['shape_pt_sequence'].count()
        not_enough_for_line=points_per_shape_id.loc[points_per_shape_id<2].index.tolist()
        
        good_points=shapes.loc[~shapes['shape_id'].isin(not_enough_for_line)]

        line_segments = create_line_segments(good_points)

        if rail == "nyc_subway":
            line_segments["route_id"] = line_segments["shape_id"].str.split(
                ".", expand=True
            )[0]
        else:
            line_segments = line_segments.merge(trips, on="shape_id").drop("dir_id", axis=1)

        lines = line_segments.dissolve(by="route_id", as_index=False)

        rail_lines = lines.merge(routes, on="route_id")
        # reinitialize CRS
        rail_lines.crs=CRS.from_epsg(4269)

        if rail == "nyc_subway":
            rail_lines = rail_lines.merge(
                route_groups, on="route_id"
            )  # table join for groups (subway only)
            # add missing colors for S and SIR lines of the subway
            rail_lines.loc[rail_lines["route_id"] == "FS", "color"] = "808183"
            rail_lines.loc[rail_lines["route_id"] == "H", "color"] = "808183"
            rail_lines.loc[rail_lines["route_id"] == "SI", "color"] = "053159"
            # and make route_short equal to JZ rather than J
            rail_lines.loc[rail_lines["route_id"] == "J", "route_short"] = "JZ"
            rail_lines = rail_lines.drop("shape_id", axis=1)
        else:
            rail_lines = rail_lines.drop(["shape_id", "route_short"], axis=1)
        rail_lines["color"] = "#" + rail_lines["color"]
        rail_lines = rail_lines.to_crs(epsg=2263)  # reproject to State Plane
        # save GeoDataframe to shapefiles
        rail_lines.to_file(
            os.path.join(
                path,
                folder,
                "shapes",
                f"routes_{rail}_{monthYear.lower()}.shp",
            )
        )
        write_feature_report(
            path=path,
            folder=folder,
            feature=rail_lines,
            feature_name=f"routes_{rail}_{monthYear.lower()}.shp",
        )

        print(f"Created route shapefiles for {rail}")
    except Exception as e:
        logger.exception("Unexpected exception occurred")
        raise


def make_bus_stops_shapefiles(path, folder):
    """ Create local and express bus stops shapefiles
    
        Params:
            path(str): Path to the directory where GTFS data is stored
            folder (str): Name of the folder where the GTFS data is stored
            
        Created shapefiels are stored in the 'shapes' folder in the same directory as 
        as the the input parameters.
    """
    bus_services = ["mn_bus", "si_bus", "qn_bus", "bx_bus", "bk_bus", "bus_company"]
    bus_stops = []
    try:
        for bus_service in bus_services:
            stops = pre_process_stops(path=path, folder=folder, bus_service=bus_service)
            bus_stops.append(stops)

        all_stops = pd.concat(bus_stops)

        local_stops_mask = all_stops["route_id"].str.match(
            r"([A-W-Z]\d+|BX\d+)(?!^X\.*?)", na=False
        )
        local_stops = all_stops.loc[local_stops_mask].copy()
        express_stops = all_stops.loc[~local_stops_mask].copy()

        local_stop_shapes = create_point_shapes(local_stops)
        local_stop_shapes = local_stop_shapes.to_crs(CRS.from_epsg(2263))

        express_stop_shapes = create_point_shapes(express_stops)
        express_stop_shapes = express_stop_shapes.to_crs(CRS.from_epsg(2263))

        counties = gpd.read_file(
            os.path.join(path, "counties_bndry.geojson"), driver="GeoJSON"
        )

        # reproject to NY State Plane (ft)
        counties = counties.to_crs(CRS.from_epsg(2263))

        local_stop_shapes = gpd.sjoin(
            local_stop_shapes, counties, how="inner", predicate="intersects"
        ).drop(["route_id", "index_right"], axis=1)

        express_stop_shapes = gpd.sjoin(
            express_stop_shapes, counties, how="inner", predicate="intersects"
        ).drop(["route_id", "index_right"], axis=1)

        # save GeoDataframes to shapefiles
        local_stop_shapes.drop_duplicates(
            subset=["stop_id", "stop_lat", "stop_lon"]
        ).to_file(
            os.path.join(
                path, folder, "shapes", f"bus_stops_nyc_{monthYear.lower()}.shp"
            )
        )

        write_feature_report(
            path=path,
            folder=folder,
            feature=local_stop_shapes,
            feature_name=f"bus_stops_nyc_{monthYear.lower()}.shp",
        )
        express_stop_shapes.drop_duplicates(
            subset=["stop_id", "stop_lat", "stop_lon"]
        ).to_file(
            os.path.join(
                path, folder, "shapes", f"express_bus_stops_nyc_{monthYear.lower()}.shp"
            )
        )
        write_feature_report(
            path=path,
            folder=folder,
            feature=express_stop_shapes,
            feature_name=f"express_bus_stops_nyc_{monthYear.lower()}.shp",
        )
        print(f"Created stop shapefiles for local and express bus stops")

    except Exception as e:
        logger.exception("Unexpected exception occurred")
        raise


def make_bus_routes_shapefiles(path, folder):
    """ Create local and express bus routes shapefiles
    
        Params:
            path(str): Path to the directory where GTFS data is stored
            folder (str): Name of the folder where the GTFS data is stored
            
        Created shapefiels are stored in the 'shapes' folder in the same directory as 
        as the the input parameters.
    """
    bus_services = ["mn_bus", "si_bus", "qn_bus", "bx_bus", "bk_bus", "bus_company"]
    express_services = []
    local_services = []
    try:
        for bus_service in bus_services:
            routes, shapes, trips = read_lines_tables(path, folder, service=bus_service)

            shapes = shapes.merge(
                trips[["route_id", "shape_id"]], on="shape_id"
            ).drop_duplicates()

            bus_shapes = shapes.merge(routes, on="route_id")  # table join

            bus_route_shapes = create_point_shapes(bus_shapes, x="lon", y="lat")

            line_segments = create_line_segments(bus_route_shapes)

            # merge trips and routes to line segments
            gdf = line_segments.merge(trips, on="shape_id", how="left")

            gdf = gdf.merge(
                routes, on="route_id", how="left"
            )  # table join to get Route associated columns

            # creates new column as concatenation of route_id and direction_id
            gdf["route_dir"] = gdf.route_id.astype(str).str.cat(
                gdf.dir_id.astype(str), sep="_"
            )

            # dissolves on route_dir to get single line per route
            route_gdf = gdf.dissolve(by="route_dir", as_index=False)

            # reinitialize CRS
            route_gdf.crs=CRS.from_epsg(4269)

            # make hex number for colors
            route_gdf["color"] = "#" + route_gdf["color"].astype(str)

            # create a boolean mask with True values for local services
            local = route_gdf["route_id"].str.match(
                r"([A-W-Z]\d+|BX\d+)(?!^X\.*?)", na=False
            )

            # apply mask to get local routes
            local_routes = route_gdf.loc[local].copy()

            # apply the inverse of mask to get express routes
            express_routes = route_gdf.loc[~local].copy()

            local_services.append(local_routes)
            express_services.append(express_routes)

        express_route_gdf = gpd.GeoDataFrame(
            pd.concat(express_services, sort=False),
            columns=[
                "route_id",
                #                 "dir_id",
                "route_dir",
                "geometry",
                "route_short",
                "route_long",
                "color",
            ],
            crs=CRS.from_epsg(4269),
        )

        local_route_gdf = gpd.GeoDataFrame(
            pd.concat(local_services, sort=False),
            columns=[
                "route_id",
                #                 "dir_id",
                "route_dir",
                "geometry",
                "route_short",
                "route_long",
                "color",
            ],
            crs=CRS.from_epsg(4269),
        )

        local_route_gdf = local_route_gdf.to_crs(
            CRS.from_epsg(2263)
        )  # reproject to NY State Plane (ft)
        express_route_gdf = express_route_gdf.to_crs(
            CRS.from_epsg(2263)
        )  # reproject to NY State Plane (ft)

        # save GeoDataframes to shapefiles
        local_route_gdf.to_file(
            os.path.join(
                path, folder, "shapes", f"bus_routes_nyc_{monthYear.lower()}.shp"
            )
        )

        write_feature_report(
            path=path,
            folder=folder,
            feature=local_route_gdf,
            feature_name=f"bus_routes_nyc_{monthYear.lower()}.shp",
        )
        express_route_gdf.to_file(
            os.path.join(
                path,
                folder,
                "shapes",
                f"express_bus_routes_nyc_{monthYear.lower()}.shp",
            )
        )
        write_feature_report(
            path=path,
            folder=folder,
            feature=express_route_gdf,
            feature_name=f"express_bus_routes_nyc_{monthYear.lower()}.shp",
        )
        print(f"Created line shapefiles for local and express bus routes")

    except Exception as e:
        logger.exception("Unexpected exception occurred")
        raise


def make_subway_entrances_shapefiles(path, folder):
    """Create subway entrances shapefiles from csv data
    
    Data Source is at http://web.mta.info/developers/data/nyct/subway/StationEntrances.csv
        
    Params:
        path(str): Path to the directory where GTFS data is stored
        folder (str): Name of the folder where the GTFS data is stored
            
        Created shapefiels are stored in the 'shapes' folder in the same directory as 
        as the input parameters.
    """

    try:
        # read the entrances data directly from MTA's website
        entrances = pd.read_csv(
            "http://web.mta.info/developers/data/nyct/subway/StationEntrances.csv"
        )

        # write out the entrances data for archivial purposes
        entrances.to_csv(os.path.join(path, folder, "StationEntrances.csv"))

        # get counties to use in spatial join
        counties = gpd.read_file(
            os.path.join(path, "counties_bndry.geojson"), driver="GeoJSON"
        )
        counties = counties.to_crs(
            CRS.from_epsg(2263)
        )  # reproject counties to NY State Plane

        # give shorter names to columns
        entrances.columns = [
            "division",
            "line",
            "stn_name",
            "stn_Lat",
            "stn_Lon",
            "route_1",
            "route_2",
            "route_3",
            "route_4",
            "route_5",
            "route_6",
            "route_7",
            "route_8",
            "route_9",
            "route_10",
            "route_11",
            "entr_type",
            "entry",
            "exit_only",
            "vending",
            "staffing",
            "staff_hour",
            "ada",
            "ada_notes",
            "free_cross",
            "n_s_Street",
            "e_w_Street",
            "corner",
            "lat",
            "lon",
        ]

        # one of the longtitudes is missing negative sign
        # multiply longtitude by -1 where it is positive (in US it will always be negative)
        entrances.update(entrances.loc[entrances["lon"] > 0, "lon"].mul(-1))
        entrances_shapes = create_point_shapes(entrances, x="lon", y="lat")
        entrances_shapes = entrances_shapes.to_crs(
            CRS.from_epsg(2263)
        )  # reproject to NY State Plane (ft)
        entrances_shapes = gpd.sjoin(
            entrances_shapes, counties, how="inner", predicate="intersects"
        ).drop(
            "index_right", axis=1
        )  # spatially join entraces to counties layer
        # change data type of the ADA and free_cross columns -- boolean fields can't be written into shapefile
        entrances_shapes["ada"] = entrances_shapes["ada"].astype(str)
        entrances_shapes["free_cross"] = entrances_shapes["free_cross"].astype(str)
        entrances_shapes.to_file(
            os.path.join(
                path, folder, "shapes", f"subway_entrances_{monthYear.lower()}.shp"
            )
        )  # write geodataframe to shapefile

        write_feature_report(
            path=path,
            folder=folder,
            feature=entrances_shapes,
            feature_name=f"subway_entrances_{monthYear.lower()}.shp",
        )
        print(f"Created subway entrances shapefiles")

    except Exception as e:
        logger.exception("Unexpected exception occurred")
        raise
