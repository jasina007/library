from flask import Blueprint, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField
from wtforms.validators import DataRequired
from errorsAndCommunicates import *
from loggings import isReaderLoggedIn

extensionBorrow = Blueprint("extensionBorrow", __name__, static_folder="static", template_folder="templates")

class ExtendBorrowForm(FlaskForm):
    borrow = SelectField('borrow', validators=[DataRequired()])
    newReturnDate = DateField('newReturnDate', validators=[DataRequired()])

    
@extensionBorrow.route("/extendBorrow", methods=['GET', 'POST'])
def extendBorrow():
    from app import mysql, session
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
            return redirect(url_for('extensionBorrow.extendBorrow'))
        if newReturnDate <= selected_borrow[3]:
            flash('Nowa data musi być późniejsza', 'error')
            return redirect(url_for('extensionBorrow.extendBorrow'))

        # Insert the borrow record into the database
        sql = "UPDATE wypozyczenia SET OczekDataZwr = %s WHERE IdWyp = %s"
        cursor.execute(
            sql, (newReturnDate, selected_borrow_id)
        )
        mysql.connection.commit()

        flash('Przedłużono pomyślnie', 'success')
        return redirect(url_for('logging.loggedIn'))

    return isReaderLoggedIn('extendBorrow.html', form=form)
