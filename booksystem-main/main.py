from flask import *
from datetime import datetime
# import sqlite3, hashlib, os
import hashlib, os
from werkzeug.utils import secure_filename
from query import runQuery
import time
app = Flask(__name__)
app.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def makeSignin():
    if 'email' not in session:
        loggedIn = False
        userData = {}
    else:
        loggedIn = True
        userData = {}
        userData = runQuery("SELECT * FROM users WHERE email = '" + session['email'] + "'","select")
        if len(userData)>0:
            userData = userData[0]
    return (userData, loggedIn)

@app.route("/")
def root():
    # import pdb;pdb.set_trace()
    userData, loggedIn = makeSignin()
    itemData = runQuery('SELECT * FROM books WHERE status = 1',"select")
    # print(itemData)
    return render_template('home.html', itemData=itemData, userData = userData, loggedIn=loggedIn)

@app.route("/account/dashboard")
def Dashboard():
    if 'email' not in session:
        return redirect(url_for('root'))
    userData, loggedIn = makeSignin()
    itemData = runQuery('SELECT * FROM books where status = 1'.format(userData["userid"]),"select")

    return render_template("dashboard.html", userData=userData, itemData=itemData, loggedIn=loggedIn)

@app.route("/account/addbook", methods=["GET", "POST"])
def addBook():
    if 'email' not in session:
        return redirect(url_for('root'))

    userData, loggedIn = makeSignin()

    if request.method == 'GET':
        return render_template("addBook.html",userData=userData , loggedIn=loggedIn)
    elif request.method == 'POST':
        file1 = request.files["image"]
        path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        image = file1.filename

        file1.save(path)

        bookname = request.form['bookname']
        authorname = request.form['authorname']
        price = request.form['price']
        description = request.form['description']
        createdate = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
        updatedate = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")

        try:
            result = runQuery("INSERT INTO books (userid,image,bookname,authorname,price,description,createdate,updatedate) VALUES ({},'{}','{}','{}','{}','{}','{}','{}')".format(userData["userid"],image,bookname,authorname,price,description,createdate,updatedate),"insert")
            response = "Request is completed successfully."
            return redirect(url_for('Dashboard'))
        except:
            response = "Request is failed."
            return render_template("addBook.html",error=response)

@app.route("/search", methods=["GET", "POST"])
def search():
    # import pdb;pdb.set_trace()
    if request.method == 'POST':
        response = request.form['searchBox']
        userData, loggedIn = makeSignin()
        itemData = runQuery("SELECT * FROM books where status = 1 and (description ILIKE '%{}%' OR bookname ILIKE '%{}%')".format(response,response),"select")
        return render_template('home.html', itemData=itemData, userData=userData, loggedIn=loggedIn)

@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'GET':
        if 'email' in session:
            return redirect(url_for('root'))
        else:
            return render_template('login.html', error='')
    elif request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        status,data = is_valid(email, password)
        if status:
            session['email'] = email
            if data["usertype"] == "author":
                return redirect(url_for('Dashboard'))
            else:
                return redirect(url_for('root'))
        else:
            error = 'Invalid Email or Password. Please try again.'
            return render_template('login.html', error=error)

@app.route("/bookDescription")
def bookDescription():
    ratingsData = {}
    userData, loggedIn = makeSignin()
    productId = request.args.get('productId')
    productData = runQuery("SELECT * FROM books WHERE status =1 and bookid = " + productId +"","select")
    commentsData = runQuery("SELECT cm.commentid,cm.message,cm.createdate,us.name from comment as cm left join users as us on us.userid = cm.userid where cm.bookid = " + productId + " ORDER BY cm.commentid","select")
    ratingsData = runQuery("SELECT round(avg(ratings),2) as avg_ratings,count(*) as tot_ratings,count(case ratings when 1 then 1 else null END) as one_rating,count(case ratings when 2 then 1 else null END) as two_rating,count(case ratings when 3 then 1 else null END) as three_rating,count(case ratings when 4 then 1 else null END) as four_rating,count(case ratings when 5 then 1 else null END) as five_rating from comment where bookid = {}".format(productId),"select")

    if len(ratingsData)>0:
        ratingsData = ratingsData[0]

    for comment in commentsData:
        comment["date_diff"] = get_time(comment)

    return render_template("bookDescription.html", data=productData[0], commentsData=commentsData,ratingsData=ratingsData,userData=userData, loggedIn = loggedIn)


