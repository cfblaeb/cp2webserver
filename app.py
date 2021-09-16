import pandas as pd
from flask import Flask, request, render_template
from sqlite3 import connect
from datetime import datetime, timedelta

app = Flask(__name__)


def parse_temp_level_data(data):
    # "CURRENT LEVEL=005.00, TEMP=-00141., (1) @ =00048. . . .02:22PM JUL 08, 2021"
    data_s = data.split("=")
    t = datetime.strptime(data.split(".")[-1], "%I:%M%p %b %d, %Y")
    lv = float(data_s[1].split(",")[0])
    tp = float(data_s[2].split(",")[0])
    return {'time': t, 'liquid_level': lv, 'temperature': tp}


def filter_log_output(log, error=False):
    if error:
        return [x for x in log if "ERROR" in x[1] and ". . . ." not in x[1]]
    else:
        filter_list = ['COVER CLOSED', 'COVER OPENED', 'AUTO FILL', 'CURRENT LEVEL', 'MANUAL FILL STARTED', 'ERROR']
        return [log_str for log_str in log if not any(sub in log_str[1] for sub in filter_list)]


@app.route('/')
def hello_world():
    con = connect("cp2s_data.sqlite")
    cur = con.cursor()
    # get data 30 days back
    content = list(cur.execute("SELECT * FROM data WHERE date >= date(?) ORDER BY date DESC", (datetime.now()-timedelta(days=30), )))
    cur.close()
    con.close()
    df = pd.DataFrame([parse_temp_level_data(x[1]) for x in content if x[1].startswith("CURRENT LEVEL")])
    df['time'] = df['time'].dt.tz_localize('Europe/Copenhagen')  # localize to Denmark
    return render_template(
        'main.html',
        log=filter_log_output(content),
        error_log=filter_log_output(content, True),
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
