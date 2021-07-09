import pandas as pd
from flask import Flask, request, render_template
from sqlite3 import connect
from datetime import datetime

app = Flask(__name__)


def parse_temp_level_data(data):
    # "CURRENT LEVEL=005.00, TEMP=-00141., (1) @ =00048. . . .02:22PM JUL 08, 2021"
    data_s = data.split("=")
    t = datetime.strptime(data.split(".")[-1], "%I:%M%p %b %d, %Y")
    lv = float(data_s[1].split(",")[0])
    tp = float(data_s[2].split(",")[0])
    return {'time': t, 'liquid_level': lv, 'temperature': tp}


@app.route('/')
def hello_world():
    con = connect("cp2s_data.sqlite")
    cur = con.cursor()
    content = list(cur.execute("SELECT * FROM data"))
    cur.close()
    con.close()
    da = [parse_temp_level_data(x[1]) for x in content if x[1].startswith("CURRENT LEVEL")]
    df = pd.DataFrame(da)
    return render_template(
        'main.html',
        log=content,
        ll=df[['time', 'liquid_level']].rename(columns={'time': 'x', 'liquid_level': 'y'}).to_json(orient='records'),
        tt=df[['time', 'temperature']].rename(columns={'time': 'x', 'temperature': 'y'}).to_json(orient='records')
    )


@app.post('/new_data')
def new_data():
    # check that data is not null and that its a dictionary and that it has a key named data
    if request.json and isinstance(request.json, dict) and 'data' in request.json:
        con = connect("cp2s_data.sqlite")
        cur = con.cursor()
        cur.execute("INSERT INTO data VALUES (?, ?)", (datetime.now(), request.json['data']))
        con.commit()
        cur.close()
        con.close()
    return "thanks"
