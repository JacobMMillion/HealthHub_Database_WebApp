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
from flask import Flask, request, render_template, g, redirect, Response, url_for

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DB_USER = "mc5672"
DB_PASSWORD = "mc5672p"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"

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


@app.route('/')
def index():

    query = """
          SELECT s.State_Name, SUM(dh.Count) AS Cases
          FROM Disease_Has dh
          JOIN States s ON dh.State_Name = s.State_Name
          JOIN Diseases d ON dh.Disease_ID = d.Disease_ID
          GROUP BY s.State_Name
          ORDER BY SUM(dh.Count) DESC
          LIMIT 1;
    """
    cursor = g.conn.execute(text(query))

    data = cursor.fetchall()
    cursor.close()

    
    return render_template('index.html', data=data)

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
            SELECT s.State_Name AS State, dh.Count AS State_Count
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


# 3. Healthcare facilities by state
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

# 4. Feed (Posts & Replies)
@app.route('/feed', methods=['GET', 'POST'])
def feed():
    error_message = None
    if request.method == 'POST':
        # Check if the request is for a new post or a reply
        if 'title' in request.form:  # Adding a new post
            title = request.form['title']
            content = request.form['content']
            user_name = request.form['user_name']

            # Check if the user exists
            user_check = g.conn.execute(text("SELECT 1 FROM Users WHERE User_Name = :user_name"), {"user_name": user_name}).fetchone()
            if not user_check:
                error_message = f"User '{user_name}' does not exist."
            else:
                query = """
                    INSERT INTO Posts (Title, Content, Num_Likes, Date, User_Name)
                    VALUES (:title, :content, 0, DATE_TRUNC('minute', CURRENT_TIMESTAMP), :user_name);
                """
                try:
                    g.conn.execute(text(query), {"title": title, "content": content, "user_name": user_name})
                    g.conn.commit()
                except Exception as e:
                    error_message = f"Error inserting post: {e}"

        elif 'post_id' in request.form:  # Adding a reply to a post
            post_id = request.form['post_id']
            reply_content = request.form['reply_content']
            reply_user_name = request.form['reply_user_name']

            # Check if the user exists
            user_check = g.conn.execute(text("SELECT 1 FROM Users WHERE User_Name = :user_name"), {"user_name": reply_user_name}).fetchone()
            if not user_check:
                error_message = f"User '{reply_user_name}' does not exist."
            else:
                query = """
                    INSERT INTO Comments (Content, Date, User_Name, Post_ID)
                    VALUES (:reply_content, DATE_TRUNC('minute', CURRENT_TIMESTAMP), :reply_user_name, :post_id);
                """
                g.conn.execute(text(query), {"reply_content": reply_content, "reply_user_name": reply_user_name, "post_id": post_id})
                g.conn.commit()

        # Redirect to the feed page to refresh content
        if not error_message:
            return redirect(url_for('feed'))

    # Fetch all posts with their user details
    post_query = """
        SELECT p.Post_ID, p.Title, p.Content, p.Num_Likes, p.Date, u.Name
        FROM Posts p
        JOIN Users u ON p.User_Name = u.User_Name
        ORDER BY p.Date DESC;
    """
    posts = g.conn.execute(text(post_query)).fetchall()

    # Fetch all replies associated with posts
    comment_query = """
        SELECT c.Post_ID, c.Content, c.Date, u.Name
        FROM Comments c
        JOIN Users u ON c.User_Name = u.User_Name
        ORDER BY c.Date ASC;
    """
    comments = g.conn.execute(text(comment_query)).fetchall()

    # Organize comments by post for easy access in the template
    comments_by_post = {}
    for comment in comments:
        post_id = comment[0]
        if post_id not in comments_by_post:
            comments_by_post[post_id] = []
        comments_by_post[post_id].append(comment)

    return render_template('feed.html', posts=posts, comments_by_post=comments_by_post, error_message=error_message)

