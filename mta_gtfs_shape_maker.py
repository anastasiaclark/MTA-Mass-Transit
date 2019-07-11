import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point, LineString
from fiona.crs import from_epsg
import logging
import datetime

# configure logger
logger = logging.getLogger (__name__)
logger.setLevel (logging.INFO)
handler = logging.FileHandler ("error_log.log")
handler.setLevel (logging.ERROR)
formatter = logging.Formatter ("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter (formatter)
logger.addHandler (handler)

# read-in file that indicates which trains stop at which stations
trains_at_stops = pd.read_csv (
    "http://web.mta.info/developers/data/nyct/subway/Stations.csv",
    usecols=["GTFS Stop ID", "Daytime Routes", "Structure"],
)

trains_at_stops.rename (
    columns={
        "GTFS Stop ID": "stop_id",
        "Daytime Routes": "trains",
        "Structure": "structure",
    },
    inplace=True,
)

# monthYear is appended to all shapefiles names
today = datetime.datetime.today ()
month = today.strftime ("%B").lower ()
year = today.year
monthYear = f'{month}{year}'


def create_stop_shapes(df, x="stop_lon", y="stop_lat"):
    """ Create a point GeodataFrame from df with x,y coordinates
        in NAD83 coordinate system
        
        Params:
            df (DataFrame): pandas DataFrame 
            x, y (str, optional) Default values x="stop_lon", y="stop_lat", 
            column names for x and y coordinates
        Returns:
            GeodataFrame in NY State Plane Projection
    """
    if df[x].isna ().sum () > 0 or df[y].isna ().sum () > 0:
        raise Exception ("DataFrame contains Null coordinates")

    points = [Point (xy) for xy in zip (df[x], df[y])]
    gdf = gpd.GeoDataFrame (df, geometry=points)
    gdf.crs = from_epsg (4269)  # initiate crs as NAD83
    gdf = gdf.to_crs (epsg=2263)  # NY State Plane
    return gdf


def make_rail_stops(path_name, folder, rail):
    """ Create stops shapefiles for the given rail service
    
        Params:
            path_name (str): Path to the directory the GTFS data is stored
            folder (str): Name of the folder where the GTFS data is stored
            rail: (str): name of rail service; one of "LIRR", "metro_north" or "nyc_subway"
            
        Created shapefiels are stored in the 'shapes' folder in the same directory as 
        as the original GTFS data
    """
    try:
        counties = gpd.read_file (
            os.path.join (path_name, "counties_bndry.geojson"), driver="GeoJSON"
        )
        counties = counties.to_crs (epsg=2263)

        file = os.path.join (path_name, folder, f"{rail}")
        stops = pd.read_csv (
            os.path.join (file, "stops.txt"),
            usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"],
        )

        stops = stops.loc[
            stops["stop_id"].isin (
                stops.stop_id.astype (str)
                    .str.rstrip ("N")
                    .str.rstrip ("S")
                    .unique ()
                    .tolist ()
            )
        ]

        # correct coordinates of the station with id='H01'
        stops.loc[stops["stop_id"] == "H01", "stop_lat"] = 40.672086
        stops.loc[stops["stop_id"] == "H01", "stop_lon"] = -73.835914

        df = stops.loc[stops.duplicated (subset=["stop_lat", "stop_lon"])][
            ["stop_lat", "stop_lon", "stop_id"]
        ]  # get the duplciate stations only; columns specified
        df.rename (
            columns={"stop_id": "stop_id2"}, inplace=True
        )  # rename the last column; it will be used as stop_id2 to reference the removed duplicates

        if rail == "nyc_subway":
            stops = (
                stops.merge (trains_at_stops, on="stop_id", how="outer")
                    .drop_duplicates (["stop_lat", "stop_lon"], keep="first")
                    .merge (df, on=["stop_lat", "stop_lon"], how="left")
            )
        elif rail == "metro_north":
            metro_north_bus_stops = stops.loc[
                (stops["stop_id"] > 500)
                & (stops["stop_id"] != 622)
                & (stops["stop_id"] < 1000)
                | (stops["stop_id"] == 14)
                | (stops["stop_id"] == 16)
                ].copy()
            stops = stops.loc[(stops['stop_id'] < 500) | (stops['stop_id'] == 622)].copy()
            stops = stops.drop_duplicates (["stop_lat", "stop_lon"], keep="first")
            bus_stops_geo = create_stop_shapes(metro_north_bus_stops)
            bus_stops_geo = gpd.sjoin (bus_stops_geo, counties, how="inner", op="intersects").drop (
                "index_right", 1)
            bus_stops_geo.to_file(
                os.path.join (
                    path_name, folder, "shapes", f"{rail}__bx_bus_{monthYear.lower()}.shp"

            )

        else:
            stops = stops.drop_duplicates (["stop_lat", "stop_lon"], keep="first")

        stops_geo = create_stop_shapes (stops)

        stops_geo = gpd.sjoin (stops_geo, counties, how="inner", op="intersects").drop (
            "index_right", 1
        )
        stops_geo.to_file (
            os.path.join (
                path_name, folder, "shapes", f"stops_{rail}_{monthYear.lower()}.shp"
            )
        )
        print (f"Created stop shapefiles for {rail}")

    except Exception as e:
        logger.exception ("Unexpected exception occurred")
        raise


# these are segments that represent unusual service (rush hour etc;)
# and don't appear on MTA map.
segments_to_remove = [
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
    "N": "NQR",
    "Q": "NQR",
    "R": "NQR",
    "SI": "SIR",
}

# create a dataframe form group dictionary
route_groups = pd.DataFrame (
    [[key, value] for key, value in d.items ()], columns=["route_id", "group"]
)


def create_line_segments(df, x="lon", y="lat"):
    """Creates a GeodataFrame of line segments from the 
        shapes datframe (CRS is NAD83) 
    """

    if df[x].isna ().sum () > 0 or df[y].isna ().sum () > 0:
        raise "DataFrame contains Null coordinates"

    points = [Point (xy) for xy in zip (df[x], df[y])]
    gdf = gpd.GeoDataFrame (df.copy (), geometry=points)
    line_segments = (
        gdf.groupby (["shape_id"])["geometry"]
            .apply (lambda x: LineString (x.tolist ()))
            .reset_index ()
    )

    gdf_out = gpd.GeoDataFrame (line_segments, geometry="geometry", crs=from_epsg (4269))
    return gdf_out


def make_rail_lines(path_name, folder, rail):
    """ Create route shapefiles for the given rail service
    
        Params:
            path_name (str): Path to the directory the GTFS data is stored
            folder (str): Name of the folder where the GTFS data is stored
            rail: (str): name of rail service; one of "LIRR", "metro_north" or "nyc_subway"
            
            Created shapefiels are stored in the 'shapes' folder in the same directory as 
            as the original GTFS data
    """
    try:
        routes = pd.read_csv (
            os.path.join (path_name, folder, f"{rail}", "routes.txt"),
            usecols=["route_id", "route_short_name", "route_long_name", "route_color"],
            dtype={"route_id": str},
        )

        routes.rename (
            columns={
                "route_short_name": "route_short",
                "route_long_name": "route_long",
                "route_color": "color",
            },
            inplace=True,
        )

        shapes = pd.read_csv (
            os.path.join (path_name, folder, f"{rail}", "shapes.txt"),
            usecols=["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"],
            dtype={"shape_id": str},
        )

        shapes.rename (
            columns={"shape_pt_lat": "lat", "shape_pt_lon": "lon"}, inplace=True
        )

        # create new df that doesn't contain unusual service for MTA (applies to subway only)
        shapes = shapes[~shapes["shape_id"].isin (segments_to_remove)]

        shapes.sort_values (["shape_id", "shape_pt_sequence"], inplace=True)

        trips = pd.read_csv (
            os.path.join (path_name, folder, f"{rail}", "trips.txt"),
            usecols=["route_id", "shape_id"],
            dtype={"shape_id": str, "route_id": str},
        )
        trips = trips.drop_duplicates ()

        shapes = shapes.merge (
            trips[["route_id", "shape_id"]], on="shape_id"
        ).drop_duplicates ()

        if rail == "metro_north":
            # these shape_ids belong to old version of GTFS feed for Metro-North
            shapes = shapes.loc[~shapes["shape_id"].isin (["52", "51"])]

        line_segments = create_line_segments (shapes)
        lines = line_segments.merge (trips, on="shape_id").dissolve (
            by="route_id", as_index=False
        )

        rail_lines = lines.merge (routes, on="route_id")

        if rail == "nyc_subway":
            rail_lines = rail_lines.merge (
                route_groups, on="route_id"
            )  # table join for groups (subway only)
            # add missing colors for S and SIR lines of the subway
            rail_lines.loc[rail_lines["route_id"] == "FS", "color"] = "808183"
            rail_lines.loc[rail_lines["route_id"] == "H", "color"] = "808183"
            rail_lines.loc[rail_lines["route_id"] == "SI", "color"] = "053159"
            # and make route_short equal to JZ rather than J
            rail_lines.loc[rail_lines["route_id"] == "J", "route_short"] = "JZ"
            rail_lines = rail_lines.drop ("shape_id", 1)
        else:
            rail_lines = rail_lines.drop (["shape_id", "route_short"], 1)
        rail_lines["color"] = "#" + rail_lines["color"]
        rail_lines = rail_lines.to_crs (epsg=2263)  # reproject to State Plane
        rail_lines.to_file (
            os.path.join (
                path_name, f"{folder}", "shapes", f"routes_{rail}_{monthYear}.shp"
            )
        )
        print (f"Created route shapefiles for {rail}")
    except Exception as e:
        logger.exception ("Unexpected exception occurred")
        raise


def process_bus_stops(file):
    """Read bus stop tables, join them and deduplicate"""
    stops = pd.read_csv (os.path.join (file, "stops.txt"))
    stop_times = pd.read_csv (os.path.join (file, "stop_times.txt"))
    trips = pd.read_csv (os.path.join (file, "trips.txt"))
    stops = pd.merge (stops, stop_times, on="stop_id", how="left")
    stops = stops.merge (trips, on="trip_id", how="left")
    stops = pd.DataFrame (
        stops, columns=["stop_id", "stop_name", "stop_lat", "stop_lon", "route_id"]
    )
    unique_routes_at_stops = stops.drop_duplicates ()
    return unique_routes_at_stops


def make_bus_stops(path, folder):
    """ Create shapefiles for local and express bus stops
    
        Params:
            path (str): Path to the directory the GTFS data is stored
            folder (str): Name of the folder where the GTFS data is stored
            
        Created shapefiels are stored in the 'shapes' folder in the same directory as 
        as the original GTFS data
    """
    buses = ["mn_bus", "si_bus", "qn_bus", "bx_bus", "bk_bus", "bus_company"]
    bus_stops = []
    try:
        for bus in buses:
            file = os.path.join (path, folder, f"{bus}")
            stops = process_bus_stops (file)
            bus_stops.append (stops)

        all_stops = pd.concat (bus_stops)

        local_stops_mask = all_stops["route_id"].str.match (r"\w\d+|BX\d+")
        local_stops_mask = local_stops_mask.fillna (False)

        local_stops = all_stops.loc[local_stops_mask].copy ()
        express_stops = all_stops.loc[~local_stops_mask].copy ()

        local_stop_shapes = create_stop_shapes (local_stops)
        express_stop_shapes = create_stop_shapes (express_stops)

        counties = gpd.read_file (
            os.path.join (path, "counties_bndry.geojson"), driver="GeoJSON"
        )
        counties = counties.to_crs (from_epsg (2263))

        local_stop_shapes = gpd.sjoin (
            local_stop_shapes, counties, how="inner", op="intersects"
        ).drop (["route_id", "index_right"], 1)

        express_stop_shapes = gpd.sjoin (
            express_stop_shapes, counties, how="inner", op="intersects"
        ).drop (["route_id", "index_right"], 1)

        local_stop_shapes.to_file (
            os.path.join (path, folder, "shapes", f"bus_stops_nyc_{monthYear}.shp")
        )

        express_stop_shapes.to_file (
            os.path.join (
                path, folder, "shapes", f"express_bus_stops_nyc_{monthYear}.shp"
            )
        )
        print (f"Created stop shapefiles for local and express bus stops")

    except Exception as e:
        logger.exception ("Unexpected exception occurred")
        raise
