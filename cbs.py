from datetime import datetime

def parse_cbs(data: list):
    if len(cbs_df):
        cbs_df['time'] = cbs_df['time'].dt.tz_localize('Europe/Copenhagen')  # localize to Denmark
    return {'time': datetime.strptime("02:22PM JUL 08, 2021", "%I:%M%p %b %d, %Y"), 'liquid_level': 0, 'temperature': 0}