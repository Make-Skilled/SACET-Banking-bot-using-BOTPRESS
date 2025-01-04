from flask import Flask, render_template,request,session,redirect,url_for
from pymongo import MongoClient
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key="banking_app"

# MongoDB Configuration
MONGO_URI = "mongodb+srv://krishnareddy:1234567890@diploma.1v5g6.mongodb.net/"
DB_NAME = "banking"

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users=db['users']
transactions=db['transactions']

@app.route('/')
def index():    
    return render_template('index.html')

@app.route("/sendmoney")
def returnmoney():
    customer_id=session['customerid']
    if not customer_id:
        return render_template('login.html')
    user=users.find_one({"customerid": customer_id})
    return render_template('send.html',balance=user.get('balance'))

@app.route("/admindashboard")
def admindashboard():
    return render_template('admindashboard.html')

@app.route("/dashboard")
def dashboard():
    customer_id=session['customerid']
    if not customer_id:
        return render_template('login.html')
    user=users.find_one({"customerid": customer_id})
    return render_template('dashboard.html',balance=user.get('balance'))

@app.route('/login', methods=['GET', 'POST'])
def loginuser():
    if request.method == 'POST':
        # Get form data from the request
        customer_id = request.form.get('customerid')
        password = request.form.get('password')
        
        if customer_id=="9876543210" and password == "1234567890":
            session['userType']='admin'
            return redirect('/admindashboard')

        if not customer_id or not password:
            return render_template('login.html', error="Customer ID and Password are required.")

        user=users.find_one({"customerid": customer_id})

        if user and user.get("password") == password:
            session['customerid']=customer_id
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid Customer ID or Password.")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def registeruser():
    if request.method == 'POST':
        # Get form data from the request
        cname = request.form.get('cname')
        aadhaar = request.form.get('aadhaar')
        mobile = request.form.get('mobile')
        address = request.form.get('address')
        account_type = request.form.get('accountType')
        customer_id = request.form.get('customerId')
        password = request.form.get('password')

        # Validate Aadhaar and Customer ID
        if len(aadhaar) != 12 or not aadhaar.isdigit():
            return render_template('register.html', error="Aadhaar number must be 12 digits.")
        if len(customer_id) != 12 or not customer_id.isdigit():
            return render_template('register.html', error="Customer ID must be 12 digits.")

        # Insert user into MongoDB
        collection = db["users"]
        if collection.find_one({"customerid": customer_id}):
            return render_template('register.html', error="Customer ID already exists.")
        if collection.find_one({"aadhaar": aadhaar}):
            return render_template('register.html', error="Aadhaar number already exists.")
        if collection.find_one({"mobile": mobile}):
            return render_template('register.html', error="Mobile number already exists.")

        collection.insert_one({
            "cname": cname,
            "aadhaar": aadhaar,
            "mobile": mobile,
            "address": address,
            "accountType": account_type,
            "customerid": customer_id,
            "password": password,
            "balance":1000
        })
        session['userType']='customer'
        session['customerid']=customer_id

        return render_template('admindashboard.html',message="User registration successful")

    return render_template('register.html')

@app.route('/transfer', methods=['POST'])
def transfer():
    if 'customerid' not in session:
        return render_template('login.html', error="User not logged in.")

    from_customer_id = session['customerid']
    to_customer_id = request.form.get('to')
    amount = request.form.get('amount')

    if not to_customer_id or not amount:
        return render_template('send.html', error="Customer ID and amount are required.")

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive.")
    except ValueError as e:
        return render_template('transfer.html', error=str(e))

    collection = db["users"]

    from_user = collection.find_one({"customerid": from_customer_id})
    to_user = collection.find_one({"customerid": to_customer_id})

    if not from_user:
        return render_template('send.html', error="Sender account not found.")
    if not to_user:
        return render_template('send.html', error="Recipient account not found.")

    if from_user.get("balance", 0) < amount:
        return render_template('send.html', error="Insufficient balance.")
    
    

    # Perform the transfer
    collection.update_one({"customerid": from_customer_id}, {"$inc": {"balance": -amount}})
    collection.update_one({"customerid": to_customer_id}, {"$inc": {"balance": amount}})
    
    user=collection.find_one({"customerid": from_customer_id})
    current_time = time.time()
    readable_time = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
    
    record={
    "sent_from":from_customer_id,
    "sent_to":to_customer_id,
    "time":readable_time,
    "amount":amount,
    "balance":user.get('balance'),
    "type":"debited",
    }
    record1={
    "sent_from":to_customer_id,
    "sent_to":from_customer_id,
    "time":readable_time,
    "amount":amount,
    "balance":user.get('balance'),
    "type":"credited",
    }
    transactions.insert_one(record)
    transactions.insert_one(record1)
    return render_template('send.html', success="Transfer completed successfully.",balance=user.get('balance'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)
