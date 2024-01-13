import hashlib

from flask import Flask, request, render_template, session, flash, redirect, url_for, Response, Blueprint
from flask_mysqldb import MySQL
from loggings import isWorkerLoggedIn, isReaderLoggedIn

changePasswords = Blueprint("changePasswords", __name__, static_folder="static", template_folder="templates")

def changePassword(tableName, urlForPassword, keyAttributeName, urlForMainPage):
    from app import mysql
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


@changePasswords.route("/changeReaderPassword", methods=['GET', 'POST'])
def changeReaderPassword():
    if request.method == 'POST':
        return changePassword('czytelnicy', 'changePasswords.changeReaderPassword', 'IdCz', 'logging.loggedIn')
    return isReaderLoggedIn("changeReaderPassword.html")


@changePasswords.route("/changeWorkerPassword", methods=['GET', 'POST'])
def changeWorkerPassword():
    if request.method == 'POST':
        return changePassword('pracownicy', 'changePasswords.changeWorkerPassword', 'IdP','logging.loggedInWorker')
    return isWorkerLoggedIn("changeWorkerPassword.html")
