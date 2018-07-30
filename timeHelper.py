import time
from datetime import datetime

def current_time_to_hex():
	now = datetime.now()
	year_hex = hex(now.year)[2:].zfill(4)
	time_zone_byte = int((time.altzone / 3600) * 60)
	time_data = ''.join(reversed([year_hex[i:i+2] for i in range(0, len(year_hex), 2)])) + hex(now.month)[2:].zfill(2) + hex(now.day)[2:].zfill(2) + hex(now.hour)[2:].zfill(2) + hex(now.minute)[2:].zfill(2) + hex(now.second)[2:].zfill(2) + hex(time_zone_byte)[2:] + str(time.daylight).zfill(2)
	return time_data

def date_hex_to_datetime(value):
	year = value[0:4]
	year =''.join(reversed([year[i:i+2] for i in range(0, len(year), 2)]))
	year = int(year, 16)
	date = datetime(year, int(value[4:6], 16), int(value[6:8], 16), int(value[8:10], 16), int(value[10:12], 16), int(value[12:14], 16))
	return date
