from flask import Flask, request, render_template
from sqlite3 import connect
from datetime import datetime, timedelta
from pandas import DataFrame, to_datetime
from config import db_name
from parsers import parse_cp2, parse_cbs

app = Flask(__name__)


@app.route('/')
def hello_world():
    con = connect(db_name)
    cur = con.cursor()
    # get data 30 days back
    content = DataFrame(cur.execute("SELECT * FROM data WHERE date >= date(?) ORDER BY date DESC", (datetime.now()-timedelta(days=30), )), columns=['date', 'data', 'freezer'])
    cur.close()
    con.close()
    content['date'] = to_datetime(content['date']).dt.tz_localize('Europe/Copenhagen')  # localize to Denmark
    content = content.sort_values('date')

    cp2_data, cp2_error_log, cp2_rest = parse_cp2(content[content.freezer == 0])
    cbs_data, cbs_error_log, cbs_rest = parse_cbs(content[content.freezer == 1])

    return render_template(
        'main.html',
        cp2_log=cp2_rest,
        cp2_error_log=cp2_error_log,
        cp2_ll=cp2_data[['time', 'liquid_level']].rename(columns={'time': 'x', 'liquid_level': 'y'}).to_json(orient='records') if len(cp2_data) else [],
        cp2_tt=cp2_data[['time', 'temperature']].rename(columns={'time': 'x', 'temperature': 'y'}).to_json(orient='records') if len(cp2_data) else [],

        cbs_log=cbs_rest,
        cbs_error_log=cbs_error_log,
        cbs_ll=cbs_data[['time', 'liquid_level']].rename(columns={'time': 'x', 'liquid_level': 'y'}).to_json(orient='records') if len(cbs_data) else [],
        cbs_tt=cbs_data[['time', 'temperature']].rename(columns={'time': 'x', 'temperature': 'y'}).to_json(orient='records') if len(cbs_data) else []
    )


@app.post('/new_data')
def new_data():
    # check that data is not null and that it's a dictionary and that it has a key named data
    if request.json and isinstance(request.json, dict) and 'data' in request.json:
        con = connect(db_name)
        cur = con.cursor()
        cur.execute("INSERT INTO data VALUES (?, ?, ?)", (datetime.now(), request.json['data'], request.json['freezer']))
        con.commit()
        cur.close()
        con.close()
    return "thanks"
