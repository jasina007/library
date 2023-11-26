try:
        if request.method == 'POST':
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            phone = request.form['phone']
            email = request.form['email']
            password = request.form['password']

            cursor = mysql.connection.cursor()
            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor.execute("INSERT INTO czytelnicy (ImieCz, NazwiskoCz, NrTel, Email, Haslo) VALUES (%s, %s, %s, %s, %s)",
                        (first_name, last_name, phone, email, hashed_password))
            mysql.connection.commit()
            cursor.close()
            flash('Your account has been created!', 'success')
            return redirect(url_for('log_in'))
    except IntegrityError:
        flash('Your e-mail was used in another account! Please enter not used e-mail', 'error')
        return redirect(url_for('register'))
    return render_template("register.html")