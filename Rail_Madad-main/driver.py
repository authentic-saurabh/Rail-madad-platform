from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import pymongo
import uuid
import json
from pymongo import MongoClient
import prompts
import os
from PIL import Image
#from IPython.display import Image
#from IPython.core.display import HTML
import google.generativeai as genai

app = Flask(__name__)
uri = "mongodb+srv://deepanshumehlawat2003:m7E9EiYSSDHhI3z9@sih.0oetq.mongodb.net/?retryWrites=true&w=majority&appName=sih"
bcrypt = Bcrypt(app)
load_dotenv()
api_key = os.getenv('API_KEY')
genai.configure(api_key=api_key)
app.secret_key = os.urandom(24) 

# Create a new client and connect to the server
client = MongoClient(uri)
db = client['SIH']
users_collection = db['Users']
complaints_collection = db['Complaints']

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/sih')
    return redirect('/login')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({'email': email})

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])  # Storing user_id in session
            session['username'] = user['username']
            if user.get('type') == 1:
                return redirect('/admin_login')  # Redirect to admin login page
            else:
                return redirect('/sih')  # Redirect to 'sih' page
        else:
            return render_template('login.html', message='Username or password incorrect')
    return render_template('login.html', message='Login to Continue')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Clear session data
    session.pop('username', None)
    return redirect('/login')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if users_collection.find_one({'email': email}):
            return render_template('register.html', message='Account already exists. Login to continue.')
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({'username': username, 'email': email, 'password': hashed_password, 'type':0})
        return render_template('login.html', message='Account created! Login to continue')
    
    return render_template('register.html', message='Please register')

# SIH route (Protected)
@app.route('/sih')
def sih():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('sih.html', username=session.get('username'))

@app.route('/cat_img', methods=['POST'])
def cat_img():
    if 'image' not in request.files:
        return jsonify({"type": "0"})  # No image received
    
    image_file = request.files['image']
    
    try:
        image = Image.open(image_file)  # Open the uploaded image
    except IOError:
        return jsonify({"type": "0"})

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([prompts.prompt1, image])

    # Print response.text to debug
    print('Response text from model:', response.text)
    
    try:
        # Attempt to parse the response as JSON
        response_json = json.loads(response.text)
    except json.JSONDecodeError:
        # If parsing fails, return a default error response
        return jsonify({"type": "0"})
    
    # Return the parsed JSON response
    return jsonify(response_json)

@app.route('/cat_text',methods=['POST'])
def cat_text():
    if 'text' not in request.form:
        return jsonify({"type": "0"})

    text = request.form['text']
    print(text)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompts.prompt2+text)

    print('Response text from model:', response.text)
    
    try:
        # Attempt to parse the response as JSON
        response_json = json.loads(response.text)
    except json.JSONDecodeError:
        # If parsing fails, return a default error response
        return jsonify({"type": "0"})
    
    # Return the parsed JSON response
    return jsonify(response_json)

@app.route('/admin_login')
def admin_login():
    if not session.get('user_id'):
        return redirect('/login')

    try:
        # Define severity mapping for sorting (High -> 1, Medium -> 2, Low -> 3)
        severity_order = {'high': 1, 'medium': 2, 'low': 3}

        # Retrieve and sort pending complaints (status = 0) by severity
        pending_complaints = list(
            complaints_collection.find({'status': 0}).sort(
                [("severity", 1)]  # Sort by severity, lower is prioritized
            )
        )

        # Retrieve and sort active complaints (status = 1) by severity
        active_complaints = list(
            complaints_collection.find({'status': 1}).sort(
                [("severity", 1)]  # Sort by severity, lower is prioritized
            )
        )

        # Pass the complaints and status options to the template
        return render_template('admin_page.html', 
                               pending_complaints=pending_complaints, 
                               active_complaints=active_complaints,
                               here={1: "approved", 2: "disapproved", 0: "pending"})

    except Exception as e:
        print(f'Error loading complaints: {e}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/add_complaint', methods=['POST'])
def add_complaint():
    try:
        data = request.json
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not logged in'})
        
        # Generate a unique complaint ID
        complaint_id = str(uuid.uuid4())
        
        # Prepare the data
        complaint_data = {
            'complaint_id': complaint_id,
            'user_id': user_id,
            'name': data.get('name'),
            'email': data.get('email'),
            'pnr': data.get('pnr'),
            'incident_date_time': data.get('incidentDateTime'),
            'type': data.get('type'),
            'sub_type': data.get('subType'),
            'message': data.get('message'),
            'severity': 'Uncategorized'  # Default value before categorization
        }
        
        # Call Gemini API to categorize and get severity
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompts.prompt3 + 'Type: ' + data.get('type') + " details:" + data.get('message'))
        print(response.text)
        # Extract severity from the response
        response_json = json.loads(response.text)
        severity = response_json.get('severity', 'Uncategorized')
        department = response_json.get('department', 'Uncategorized')
        
        # Update severity in the complaint data
        complaint_data['severity'] = severity
        complaint_data['department'] = department
        complaint_data['status']=0
        
        
        # Save to MongoDB
        complaints_collection.insert_one(complaint_data)
        
        return jsonify({'success': True, 'complaint_id': complaint_id})
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/status', methods=['POST'])
def status():
    try:
        data = request.get_json()
        complaint_id = data.get('complaint_id')
        new_status = data.get('status')  # 1 for approve, 2 for disapprove
        
        if not complaint_id or new_status not in [1, 2]:
            return jsonify({'success': False, 'message': 'Invalid data'}), 400
        
        # Update the status in the database
        result = complaints_collection.update_one(
            {'complaint_id': complaint_id},
            {'$set': {'status': new_status}}
        )
        
        if result.modified_count == 1:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Complaint not found or no update made'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    try:
        # Retrieve the user's requests from MongoDB
        user_id = session['user_id']  # Define this based on your authentication method
        
        # Define severity mapping for sorting (High -> 1, Medium -> 2, Low -> 3)
        severity_order = {'high': 1, 'medium': 2, 'low': 3}

        # Retrieve and sort user requests by severity
        user_requests = list(
            complaints_collection.find({'user_id': user_id}).sort(
                [("severity", 1)]  # Sort by severity, lower values (1 = high) come first
            )
        )
        
        # Pass the requests to the template
        return render_template('dashboard.html', 
                               user_requests=user_requests, 
                               here={1: "approved", 2: "disapproved", 0: "pending"})
    except Exception as e:
        print(f'Error loading user requests: {e}')
        return jsonify({'success': False, 'error': str(e)})


@app.route('/save_changes', methods=['POST'])
def save_changes():
    try:
        data = request.json
        complaint_id = data['complaint_id']
        
        # Debugging to see the received data
        print(f"Received data: {data}")
        print(f"Complaint ID: {complaint_id}")

        # Perform the update in MongoDB
        result = complaints_collection.update_one(
            {'complaint_id': complaint_id},  # Match complaint ID
            {
                '$set': {
                    'type': data['type'],
                    'severity': data['severity'],
                    'department': data['department']
                }
            }
        )
        
        # Check if the document was actually modified
        if result.matched_count == 0:
            print(f"No document found with complaint_id: {complaint_id}")
            return jsonify({'success': False, 'message': 'No matching document found'})
        else:
            print(f"Document updated for complaint_id: {complaint_id}")
            return jsonify({'success': True})

    except Exception as e:
        print(f"Error while saving changes: {e}")
        return jsonify({'success': False, 'message': str(e)})




if __name__ == '__main__':
    app.run(debug=True)
