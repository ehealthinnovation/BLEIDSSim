
class ActiveBasalRateDeliveryFlags(object):
	tbr_present_bit = 0
	tbr_template_number_present_bit = 1
	basal_delivery_context_present_bit = 2

class BasalRateProfileTemplateFlags(object):
	end_transaction_bit = 0
	second_time_block_present_bit = 1
	third_time_block_present_bit = 2

class BolusTemplateFlags(object):
	bolus_delay_time_present_bit = 0
	bolus_delivery_reason_correction_bit = 1
	bolus_delivery_reason_meal_bit = 2

class TBRAdjustmentFlags(object):
	tbr_template_number_present_bit = 0
	tbr_delivery_context_present_bit = 1
	change_tbr_bit = 2

class BolusFlags(object):
	bolus_delay_time_present_bit = 0
	bolus_template_number_present_bit = 1
	bolus_activation_type_present_bit = 0
	bolus_delivery_reason_correction_bit = 0
	bolus_delivery_reason_meal_bit = 0
	
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

class ResponseCodes(object):
	success = 0x0F
	op_code_not_supported = 0x70
	invalid_operand = 0x71
	procedure_not_completed = 0x72
	parameter_out_of_range = 0x73
	procedure_not_applicable = 0x74
	plausibility_check_failed = 0x75
	maximum_bolus_number_reached = 0x76

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

class TemplateTypeValues(object):
	undetermined = 0x0F
	basal_rate_profile_template = 0x33
	tbr_template = 0x3C
	bolus_template = 0x55
	isf_profile_template = 0x5A
	i2cho_ratio_profile_template = 0x66
	target_glucose_range_profile_template = 0x96

class RecordAccessControlPointOpCodes(object):
	response_code = 0x0F
	report_stored_records = 0x33
	delete_stored_records = 0x3C
	abort_operation = 0x55
	report_number_of_stored_records = 0x5A
	number_of_stored_records_response = 0x66

class RecordAccessControlPointOperators(object):
	null = 0x0F
	all_records = 0x33
	less_than_or_equal_to = 0x3C
	greater_than_or_equal_to = 0x55
	within_range_of = 0x5A
	first_record = 0x66
	last_record = 0x69
	
class RecordAccessControlPointOperandFilters(object):
	sequence_number = 0x0F
	sequence_number_filtered_by_reference_time_event = 0x33
	sequence_number_filtered_by_nonreference_time_event = 0x3C

class RecordAccessControlPointResponseCodes(object):
	procedure_not_applicable = 0x0A
	success = 0xF0
