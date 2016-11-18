#!/usr/bin/env python

import csv, geojson
from PIL import Image

DATA_FOLDER = '../data'
# Digested CSV made using export_csv_digest.py
IN_CSV = DATA_FOLDER+'/opentraffic-000.csv'
# Takes a GeoJSON generated from the Shapefile (ogr2ogr -f GeoJSON opentraffic_route.geojson opentraffic_route.shp)
IN_GEOJSON = DATA_FOLDER+'/opentraffic_route.geojson'
# This files will be merged in a GeoJSON file containing the geometry
OUT_GEOJSON = DATA_FOLDER+'/opentraffic.json'
# ... and a image with the average speed over time
OUT_HOURS_INDEX = DATA_FOLDER+'/hours.json'
# ... and a image with the average speed over time
OUT_IMAGE = DATA_FOLDER+'/opentraffic.png'
OUT_IMAGE_HEIGHT = 1000

# Some small useful functions
def remove_duplicates(l):
    return list(set(l))

def find_average(_dict):
    total = 0
    samples = 0 
    for key, value in _dict.iteritems():
        total += float(value)
        samples += 1
    return total/samples

# Gather time/geom data from the CSV file
time_indices = []
geom_indices = []
speeds = dict()
with open(IN_CSV, 'rb') as csv_file:
    reader = csv.reader(csv_file)
    # skip header
    next(reader, None)
    for row in reader:
        geom_id = row[0]
        geom_indices.append(geom_id)
        time_id = int(row[1]);
        time_indices.append(time_id)
        if not geom_id in speeds:
            speeds[geom_id] = {}
        speeds[geom_id][str(time_id)] = row[2]

# Housekeep the indices list
print "pre clean:",len(time_indices),'(time_indices),',len(geom_indices),'(geom_indices)'
time_indices = remove_duplicates(time_indices)
time_indices = sorted(time_indices, key=int)
geom_indices = remove_duplicates(geom_indices)
print "post clean:",len(time_indices),'(time_indices -> width),',len(geom_indices),'(geom_indices -> height)'

# Create an index file of the hours
out_hours = open(OUT_HOURS_INDEX, 'w')
out_hours.write('['+','.join('"'+str(n)[:4]+'-'+str(n)[4:6]+'-'+str(n)[6:8]+'-'+str(n)[8:10]+'"' for n in time_indices)+']')
out_hours.close()

# Create an image as a look up table wich rows match...
height = OUT_IMAGE_HEIGHT #len(geom_indices)
width = len(time_indices)*int(len(geom_indices)/OUT_IMAGE_HEIGHT+1)
out_image = Image.new('RGBA',(width,height),'black')
pixels = out_image.load()

print "Image will be:",width,height

# the ID of a GeoJson with the geometry
features = []
id_counter = 0
with open(IN_GEOJSON,'rb') as in_geojson_file:
    in_geojson = geojson.load(in_geojson_file)
    for feature in in_geojson.features:
        geom_id = str(feature.properties['segment_id'])
        if geom_id in geom_indices:
            y = id_counter%OUT_IMAGE_HEIGHT
            x_offset = int(id_counter/OUT_IMAGE_HEIGHT)

            features.append(geojson.Feature(geometry=feature.geometry, id=id_counter, properties={'id':id_counter}))
            last_value = -1
            time_samples = len(time_indices)
            for time_index in range(time_samples):
                x = x_offset*time_samples+time_index
                time_id = str(time_indices[time_index])
                
                if time_id in speeds[geom_id]:
                    last_value = float(speeds[geom_id][time_id])

                if last_value == -1:
                    last_value = find_average(speeds[geom_id])

                pixels[x,y] = (int(last_value*2.),0,0,255)
            id_counter += 1

out_image.save(OUT_IMAGE)
out_geojson = open(OUT_GEOJSON, 'w')
out_geojson.write(geojson.dumps(geojson.FeatureCollection(features), sort_keys=True))
out_geojson.close()


