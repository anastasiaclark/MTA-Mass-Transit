# MTA-Mass-Transit
Convert GTFS data from the MTA's Static Developer Feed to usable GIS layers.

# Required libraries:
* urllib
* BeautifulSoup
* requests
* pandas
* geopandas
* shapely

# Run order
1. [Download MTA Statis feeds first by running get_mta_gtfs_data.py](get_mta_gtfs_data.py). Enter folder name when prompted.
2. Run the rest of the scripts and provide same folder name as in step 1 when prompted
