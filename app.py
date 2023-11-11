from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template('home.html')

@app.route("/login")
def log_in():
    return render_template("login.html", code=302)

@app.route("/register")
def register():
    return render_template("register.html", code=302)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)