import logging
from datatypes import *
from timer import *
import time
from bolus import *
import ids
from statusChanged import *
from status import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bolus_delivery_interval = 1
bolus_delivery_amount_remaining = None
bolus_delivery_rate = None
bolus_timer = None
active_bolus_id = None

total_delivered_bolus = 0
total_delivered_basal = 0

full_reservoir_amount = 180

def post_bolus_delivery():
	logger.info('DONE')
	
def deliver_single_shot_bolus(amount):
	logger.info('deliver_single_shot_bolus')
	logger.info(amount)
	global total_delivered_bolus
	total_delivered_bolus += amount
	update_status_changed(80)
	update_status('reservoir_remaining_amount', (full_reservoir_amount - total_delivered_bolus - total_delivered_basal))

def deliver_extended_bolus(bolus_id, amount, duration):
	global bolus_delivery_amount_remaining
	global bolus_delivery_rate
	global bolus_timer

	logger.info('deliver_extended_bolus')
	rate = round(amount/duration, 2)
	
	bolus_delivery_amount_remaining = amount
	bolus_delivery_rate = rate
	bolus_timer = perpetualTimer(bolus_delivery_interval, deliver_bolus, bolus_id, post_bolus_delivery)
	bolus_timer.start()
	update_status_changed(64)

def deliver_bolus(bolus_id):
	logger.info('deliver_bolus')
	global bolus_delivery_amount_remaining
	global bolus_delivery_rate
	global total_delivered_bolus
	if bolus_delivery_amount_remaining < bolus_delivery_rate:
		bolus_delivery_amount_remaining = 0
	else:
		bolus_delivery_amount_remaining = bolus_delivery_amount_remaining - bolus_delivery_rate
	
	logger.info(round(bolus_delivery_amount_remaining,2))
	logger.info(ids.q)
	#update_bolus_remaining_amount(bolus_id, bolus_delivery_amount_remaining)
	total_delivered_bolus += bolus_delivery_rate
	if bolus_delivery_amount_remaining <= 0:
		logger.info('total_delivered_bolus')
		logger.info(total_delivered_bolus)
		update_status_changed(80)
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