@app.route('/disease_info', methods=['GET', 'POST'])
def disease_info():

    disease_id = request.args.get('disease_id')
    if request.method == 'POST':
        disease_id = request.form.get('disease_id')

    disease_id = int(disease_id) if disease_id else None

    # Fetch the disease details
    disease_details = prevention_strategies = symptoms = transmission_methods = None
    if disease_id:
        # Query for basic disease information
        disease_query = """
            SELECT Disease_ID, Name, Category
            FROM Diseases
            WHERE Disease_ID = :disease_id;
        """
        result = g.conn.execute(text(disease_query), {"disease_id": disease_id}).fetchone()
        disease_details = {
            "Disease_ID": result[0],
            "Name": result[1],
            "Category": result[2]
        } if result else None

        # Query for prevention strategies
        prevention_query = """
            SELECT Name, Description, Type
            FROM PreventionStratsPreventedBy
            WHERE Disease_ID = :disease_id;
        """
        prevention_strategies = g.conn.execute(text(prevention_query), {"disease_id": disease_id}).fetchall()

        # Query for symptoms
        symptoms_query = """
            SELECT Name, System, Description
            FROM SymptomsCauses
            WHERE Disease_ID = :disease_id;
        """
        symptoms = g.conn.execute(text(symptoms_query), {"disease_id": disease_id}).fetchall()

        # Query for transmission methods
        transmission_query = """
            SELECT Name, Mode
            FROM TransmissionMethodsTransmittedBy
            WHERE Disease_ID = :disease_id;
        """
        transmission_methods = g.conn.execute(text(transmission_query), {"disease_id": disease_id}).fetchall()

    # Query for all diseases to populate the dropdown
    diseases_query = "SELECT Disease_ID, Name FROM Diseases ORDER BY Name;"
    diseases = g.conn.execute(text(diseases_query)).fetchall()
    return render_template('disease_info.html', diseases=diseases, disease_details=disease_details,
                           prevention_strategies=prevention_strategies, symptoms=symptoms,
                           transmission_methods=transmission_methods, selected_disease_id=disease_id)

# 5. User favorites
@app.route('/favorites', methods=['GET', 'POST'])
def favorites():
  if request.method == 'POST':
    selected_user = request.form['user']
    query = """
            SELECT User_Name, State_Name
            FROM Favorites 
            WHERE User_Name = :user
            ORDER BY State_Name;
        """
    cursor = g.conn.execute(text(query), {"user": selected_user})
  else:
    selected_user = None
    query = """
            SELECT User_Name, State_Name
            FROM Favorites
            ORDER BY User_Name
        """
    cursor = g.conn.execute(text(query))

  data = cursor.fetchall()
  cursor.close()

  # Fetch all users for the dropdown menu
  users_cursor = g.conn.execute(text("SELECT User_Name FROM Users ORDER BY User_Name;"))
  users = [row[0] for row in users_cursor]
  users_cursor.close()

  return render_template('favorites.html', data=data, users=users, selected_user=selected_user)

# 5. User following
@app.route('/follows', methods=['GET', 'POST'])
def follows():
  if request.method == 'POST':
    selected_user = request.form['user']
    query = """
            SELECT User_Name, d.Name
            FROM Follows as f
            JOIN Diseases d
            ON d.Disease_ID = f.Disease_ID
            WHERE f.User_Name = :user
            ORDER BY d.Name;
        """
    cursor = g.conn.execute(text(query), {"user": selected_user})
  else:
    selected_user = None
    query = """
            SELECT User_Name, d.Name
            FROM Follows as f
            JOIN Diseases d
            ON d.Disease_ID = f.Disease_ID
            ORDER BY f.User_Name;
        """
    cursor = g.conn.execute(text(query))

  data = cursor.fetchall()
  cursor.close()

  # Fetch all users for the dropdown menu
  users_cursor = g.conn.execute(text("SELECT User_Name FROM Users ORDER BY User_Name;"))
  users = [row[0] for row in users_cursor]
  users_cursor.close()

  return render_template('follows.html', data=data, users=users, selected_user=selected_user)

