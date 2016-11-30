#!/usr/bin/env python

import os, csv
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Global variables
DATA_FOLDER = '../data'
# EXTRACT_NAME = 'opentraffic_export_2016-11-17T20-26-26GMT' # Average_Monday
# EXTRACT_NAME = 'opentraffic_export_2016-11-30T02-23-51GMT' # Control_Friday
EXTRACT_NAME = 'opentraffic_export_2016-11-30T02-20-20GMT' # Carmagedon_Friday
# EXTRACT_NAME = 'opentraffic_export_2016-11-30T02-33-55GMT' # Control_Friday vs Carmagedon_Friday
IN_CSV = DATA_FOLDER+'/'+EXTRACT_NAME+'/'+EXTRACT_NAME+'.csv'
OUT_FORMAT =  DATA_FOLDER+'/opentraffic-%03d.csv'
SAMPLES_PER_FILE = 1701147
header = "Edge_Id,Timestamp,Average_Speed_KPH\n"

# Clean previus records
os.system('rm -rf '+DATA_FOLDER+'/opentraffic-*.csv')
os.system('rm -rf '+DATA_FOLDER+'/opentraffic_route.geojson')

# Transform ShapeFile into GeoJSON
os.system('ogr2ogr -f GeoJSON '+DATA_FOLDER+'/opentraffic_route.geojson '+DATA_FOLDER+'/'+EXTRACT_NAME+'/opentraffic_route.shp')

file_counter = 0
sampler_counter = 0
min_speed = 1000
max_speed = 0
max_samples = 0
with open(IN_CSV, 'rb') as csv_file:
    reader = csv.reader(csv_file)
    # skip header
    next(reader, None)
    file = None
    for row in reader:
        if sampler_counter%SAMPLES_PER_FILE == 0:
            # If there is an open file... close it
            if file != None:
                file.close()

            # Start a new file
            filename = OUT_FORMAT % file_counter
            file = open(filename, 'w')
            file_counter += 1

            # Add header to new CSV file
            file.write(header)
        else:
            # Calculate the timestamp from the "Date Start" ...
            time = row[10].split(':')
            if len(time[0]) == 3:
                time[0] = time[0][1:]
            timestamp = datetime.strptime(row[1]+' '+str(1+int(time[0]))+':'+str(1+int(time[1])),'%m/%d/%Y %H:%M')
            # ... plus adding the offset of days from Wednesday (note: this will not work probably for other extracts)
            time_offset = 0*int(row[3]) + 1*int(row[4]) + 2*int(row[5]) + 3*int(row[6]) + 4*int(row[7]) + 5*int(row[8]) + 6*int(row[9])
            timestamp = timestamp + relativedelta(days=time_offset)

            speed = float(row[12])
            if speed > max_speed:
                max_speed = speed
            elif speed < min_speed:
                min_speed = speed

            samples = float(row[13])
            if samples > max_samples:
                max_samples = samples

            # add row to file
            file.write(row[0]+','+timestamp.strftime("%Y%m%d%H")+','+row[12]+','+row[13]+'\n')
        sampler_counter += 1
file.close()

print sampler_counter,"total samples"
print max_samples,"max sources for samples"
print "The range of speed goes from ", min_speed, 'to', max_speed
