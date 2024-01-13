import hashlib
from werkzeug.exceptions import BadRequestKeyError
from datetime import date
from datetime import datetime
from fpdf import FPDF

from MySQLdb import IntegrityError
from flask import Flask, request, render_template, session, flash, redirect, url_for, Response
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


def search(path):
    try:
        search_term = request.form.get('searchedBook')
        cursor = mysql.connection.cursor()
        # Modify the SQL query to search for books by title
        cursor.execute(
            "SELECT Tytul, RokWyd, Wydawnictwo, LiczDostEgz, ISBN FROM `ksiazki` WHERE Tytul LIKE %s ORDER BY Tytul",
            ('%' + search_term + '%',))
        books = cursor.fetchall()
        cursor.close()
        return render_template("search.html", books=books, path=path)
    except TypeError:
        return noSearchParameters()


@app.route("/search", methods=['GET', 'POST'])
def searchForAll():
    return search("/")

@app.route("/searchWorker", methods=['GET', 'POST'])
def searchForWorker():
    return search("/loggedUser/worker")

@app.route("/searchReader", methods=['GET', 'POST'])
def searchForReader():
    return search("/loggedUser/reader")


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


def noPermissions():
    flash("Nie posiadasz odpowiednich uprawnień. Zaloguj się.")
    return redirect(url_for('log_in'))

def noSearchParameters():
    flash("Nie podano danych do wyszukania książki.")
    return redirect(url_for('hello_world'))


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


@app.route("/searchBookWorker")
def searchWorker():
    return isWorkerLoggedIn("searchBookWorker.html")

@app.route("/searchBookReader")
def searchReader():
    return isReaderLoggedIn("searchBookReader.html")


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


def incorrectBorrowDate(urlTo):
    flash('Data wypożyczenia nie może być późniejsza od obecnej', 'error')
    return redirect(url_for(urlTo))

def incorrectReturnDate(urlTo):
    flash('Data zwrotu nie może być wcześniejsza od obecnej', 'error')
    return redirect(url_for(urlTo))


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
            return incorrectBorrowDate('addBorrow')
        if return_date < date.today():
            return incorrectReturnDate('addBorrow')
        # Insert the borrow record into the database
        cursor.execute(
            'INSERT INTO wypozyczenia (IdCz, ISBN, DataWyp, OczekDataZwr, IdPWyd) VALUES (%s, %s, %s, %s, %s)',
            (form.reader.data, form.book.data, form.borrow_date.data, form.return_date.data, session.get('id'))
        )
        mysql.connection.commit()

        flash('Dodano pomyślnie', 'success')
        return redirect(url_for('loggedInWorker'))

    return isWorkerLoggedIn('addBorrow.html', form=form)


class EditBorrowForm(FlaskForm):
    borrow = SelectField('borrow', validators=[DataRequired()])
    readerId = SelectField('readerId', validators=[DataRequired()])
    bookISBN = SelectField('bookISBN', validators=[DataRequired()])
    borrowDate = DateField('borrowDate', validators=[Optional()])
    returnDate = DateField('returnDate', validators=[Optional()])


