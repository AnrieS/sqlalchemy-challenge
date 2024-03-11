# Import the dependencies.
from flask import Flask, jsonify
import datetime as dt
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
# from models import database_setup, query_precipitation_data
import pandas as pd
import matplotlib.pyplot as plt


#################################################
# Database Setup
#################################################
def database_setup(database_path):
    engine = create_engine(f"sqlite:///{database_path}")
    Base = automap_base()
    Base.prepare(engine, reflect=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session, Base.classes.station, Base.classes.measurement

from datetime import datetime, timedelta

def query_precipitation_data(session, Measurement):
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    query_date = datetime.strptime(most_recent_date, '%Y-%m-%d') - timedelta(days=365)
    query_date_str = query_date.strftime('%Y-%m-%d')

    results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date > query_date_str).order_by(Measurement.date).all()

    df = pd.DataFrame(results, columns=['date', 'prcp'])
    df.set_index('date', inplace=True)

    # Drop duplicate index values, if any
    df = df[~df.index.duplicated(keep='first')]

    return df



# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# Declare a Base using `automap_base()`
Base = automap_base()
# Use the Base class to reflect the database tables
Base.prepare(engine, reflect=True)

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session
session = Session(bind=engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_date/end_date"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session, _, Measurement = database_setup('Resources/hawaii.sqlite')
    df = query_precipitation_data(session, Measurement)
    session.close()
    prcp_dict = df.to_dict(orient='index')
    return jsonify(prcp_dict)



@app.route("/api/v1.0/stations")
def stations():
    session, _, Measurement = database_setup('Resources/hawaii.sqlite')
    some_station = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
    df = pd.DataFrame(some_station, columns=['station', 'count'])
    session.close()
    station_dict = df.to_dict(orient='index')
    return jsonify(station_dict)


@app.route("/api/v1.0/tobs")
def tobs():
    session, _, Measurement = database_setup('Resources/hawaii.sqlite')
    most_active_station = session.query(Measurement.station).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()[0]
    
    most_recent_date = session.query(func.max(Measurement.date)).filter(Measurement.station == most_active_station).scalar()
    query_date = datetime.strptime(most_recent_date, '%Y-%m-%d') - timedelta(days=365)
    query_date_str = query_date.strftime('%Y-%m-%d')
    
    results = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_station).filter(Measurement.date > query_date_str).order_by(Measurement.date).all()
    
    session.close()
    
    tobs_list = [{'date': row[0], 'tobs': row[1]} for row in results]

    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
def temp_start(start):
    session, _, Measurement = database_setup('Resources/hawaii.sqlite')

    # Query for minimum, average, and maximum temperatures for dates greater than or equal to the start date
    temp_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).filter(Measurement.date >= start).all()

    session.close()

    # Convert the results into a dictionary
    temp_dict = {"TMIN": temp_data[0][0], "TAVG": temp_data[0][1], "TMAX": temp_data[0][2]}

    return jsonify(temp_dict)

@app.route("/api/v1.0/<start>/<end>")
def temp_start_end(start, end):
    session, _, Measurement = database_setup('Resources/hawaii.sqlite')
    
    # Query for minimum, average, and maximum temperatures for dates between the start and end dates, inclusive
    temp_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).filter(Measurement.date >= start).filter(Measurement.date <= end).all()

    session.close()

    # Convert the results into a dictionary
    temp_dict = {"TMIN": temp_data[0][0], "TAVG": temp_data[0][1], "TMAX": temp_data[0][2]}

    return jsonify(temp_dict)


if __name__ == '__main__':
    app.run(debug=True)



