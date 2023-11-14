from flask import Flask, request, render_template
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'sql11.freemysqlhosting.net'
app.config['MYSQL_USER'] = 'sql11661169'
app.config['MYSQL_PASSWORD'] = 'hcJM5mgLXi'
app.config['MYSQL_DB'] = 'sql11661169'

mysql = MySQL(app)


@app.route("/")
def hello_world():
    return render_template('index.html')


@app.route("/login")
def log_in():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/search", methods=['POST'])
def search():
    search_term = request.form.get('searchedBook')
    cursor = mysql.connection.cursor()
    # Modify the SQL query to search for books by title
    cursor.execute("SELECT * FROM `ksiazki` WHERE Tytul LIKE %s", ('%' + search_term + '%',))
    books = cursor.fetchall()
    cursor.close()
    return render_template("search.html", books=books)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
