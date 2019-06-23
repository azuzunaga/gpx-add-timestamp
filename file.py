import gpxpy
import matplotlib.pyplot as plt
import datetime
from math import sqrt, floor
import numpy as np
import pandas as pd
import random

import tkinter as tk
from tkinter import filedialog

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

df = pd.DataFrame(columns=['lon', 'lat', 'alt', 'time'])

for point in data:
    df = df.append({'lon': point.longitude, 'lat': point.latitude,
                    'alt': point.elevation, 'time': point.time}, ignore_index=True)

# Calculate total time, time per coordinate, and total points
total_points = len(df)
total_time = df.iloc[-1].time - df.iloc[0].time
timedelta = (df.iloc[-1].time - df.iloc[0].time) / total_points

# Calculate feet ascending, feet descending, and feet flat
climbing_stats = {'asc': 0, 'desc': 0, 'flat': 0}
for i, j in df.iterrows():
    if i == 0:
        climbing_stats['flat'] += 1
    ele_change = j.alt - df.iat[i - 1, 2]
    if ele_change > 0:
        climbing_stats['asc'] += 1
    elif ele_change < 0:
        climbing_stats['desc'] += 1
    else:
        climbing_stats['flat'] += 1

# Figure out ascent and descent rates
desc_rate = (total_points -
             climbing_stats['flat']) / (climbing_stats['desc'] * 2)
asc_rate = climbing_stats['desc'] / climbing_stats['asc'] * desc_rate

# Fill in time column
for i, j in df.iterrows():
    if i == 0 or i == len(df) - 1:
        continue
    ele_change = j.alt - df.iat[i - 1, 2]
    if ele_change > 0:
        time_step = timedelta * asc_rate
    elif ele_change < 0:
        time_step = timedelta * desc_rate
    else:
        time_step = timedelta

    df.iat[i, -1] = df.iat[i - 1, -1] + time_step

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
