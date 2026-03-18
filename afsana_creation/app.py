from flask import Flask, render_template, request, jsonify, session, redirect,url_for, request, json

# --- MongoDB driver setup for aptiFlow apps---
from pymongo import MongoClient

# for aptiFlow apps - connection to MongoDB Atlas & create db object to send data to MongoDB from flask app. 
# Note: This is currently only used for aptiFlow apps, not the calendar or task flows which use PostgreSQL Neon DB.
#  We can unify later if needed.

client = MongoClient("mongodb+srv://afsana:123@cluster0.smfjexk.mongodb.net/aptiFlow_db")
db = client['aptiFlow_db']
users_collection = db['users']


# add flask sql postgresql driver to get neon database connection
import psycopg2
#Import smtplib to connect with gmail SMTP(Simple Mail Transfer Protocol)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
# Needed for sessions (storing logged-in user name)
app.secret_key = "change-this-key-later"

# load once at startup
with open('static/ai_Data.json') as f:
    aiData = json.load(f)

# =========================================================================
# CRITICAL: GMAIL CREDENTIALS
# The GMAIL_APP_PASSWORD MUST be a generated App Password if you have 2FA enabled.
# Using your regular account password will fail. Check Google Account security settings.
# =========================================================================
app.config['GMAIL_USER'] = "asefau13@gmail.com"
app.config['GMAIL_APP_PASSWORD'] = "Asef123!" # <-- **CRITICAL: Ensure this is a Google App Password**
app.config['DATABASE_URL'] = "postgresql://neondb_owner:npg_A7Dqxr0fVKcM@ep-sparkling-haze-adok795f-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"


@app.route('/')
def index():
    return render_template('index.html')



@app.route('/calendar')
def calendar():
    return render_template('CALENDER.html')


@app.route('/design')
def design():
    return render_template('design.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')


@app.route('/extended')
def extended():
    return render_template('extended.html')

@app.route('/footer')
def footer():
    return render_template('footer.html')

#Testing & working with gallery for script extension on new_gallery.html. 
@app.route('/new_gallery')
def new_gallery():
    return render_template('new_gallery.html')



# @app.route('/ai_data')
# def ai_data():
#     key = request.args.get('key')
#     if not key:
#         return jsonify(aiData)

#     # support nested keys like product.pricing
#     data = aiData
#     for part in key.split('.'):
#         if isinstance(data, dict):
#             data = data.get(part)
#         else:
#             data = None

#     return jsonify(data or {})

@app.route('/ai_data')
def ai_data():
    import os, json

    path = os.path.join(app.root_path, 'static', 'ai_Data.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # always send first usable object
    if isinstance(data, list):
        item = data[0]
    else:
        item = data

    # FIX image path for browser
    if 'images' in item:
        item['images'] = [('/' + p.lstrip('/')) for p in item['images']]
    if 'image' in item:
        item['image'] = '/' + item['image'].lstrip('/')

    return jsonify(item)




# Gallery GLB text route (JS calls /glb-text?i=0)
@app.route('/glb-text')
def glb_text():
    i = request.args.get('i', default=0, type=int)
    try:
        import json, os
        path = os.path.join(app.root_path, 'static', 'data.json')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data[i] if 0 <= i < len(data) else ''
    except Exception:
        return ''


@app.route('/craftFlow')
def craftFlow():
    return render_template('CraftFlow.html')

#Rest API flow apps for signin route to get data from request object. 
# signin route
@app.route('/signin', methods=['POST'])
def signin():
    data = request.form
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # save user to database & prevent duplicates (basic check) and return on the register section and tell 
    # use different credetial to register
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        return render_template('CraftFlow.html', msg="Username already exists...", show_register=True)
    users_collection.insert_one({
        "username": username,
        "email": email,
        "password": password
    })
    # after successful save
    return render_template('CraftFlow.html', msg="Your Credentials Have Been Saved. Pls login to continue.")


# CraftFlow login route 
@app.route('/craft-login', methods=['POST'])
def craft_login():
    data = request.form
    username = data.get('username')
    password = data.get('password')

    # check credentials in database
    user = users_collection.find_one({"username": username, "password": password})
    if user:
        is_admin = user.get("role") == "admin"
        users = list(users_collection.find({}, {"_id":0,"username":1,"email":1,"role":1})) if is_admin else []
        return render_template('CraftFlow.html', msg="Login successful!", username=username, is_admin=is_admin, users=users)
    else:
        return render_template('CraftFlow.html', msg="Invalid credentials. Please try again.", is_admin=False, users=[])

@app.route('/dashboard')
def dashboard():
    username = request.args.get('username')
    user = users_collection.find_one({"username": username})
    is_admin = user.get("role") == "admin"
    users = list(users_collection.find({}, {"_id":0,"username":1,"email":1,"role":1})) if is_admin else []
    return render_template('CraftFlow.html', username=username, is_admin=is_admin, users=users)



# ArcGIS explore object & how to use esri maps in our apps and manage routes for that.
@app.route('/aptiCraft_ArcGIS')
def aptiCraft_ArcGIS():
    return render_template('aptiCraft_ArcGIS.html')



@app.route('/health2')
def health2():
    return render_template('health2.html')


# Valentine’s Day route
@app.route('/valentine')
def valentine():
    return render_template('valentine.html')



# Login and register routes with Neon DB save, then redirect after success
@app.route('/register', methods=['GET','POST'])
def register():
    # If user submits the form
    if request.method == 'POST':
        # Grab data from form
        username = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Store in DB
        conn = psycopg2.connect(app.config['DATABASE_URL'], connect_timeout=5)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (username, email, password))
        conn.commit()
        
        # Verify save worked
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        # Redirect to login page
        return redirect(url_for('login'))

    # If GET — just show the page
    return render_template('calendar_login.html')


