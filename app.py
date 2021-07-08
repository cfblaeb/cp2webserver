from flask import Flask, request, render_template
from sqlite3 import connect
from datetime import datetime

app = Flask(__name__)


@app.route('/')
def hello_world():
    con = connect("cp2s_data.sqlite")
    cur = con.cursor()
    content = [[datetime.fromtimestamp(x[0]/1000), x[1]] for x in cur.execute("SELECT * FROM data")]
    con.close()

    return render_template('main.html', data=content)


@app.post('/new_data')
def new_data():
    if request.json and isinstance(request.json, dict) and 'data' in request.json:  # check that data is not null and that its a dictionary and that it has a key named data
        con = connect("cp2s_data.sqlite")
        cur = con.cursor()
        cur.execute("INSERT INTO data VALUES (?, ?)", (datetime.now(), request.json['data']))
        con.commit()
        con.close()
    return "thanks"
