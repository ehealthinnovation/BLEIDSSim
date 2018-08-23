import logging
import dbus
import collections
from status import *
from helper import *
from bolus import *
from history import *
from annunciation import *
from delivery import *
from datatypes import *
from statusChanged import *
from template import *
from response import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

flight_mode = 0
tbr_adjustment_active = 0
bolus_id = 0
active_bolus_delivery = 0
max_bolus = 0
is_priming = 0

def logic_init():
	logger.info('logic init')

'''
IDS Command Control Point
'''
def set_therapy_control_state(state):
	global therapy_control_state
	logger.info('set_therapy_control_state')	
	status = get_current_status()
	previous_therapy_control_state = status.therapy_control_state
	
	print(hex(previous_therapy_control_state)[2:])
	print(hex(state)[2:])
	history_data = str(hex(status.therapy_control_state)[2:]) + str(hex(state)[2:])

	update_status_changed(1)
	update_status('therapy_control_state', state)
	
	print(repr(history_data))
	add_history_event(EventType.therapy_control_state_changed, history_data)
	return True
	
def set_flight_mode(enabled):
	logger.info('set_flight_mode')
	global flight_mode
	flight_mode = enabled

def snooze_annunciation(annunciation_id):
	logger.info('snooze_annunciation')
	set_annunciation_status(annunciation_id, AnnunciationStatusValues.snoozed)
	
def confirm_annunciation(annunciation_id):
	logger.info('confirm_annunciation')
	set_annunciation_status(annunciation_id, AnnunciationStatusValues.confirmed)

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

def activate_templates(templates):
	logger.info('activate_templates')
	logger.info(templates)
	
	for template in templates:
		logger.info(template.template_number)
		result = activate_template(template.template_number)
		
	return result

def bolus_delivery_complete():
	logger.info('bolus_delivery_complete')

def set_bolus(bolus_type ,fast_amount, extended_amount, duration, delay_time, template_number, activation_type):
	logger.info('set_bolus')
	bolus_id = get_next_available_bolus_id()
	store_bolus(bolus_id, bolus_type, fast_amount, extended_amount, duration, delay_time, template_number, activation_type, 1)
	if bolus_type is BolusType.fast:
		deliver_single_shot_bolus(fast_amount)
	if bolus_type is BolusType.extended:
		deliver_extended_bolus(bolus_id, extended_amount, duration)

	return bolus_id

def cancel_bolus(bolus_id):
	logger.info('cancel_bolus')
	logger.info(bolus_id)
	active_bolus_ids = get_active_bolus_ids()
	print('currently active bolus ids: ', active_bolus_ids)
	for bolus in active_bolus_ids:
		if bolus.bolus_id == bolus_id:
			deactivate_bolus(bolus_id)
			print('FOUND BOLUS TO CANCEL')
			print(repr(bolus))
			return True
	print('no active bolus ids match provided bolus id')
	return False

def start_priming(priming_amount):
	logger.info('start priming')
	global is_priming
	is_priming = 1

def stop_priming():
	logger.info('stop priming')
	global is_priming
	logger.info(is_priming)
	if is_priming == 0:
		return False
	else:
		is_priming = 0
		return True

def set_initial_reservoir_fill_level(fill_level):
	logger.info('set_initial_reservoir_fill_level')
	return True

def reset_reservoir_insulin_operation_time():
	logger.info('reset_reservoir_insulin_operation_time')

def set_max_bolus(amount):
	logger.info('set max bolus')
	global max_bolus
	old_max_bolus_amount = max_bolus
	max_bolus = amount
	history_data = [old_max_bolus_amount, max_bolus]
	add_history_event(EventType.max_bolus_amount_changed, history_data)

def get_max_bolus():
	logger.info('get max bolus')
	global max_bolus
	logger.info(max_bolus)
	return max_bolus

