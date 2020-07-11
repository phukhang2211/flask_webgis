
import os


import geopy 
import pandas as pd #create table to easy work with db
import requests  #get data from api google and route OSM
import psycopg2 #connect db postgresql
from flask import (Flask, request, session, g, redirect, url_for, abort,
                   render_template, flash)

from shapely.geometry import Point #use to caculate distance 2 point
import bs4

app = Flask(__name__)

#connect postgresql
app.config.update(dict(
    HOST = 'ec2-3-211-48-92.compute-1.amazonaws.com',
    SECRET_KEY = 'development',
    USERNAME='bbgrqshytjocpy',
    PASSWORD='ffc33f8fbd44674b2be5c0980e87c0c5e2f763c02eb0fe479f08d412246f7e1f',
))

app.config.from_envvar('SETTING', silent=True)

def connect_db():
    rv = psycopg2.connect("dbname='d3sge2o4nt96mm'")
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

#Get data from user
@app.route("/")
def main():
    return render_template("index.html")


#display location user input to OSM map
location_input = 'a'
@app.route("/location", methods = ['POST', 'GET'])
def location():
    #get value user input
    if request.method == 'POST':
        address = request.form['address']
        #get google api token
        with open('API_google.txt','r') as f:
            api = f.read()
        #use google api show address user input
        url = 'https://maps.googleapis.com/maps/api/geocode/json?address='+address+'&key='+api
        resp = requests.get(url).json()
        temp = resp['results'][0]
        # save location_input to next function use
        global location_input
        # create dictionary and send to html for display location user input
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
    #get database
    db = get_db()
    cur = db.cursor()
    # get hospital from database
    cur.execute("SELECT * FROM data WHERE type='hospital';")
    rows = cur.fetchall()
    # add data to pandas and find location have min distance with user input
    df = pd.DataFrame(columns=['Index','Name',"Address","Long","Lat","Type"])
    for i in rows:
        df = df.append({'Index': i[0],'Name':i[1],'Address':i[2],'Long':i[3],'Lat':i[4],'Type':i[5]},ignore_index=True)
    min_distance = 100
    for index, row in df.iterrows():
        if min_distance >= Point(location_input['features'][0]['geometry']['coordinates'][1], location_input['features'][0]['geometry']['coordinates'][0]).distance(Point(row['Lat'],row['Long'])):
            min_distance = Point(location_input['features'][0]['geometry']['coordinates'][1], location_input['features'][0]['geometry']['coordinates'][0]).distance(Point(row['Lat'],row['Long']))
            row_min = row
    # add start and end to get direction from OSM API (format json)
    start = '{},{}'.format(location_input['features'][0]['geometry']['coordinates'][0], location_input['features'][0]['geometry']['coordinates'][1])
    end = '{},{}'.format(row_min[3], row_min[4])
    direction_coor = []
    url_direction = 'http://router.project-osrm.org/route/v1/trip/{};{}?steps=true'.format(start,end)
    direction = requests.get(url_direction).json()
    for step in direction['routes'][0]['legs'][0]['steps']:
        for location in step['intersections']:
            direction_coor.append(location['location'])
    # save route to geojson for display in html
    direction_line = {
        'type': 'LineString',
        'coordinates': direction_coor
    }  
    # save point hospital to geojson for display in html
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
    return render_template('route.html', location_input = location_input, point_end = point_end, direction_line = direction_line )


@app.route('/route_store')
def route_store():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM data WHERE type='store';")
    rows = cur.fetchall()
    df = pd.DataFrame(columns=['Index','Name',"Address","Long","Lat","Type"])
    for i in rows:
        df = df.append({'Index': i[0],'Name':i[1],'Address':i[2],'Long':i[3],'Lat':i[4],'Type':i[5]},ignore_index=True)
    min_distance = 100
    for index, row in df.iterrows():
        if min_distance >= Point(location_input['features'][0]['geometry']['coordinates'][1], location_input['features'][0]['geometry']['coordinates'][0]).distance(Point(row['Lat'],row['Long'])):
            min_distance = Point(location_input['features'][0]['geometry']['coordinates'][1], location_input['features'][0]['geometry']['coordinates'][0]).distance(Point(row['Lat'],row['Long']))
            row_min = row
    start = '{},{}'.format(location_input['features'][0]['geometry']['coordinates'][0], location_input['features'][0]['geometry']['coordinates'][1])
    end = '{},{}'.format(row_min[3], row_min[4])
    direction_coor = []
    url_direction = 'http://router.project-osrm.org/route/v1/trip/{};{}?steps=true'.format(start,end)
    direction = requests.get(url_direction).json()
    for step in direction['routes'][0]['legs'][0]['steps']:
        for location in step['intersections']:
            direction_coor.append(location['location'])

    direction_line = {
        'type': 'LineString',
        'coordinates': direction_coor
    }
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
    return render_template('route.html', location_input = location_input, point_end = point_end, direction_line = direction_line)

@app.route('/covid19')
def get_data():
    #get url covid
    url = 'https://ncov.moh.gov.vn'
    resp = requests.get(url, verify=False)
    tree = bs4.BeautifulSoup(markup=resp.text)
    table = tree.find_all(attrs={'id': 'sailorTable'})
    #convert data from text to list
    statistical_table = table[0].text.splitlines()
    data_static = []
    #remove some cases list = ''
    for item in statistical_table:
        if item != '':
            data_static.append(item)
    #create dataframe with columns
    df = pd.DataFrame(columns=[data_static[0],data_static[1],data_static[2],data_static[3],data_static[4]])
    #add data to dataframe
    for i in range(len(data_static)):
        if i % 5 == 0:
            df = df.append({'Tỉnh, Thành phố':data_static[i], 'Số ca nhiễm': data_static[i + 1], 'Đang điều trị':data_static[i + 2], 'Khỏi':data_static[i + 3], 'Tử vong': data_static[i + 4] }, ignore_index=True)
    df= df.iloc[1:]
    #convert to dict and render html
    data_covid = df.to_dict()
    return render_template('covid.html', data_covid = data_covid)


if __name__ == "__main__":
    app.run(debug=True)
