import dbus
import collections

from helper import *
from crc import *
from shortfloat import *
from config import *

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

class TherapyControlState(object):
	undetermined = 0x0F
	stop = 0x33
	pause = 0x3C
	run	= 0x55

class OperationalState(object):
	undetermined = 0x0F
	off = 0x33
	standby = 0x3C
	preparing = 0x55
	priming = 0x5A
	waiting = 0x66
	ready = 0x96

class StatusReaderOpCodes(object):
	response_code = 0x0303
	reset_status = 0x030C
	get_active_bolus_ids = 0x0330
	get_active_bolus_ids_response = 0x033F
	get_active_bolus_delivery = 0x0356
	get_active_bolus_delivery_response = 0x0359
	get_active_basal_rate_delivery = 0x0365
	get_active_basal_rate_delivery_response = 0x036A
	get_total_daily_insulin_status = 0x0395
	get_total_daily_insulin_status_response = 0x039A
	get_counter = 0x03A6
	get_counter_response = 0x03A9
	get_delivered_insulin = 0x03C0
	get_delivered_insulin_response = 0x03CF
	get_insulin_on_board = 0x03F3
	get_insulin_on_board_response = 0x03FC

#class StatusReaderResponseCodes(object):
class ResponseCodes(object):
	success = 0x0F
	op_code_not_supported = 0x70
	invalid_operand = 0x71
	procedure_not_supported = 0x72
	parameter_out_of_range = 0x73
	procedure_not_applicable = 0x74

class BolusValueSelection(object):
	programmed = 0x0F
	remaining = 0x33
	delivered = 0x3C

class BolusType(object):
	undetermined = 0x0F
	fast = 0x33
	extended = 0x3C
	multiwave = 0x55

class BolusActivationType(object):
	undetermined = 0x0F
	manual_bolus = 0x33
	recommended_bolus = 0x3C
	manually_changed_recommended_bolus = 0x55
	commanded_bolus = 0x5A

class TBRType(object):
	undetermined = 0x0F
	absolute = 0x33
	relative = 0x3C

class BasalDeliveryContext(object):
	undetermined = 0x0F
	device_based = 0x33
	remote_control = 0x3C
	ap_controller = 0x55

class CommandControlOpCodes(object):
	response_code = 0x0F55
	set_therapy_control_state = 0x0F5A
	set_flight_mode = 0x0F66
	snooze_annunciation = 0x0F69
	snooze_annunciation_response = 0x0F96
	confirm_annunciation = 0x0F99
	confirm_annunciation_response = 0x0FA5
	read_basal_rate_profile_template = 0x0FAA
	read_basal_rate_profile_template_response = 0x0FC3
	write_basal_rate_profile_template = 0x0FCC
	write_basal_rate_profile_template_response = 0x0FF0
	set_tbr_adjustment = 0x0FFF
	cancel_tbr_adjustment = 0x1111
	get_tbr_template = 0x111E
	get_tbr_template_response = 0x1122
	set_tbr_template = 0x112D
	set_tbr_template_response = 0x1144
	set_bolus = 0x114B
	set_bolus_response = 0x1177
	cancel_bolus = 0x1178
	cancel_bolus_response = 0x1187
	get_available_boluses = 0x1188
	get_available_boluses_response = 0x11B4
	get_bolus_template = 0x11BB
	get_bolus_template_response = 0x11D2
	set_bolus_template = 0x11DD
	set_bolus_template_response = 0x11E1
	get_template_status_and_details = 0x11EE
	get_template_status_and_details_response = 0x1212
	reset_template_status = 0x121D
	reset_template_status_response = 0x1221
	activate_profile_templates = 0x122E
	activate_profile_templates_response = 0x1247
	get_activated_profile_templates = 0x1248
	get_activated_profile_templates_response = 0x1274
	start_priming = 0x127B
	stop_priming = 0x1284
	set_initial_reservoir_fill_level = 0x128B
	reset_reservoir_insulin_operation_time = 0x12B7
	read_isf_profile_template = 0x12B8
	read_isf_profile_template_response = 0x12D1
	write_isf_profile_template = 0x12DE
	write_isf_profile_template_response = 0x12E2
	read_i2cho_ratio_profile_template = 0x12ED
	read_i2cho_ratio_profile_template_response = 0x1414
	write_i2cho_ratio_profile_template = 0x141B
	write_i2cho_ratio_profile_template_response = 0x1427
	read_target_glucose_range_profile_template = 0x1428
	read_target_glucose_range_profile_template_response = 0x1441
	write_target_glucose_range_profile_template = 0x144E
	write_target_glucose_range_profile_template_response = 0x1472
	get_max_bolus_amount = 0x147D
	get_max_bolus_amount_response = 0x1482
	set_max_bolus_amount = 0x148D


