from datetime import datetime
from pandas import DataFrame, Series


def parse_cp2_data(data: Series):
	# "CURRENT LEVEL=005.00, TEMP=-00141., (1) @ =00048. . . .02:22PM JUL 08, 2021"
	data_s = data.data.split("=")
	t = datetime.strptime(data.data.split(".")[-1].strip(), "%I:%M%p %b %d, %Y")
	lv = float(data_s[1].split(",")[0])
	tp = float(data_s[2].split(",")[0])
	return Series({'time': t, 'liquid_level': lv, 'temperature': tp})


def parse_cp2(data: DataFrame):
	cp2_df = data[data.data.str.startswith("CURRENT LEVEL")].apply(parse_cp2_data, axis=1)
	cp2_df['time'] = cp2_df['time'].dt.tz_localize('Europe/Copenhagen')  # localize to Denmark

	# errors have two lines.
	# Line 1: "ERROR # (11) @ =00417. . . . . . . . . . . . . . . . . 09:19PM SEP 14, 2023"
	# Line 2: "FILL ERROR - LIQUID TEMPERATURE IS ABOVE SET LIMIT."
	error_data = data[data.data.str.contains("ERROR")]
	cp2_error_log = error_data.groupby(error_data.reset_index(drop=True).index // 2).apply(lambda x: Series([x.iloc[0].data.split(".")[-1].strip(), x.iloc[1].data])).values.tolist()
	cp2_error_log.reverse()

	# get remaining log data
	rest_data = data[(~data.data.str.startswith("CURRENT LEVEL")) & (~data.data.str.contains("ERROR")) & (data.data.str.contains("@"))].sort_values(by='date', ascending=False)
	cp2_rest = rest_data.apply(lambda x: Series([x.data.split(".")[-1], x.data.split(".")[0]]), axis=1).values.tolist()

	return cp2_df, cp2_error_log, cp2_rest


def parse_cbs(data: DataFrame):
	# data comes in 4 lines
	# 14 September 2023 15:00	TANK ID: 1
	# TEMP-A: -183 *C
	# TEMP-B: -192 *C
	# Liquid Level: 39.8 CM
	# I will identify the Liquid Level Line and then assume the previous 3 lines belong to that block.
	data = data.reset_index(drop=True).data
	llids = data[data.str.contains('Liquid Level:')].index

	cbs_data = []
	for i in llids:
		try:
			date = datetime.strptime(data.loc[i - 3].split("\t")[0], "%d %B %Y %H:%M")
			temp = int(data.loc[i - 2].split(" ")[1])
			other_temp = data.loc[i - 1]  # cbs captures bottom and top temp...I don't care
			ll = float(data.loc[i].split(" ")[2])
			cbs_data.append({'time': date, 'temperature': temp, 'liquid_level': ll})
		except ValueError as e:
			pass

	cbs_df = DataFrame(cbs_data)
	cbs_df['time'] = cbs_df['time'].dt.tz_localize('Europe/Copenhagen')  # localize to Denmark

	# find the latest "report" and use that for all errors
	# REPORT DONE BY ________________________________________
	# blank line
	# blank line
	# blank line
	# line-n
	# line-2
	# line-1
	# blank line
	# -----
	# HISTORY
	his_ind = data[data == 'HISTORY'].index[-1]
	rdb_ind = data[data.str.startswith("REPORT DONE BY")].index[-1]
	log_data = data.loc[his_ind+3:rdb_ind-4]
	massaged_log_data = log_data.apply(lambda x: Series([" ".join(x.split(" ")[-4:]), " ".join(x.split(" ")[:-4])])).values.tolist()

	# examples of alarms:
	# TEMP-A. HIGH 27 June 2023 12:43
	# LOW ALARM 10 September 2023 21:56
	# SYSTEM POWER OFF 05 September 2023 11:15
	alarm_data = log_data[log_data.str.contains("ALARM") | log_data.str.contains("POWER") | log_data.str.contains("HIGH")]
	massaged_alarm_data = alarm_data.apply(lambda x: Series([" ".join(x.split(" ")[-4:]), " ".join(x.split(" ")[:-4])])).values.tolist()

	return cbs_df, massaged_alarm_data, massaged_log_data
