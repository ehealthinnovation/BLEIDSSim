import logging
from datatypes import *
from timer import *
import time
from bolus import *
import ids
from statusChanged import *
from status import *
import threading
from history import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bolus_delivery_interval = 2
bolus_delivery_amount_remaining = None
bolus_delivery_rate = None
bolus_timer = None
active_bolus_id = None

total_delivered_bolus = 0
total_delivered_basal = 0

full_reservoir_amount = 180

def update_reservoir_remaining_amount(remaining_amount):
	logger.info('update_reservoir_remaining_amount' + str(remaining_amount))
	update_status('reservoir_remaining_amount', remaining_amount)
	reservoir_remaining_data = str(format(float_to_shortfloat(remaining_amount), 'x'))
	history_data = reservoir_remaining_data
	add_history_event(EventType.reservoir_remaining_amount_changed, history_data)

def post_bolus_delivery():
	logger.info('Delivery Complete')
	
def deliver_single_shot_bolus(amount):
	logger.info('deliver_single_shot_bolus')
	logger.info(amount)
	update_status_changed(64)
	global total_delivered_bolus
	total_delivered_bolus += amount
	update_status_changed(80)
	update_reservoir_remaining_amount(full_reservoir_amount - total_delivered_bolus - total_delivered_basal)
	#update_status('reservoir_remaining_amount', (full_reservoir_amount - total_delivered_bolus - total_delivered_basal))

def deliver_extended_bolus(bolus_id, amount, duration):
	global bolus_delivery_amount_remaining
	global bolus_delivery_rate
	global bolus_timer
	global target_reservoir_amount

	logger.info('deliver_extended_bolus')
	bolus_delivery_rate = round(amount/duration, 1)
	logger.info('Rate: %f', amount/duration)
	logger.info('Rounded rate: %f', bolus_delivery_rate)
	logger.info('Amount: %f', amount)
	logger.info('Duration: %f', duration)
	
	bolus_delivery_amount_remaining = amount
	update_status_changed(64)
	bolus_timer = perpetualTimer(bolus_delivery_interval, deliver_bolus, bolus_id, post_bolus_delivery)
	bolus_timer.start()

def deliver_bolus(bolus_id):
	logger.info('deliver_bolus')
	global bolus_delivery_amount_remaining
	global bolus_delivery_rate
	global total_delivered_bolus

	if bolus_delivery_rate > bolus_delivery_amount_remaining:
		bolus_delivery_rate = bolus_delivery_amount_remaining

	total_delivered_bolus += bolus_delivery_rate
	bolus_delivery_amount_remaining -= bolus_delivery_rate
	
	update_status_changed(80)
	update_reservoir_remaining_amount(round(full_reservoir_amount - total_delivered_bolus - total_delivered_basal, 1))
	#update_status('reservoir_remaining_amount', round(full_reservoir_amount - total_delivered_bolus - total_delivered_basal, 1))
	
	logger.info('Bolus Delivery Amount Remaining: %f', bolus_delivery_amount_remaining)
	if bolus_delivery_amount_remaining == 0:
		return False
	else:
		return True

def cancel_bolus_delivery():
	logger.info('cancel_bolus_delivery')
	if bolus_timer is not None:
		bolus_timer.cancel()

def cancel_all_delivery():
	logger.info('cancel_all_delivery')
	cancel_bolus_delivery()
