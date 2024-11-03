#!/usr/bin/env python3

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "mc5672"
DB_PASSWORD = "mc5672p"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)

try:
    with engine.connect() as conn:
        conn.execute(text("""DROP TABLE IF EXISTS test;"""))
        conn.execute(text("""CREATE TABLE IF NOT EXISTS test (
            id serial,
            name text
        );"""))
        conn.execute(text("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');"""))
        conn.commit()
    print("Created test table")
except Exception as e:
    print("Error creating test table:", e)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
    
  print("before_request entered, setting up connection to database")
    
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """

  print("teardown_request entered, ending connection to database")
    
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#

# Home route with links to the three views
@app.route('/')
def index():
    return render_template('index.html')

# 1. Disease counts by state
@app.route('/disease_counts_by_state', methods=['GET', 'POST'])
def disease_counts_by_state():
  if request.method == 'POST':
    selected_state = request.form['state']
    query = """
          SELECT s.State_Name, d.Name AS Disease, dh.Count
          FROM Disease_Has dh
          JOIN States s ON dh.State_Name = s.State_Name
          JOIN Diseases d ON dh.Disease_ID = d.Disease_ID
          WHERE s.State_Name = :state
          ORDER BY d.Name;
      """
    cursor = g.conn.execute(text(query), {"state": selected_state})
  else:
    selected_state = None
    query = """
          SELECT s.State_Name, d.Name AS Disease, dh.Count
          FROM Disease_Has dh
          JOIN States s ON dh.State_Name = s.State_Name
          JOIN Diseases d ON dh.Disease_ID = d.Disease_ID
          ORDER BY s.State_Name;
      """
    cursor = g.conn.execute(text(query))

  data = cursor.fetchall()
  cursor.close()

  # Fetch all states for the dropdown menu
  states_cursor = g.conn.execute(text("SELECT State_Name FROM States ORDER BY State_Name;"))
  states = [row[0] for row in states_cursor]
  states_cursor.close()

  return render_template('disease_counts_by_state.html', data=data, states=states, selected_state=selected_state)


# 2. State counts by disease
@app.route('/state_counts_by_disease', methods=['GET', 'POST'])
def state_counts_by_disease():
  if request.method == 'POST':
    selected_disease = request.form['disease']
    query = """
            SELECT s.State_Name, dh.Count
            FROM Disease_Has dh
            JOIN Diseases d ON dh.Disease_ID = d.Disease_ID
            JOIN States s ON dh.State_Name = s.State_Name
            WHERE d.Name = :disease
            ORDER BY s.State_Name;
        """
    cursor = g.conn.execute(text(query), {"disease": selected_disease})
  else:
    selected_disease = None
    query = """
            SELECT d.Name AS Disease, COUNT(dh.State_Name) AS State_Count
            FROM Disease_Has dh
            JOIN Diseases d ON dh.Disease_ID = d.Disease_ID
            GROUP BY d.Name
            ORDER BY State_Count DESC;
        """
    cursor = g.conn.execute(text(query))

  data = cursor.fetchall()
  cursor.close()

  # Fetch all diseases for the dropdown menu
  diseases_cursor = g.conn.execute(text("SELECT Name FROM Diseases ORDER BY Name;"))
  diseases = [row[0] for row in diseases_cursor]
  diseases_cursor.close()

  return render_template('state_counts_by_disease.html', data=data, diseases=diseases,
                         selected_disease=selected_disease)


# 3. Healthcare facilities by state with dropdown to filter by state
@app.route('/healthcare_facilities_by_state', methods=['GET', 'POST'])
def healthcare_facilities_by_state():
  if request.method == 'POST':
    selected_state = request.form['state']
    query = """
            SELECT s.State_Name, hf.Name AS Facility, hf.Address
            FROM HealthcareFacilities hf
            JOIN States s ON hf.State_Name = s.State_Name
            WHERE s.State_Name = :state
            ORDER BY hf.Name;
        """
    cursor = g.conn.execute(text(query), {"state": selected_state})
  else:
    selected_state = None
    query = """
            SELECT s.State_Name, hf.Name AS Facility, hf.Address
            FROM HealthcareFacilities hf
            JOIN States s ON hf.State_Name = s.State_Name
            ORDER BY s.State_Name;
        """
    cursor = g.conn.execute(text(query))

  data = cursor.fetchall()
  cursor.close()

  # Fetch all states for the dropdown menu
  states_cursor = g.conn.execute(text("SELECT State_Name FROM States ORDER BY State_Name;"))
  states = [row[0] for row in states_cursor]
  states_cursor.close()

  return render_template('healthcare_facilities_by_state.html', data=data, states=states, selected_state=selected_state)


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
