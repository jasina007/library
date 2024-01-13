from flask import Blueprint, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired
from datetime import date, datetime
from errorsAndCommunicates import *
from loggings import isWorkerLoggedIn

returningBorrow = Blueprint("returningBorrow", __name__, static_folder="static", template_folder="templates")


class ReturnBorrowForm(FlaskForm):
    borrow = SelectField('borrow', validators=[DataRequired()])
    returnDate = DateField('returnDate', validators=[DataRequired()])
    comments = TextAreaField('comments')


@returningBorrow.route('/returnBorrow', methods=['GET', 'POST'])
def returnBorrow():
    from app import mysql, session
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
        
        cursor.execute(f"SELECT ISBN FROM wypozyczenia WHERE IdWyp = {selected_borrow_id}")
        chosenBorrowIsbn = cursor.fetchone()[0]

        if return_date > date.today():
            flash('Data faktycznego zwrotu nie może być późniejsza od obecnej', 'error')
            return redirect(url_for('returningBorrow.returnBorrow'))
        if return_date < borrow_date:
            flash('Data faktycznego zwrotu nie może być wcześniejsza od daty wypożyczenia ', 'error')
            return redirect(url_for('returningBorrow.returnBorrow'))

        # Insert the borrow record into the database
        sql = "UPDATE wypozyczenia SET FaktDataZwr = %s, Uwagi = %s, IdPOdb = %s WHERE IdWyp = %s"
        cursor.execute(
            sql, (form.returnDate.data, form.comments.data, session.get("id"), selected_borrow_id)
        )
        
        #change number of available books(plus 1)
        cursor.execute(f"UPDATE ksiazki SET LiczDostEgz = LiczDostEgz + 1 WHERE ISBN = {chosenBorrowIsbn}")
        mysql.connection.commit()

        flash('Dodano pomyślnie', 'success')
        return redirect(url_for('logging.loggedInWorker'))

    return isWorkerLoggedIn('returnBorrow.html', form=form)