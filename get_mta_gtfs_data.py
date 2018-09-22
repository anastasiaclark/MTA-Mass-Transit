# -*- coding: utf-8 -*-
"""
Created on Tue May 23 09:09:26 2017

This script downloads the GTFS data feeds and 
places them into corresponding folders. The dates of the MTA
updates are written into updates.txt file.

@author: AClark
last updated on : May 18, 2018

"""

import urllib
from bs4 import BeautifulSoup
import requests, os
import zipfile

mon_year = input('Please provide the folder name to create, Ex: May2018\n')

# server_path=r'\\DFSN1V-B\Shares\LibShare\Shared\Divisions\Graduate\GEODATA\MASS_Transit'
server_path = os.getcwd()
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

# get all `li` elements
lis=soup.find_all('li')

# find links and their associated texts in li elements 
all_links={l.find('a').get('href'):[l.text, l.find('a').text] for l in lis if l.find('a') and l.text}

# get links of the GTFS static feeds only 
gtfs = [k for k in all_links.keys() if k and '.zip' in k and k.startswith('data')
        and 'Shapefiles' not in k and 'Historical' not in k]

# place link and the cleaned-up text of the link in a dictionary 
gtfs_d = {l: all_links[l][1].strip('-').strip() for l in gtfs}

# get the info when the GTF feed was updated
updates={l: all_links[l][0] for l in gtfs}
dates=[v for v in updates.values()]
dates_fromatted=[' '.join(d.split()) for d in dates]

print ('Downloading the data.............')
# download and unzip the data into its appropriate folders
for k, v in gtfs_d.items():
    name = '{}.zip'.format(folders_match[v])
    urllib.request.urlretrieve(os.path.join(base_path, k), os.path.join(server_path, mon_year, folders_match[v], name))
    zip_ref = zipfile.ZipFile(os.path.join(server_path, mon_year, folders_match[v], name), 'r')
    zip_ref.extractall(os.path.join(server_path, mon_year, folders_match[v]))
    zip_ref.close()

# write out the dates of the latest update by MTA for each data downloaded
with open (os.path.join(server_path, mon_year, 'updates.txt'),'w') as t:
    for line in dates_fromatted:
        t.write(line+'\n')
        
print ('Done!', 'Check the', mon_year, 'folder')      