import logging
from db import *
from response import *
from statusChanged import *
from datatypes import *
from timeHelper import *
from datetime import timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

counter = 0

class Event(Base):
	__tablename__ = 'events'

	id = Column(Integer, primary_key=True)
	event = Column("Event", Integer)
	sequence = Column("Sequence", Integer, unique=True)
	relative_offset = Column("Offset", Integer)
	data = Column("Data", String(1024))

	def __repr__(self):
		return "<Event(event='%s', sequence='%s', data='%s')>" % (
			self.event, self.sequence, self.data)

class EventType(object):
	reference_time = 0x000F
	reference_time_base_offset = 0x0033
	bolus_calculated_1_of_2 = 0x003C
	bolus_calculated_2_of_2	= 0x0055
	bolus_programmed_1_of_2	= 0x005A
	bolus_programmed_2_of_2 = 0x0066
	bolus_delivered_1_of_2 = 0x0069
	bolus_delivered_2_of_2 = 0x0096
	delivered_basal_rate_changed = 0x0099
	tbr_adjustment_started = 0x00A5
	tbr_adjustment_ended = 0x00AA
	tbr_adjustment_changed = 0x00C3
	profile_template_activated = 0x00CC
	basal_rate_profile_template_time_block_changed = 0x00F0
	total_daily_insulin_delivery = 0x00FF
	therapy_control_state_changed = 0x0303
	operational_state_changed = 0x030C
	reservoir_remaining_amount_changed = 0x0330
	annunciation_status_changed_1_of_2 = 0x033F
	annunciation_status_changed_2_of_2 = 0x0356
	isf_profile_template_time_block_changed = 0x0359
	i2cho_ratio_profile_template_time_block_changed = 0x0365
	target_glucose_range_profile_template_time_block_changed = 0x036A
	priming_started = 0x0395
	priming_done = 0x39A
	data_corruption = 0x03A6
	pointer_event = 0x03A9
	bolus_template_changed_1_of_2 = 0x03C0
	bolus_template_changed_2_of_2 = 0x03CF
	tbr_template_changed = 0x03F3
	max_bolus_amount_changed = 0x03FC
	
def history_init():
	global counter
	logger.info('history_init')
	last_counter_value = get_last_counter_value()
	if last_counter_value is not None:
		counter = last_counter_value + 1

def get_latest_reference_time():
	logger.info('get_latest_reference_time')
	last_ref_event = get_last_row_for_object_with_value(Event, Event.event, EventType.reference_time)
	print(repr(last_ref_event))
	return last_ref_event

def get_last_counter_value():
	logger.info('get_next_counter_value')
	row_count = get_row_count(Event)
	if row_count == 0:
		return None
	else:
		last_row = get_last_row(Event)
		return last_row.sequence

def add_history_event(event_type, event_data):
	global counter
	logger.info('add_history_event')
	logger.info(event_type)
	logger.info(event_data)
	offset = get_latest_time_offset()
	add_entry(Event(event = event_type, relative_offset = offset, sequence = counter, data = event_data))
	counter += 1
	update_status_changed(0x80)

def get_history_count():
	logger.info('get_history_count')
	count = get_row_count(Event)
	return count

def report_all_history_events():
	logger.info('report_all_history_events')
	data = []
	rows = get_all_rows(Event)
	print(repr(rows))

	for row in rows:
		data = []
		data.append(dbus.Byte(row.event & 0xff))
		data.append(dbus.Byte(row.event >> 8))
		data.append(dbus.Byte(row.sequence & 0xff))
		data.append(dbus.Byte(row.sequence >> 8))
		data.append(dbus.Byte(row.sequence >> 16))
		data.append(dbus.Byte(row.sequence >> 24))
		data.append(dbus.Byte(row.relative_offset & 0xff))
		data.append(dbus.Byte(row.relative_offset >> 8))
		event_data = row.data
		event_bytes = [event_data[i:i+2] for i in range(0,len(event_data), 2)]
		for event_data_byte in event_bytes[::-1]:
			data.append(dbus.Byte(int(event_data_byte, 16)))
		packet = build_response_packet(None, data)
		send_response(IDSServiceCharacteristics.history, packet)

	data = []
	data.append(dbus.Byte(RecordAccessControlPointOpCodes.report_stored_records))
	data.append(dbus.Byte(RecordAccessControlPointResponseCodes.success))
	packet = build_response_packet(RecordAccessControlPointOpCodes.response_code, data)
	send_response(IDSServiceCharacteristics.racp, packet)

def get_latest_time_offset():
	latest_time_reference = get_latest_reference_time()
	if latest_time_reference is None:
		return 0

	latest_time_data = latest_time_reference.data[2:]
	latest_time_date = date_hex_to_datetime(latest_time_data)
	print(latest_time_date)
	now = datetime.now()
	print(now)
	time_difference = now - latest_time_date
	time_difference_in_minutes = time_difference / timedelta(seconds=1)
	print(int(time_difference_in_minutes))
	return(int(time_difference_in_minutes))
