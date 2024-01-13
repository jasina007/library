import hashlib
from flask import request, render_template, session, flash, redirect, url_for, Blueprint

from errorsAndCommunicates import incorrectLogging, noPermissions

logging = Blueprint("logging", __name__, static_folder="static", template_folder="templates")


@logging.route("/login")
def log_in():
    return render_template("login.html")


@logging.route("/loggedUser/reader", methods=['POST', 'GET'])
def loggedIn():
    from app import setSessionReader, mysql
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        hashPassword = hashlib.md5(password.encode()).hexdigest()
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM `czytelnicy` WHERE Email = %s AND Haslo = %s', (email, hashPassword))
        account = cursor.fetchone()
        session['email'] = email
        session['hashPassword'] = hashPassword

        if account:
            session['id'] = account[0]
            return setSessionReader(account, "loggedReader.html")
        else:
            return redirect(url_for("logging.loggedInWorker"))
    #check if user(reader) was already logged in
    elif session.get('loggedInReader'):
        return render_template("loggedReader.html")
    else:
        return incorrectLogging()


@logging.route("/loggedUser/worker")
def loggedInWorker():
    from app import setSessionWorker, mysql
    #check if user(worker) was already logged in
    if session.get('loggedInWorker'):
        return render_template("loggedWorker.html")
    
    email = session.get('email')
    hashPassword = session.get('hashPassword')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM `pracownicy` WHERE Email = %s AND Haslo = %s', (email, hashPassword))
    accountWorker = cursor.fetchone()
    if accountWorker:
        session['id'] = accountWorker[0]
        return setSessionWorker(accountWorker, "loggedWorker.html")
    else:
        return incorrectLogging()

        
@logging.route("/loggedOut")
def logout():
    session.pop('loggedInReader', False)
    session.pop('loggedInWorker', False)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('email', None)
    session.pop('hashPassword', None)
    return render_template("index.html")


# method which not to allow unwanted user to go to websites for logged users only
def isUserLoggedIn(loggingType: str, website, **kwargs):
    if session.get(loggingType):
        return render_template(website, **kwargs)
    else:
        return noPermissions()
    
    
def isReaderLoggedIn(website, **kwargs):
    return isUserLoggedIn('loggedInReader', website, **kwargs)
    

def isWorkerLoggedIn(website, **kwargs):
    return isUserLoggedIn('loggedInWorker', website, **kwargs) 