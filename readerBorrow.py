from flask import Blueprint
from loggings import isReaderLoggedIn

readerBorrow = Blueprint("readerBorrow", __name__, static_folder="static", template_folder="templates")

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


@readerBorrow.route("/readerBorrows")
def readerBorrows():
    from app import session, mysql
    idCz = session.get('id')
    cursor = mysql.connection.cursor()
    cursor.execute(
    "SELECT k.Tytul, w.DataWyp, w.OczekDataZwr, w.FaktDataZwr FROM `wypozyczenia` AS w INNER JOIN `ksiazki` AS k ON w.ISBN = k.ISBN WHERE w.IdCz = %s",  (idCz,))
    borrows = cursor.fetchall()
    cursor.close()
    borrows = setNoneToUserMessage(borrows)
    return isReaderLoggedIn("readerBorrows.html", borrows=borrows)