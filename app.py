from flask import Flask, request, render_template, session, flash, redirect, url_for
from flask_mysqldb import MySQL
import hashlib

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'sql11.freemysqlhosting.net'
app.config['MYSQL_USER'] = 'sql11661169'
app.config['MYSQL_PASSWORD'] = 'hcJM5mgLXi'
app.config['MYSQL_DB'] = 'sql11661169'

mysql = MySQL(app)

app.secret_key = ' '

@app.route("/")
def hello_world():
    return render_template('index.html')


@app.route("/login")
def log_in():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/search", methods=['POST'])
def search():
    search_term = request.form.get('searchedBook')
    cursor = mysql.connection.cursor()
    # Modify the SQL query to search for books by title
    cursor.execute("SELECT * FROM `ksiazki` WHERE Tytul LIKE %s", ('%' + search_term + '%',))
    books = cursor.fetchall()
    cursor.close()
    return render_template("search.html", books=books)



@app.route("/loggedUser/reader", methods=['POST', 'GET'])
def loggedIn():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        hashPassword = hashlib.md5(password.encode()).hexdigest()
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM `czytelnicy` WHERE Email = %s AND Haslo = %s', (email, hashPassword))
        account = cursor.fetchone()
        
        if account: 
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[4]
            return render_template("loggedReader.html", name=account[1], surname=account[2])
        else:
            cursor.execute('SELECT * FROM `pracownicy` WHERE Email = %s AND Haslo = %s', (email, hashPassword))
            accountWorker = cursor.fetchone()
            if accountWorker:
                session['loggedin'] = True
                session['id'] = accountWorker[0]
                session['username'] = accountWorker[4]
                return render_template("loggedWorker.html", name=accountWorker[1], surname=accountWorker[2])
            else:
                flash('Wprowadzono niepoprawny email lub hasło')
                return redirect('/login')


@app.route("/loggedOut")
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return render_template("index.html")


@app.route("/register", methods=['GET', 'POST'])
def registering():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        cursor.execute("INSERT INTO czytelnicy (ImieCz, NazwiskoCz, NrTel, Email, Haslo) VALUES (%s, %s, %s, %s, %s)",
                       (first_name, last_name, phone, email, hashed_password))
        mysql.connection.commit()
        cursor.close()
        flash('Your account has been created!', 'success')
        return redirect(url_for('log_in'))
    return render_template("register.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
