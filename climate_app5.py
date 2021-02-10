#flask API for climate data
#a few useful libraries
from flask import Flask, jsonify
import pandas as pd
import datetime as dt
import numpy as np
# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

#This first part of my app is the part where I extract data from the sql database and transform it into dicts to supply through the api
#create my engine
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model

Base = automap_base()

#this line reflects the database so that we can examine it
Base.prepare(engine, reflect=True)

# I am going to assign classes 'measurement' and 'station' to variables
# a database table is always associated with a class in python, which dictates what
#column values are expected. These columns are the attributes of a class
measur = Base.classes.measurement

stat = Base.classes.station

#create a session so that I can connect with the database and retreive data
sesh = Session(engine)

# Design a query to retrieve the last 12 months of precipitation data and plot the results
# Last date in file found to be 8/23/17 by inspecting .csv

#set a reference date 12mos before the last date in the set
ref_date = dt.datetime(2016, 8, 23)

#a list of columns to select
sel = [measur.prcp, measur.station, measur.id, measur.tobs, measur.date]

#write a query with a filter that specifies the date be later than the reference date
yr_precip = sesh.query(*sel).filter( measur.date > ref_date).all()

#set up lists for the 4 most interesting quantities in the list above
precip = []
date = []
stid = []
temps = []

#this loop is to sort the quantities into the list
#it also contains a conditional to clean the precipitation data of values that say "none"
#its somewhat ambiguous, but I understand that value to mean "no precipitation", and not "null", so I'm replacing it with 0.0


for y in yr_precip:
    date.append(y[4])
    temps.append(y[3])
    stid.append(y[1])
    if type(y[0]) == float: 
        precip.append(y[0])
    else:
        precip.append(0.0)

        
#writing a dataframe for this data
y_prec = {"Date":date, "Precipitation":precip, "Temperature":temps, "Station_id":stid}
y_prec_df = pd.DataFrame(data = y_prec, index= date)

#sort the dataframe
y_prec_df = y_prec_df.sort_values(by=['Date'])

#do the same stuff for the other table. 
#this is a small tale that doesn't need much cleaning so the procedure is simpler. 
stat_dat = pd.read_sql("Select * FROM station", engine)

stat_dat = stat_dat.rename(columns = {"station":"Station_id"})

#I'm joining these dataframes using a left join so that I can group by station or station id later
#****yr_combi_df contains date, precipitation and temperature data, as well as info about the stations the data was collected from****

yr_combi_df = pd.merge(y_prec_df, stat_dat, on='Station_id', how="left")

#write a query to order the stations by activity

#use a query to count instances of a station showing up, group by stations and order by count descending
act_stats = pd.read_sql('SELECT station, COUNT(station) AS measurement_ct FROM measurement GROUP BY station ORDER BY COUNT(station) DESC'
                        , engine)

#I'm renaming so that I can merge in data on what the stations are
act_stats = act_stats.rename(columns={'station':'Station_id'})

#merging the data. the sort gets lost because I put the station table first for aesthetic reasons
act_stats_ex = pd.merge(stat_dat, act_stats, on='Station_id')

#dropping id column
act_stats_ex = act_stats_ex.drop(columns = ['id'])

#index on station id
act_stats_ex = act_stats_ex.set_index(['Station_id'])

#****resorting  - result: act_stats_ex is an ordered list of stations by activity, with data about the stations****
act_stats_ex = act_stats_ex.sort_values(by='measurement_ct', ascending=False)

#****DF for last 12 mos of temperature data ****
y_temp_df = y_prec_df[['Temperature', 'Station_id']].copy()

#In this section I am going to make all the important dataframes for the api into dictionaries

#TEMPERATURE DATA DICT
y_temp_di = y_temp_df.to_dict()

#DICT WITH STATION DATA AND ACTIVITY STATS
act_stats_di = act_stats_ex.to_dict()

#DICT FOR PRECIPITATION DATA
pre_df = yr_combi_df[['Date', 'Precipitation', 'Station_id']].copy()

pre_df = pre_df.set_index(['Date'])

pre_di = pre_df.to_dict()

#Begin Flask API

app = Flask(__name__)

@app.route("/")
def home():
    return( f'''Welcome to Oahu Climate API.  

     Routes to available data follow.

     Route: /api/v1.0/precipitation  - precipitation data.

     Route: /api/v1.0/stations - data on weather stations. 

     Route /api/v1.0/tobs - temperature observations for the previous year. 

     Route: /api/v1.0/DD_MM_YYYY - Minimum, Maximum and Average temp after a starting date.

     Route: api/v1.0/DD_MM_YYYY/DD_MM_YYYY - Minimum, Maximum and Average temp in a date range.

     Note: for the temperature stats for a date range, enter the earlier date first.

     Our data ranges from 01_01_2010 to 23_08_2017 (DD_MM_YYYY)''')

@app.route("/api/v1.0/precipitation")
def precipitation():
    return jsonify(pre_di)

@app.route("/api/v1.0/stations")
def stations():
    return jsonify(act_stats_di)

@app.route("/api/v1.0/tobs")
def tobs():
    return jsonify(y_temp_di)
#https://stackoverflow.com/questions/35188540/get-a-variable-from-the-url-in-a-flask-route
#this reference is helpful for figuring out how to extract variables from a url in flask

@app.route('/api/v1.0/<d1>_<m1>_<y1>')
def stdt_temp(d1, m1, y1):
    st_date = dt.datetime(int(y1), int(m1), int(d1))
    #in order for this to work, sql objects have to be "in the same thread"
    #so I am going to use some code from above
    engine = create_engine("sqlite:///hawaii.sqlite")
    Base = automap_base()
    Base.prepare(engine, reflect=True)
    measur = Base.classes.measurement
    sesh = Session(engine)
    #List for the last two queries in the API
    stdt_stats = [func.avg(measur.tobs), func.min(measur.tobs), func.max(measur.tobs)] 
    #query is below   
    dt_tobs = sesh.query(*stdt_stats).filter( measur.date > st_date).all()
    stdt_di = {'Average Temp':dt_tobs[0][0], 'Min Temp':dt_tobs[0][1], 'Max Temp': dt_tobs[0][2]}
    return jsonify(stdt_di)

            

@app.route('/api/v1.0/<d2>_<m2>_<y2>/<d3>_<m3>_<y3>')
def stdt_temp2(d2, m2, y2, d3, m3, y3):
    st_dt2 = dt.datetime(int(y2), int(m2), int(d2))
    st_dt3 = dt.datetime(int(y3), int(m3), int(d3))
    #in order for this to work, sql objects have to be "in the same thread"
    #so I am going to use some code from above
    engine = create_engine("sqlite:///hawaii.sqlite")
    Base = automap_base()
    Base.prepare(engine, reflect=True)
    measur = Base.classes.measurement
    sesh = Session(engine)
    #List for the last two queries in the API
    stdt_stats = [func.avg(measur.tobs), func.min(measur.tobs), func.max(measur.tobs)]
    #query is below
    dt_tobs2 = sesh.query(*stdt_stats).filter(measur.date > st_dt2, measur.date < st_dt3).all()
    stdt_di2 = {'Average Temp':dt_tobs2[0][0], 'Min Temp':dt_tobs2[0][1], 'Max Temp': dt_tobs2[0][2]}
    return jsonify(stdt_di2)    
    
             

#this line is important for making the app run
if __name__ == '__main__':
    app.run(debug = True)