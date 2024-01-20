from flask import request, Blueprint, render_template
from errorsAndCommunicates import noSearchParameters
from loggings import isReaderLoggedIn, isWorkerLoggedIn

searchings = Blueprint("searchings", __name__, static_folder="static", template_folder="templates")

def search(path):
    from app import mysql
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

def search(path):
    from app import mysql
    try:
        search_term = request.form.get('searchedBook')
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                k.Tytul, k.RokWyd, k.Wydawnictwo, k.LiczDostEgz, k.ISBN, a.ImieA, a.NazwiskoA
            FROM 
                ksiazki k
            JOIN 
                autorstwa ka ON k.ISBN = ka.ISBN
            JOIN 
                autorzy a ON ka.IdA = a.IdA
            WHERE 
                k.Tytul LIKE %s
            ORDER BY 
                a.NazwiskoA
        """, ('%' + search_term + '%',))
        books = cursor.fetchall()
        cursor.close()
        return render_template("search.html", books=books, path=path)
    except TypeError:
        return noSearchParameters()



@searchings.route("/search", methods=['GET', 'POST'])
def searchForAll():
    return search("/")

@searchings.route("/searchWorker", methods=['GET', 'POST'])
def searchForWorker():
    return search("/loggedUser/worker")

@searchings.route("/searchReader", methods=['GET', 'POST'])
def searchForReader():
    return search("/loggedUser/reader")


@searchings.route("/searchBookWorker")
def searchWorker():
    return isWorkerLoggedIn("searchBookWorker.html")


@searchings.route("/searchBookReader")
def searchReader():
    return isReaderLoggedIn("searchBookReader.html")