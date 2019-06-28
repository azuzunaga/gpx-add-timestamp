import os
import gpxpy
import gmplot
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from dotenv import load_dotenv

# Get Google Maps API key
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Open file using system dialog
root = tk.Tk()
root.withdraw()

file_path = filedialog.askopenfilename()

root.update()

# Parse GPX file
gpx_file = open(file_path, 'r')
gpx = gpxpy.parse(gpx_file)

# Create a dataframe with the GPX data
data = gpx.tracks[0].segments[0].points

df = pd.DataFrame(columns=['lon', 'lat', 'alt', 'time', 'ele_change'])

# Get the climbing stats while creating the dataframe
climbing_stats = {'asc': 0, 'desc': 0, 'flat': 0}

for index, point in enumerate(data, start=0):
    climb_delta = point.elevation - data[index - 1].elevation
    if climb_delta > 0:
        climbing_stats['asc'] += 1
        ele_change = 'asc'
    elif climb_delta < 0:
        climbing_stats['desc'] += 1
        ele_change = 'desc'
    else:
        climbing_stats['flat'] += 1
        ele_change = 'flat'

    df = df.append({'lon': point.longitude, 'lat': point.latitude,
                    'alt': point.elevation, 'time': point.time,
                    'ele_change': ele_change}, ignore_index=True)

# Calculate total time, time per coordinate, and total points
total_points = len(df)
total_time = df.iloc[-1].time - df.iloc[0].time
timedelta = (df.iloc[-1].time - df.iloc[0].time) / total_points

# Figure out ascent and descent rates
desc_rate = (total_points -
             climbing_stats['flat']) / (climbing_stats['desc'] * 2)
asc_rate = climbing_stats['desc'] / climbing_stats['asc'] * desc_rate

# Fill in time column
for i, j in df.iterrows():
    if i == 0 or i == len(df) - 1:
        continue
    ele_change = j.ele_change
    if ele_change == 'asc':
        time_step = timedelta * asc_rate
    elif ele_change == 'desc':
        time_step = timedelta * desc_rate
    else:
        time_step = timedelta

    df.iat[i, -2] = df.iat[i - 1, -2] + time_step

# Create a new GPX file with time data
new_gpx = gpxpy.gpx.GPX()

# Create first track in our GPX:
gpx_track = gpxpy.gpx.GPXTrack()
new_gpx.tracks.append(gpx_track)

# Create first segment in our GPX track:
gpx_segment = gpxpy.gpx.GPXTrackSegment()
gpx_track.segments.append(gpx_segment)

for _, j in df.iterrows():
    gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(
        j.lat, j.lon, elevation=j.alt, time=j.time))

# Plot the data
# Get the center of the map
min_lat, max_lat, min_lon, max_lon = \
    min(df['lat']), max(df['lat']), min(df['lon']), max(df['lon'])

center_lat, center_lon = \
    min_lat + (max_lat - min_lat) / 2, min_lon + (max_lon - min_lon) / 2,

# Create an empty map with zoom level 14
google_map = gmplot.GoogleMapPlotter(
    center_lat, center_lon, 13, GOOGLE_MAPS_API_KEY
)

# Add the data to the map
google_map.plot(df['lat'], df['lon'], '#FB051D', edge_width=2)

google_map.draw('google_map.html')