#def ids_init():
#	global crc_count
#	crc_count = int()

def crc_is_valid(value):
	packet_len = len(value)

	packet_crc = value[packet_len-2:packet_len]
	packet_crc = ''.join(map(lambda b: format(b, "02x"), packet_crc))

	packet_data = value[0:packet_len-2]
	calculated_crc = hex(crc_calculate(packet_data))[2:].zfill(4)
	calculated_crc = "".join(reversed([calculated_crc[i:i+2] for i in range(0, len(calculated_crc), 2)]))
	
	print('packet_crc: ' + repr(packet_crc))
	print('calculated_crc: ' + repr(calculated_crc))

	if calculated_crc == packet_crc:
		return True
	else:
		return False

	return False


def get_ids_status():
	print('get_ids_status')
	
	therapy = TherapyControlState.run
	state = OperationalState.ready
	
	status = [therapy, state]
	reservoir_remaining = float_to_shortfloat(5.22)
	status.append(reservoir_remaining & 0xff)
	status.append(reservoir_remaining >> 8)
	# reservoir attached
	status.append(1)
	# crc-counter
	status.append(0)
	crc = crc_calculate(status)
	status.append(crc & 0xff)
	status.append(crc >> 8)

	return status


def get_ids_status_changed():
	print('get_ids_status_changed')
	ids_status = 0

	status = get_dict('running', 'STATUS_CHANGED')
	
	for key in status:
		if status[key] == '1':
			ids_status = set_bit(ids_status, int(status.keys().index(key)))

	status = [ids_status >> 8, ids_status & 0xff]
	status.append(0)
	crc = crc_calculate(status)
	status.append(crc & 0xff)
	status.append(crc >> 8)
		
	return status


def get_ids_features():
	print('get_ids_features')
	ids_features = 0
	features = 0

	dict_features = get_dict('configuration', 'FEATURES')
	print(repr(dict_features))

	for key in dict_features:
		if dict_features[key] == '1':
			ids_features = set_bit(ids_features, int(dict_features.keys().index(key)))

	features = [ids_features & 0xff, ids_features >> 8, 0x00]

	insulin_concentration = float_to_shortfloat(5.22)
	features.insert(0, insulin_concentration & 0xff)
	features.insert(1, insulin_concentration >> 8)

	features.insert(0, 0)

	crc = crc_calculate(features)	
	features.insert(0, crc & 0xff)
	features.insert(1, crc >> 8)

	return features


def get_ids_annunciation_status():
	print('get_ids_annunciation_status')
	flags = 0

	dict_annunciation = get_dict('configuration', 'ANNUNCIATION_STATUS')
	print(repr(dict_annunciation))

	for key in dict_annunciation:
		if dict_annunciation[key] == '1':
			flags = set_bit(flags, int(dict_annunciation.keys().index(key)))

	annunciation = [flags]

	#annunciation instance id
	annunciation.append(0x01)
	annunciation.append(0x00)

	#annunciation type
	annunciation.append(AnnunciationTypeValues.battery_low & 0xff)
	annunciation.append(AnnunciationTypeValues.battery_low >> 8)
	
	annunciation.append(AnnunciationStatusValues.snoozed)	

	#counter
	annunciation.append(0x00)

	crc = crc_calculate(annunciation)
	annunciation.append(crc & 0xff)
	annunciation.append(crc >> 8)

	return annunciation

'''
pg. 32
If the Reset Status Op Code is written to the IDD Status Reader Control Point with an Operand containing a Flags field, 
the Server shall reset the status exposed by the IDD Status Changed characteristic.

The Server shall confirm the status reset by indicating the IDD Status Reader Control Point with a Response Code Op Code, 
a Request Op Code of Reset Status and Response Code Value of Success.
'''
def parse_ids_status_reader_control_point(value):
	print('parse_ids_status_reader_control_point')
	response = []

	if(crc_is_valid(value) == False):
		return None

	opcode_bytes = value[0:2]
	opcode = ''.join(map(lambda b: format(b, "02x"), opcode_bytes))
	
	print('op code: ' + repr(opcode))

	if str(int(opcode,16)) == str(StatusReaderOpCodes.reset_status):
		response = handle_reset_status()
		return response
	elif str(int(opcode,16)) == str(StatusReaderOpCodes.get_active_bolus_ids):
		response = handle_get_active_bolus_ids()
		return response
	elif str(int(opcode,16)) == str(StatusReaderOpCodes.get_active_bolus_delivery):
		response = handle_get_active_bolus_delivery(value)
		return response
	elif str(int(opcode,16)) == str(StatusReaderOpCodes.get_active_basal_rate_delivery):
		response = handle_get_active_basal_rate_delivery()
		return response
	elif str(int(opcode,16)) == str(StatusReaderOpCodes.get_total_daily_insulin_status):
		response = handle_get_total_daily_insulin_status()
		return response
	elif str(int(opcode,16)) == str(StatusReaderOpCodes.get_counter):
		response = handle_get_counter(value)
		return response
	elif str(int(opcode,16)) == str(StatusReaderOpCodes.get_delivered_insulin):
		response = handle_get_delivered_insulin()
		return response
	elif str(int(opcode,16)) == str(StatusReaderOpCodes.get_insulin_on_board):
		response = handle_get_insulin_on_board()
		return response
		

