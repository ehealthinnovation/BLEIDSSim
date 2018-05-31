'''
IDS Simulator v1.0
--
History events not supported in this version:
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
	total_daily_insulin_delivery = 0x00FF
	operational_state_changed = 0x030C
	annunciation_status_changed_1_of_2 = 0x033F
	annunciation_status_changed_2_of_2 = 0x0356
	bolus_template_changed_1_of_2 = 0x03C0
	bolus_template_changed_2_of_2 = 0x03CF
'''

import logging
import dbus
import collections
import threading

from datetime import datetime
from logic import *
from helper import *
from crc import *
from shortfloat import *
from config import *
from history import *
from template import *
from annunciation import *
from status import *
from statusChanged import *
from bolus import *
from service import *
from datatypes import *
from basal import *
from response import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

time_zone = 0
dst = 0
crc_counter = 0


def parser_init():
	logger.info('parser_init')
	db_init()
	history_init()
	annunciation_init()
	check_if_date_time_set()
	set_default_status()
	status_changed_init()
	template_init()
	time_zone = 0
	dst = 0
	

def set_default_status():
	logger.info('set_default_status')
	reservoir_remaining = float_to_shortfloat(full_reservoir_amount)
	write_status(Status(therapy_control_state = TherapyControlState.stop,
						operational_state = OperationalState.standby,
						reservoir_remaining_amount = reservoir_remaining,
						reservoir_attached = 1))

#TO-DO: check if an unconfirmed date-time issue already exists
def check_if_date_time_set():
	date_time = get_latest_reference_time()
	if date_time is None:
		print("date time not set!")
		write_annunciation(AnnunciationTypeValues.date_time_issue, AnnunciationStatusValues.pending)

def crc_counter_is_valid():
	return True

def crc_is_valid(value):
	packet_len = len(value)

	packet_crc = value[packet_len-2:packet_len]
	packet_crc = ''.join(map(lambda b: format(b, "02x"), packet_crc))
	
	packet_data = value[0:packet_len-2]
	calculated_crc = hex(crc_calculate(packet_data))[2:].zfill(4)
	calculated_crc = "".join(reversed([calculated_crc[i:i+2] for i in range(0, len(calculated_crc), 2)]))
	
	if calculated_crc == packet_crc:
		logger.info('crc passed')
		return True
	else:
		logger.info('crc failed')
		return False

	return False


def get_ids_status():
	logger.info('get ids status')
	
	status = get_current_status()
	data = []
	print(status)

	if status is None:
		logger.info('status not found')
		return None
	else:
		logger.info('status found')
		reservoir_remaining = float_to_shortfloat(status.reservoir_remaining_amount)
		
		data.append(dbus.Byte(status.therapy_control_state))
		data.append(dbus.Byte(status.operational_state))
		data.append(dbus.Byte(reservoir_remaining & 0xff))
		data.append(dbus.Byte(reservoir_remaining >> 8))
		data.append(dbus.Byte(status.reservoir_attached))
		packet = build_response_packet(None, data)
		return packet

def get_ids_status_changed():
	logger.info('get_ids_status_changed')
	
	status_changed = get_current_status_changed()
	data = []
	status_dict = status_changed.as_dict()
	ids_status = 0

	if status_changed is None:
		logger.info('status changed not found')
		return None
	else:
		logger.info('status changed found')	
		
		for key in status_dict:
			if status_dict[key] == 1:
				ids_status = set_bit(ids_status, int(list(status_dict.keys()).index(key)))
		data = [dbus.Byte(ids_status & 0xff), 
				dbus.Byte(ids_status >> 8)]
		packet = build_response_packet(None, data)
		print(repr(packet))
		return packet

def get_ids_features():
	logger.info('get ids features')
	ids_features = 0
	features = 0

	dict_features = get_dict('features', 'FEATURES')
	logger.info(dict_features)

	for key in dict_features:
		if dict_features[key] == '1':
			ids_features = set_bit(ids_features, int(list(dict_features.keys()).index(key)))
	
	features = [ids_features & 0xff, ids_features >> 8, 0x00]
	insulin_concentration = float_to_shortfloat(0.01)
	features.insert(0, insulin_concentration & 0xff)
	features.insert(1, insulin_concentration >> 8)

	features.insert(0, 0)

	crc = crc_calculate(features)	
	features.insert(0, crc & 0xff)
	features.insert(1, crc >> 8)
	return features


def get_ids_annunciation_status():
	logger.info('get_ids_annunciation_status')
	
	annunciation = get_latest_annunciation()
	print(annunciation)

	data = []
	data.append(dbus.Byte(0x01)) #flags
	data.append(dbus.Byte(annunciation.annunciation_id & 0xff))
	data.append(dbus.Byte(annunciation.annunciation_id >> 8))
	data.append(dbus.Byte(annunciation.annunciation_type & 0xff))
	data.append(dbus.Byte(annunciation.annunciation_type >> 8))
	data.append(dbus.Byte(annunciation.status))
	packet = build_response_packet(None, data)

	print(repr(packet))
	
	return packet
	

'''
If the Reset Status Op Code is written to the IDD Status Reader Control Point with an Operand containing a Flags field, 
the Server shall reset the status exposed by the IDD Status Changed characteristic.

The Server shall confirm the status reset by indicating the IDD Status Reader Control Point with a Response Code Op Code, 
a Request Op Code of Reset Status and Response Code Value of Success.
'''
def parse_ids_status_reader_control_point(value):
	logger.info('parse ids status reader control point')
	response = []

	if crc_is_valid(value) == False or crc_counter_is_valid() == False: 
		return None

	opcode = bytes_to_int16(value[0:2][::-1])

	if opcode == StatusReaderOpCodes.reset_status:
		response = handle_reset_status(value)
		return response
	elif opcode == StatusReaderOpCodes.get_active_bolus_ids:
		response = handle_get_active_bolus_ids()
		return response
	elif opcode == StatusReaderOpCodes.get_active_bolus_delivery:
		response = handle_get_active_bolus_delivery(value)
		return response
	elif opcode == StatusReaderOpCodes.get_active_basal_rate_delivery:
		response = handle_get_active_basal_rate_delivery()
		return response
	elif opcode == StatusReaderOpCodes.get_total_daily_insulin_status:
		response = handle_get_total_daily_insulin_status()
		return response
	elif opcode == StatusReaderOpCodes.get_counter:
		response = handle_get_counter(value)
		return response
	elif opcode == StatusReaderOpCodes.get_delivered_insulin:
		response = handle_get_delivered_insulin()
		return response
	elif opcode == StatusReaderOpCodes.get_insulin_on_board:
		response = handle_get_insulin_on_board()
		return response
		

def handle_reset_status(value):
	logger.info("handle_reset_status")
	data = []
	status_changed_reset()

	logger.info("handle_reset_status - 2")
	data.append(dbus.Byte(StatusReaderOpCodes.reset_status & 0xff))
	data.append(dbus.Byte(StatusReaderOpCodes.reset_status >> 8))
	data.append(dbus.Byte(ResponseCodes.success))
	packet = build_response_packet(StatusReaderOpCodes.response_code, data)
	logger.info("handle_reset_status - send response")
	send_response(IDSServiceCharacteristics.status_reader_control_point, packet)


