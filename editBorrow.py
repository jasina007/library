from flask import request, Blueprint, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField
from wtforms.validators import DataRequired, Optional
from datetime import date
from errorsAndCommunicates import *
from loggings import isWorkerLoggedIn

editionBorrow = Blueprint("editionBorrow", __name__, static_folder="static", template_folder="templates")

class EditBorrowForm(FlaskForm):
    borrow = SelectField('borrow', validators=[DataRequired()])
    readerId = SelectField('readerId', validators=[DataRequired()])
    bookISBN = SelectField('bookISBN', validators=[DataRequired()])
    borrowDate = DateField('borrowDate', validators=[Optional()])
    returnDate = DateField('returnDate', validators=[Optional()])


@editionBorrow.route('/editBorrow', methods=['GET', 'POST'])
def editBorrow():
    from app import mysql
    cursor = mysql.connection.cursor()

    # Fetch existing books from the database
    cursor.execute('''SELECT w.IdWyp, c.ImieCz, c.NazwiskoCz, c.IdCz, k.Tytul, w.DataWyp, w.OczekDataZwr FROM wypozyczenia w JOIN czytelnicy c ON w.IdCz = c.IdCz JOIN ksiazki k ON w.ISBN = k.ISBN ORDER BY w.IdWyp''')
    borrows= [(borrow[0], f"{borrow[0]} - {borrow[1]} {borrow[2]} {borrow[3]}- {borrow[4]} - {borrow[5]} - {borrow[6]}") for borrow in cursor.fetchall()]
    
    cursor.execute('SELECT IdCz, ImieCz, NazwiskoCz FROM czytelnicy')
    readers = [(str(reader[0]), f"{reader[1]} {reader[2]} - {str(reader[0])}") for reader in cursor.fetchall()]
    
    cursor.execute('SELECT ISBN, Tytul FROM ksiazki')
    books = [(book[0], f"{book[1]} - {book[0]}") for book in cursor.fetchall()]

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
            return redirect(url_for('logging.loggedInWorker'))

        idWyp = form.borrow.data
        idCz = form.readerId.data
        isbn = form.bookISBN.data
        dataWyp = form.borrowDate.data
        oczekDataZwr = form.returnDate.data
        
        cursor.execute(f'SELECT ISBN FROM wypozyczenia WHERE IdWyp = %s', (idWyp,))
        isbnFromChosenBorrow = cursor.fetchone()
        
        try: #there can be catched exception because LiczDostEgz is optional
                cursor.execute(f'SELECT LiczDostEgz FROM ksiazki WHERE ISBN = {isbn}')
                availableBooks = cursor.fetchone()
                
                if availableBooks and availableBooks[0] <= 0 and isbn != isbnFromChosenBorrow[0]:
                    flash('Brak wolnych egzemplarzy wybranej książki', 'error')
                    return redirect(url_for('editionBorrow.editBorrow'))
        except TypeError:
                flash('Nie podano ilości wolnych egzemplarzy tej książki', 'error')
                return redirect(url_for('editionBorrow.editBorrow'))
        
        
        if dataWyp != None and oczekDataZwr != None:
            if dataWyp > date.today():
                return incorrectBorrowDate('editionBorrow.editBorrow')
            if oczekDataZwr < date.today():
                return incorrectReturnDate('editionBorrow.editBorrow')
            
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
        
        '''
        if isbn != isbnFromChosenBorrow[0]:  
            newAvailableBooks = availableBooks[0] - 1
            cursor.execute("UPDATE ksiazki SET LiczDostEgz = %s WHERE ISBN = %s", (newAvailableBooks, isbn)) '''
        
        mysql.connection.commit()
        flash('Zedytowano pomyślnie wypożyczenie', 'success')
        return redirect(url_for('logging.loggedInWorker'))

    return isWorkerLoggedIn('editBorrow.html', form=form)