# Login route with DB verification and user session store
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        conn = psycopg2.connect(app.config['DATABASE_URL'])
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE name=%s AND password=%s", (name, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['name'] = user[0]  # Save logged-in username
            return redirect('/2026_calendar')
        else:
            return "Invalid credentials"  # Later show UI message

    return render_template('calendar_login.html', show_login=True)


# Logout route to clear session
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("calendar2026"))


# Check Auth Route
@app.route('/check-auth')
def check_auth():
    if 'name' in session:
        return {'logged_in': True}
    return {'logged_in': False}


# Add Task Route
@app.route('/add-task', methods=['POST'])
def add_task():
    data = request.get_json()
    db = psycopg2.connect(app.config['DATABASE_URL'])
    cur = db.cursor()
    # Note: We assume the 'schedules' table is ready to store the task details
    cur.execute("INSERT INTO schedules (user_name, schedule_date, schedule_time, title, details) VALUES (%s, %s, %s, %s, %s)",
                (session.get('name'), data['dateKey'], data['time'], data['title'], data.get('details')))
    db.commit()
    cur.close()
    db.close()
    return jsonify({'saved': True})


# Gmail send function
def send_email(to_email, subject, body):
    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = app.config['GMAIL_USER']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        # Authentication step
        server.login(app.config['GMAIL_USER'], app.config['GMAIL_APP_PASSWORD'])
        
        # Send the email
        text = msg.as_string()
        server.sendmail(app.config['GMAIL_USER'], to_email, text)
        server.quit()
        print(f"Successfully sent email to {to_email} for subject: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("SMTP AUTHENTICATION ERROR: Check GMAIL_APP_PASSWORD and GMAIL_USER configuration.")
        return False
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False

# Check Reminders Route (GitHub Action will call this every 1 min)
@app.route('/check-reminders')
def check_reminders():
    # Connect to Neon
    db = psycopg2.connect(app.config['DATABASE_URL'])
    cur = db.cursor()

    # --- FIX: Check for tasks that are due *in the next 1 to 30 minutes*
    # This uses a range to reliably catch reminders, instead of exact minute matches.
    cur.execute("""
        SELECT user_name, schedule_date, schedule_time, title
        FROM schedules
        WHERE (schedule_date = CURRENT_DATE)
        AND (
            -- Task time must be after NOW + 1 minute (to prevent immediate repeats)
            schedule_time > (NOW() + INTERVAL '1 minute')::time 
            AND 
            -- Task time must be before NOW + 31 minutes
            schedule_time <= (NOW() + INTERVAL '31 minutes')::time
        )
    """)
    rows = cur.fetchall()

    reminders_sent = 0

    # If found -> send Gmail reminder
    for r in rows:
        user_name, d, t, title = r
        
        # --- Retrieve the user's email address using their user_name ---
        try:
            # Query the users table for the recipient's email
            cur.execute("SELECT email FROM users WHERE name = %s", (user_name,))
            email_row = cur.fetchone()

            if email_row:
                recipient_email = email_row[0]
                
                # Format the time for the subject and body
                time_display = t.strftime('%I:%M %p')
                date_display = d.strftime('%Y-%m-%d')
                
                subject = f"AptiCraft Reminder: {title} at {time_display}"
                body = (
                    f"Hi {user_name},\n\n"
                    f"This is a reminder from your AptiCraft Planner.\n\n"
                    f"Your task: '{title}'\n"
                    f"Is scheduled for: {time_display} on {date_display}.\n\n"
                    f"Plan your day accordingly!"
                )
                
                # Send to the actual recipient email
                if send_email(recipient_email, subject, body):
                    reminders_sent += 1
            else:
                print(f"ERROR: Could not find email for user: {user_name}")

        except Exception as e:
            print(f"Failed to process and send email for user {user_name}: {e}")
        # --- END FIX ---


    cur.close()
    db.close()
    return jsonify({'checked': True, 'reminders': reminders_sent})


# Task lists edit & delete routes would go here

# --- Edit schedule (by id) ---
@app.route('/schedule/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    data = request.get_json()
    db = psycopg2.connect(app.config['DATABASE_URL'])
    cur = db.cursor()
    cur.execute("UPDATE schedules SET title=%s WHERE id=%s", (data.get('title'), schedule_id))
    db.commit()
    cur.close()
    db.close()
    return jsonify({'ok': True}), 200


@app.route('/schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    db = psycopg2.connect(app.config['DATABASE_URL'])
    cur = db.cursor()
    cur.execute("DELETE FROM schedules WHERE id=%s", (schedule_id,))
    db.commit()
    cur.close()
    db.close()
    return jsonify({'ok': True}), 200



if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)
