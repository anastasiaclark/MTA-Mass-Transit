# -*- coding: utf-8 -*-
"""
Created on Tue May 23 09:09:26 2017

@author: AClark
"""

import urllib
from bs4 import BeautifulSoup
import requests, os
import zipfile

mon_year = 'May2018'

# server_path=r'\\DFSN1V-B\Shares\LibShare\Shared\Divisions\Graduate\GEODATA\MASS_Transit'
server_path = '/Users/anastasiaclark/MyStaff/Git_Work/MTA-Mass-Transit'
base_path = 'http://web.mta.info/developers'

folders_to_create = ['nyc_subway', 'bk_bus', 'qn_bus', 'bus_company',
                     'bx_bus', 'si_bus', 'mn_bus', 'LIRR', 'metro_north', 'shapes']

folders_match = {'Bus Company': 'bus_company', 'Long Island Rail Road': 'LIRR',
             'Metro-North Railroad': 'metro_north',
             'Bronx': 'bx_bus', 'Brooklyn': 'bk_bus', 'Manhattan': 'mn_bus',
             'Queens': 'qn_bus', 'Staten Island': 'si_bus',
             'New York City Transit Subway': 'nyc_subway'}

for folder in folders_to_create:
    if not os.path.exists(os.path.join(server_path, mon_year, folder)):
        os.makedirs(os.path.join(server_path, mon_year, folder))

url = 'http://web.mta.info/developers/developer-data-terms.html#data'
r = requests.get(url)
data = r.text
soup = BeautifulSoup(data, 'lxml')
all_links = {l.get('href'): l.text for l in soup.find_all('a')}

gtfs = [k for k in all_links.keys() if k is not None and '.zip' in k and k.startswith('data')
        and 'Shapefiles' not in k and 'Historical' not in k]

gtfs_d = {l: all_links[l].strip('-').strip() for l in gtfs}

for k, v in gtfs_d.items():
    name = '{}.zip'.format(folders_match[v])
    urllib.request.urlretrieve(os.path.join(base_path, k), os.path.join(server_path, mon_year, folders_match[v], name))
    zip_ref = zipfile.ZipFile(os.path.join(server_path, mon_year, folders_match[v], name), 'r')
    zip_ref.extractall(os.path.join(server_path, mon_year, folders_match[v]))
    zip_ref.close()
