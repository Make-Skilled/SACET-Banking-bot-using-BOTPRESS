from flask import Flask, render_template,request,session,redirect,url_for
from pymongo import MongoClient
import time
from flask_cors import CORS
from datetime import datetime
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key="banking_app"
CORS(app)

def generate_customer_id():
    """Generate a unique 12-digit customer ID not starting with 0."""
    return random.randint(100000000000, 999999999999)

def send_email(recipient, subject, body):
    """Send an email using SMTP."""
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "kr4785543@gmail.com"
        sender_password = "lkrmqtcolyshijmf"

        # Set up the message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

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
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate Aadhaar number
        if len(aadhaar) != 12 or not aadhaar.isdigit():
            return render_template('register.html', error="Aadhaar number must be 12 digits.")

        # Validate email, Aadhaar, and mobile for uniqueness
        collection = db["users"]
        if collection.find_one({"email": email}):
            return render_template('register.html', error="Email already exists.")
        if collection.find_one({"aadhaar": aadhaar}):
            return render_template('register.html', error="Aadhaar number already exists.")
        if collection.find_one({"mobile": mobile}):
            return render_template('register.html', error="Mobile number already exists.")

        # Generate a unique 12-digit customer ID
        customer_id = generate_customer_id()
        while collection.find_one({"customerid": str(customer_id)}):
            customer_id = generate_customer_id()

        # Insert user into MongoDB
        collection.insert_one({
            "cname": cname,
            "aadhaar": aadhaar,
            "mobile": mobile,
            "address": address,
            "accountType": account_type,
            "customerid": str(customer_id),
            "email": email,
            "password": password,
            "balance": 1000
        })

        # Set session details for the user
        session['userType'] = 'customer'
        session['customerid'] = str(customer_id)

        # Send success email to the user
        email_body = f"""
        Dear {cname},

        Congratulations! Your bank account has been successfully created.

        Your Customer ID: {customer_id}

        Please keep this Customer ID safe as it will be required for future transactions.

        Regards,
        Your Bank Team
        """
        send_email(email, "Bank Account Registration Successful", email_body)

        # Return success message
        return render_template('admindashboard.html', message="User registration successful. Email sent with Customer ID.")

    return render_template('register.html')

@app.route('/transfer', methods=['POST'])
def transfer():

    from_customer_id = request.form.get('from')
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

@app.route('/deposit', methods=['GET'])
def deposit_form():
    return render_template('deposit.html')

# Route for handling form submission
@app.route('/deposit', methods=['POST'])
def deposit():
    # Get form data using request.form.get
    to_customer_id = request.form.get('to')
    amount = request.form.get('amount')
    
    # Perform any logic here (e.g., validate inputs, check user, etc.)
    if to_customer_id and amount :
        try:
            # Convert amount to float and ensure it's a valid number
            deposit_amount = float(amount)
            if deposit_amount <= 0:
                return render_template('deposit.html', error='Amount must be positive.')

            # Find the user by the provided `to_customer_id` (customer ID)
            user = users.find_one({'customerid': to_customer_id})

            if user:
                # Increment the user's balance by the deposit amount
                users.update_one(
                    {'customerid': to_customer_id},
                    {'$inc': {'balance': deposit_amount}}
                )
                
                # Record the transaction in a 'transactions' collection
                current_time = time.time()
                readable_time = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
                user = users.find_one({'customerid': to_customer_id})
                record = {
                    "sent_from":to_customer_id,
                    "sent_to":"-",
                    "time": readable_time,
                    "amount": deposit_amount,
                    "balance": user.get('balance') ,  # New balance after deposit
                    "type": "deposited",  # Assuming the action is a credit (deposit)
                }
                print("hello")
                # Insert the transaction record
                transactions.insert_one(record)
                
                # Redirect to a success page or deposit page
                return render_template('deposit.html', success='Deposit successful.')
            else:
                return render_template('deposit_form', error='Recipient user not found.')

        except ValueError:
            return redirect(url_for('deposit_form', error='Invalid amount.'))
        except Exception as e:
            return redirect(url_for('deposit_form', error=str(e)))
    else:
        # Handle missing or invalid form data
        return render_template('deposit.html', error='Invalid input')

@app.route("/checkbalance")
def checkbalance():
    return render_template('checkbalance.html')

@app.route("/checkbalance",methods=['post'])
def checkbala():
    id=request.form.get('to')
    user=users.find_one({"customerid":id})
    if not user:
        return render_template('checkbalance.html',error="User does not exist")
    return render_template("checkbalance.html",balance=user.get('balance'))

from flask import Flask, jsonify, request

@app.route("/checkbal", methods=['POST'])
def checkbal():
    id = request.args.get('id')
    
    # Find the user in the MongoDB collection
    user = users.find_one({"customerid": id})
    
    if not user:
        return jsonify({"error": "User does not exist"}), 404  # Return a 404 error if user doesn't exist
    
    # Return the user's balance as a JSON response
    return jsonify({"customerid": id, "balance": user.get('balance')}), 200

@app.route('/transactions', methods=['GET'])
def transactions1():
    print(session['customerid'])
    # Fetch the list of transaction records from the MongoDB collection
    user_transactions = transactions.find({"sent_from":session['customerid']})

    # Convert the cursor to a list and send it to the template
    transaction_list = list(user_transactions)

    # Pass the transaction list to the HTML template
    return render_template('transactions.html', transactions=transaction_list)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)
