
import collections

from helper import *
from crc import *
from shortfloat import *

#page 95/96
'''
[Therapy Control State Field - UINT8]
Undetermined 	0x0F
Stop 			0x33
Pause			0x3C
Run				0x55

[Operational State Field - UINT8]
Undetermined 	0x0F
Off 			0x33
Standby			0x3C
Preparing		0x55
Priming			0x5A
Waiting			0x66
Ready			0x96

[Reservoir Remaining Amount - SFLOAT]

[Flags - 8 bit]
Reservoir Attached 		Bit 0
'''


class TherapyControlState(object):
		Undetermined = 0x0F
		Stop = 0x33
		Pause = 0x3C
		Run	= 0x55

class OperationalState(object):
		Undetermined = 0x0F
		Off = 0x33
		Standby = 0x3C
		Preparing = 0x55
		Priming = 0x5A
		Waiting = 0x66
		Ready = 0x96

def ids_init():
	global crc_count
	print('ids_init')
	crc_count = int()

def get_ids_status():
	print('get_ids_status')
	
	therapy = TherapyControlState.Run
	operationalState = OperationalState.Ready
	
	status = [therapy, operationalState]
	reservoirRemainingAmount = float_to_shortfloat(5.22)
	status.append(reservoirRemainingAmount >> 8)
	status.append(reservoirRemainingAmount & 0xff)

	status.append(0)
	crc = crc_calculate(status)
	status.append(crc >> 8)
	status.append(crc & 0xff)

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
	status.append(crc >> 8)
	status.append(crc & 0xff)
	
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
	features.append(shortfloat_value >> 8)
	features.append(shortfloat_value & 0xff)
	features.append(0)

	crc = crc_calculate(features)
	features.append(crc >> 8)
	features.append(crc & 0xff)

	return features