@app.route('/editBorrow', methods=['GET', 'POST'])
def editBorrow():
    cursor = mysql.connection.cursor()

    # Fetch existing books from the database
    cursor.execute('''SELECT w.IdWyp, c.ImieCz, c.NazwiskoCz, k.Tytul, w.DataWyp, w.OczekDataZwr FROM wypozyczenia w JOIN czytelnicy c ON w.IdCz = c.IdCz JOIN ksiazki k ON w.ISBN = k.ISBN''')
    borrows= [(borrow[0], f"{borrow[0]} - {borrow[1]} {borrow[2]} - {borrow[3]} - {borrow[4]} - {borrow[5]}") for borrow in cursor.fetchall()]
    
    cursor.execute('SELECT IdCz, ImieCz, NazwiskoCz FROM czytelnicy')
    readers = [(str(reader[0]), f"{reader[1]} {reader[2]}") for reader in cursor.fetchall()]
    
    cursor.execute('SELECT ISBN, Tytul FROM ksiazki')
    books = [(book[0], book[1]) for book in cursor.fetchall()]

    form = EditBorrowForm()
    form.borrow.choices = borrows
    form.readerId.choices = readers
    form.bookISBN.choices = books

    if form.validate_on_submit():

        if 'delete_borrow' in request.form and request.form['delete_borrow'] == 'true':
            idWyp_to_delete = form.borrow.data
            cursor.execute('DELETE FROM wypozyczenia WHERE IdWyp= %s', (idWyp_to_delete,))
            mysql.connection.commit()

            flash('Wypożyczenie zostało usunięte pomyślnie', 'success')
            return redirect(url_for('loggedInWorker'))

        idWyp = form.borrow.data
        idCz = form.readerId.data
        isbn = form.bookISBN.data
        dataWyp = form.borrowDate.data
        oczekDataZwr = form.returnDate.data
        
        if dataWyp != None and oczekDataZwr != None:
            if dataWyp > date.today():
                return incorrectBorrowDate('editBorrow')
            if oczekDataZwr < date.today():
                return incorrectReturnDate('editBorrow')

            cursor.execute('UPDATE wypozyczenia SET IdCz = %s, ISBN = %s, DataWyp = %s, OczekDataZwr = %s WHERE IdWyp = %s',
                        (idCz, isbn, dataWyp, oczekDataZwr, idWyp))
        elif oczekDataZwr == None and dataWyp != None:
            cursor.execute('UPDATE wypozyczenia SET IdCz = %s, ISBN = %s, DataWyp = %s WHERE IdWyp = %s',
                       (idCz, isbn, dataWyp, idWyp))
        elif oczekDataZwr != None and dataWyp == None:
            cursor.execute('UPDATE wypozyczenia SET IdCz = %s, ISBN = %s,  OczekDataZwr = %s WHERE IdWyp = %s',
                       (idCz, isbn, oczekDataZwr, idWyp))
        else:
            cursor.execute('UPDATE wypozyczenia SET IdCz = %s, ISBN = %s WHERE IdWyp = %s',
                       (idCz, isbn, idWyp))
        
        mysql.connection.commit()
        flash('Zedytowano pomyślnie wypożyczenie', 'success')
        return redirect(url_for('loggedInWorker'))

    return isWorkerLoggedIn('editBorrow.html', form=form)


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
    title = StringField('title', validators=[Optional()])
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
            cursor.execute('DELETE FROM wypozyczenia WHERE ISBN = %s', (isbn_to_delete,))
            cursor.execute('DELETE FROM ksiazki WHERE ISBN = %s', (isbn_to_delete,))
            mysql.connection.commit()

            flash('Książka została usunięta pomyślnie', 'success')
            return redirect(url_for('loggedInWorker'))

        isbn = form.book.data
        title = form.title.data
        rokwyd = form.year.data
        wydawnictwo = form.publisher.data
        liczdostegz = form.available_copies.data
        
        #below checking is necessary when title is optional field
        #and in this case it must be optional for easier deleting
        if title == "":
            flash('Należy podać tytuł edytowanej książki', 'error')
            return redirect(url_for('edit_book'))
            
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


@app.route("/reports")
def genReports():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT DISTINCT EXTRACT(YEAR FROM DataWyp) FROM `wypozyczenia`;')
    years = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM `autorzy`")
    authors = [author for author in cursor.fetchall()]
    return isWorkerLoggedIn("reports.html", availableYears= years, authors= authors)


#method which convert month integer to string(Polish word)
def convertNumberToMonth(number):
        if number == 1:
            return "Styczeń"
        elif number == 2:
            return "Luty"
        elif number == 3:
            return "Marzec"
        elif number == 4:
            return "Kwiecień"
        elif number == 5:
            return "Maj"
        elif number == 6:
            return "Czerwiec"
        elif number == 7:
            return "Lipiec"
        elif number == 8:
            return "Sierpień"
        elif number == 9:
            return "Wrzesień"
        elif number == 10:
            return "Październik"
        elif number == 11:
            return "Listopad"
        elif number == 12:
            return "Grudzień"


#method which set FPDF object and another related with it attributes
def setFpdfObject(headline, columnsNumber):
    pdf = FPDF()
    pdf.add_page()
    pageWidth = pdf.w - 2*pdf.l_margin
    pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)
    pdf.cell(pageWidth, 0.0, headline, align='C')
    pdf.ln(20)
    col_width = pageWidth/columnsNumber
    pdf.ln(1)
    th = pdf.font_size
    return pdf, col_width, th
    