def get_time(comment):
    time = datetime.now()
    # created_date = comment.created_at.astimezone(timezone('Asia/Kolkata'))
    created_date = comment["createdate"]

    start = datetime.strptime(created_date,'%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(datetime.strftime(time,'%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')

    diff_sec = (end -start).total_seconds()

    seconds = diff_sec
    minutes = diff_sec // 60
    hours = (diff_sec // 60) // 60
    days = ((diff_sec // 60) // 60) // 24

    # print(days,minutes,hours,seconds)

    if days > 0:
        return str(int(days)) + " days ago"
    elif hours > 0:
        return str(int(hours)) + " hours ago"
    elif minutes > 0:
        return str(int(minutes)) + " minutes ago"
    elif seconds > 0:
        return str(int(seconds)) + " seconds ago"
    else:
        return "just now"

@app.route("/account/postComment", methods=["POST"])
def postComment():
    if 'email' not in session:
        return redirect(url_for('root'))

    userData, loggedIn = makeSignin()

    if request.method == 'POST':
        # import pdb;pdb.set_trace()

        bookId = request.form['bookId']
        userId = request.form['userId']
        comment = request.form['comment']
        ratings = request.form['ratings']
        createDate = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")

        try:
            result = runQuery("INSERT INTO comment (userid, bookid, ratings, message, createdate) VALUES ({}, {}, {}, '{}', '{}')".format(userData["userid"], bookId, ratings, comment, createDate),"insert")
            response = "Request is completed successfully."
            return jsonify({"status" : True,"response":response})
        except:
            response = "Request is failed."
            return jsonify({"status" : False,"response":response})

@app.route("/account/bookedit/<bookid>", methods=["GET", "POST"])
def editBook(bookid=None):
    if 'email' not in session:
        return redirect(url_for('root'))

    userData, loggedIn = makeSignin()

    if request.method == 'GET':
        productData = runQuery("SELECT * FROM books WHERE status = 1 and bookid = " + bookid +"","select")
        return render_template("editBook.html", userData=userData ,data=productData[0], loggedIn=loggedIn)
    elif request.method == 'POST':
        file1 = request.files["image"]
        if file1:
            path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
            image = file1.filename
            file1.save(path)
        else:
            image = request.form['image']


        bookname = request.form['bookname']
        authorname = request.form['authorname']
        price = request.form['price']
        description = request.form['description']
        createdate = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
        updatedate = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")

        try:
            result = runQuery("UPDATE books SET userid = {},image = '{}',bookname = '{}',authorname = '{}',price = '{}',description = '{}',createdate= '{}',updatedate= '{}' WHERE bookid = '{}'".format(userData["userid"],image,bookname,authorname,price,description,createdate,updatedate,bookid),"update")
            response = "Request is completed successfully."
            return redirect(url_for('Dashboard'))
        except:
            response = "Request is failed."
            return render_template("editBook.html",error=response)

@app.route("/account/bookdelete/<bookid>", methods=["GET", "POST"])
def deleteBook(bookid=None):
    if 'email' not in session:
        return redirect(url_for('root'))

    userData, loggedIn = makeSignin()

    if request.method == 'POST':
        try:
            result = runQuery("UPDATE books SET status = {} WHERE bookid = '{}'".format(0,bookid),"update")
            response = "Request is completed successfully."
            return jsonify({"status" : True,"response":response})
        except:
            response = "Request is failed."
            return jsonify({"status" : False,"response":response})

@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))

def is_valid(email, password):
    data = runQuery("SELECT email, password, usertype FROM users WHERE email='{}' and password='{}'".format(email,hashlib.md5(password.encode()).hexdigest()),"select")
    if data:
        return (True,data[0])
    return (False,{})

def validate(email):
    userId = None
    result = runQuery("SELECT userid FROM users WHERE email = '" + email + "'","select")
    if result:
        userId = result[0]["userid"]
    return userId

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    elif request.method == 'POST':
        password = request.form['password']
        email = request.form['email'].strip().lower()
        name = request.form['name']
        # userType = request.form['userType']
        userType = request.form['userType']
        createDate = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")

        if (validate(email)) != None:
            return render_template("login.html", error="Email already exist.")
        else:
            try:
                runQuery("INSERT INTO users (password, email, name, userType, createDate) VALUES ('{}', '{}', '{}', '{}', '{}')".format(hashlib.md5(password.encode()).hexdigest(), email, name, userType, createDate),"insert")
                response = "Request is completed successfully."
            except:
                response = "Request is failed."
            return render_template("login.html", error=response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
