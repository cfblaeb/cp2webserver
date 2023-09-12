import pandas as pd
from flask import Flask, request, render_template
from sqlite3 import connect
from datetime import datetime, timedelta

app = Flask(__name__)
freezers = {'cp2': 0, 'cbs': 1}


def parse_temp_level_data(data: str, freezer: int):
    if freezer == 0:  # cp2
        # "CURRENT LEVEL=005.00, TEMP=-00141., (1) @ =00048. . . .02:22PM JUL 08, 2021"
        data_s = data.split("=")
        t = datetime.strptime(data.split(".")[-1], "%I:%M%p %b %d, %Y")
        lv = float(data_s[1].split(",")[0])
        tp = float(data_s[2].split(",")[0])
        return {'time': t, 'liquid_level': lv, 'temperature': tp}
    elif freezer == 1:  # cbs
        return {'time': datetime.strptime("02:22PM JUL 08, 2021", "%I:%M%p %b %d, %Y"), 'liquid_level': 0, 'temperature': 0}


def filter_log_output(log, freezer: int, error=False):
    if freezer == 0:  # cp2
        if error:
            return [x for x in log if "ERROR" in x[1] and ". . . ." not in x[1]]
        else:
            filter_list = ['COVER CLOSED', 'COVER OPENED', 'AUTO FILL', 'CURRENT LEVEL', 'MANUAL FILL STARTED', 'ERROR']
            return [log_str for log_str in log if not any(sub in log_str[1] for sub in filter_list)]
    elif freezer == 1:  # cbs
        return ["no", "errors"]


@app.route('/')
def hello_world():
    con = connect("cp2s_data.sqlite")
    cur = con.cursor()
    # get data 30 days back
    content = list(cur.execute("SELECT * FROM data WHERE date >= date(?) ORDER BY date DESC", (datetime.now()-timedelta(days=30), )))
    cur.close()
    con.close()

    cp2_df = pd.DataFrame([parse_temp_level_data(x[1], 0) for x in content if x[1].startswith("CURRENT LEVEL") and x[2]==0])
    cp2_df['time'] = cp2_df['time'].dt.tz_localize('Europe/Copenhagen')  # localize to Denmark

    cbs_df = pd.DataFrame([parse_temp_level_data(x[1], 1) for x in content if x[1].startswith("CURRENT LEVEL") and x[2]==1])
    if len(cbs_df):
        cbs_df['time'] = cbs_df['time'].dt.tz_localize('Europe/Copenhagen')  # localize to Denmark

    return render_template(
        'main.html',
        cp2_log=filter_log_output(content, 0),
        cp2_error_log=filter_log_output(content, 0, True),
        cp2_ll=cp2_df[['time', 'liquid_level']].rename(columns={'time': 'x', 'liquid_level': 'y'}).to_json(orient='records'),
        cp2_tt=cp2_df[['time', 'temperature']].rename(columns={'time': 'x', 'temperature': 'y'}).to_json(orient='records'),

        cbs_log=filter_log_output(content, 1),
        cbs_error_log=filter_log_output(content, 1, True),
        cbs_ll=cbs_df[['time', 'liquid_level']].rename(columns={'time': 'x', 'liquid_level': 'y'}).to_json(orient='records') if len(cbs_df) else None,
        cbs_tt=cbs_df[['time', 'temperature']].rename(columns={'time': 'x', 'temperature': 'y'}).to_json(orient='records') if len(cbs_df) else None
    )


@app.post('/new_data')
def new_data():
    # check that data is not null and that it's a dictionary and that it has a key named data
    if request.json and isinstance(request.json, dict) and 'data' in request.json:
        con = connect("cp2s_data.sqlite")
        cur = con.cursor()
        cur.execute("INSERT INTO data VALUES (?, ?, ?)", (datetime.now(), request.json['data'], request.json['freezer']))
        con.commit()
        cur.close()
        con.close()
    return "thanks"
