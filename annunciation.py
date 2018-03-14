import logging
from db import *
from history import *

counter = 0

class Annunciation(Base):
	__tablename__ = 'annunciations'

	id = Column(Integer, primary_key=True)
	annunciation_id = Column(Integer, unique=True)
	annunciation_type = Column(Integer)
	status = Column(Integer)

	def __str__(self):
		return "<Annunciation(annunciation_id,='%s', annunciation_type='%s', status='%s')>" % (
			self.annunciation_id, self.annunciation_type, self.status)

class AnnunciationTypeValues(object):
	system_issue = 0x000F
	mechanical_issue = 0x0033
	occlusion_detected = 0x003C
	reservoir_issue	= 0x0055
	reservoir_empty	= 0x005A
	reservoir_low = 0x0066
	priming_issue = 0x0069
	infusion_set_incomplete = 0x0096
	infusion_set_detached = 0x0099
	power_source_insufficient = 0x00A5
	battery_empty = 0x00AA
	battery_low = 0x00C3
	battery_medium = 0x00CC
	battery_full = 0x00F0
	temperature_out_of_range = 0x00FF
	air_pressure_out_of_range = 0x0303
	bolus_cancelled = 0x030C
	tbr_over = 0x0330
	tbr_cancelled = 0x033F
	max_delivery = 0x0356
	date_time_issue = 0x0359
	temperature = 0x0365

class AnnunciationStatusValues(object):
	undetermined = 0x0F
	pending = 0x33
	snoozed = 0x3C
	confirmed = 0x55

def annunciation_init():
	global counter
	logger.info('annunciation_init')
	last_counter_value = get_last_counter_value()
	if last_counter_value is not None:
		counter = last_counter_value + 1
	
def get_last_counter_value():
	logger.info('get_next_counter_value')
	row_count = get_row_count(Annunciation)
	if row_count == 0:
		return None
	else:
		last_row = get_last_row(Annunciation)
		return last_row.annunciation_id

def write_annunciation(annunciation_type, status):
	logger.info('write_annunciation')
	global counter
	result = add_entry(Annunciation(annunciation_id = counter,
						  			annunciation_type = annunciation_type,
						  			status = status))
	if result is True:
		counter += 1
	else:
		logger.info('error writing annunciation')

	return result

# TO-DO: get last unconfirmed annunciation?
def get_annunciation(annunciation_id):
	logger.info('get_annunciation')
	logger.info(annunciation_id)
	annunciation =  get_row_for_object(Annunciation, Annunciation.annunciation_id, annunciation_id)
	print(repr(annunciation))
	return annunciation

def get_latest_annunciation():
	logger.info('get_latest_annunciation')
	logger.info(counter)
	annunciation =  get_last_row_for_object(Annunciation, Annunciation.annunciation_id, counter-1)
	logger.info(annunciation)
	return annunciation

def set_annunciation_status(annunciation_id, status):
	logger.info('set_annunciation_status')
	update_arbitrary_row(Annunciation, 'annunciation_id', str(annunciation_id), 'status', status)
	annunciation = get_row_for_object(Annunciation, Annunciation.annunciation_id, annunciation_id)

	history_data = [0, annunciation.annunciation_id, annunciation.annunciation_type, annunciation.status]
	add_history_event(EventType.annunciation_status_changed_1_of_2, history_data)
	return True

'''
def snooze_annunciation(annunciation_id):
	logger.info('snooze_annuncation')
	result = update_arbitrary_row(Annunciation, 'annunciation_id', str(annunciation_id), 'snoozed', 1)
	return result

def confirm_annunciation(annunciation_id):
	logger.info('confirm_annuncation')
	result = update_arbitrary_row(Annunciation, 'annunciation_id', str(annunciation_id), 'confirmed', 1)
	return result
'''

