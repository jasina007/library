from flask import request, Blueprint, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, IntegerField
from wtforms.validators import DataRequired, Optional
from loggings import isWorkerLoggedIn

books = Blueprint("books", __name__, static_folder="static", template_folder="templates")

@books.route("/newBook", methods=['GET', 'POST'])
def newBook():
    from app import mysql
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
        return redirect(url_for('logging.loggedInWorker'))
    return isWorkerLoggedIn("addBook.html")


class EditBookForm(FlaskForm):
    book = SelectField('isbn', validators=[DataRequired()])
    author = SelectField('author', validators=[DataRequired()])
    title = StringField('title', validators=[Optional()])
    year = IntegerField('year', validators=[Optional()])
    publisher = StringField('publisher', validators=[Optional()])
    available_copies = IntegerField('available_copies', validators=[Optional()])


@books.route('/editBook', methods=['GET', 'POST'])
def edit_book():
    from app import mysql
    cursor = mysql.connection.cursor()

    # Fetch existing books from the database
    cursor.execute("SELECT k.ISBN, k.Tytul, k.RokWyd, k.Wydawnictwo, k.LiczDostEgz, a.ImieA, a.NazwiskoA FROM ksiazki k JOIN autorstwa auth ON k.ISBN = auth.isbn JOIN autorzy a ON auth.IdA = a.IdA;")
    books = [(book[0], f"{book[0]} - {book[1]} - {book[2]} - {book[3]} - {book[4]} - {book[5]} {book[6]}") for book in cursor.fetchall()]
    
    cursor.execute('SELECT IdA, NazwiskoA, ImieA FROM autorzy')
    authors = [(author[0], f"{author[0]} - {author[1]} - {author[2]}") for author in cursor.fetchall()]

    form = EditBookForm()
    form.book.choices = books
    form.author.choices = authors

    if form.validate_on_submit():

        if 'delete_book' in request.form and request.form['delete_book'] == 'true':
            # Delete the book record from the database
            isbn_to_delete = form.book.data
            cursor.execute('DELETE FROM autorstwa WHERE ISBN = %s', (isbn_to_delete,))
            cursor.execute('DELETE FROM wypozyczenia WHERE ISBN = %s', (isbn_to_delete,))
            cursor.execute('DELETE FROM ksiazki WHERE ISBN = %s', (isbn_to_delete,))
            mysql.connection.commit()

            flash('Książka została usunięta pomyślnie', 'success')
            return redirect(url_for('logging.loggedInWorker'))

        isbn = form.book.data
        idA = form.author.data
        title = form.title.data
        rokwyd = form.year.data
        wydawnictwo = form.publisher.data
        liczdostegz = form.available_copies.data
        
        #below checking is necessary when title is optional field
        #and in this case it must be optional for easier deleting
        if title == "":
            flash('Należy podać tytuł edytowanej książki', 'error')
            return redirect(url_for('books.edit_book'))
            
        # Update the book record in the database
        cursor.execute('UPDATE ksiazki SET Tytul = %s, RokWyd = %s, Wydawnictwo = %s, LiczDostEgz = %s WHERE ISBN = %s',
                       (title, rokwyd, wydawnictwo, liczdostegz, isbn))
        cursor.execute('UPDATE autorstwa SET IdA = %s WHERE ISBN = %s', (idA, isbn))
        mysql.connection.commit()

        flash('Dodano pomyślnie', 'success')
        return redirect(url_for('logging.loggedInWorker'))

    return isWorkerLoggedIn('editBook.html', form=form)
