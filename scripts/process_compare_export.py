#!/usr/bin/env python

import os
import csv
from datetime import datetime
from dateutil.relativedelta import relativedelta
import geojson
from PIL import Image

EXTRACT_NAME = 'opentraffic_export_2016-11-30T02-33-55GMT' # Control_Friday vs Carmagedon_Friday

# Global variables
DATA_FOLDER = '../data/'+EXTRACT_NAME
IN_CSV = DATA_FOLDER+'/'+EXTRACT_NAME+'.csv'
IN_SHPFILE = DATA_FOLDER+'/opentraffic_route.shp'

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
    for key, values in _dict.iteritems():
        total += values[0]
        samples += 1
    return total/samples

# Clean previus records
os.system('rm -rf '+IN_GEOJSON)

# Transform ShapeFile into GeoJSON
os.system('ogr2ogr -f GeoJSON '+IN_GEOJSON+' '+IN_SHPFILE)

# DATABASE to store samples on
samples = dict()
# indeces (geometries and times) 
geom_indices = []
time_indices = []

min_speed = 1000
max_speed = 0
max_observations = 0

# Edge Id,Date Start (Baseline),Date End (Baseline),Date Start (Comparison),Date End (Comparison),Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday,Time Start,Time End,Percent Change,Confidence Interval,Alpha,T-Score,Degrees of Freedom,Margin of Error,Normalized by Time,Average Speed KPH (Baseline),Number of Observations (Baseline),Standard Deviation (Baseline),Standard Error (Baseline),99% Upper Bound (Baseline),99% Lower Bound (Baseline),97% Upper Bound (Baseline),97% Lower Bound (Baseline),95% Upper Bound (Baseline),95% Lower Bound (Baseline),90% Upper Bound (Baseline),90% Lower Bound (Baseline),Average Speed (Comparison),Number of Observations (Comparison),Standard Deviation (Comparison),Standard Error (Comparison),99% Upper Bound (Comparison),99% Lower Bound (Comparison),97% Upper Bound (Comparison),97% Lower Bound (Comparison),95% Upper Bound (Comparison),95% Lower Bound (Comparison),90% Upper Bound (Comparison),90% Lower Bound (Comparison)
with open(IN_CSV, 'rb') as csv_file:
    reader = csv.reader(csv_file)
    # skip header
    next(reader, None)
    file = None
    for row in reader:
        # Extract and Index Geometry ID
        geom_id = row[0]
        geom_indices.append(geom_id)

        # Extract time by calculating the timestamp from the "Date Start" ...
        time = row[10].split(':')
        if len(time[0]) == 3:
            time[0] = time[0][1:]
        timestamp = datetime.strptime(row[1]+' '+str(1+int(time[0]))+':'+str(1+int(time[1])),'%m/%d/%Y %H:%M')
        # Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday
        time_offset = 0*int(row[3]) + 1*int(row[4]) + 2*int(row[5]) + 3*int(row[6]) + 4*int(row[7]) + 5*int(row[8]) + 6*int(row[9])
        timestamp = timestamp + relativedelta(days=time_offset)
        # Indexing the time stamp
        time_id = int(timestamp.strftime("%Y%m%d%H"));
        time_indices.append(time_id)

        # Extract Speed number
        speed = float(row[12])
        if speed > max_speed:
            max_speed = speed
        elif speed < min_speed:
            min_speed = speed

        # Extract Observation number
        observations = int(float(row[13]))
        if observations > max_observations:
            max_observations = observations

        # Add to DATABASE of SAMPLES
        if not geom_id in samples:
            samples[geom_id] = {}
        samples[geom_id][str(time_id)] = [speed,observations]

# Report
print len(samples),"total samples"
print max_observations,"max sources for samples"
print "The range of speed goes from ", min_speed, 'to', max_speed

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

print "An image of ",width,'x',height,'will be generated to contain the speed and observations samples at',OUT_IMAGE

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
            last_speed = -1
            time_samples = len(time_indices)
            for time_index in range(time_samples):
                x = x_offset*time_samples+time_index
                time_id = str(time_indices[time_index])
                total_samples = 0

                if time_id in samples[geom_id]:
                    last_speed = samples[geom_id][time_id][0]
                    total_samples = samples[geom_id][time_id][1]

                if last_speed == -1:
                    last_speed = find_average(samples[geom_id])

                pixels[x,y] = (int(last_speed*1.5),total_samples,0,255)
            id_counter += 1

out_image.save(OUT_IMAGE)

print 'A .json file containing the geometry for the samples data will be generated at', OUT_GEOJSON
out_geojson = open(OUT_GEOJSON, 'w')
out_geojson.write(geojson.dumps(geojson.FeatureCollection(features), sort_keys=True))
out_geojson.close()