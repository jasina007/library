from flask import Flask
from flask import render_template
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'sql11.freemysqlhosting.net'
app.config['MYSQL_USER'] = 'sql11661169'
app.config['MYSQL_PASSWORD'] = 'hcJM5mgLXi'
app.config['MYSQL_DB'] = 'sql11661169'

mysql = MySQL(app)


@app.route("/")
def hello_world():  
    return render_template('home.html')

@app.route("/login")
def log_in():
    return render_template("login.html", code=302)

@app.route("/register")
def register():
    return render_template("register.html", code=302)

@app.route("/search")
def search():
    cursor = mysql.connection.cursor()
    cursor.execute(''' SELECT * FROM `autorzy` ''')
    data = cursor.fetchall()
    mysql.connection.commit()
    cursor.close()
    print(data)
    return render_template("search.html", code=302)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)