def handle_reset_status():
	print("handle_reset_status")
	response = []

	# 03 03 = response code, 03 0C = reset status, 0F = success
	response.append(dbus.Byte(StatusReaderOpCodes.response_code & 0xff))
	response.append(dbus.Byte(StatusReaderOpCodes.response_code >> 8))
	response.append(dbus.Byte(StatusReaderOpCodes.reset_status & 0xff))
	response.append(dbus.Byte(StatusReaderOpCodes.reset_status >> 8))
	response.append(dbus.Byte(ResponseCodes.success))
	response.append(dbus.Byte(0x00))
	crc = crc_calculate(response)
	response.append(dbus.Byte(crc & 0xff))
	response.append(dbus.Byte(crc >> 8))
	return response

def handle_get_active_bolus_ids():
	print("get_active_bolus_ids")
	response = []

	# return 2 active boluses with an ID of 0001 and 0002
	response.append(dbus.Byte(StatusReaderOpCodes.get_active_bolus_ids_response & 0xff))
	response.append(dbus.Byte(StatusReaderOpCodes.get_active_bolus_ids_response >> 8))
	response.append(dbus.Byte(0x02))
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x01))
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x02))
	#crc counter
	response.append(dbus.Byte(0x00))
	crc = crc_calculate(response)
	response.append(dbus.Byte(crc & 0xff))
	response.append(dbus.Byte(crc >> 8))
	return response


def handle_get_active_bolus_delivery(value):
	print('handle_get_active_bolus_delivery')
	response = []
	flags = 0

	#extract the bolus id from the request packet
	bolus_id_bytes = value[2:4]
	#bolus_id = ''.join(map(lambda b: format(b, "02x"), bolus_id_bytes))

	bolus_flags = collections.OrderedDict((('Bolus_delay_time_present', 1),
					 			 ('Bolus_template_number_present', 1),
					 			 ('Bolus_activation_type_present', 1),
								 ('Bolus_delivery_reason_correction', 1),
								 ('Bolus_delivery_reason_meal', 1)
								))

	for key in bolus_flags:
		if bolus_flags[key] == 1:
			flags = set_bit(flags, int(bolus_flags.keys().index(key)))

	response.append(dbus.Byte(StatusReaderOpCodes.get_active_bolus_delivery_response & 0xff))
	response.append(dbus.Byte(StatusReaderOpCodes.get_active_bolus_delivery_response >> 8))
	response.append(dbus.Byte(flags))
	
	#bolus ID
	response.append(bolus_id_bytes[0])
	response.append(bolus_id_bytes[1])

	response.append(dbus.Byte(BolusType.fast))

	fast_amount = float_to_shortfloat(5.22)
	response.append(fast_amount & 0xff)
	response.append(fast_amount >> 8)
	
	# set to all zeros if type is fast
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x00))

	# bolus delay time (5 minutes)
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x05))

	# bolus template number
	response.append(dbus.Byte(0x01))

	# bolus activation type
	response.append(dbus.Byte(BolusActivationType.manual_bolus))

	#crc counter
	response.append(dbus.Byte(0x00))
	crc = crc_calculate(response)
	response.append(dbus.Byte(crc & 0xff))
	response.append(dbus.Byte(crc >> 8))
	return response

