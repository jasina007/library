import hashlib
from datetime import date
from datetime import datetime

from MySQLdb import IntegrityError
from flask import Flask, request, render_template, session, flash, redirect, url_for
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, TextAreaField, StringField, IntegerField
from wtforms.validators import DataRequired, Optional

app = Flask(__name__)

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


def incorrectLogging():
    flash('Wprowadzono niepoprawny email lub hasło')
    return redirect('/login')


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
            session['id'] = account[0]
            return setSessionReader(account, "loggedReader.html")
        else:
            return redirect(url_for("loggedInWorker"))
    #check if user(reader) was already logged in
    elif session.get('loggedInReader'):
        return render_template("loggedReader.html")
    else:
        return incorrectLogging()


@app.route("/loggedUser/worker")
def loggedInWorker():
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

        
@app.route("/loggedOut")
def logout():
    session.pop('loggedInReader', False)
    session.pop('loggedInWorker', False)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('email', None)
    session.pop('hashPassword', None)
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
        flash('Twój e-mail został użyty już w innym koncie! Użyj innego e-maila.', 'error')
        return redirect(url_for('register'))


# method which not to allow unwanted user to go to websites for logged users only
def isUserLoggedIn(loggingType: str, website, **kwargs):
    if session.get(loggingType):
        return render_template(website, **kwargs)
    else:
        flash("Nie posiadasz odpowiednich uprawnień. Zaloguj się.")
        return redirect(url_for('log_in'))
    
    
def isReaderLoggedIn(website, **kwargs):
    return isUserLoggedIn('loggedInReader', website, **kwargs)
    

def isWorkerLoggedIn(website, **kwargs):
    return isUserLoggedIn('loggedInWorker', website, **kwargs) 


@app.route("/newBook", methods=['GET', 'POST'])
def newBook():
    if request.method == 'POST':

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
        flash('Dodano książkę pomyślnie!', 'success')
        return redirect(url_for('loggedInWorker'))
    return isWorkerLoggedIn("addBook.html")


class BorrowForm(FlaskForm):
    reader = SelectField('idCz', validators=[DataRequired()])
    book = SelectField('isbn', validators=[DataRequired()])
    borrow_date = DateField('borrowDate', validators=[DataRequired()])
    return_date = DateField('returnDate', validators=[DataRequired()])



@app.route('/newBorrow', methods=['GET', 'POST'])
def addBorrow():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT IdCz, ImieCz, NazwiskoCz FROM czytelnicy')
    readers = [(str(reader[0]), f"{reader[1]} {reader[2]}") for reader in cursor.fetchall()]
    cursor.execute('SELECT ISBN, Tytul FROM ksiazki')
    books = [(book[0], book[1]) for book in cursor.fetchall()]

    form = BorrowForm()
    form.reader.choices = readers
    form.book.choices = books

    if form.validate_on_submit():
        borrow_date = form.borrow_date.data
        return_date = form.return_date.data
        if borrow_date > date.today():
            flash('Data wypożyczenia nie może być późniejsza od obecnej', 'error')
            return redirect(url_for('addBorrow'))
        if return_date < date.today():
            flash('Data zwrotu nie może być wcześniejsza od obecnej', 'error')
            return redirect(url_for('addBorrow'))
        # Insert the borrow record into the database
        cursor.execute(
            'INSERT INTO wypozyczenia (IdCz, ISBN, DataWyp, OczekDataZwr, IdPWyd) VALUES (%s, %s, %s, %s, %s)',
            (form.reader.data, form.book.data, form.borrow_date.data, form.return_date.data, session.get('id'))
        )
        mysql.connection.commit()

        flash('Dodano pomyślnie', 'success')
        return redirect(url_for('loggedInWorker'))

    return isWorkerLoggedIn('addBorrow.html', form=form)


class ReturnBorrowForm(FlaskForm):
    borrow = SelectField('borrow', validators=[DataRequired()])
    returnDate = DateField('returnDate', validators=[DataRequired()])
    comments = TextAreaField('comments')


