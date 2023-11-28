import hashlib

from MySQLdb import IntegrityError
from flask import Flask, request, render_template, session, flash, redirect, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'sql.freedb.tech'
app.config['MYSQL_USER'] = 'freedb_jasina'
app.config['MYSQL_PASSWORD'] = 'v4Y33xteRgdvC@G'
app.config['MYSQL_DB'] = 'freedb_Biblioteka'

mysql = MySQL(app)

app.secret_key = ' '


@app.before_request
def before_request():
    if 'loggedin' not in session:
        session['loggedin'] = None


# function in order to reduce repeating of code
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
    cursor.execute(
        "SELECT Tytul, RokWyd, Wydawnictwo, LiczDostEgz, ISBN FROM `ksiazki` WHERE Tytul LIKE %s ORDER BY Tytul",
        ('%' + search_term + '%',))
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
        session['email'] = email
        session['hashPassword'] = hashPassword

        if account:
            return setSession(account, "loggedReader.html")
        else:
            return redirect(url_for("loggedInWorker"))     


@app.route("/loggedUser/worker")
def loggedInWorker():
        email = session.get('email')
        hashPassword = session.get('hashPassword')
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM `pracownicy` WHERE Email = %s AND Haslo = %s', (email, hashPassword))
        accountWorker = cursor.fetchone()
        if accountWorker:
                return setSession(accountWorker, "loggedWorker.html")
        else:
                flash('Wprowadzono niepoprawny email lub hasło')
                return redirect('/login')


@app.route("/loggedOut")
def logout():
    session.pop('loggedin', False)
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
            cursor.execute(
                "INSERT INTO czytelnicy (ImieCz, NazwiskoCz, NrTel, Email, Haslo) VALUES (%s, %s, %s, %s, %s)",
                (first_name, last_name, phone, email, hashed_password))
            mysql.connection.commit()
            cursor.close()
            flash('Your account has been created!', 'success')
            return redirect(url_for('log_in'))
        return render_template("register.html")
    except IntegrityError:
        flash('Your e-mail was used in another account! Please enter another e-mail', 'error')
        return redirect(url_for('register'))


# method which not to allow unwanted user to go to websites for logged users only
def isUserLoggedIn(website):
    if session.get('loggedin'):
        return render_template(website)
    else:
        flash("You don't have a permission. Please log-in firstly")
        return redirect(url_for('log_in'))


@app.route("/newBook", methods=['GET', 'POST'])
def newBook():
    if request.method == 'POST':
        print(request.form)

        isbn = request.form['isbn']
        title = request.form['title']
        year = request.form['releaseYear']
        publisher = request.form['publisher']
        available_copies = request.form['availableBooks']
        first_name = request.form['authorName']
        last_name = request.form['authorSurname']

        cursor = mysql.connection.cursor()

        # Check if the author exists in the Authors table
        cursor.execute("SELECT IdA FROM autorzy WHERE ImieA = %s AND NazwiskoA = %s", (first_name, last_name))
        author = cursor.fetchone()

        if author:
            author_id = author[0]
        else:
            # If the author doesn't exist, insert a new author
            cursor.execute("INSERT INTO autorzy (ImieA, NazwiskoA) VALUES (%s, %s)", (first_name, last_name))
            author_id = cursor.lastrowid

        # Insert the book into the Books table
        cursor.execute("INSERT INTO ksiazki (ISBN, Tytul, RokWyd, Wydawnictwo, LiczDostEgz) "
                       "VALUES (%s, %s, %s, %s, %s)",
                       (isbn, title, year, publisher, available_copies))

        # Insert the book-author relationship into the BooksAuthors table
        cursor.execute("INSERT INTO autorstwa (ISBN, IdA) VALUES (%s, %s)", (isbn, author_id))

        # Commit the changes to the database
        mysql.connection.commit()
        cursor.close()
        flash('New book added!', 'success')
        return redirect(url_for('newBook'))
    return render_template("addBook.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
