
import collections

from helper import *
from crc import *
from shortfloat import *


class AnnunciationTypeValues(object):
	system_issue = 0x000F
	mechanical_issue = 0x0033
	occlusion_detected = 0x003C
	reservoir_issue	= 0x0055
	reservoir_empty	= 0x005A
	reservoir_low = 0x0066
	priming_issue = 0x0069
	infusion_set_incomplete = 0x0069
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

class OpCodes(object):
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

class ResponseCodes(object):
	success = 0x0F
	op_code_not_supported = 0x70
	invalid_operand = 0x71
	procedure_not_supported = 0x72
	parameter_out_of_range = 0x73
	procedure_not_applicable = 0x74


def ids_init():
	global crc_count
	crc_count = int()

def get_ids_status():
	print('get_ids_status')
	
	therapy = TherapyControlState.run
	operationalState = OperationalState.ready
	
	status = [therapy, operationalState]
	reservoirRemainingAmount = float_to_shortfloat(5.22)
	status.append(reservoirRemainingAmount & 0xff)
	status.append(reservoirRemainingAmount >> 8)

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

	status = collections.OrderedDict((('ids_status_therapy_control_status_changed', 1),
					 			 ('ids_status_operational_state_changed', 1),
					 			 ('ids_status_reservoir_status_changed', 1),
					 			 ('ids_status_annunciation_status_changed', 1),
					 			 ('ids_status_total_daily_insulin_status_changed', 1),
					 			 ('ids_status_active_basal_rate_status_changed', 1),
					 			 ('ids_status_active_bolus_status_changed', 1),
					 			 ('ids_status_history_event_recorded', 1)
								))
	for key in status:
		if status[key] == 1:
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

	features = collections.OrderedDict((('ids_features_e2e_protection_supported', 1),
					 			 ('ids_features_basal_rate_supported', 1),
					 			 ('ids_features_tbr_absolute_supported', 1),
								 ('ids_features_tbr_relative_supported', 1),
								 ('ids_features_tbr_template_supported', 1),
								 ('ids_features_fast_bolus_supported', 1),
								 ('ids_features_extended_bolus_supported', 1),
								 ('ids_features_multiwave_bolus_supported', 1),
								 ('ids_features_bolus_delay_supported', 1),
								 ('ids_features_bolus_template_supported', 1),
								 ('ids_features_bolus_activation_type_supported', 1),
								 ('ids_features_multiple_bond_supported', 1),
								 ('ids_features_isf_profile_template_supported', 1),
								 ('ids_features_i2cho_ratio_profile_template_supported', 1),
								 ('ids_features_target_glucose_range_profile_template_supported', 1),
								 ('ids_features_insulin_onboard_supported', 1)
								 #('ids_features_feature_extension', 1)
								))

	for key in features:
		if features[key] == 1:
			ids_features = set_bit(ids_features, int(features.keys().index(key)))

	features = [0x00, ids_features >> 8, ids_features & 0xff]
	
	shortfloat_value = float_to_shortfloat(5.22)
	
	features.append(shortfloat_value & 0xff)
	features.append(shortfloat_value >> 8)
	
	features.append(0)

	crc = crc_calculate(features)
	
	features.append(crc & 0xff)
	features.append(crc >> 8)
	
	return features


def get_ids_annunciation_status():
	print('get_ids_annunciation_status')
	flags = 0

	annunciation_flags = collections.OrderedDict((('annunciation_present', 1),
					 			 ('AuxInfo1_present', 0),
					 			 ('AuxInfo2_present', 0),
								 ('AuxInfo3_present', 0),
								 ('AuxInfo4_present', 0),
								 ('AuxInfo5_present', 0)
								))

	for key in annunciation_flags:
		if annunciation_flags[key] == 1:
			flags = set_bit(flags, int(annunciation_flags.keys().index(key)))

	annunciation = [flags]

	annunciation.append(0x12)
	annunciation.append(0x34)

	annunciation.append(AnnunciationTypeValues.battery_low >> 8)
	annunciation.append(AnnunciationTypeValues.battery_low & 0xff)
	
	annunciation.append(AnnunciationStatusValues.snoozed)	

	#counter
	annunciation.append(0x00)

	crc = crc_calculate(annunciation)
	annunciation.append(crc >> 8)
	annunciation.append(crc & 0xff)

	return annunciation


def parse_ids_status_reader_control_point(value):
	print('parse_ids_status_reader_control_point')
	print(value)

def parse_ids_command_control_point(value):
	print('parse_ids_command_control_point')
	print(value)

def parse_racp(value):
	print("parse_racp")
	print(value)