def handle_get_active_bolus_ids():
	logger.info("get_active_bolus_ids")
	data = []

	active_bolus_ids = get_active_bolus_ids()
	logger.info(len(active_bolus_ids))

	if len(active_bolus_ids) > 7:
		logger.info('TO-DO: support >7 active bolus ids')
		return

	if len(active_bolus_ids) == 0:
		logger.info('no active bolus ids')
		data.append(dbus.Byte(StatusReaderOpCodes.get_active_bolus_ids & 0xff))
		data.append(dbus.Byte(StatusReaderOpCodes.get_active_bolus_ids >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(StatusReaderOpCodes.response_code, data)
	else:
		logger.info('building active bolus ids packet')
		data.append(dbus.Byte(len(active_bolus_ids)))
		for x in range(len(active_bolus_ids)):
			logger.info(active_bolus_ids[x])
			data.append(dbus.Byte(active_bolus_ids[x].bolus_id & 0xff))
			data.append(dbus.Byte(active_bolus_ids[x].bolus_id >> 8))
		packet = build_response_packet(StatusReaderOpCodes.get_active_bolus_ids_response, data)
	send_response(IDSServiceCharacteristics.status_reader_control_point, packet)


def handle_get_active_bolus_delivery(value):
	logger.info('handle_get_active_bolus_delivery')
	data = []

	bolus_id = bytes_to_int16(value[2:4][::-1])
	logger.info(bolus_id)
	bolus_value_selection = value[4]
	logger.info(bolus_value_selection)

	bolus = get_bolus(bolus_id)
	logger.info(bolus)

	if (bolus is None) or (bolus.active == 0):
		logger.info('bolus does not exist or is not active')
		data.append(dbus.Byte(CommandControlOpCodes.get_active_basal_rate_delivery & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.get_active_basal_rate_delivery >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
		packet = build_response_packet(StatusReaderOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.status_reader_control_point, packet)
		return

	if (bolus_value_selection == BolusValueSelection.programmed) or (bolus_value_selection == BolusValueSelection.remaining) or (bolus_value_selection == BolusValueSelection.delivered):
		logger.info('')
	else:
		logger.info('bolus value selection is not valid')
		data.append(dbus.Byte(CommandControlOpCodes.get_active_basal_rate_delivery & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.get_active_basal_rate_delivery >> 8))
		data.append(dbus.Byte(ResponseCodes.invalid_operand))
		packet = build_response_packet(StatusReaderOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.status_reader_control_point, packet)
		return
	
	'''
	If the Bolus Value Selection Operand is set to Delivered and the Bolus Delay Time field is present (i.e., Bolus Delay Time Present bit is set in Flags field), the Server shall set the Bolus Delay Time field to 0xFFFF to signal that the Bolus Delay Time is not applicable with that Bolus Value Selection Operand.
	'''
	if bolus_value_selection is BolusValueSelection.delivered:
		if(is_set(bolus.flags, BolusFlags.bolus_delay_time_present_bit)):
			bolus.delay_time = 0xFFFF

	'''
	If the Bolus Type within the Active Bolus Delivery record is set to “Fast”, the Server shall set the Bolus Duration and the Bolus Extended Amount to 0.
	'''
	if bolus.bolus_type is BolusType.fast:
		bolus.duration = 0
		bolus.extended_amount = 0

	'''
	If the Bolus Type within the Active Bolus Delivery record is set to “Extended”, the Server shall set the Bolus Fast Amount to 0.
	'''
	if bolus is BolusType.extended:
		bolus.fast_amount = 0

	bolus_fast_amount = float_to_shortfloat(bolus.fast_amount)
	bolus_extended_amount = float_to_shortfloat(bolus.extended_amount)

	data.append(dbus.Byte(bolus.flags))
	data.append(dbus.Byte(bolus.bolus_id & 0xff))
	data.append(dbus.Byte(bolus.bolus_id >> 8))
	data.append(dbus.Byte(bolus.bolus_type))
	data.append(dbus.Byte(bolus_fast_amount & 0xff))
	data.append(dbus.Byte(bolus_fast_amount >> 8))
	data.append(dbus.Byte(bolus_extended_amount & 0xff))
	data.append(dbus.Byte(bolus_extended_amount >> 8))
	data.append(dbus.Byte(bolus.duration & 0xff))
	data.append(dbus.Byte(bolus.duration >> 8))
	
	if(is_set(bolus.flags, BolusFlags.bolus_delay_time_present_bit)):
		data.append(dbus.Byte(bolus.delay_time & 0xff))
		data.append(dbus.Byte(bolus.delay_time >> 8))
	
	if(is_set(bolus.flags, BolusFlags.bolus_template_number_present_bit)):
		data.append(dbus.Byte(bolus.template_number))
	
	if(is_set(bolus.flags, BolusFlags.bolus_activation_type_present_bit)):
		data.append(dbus.Byte(bolus.activation_type))
	
	packet = build_response_packet(StatusReaderOpCodes.get_active_bolus_delivery_response, data)
	send_response(IDSServiceCharacteristics.status_reader_control_point, packet)
	return


def handle_get_active_basal_rate_delivery():
	logger.info('handle_get_active_basal_rate_delivery')
	
	flags = 0
	data = []

	templates_in_range = get_rows_with_range(TemplateLookup, TemplateLookup.template_number, TemplateRange.basal_rate_profile_template_range[0], (TemplateRange.basal_rate_profile_template_range[0] + len(TemplateRange.basal_rate_profile_template_range)))
	logger.info(templates_in_range)

	for template in templates_in_range:
		if template.active == 1:
			logger.info('found activated template number: ' + str(template.template_number))
			basal_template = get_template_details(template.template_number)
			logger.info(basal_template)
			
			first_rate = float_to_shortfloat(basal_template.first_rate)

			data.append(dbus.Byte(flags))
			data.append(dbus.Byte(basal_template.template_number))
			data.append(dbus.Byte(first_rate & 0xff))
			data.append(dbus.Byte(first_rate >> 8))

			#TO-DO: check if a TBR is active, add to packet if so
			packet = build_response_packet(StatusReaderOpCodes.get_active_basal_rate_delivery_response, data)
			send_response(IDSServiceCharacteristics.status_reader_control_point, packet)
			return

	'''
	If there is no currently active basal rate, the Server shall indicate the IDD Status Reader Control Point with a Response Code Op Code, a Request Op Code of
	Get Active Basal Rate Delivery, and a Response Code Value in the Operand set to Procedure not applicable.
	'''
	logger.info('no active basal rate delivery')

	data.append(dbus.Byte(StatusReaderOpCodes.get_active_basal_rate_delivery & 0xff))
	data.append(dbus.Byte(StatusReaderOpCodes.get_active_basal_rate_delivery >> 8))
	data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
	packet = build_response_packet(StatusReaderOpCodes.response_code, data)
	send_response(IDSServiceCharacteristics.status_reader_control_point, packet)
	return


def handle_get_total_daily_insulin_status():
	logger.info('handle_get_total_daily_insulin_status')
	data = []

	total_daily_insulin_sum_of_bolus_delivered = float_to_shortfloat(total_delivered_bolus)
	data.append(dbus.Byte(total_daily_insulin_sum_of_bolus_delivered & 0xff))
	data.append(dbus.Byte(total_daily_insulin_sum_of_bolus_delivered >> 8))

	total_daily_insulin_sum_of_basal_delivered = float_to_shortfloat(total_delivered_basal)
	data.append(dbus.Byte(total_daily_insulin_sum_of_basal_delivered & 0xff))
	data.append(dbus.Byte(total_daily_insulin_sum_of_basal_delivered >> 8))

	total_daily_insulin_sum_of_bolus_and_basal_delivered = float_to_shortfloat(total_delivered_bolus + total_delivered_basal)
	data.append(dbus.Byte(total_daily_insulin_sum_of_bolus_and_basal_delivered & 0xff))
	data.append(dbus.Byte(total_daily_insulin_sum_of_bolus_and_basal_delivered >> 8))

	packet = build_response_packet(StatusReaderOpCodes.get_total_daily_insulin_status_response, data)
	send_response(IDSServiceCharacteristics.status_reader_control_point, packet)

def handle_get_counter(value):
	logger.info('handle_get_counter')
	data = []

	counter_type = value[2]
	counter_value_selection = value[3]

	data.append(dbus.Byte(counter_type))
	data.append(dbus.Byte(counter_value_selection))

	# counter value (minutes)
	data.append(dbus.Byte(0x00))
	data.append(dbus.Byte(0x00))
	data.append(dbus.Byte(0x00))
	data.append(dbus.Byte(0x05))

	packet = build_response_packet(StatusReaderOpCodes.get_counter_response, data)
	send_response(IDSServiceCharacteristics.status_reader_control_point, packet)

def handle_get_delivered_insulin():
	logger.info('handle_get_delivered_insulin')
	data = []

	bolus = bytearray(struct.pack("f", total_delivered_bolus))
	data.append(dbus.Byte(bolus[3]))
	data.append(dbus.Byte(bolus[2]))
	data.append(dbus.Byte(bolus[1]))
	data.append(dbus.Byte(bolus[0]))
	
	basal = bytearray(struct.pack("f", total_delivered_basal))
	data.append(dbus.Byte(basal[3]))
	data.append(dbus.Byte(basal[2]))
	data.append(dbus.Byte(basal[1]))
	data.append(dbus.Byte(basal[0]))

	packet = build_response_packet(StatusReaderOpCodes.get_delivered_insulin_response, data)
	send_response(IDSServiceCharacteristics.status_reader_control_point, packet)

def handle_get_insulin_on_board():
	logger.info('handle_get_insulin_on_board')
	data = []

	data.append(dbus.Byte(0x01)) #flags
	
	insulin_onboard = float_to_shortfloat(2.05)
	data.append(insulin_onboard & 0xff)
	data.append(insulin_onboard >> 8)

	minutes_remaining = 10
	data.append(minutes_remaining & 0xff)
	data.append(minutes_remaining >> 8)
	
	packet = build_response_packet(StatusReaderOpCodes.get_insulin_on_board_response, data)
	send_response(IDSServiceCharacteristics.status_reader_control_point, packet)


def parse_ids_command_control_point(value):
	logger.info('parse_ids_command_control_point')
	response = []

	if crc_is_valid(value) == False or crc_counter_is_valid() == False: 
		return None

	opcode = bytes_to_int16(value[0:2][::-1])

	if opcode == CommandControlOpCodes.set_therapy_control_state:
		response = handle_set_therapy_control_state(value)
		return response
	elif opcode == CommandControlOpCodes.set_flight_mode:
		response = handle_set_flight_mode()
		return response
	elif opcode == CommandControlOpCodes.snooze_annunciation:
		response = handle_snooze_annunciation(value)
		return response
	elif opcode == CommandControlOpCodes.confirm_annunciation:
		response = handle_confirm_annunciation(value)
		return response
	elif opcode == CommandControlOpCodes.read_basal_rate_profile_template:
		response = handle_read_basal_rate_profile_template(value)
		return response
	elif opcode == CommandControlOpCodes.write_basal_rate_profile_template:
		response = handle_write_basal_rate_profile_template(value)
		return response
	elif opcode == CommandControlOpCodes.set_tbr_adjustment:
		response = handle_set_tbr_adjustment(value)
		return response
	elif opcode == CommandControlOpCodes.cancel_tbr_adjustment:
		response = handle_cancel_tbr_adjustment()
		return response
	elif opcode == CommandControlOpCodes.get_tbr_template:
		response = handle_get_tbr_template(value)
		return response
	elif opcode == CommandControlOpCodes.set_tbr_template:
		response = handle_set_tbr_template(value)
		return response
	elif opcode == CommandControlOpCodes.set_bolus:
		response = handle_set_bolus(value)
		return response
	elif opcode == CommandControlOpCodes.cancel_bolus:
		response = handle_cancel_bolus(value)
		return response
	elif opcode == CommandControlOpCodes.get_available_boluses:
		response = handle_get_available_boluses()
		return response
	elif opcode == CommandControlOpCodes.get_bolus_template:
		response = handle_get_bolus_template(value)
		return response
	elif opcode == CommandControlOpCodes.set_bolus_template:
		response = handle_set_bolus_template(value)
		return response
	elif opcode == CommandControlOpCodes.get_template_status_and_details:
		response = handle_get_template_status_and_details()
		return response
	elif opcode == CommandControlOpCodes.reset_template_status:
		response = handle_reset_template_status(value)
		return response
	elif opcode == CommandControlOpCodes.activate_profile_templates:
		response = handle_activate_profile_templates(value)
		return response
	elif opcode == CommandControlOpCodes.get_activated_profile_templates:
		response = handle_get_activated_profile_templates()
		return response
	elif opcode == CommandControlOpCodes.start_priming:
		response = handle_start_priming(value)
		return response
	elif opcode == CommandControlOpCodes.stop_priming:
		response = handle_stop_priming()
		return response
	elif opcode == CommandControlOpCodes.set_initial_reservoir_fill_level:
		response = handle_set_initial_reservoir_fill_level(value)
		return response
	elif opcode == CommandControlOpCodes.reset_reservoir_insulin_operation_time:
		response = handle_reset_reservoir_insulin_operation_time()
		return responsels
	elif opcode == CommandControlOpCodes.read_isf_profile_template:
		response = handle_read_isf_profile_template(value)
		return response
	elif opcode == CommandControlOpCodes.write_isf_profile_template:
		response = handle_write_isf_profile_template(value)
		return response
	elif opcode == CommandControlOpCodes.read_i2cho_ratio_profile_template:
		response = handle_read_i2cho_ratio_profile_template(value)
		return response
	elif opcode == CommandControlOpCodes.write_i2cho_ratio_profile_template:
		response = handle_write_i2cho_ratio_profile_template(value)
		return response
	elif opcode == CommandControlOpCodes.read_target_glucose_range_profile_template:
		response = handle_read_target_glucose_range_profile_template(value)
		return response
	elif opcode == CommandControlOpCodes.write_target_glucose_range_profile_template:
		response = handle_write_target_glucose_range_profile_template(value)
		return response
	elif opcode == CommandControlOpCodes.get_max_bolus_amount:
		response = handle_get_max_bolus_amount()
		return response
	elif opcode == CommandControlOpCodes.set_max_bolus_amount:
		response = handle_set_max_bolus_amount(value)
		return response

def handle_set_therapy_control_state(value):
	logger.info('set_therapy_control_state')
	data = []
	state = value[2]
	status = get_current_status()
	
	current_state = hex(status.therapy_control_state)[2:]
	new_state = hex(state)[2:]
	print(repr(current_state))
	print(repr(new_state))
	
	'''
	If the therapy control state could not be set in the current application context (e.g., the Therapy Control State is set to Run although there is no inserted insulin reservoir), the Server shall indicate the IDD Command Control Point with a Response Code Op Code, a Request Op Code of Set Therapy Control State, and a Response Code Value in the Operand set to Procedure not applicable.
	'''
	if (state == TherapyControlState.run) and (status.reservoir_attached == 0):
		logger.info('can not set therapy state to run, reservoir not attached')
		data.append(dbus.Byte(CommandControlOpCodes.set_therapy_control_state & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_therapy_control_state >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	'''
	If the Therapy Control State is set to Undetermined or an RFU, the Server shall indicate the IDD Command Control Point with a Response Code Op Code, a Request Op Code of Set Therapy Control State, and a Response Code Value in the Operand set to Invalid Operand.
	'''
	if (state == TherapyControlState.undetermined):
		logger.info('can not set therapy state to undetermined')
		data.append(dbus.Byte(CommandControlOpCodes.set_therapy_control_state & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_therapy_control_state >> 8))
		data.append(dbus.Byte(ResponseCodes.invalid_operand))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	#set the therapy control state
	result = set_therapy_control_state(state)

	#return a response
	if result == True:
		logger.info('therapy control state set successfully')
		data.append(dbus.Byte(CommandControlOpCodes.set_therapy_control_state & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_therapy_control_state >> 8))
		data.append(dbus.Byte(ResponseCodes.success))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	else:
		logger.info('error setting status')
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		data.append(dbus.Byte(CommandControlOpCodes.set_therapy_control_state & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_therapy_control_state >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_set_flight_mode():
	logger.info('handle_set_flight_mode')
	data = []
	set_flight_mode(1)

	data.append(dbus.Byte(CommandControlOpCodes.set_flight_mode & 0xff))
	data.append(dbus.Byte(CommandControlOpCodes.set_flight_mode >> 8))
	data.append(dbus.Byte(ResponseCodes.success))
	packet = build_response_packet(CommandControlOpCodes.response_code, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)


'''
-Set the Annunciation Status field of the IDD Annunciation Status characteristic (see
 Section 3.4) to value of Snoozed if this annunciation is made available.
-Set the Annunciation Status Changed bit of the Flags field of the IDD Status
 Changed characteristic (see Section 3.1) to True.
-Finally, snooze the corresponding annunciation, which shall still be active until it is confirmed, and indicate the IDD Command Control Point with a
 Snooze Annunciation Response Op Code and the Annunciation Instance ID of the snoozed annunciation.
'''
def handle_snooze_annunciation(value):
	logger.info('handle_snooze_annunciation')
	data = []
	instance_id = bytes_to_int16(value[2:4][::-1])
	logger.info(instance_id)

	annunciation = get_annunciation(instance_id)
	if (annunciation is None) or (annunciation.status == AnnunciationStatusValues.snoozed):
		logger.info('annunciation not found, or exists but already snoozed')
		data.append(dbus.Byte(CommandControlOpCodes.snooze_annunciation & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.snooze_annunciation >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return
	
	# - Finally, snooze the corresponding annunciation
	snooze_annunciation(instance_id)
	annunication = get_ids_annunciation_status()
	send_response(IDSServiceCharacteristics.annunciation, annunication)

	# - Set the Annunciation Status Changed bit of the Flags field of the IDD Status Changed characteristic (see Section 3.1) to True.
	update_status_changed(8)

	# - indicate the IDD Command Control Point with a Snooze Annunciation Response Op Code and the Annunciation Instance ID of the snoozed annunciation
	data.append(dbus.Byte(instance_id & 0xff))
	data.append(dbus.Byte(instance_id >> 8))
	packet = build_response_packet(CommandControlOpCodes.snooze_annunciation_response, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)
	

#indicate the IDD Command Control Point with a Confirm Annunciation
#Response Op Code and the Annunciation Instance ID of the confirmed annunciation
'''
the Server shall:
• No longer provide information about this annunciation in the IDD Annunciation
Status characteristic (see Section 3.4) when it is read by the Client.
• Set the Annunciation Status Changed bit of the Flags field of the IDD Status
Changed characteristic (see Section 3.4) to True.
• Finally, indicate the IDD Command Control Point with a Confirm Annunciation
Response Op Code and the Annunciation Instance ID of the confirmed annunciation.
--
If the Operand that was sent with a Confirm Annunciation Op Code specifies an Annunciation Instance ID that does not exist (i.e., the Server Application has never assigned that Annunciation ID to an occurred annunciation) or is already confirmed, the Server shall indicate the IDD Command Control Point with a Response Code Op Code, a Request Op Code of Confirm Annunciation, and a Response Code Value in the Operand set to Procedure not applicable.
If the operation results in an error condition, this shall be indicated using a Response Code Op Code, a Request Op Code of Confirm Annunciation, and the appropriate Response Code Value in the Operand for the error condition as described in Section 3.11.4.

'''
def handle_confirm_annunciation(value):
	logger.info('handle_confirm_annunciation')
	data = []
	instance_id = bytes_to_int16(value[2:4][::-1])

	annunciation = get_annunciation(instance_id)
	if (annunciation is None) or (annunciation.status == AnnunciationStatusValues.confirmed):
		logger.info('annunciation not found, or exists but already confirmed')
		data.append(dbus.Byte(CommandControlOpCodes.confirm_annunciation & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.confirm_annunciation >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return
	
	#NOTE: we do not normally confirm an annunciation, remove this, just for testing
	confirm_annunciation(instance_id)
	annunication = get_ids_annunciation_status()
	send_response(IDSServiceCharacteristics.annunciation, annunication)

	# - Set the Annunciation Status Changed bit of the Flags field of the IDD Status Changed characteristic (see Section 3.1) to True.
	update_status_changed(8)

	# - Finally, confirm the corresponding annunciation
	confirm_annunciation(instance_id)

	data.append(dbus.Byte(instance_id & 0xff))
	data.append(dbus.Byte(instance_id >> 8))
	packet = build_response_packet(CommandControlOpCodes.confirm_annunciation_response, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)

	
#TO-DO: support multiple packet response
'''
the Server shall notify the IDD Command Data characteristic (see Section 3.8) until all time blocks of the basal rate profile have been sent. The Server shall indicate the IDD Command Control Point after notifying the last response. Each notification of the IDD Command Data characteristic shall contain a
Read Basal Rate Profile Template Response Op Code and a Basal Rate Profile Template record (see Section 3.8.1.4).

For the Read Basal Rate Profile Template Procedure, the common behavior of reading profile templates and their error conditions apply (see Section 3.7.2.1.1).
'''
def handle_read_basal_rate_profile_template(value):
	logger.info('handle_read_basal_rate_profile_template')
	template_number = value[2]
	print(repr(template_number))
	
	template = get_basal_rate_profile_template(int(template_number))
	print(template)
	data = []
	packet = []
	flags = 0

	if template_number not in TemplateRange.basal_rate_profile_template_range:
		logger.info('basal rate template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.read_basal_rate_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_basal_rate_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	if template is None:
		logger.info('template not found')
		data.append(dbus.Byte(CommandControlOpCodes.read_basal_rate_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_basal_rate_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return
	else:
		logger.info('template found')
		first_rate = float_to_shortfloat(template.first_rate)
		if template.second_duration != 0:
			flags = set_bit(flags, 0)
		if template.third_duration != 0:
			flags = set_bit(flags, 1)
		data.append(dbus.Byte(flags))
		data.append(dbus.Byte(template.template_number))
		data.append(dbus.Byte(template.first_time_block_number_index))
		data.append(dbus.Byte(template.first_duration & 0xff))
		data.append(dbus.Byte(template.first_duration >> 8))
		data.append(dbus.Byte(first_rate & 0xff))
		data.append(dbus.Byte(first_rate >> 8))
		if template.second_duration != 0:
			second_rate = float_to_shortfloat(template.second_rate)
			data.append(dbus.Byte(template.second_duration & 0xff))
			data.append(dbus.Byte(template.second_duration >> 8))
			data.append(dbus.Byte(second_rate & 0xff))
			data.append(dbus.Byte(second_rate >> 8))
		if template.third_duration != 0:
			third_rate = float_to_shortfloat(template.third_rate)
			data.append(dbus.Byte(template.third_duration & 0xff))
			data.append(dbus.Byte(template.third_duration >> 8))
			data.append(dbus.Byte(third_rate & 0xff))
			data.append(dbus.Byte(third_rate >> 8))
		packet = build_response_packet(CommandControlOpCodes.read_basal_rate_profile_template_response, data)
		send_response(IDSServiceCharacteristics.command_data, packet)

		data = []
		data.append(dbus.Byte(CommandControlOpCodes.read_basal_rate_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_basal_rate_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.success))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)

#TO-DO: do plausiblity checks
'''
If a Profile Template writing procedure is executed successfully (e.g., Write Basal Rate Profile Template Procedure), the Server shall set that template status to Configured
'''
def handle_write_basal_rate_profile_template(value):
	logger.info('handle_write_basal_rate_profile_template')
	data = []
	
	flags = value[2]
	template_number = value[3]
	first_time_block_number_index = value[4]

	first_duration = bytes_to_int16(value[5:7][::-1])
	first_rate = shortfloat_bytes_to_float(value[7:9][::-1])

	if(is_set(flags, 1)):
		second_duration = bytes_to_int16(value[9:11][::-1])
		second_rate = shortfloat_bytes_to_float(value[11:13][::-1])
	else:
		second_duration = 0
		second_rate = 0

	if(is_set(flags, 2)):
		third_duration = bytes_to_int16(value[13:15][::-1])
		third_rate = shortfloat_bytes_to_float(value[15:17][::-1])
	else:
		third_duration = 0
		third_rate = 0
	
	if template_number not in TemplateRange.basal_rate_profile_template_range:
		logger.info('basal rate template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.write_basal_rate_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.write_basal_rate_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	#perform plausiblity check: the sum of all time block durations is 24 hours (1440 minutes)
	if (first_duration + second_duration + third_duration) > 1440:
		print("sum of all time blocks is greater than 24 hours (1440 minutes)")
		data.append(dbus.Byte(CommandControlOpCodes.write_basal_rate_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.write_basal_rate_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.plausibility_check_failed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	result = write_basal_rate_profile_template(flags,
									  template_number,
								  	  first_time_block_number_index,
									  first_duration,
									  first_rate,
									  second_duration,
									  second_rate,
									  third_duration,
									  third_rate)
	logger.info(result)

	if result == True:
		template_number_str = str(int(template_number)).zfill(2)
		first_time_block_number_index_str = str(int(first_time_block_number_index)).zfill(2)
		first_duration_data = value[5:7]
		first_rate_data = value[7:9]

		print(repr(first_duration_data))
		print(repr(first_rate_data))

		history_data = template_number_str + first_time_block_number_index_str + ''.join(format(x, '02x') for x in first_duration_data) + ''.join(format(x, '02x') for x in first_rate_data)
		add_history_event(EventType.basal_rate_profile_template_time_block_changed, history_data)

		data.append(dbus.Byte(0x01)) #flags, transaction complete
		data.append(dbus.Byte(template_number))
		data.append(dbus.Byte(first_time_block_number_index))
		packet = build_response_packet(CommandControlOpCodes.write_basal_rate_profile_template_response, data)
	else:
		data.append(dbus.Byte(CommandControlOpCodes.write_basal_rate_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.write_basal_rate_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_set_tbr_adjustment(value):
	logger.info('handle_set_tbr_adjustment')
	data = []
	flags = value[2]
	tbr_type = value[3]
	tbr_adjustment_value = value[4]
	tbr_adjustment_duration = value[5]
	procedure_not_applicable = 0
	invalid_operand = 0
	tbr_delivery_context = 0

	#The provided TBR Type is not supported by the Server.
	tbr_absolute_supported = get_setting('features', 'FEATURES', 'ids_features_tbr_absolute_supported')
	if (tbr_type == TBRType.absolute) and (tbr_absolute_supported == '0'):
		logger.info('tbr type is absolute, but not supported')
		procedure_not_applicable = 1

	tbr_relative_supported = get_setting('features', 'FEATURES', 'ids_features_tbr_relative_supported')
	if (tbr_type == TBRType.relative) and (tbr_relative_supported == '0'):
		logger.info('tbr type is relative, but not supported')
		procedure_not_applicable = 1

	#An active TBR should be changed although there is currently no active TBR.
	change_tbr_present = is_set(flags, TBRAdjustmentFlags.change_tbr_bit)
	if (change_tbr_present is True) and (tbr_adjustment_is_active() == 0):
		logger.info('change tbr bit is set, but there is no active tbr')
		procedure_not_applicable = 1

	#The TBR Template Number Present bit of the Flags field is set to 1 although the Server does not support TBR templates.
	tbr_template_number_present = is_set(flags, TBRAdjustmentFlags.tbr_template_number_present_bit)
	template_supported = get_setting('features', 'FEATURES', 'ids_features_tbr_template_supported')
	if (tbr_template_number_present == True) and (template_supported == '0'):
		logger.info('tbr template number present, but not supported')
		procedure_not_applicable = 1

	#The TBR Template Number denotes a template that is not configured (see Section 3.7.2.17).
	if (tbr_template_number_present == True):
		template_number = value[8]
		
		if template_number not in TemplateRange.tbr_template_range:
			logger.info('tbr template number is out of range')
			data.append(dbus.Byte(CommandControlOpCodes.set_tbr_adjustment & 0xff))
			data.append(dbus.Byte(CommandControlOpCodes.set_tbr_adjustment >> 8))
			data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
			packet = build_response_packet(CommandControlOpCodes.response_code, data)
			send_response(IDSServiceCharacteristics.command_control_point, packet)
			return

		template = get_template_details(template_number)
		if (template is None) or template.configured == 0:
			logger.info('tbr template number present, but no template exists or is not configured')
			data.append(dbus.Byte(CommandControlOpCodes.set_tbr_adjustment & 0xff))
			data.append(dbus.Byte(CommandControlOpCodes.set_tbr_adjustment >> 8))
			data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
			packet = build_response_packet(CommandControlOpCodes.response_code, data)
			send_response(IDSServiceCharacteristics.command_control_point, packet)
			return

	if (tbr_type == TherapyControlState.undetermined):
		logger.info('tbr type is undetermined')
		invalid_operand = 1

	#check if a tbr adjustment is already active
	if (tbr_adjustment_is_active() == 1):
		logger.info('tbr is already active')
		procedure_not_applicable = 1

	if(procedure_not_applicable == 1):
		logger.info('procedure_not_applicable')
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_adjustment & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_adjustment >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	elif (invalid_operand == 1):
		logger.info('invalid_operand')
		invalid_operand = 1
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_adjustment & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_adjustment >> 8))
		data.append(dbus.Byte(ResponseCodes.invalid_operand))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	else:
		tbr_adjustment_set_active(1)
		
		if (tbr_template_number_present == True):
			template_number = value[8]
			set_tbr_adjustment_using_template(template_number)
		else:
			set_tbr_adjustment(tbr_type, tbr_adjustment_value, tbr_adjustment_duration, tbr_delivery_context)

		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_adjustment & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_adjustment >> 8))
		data.append(dbus.Byte(ResponseCodes.success))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_cancel_tbr_adjustment():
	logger.info('handle_cancel_tbr_adjustment')
	data = []
	
	if (tbr_adjustment_is_active() == 1):
		tbr_adjustment_set_active(0)
		cancel_tbr_adjustment()
		logger.info('tbr adjustment cancelled')
		data.append(dbus.Byte(CommandControlOpCodes.cancel_tbr_adjustment & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.cancel_tbr_adjustment >> 8))
		data.append(dbus.Byte(ResponseCodes.success))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	else:
		logger.info('no active tbr')
		data.append(dbus.Byte(CommandControlOpCodes.cancel_tbr_adjustment & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.cancel_tbr_adjustment >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_get_tbr_template(value):
	logger.info('handle_get_tbr_template')
	logger.info(value)

	template_number = value[2]
	
	template = get_tbr_template(int(template_number))
	print(template)
	data = []

	if template_number not in TemplateRange.tbr_template_range:
		logger.info('tbr template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.get_tbr_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.get_tbr_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	if template is None:
		logger.info('template not found')
		data.append(dbus.Byte(CommandControlOpCodes.get_tbr_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.get_tbr_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	else:
		logger.info('template found')
		tbr_adjustment_value = float_to_shortfloat(template.tbr_adjustment_value)
		data.append(dbus.Byte(template.template_number))
		data.append(dbus.Byte(template.tbr_type))
		data.append(dbus.Byte(tbr_adjustment_value & 0xff))
		data.append(dbus.Byte(tbr_adjustment_value >> 8))
		data.append(dbus.Byte(template.tbr_duration & 0xff))
		data.append(dbus.Byte(template.tbr_duration >> 8))
		packet = build_response_packet(CommandControlOpCodes.get_tbr_template_response, data)	
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_set_tbr_template(value):
	print('handle_set_tbr_template')
	print(value)
	data = []
	procedure_not_applicable = 0

	template_number = value[2]
	tbr_type = value[3]
	
	print(repr((template_number)))
	print(repr((tbr_type)))
	
	if template_number not in TemplateRange.tbr_template_range:
		logger.info('tbr template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	'''
	If the Operand that was sent with a Set TBR Template Op Code specifies a TBR Type that is set to Undetermined or an RFU value, the Server shall indicate the IDD Command Control Point with a Response Code Op Code, a Request Op Code of
	Set TBR Template, and a Response Code Value in the Operand set to Invalid Operand.
	'''
	if (tbr_type == TBRType.undetermined):
		print('tbr type is undetermined')
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_template >> 8))
		data.append(dbus.Byte(ResponseCodes.invalid_operand))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	'''
	The Server shall indicate the IDD Command Control Point with a Response Code Op Code, a Request Op Code of Set TBR Template, and a Response Code Value in the Operand set to Procedure not applicable in the following cases:
	'''
	# The TBR Type is not supported by the Server
	tbr_absolute_supported = get_setting('features', 'FEATURES', 'ids_features_tbr_absolute_supported')
	if (tbr_type == TBRType.absolute) and (tbr_absolute_supported == '0'):
		print('tbr type is absolute, but not supported')
		procedure_not_applicable = 1

	tbr_relative_supported = get_setting('features', 'FEATURES', 'ids_features_tbr_relative_supported')
	if (tbr_type == TBRType.relative) and (tbr_relative_supported == '0'):
		print('tbr type is relative, but not supported')
		procedure_not_applicable = 1

	if(procedure_not_applicable == 1):
		print('procedure_not_applicable')
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	tbr_adjustment_value = shortfloat_bytes_to_float(value[4:6][::-1])
	tbr_duration_value = bytes_to_int16(value[6:8][::-1])
	
	result = write_tbr_template(template_number, 
					   tbr_type, 
					   tbr_adjustment_value, 
					   tbr_duration_value)

	logger.info(result)

	if result == True:
		tbr_adjustment_value_bytes = value[4:6]
		tbr_duration_value_bytes = value[6:8]
		
		history_data = str(hex(template_number)[2:]).zfill(2) + str(hex(tbr_type)[2:]) + ''.join(format(x, '02x') for x in tbr_adjustment_value_bytes) + ''.join(format(x, '02x') for x in tbr_duration_value_bytes)
		add_history_event(EventType.tbr_template_changed, history_data)
		
		data.append(dbus.Byte(template_number))
		packet = build_response_packet(CommandControlOpCodes.set_tbr_template_response, data)
	else:
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_tbr_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)

	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_set_bolus(value):
	logger.info('handle_set_bolus')
	logger.info(value)
	data = []
	procedure_not_applicable = 0
	invalid_operand = 0
	bolus_template_number = 0

	flags = value[2]
	bolus_type = value[3]
	print('bolus type: ' + repr(int(bolus_type)))

	bolus_fast_amount = shortfloat_bytes_to_float(value[4:6][::-1])
	print('bolus fast amount: ' + repr(bolus_fast_amount))
	bolus_extended_amount = shortfloat_bytes_to_float(value[6:8][::-1])
	print('bolus extended amount: ' + repr(bolus_extended_amount))
	bolus_duration = bytes_to_int16(value[8:10][::-1])
	print('bolus duration: ' + repr(bolus_duration))
	
	'''The Server shall indicate the IDD Command Control Point with a Response Code Op Code, a Request Op Code of Set Bolus, and a Response Code Value in the Operand set to Procedure not applicable in the following cases:
	- The Bolus Type is not supported by the Server.
	'''
	fast_bolus_supported = get_setting('features', 'FEATURES', 'ids_features_fast_bolus_supported')
	if (bolus_type == BolusType.fast) and (fast_bolus_supported == '0'):
		print('bolus type is fast, but not supported')
		procedure_not_applicable = 1

	extended_bolus_supported = get_setting('features', 'FEATURES', 'ids_features_extended_bolus_supported')
	if (bolus_type == BolusType.extended) and (extended_bolus_supported == '0'):
		print('bolus type is extended, but not supported')
		procedure_not_applicable = 1
	
	multiwave_bolus_supported = get_setting('features', 'FEATURES', 'ids_features_multiwave_bolus_supported')
	if (bolus_type == BolusType.multiwave) and (multiwave_bolus_supported == '0'):
		print('bolus type is multiwave, but not supported')
		procedure_not_applicable = 1

	#The Bolus Delay Time Present bit of the Flags field is set to 1 although the Server does not support a bolus delay time.
	bolus_delay_time_present = is_set(flags, BolusFlags.bolus_delay_time_present_bit)
	bolus_delay_time_supported = get_setting('features', 'FEATURES', 'ids_features_bolus_delay_supported')
	if (bolus_delay_time_present == True) and (bolus_delay_time_supported == '0'):
		print('bolus delay time present, but not supported')
		procedure_not_applicable = 1

	#The Bolus Template Number Present bit of the Flags field is set to 1 although the Server does not support bolus templates.
	bolus_template_number_present = is_set(flags, BolusFlags.bolus_template_number_present_bit)
	bolus_template_supported = get_setting('features', 'FEATURES', 'ids_features_bolus_template_supported')
	if (bolus_template_number_present == True) and (bolus_template_supported == '0'):
		print('bolus template number present, but not supported')
		procedure_not_applicable = 1

	#The Bolus Template Number Present bit of the Flags field is set to 1 although the Server does not support bolus templates.
	bolus_activation_type_present = is_set(flags, BolusFlags.bolus_activation_type_present_bit)
	bolus_activation_type_supported = get_setting('features', 'FEATURES', 'ids_features_bolus_activation_type_supported')
	if (bolus_activation_type_present == True) and (bolus_activation_type_supported == '0'):
		print('bolus activation type present, but not supported')
		procedure_not_applicable = 1

	if (bolus_template_number_present == True):
		template_number = value[8]
		
		if template_number not in TemplateRange.bolus_template_range:
			logger.info('bolus template number is out of range')
			data.append(dbus.Byte(CommandControlOpCodes.set_bolus & 0xff))
			data.append(dbus.Byte(CommandControlOpCodes.set_bolus >> 8))
			data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
			packet = build_response_packet(CommandControlOpCodes.response_code, data)
			send_response(IDSServiceCharacteristics.command_control_point, packet)
			return

		template = get_template_details(template_number)
		if (template is None) or template.configured == 0:
			logger.info('bolus template number present, but no template exists or is not configured')
			data.append(dbus.Byte(CommandControlOpCodes.set_bolus & 0xff))
			data.append(dbus.Byte(CommandControlOpCodes.set_bolus >> 8))
			data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
			packet = build_response_packet(CommandControlOpCodes.response_code, data)
			send_response(IDSServiceCharacteristics.command_control_point, packet)
			return

	'''
	The Server shall indicate the IDD Command Control Point with a Response Code Op Code, a Request Op Code of Set Bolus, and a Response Code Value in the Operand set to Invalid Operand in the following cases:
	- The Bolus Type is set to Undetermined or to an RFU value.
	'''
	if (bolus_type == BolusType.undetermined):
		logger.info('bolus type is undetermined')
		invalid_operand = 1

	'''
	Bolus Fast Amount, Bolus Extended Amount, or Bolus Duration do not fit to Bolus Type:
		- Bolus Fast Amount has to be 0 if Bolus Type is “Extended”
		- Bolus Extended Amount and Bolus Duration have to be 0 if Bolus Type is “Fast”
	'''
	if (bolus_type == BolusType.extended) and (bolus_fast_amount != 0):
		logger.info('bolus type is extended, but fast amount is not zero')
		invalid_operand = 1

	if (bolus_type == BolusType.fast) and (bolus_extended_amount != 0) and (bolus_duration != 0):
		logger.info('bolus type is fast, but extended amount and/or duration is not zero')
		invalid_operand = 1

	'''
	If the Set Bolus Op Code is written to the IDD Command Control Point with an Operand containing a bolus record, the Server shall set a bolus with the provided settings and indicate the IDD Command Control Point with a Set Bolus Response Op Code and the Bolus ID of the set bolus.
	'''
	if (procedure_not_applicable == 1):
		print('procedure_not_applicable')
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		return

	if (invalid_operand == 1):
		print('invalid_operand')
		invalid_operand = 1
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus >> 8))
		data.append(dbus.Byte(ResponseCodes.invalid_operand))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		return
	
	if (bolus_template_number_present == True):
		bolus_template_number = value[12]
		
	if(bolus_delay_time_present == True):
		bolus_delay_time = bytes_to_int16(value[10:12][::-1])
	else:
		bolus_delay_time = 0

	if(bolus_activation_type_present == True):
		bolus_activation_type = value[13]
	else:
		bolus_activation_type = 0

	bolus_id = set_bolus(int(bolus_type) ,bolus_fast_amount, bolus_extended_amount, bolus_duration, bolus_delay_time, bolus_template_number, bolus_activation_type)

	data.append(dbus.Byte(bolus_id & 0xff))
	data.append(dbus.Byte(bolus_id >> 8))
	packet = build_response_packet(CommandControlOpCodes.set_bolus_response, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)
	

'''
If the Cancel Bolus Op Code is written to the IDD Command Control Point with a
Bolus ID field, the Server shall cancel the bolus identified by the specified Bolus ID and indicate the IDD Command Control Point with a Cancel Bolus Response Op Code and the Bolus ID of the canceled bolus.
If the Operand that was sent with a Cancel Bolus Op Code specifies an invalid Bolus ID (e.g., a Bolus ID that does not exist (i.e., the Server Application has never assigned that Bolus ID to a set bolus) or identifies a bolus that is not currently active), the Server shall indicate the IDD Command Control Point with a Response Code Op Code, a Request Op Code of Cancel Bolus, and a Response Code Value in the Operand set to Procedure not applicable.
'''
def handle_cancel_bolus(value):
	print('handle_cancel_bolus')
	data = []

	bolus_id = bytes_to_int16(value[2:4][::-1])
	result = cancel_bolus(bolus_id)

	if result is False:
		logger.info('invalid Bolus ID or Bolus ID is not active')
		data.append(dbus.Byte(CommandControlOpCodes.cancel_bolus & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.cancel_bolus >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	else:
		logger.info('bolus cancelled')
		data.append(dbus.Byte(bolus_id & 0xff))
		data.append(dbus.Byte(bolus_id >> 8))
		packet = build_response_packet(CommandControlOpCodes.cancel_bolus_response, data)
	
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_get_available_boluses():
	print('handle_get_available_boluses')
	data = []
	flags = 0

	if get_setting('features', 'FEATURES', 'ids_features_fast_bolus_supported') == '1':
		flags = set_bit(flags, 0)
	if get_setting('features', 'FEATURES', 'ids_features_extended_bolus_supported') == '1':
		flags = set_bit(flags, 1)
	if get_setting('features', 'FEATURES', 'ids_features_multiwave_bolus_supported') == '1':
		flags = set_bit(flags, 2)
	
	data.append(dbus.Byte(flags))
	packet = build_response_packet(CommandControlOpCodes.get_available_boluses_response, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_get_bolus_template(value):
	print('handle_get_bolus_template')
	template_number = value[2]
	print(repr(template_number))
	data = []

	if template_number not in TemplateRange.bolus_template_range:
		logger.info('bolus template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.get_bolus_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.get_bolus_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	template = get_bolus_template(int(template_number))
	print(template)

	flags = 0

	if template is None:
		logger.info('template not found')
		data.append(dbus.Byte(CommandControlOpCodes.get_bolus_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.get_bolus_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	else:
		logger.info('template found')
		
		if template.bolus_delay_time > 0:
			flags = set_bit(flags, 0)
		if template.bolus_delivery_reason_correction == 1:
			flags = set_bit(flags, 1)
		if template.bolus_delivery_reason_meal == 1:
			flags = set_bit(flags, 2)
		
		bolus_fast_amount = float_to_shortfloat(template.bolus_fast_amount)
		bolus_extended_amount = float_to_shortfloat(template.bolus_extended_amount)
		data.append(dbus.Byte(template.template_number))
		data.append(dbus.Byte(flags))
		data.append(dbus.Byte(template.bolus_type))
		data.append(dbus.Byte(bolus_fast_amount & 0xff))
		data.append(dbus.Byte(bolus_fast_amount >> 8))
		data.append(dbus.Byte(bolus_extended_amount & 0xff))
		data.append(dbus.Byte(bolus_extended_amount >> 8))
		data.append(dbus.Byte(template.bolus_duration & 0xff))
		data.append(dbus.Byte(template.bolus_duration >> 8))
		if template.bolus_delay_time > 0:
			data.append(dbus.Byte(template.delay_time & 0xff))
			data.append(dbus.Byte(template.delay_time >> 8))
		packet = build_response_packet(CommandControlOpCodes.get_bolus_template_response, data)

	send_response(IDSServiceCharacteristics.command_control_point, packet)
	

def handle_set_bolus_template(value):
	print('handle_set_bolus_template')
	data = []
	procedure_not_applicable = 0
	parameter_out_of_range = 0
	invalid_operand = 0

	template_number = value[2]
	flags = value[3]
	bolus_type = value[4]
	bolus_fast_amount = shortfloat_bytes_to_float(value[5:7][::-1])
	bolus_extended_amount = shortfloat_bytes_to_float(value[7:9][::-1])
	bolus_duration = bytes_to_int16(value[9:11][::-1])
	
	bolus_delay_time_present = is_set(flags, BolusTemplateFlags.bolus_delay_time_present_bit)
	if bolus_delay_time_present == 1:
		bolus_delay_time = bytes_to_int16(value[11:13][::-1])
	else:
		bolus_delay_time = 0

	bolus_delivery_reason_correction = is_set(flags, BolusTemplateFlags.bolus_delivery_reason_correction_bit)
	bolus_delivery_reason_meal = is_set(flags, BolusTemplateFlags.bolus_delivery_reason_meal_bit)

	if template_number not in TemplateRange.bolus_template_range:
		logger.info('bolus template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	'''
	The Server shall indicate the IDD Command Control Point with a Response Code Op Code, a Request Op Code of Set Bolus Template, and a Response Code Value in the Operand set to Procedure not applicable in the following cases:
	- The Bolus Type is not supported by the Server.
	'''
	if bolus_type == BolusType.fast:
		logger.info('bolus type: fast')
		supported = get_setting('features', 'FEATURES', 'ids_features_fast_bolus_supported')
		logger.info(supported)
		if supported == '0':
			procedure_not_applicable = 1
	elif bolus_type == BolusType.extended:
		supported = get_setting('features', 'FEATURES', 'ids_features_extended_bolus_supported')
		logger.info(supported)
		if supported == '0':
			procedure_not_applicable = 1
	elif bolus_type == BolusType.multiwave:
		supported = get_setting('features', 'FEATURES', 'ids_features_multiwave_bolus_supported')
		logger.info(supported)
		if supported == '0':
			procedure_not_applicable = 1

	# - The Bolus Delay Time Present bit of the Flags field is set to 1 although the Server
	#   does not support a bolus delay time.
	bolus_delay_time_present = is_set(flags, BolusTemplateFlags.bolus_delay_time_present_bit)
	if bolus_delay_time_present == 1:
		supported = get_setting('features', 'FEATURES', 'ids_features_bolus_delay_supported')
		logger.info(supported)
		if supported == '0':
			procedure_not_applicable = 1

	# - The Bolus Template Number denotes a template that is not configurable (see
	#   Section 3.7.2.17).
	#TO-DO

	#
	if (procedure_not_applicable == 1):
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus_template  & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return
	
	'''
	'Delay Time': Attached if bit 0 of Flags field is set, otherwise excluded.
	The Bolus Fast Amount field shall be set to 0 if Bolus Type is set to “Extended”.
	The Bolus Extended Amount field shall be set to 0 if Bolus Type is set to “Fast”.
	The Bolus Duration field shall be set to 0 if Bolus Type is set to “Fast”.
	'''
	if (bolus_type == BolusType.undetermined):
		logger.info('bolus type is set to undetermined')
		invalid_operand = 1

	if (bolus_type == BolusType.fast) and (bolus_extended_amount != 0) or (bolus_duration != 0):
		logger.info('bolus type is fast, but extended amount and/or duration is not zero')
		invalid_operand = 1

	if (bolus_type == BolusType.extended) and (bolus_fast_amount != 0):
		logger.info('bolus type is extended, but fast amount is not zero')
		invalid_operand = 1
	
	if (invalid_operand == 1):
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus_template >> 8))
		data.append(dbus.Byte(ResponseCodes.invalid_operand))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	result = write_bolus_template(template_number,
						 flags,
						 bolus_type,
						 bolus_fast_amount,
						 bolus_extended_amount,
						 bolus_duration,
						 bolus_delay_time,
						 bolus_delivery_reason_correction,
						 bolus_delivery_reason_meal)

	logger.info(result)
	if result == True:
		data.append(dbus.Byte(template_number))
		packet = build_response_packet(CommandControlOpCodes.set_bolus_template_response, data)
	else:
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_bolus_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)

	send_response(IDSServiceCharacteristics.command_control_point, packet)


#pg. 67/188
def handle_get_template_status_and_details():
	print('handle_get_template_status_and_details')
	'''
	If the template type is not a Profile Template type, the value of the Max Number of Supported Time Blocks field shall be set to 0; otherwise this field shall not be set to 0.
	3.8.1.8.5 Configurable and Configured Flags Field
	
	The Configurable and Configured Flags field is an array of 2 bit values where the first bit is the configurable status of the template and the second bit is the configured status of the template. If the configurable bit, bit 0, is set to 1 (=true), then this template is configurable and can be configured by the Collector Application. If the configured bit, bit 1, is set to 1 (=true), then this template is configured and does contain data. The total number of elements in this array is the value of the Number of Templates field in Section 3.8.1.8.3. A padding of bits (set to 0) shall be appended if the number of elements of the Configurable and Configured Flags field does not fill a whole number of octets.
	'''
	supported = get_setting('features', 'FEATURES', 'ids_features_basal_rate_supported')
	if (supported == '1'):
		y = 0
		config_bits = 0
		data = []
		data.append(dbus.Byte(TemplateType.basal_rate_profile_template_type))
		data.append(dbus.Byte(TemplateRange.basal_rate_profile_template_range[0]))
		data.append(dbus.Byte(len(TemplateRange.basal_rate_profile_template_range)-1))
		data.append(dbus.Byte(24))
		for x in range(TemplateRange.basal_rate_profile_template_range[0], (TemplateRange.basal_rate_profile_template_range[0] + len(TemplateRange.basal_rate_profile_template_range))):
			template = get_template(x)
			if (template.configurable):
				config_bits = set_bit(config_bits, y)
			if (template.configured):
				config_bits = set_bit(config_bits, y+1)
			y+=2
		data.append(dbus.Byte(config_bits))
		packet = build_response_packet(CommandControlOpCodes.get_template_status_and_details_response, data)
		send_response(IDSServiceCharacteristics.command_data, packet)
		
	supported = get_setting('features', 'FEATURES', 'ids_features_tbr_template_supported')
	if (supported == '1'):
		y = 0
		config_bits = 0
		data = []
		data.append(dbus.Byte(TemplateType.tbr_template_type))
		data.append(dbus.Byte(TemplateRange.tbr_template_range[0]))
		data.append(dbus.Byte(len(TemplateRange.tbr_template_range)-1))
		data.append(dbus.Byte(0))
		for x in range(TemplateRange.tbr_template_range[0], (TemplateRange.tbr_template_range[0] + len(TemplateRange.tbr_template_range))):
			template = get_template(x)
			if (template.configurable):
				config_bits = set_bit(config_bits, y)
			if (template.configured):
				config_bits = set_bit(config_bits, y+1)
			y+=2
		data.append(dbus.Byte(config_bits))
		packet = build_response_packet(CommandControlOpCodes.get_template_status_and_details_response, data)
		send_response(IDSServiceCharacteristics.command_data, packet)

	supported = get_setting('features', 'FEATURES', 'ids_features_bolus_template_supported')
	if (supported == '1'):
		y = 0
		config_bits = 0
		data = []
		data.append(dbus.Byte(TemplateType.bolus_template_type))
		data.append(dbus.Byte(TemplateRange.bolus_template_range[0]))
		data.append(dbus.Byte(len(TemplateRange.bolus_template_range)-1))
		data.append(dbus.Byte(0))
		for x in range(TemplateRange.bolus_template_range[0], (TemplateRange.bolus_template_range[0] + len(TemplateRange.bolus_template_range))):
			template = get_template(x)
			if (template.configurable):
				config_bits = set_bit(config_bits, y)
			if (template.configured):
				config_bits = set_bit(config_bits, y+1)
			y+=2
		data.append(dbus.Byte(config_bits))
		packet = build_response_packet(CommandControlOpCodes.get_template_status_and_details_response, data)
		send_response(IDSServiceCharacteristics.command_data, packet)

	supported = get_setting('features', 'FEATURES', 'ids_features_isf_profile_template_supported')
	if (supported == '1'):
		y = 0
		config_bits = 0
		data = []
		data.append(dbus.Byte(TemplateType.isf_profile_template_type))
		data.append(dbus.Byte(TemplateRange.isf_template_range[0]))
		data.append(dbus.Byte(len(TemplateRange.isf_template_range)-1))
		data.append(dbus.Byte(24))
		for x in range(TemplateRange.isf_template_range[0], (TemplateRange.isf_template_range[0] + len(TemplateRange.isf_template_range))):
			template = get_template(x)
			if (template.configurable):
				config_bits = set_bit(config_bits, y)
			if (template.configured):
				config_bits = set_bit(config_bits, y+1)
			y+=2
		data.append(dbus.Byte(config_bits))
		packet = build_response_packet(CommandControlOpCodes.get_template_status_and_details_response, data)
		send_response(IDSServiceCharacteristics.command_data, packet)

	supported = get_setting('features', 'FEATURES', 'ids_features_i2cho_ratio_profile_template_supported')
	if (supported == '1'):
		y = 0
		config_bits = 0
		data = []
		data.append(dbus.Byte(TemplateType.i2cho_template_type))
		data.append(dbus.Byte(TemplateRange.i2cho_template_range[0]))
		data.append(dbus.Byte(len(TemplateRange.i2cho_template_range)-1))
		data.append(dbus.Byte(24))
		for x in range(TemplateRange.i2cho_template_range[0], (TemplateRange.i2cho_template_range[0] + len(TemplateRange.i2cho_template_range))):
			template = get_template(x)
			if (template.configurable):
				config_bits = set_bit(config_bits, y)
			if (template.configured):
				config_bits = set_bit(config_bits, y+1)
			y+=2
		data.append(dbus.Byte(config_bits))
		packet = build_response_packet(CommandControlOpCodes.get_template_status_and_details_response, data)
		send_response(IDSServiceCharacteristics.command_data, packet)

	supported = get_setting('features', 'FEATURES', 'ids_features_target_glucose_range_profile_template_supported')
	if (supported == '1'):
		y = 0
		config_bits = 0
		data = []
		data.append(dbus.Byte(TemplateType.target_glucose_template_type))
		data.append(dbus.Byte(TemplateRange.target_glucose_range_template_range[0]))
		data.append(dbus.Byte(len(TemplateRange.target_glucose_range_template_range)-1))
		data.append(dbus.Byte(24))
		for x in range(TemplateRange.target_glucose_range_template_range[0], (TemplateRange.target_glucose_range_template_range[0] + len(TemplateRange.target_glucose_range_template_range))):
			template = get_template(x)
			if (template.configurable):
				config_bits = set_bit(config_bits, y)
			if (template.configured):
				config_bits = set_bit(config_bits, y+1)
			y+=2
		data.append(dbus.Byte(config_bits))
		packet = build_response_packet(CommandControlOpCodes.get_template_status_and_details_response, data)
		send_response(IDSServiceCharacteristics.command_data, packet)

	data = []
	data.append(dbus.Byte(CommandControlOpCodes.get_template_status_and_details  & 0xff))
	data.append(dbus.Byte(CommandControlOpCodes.get_template_status_and_details >> 8))
	data.append(dbus.Byte(ResponseCodes.success))
	packet = build_response_packet(CommandControlOpCodes.response_code, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)
	

def handle_reset_template_status(value):
	print('handle_reset_template_status')
	print(value)
	data = []

	number_of_templates_to_reset = value[2]
	print('number of templates to reset: ' + repr(int(number_of_templates_to_reset)))
	
	for template_number in range(0, int(number_of_templates_to_reset)):
		print('reset template: ' + repr(int(value[template_number + 3])))
		template = get_template(int(value[template_number + 3]))
		if (template is None) or (template.configured == 0) or (template.configurable == 0) or (template.active == 1):
			logger.info('issue resetting template')
			data.append(dbus.Byte(CommandControlOpCodes.reset_template_status  & 0xff))
			data.append(dbus.Byte(CommandControlOpCodes.reset_template_status >> 8))
			data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
			packet = build_response_packet(CommandControlOpCodes.response_code, data)
			send_response(IDSServiceCharacteristics.command_control_point, packet)
			return
		else:
			reset_template_status(int(value[template_number + 3]))

	data.append(dbus.Byte(number_of_templates_to_reset))
	for template_number in range(0, int(number_of_templates_to_reset)):
		data.append(dbus.Byte(int(value[template_number + 3])))

	packet = build_response_packet(CommandControlOpCodes.reset_template_status_response, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)
	

def handle_activate_profile_templates(value):
	print('handle_activate_profile_templates')
	print(value)
	data = []
	templates = []

	number_of_templates_to_activate = value[2]
	print('number of templates to activate: ' + repr(int(number_of_templates_to_activate)))
	
	for template_number in range(0, int(number_of_templates_to_activate)):
		print('activate template: ' + repr(int(value[template_number + 3])))
		template = get_template(int(value[template_number + 3]))
		templates.append(template)
		logger.info(template)
		if (template is None) or (template.configured == 0):
			logger.info('issue activating template')
			if template is None:
				logger.info('template does not exist')
			else:
				logger.info(template.configured)
			data.append(dbus.Byte(CommandControlOpCodes.activate_profile_templates  & 0xff))
			data.append(dbus.Byte(CommandControlOpCodes.activate_profile_templates >> 8))
			data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
			packet = build_response_packet(CommandControlOpCodes.response_code, data)
			send_response(IDSServiceCharacteristics.command_control_point, packet)
			return
		else:
			activate_templates(templates)

	data.append(dbus.Byte(number_of_templates_to_activate))
	for template_number in range(0, int(number_of_templates_to_activate)):
		data.append(dbus.Byte(int(value[template_number + 3])))

	packet = build_response_packet(CommandControlOpCodes.activate_profile_templates_response, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_get_activated_profile_templates():
	print('handle_get_activated_profile_templates')
	data = []
	
	rows = get_rows(TemplateLookup, TemplateLookup.active, 1)
	logger.info(rows)
	data.append(dbus.Byte(len(rows)))
	number_of_activated_templates = len(rows)

	if number_of_activated_templates > 0:
		logger.info('appending activated templates')
		for i in range(0, number_of_activated_templates):
			logger.info(i)
			template = rows[i]
			logger.info(template)
			data.append(dbus.Byte(template.template_number))
	else:
		logger.info('no activated templates')

	packet = build_response_packet(CommandControlOpCodes.get_activated_profile_templates_response, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)
	

def handle_start_priming(value):
	print('handle_start_priming')
	print(repr(value))
	data = []
	
	event_data = value[2:4][::-1]
	priming_amount = shortfloat_bytes_to_float(event_data)
	print('priming amount: ' + repr(priming_amount))

	start_priming(priming_amount)
	
	# pg.171
	history_data = ''.join(format(x, '02x') for x in event_data)
	print(type(history_data))
	add_history_event(EventType.priming_started, history_data)

	data.append(dbus.Byte(CommandControlOpCodes.start_priming  & 0xff))
	data.append(dbus.Byte(CommandControlOpCodes.start_priming >> 8))
	data.append(dbus.Byte(ResponseCodes.success))
	packet = build_response_packet(CommandControlOpCodes.response_code, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_stop_priming():
	print('handle_stop_priming')
	data = []

	'''
	If the priming was not started before by executing the Start Priming procedure (see Section 3.7.2.19), or the priming was already finished (i.e., the provided amount of insulin to fill the fluidic path was delivered completely), the Server shall indicate the IDD Command Control Point with a Response Code Op Code, a Request Op Code of
	Stop Priming, and a Response Code Value in the Operand set to Procedure not applicable.
	'''
	result = stop_priming()
	if result is False:
		data.append(dbus.Byte(CommandControlOpCodes.stop_priming  & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.stop_priming >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_applicable))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	else:
		# pg.172
		#no flags set, 5.7, programmed amount reached
		history_data = '0039F03C'
		add_history_event(EventType.priming_done, history_data)

		data.append(dbus.Byte(CommandControlOpCodes.stop_priming  & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.stop_priming >> 8))
		data.append(dbus.Byte(ResponseCodes.success))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_set_initial_reservoir_fill_level(value):
	print('handle_set_initial_reservoir_fill_level')
	data = []
	
	initial_reservoir_fill_level = shortfloat_bytes_to_float(value[2:4][::-1])
	print('initial reservoir fill level amount: ' + repr(initial_reservoir_fill_level))
	result = set_initial_reservoir_fill_level(initial_reservoir_fill_level)

	if result is False:
		data.append(dbus.Byte(CommandControlOpCodes.set_initial_reservoir_fill_level  & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_initial_reservoir_fill_level >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	else:
		data.append(dbus.Byte(CommandControlOpCodes.set_initial_reservoir_fill_level  & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.set_initial_reservoir_fill_level >> 8))
		data.append(dbus.Byte(ResponseCodes.success))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_reset_reservoir_insulin_operation_time():
	print('handle_reset_reservoir_insulin_operation_time')
	data = []

	reset_reservoir_insulin_operation_time()

	data.append(dbus.Byte(CommandControlOpCodes.reset_reservoir_insulin_operation_time  & 0xff))
	data.append(dbus.Byte(CommandControlOpCodes.reset_reservoir_insulin_operation_time >> 8))
	data.append(dbus.Byte(ResponseCodes.success))
	packet = build_response_packet(CommandControlOpCodes.response_code, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)

	
def handle_read_isf_profile_template(value):
	print('handle_read_isf_profile_template')
	template_number = value[2]
	print(repr(template_number))
	data = []

	if template_number not in TemplateRange.isf_template_range:
		logger.info('isf template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.read_isf_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_isf_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	template = get_isf_template(int(template_number))
	print(template)

	if template is None:
		logger.info('template not found')
		data.append(dbus.Byte(CommandControlOpCodes.read_isf_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_isf_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return
	else:
		logger.info('template found')
		first_isf = float_to_shortfloat(template.first_isf)
		data.append(dbus.Byte(0x00)) #TO-DO: set the flags correctly
		data.append(dbus.Byte(template.template_number))
		data.append(dbus.Byte(template.first_time_block_number_index))
		data.append(dbus.Byte(template.first_duration & 0xff))
		data.append(dbus.Byte(template.first_duration >> 8))
		data.append(dbus.Byte(first_isf & 0xff))
		data.append(dbus.Byte(first_isf >> 8))
		
		if template.second_duration > 0:
			second_isf = float_to_shortfloat(template.second_isf)
			data.append(dbus.Byte(template.second_duration & 0xff))
			data.append(dbus.Byte(template.second_duration >> 8))
			data.append(dbus.Byte(second_isf & 0xff))
			data.append(dbus.Byte(second_isf >> 8))

		if template.third_duration > 0:
			third_isf = float_to_shortfloat(template.third_isf)
			data.append(dbus.Byte(template.third_duration & 0xff))
			data.append(dbus.Byte(template.third_duration >> 8))
			data.append(dbus.Byte(third_isf & 0xff))
			data.append(dbus.Byte(third_isf >> 8))

		packet = build_response_packet(CommandControlOpCodes.read_isf_profile_template_response, data)
		send_response(IDSServiceCharacteristics.command_data, packet)
		
		data = []
		data.append(dbus.Byte(CommandControlOpCodes.read_isf_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_isf_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.success))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_write_isf_profile_template(value):
	print('handle_write_isf_profile_template')
	data = []
	flags = value[2]
	template_number = value[3]
	first_time_block_number_index = value[4]
	
	first_duration = bytes_to_int16(value[5:7][::-1])
	print('first_duration: ' + repr(first_duration))

	first_isf = shortfloat_bytes_to_float(value[7:9][::-1])
	print('first_isf: ' + repr(first_isf))

	if template_number not in TemplateRange.isf_template_range:
		logger.info('isf template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.write_isf_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.write_isf_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	if(is_set(flags, 1)):
		second_duration = bytes_to_int16(value[9:11][::-1])
		second_isf = shortfloat_bytes_to_float(value[11:13][::-1])
	else:
		second_duration = 0
		second_isf = 0

	if(is_set(flags, 2)):
		third_duration = bytes_to_int16(value[13:15][::-1])
		third_isf = shortfloat_bytes_to_float(value[15:17][::-1])
	else:
		third_duration = 0
		third_isf = 0

	result = write_isf_template(flags,
					   template_number,
					   first_time_block_number_index,
					   first_duration,
					   first_isf,
					   second_duration,
					   second_isf,
					   third_duration,
					   third_isf)

	logger.info(result)

	if result == True:
		first_duration_data = value[5:7]
		first_isf_data = value[7:9]
		history_data = str(hex(template_number)[2:]).zfill(2) + str(hex(first_time_block_number_index)[2:]).zfill(2) + ''.join(format(x, '02x') for x in first_duration_data) + ''.join(format(x, '02x') for x in first_isf_data) 
		add_history_event(EventType.isf_profile_template_time_block_changed, history_data)

		data.append(dbus.Byte(0x01)) # flags
		data.append(dbus.Byte(template_number))
		data.append(dbus.Byte(first_time_block_number_index))
		packet = build_response_packet(CommandControlOpCodes.write_isf_profile_template_response, data)
	else:
		'''If the Collector writes to a control point characteristic and the procedure could not be completed for any reason,
		it will receive a Response Code CP indication with the Response Code Value set to Procedure not completed.
		'''
		data.append(dbus.Byte(CommandControlOpCodes.write_isf_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.write_isf_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)

	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_read_i2cho_ratio_profile_template(value):
	print('handle_read_i2cho_ratio_profile_template')
	
	template_number = value[2]
	data = []
	flags = 0

	if template_number not in TemplateRange.i2cho_template_range:
		logger.info('i2cho template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.read_i2cho_ratio_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_i2cho_ratio_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	template = get_i2cho_template(int(template_number))
	print(template)

	if template is None:
		logger.info('template not found')
		data.append(dbus.Byte(CommandControlOpCodes.read_i2cho_ratio_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_i2cho_ratio_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return
	else:
		logger.info('template found')
		first_ratio = float_to_shortfloat(template.first_ratio)
		if template.second_duration > 0:
			flags = set_bit(flags, 0)
		if template.third_duration > 0:
			flags = set_bit(flags, 1)

		data.append(dbus.Byte(flags))
		data.append(dbus.Byte(template.template_number))
		data.append(dbus.Byte(template.first_time_block_number_index))
		data.append(dbus.Byte(template.first_duration & 0xff))
		data.append(dbus.Byte(template.first_duration >> 8))
		data.append(dbus.Byte(first_ratio & 0xff))
		data.append(dbus.Byte(first_ratio >> 8))
		
		if template.second_duration > 0:
			second_ratio = float_to_shortfloat(template.second_ratio)
			data.append(dbus.Byte(template.second_duration & 0xff))
			data.append(dbus.Byte(template.second_duration >> 8))
			data.append(dbus.Byte(second_ratio & 0xff))
			data.append(dbus.Byte(second_ratio >> 8))

		if template.third_duration > 0:
			third_ratio = float_to_shortfloat(template.third_ratio)
			data.append(dbus.Byte(template.third_duration & 0xff))
			data.append(dbus.Byte(template.third_duration >> 8))
			data.append(dbus.Byte(third_ratio & 0xff))
			data.append(dbus.Byte(third_ratio >> 8))

		packet = build_response_packet(CommandControlOpCodes.read_i2cho_ratio_profile_template_response, data)
		send_response(IDSServiceCharacteristics.command_data, packet)
		
		data = []
		data.append(dbus.Byte(CommandControlOpCodes.read_i2cho_ratio_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_i2cho_ratio_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.success))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_write_i2cho_ratio_profile_template(value):
	print('handle_write_i2cho_ratio_profile_template')
	data = []
	flags = value[2]
	template_number = value[3]
	first_time_block_number_index = value[4]

	first_duration = bytes_to_int16(value[5:7][::-1])
	print('first_duration: ' + repr(first_duration))

	first_ratio = shortfloat_bytes_to_float(value[7:9][::-1])
	print('first_ratio: ' + repr(first_ratio))

	if template_number not in TemplateRange.i2cho_template_range:
		logger.info('i2cho template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.write_i2cho_ratio_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.write_i2cho_ratio_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	if(is_set(flags, 1)):
		second_duration = bytes_to_int16(value[9:11][::-1])
		second_ratio = shortfloat_bytes_to_float(value[11:13][::-1])
	else:
		second_duration = 0
		second_ratio = 0

	if(is_set(flags, 2)):
		third_duration = bytes_to_int16(value[13:15][::-1])
		third_ratio = shortfloat_bytes_to_float(value[15:17][::-1])
	else:
		third_duration = 0
		third_ratio = 0

	result = write_i2cho_template(flags,
						 template_number,
						 first_time_block_number_index,
						 first_duration,
						 first_ratio, 
						 second_duration, 
						 second_ratio, 
						 third_duration, 
						 third_ratio)

	logger.info(result)

	if result == True:
		first_duration_data = value[5:7]
		first_ratio_data = value[7:9]
		history_data = str(hex(template_number)[2:]).zfill(2) + str(hex(first_time_block_number_index)[2:]).zfill(2) + ''.join(format(x, '02x') for x in first_duration_data) + ''.join(format(x, '02x') for x in first_ratio_data)
		add_history_event(EventType.i2cho_ratio_profile_template_time_block_changed, history_data)

		data.append(dbus.Byte(0x01)) #flags [end transaction]
		data.append(dbus.Byte(template_number))
		data.append(dbus.Byte(first_time_block_number_index))
		packet = build_response_packet(CommandControlOpCodes.write_i2cho_ratio_profile_template_response, data)
	else:
		'''If the Collector writes to a control point characteristic and the procedure could not be completed for any reason, 
		it will receive a Response Code CP indication with the Response Code Value set to Procedure not completed.
		'''
		data.append(dbus.Byte(CommandControlOpCodes.write_i2cho_ratio_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.write_i2cho_ratio_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
	
	send_response(IDSServiceCharacteristics.command_control_point, packet)
	

def handle_read_target_glucose_range_profile_template(value):
	print('handle_read_target_glucose_range_profile_template')
	template_number = value[2]
	print(repr(template_number))
	data = []

	if template_number not in TemplateRange.target_glucose_range_template_range:
		logger.info('target glucose range profile template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.read_target_glucose_range_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_target_glucose_range_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	template = get_target_glucose_template(int(template_number))
	print(template)
	
	if template is None:
		logger.info('template not found')
		data.append(dbus.Byte(CommandControlOpCodes.read_target_glucose_range_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_target_glucose_range_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return
	else:
		logger.info('template found')
		first_lower_target_glucose_limit = float_to_shortfloat(template.first_lower_target_glucose_limit)
		first_upper_target_glucose_limit = float_to_shortfloat(template.first_upper_target_glucose_limit)
		data.append(dbus.Byte(0x00)) #TO-DO: set the flags correctly
		data.append(dbus.Byte(template.template_number))
		data.append(dbus.Byte(template.first_time_block_number_index))
		data.append(dbus.Byte(template.first_duration & 0xff))
		data.append(dbus.Byte(template.first_duration >> 8))
		data.append(dbus.Byte(first_lower_target_glucose_limit & 0xff))
		data.append(dbus.Byte(first_lower_target_glucose_limit >> 8))
		data.append(dbus.Byte(first_upper_target_glucose_limit & 0xff))
		data.append(dbus.Byte(first_upper_target_glucose_limit >> 8))
		#data.append(dbus.Byte(0x00)) #TO-DO: second duration
		#data.append(dbus.Byte(0x00)) #TO-DO: second lower target glucose limit
		#data.append(dbus.Byte(0x00)) #TO-DO: second upper target glucose limit
		packet = build_response_packet(CommandControlOpCodes.read_target_glucose_range_profile_template_response, data)
		send_response(IDSServiceCharacteristics.command_data, packet)

		data = []
		data.append(dbus.Byte(CommandControlOpCodes.read_target_glucose_range_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.read_target_glucose_range_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.success))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_write_target_glucose_range_profile_template(value):
	print('handle_write_target_glucose_range_profile_template')
	print(value)
	data = []
	flags = value[2]
	template_number = value[3]
	first_time_block_number_index = value[4]

	first_duration = bytes_to_int16(value[5:7][::-1])
	first_lower_target_glucose_limit = shortfloat_bytes_to_float(value[7:9][::-1])
	first_upper_target_glucose_limit = shortfloat_bytes_to_float(value[9:11][::-1])
	
	if template_number not in TemplateRange.target_glucose_range_template_range:
		logger.info('target glucose range profile template number is out of range')
		data.append(dbus.Byte(CommandControlOpCodes.write_target_glucose_range_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.write_target_glucose_range_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.parameter_out_of_range))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)
		send_response(IDSServiceCharacteristics.command_control_point, packet)
		return

	if(is_set(flags, 1)):
		second_duration = bytes_to_int16(value[11:13][::-1])
		second_lower_target_glucose_limit = shortfloat_bytes_to_float(value[13:15][::-1])
		second_upper_target_glucose_limit = shortfloat_bytes_to_float(value[15:17][::-1])
	else:
		second_duration = 0
		second_lower_target_glucose_limit = 0
		second_upper_target_glucose_limit = 0

	result = write_target_glucose_template(flags,
								  template_number, 
								  first_time_block_number_index, 
								  first_duration, 
								  first_lower_target_glucose_limit, 
								  first_upper_target_glucose_limit,
								  second_duration, 
								  second_lower_target_glucose_limit, 
								  second_upper_target_glucose_limit)
	
	logger.info(result)

	if result == True:
		first_duration_data = value[5:7]
		first_lower_target_glucose_limit_data = value[7:9]
		first_upper_target_glucose_limit_data = value[9:11]
		history_data = str(hex(template_number)[2:]).zfill(2) + str(hex(first_time_block_number_index)[2:]).zfill(2) + ''.join(format(x, '02x') for x in first_duration_data) + ''.join(format(x, '02x') for x in first_lower_target_glucose_limit_data) + ''.join(format(x, '02x') for x in first_upper_target_glucose_limit_data) 
		add_history_event(EventType.target_glucose_range_profile_template_time_block_changed, history_data)

		data.append(dbus.Byte(0x01)) #flags [end transaction]
		data.append(dbus.Byte(template_number))
		data.append(dbus.Byte(first_time_block_number_index))
		packet = build_response_packet(CommandControlOpCodes.write_target_glucose_range_profile_template_response, data)
	else:
		'''If the Collector writes to a control point characteristic and the procedure could not be completed for any reason, 
		it will receive a Response Code CP indication with the Response Code Value set to Procedure not completed.
		'''
		data.append(dbus.Byte(CommandControlOpCodes.write_target_glucose_range_profile_template & 0xff))
		data.append(dbus.Byte(CommandControlOpCodes.write_target_glucose_range_profile_template >> 8))
		data.append(dbus.Byte(ResponseCodes.procedure_not_completed))
		packet = build_response_packet(CommandControlOpCodes.response_code, data)

	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_get_max_bolus_amount():
	print('handle_get_max_bolus_amount')
	data = []
	
	max_bolus_amount = float_to_shortfloat(get_max_bolus())

	data.append(dbus.Byte(max_bolus_amount & 0xff))
	data.append(dbus.Byte(max_bolus_amount >> 8))
	packet = build_response_packet(CommandControlOpCodes.get_max_bolus_amount_response, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def handle_set_max_bolus_amount(value):
	print('handle_set_max_bolus_amount')
	data = []
	
	max_bolus_data = value[2:4]
	
	#get previous max bolus as short float string, leading zeros added if necessary
	previous_max_bolus_amount = str(float_to_shortfloat(get_max_bolus())).zfill(4)
	
	#reverse string 2 bytes at a time (LSO, MSO)
	previous_max_bolus_amount = "".join(reversed([previous_max_bolus_amount[i:i+2] for i in range(0, len(previous_max_bolus_amount), 2)]))
	
	#create history data object comprised of previous max bolus amount string, and new max bolus value
	history_data = previous_max_bolus_amount + ''.join(format(x, '02x') for x in max_bolus_data)
	add_history_event(EventType.max_bolus_amount_changed, history_data)

	max_bolus_amount = shortfloat_bytes_to_float(value[2:4][::-1])
	set_max_bolus(max_bolus_amount)

	data.append(dbus.Byte(CommandControlOpCodes.set_max_bolus_amount & 0xff))
	data.append(dbus.Byte(CommandControlOpCodes.set_max_bolus_amount >> 8))
	data.append(dbus.Byte(ResponseCodes.success))
	packet = build_response_packet(CommandControlOpCodes.response_code, data)
	send_response(IDSServiceCharacteristics.command_control_point, packet)


def parse_racp(value):
	print('parse_racp')

	if crc_is_valid(value) == False or crc_counter_is_valid() == False: 
		return None

	opcode = value[0]
	print('op code: ' + repr(opcode))

	if str(int(opcode)) == str(RecordAccessControlPointOpCodes.report_number_of_stored_records):
		handle_report_number_of_stored_records(value)
	if str(int(opcode)) == str(RecordAccessControlPointOpCodes.report_stored_records):
		handle_report_stored_records(value)
	if str(int(opcode)) == str(RecordAccessControlPointOpCodes.delete_stored_records):
		handle_delete_stored_records(value)

def handle_report_number_of_stored_records(value):
	print('handle_report_number_of_stored_records')
	data = []
	count = get_row_count(Event)
	logger.info('history count: ' + str(count))
	
	data.append(dbus.Byte(RecordAccessControlPointOperators.null))
	data.append(dbus.Byte(count & 0xff))
	data.append(dbus.Byte(count >> 8))
	data.append(dbus.Byte(count >> 16))
	data.append(dbus.Byte(count >> 24))
	packet = build_response_packet(RecordAccessControlPointOpCodes.number_of_stored_records_response, data)
	send_response(IDSServiceCharacteristics.racp, packet)

def handle_report_stored_records(value):
	print('handle_report_stored_records')
	data = []
	
	operator = value[1]
	print('operator: ' + repr(operator))

	if str(int(operator)) == str(RecordAccessControlPointOperators.all_records):
		print('all records')
		count = get_history_count()
		logger.info('history count: ' + str(count))
		if count == 0:
			#https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.record_access_control_point.xml

			''' page 81/74
			If the Server does not locate any records matching the Filter Type criteria of the request, the Server shall indicate the Record Access Control Point with a Response Code Op Code, Request Op Code of Report Stored Records, and a Response Code Value in the Operand set to No Records Found.
			'''
			data.append(dbus.Byte(RecordAccessControlPointOpCodes.report_stored_records)) #Request Op Code of Report Stored Records
			data.append(dbus.Byte(0x06)) #Response Code Value in the Operand set to No Records Found
			packet = build_response_packet(RecordAccessControlPointOpCodes.response_code, data) #Response Code Op Code
			send_response(IDSServiceCharacteristics.racp, packet)
		else:
			report_all_history_events()
	if str(int(operator)) == str(RecordAccessControlPointOperators.greater_than_or_equal_to):
		print('greater_than_or_equal_to')
	if str(int(operator)) == str(RecordAccessControlPointOperators.less_than_or_equal_to):
		print('less_than_or_equal_to')
	if str(int(operator)) == str(RecordAccessControlPointOperators.within_range_of):
		print('within_range_of')
	if str(int(operator)) == str(RecordAccessControlPointOperators.first_record):
		print('first_record')
	if str(int(operator)) == str(RecordAccessControlPointOperators.last_record):
		print('last_record')

def handle_delete_stored_records(value):
	print('handle_delete_stored_records')
	response = []
	
	operator = value[1]
	print('operator: ' + repr(operator))
	
	if str(int(operator)) == str(RecordAccessControlPointOperators.all_records):
		print('all records')
	if str(int(operator)) == str(RecordAccessControlPointOperators.greater_than_or_equal_to):
		print('greater_than_or_equal_to')
	if str(int(operator)) == str(RecordAccessControlPointOperators.less_than_or_equal_to):
		print('less_than_or_equal_to')
	if str(int(operator)) == str(RecordAccessControlPointOperators.within_range_of):
		print('within_range_of')
	if str(int(operator)) == str(RecordAccessControlPointOperators.first_record):
		print('first_record')
	if str(int(operator)) == str(RecordAccessControlPointOperators.last_record):
		print('last_record')
	return response

def parse_current_time(value):
	logger.info('parse_current_time')
	global time_zone
	global dst
	date_data = value[0:7]
	history_data = str(int(0x0F)) + ''.join(format(x, '02x') for x in date_data) + str(time_zone).zfill(2) + str(dst).zfill(2) 
	print(type(history_data))
	add_history_event(EventType.reference_time, history_data)
	
def parse_local_time_information(value):
	global time_zone
	global dst

	logger.info('parse_local_time_information')
	time_zone = format(value[0], '02x')
	dst = format(value[1], '02x')
	logger.info('time zone: ' + str(time_zone))
	logger.info('dst: ' + str(dst))

