import hashlib

from MySQLdb import IntegrityError
from flask import Flask, request, render_template, session, flash, redirect, url_for, Blueprint
from flask_mysqldb import MySQL

registration = Blueprint("registration", __name__, static_folder="static", template_folder="templates")

@registration.route("/register")
def register():
    return render_template("register.html")



@registration.route("/register", methods=['GET', 'POST'])
def registering():
    from app import mysql
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
            flash('Utworzono konto pomyślnie!', 'success')
            return redirect(url_for('logging.log_in'))
        return render_template("register.html")
    except IntegrityError:
        flash('Twój e-mail został użyty już w innym koncie! Użyj innego e-maila.', 'error')
        return redirect(url_for('registration.register'))