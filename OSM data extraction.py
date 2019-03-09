## This python code demonstrates how to manipulate and break OpenStreetMap (OSM) data as per our requirements. 
## This code will help you obtain OSM extracts for a smaller regions based on a starting point and then forming polygons around that point for which you need OSM extracts 
## First you need to download the OSM data in .osm/.pbf format which is available online. 
## You need OSMIUM command line tool installed on your system. OSMIUM is way faster than OSMOSIS.

## To run below-mentioned code, initially I had some basic data in a particular format in an excel sheet
## columns ==> Id, origin_latitude, origin_longitude, start_angle, stop_angle, distance 

## Caution: had to mask original file names, so you wil need to change the file locations properly wherever required

import os
import geopy
from geopy.distance import VincentyDistance
import time
from subprocess import call
import pandas as pd
import glob
import xml.etree.ElementTree as ET
from datetime import datetime

t1 = datetime.now()

df = pd.read_excel("abc.xlsx")

for row in range(len(df)):
    id = df["id"][row]
    lat1 = df["latitude"][row]
    lon1 = df["longitude"][row]
	start_angle = df["start_angle"][row]
    stop_angle = df["stop_angle"][row]
    dist = df["distance"][row]

    # Creating a list of coordinates to form a polygon based on the origin, start and stop angles

    coordinates = []

    initial_coord = str(format(round(lon1, 6), '.6f')) + '    ' + str(format(round(lat1, 6), '.6f'))

    coordinates.append(initial_coord)

    if stop_angle > start_angle:
        for angle in range(int(round(start_angle)), int(round(stop_angle + 2)), 2):
            origin = geopy.Point(lat1, lon1)
            destination = VincentyDistance(kilometers=dist).destination(origin, angle)
            lat2, lon2 = destination.latitude, destination.longitude
            final = str(format(round(lon2, 6), '.6f')) + '    ' + str(format(round(lat2, 6), '.6f'))
            coordinates.append(final)
    else:
        for angle in range(int(round(start_angle)), int(round(stop_angle + 362)), 2):
            if angle <= 360:
                origin = geopy.Point(lat1, lon1)
                destination = VincentyDistance(kilometers=dist).destination(origin, angle)
                lat2, lon2 = destination.latitude, destination.longitude
                final = str(format(round(lon2, 6), '.6f')) + '    ' + str(format(round(lat2, 6), '.6f'))
                coordinates.append(final)
            else:
                angle1 = angle - 360
                origin = geopy.Point(lat1, lon1)
                destination = VincentyDistance(kilometers=dist).destination(origin, angle1)
                lat2, lon2 = destination.latitude, destination.longitude
                final = str(format(round(lon2, 6), '.6f')) + '    ' + str(format(round(lat2, 6), '.6f'))
                coordinates.append(final)

    coordinates.append(initial_coord)

    # Function to create a .poly file

    def createpolyfile():
        f = open("***/poly__" + str(id) + str(time.strftime("%Y%m%d")) + ".poly", "w+")

        f.write("poly_"+str(id)+"\r\n")
        f.write("1\r\n")

        cnt = 0

        for i in range(len(coordinates)):
            f.write("     " + str(coordinates[cnt]) + "\r\n")
            cnt = cnt + 1

        f.write("END\r\n")
        f.write("END")

        f.close()

    createpolyfile()

t2 = datetime.now()

# obtain OSM extracts from whole nation OSM file

def nation(infile):
    for file in infile:
        call(["osmium", "extract", "-p", file,
              "***/USA_Final.osm.pbf", "-o",
              "***/xyz__" + str(file.split('__')[1]) + "__" +
              file.split('__')[2] + "__" + str(file.split('__')[3]) + "__" + file.split('__')[4] + "__" +
              file.split('__')[5] + "__" + str(time.strftime("%Y%m%d")) + ".osm"])

# obtain OSM extracts from state OSM files
			  
def states(infile):
    for file in infile:
        call(["osmium", "extract", "-p", file,
              "***/" + file.split('__')[4] + "-latest.osm.pbf", "-o",
              "***/xyz__" + str(file.split('__')[1]) + "__" + file.split('__')[2] + "__" +
              str(file.split('__')[3]) + "__" + file.split('__')[4] + "__" + file.split('__')[5] + "__" + str(
                  time.strftime("%Y%m%d")) + ".osm"])

## saved all .poly file at a location
infile = glob.glob(os.path.join('***/poly/*'))

## calling the states() function defined above to obtain the OSM extracts for all the .poly files one by one and saving the smaller .osm files at a different location
states(infile)

t3 = datetime.now()

df_final = pd.DataFrame(columns=['id', 'category', 'sub_category', 'count'])

## refering to all the small .osm files generated above to pull the required information regarding mapping features
## .osm files are .xml files and need to be parsed before use

for file in glob.glob(os.path.join('***/osm/*')):
    try:
        tree = ET.parse(file)
        root = tree.getroot()

        list = []

        for tag in root.iter('tag'):
            list.append(tag.attrib)

        test = pd.DataFrame(list)

		## keeping only required categories from the OSM data (information available online)
		
        osm_map = ['aerialway', 'aeroway', 'amenity', 'barrier', 'boundary', 'building', 'craft', 'emergency',
                   'geological', 'highway', 'historic', 'landuse', 'leisure', 'man_made', 'military', 'natural',
                   'office', 'place', 'power', 'public transport', 'railway', 'route', 'shop', 'sport', 'tourism',
                   'waterway', 'name']

        data = test[test['k'].isin(osm_map)]

        df = pd.DataFrame(data.groupby(['k', 'v']).size())

        df.reset_index(inplace=True)

        df['id'] = file.split('__')[1]

        df.columns = ['category', 'sub_category', 'count', 'id']

        df_new = df[['id', 'category', 'sub_category', 'count']]

        df_final = df_final.append(df_new)

    except:
        f = open("***/xyz__" + str(file.split('__')[1]) + "__" +
                 file.split('__')[2] + "__" + str(file.split('__')[3]) + "__" + file.split('__')[4] + "__" +
                 file.split('__')[5] + "__" + str(time.strftime("%Y%m%d")) + ".txt", "w+")
        f.write("XML file is empty.")
        f.close()
        pass

df_final.to_csv('***/xyz_final_data.csv', sep=',', index=False)

t4 = datetime.now()

print("Total files not parsed: ", len(glob.glob(os.path.join('***/xyz_no_data/*'))))

print("Time for creating .poly files: ", t2 - t1)
print("Time for creating .osm files: ", t3 - t2)
print("Time for parsing .osm files and creating a final data set: ", t3 - t2)

print("Time for total process: ", datetime.now() - t1)

# print('Duration: {}'.format(end_time - start_time))