# 6. User follow/unfollow
@app.route('/follow_unfollow', methods=['GET', 'POST'])
def follow_unfollow():
    error_message = None
    if request.method == 'POST':
        username = request.form.get('username')
        disease_id = request.form.get('disease_id')
        action = request.form.get('action')

        # Check if the user exists
        user_check = g.conn.execute(text("SELECT 1 FROM Users WHERE User_Name = :username"), {"username": username}).fetchone()
        if not user_check:
            error_message = f"User '{username}' does not exist."
        else:
            if action == 'follow' and disease_id:
                # Follow the disease
                follow_query = """
                    INSERT INTO Follows (User_Name, Disease_ID)
                    VALUES (:username, :disease_id)
                    ON CONFLICT DO NOTHING;
                """
                g.conn.execute(text(follow_query), {"username": username, "disease_id": disease_id})
                g.conn.commit()
            elif action == 'unfollow' and disease_id:
                # Unfollow the disease
                unfollow_query = """
                    DELETE FROM Follows
                    WHERE User_Name = :username AND Disease_ID = :disease_id;
                """
                g.conn.execute(text(unfollow_query), {"username": username, "disease_id": disease_id})
                g.conn.commit()

    # Query to get all diseases for the dropdown
    diseases_query = "SELECT Disease_ID, Name FROM Diseases ORDER BY Name;"
    diseases = g.conn.execute(text(diseases_query)).fetchall()
    return render_template('follow_unfollow.html', diseases=diseases, error_message=error_message)

# 7. User favorite/unfavorite
@app.route('/favorite_unfavorite', methods=['GET', 'POST'])
def favorite_unfavorite():
    error_message = None
    if request.method == 'POST':
        username = request.form.get('username')
        state_name = request.form.get('state_name')
        action = request.form.get('action')

        # Check if the user exists
        user_check = g.conn.execute(text("SELECT 1 FROM Users WHERE User_Name = :username"), {"username": username}).fetchone()
        if not user_check:
            error_message = f"User '{username}' does not exist."
        else:
            if action == 'favorite' and state_name:
                # Favorite the state
                favorite_query = """
                    INSERT INTO Favorites (User_Name, State_Name)
                    VALUES (:username, :state_name)
                    ON CONFLICT DO NOTHING;
                """
                g.conn.execute(text(favorite_query), {"username": username, "state_name": state_name})
                g.conn.commit()
            elif action == 'unfavorite' and state_name:
                # Unfavorite the state
                unfavorite_query = """
                    DELETE FROM Favorites
                    WHERE User_Name = :username AND State_Name = :state_name;
                """
                g.conn.execute(text(unfavorite_query), {"username": username, "state_name": state_name})
                g.conn.commit()

    # Query to get all states for the dropdown
    states_query = "SELECT State_Name FROM States ORDER BY State_Name;"
    states = g.conn.execute(text(states_query)).fetchall()

    return render_template('favorite_unfavorite.html', states=states, error_message=error_message)

# 8. Create New User
@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    error_message = None
    success_message = None

    if request.method == 'POST':
        # Retrieve form data
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        # Basic validation check
        if not username or not name or not email or not phone:
            error_message = "All fields are required."
        else:
            # Check if username already exists
            user_check = g.conn.execute(text("SELECT 1 FROM Users WHERE User_Name = :username"),
                                        {"username": username}).fetchone()

            if user_check:
                error_message = f"User '{username}' already exists."
            else:
                # Insert new user
                insert_query = """
                    INSERT INTO Users (User_Name, Name, Email, Phone)
                    VALUES (:username, :name, :email, :phone)
                """
                try:
                    g.conn.execute(text(insert_query),
                                   {"username": username, "name": name, "email": email, "phone": phone})
                    g.conn.commit()
                    success_message = f"User '{username}' created successfully."
                except Exception as e:
                    print("Error inserting new user:", e)
                    error_message = "An error occurred while creating the user."

    return render_template('create_user.html', error_message=error_message, success_message=success_message)

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
    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
