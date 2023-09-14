from datetime import datetime


def parse_cp2_data(data: str):
    # "CURRENT LEVEL=005.00, TEMP=-00141., (1) @ =00048. . . .02:22PM JUL 08, 2021"
    data_s = data.split("=")
    t = datetime.strptime(data.split(".")[-1], "%I:%M%p %b %d, %Y")
    lv = float(data_s[1].split(",")[0])
    tp = float(data_s[2].split(",")[0])
    return {'time': t, 'liquid_level': lv, 'temperature': tp}


def parse_cp2_messages(log, error=False):
    if error:
        return [(x[0], x[1]) for x in log if "ERROR" in x[1] and ". . . ." not in x[1]]
    else:
        filter_list = ['COVER CLOSED', 'COVER OPENED', 'AUTO FILL', 'CURRENT LEVEL', 'MANUAL FILL STARTED', 'ERROR']
        return [(log_str[0], log_str[1]) for log_str in log if not any(sub in log_str[1] for sub in filter_list)]