@app.route('/returnBorrow', methods=['GET', 'POST'])
def returnBorrow():
    cursor = mysql.connection.cursor()

    # Modified SQL query to fetch necessary columns
    cursor.execute('''
        SELECT w.IdWyp, c.ImieCz, c.NazwiskoCz, k.Tytul, w.DataWyp
        FROM wypozyczenia w
        JOIN czytelnicy c ON w.IdCz = c.IdCz
        JOIN ksiazki k ON w.ISBN = k.ISBN
        WHERE w.FaktDataZwr IS NULL
    ''')

    borrows = [
        (str(borrow[0]), f"{borrow[1]} {borrow[2]} - {borrow[3]} - {borrow[4]}")
        for borrow in cursor.fetchall()
    ]

    form = ReturnBorrowForm()
    form.borrow.choices = borrows

    if form.validate_on_submit():
        selected_borrow_id = form.borrow.data
        selected_borrow = next((borrow for borrow in borrows if borrow[0] == selected_borrow_id), None)
        return_date = form.returnDate.data
        borrow_date = datetime.strptime(selected_borrow[-1].split()[-1], '%Y-%m-%d').date()

        if return_date > date.today():
            flash('Data faktycznego zwrotu nie może być późniejsza od obecnej', 'error')
            return redirect(url_for('returnBorrow'))
        if return_date < borrow_date:
            flash('Data faktycznego zwrotu nie może być wcześniejsza od daty wypożyczenia ', 'error')
            return redirect(url_for('returnBorrow'))

        # Insert the borrow record into the database
        sql = "UPDATE wypozyczenia SET FaktDataZwr = %s, Uwagi = %s, IdPOdb = %s WHERE IdWyp = %s"
        cursor.execute(
            sql, (form.returnDate.data, form.comments.data, session.get("id"), selected_borrow_id)
        )
        mysql.connection.commit()

        flash('Dodano pomyślnie', 'success')
        return redirect(url_for('loggedInWorker'))

    return isWorkerLoggedIn('returnBorrow.html', form=form)


class EditBookForm(FlaskForm):
    book = SelectField('isbn', validators=[DataRequired()])
    title = StringField('title', validators=[DataRequired()])
    year = IntegerField('year', validators=[Optional()])
    publisher = StringField('publisher', validators=[Optional()])
    available_copies = IntegerField('available_copies', validators=[Optional()])


@app.route('/editBook', methods=['GET', 'POST'])
def edit_book():
    cursor = mysql.connection.cursor()

    # Fetch existing books from the database
    cursor.execute('SELECT ISBN, Tytul, RokWyd, Wydawnictwo, LiczDostEgz FROM ksiazki')
    books = [(book[0], f"{book[0]} - {book[1]} - {book[2]} - {book[3]} - {book[4]}") for book in cursor.fetchall()]

    form = EditBookForm()
    form.book.choices = books

    if form.validate_on_submit():

        if 'delete_book' in request.form and request.form['delete_book'] == 'true':
            # Delete the book record from the database
            isbn_to_delete = form.book.data
            cursor.execute('DELETE FROM autorstwa WHERE ISBN = %s', (isbn_to_delete,))
            cursor.execute('DELETE FROM ksiazki WHERE ISBN = %s', (isbn_to_delete,))
            mysql.connection.commit()

            flash('Książka została usunięta pomyślnie', 'success')
            return redirect(url_for('loggedInWorker'))

        isbn = form.book.data
        title = form.title.data
        rokwyd = form.year.data
        wydawnictwo = form.publisher.data
        liczdostegz = form.available_copies.data

        # Update the book record in the database
        cursor.execute('UPDATE ksiazki SET Tytul = %s, RokWyd = %s, Wydawnictwo = %s, LiczDostEgz = %s WHERE ISBN = %s',
                       (title, rokwyd, wydawnictwo, liczdostegz, isbn))
        mysql.connection.commit()

        flash('Dodano pomyślnie', 'success')
        return redirect(url_for('loggedInWorker'))

    return isWorkerLoggedIn('editBook.html', form=form)


#create new list with borrows to set None values to message to user
def setNoneToUserMessage(borrows):
    newBorrows = []
    #checking if FaktDataZwr attribute is None
    for row in borrows:
        currentBorrowList = list(row)
        if(currentBorrowList[-1] is None):
            currentBorrowList[-1] = "Nie zwrócono"
        newBorrows.append(tuple(currentBorrowList))
    return newBorrows


