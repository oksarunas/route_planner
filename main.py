import json
import requests
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")

# Connect to database
conn = sqlite3.connect("trucking.db")
cursor = conn.cursor()

headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
}

# Get coordinates for specific location

def coordinates(location):
    call = requests.get(f'https://api.openrouteservice.org/geocode/search?api_key={api_key}&text={location}', headers=headers)
    info = json.loads(call.text)
    return info['features'][0]['geometry']['coordinates']

# Get distance between locations

def directions(start, end):
    call = requests.get(f'https://api.openrouteservice.org/v2/directions/driving-car?api_key={api_key}&start={start[0]},{start[1]}&end={end[0]},{end[1]}', headers=headers)
    info = json.loads(call.text)
    return info['features'][0]['properties']['summary']['distance']



# Add distances between locations to database

def distances(locations):

    for start in locations:
        for end in locations:
            if start[0] != end[0]:
                distance = directions([start[1], start[2]], [end[1], end[2]])
                #a[str(start[0]) + '-' + str(end[0])] =  distance
                cursor.execute("INSERT INTO distances (start, end, distance) VALUES (?, ?, ?)", (start[0], end[0], distance / 100))
    conn.commit()            
    return 0           
 
                
cursor.execute("SELECT name, longitude, latitude FROM destinations")
locations = cursor.fetchall()
distances(locations)