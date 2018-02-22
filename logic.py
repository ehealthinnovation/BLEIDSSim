import logging
import dbus
import collections
from status import *
from helper import *
from bolus import *
from history import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

flight_mode = 0
therapy_control_state = 0
tbr_adjustment_active = 0
bolus_id = 0
active_bolus_ids = []
active_bolus_delivery = 0
max_bolus = 0
is_priming = 0

def logic_init():
	logger.info('logic init')

'''
IDS Status Reader Control Point
'''
def get_active_bolus_ids():
	logger.info('get_active_bolus_ids')
	global active_bolus_ids
	logger.info(active_bolus_ids)
	return active_bolus_ids


'''
IDS Command Control Point
'''

#TO-DO: if state = the current state, return error or success?
#TO-DO: log history event
def set_therapy_control_state(state):
	global therapy_control_state
	logger.info('set_therapy_control_state')	
	logger.info(state)
	status = get_current_status()
	status.therapy_control_state = state
	result = write_status(status)
	logger.info(result)
	if result == True:
		therapy_control_state = state
	return result

def set_flight_mode(enabled):
	logger.info('set_flight_mode')
	global flight_mode
	flight_mode = enabled

def snooze_annunciation(annunciation_id):
	logger.info('snooze_annunciation')

def confirm_annunciation(annunciation_id):
	logger.info('confirm_annunciation')

def tbr_adjustment_set_active(active):
	logger.info('tbr_adjustment_set_active')
	global tbr_adjustment_active
	tbr_adjustment_active = active

def tbr_adjustment_is_active():
	logger.info('tbr_adjustment_is_active')
	global tbr_adjustment_active
	logger.info(tbr_adjustment_active)
	return tbr_adjustment_active

def set_tbr_adjustment(type, value, duration, context):
	logger.info('set_tbr_adjustment')

def set_tbr_adjustment_using_template(template_number):
	logger.info('set_tbr_adjustment_using_template')

def cancel_tbr_adjustment():
	logger.info('cancel_tbr_adjustment')

def set_bolus_using_template(template_number):
	logger.info('set_bolus_using_template')
	global bolus_id
	bolus_id += 1
	active_bolus_ids.append(bolus_id)
	return bolus_id

def set_bolus(type ,fast_amount, extended_amount, duration, delay_time, activation_type):
	logger.info('set_bolus')
	global bolus_id
	bolus_id += 1
	active_bolus_id = Bolus(bolus_id, type, fast_amount, extended_amount, duration, delay_time, activation_type)
	active_bolus_ids.append(active_bolus_id)
	print(repr(active_bolus_ids))
	return bolus_id

def cancel_bolus(bolus_id):
	logger.info('cancel_bolus')
	for bolus in active_bolus_ids:
		if bolus.number == bolus_id:
			active_bolus_ids.remove(bolus)
			print(repr(active_bolus_ids))
			return True
		else:
			return False

def start_priming(priming_amount):
	logger.info('start priming')
	global is_priming
	is_priming = 1
	# pg.171
	add_history_event(EventType.priming_started, repr(priming_amount))

def stop_priming():
	logger.info('stop priming')
	global is_priming
	logger.info(is_priming)
	if is_priming == 0:
		return False
	else:
		is_priming = 0
		return True

#TO-DO: check if out of range
def set_initial_reservoir_fill_level(fill_level):
	logger.info('set_initial_reservoir_fill_level')
	return True

def reset_reservoir_insulin_operation_time():
	logger.info('reset_reservoir_insulin_operation_time')

def set_max_bolus(amount):
	logger.info('set max bolus')
	global max_bolus
	max_bolus = amount

def get_max_bolus():
	logger.info('get max bolus')
	global max_bolus
	logger.info(max_bolus)
	return max_bolus

