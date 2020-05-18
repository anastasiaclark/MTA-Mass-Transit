#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compares the number of bus routes between two different versions of the NYC
mass transit series. Draws from trips.txt as this records active routes; 
routes.txt contains all possible routes but they may not all be active
"""

import os

v1='dec2019'
v2='may2020'

project1=os.path.join(v1)
project2=os.path.join(v2)

def unique_routes(project):
    trips=[]    
    for folder in os.listdir(project):
        if folder.find('bus') > -1:
            trip_path=os.path.join(project,folder,'trips.txt')
            with open (trip_path,'r') as readfile:
                readfile.readline()
                for line in readfile:
                    line_list=line.strip().split(',')
                    trips.append(line_list[0])
    set_trips=set(trips)
    unq_trips=sorted(set_trips)
    return unq_trips

routes1=unique_routes(project1)
routes2=unique_routes(project2)

v1count=len(routes1)
v2count=len(routes2)

not_in_1=[item for item in routes2 if not item in routes1]
not_in_2=[item for item in routes1 if not item in routes2]

not1count=len(not_in_1)
not2count=len(not_in_2)

print('Routes in',v1, ':',v1count)
print('Routes in',v2, ':',v2count)
print('Routes in',v1,'that are not in',v2,':',not2count)
print(not_in_2)
print('Routes in',v2,'that are not in',v1,':',not1count)
print(not_in_1)