@app.route("/monthReaders", methods=['GET', 'POST'])
def monthReadersReport():
    try:
        chosenYear = request.form['chosenYear']
        cursor = mysql.connection.cursor()
        cursor.execute(f"SELECT EXTRACT(MONTH FROM w.DataWyp) AS miesiac, COUNT(DISTINCT c.IdCz) AS liczba_czytelnikow FROM `wypozyczenia` AS w INNER JOIN `czytelnicy` AS c ON w.IdCz = c.IdCz WHERE EXTRACT(YEAR FROM w.DataWyp) = %s GROUP BY EXTRACT(MONTH FROM w.DataWyp) ORDER BY EXTRACT(MONTH FROM w.DataWyp);", (chosenYear, ))
        result = cursor.fetchall()
        pdf, col_width, th = setFpdfObject(f'Liczba czytelników w danych miesiącach w roku {chosenYear}', 2)
        
        #headlines
        pdf.cell(col_width, th, "Miesiąc", border=1)
        pdf.cell(col_width, th, "Liczba czytelników", border=1)
        pdf.ln(th)
        
        for row in result:
            pdf.cell(col_width, th, convertNumberToMonth(row[0]), border=1)
            pdf.cell(col_width, th, str(row[1]), border=1)
            pdf.ln(th)
            
        cursor.close()
        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment; filename=raport1.pdf'})
    except BadRequestKeyError:
        return noPermissions()


@app.route("/workerBorrows", methods=['GET', 'POST'])
def workerBorrowsReport():
    try:
        chosenWorker = request.form['workerType']
        cursor = mysql.connection.cursor()
        
        if chosenWorker == 'borrower':
            workerType = "IdPWyd"
            workerName = "wypożyczający"
        else:
            workerType = 'IdPOdb'
            workerName = "odbierający"
            
        cursor.execute(f"SELECT w.IdP AS id_pracownika, w.NazwiskoP AS nazwisko_pracownika, w.ImieP AS imie_pracownika, COUNT(b.{workerType}) AS liczba_wypozyczen FROM `pracownicy` w LEFT JOIN `wypozyczenia` b ON b.{workerType} = w.IdP GROUP BY w.IdP, w.NazwiskoP ORDER BY w.IdP;")
        result = cursor.fetchall() 
        pdf, col_width, th = setFpdfObject(f'Liczba wystapień kazdego pracownika w wypozyczeniach jako {workerName}', 4)
        
        #headlines
        pdf.cell(col_width, th, "ID pracownika", border=1)
        pdf.cell(col_width, th, "Nazwisko pracownika", border=1)
        pdf.cell(col_width, th, "Imię pracownika", border=1)
        pdf.cell(col_width, th, "Liczba wypozyczen", border=1)
        pdf.ln(th)
        
        for row in result:
            pdf.cell(col_width, th, str(row[0]), border=1)
            pdf.cell(col_width, th, row[1], border=1)
            pdf.cell(col_width, th, row[2], border=1)
            pdf.cell(col_width, th, str(row[3]), border=1)
            pdf.ln(th)
            
        cursor.close()
        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment; filename=raport2.pdf'})
    except BadRequestKeyError:
        return noPermissions()



@app.route("/authorBooks", methods=['GET', 'POST'])
def authorBooksReport():
    try:
        chosenAuthor = request.form['allAuthors']
        splittedAuthor = chosenAuthor.strip('()').split(', ')
        tupleAuthor = tuple(splittedAuthor)
        cursor = mysql.connection.cursor()
        cursor.execute(f"SELECT k.Tytul, k.LiczDostEgz FROM ksiazki k JOIN autorstwa a ON k.ISBN = a.ISBN JOIN autorzy aut ON a.IdA = aut.IdA WHERE aut.IdA = %s;", (str(tupleAuthor[0]), ))
        result = cursor.fetchall()
        pdf, col_width, th = setFpdfObject(f'Książki autora {str(tupleAuthor[1])} {str(tupleAuthor[2])} dostępne w bibliotece w podanej liczbie egzemplarzy', 2)
        
        #headlines
        pdf.cell(col_width, th, "Tytuł książki", border=1)
        pdf.cell(col_width, th, "Dostępne egzemplarze", border=1)
        pdf.ln(th)
        
        for row in result:
            print(row)
            pdf.cell(col_width, th, row[0], border=1)
            pdf.cell(col_width, th, str(row[1]), border=1)
            pdf.ln(th) 
            
        cursor.close()
        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment; filename=raport3.pdf'})
    except BadRequestKeyError:
        return noPermissions()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
