from flask import Flask,render_template, session
from flask_mysqldb import MySQL

from searchings import searchings
from books import books
from addBorrow import newBorrow
from editBorrow import editionBorrow
from extendBorrow import extensionBorrow
from returnBorrow import returningBorrow
from readerBorrow import readerBorrow
from errorsAndCommunicates import errors
from changePassword import changePasswords
from loggings import logging
from registering import registration
from reports import reports

app = Flask(__name__)
app.register_blueprint(searchings)
app.register_blueprint(books)
app.register_blueprint(newBorrow)
app.register_blueprint(editionBorrow)
app.register_blueprint(extensionBorrow)
app.register_blueprint(returningBorrow)
app.register_blueprint(readerBorrow)
app.register_blueprint(errors)
app.register_blueprint(changePasswords)
app.register_blueprint(logging)
app.register_blueprint(registration)
app.register_blueprint(reports)


app.config['MYSQL_HOST'] = 'sql.freedb.tech'
app.config['MYSQL_USER'] = 'freedb_jasina'
app.config['MYSQL_PASSWORD'] = 'v4Y33xteRgdvC@G'
app.config['MYSQL_DB'] = 'freedb_Biblioteka'

mysql = MySQL(app)

app.secret_key = ' '

@app.before_request
def before_request():
    if 'loggedInReader' not in session  and 'loggedInWorker' not in session:
        session['loggedInReader'] = None
        session['loggedInWorker'] = None

# function in order to reduce repeating of code
def setSession(account, fileToOpen):
    session['id'] = account[0]
    session['username'] = account[4]
    return render_template(fileToOpen, name=account[1], surname=account[2])

def setSessionReader(account, fileToOpen):
    session['loggedInReader'] = True
    session['loggedInWorker'] = False
    return setSession(account, fileToOpen)
    
def setSessionWorker(account, fileToOpen):
    session['loggedInReader'] = False
    session['loggedInWorker'] = True
    return setSession(account, fileToOpen)

@app.route("/")
def hello_world():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