def handle_get_active_basal_rate_delivery():
	print('handle_get_active_basal_rate_delivery')
	response = []
	flags = 0

	active_basal_rate_flags = collections.OrderedDict((('tbr_present', 1),
					 			 ('tbr_template_number_present', 1),
					 			 ('basal_delivery_context_present', 1)
								))

	
	for key in active_basal_rate_flags:
		if active_basal_rate_flags[key] == 1:
			flags = set_bit(flags, int(active_basal_rate_flags.keys().index(key)))

	response.append(dbus.Byte(StatusReaderOpCodes.get_active_basal_rate_delivery_response & 0xff))
	response.append(dbus.Byte(StatusReaderOpCodes.get_active_basal_rate_delivery_response >> 8))
	response.append(dbus.Byte(flags))
	
	# active basal rate profile template number
	response.append(dbus.Byte(0x01))
	
	config_value = float_to_shortfloat(1.25)
	response.append(config_value & 0xff)
	response.append(config_value >> 8)
	
	response.append(dbus.Byte(TBRType.absolute))

	tbr_adjustment_value = float_to_shortfloat(1.43)
	response.append(tbr_adjustment_value & 0xff)
	response.append(tbr_adjustment_value >> 8)
	
	# time programmed (10 minutes)
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x0A))

	# time remaining (9 minutes)
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x09))

	# template number
	response.append(dbus.Byte(0x01))

	# basal delivery context
	response.append(dbus.Byte(BasalDeliveryContext.device_based))
	
	#crc counter
	response.append(dbus.Byte(0x00))
	crc = crc_calculate(response)
	response.append(dbus.Byte(crc & 0xff))
	response.append(dbus.Byte(crc >> 8))
	
	return response

def handle_get_total_daily_insulin_status():
	print('handle_get_total_daily_insulin_status')
	response = []

	response.append(dbus.Byte(StatusReaderOpCodes.get_total_daily_insulin_status_response & 0xff))
	response.append(dbus.Byte(StatusReaderOpCodes.get_total_daily_insulin_status_response >> 8))
	
	total_daily_insulin_sum_of_bolus_delivered = float_to_shortfloat(1.25)
	response.append(dbus.Byte(total_daily_insulin_sum_of_bolus_delivered & 0xff))
	response.append(dbus.Byte(total_daily_insulin_sum_of_bolus_delivered >> 8))

	total_daily_insulin_sum_of_basal_delivered = float_to_shortfloat(3.12)
	response.append(dbus.Byte(total_daily_insulin_sum_of_basal_delivered & 0xff))
	response.append(dbus.Byte(total_daily_insulin_sum_of_basal_delivered >> 8))

	total_daily_insulin_sum_of_bolus_and_basal_delivered = float_to_shortfloat(4.37)
	response.append(dbus.Byte(total_daily_insulin_sum_of_bolus_and_basal_delivered & 0xff))
	response.append(dbus.Byte(total_daily_insulin_sum_of_bolus_and_basal_delivered >> 8))

	#crc counter
	response.append(dbus.Byte(0x00))
	crc = crc_calculate(response)
	response.append(dbus.Byte(crc & 0xff))
	response.append(dbus.Byte(crc >> 8))
	
	return response

def handle_get_counter(value):
	print('handle_get_counter')
	response = []

	response.append(dbus.Byte(StatusReaderOpCodes.get_counter_response & 0xff))
	response.append(dbus.Byte(StatusReaderOpCodes.get_counter_response >> 8))

	counter_type = value[2]
	counter_value = value[3]

	response.append(dbus.Byte(counter_type))
	response.append(dbus.Byte(counter_value))

	# counter value (minutes)
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x05))

	#crc counter
	response.append(dbus.Byte(0x00))
	crc = crc_calculate(response)
	response.append(dbus.Byte(crc & 0xff))
	response.append(dbus.Byte(crc >> 8))

	return response

def handle_get_delivered_insulin():
	print('handle_get_delivered_insulin')
	response = []

	response.append(dbus.Byte(StatusReaderOpCodes.get_delivered_insulin_response & 0xff))
	response.append(dbus.Byte(StatusReaderOpCodes.get_delivered_insulin_response >> 8))

	deliveredBolusHex = float_to_hex(17.5)
	deliveredBolus = bytearray.fromhex(deliveredBolusHex)

	response.append(dbus.Byte(deliveredBolus[3]))
	response.append(dbus.Byte(deliveredBolus[2]))
	response.append(dbus.Byte(deliveredBolus[1]))
	response.append(dbus.Byte(deliveredBolus[0]))

	deliveredBasalHex = float_to_hex(10.2)
	deliveredBasal = bytearray.fromhex(deliveredBasalHex)
	response.append(dbus.Byte(deliveredBasal[3]))
	response.append(dbus.Byte(deliveredBasal[2]))
	response.append(dbus.Byte(deliveredBasal[1]))
	response.append(dbus.Byte(deliveredBasal[0]))

	#crc counter
	response.append(dbus.Byte(0x00))
	crc = crc_calculate(response)
	response.append(dbus.Byte(crc & 0xff))
	response.append(dbus.Byte(crc >> 8))

	return response

