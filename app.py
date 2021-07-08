from flask import Flask, request
from sqlite3 import connect

app = Flask(__name__)


@app.route('/')
def hello_world():
    con = connect("cp2s_data.sqlite")
    cur = con.cursor()
    content = [x for x in cur.execute("SELECT * FROM data")]
    con.close()
    return {'data': content}


@app.post('/new_data')
def new_data():
    if request.json and isinstance(request.json, dict) and 'data' in request.json:  # check that data is not null and that its a dictionary and that it has a key named data
        con = connect("cp2s_data.sqlite")
        cur = con.cursor()
        cur.execute("INSERT INTO data VALUES (?, ?)", (request.json['date'], request.json['data']))
        con.commit()
        con.close()
    return "thanks"


if __name__ == '__main__':
    app.run()