@app.route("/readerBorrows")
def readerBorrows():
    idCz = session.get('id')
    cursor = mysql.connection.cursor()
    cursor.execute(
    "SELECT k.Tytul, w.DataWyp, w.OczekDataZwr, w.FaktDataZwr FROM `wypozyczenia` AS w INNER JOIN `ksiazki` AS k ON w.ISBN = k.ISBN WHERE w.IdCz = %s",  (idCz,))
    borrows = cursor.fetchall()
    cursor.close()
    borrows = setNoneToUserMessage(borrows)
    return isReaderLoggedIn("readerBorrows.html", borrows=borrows)


class ExtendBorrowForm(FlaskForm):
    borrow = SelectField('borrow', validators=[DataRequired()])
    newReturnDate = DateField('newReturnDate', validators=[DataRequired()])

    

@app.route("/extendBorrow", methods=['GET', 'POST'])
def extendBorrow():
    idCz = session.get('id')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT w.IdWyp, k.Tytul, w.DataWyp, w.OczekDataZwr, w.FaktDataZwr FROM `wypozyczenia` AS w INNER JOIN `ksiazki` AS k ON w.ISBN = k.ISBN WHERE w.IdCz = %s",  (idCz,))
    
    borrows = [
        (str(borrow[0]), f"{borrow[1]} - {borrow[2]} - {borrow[3]} - {borrow[4]}")
        for borrow in cursor.fetchall()
    ]
    
    form = ExtendBorrowForm()
    form.borrow.choices = borrows
    
    if form.validate_on_submit():
        selected_borrow_id = form.borrow.data
        newReturnDate = form.newReturnDate.data
        
        #get selected borrow from database with needed data
        cursor.execute("SELECT w.IdWyp, k.Tytul, w.DataWyp, w.OczekDataZwr, w.FaktDataZwr FROM `wypozyczenia` AS w INNER JOIN `ksiazki` AS k ON w.ISBN = k.ISBN WHERE w.IdWyp = %s",  (selected_borrow_id,))
        selected_borrow = cursor.fetchall()[0]
        
        #checking correction of entered data
        if selected_borrow[-1] is not None:
            flash('Nie można przedłużyć wyposażenia już zakończonego', 'error')
            return redirect(url_for('extendBorrow'))
        if newReturnDate <= selected_borrow[3]:
            flash('Nowa data musi być późniejsza', 'error')
            return redirect(url_for('extendBorrow'))

        # Insert the borrow record into the database
        sql = "UPDATE wypozyczenia SET OczekDataZwr = %s WHERE IdWyp = %s"
        cursor.execute(
            sql, (newReturnDate, selected_borrow_id)
        )
        mysql.connection.commit()

        flash('Przedłużono pomyślnie', 'success')
        return redirect(url_for('loggedIn'))

    return isReaderLoggedIn('extendBorrow.html', form=form)


def changePassword(tableName, urlForPassword, keyAttributeName, urlForMainPage):
    idCz = session.get('id')
    password = request.form['password']
    cursor = mysql.connection.cursor()
    cursor.execute(f"SELECT Haslo FROM {tableName} WHERE {keyAttributeName} = %s", (idCz,))
    current_password = cursor.fetchall()[0][0]
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    #check if new password equals current in database
    if current_password == hashed_password:
        flash('Nowe hasło musi być inne od aktualnego', 'error')
        return redirect(url_for(urlForPassword))
    
    cursor.execute(f"UPDATE {tableName} SET Haslo = %s WHERE {keyAttributeName} = %s",(hashed_password, idCz))
    mysql.connection.commit()
    cursor.close()
    flash('Zmieniono hasło pomyślnie', 'success')
    return redirect(url_for(urlForMainPage))


@app.route("/changeReaderPassword", methods=['GET', 'POST'])
def changeReaderPassword():
    if request.method == 'POST':
        return changePassword('czytelnicy', 'changeReaderPassword', 'IdCz', 'loggedIn')
    return isReaderLoggedIn("changeReaderPassword.html")


@app.route("/changeWorkerPassword", methods=['GET', 'POST'])
def changeWorkerPassword():
    if request.method == 'POST':
        return changePassword('pracownicy', 'changeWorkerPassword', 'IdP','loggedInWorker')
    return isWorkerLoggedIn("changeWorkerPassword.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
