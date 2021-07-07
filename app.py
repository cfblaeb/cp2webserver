from flask import Flask, request

app = Flask(__name__)
data_log = "data_log.txt"


@app.route('/')
def hello_world():
    with open(data_log) as fi:
        return {'data': fi.readlines()}


@app.post('/new_data')
def new_data():
    if request.json and isinstance(request.json, dict) and 'data' in request.json:  # check that data is not null and that its a dictionary and that it has a key named data
        with open(data_log, 'at') as fi:
            fi.write(request.json['data'] + "\n")
    return "thanks"


if __name__ == '__main__':
    app.run()
