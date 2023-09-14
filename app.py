import pandas as pd
from flask import Flask, request, render_template
from sqlite3 import connect
from datetime import datetime, timedelta

from config import db_name
from cp2 import parse_cp2_messages, parse_cp2_data
from cbs import parse_cbs

app = Flask(__name__)


@app.route('/')
def hello_world():
    con = connect(db_name)
    cur = con.cursor()
    # get data 30 days back
    content = list(cur.execute("SELECT * FROM data WHERE date >= date(?) ORDER BY date DESC", (datetime.now()-timedelta(days=30), )))
    cur.close()
    con.close()

    cp2_df = pd.DataFrame([parse_cp2_data(x[1]) for x in content if x[1].startswith("CURRENT LEVEL") and x[2] == 0])
    if len(cp2_df):
        cp2_df['time'] = cp2_df['time'].dt.tz_localize('Europe/Copenhagen')  # localize to Denmark

    cbs_data, cbs_error_log, cbs_rest = parse_cbs([x for x in content if x[2] == 1])

    return render_template(
        'main.html',
        cp2_log=parse_cp2_messages(content, 0),
        cp2_error_log=parse_cp2_messages(content, 0, True),
        cp2_ll=cp2_df[['time', 'liquid_level']].rename(columns={'time': 'x', 'liquid_level': 'y'}).to_json(orient='records') if len(cp2_df) else [],
        cp2_tt=cp2_df[['time', 'temperature']].rename(columns={'time': 'x', 'temperature': 'y'}).to_json(orient='records') if len(cp2_df) else [],

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