def handle_get_insulin_on_board():
	print('handle_get_insulin_on_board')
	response = []

	response.append(dbus.Byte(StatusReaderOpCodes.get_insulin_on_board_response & 0xff))
	response.append(dbus.Byte(StatusReaderOpCodes.get_insulin_on_board_response >> 8))
	response.append(dbus.Byte(0x01)) #flags byte
	
	insulin_onboard = float_to_shortfloat(2.05)
	response.append(insulin_onboard & 0xff)
	response.append(insulin_onboard >> 8)

	#remaining duration (minutes)
	response.append(dbus.Byte(0x00))
	response.append(dbus.Byte(0x0d))
	
	#crc counter
	response.append(dbus.Byte(0x00))
	crc = crc_calculate(response)
	response.append(dbus.Byte(crc & 0xff))
	response.append(dbus.Byte(crc >> 8))
	return response

def parse_ids_command_control_point(value):
	print('parse_ids_command_control_point')
	response = []

	if(crc_is_valid(value) == False):
		return None

	opcode_bytes = value[0:2]
	opcode = ''.join(map(lambda b: format(b, "02x"), opcode_bytes))
	
	print('op code: ' + repr(opcode))

	if str(int(opcode,16)) == str(CommandControlOpCodes.set_therapy_control_state):
		print('set_therapy_control_state')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.set_flight_mode):
		handle_set_flight_mode()
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.snooze_annunciation):
		print('snooze_annunciation')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.confirm_annunciation):
		print('confirm_annunciation')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.read_basal_rate_profile_template):
		print('read_basal_rate_profile_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.write_basal_rate_profile_template):
		print('write_basal_rate_profile_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.set_tbr_adjustment):
		print('set_tbr_adjustment')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.cancel_tbr_adjustment):
		print('cancel_tbr_adjustment')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.get_tbr_template):
		print('get_tbr_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.set_tbr_template):
		print('set_tbr_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.set_bolus):
		print('set_bolus')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.cancel_bolus):
		print('cancel_bolus')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.get_available_boluses):
		print('get_available_boluses')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.get_bolus_template):
		print('get_bolus_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.set_bolus_template):
		print('set_bolus_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.get_template_status_and_details):
		print('get_template_status_and_details')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.reset_template_status):
		print('reset_template_status')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.activate_profile_templates):
		print('activate_profile_templates')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.get_activated_profile_templates):
		print('get_activated_profile_templates')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.start_priming):
		print('start_priming')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.stop_priming):
		print('stop_priming')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.set_initial_reservoir_fill_level):
		print('set_initial_reservoir_fill_level')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.reset_reservoir_insulin_operation_time):
		print('reset_reservoir_insulin_operation_time')
		return responsels
	elif str(int(opcode,16)) == str(CommandControlOpCodes.read_isf_profile_template):
		print('read_isf_profile_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.write_isf_profile_template):
		print('write_isf_profile_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.read_i2cho_ratio_profile_template):
		print('read_i2cho_ratio_profile_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.write_i2cho_ratio_profile_template):
		print('write_i2cho_ratio_profile_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.read_target_glucose_range_profile_template):
		print('read_target_glucose_range_profile_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.write_target_glucose_range_profile_template):
		print('write_target_glucose_range_profile_template')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.get_max_bolus_amount):
		print('get_max_bolus_amount')
		return response
	elif str(int(opcode,16)) == str(CommandControlOpCodes.set_max_bolus_amount):
		print('set_max_bolus_amount')
		return response

def handle_set_flight_mode():
	print('set_flight_mode')
	
	update_setting('running', 'FLIGHT_MODE', 'enabled', '1')

	response = []
	#The Server shall confirm the receipt of this command by indicating the IDD Command Control Point with a Response Code Op Code,
	#a Request Op Code of Set Flight Mode, and a Response Code Value of Success.
	response.append(dbus.Byte(StatusReaderOpCodes.response_code & 0xff))
	response.append(dbus.Byte(StatusReaderOpCodes.response_code >> 8))
	response.append(dbus.Byte(StatusReaderOpCodes.set_flight_mode & 0xff))
	response.append(dbus.Byte(StatusReaderOpCodes.set_flight_mode >> 8))
	response.append(dbus.Byte(ResponseCodes.success))
	print(repr(response))
	
	return response

def parse_racp(value):
	print("parse_racp")
	print(value)

