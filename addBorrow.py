from flask import Blueprint, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField
from wtforms.validators import DataRequired
from datetime import date
from errorsAndCommunicates import *
from loggings import isWorkerLoggedIn

newBorrow = Blueprint("newBorrow", __name__, static_folder="static", template_folder="templates")

class BorrowForm(FlaskForm):
    reader = SelectField('idCz', validators=[DataRequired()])
    book = SelectField('isbn', validators=[DataRequired()])
    borrow_date = DateField('borrowDate', validators=[DataRequired()])
    return_date = DateField('returnDate', validators=[DataRequired()])


@newBorrow.route('/newBorrow', methods=['GET', 'POST'])
def addBorrow():
    from app import mysql, session
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
            return incorrectBorrowDate('newBorrow.addBorrow')
        if return_date < date.today():
            return incorrectReturnDate('newBorrow.addBorrow')
        
        try: #there can be catched exception because LiczDostEgz is optional
            cursor.execute(f'SELECT LiczDostEgz FROM ksiazki WHERE ISBN = {form.book.data}')
            availableBooks = cursor.fetchone()
            
            if availableBooks and availableBooks[0] <= 0:
                flash('Brak wolnych egzemplarzy wybranej książki', 'error')
                return redirect(url_for('newBorrow.addBorrow'))
        except TypeError:
            flash('Nie podano ilości wolnych egzemplarzy tej książki', 'error')
            return redirect(url_for('newBorrow.addBorrow'))
            
        # Insert the borrow record into the database
        cursor.execute(
            'INSERT INTO wypozyczenia (IdCz, ISBN, DataWyp, OczekDataZwr, IdPWyd) VALUES (%s, %s, %s, %s, %s)',
            (form.reader.data, form.book.data, borrow_date, return_date, session.get('id'))
        )
        
        newAvailableBooks = availableBooks[0] - 1
        cursor.execute("UPDATE ksiazki SET LiczDostEgz = %s WHERE ISBN = %s", (newAvailableBooks, form.book.data))
        mysql.connection.commit()

        flash('Dodano pomyślnie', 'success')
        return redirect(url_for('logging.loggedInWorker'))

    return isWorkerLoggedIn('addBorrow.html', form=form)





