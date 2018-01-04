import logging
from db import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

counter = 0

class Event(Base):
	__tablename__ = 'events'

	id = Column(Integer, primary_key=True)
	event = Column(Integer)
	sequence = Column(Integer, unique=True)
	offset = Column(Integer)
	data = Column(Text)

	def __repr__(self):
		return "<Event(event='%s', sequence='%s', offset='%s', data='%s')>" % (
			self.event, self.sequence, self.offset, self.data)

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
	db_init()
	get_latest_reference_time()
	last_counter_value = get_last_counter_value()
	if last_counter_value is not None:
		counter = last_counter_value + 1
	# otherwise, counter remains at zero
	print(repr(counter))

#this is called once at startup to get the last reference time
def get_latest_reference_time():
	logger.info('get_latest_reference_time')
	last_ref_event = get_last_event(Event, Event.event, EventType.reference_time)
	print(repr(last_ref_event))

#this should be called once at startup for better performance
def get_last_counter_value():
	logger.info('get_next_counter_value')
	row_count = get_row_count(Event)
	if row_count == 0:
		return None
	else:
		last_row = get_last_row(Event)
		return last_row.sequence
	
#sequence number and offset should be automatically handled
def add_event(event_type, event_data):
	global counter
	logger.info('add_event')
	add_entry(Event(event = event_type, sequence = counter, offset = 0, data = event_data))
	counter += 1


