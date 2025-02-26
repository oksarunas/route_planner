import json
import requests
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")

# Check for API key
if not api_key:
    raise ValueError("API_KEY not found. Please set it in the .env file.")

# Connect to database
conn = sqlite3.connect("trucking.db")
cursor = conn.cursor()

headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
}


# Get coordinates for specific location
def coordinates(location):
    url = f'https://api.openrouteservice.org/geocode/search'
    
    try:
        response = requests.get(url, params={'api_key': api_key, 'text': location}, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        info = response.json()  # Directly parse JSON
        
        # Check if 'features' exists and is not empty
        if 'features' in info and info['features']:
            return info['features'][0]['geometry']['coordinates']
        else:
            print(f"No results found for location: {location}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None  
        
# Get distance between locations

def directions(start, end):
    call = requests.get(f'https://api.openrouteservice.org/v2/directions/driving-car?api_key={api_key}&start={start[0]},{start[1]}&end={end[0]},{end[1]}', headers=headers)
    info = json.loads(call.text)
    return info['features'][0]['properties']['summary']['distance']


# Add missing distances between locations to database

def distances():
    cursor.execute('SELECT name, longitude, latitude FROM destinations')
    locations = cursor.fetchall()

    for start in locations:
        for end in locations:
            if start[0] != end[0]:  # Avoid same start and end locations
                
                # Check if the distance already exists
                cursor.execute("SELECT 1 FROM distances WHERE start = ? AND end = ?", (start[0], end[0]))
                existing_distance = cursor.fetchone()
                
                if not existing_distance:  # If no record exists, calculate and insert
                    distance = directions([start[1], start[2]], [end[1], end[2]])
                    cursor.execute("INSERT INTO distances (start, end, distance) VALUES (?, ?, ?)", 
                                   (start[0], end[0], distance / 1000))
                    conn.commit()
                    
    return 0  
        

def update():
    location = input("Enter a location: ").strip()
    
    # Check if location exists in the database
    cursor.execute("SELECT name FROM destinations WHERE name = ?", (location,))
    existing_location = cursor.fetchone()
    
    if not existing_location:
        new_coordinates = coordinates(location)
        
        # Ensure valid coordinates before inserting
        if new_coordinates:
            cursor.execute("INSERT INTO destinations (name, longitude, latitude) VALUES (?, ?, ?)", 
                           (location, new_coordinates[0], new_coordinates[1]))
            conn.commit()
            print(f"{location} added to the database with coordinates: {new_coordinates}")
        else:
            print(f"Failed to get coordinates for {location}.")
    else:
        print(f"{location} is already in the database.")



def calculate(location_list):
    distance = 0
    route = ['Kaunas']  # Track the full path explicitly
    remaining = location_list.copy()  # Work with a copy to preserve input
    current = 'Kaunas'

    # Visit all points
    while remaining:
        distances = []
        for next_stop in remaining:
            if next_stop != current:
                cursor.execute("SELECT start, end, distance FROM distances WHERE start = ? AND end = ?", (current, next_stop))
                result = cursor.fetchone()
                if result:  # Check if query returned something
                    distances.append(result)
        
        if not distances:  # No valid next stops
            print("No distances found—check database!")
            return None, None
        
        # Pick the closest
        min_distance = min(distances, key=lambda x: x[2])
        distance += float(min_distance[2])
        current = min_distance[1]  # Move to the next stop
        route.append(current)
        remaining.remove(current)  # Drop it from unvisited list
        print(f"Step: {current}, Total so far: {distance}")

    # Return to Kaunas
    cursor.execute("SELECT distance FROM distances WHERE start = ? AND end = ?", (current, 'Kaunas'))
    last = cursor.fetchone()
    if last:
        distance += float(last[0])
        route.append('Kaunas')
        print(f"Back to Kaunas, Final distance: {distance}")
    else:
        print("No route back to Kaunas—check data!")

    return route, distance

# Test it
#location_list = ['Josvainiai', 'Kunioniai', "Dotnuva", "Paparciai"]
#route, total = calculate(location_list)
#print(f"Full route: {route}, Total distance: {total}")

distances()
