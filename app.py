from flask import Flask, request, render_template, session, flash, redirect, url_for
from flask_mysqldb import MySQL
from MySQLdb import IntegrityError
import hashlib

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'sql.freedb.tech'
app.config['MYSQL_USER'] = 'freedb_jasina'
app.config['MYSQL_PASSWORD'] = 'v4Y33xteRgdvC@G'
app.config['MYSQL_DB'] = 'freedb_Biblioteka'

mysql = MySQL(app)

app.secret_key = ' '

#function in order to reduce repeating of code
def setSession(account, fileToOpen):
    session['loggedin'] = True
    session['id'] = account[0]
    session['username'] = account[4]
    return render_template(fileToOpen, name=account[1], surname=account[2])


@app.route("/")
def hello_world():
    return render_template('index.html')


@app.route("/login")
def log_in():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/search", methods=['GET', 'POST'])
def search():
    search_term = request.form.get('searchedBook')
    cursor = mysql.connection.cursor()
    # Modify the SQL query to search for books by title
    cursor.execute("SELECT Tytul, RokWyd, Wydawnictwo, LiczDostEgz, ISBN FROM `ksiazki` WHERE Tytul LIKE %s ORDER BY Tytul", ('%' + search_term + '%',))
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
            return setSession(account, "loggedReader.html")
        else:
            cursor.execute('SELECT * FROM `pracownicy` WHERE Email = %s AND Haslo = %s', (email, hashPassword))
            accountWorker = cursor.fetchone()
            if accountWorker:
                return setSession(accountWorker, "loggedWorker.html")
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
    try:
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
    except IntegrityError:
        flash('Your e-mail was used in another account! Please enter another e-mail', 'error')
        return redirect(url_for('register'))

@app.route("/newBook")
def newBook():
    return render_template("addBook.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
