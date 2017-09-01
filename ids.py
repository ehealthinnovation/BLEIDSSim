
import collections

from helper import *
from crc import *
from shortfloat import *

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
	status.append(0) # TO-DO: crc counter
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
	features.append(0) # TO-DO: crc counter

	crc = crc_calculate(features)
	features.append(crc >> 8)
	features.append(crc & 0xff)

	return features
