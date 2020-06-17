
import geopy
import pandas as pd
import requests
import psycopg2
from flask import (Flask, request, session, g, redirect, url_for, abort,
                   render_template, flash)
import os
from shapely.geometry import Point
import json

app = Flask(__name__)
app.config.from_object(__name__)


app.config.update(dict(
    DATABASE = os.path.join(app.root_path),
    SECRET_KEY = 'development',
    USERNAME='kane',
    PASSWORD='q',
))

app.config.from_envvar('BLOG_SETTING', silent=True)

def connect_db():
    rv = psycopg2.connect("dbname='gis'")
    return rv

def get_db():
    if not hasattr(g, 'postgresql_db'):
        g.postgresql_db = connect_db()
    return g.postgresql_db
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'postgresql_db'):
        g.postgresql_db.close()


def init_db():
    db = get_db()
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')

@app.route("/")
def main():
    return render_template("index.html")



location_input = 'a'
@app.route("/location", methods = ['POST', 'GET'])
def location():
    if request.method == 'POST':
        address = request.form['address']
        with open('API_google.txt','r') as f:
            api = f.read()
        url = 'https://maps.googleapis.com/maps/api/geocode/json?address='+address+'&key='+api
        resp = requests.get(url).json()
        temp = resp['results'][0]
        global location_input
        location_input = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        temp['geometry']['location']['lng'],
                        temp['geometry']['location']['lat']
                    ]
                },
                "properties": {
                    "name": "Your Location Input",
                    "Address": temp['formatted_address']
                }
            }]}
        return render_template("location.html", location_input = location_input)

@app.route('/route_hospital')
def route_hospital():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM data WHERE type='hospital'")
    rows = cur.fetchall()
    df = pd.DataFrame(columns=['Index','Name',"Address","Long","Lat","Type"])
    for i in rows:
        df = df.append({'Index': i[0],'Name':i[1],'Address':i[2],'Long':i[3],'Lat':i[4],'Type':i[5]},ignore_index=True)
    min_distance = 100
    for index, row in df.iterrows():
        if min_distance >= Point(location_input['features'][0]['geometry']['coordinates'][1], location_input['features'][0]['geometry']['coordinates'][0]).distance(Point(row['Lat'],row['Long'])):
            min_distance = Point(location_input['features'][0]['geometry']['coordinates'][1], location_input['features'][0]['geometry']['coordinates'][0]).distance(Point(row['Lat'],row['Long']))
            row_min = row
    start = '{},{}'.format(location_input['features'][0]['geometry']['coordinates'][1], location_input['features'][0]['geometry']['coordinates'][0])
    end = '{},{}'.format(row_min[4], row_min[3])
    with open('API_google.txt','r') as f:
        api = f.read()
    direction_coor = []
    url_direction = 'https://maps.googleapis.com/maps/api/directions/json?origin='+start+'&destination='+end+'&key='+api
    
    direction = requests.get(url_direction).json()
    
    direction_coor.append([direction['routes'][0]['legs'][0]['start_location']['lng'],direction['routes'][0]['legs'][0]['start_location']['lat']])
    
    for step in range(len(direction['routes'][0]['legs'][0]['steps'])):
        direction_coor.append([direction['routes'][0]['legs'][0]['steps'][step]['end_location']['lng'],direction['routes'][0]['legs'][0]['steps'][step]['end_location']['lat']])
    
    direction_line = {
        'type': 'LineString',
        'coordinates': direction_coor
    }
    with open("static/js/data.js", "w") as f:
        f.write('var myLines = {}'.format(json.dumps(direction_line,indent =4)))   
    print(direction_line)
    point_end = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    row_min[3],
                    row_min[4]
                ]
            },
            "properties": {
                "name": row_min[1],
                "Address": row_min[2]
            }
        }]}
    return render_template('route_hospital.html', location_input = location_input, point_end = point_end )



@app.route('/route_store')
def route_store():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM data WHERE type='store'")
    rows = cur.fetchall()
    df = pd.DataFrame(columns=['Index','Name',"Address","Long","Lat","Type"])
    for i in rows:
        df = df.append({'Index': i[0],'Name':i[1],'Address':i[2],'Long':i[3],'Lat':i[4],'Type':i[5]},ignore_index=True)
    min_distance = 100
    for index, row in df.iterrows():
        if min_distance >= Point(location_input['features'][0]['geometry']['coordinates'][1], location_input['features'][0]['geometry']['coordinates'][0]).distance(Point(row['Lat'],row['Long'])):
            min_distance = Point(location_input['features'][0]['geometry']['coordinates'][1], location_input['features'][0]['geometry']['coordinates'][0]).distance(Point(row['Lat'],row['Long']))
            row_min = row
    start = '{},{}'.format(location_input['features'][0]['geometry']['coordinates'][1], location_input['features'][0]['geometry']['coordinates'][0])
    end = '{},{}'.format(row_min[4], row_min[3])
    with open('API_google.txt','r') as f:
        api = f.read()
    direction_coor = []
    url_direction = 'https://maps.googleapis.com/maps/api/directions/json?origin='+start+'&destination='+end+'&key='+api
    
    direction = requests.get(url_direction).json()
    
    direction_coor.append([direction['routes'][0]['legs'][0]['start_location']['lng'],direction['routes'][0]['legs'][0]['start_location']['lat']])
    
    for step in range(len(direction['routes'][0]['legs'][0]['steps'])):
        direction_coor.append([direction['routes'][0]['legs'][0]['steps'][step]['end_location']['lng'],direction['routes'][0]['legs'][0]['steps'][step]['end_location']['lat']])
    
    direction_line = {
        'type': 'LineString',
        'coordinates': direction_coor
    }
    with open("static/js/data.js", "w") as f:
        f.write('var myLines = {}'.format(json.dumps(direction_line,indent =4)))   
    print(direction_line)
    point_end = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    row_min[3],
                    row_min[4]
                ]
            },
            "properties": {
                "name": row_min[1],
                "Address": row_min[2]
            }
        }]}
    return render_template('route_hospital.html', location_input = location_input, point_end = point_end )



if __name__ == "__main__":
    app.run(debug=True)
