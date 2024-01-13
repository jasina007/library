from flask import flash, redirect, url_for, Blueprint

errors = Blueprint("errors", __name__, static_folder="static", template_folder="templates")

def incorrectBorrowDate(urlTo):
    flash('Data wypożyczenia nie może być późniejsza od obecnej', 'error')
    return redirect(url_for(urlTo))

def incorrectReturnDate(urlTo):
    flash('Data zwrotu nie może być wcześniejsza od obecnej', 'error')
    return redirect(url_for(urlTo))

def incorrectLogging():
    flash('Wprowadzono niepoprawny email lub hasło')
    return redirect(url_for('logging.log_in'))

def noPermissions():
    flash("Nie posiadasz odpowiednich uprawnień. Zaloguj się.")
    return redirect(url_for('logging.log_in'))

def noSearchParameters():
    flash("Nie podano danych do wyszukania książki.")
    return redirect(url_for('hello_world'))
