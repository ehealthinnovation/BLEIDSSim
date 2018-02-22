import logging
import os
from db import *
from config import *


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemplateRange(object):
	basal_rate_profile_template_range = range(0, 5)
	tbr_template_range = range(5, 10)
	bolus_template_range = range(10, 15)
	isf_template_range = range(15, 20)
	i2cho_template_range = range(20, 25)
	target_glucose_range_template_range = range(30, 35)

class TemplateType(object):
	basal_rate_profile_template_type = 0x33
	tbr_template_type = 0x3C
	bolus_template_type = 0x55
	isf_profile_template_type = 0x5A
	i2cho_template_type = 0x66
	target_glucose_template_type = 0x96

class TemplateLookup(Base):
    __tablename__ = 'template_lookup'
    id = Column(Integer, primary_key=True)
    template_number = Column("Template Number", Integer, unique=True)
    template_type = Column("Template Type", Integer, default = 15) #0x0F = undetermined
    table_name = Column("Table Name", String)
    active = Column("Active", Integer, default=0)
    configurable = Column("Configurable", Integer, default=0)
    configured = Column("Configured", Integer, default=0)
    
class BasalRateProfileTemplate(Base):
	__tablename__ = 'basal_rate_profile_templates'

	id = Column(Integer, primary_key=True)
	flags = Column(Integer)
	template_number = Column("Template Number", Integer, unique=True)
	first_time_block_number_index = Column("First Time Block Number Index", Integer)
	first_duration = Column("First Duration", Integer)
	first_rate = Column("First Rate", Integer)
	second_duration = Column("Second Duration", Integer, default=0)
	second_rate = Column("Second Rate", Integer, default=0)
	third_duration = Column("Third Duration", Integer, default=0)
	third_rate = Column("Third Rate", Integer, default=0)

	def __str__(self):
		return "<BasalRateProfileTemplate(flags='%s', template_number='%s', first_time_block_number_index='%s', first_duration='%s', first_rate='%s', second_duration='%s', second_rate='%s', third_duration='%s', third_rate='%s')>" % (
			self.flags, self.template_number, self.first_time_block_number_index, self.first_duration, self.first_rate, self.second_duration, self.second_rate, self.third_duration, self.third_rate)


class TBRTemplate(Base):
	__tablename__ = 'tbr_templates'

	id = Column(Integer, primary_key=True)
	template_number = Column("Template Number", Integer, unique=True)
	tbr_type = Column("TBR Type", Integer)
	tbr_adjustment_value = Column("TBR Adjustment Value", Integer)
	tbr_duration = Column("TBR Duration", Integer)

	def __str__(self):
		return "<TBRTemplate(template_number='%s', tbr_type='%s', tbr_adjustment_value='%s', tbr_duration='%s')>" % (
			self.template_number, self.tbr_type, self.tbr_adjustment_value, self.tbr_duration)


class BolusTemplate(Base):
	__tablename__ = 'bolus_templates'

	id = Column(Integer, primary_key=True)
	template_number = Column("Template Number", Integer, unique=True)
	flags = Column("Flags", Integer)
	bolus_type = Column("Bolus Type", Integer)
	bolus_fast_amount = Column("Bolus Fast Amount", Integer)
	bolus_extended_amount = Column("Bolus Extended Amount", Integer)
	bolus_duration = Column("Bolus Duration", Integer)
	bolus_delay_time = Column("Bolus Delay Time", Integer)
	bolus_delivery_reason_correction = Column("Bolus Delivery Reason Correction", Integer)
	bolus_delivery_reason_meal = Column("Bolus Delivery Reason Meal", Integer)

	def __str__(self):
		return "<BolusTemplate(template_number='%s', flags='%s', bolus_type='%s', bolus_fast_amount='%s', bolus_extended_amount='%s', bolus_duration='%s', bolus_delay_time='%s', bolus_delivery_reason_correction='%s', bolus_delivery_reason_meal='%s')>" % (
			self.template_number, self.flags, self.bolus_type, self.bolus_fast_amount, self.bolus_extended_amount, self.bolus_duration, self.bolus_delay_time, self.bolus_delivery_reason_correction, self.bolus_delivery_reason_meal)


class ISFTemplate(Base):
	__tablename__ = 'isf_templates'

	id = Column(Integer, primary_key=True)
	flags = Column("Flags", Integer)
	template_number = Column("Template Number", Integer, unique=True)
	first_time_block_number_index = Column("First Time Block Number Index", Integer)
	first_duration = Column("First Duration", Integer)
	first_isf = Column("First ISF", Integer)
	second_duration = Column("Second Duration", Integer, default=0)
	second_isf = Column("Second ISF", Integer, default=0)
	third_duration = Column("Third Duration", Integer, default=0)
	third_isf = Column("Third ISF", Integer, default=0)

	def __str__(self):
		return "<ISFTemplate(flags,='%s', template_number='%s', first_time_block_number_index='%s', first_duration='%s', first_isf='%s', second_duration='%s', second_isf='%s', third_duration='%s', third_isf='%s')>" % (
			self.flags, self.template_number, self.first_time_block_number_index, self.first_duration, self.first_isf, self.second_duration, self.second_isf, self.third_duration, self.third_isf)


class I2CHOTemplate(Base):
	__tablename__ = 'i2cho_templates'

	id = Column(Integer, primary_key=True)
	flags = Column("Flags", Integer)
	template_number = Column("Template Number", Integer, unique=True)
	first_time_block_number_index = Column("First Time Block Number Index", Integer)
	first_duration = Column("First Duration", Integer)
	first_ratio = Column("First Ratio", Integer)
	second_duration = Column("Second Duration", Integer, default=0)
	second_ratio = Column("Second Ratio", Integer, default=0)
	third_duration = Column("Third Duration", Integer, default=0)
	third_ratio = Column("Third Ratio", Integer, default=0)
	
	def __str__(self):
		return "<I2CHOTemplate(flags,='%s',template_number='%s', first_time_block_number_index='%s', first_duration='%s', first_ratio='%s', second_duration='%s', second_ratio='%s', third_duration='%s', third_ratio='%s')>" % (
			self.flags, self.template_number, self.first_time_block_number_index, self.first_duration, self.first_ratio, self.second_duration, self.second_ratio, self.third_duration, self.third_ratio)


class TargetGlucoseTemplate(Base):
	__tablename__ = 'target_glucose_templates'

	id = Column(Integer, primary_key=True)
	flags = Column("Flags", Integer)
	template_number = Column("Template Number", Integer, unique=True)
	first_time_block_number_index = Column("First Time Block Number Index", Integer)
	first_duration = Column("First Duration", Integer)
	first_lower_target_glucose_limit = Column("First Lower Target Glucose Limit", Integer)
	first_upper_target_glucose_limit = Column("First Upper Target Glucose Limit", Integer)
	second_duration = Column("Second Duration", Integer, default=0)
	second_lower_target_glucose_limit = Column("Second Lower Target Glucose Limit", Integer, default=0)
	second_upper_target_glucose_limit = Column("Second Upper Target Glucose Limit", Integer, default=0)
	
	def __str__(self):
		return "<TargetGlucoseTemplate(flags,='%s',template_number='%s', first_time_block_number_index='%s', first_duration='%s', first_lower_target_glucose_limit='%s', first_upper_target_glucose_limit='%s', second_duration='%s', second_lower_target_glucose_limit='%s', second_upper_target_glucose_limit='%s')>" % (
			self.flags, self.template_number, self.first_time_block_number_index, self.first_duration, self.first_lower_target_glucose_limit, self.first_upper_target_glucose_limit, self.second_duration, self.second_lower_target_glucose_limit, self.second_upper_target_glucose_limit)

#populate the template lookup table
def template_init():
	logger.info('template_init')
	if (get_setting('features', 'FEATURES', 'ids_features_basal_rate_supported') == '1'):
		for x in range(TemplateRange.basal_rate_profile_template_range[0], TemplateRange.basal_rate_profile_template_range[-1]):
			result = add_entry(TemplateLookup(template_number = x,
											  template_type = 0x33,
											  active = 0,
											  configurable = 1,
											  configured = 0))

	if (get_setting('features', 'FEATURES', 'ids_features_tbr_template_supported') == '1'):
		for x in range(TemplateRange.tbr_template_range[0], TemplateRange.tbr_template_range[-1]):
			result = add_entry(TemplateLookup(template_number = x,
											  template_type = 0x3C,
											  active = 0,
											  configurable = 1,
											  configured = 0))
	
	if (get_setting('features', 'FEATURES', 'ids_features_bolus_template_supported') == '1'):
		for x in range(TemplateRange.bolus_template_range[0], TemplateRange.bolus_template_range[-1]):
			result = add_entry(TemplateLookup(template_number = x,
											  template_type = 0x55,
											  active = 0,
											  configurable = 1,
											  configured = 0))

	if (get_setting('features', 'FEATURES', 'ids_features_isf_profile_template_supported') == '1'):
		for x in range(TemplateRange.isf_template_range[0], TemplateRange.isf_template_range[-1]):
			result = add_entry(TemplateLookup(template_number = x,
											  template_type = 0x5A,
											  active = 0,
											  configurable = 1,
											  configured = 0))

	if (get_setting('features', 'FEATURES', 'ids_features_i2cho_ratio_profile_template_supported') == '1'):
		for x in range(TemplateRange.i2cho_template_range[0], TemplateRange.i2cho_template_range[-1]):
			result = add_entry(TemplateLookup(template_number = x,
											  template_type = 0x66,
											  active = 0,
											  configurable = 1,
											  configured = 0))

	if (get_setting('features', 'FEATURES', 'ids_features_target_glucose_range_profile_template_supported') == '1'):
		for x in range(TemplateRange.target_glucose_range_template_range[0], TemplateRange.target_glucose_range_template_range[-1]):
			result = add_entry(TemplateLookup(template_number = x,
											  template_type = 0x96,
											  active = 0,
											  configurable = 1,
											  configured = 0))


#If a template is written by the Collector, then its status is set to Configured by the Insulin Delivery Sensor
def write_basal_rate_profile_template(flags, template_number, first_time_block_number_index, first_duration, first_rate, second_duration, second_rate, third_duration, third_rate):
	logger.info('write_basal_rate_profile_template')
	
	template = get_row_for_object(TemplateLookup, TemplateLookup.template_number, template_number)
	if not template.configurable:
		logger.info('template not configurable')
		return False

	profile_exists = get_last_row_for_object(BasalRateProfileTemplate, BasalRateProfileTemplate.template_number, template_number)
	if profile_exists is not None:
		delete_row(BasalRateProfileTemplate, BasalRateProfileTemplate.template_number, template_number)

	result = add_entry(BasalRateProfileTemplate(flags = flags,
									   			template_number = template_number,
									   			first_time_block_number_index = first_time_block_number_index,
									   			first_duration = first_duration,
									   			first_rate = first_rate,
									   			second_duration = second_duration,
									   			second_rate = second_rate,
									   			third_duration = third_duration,
									   			third_rate = third_rate))

	logger.info(result)
	
	if result is True:
		update_arbitrary_row(TemplateLookup, 'template_number', template_number, 'configured', 1)
	
	return result

def get_basal_rate_profile_template(template_number):
	logger.info('get_basal_rate_profile_template')
	template =  get_row_for_object(BasalRateProfileTemplate, BasalRateProfileTemplate.template_number, template_number)
	return template

def write_tbr_template(template_number, tbr_type, tbr_adjustment_value, tbr_duration):
	logger.info('write_tbr_template')
	
	template = get_row_for_object(TemplateLookup, TemplateLookup.template_number, template_number)
	if not template.configurable:
		logger.info('template not configurable')
		return False

	profile_exists = get_last_row_for_object(TBRTemplate, TBRTemplate.template_number, template_number)
	if profile_exists is not None:
		delete_row(TBRTemplate, TBRTemplate.template_number, template_number)

	result = add_entry(TBRTemplate(template_number = template_number,
						  		   tbr_type = tbr_type,
						  		   tbr_adjustment_value = tbr_adjustment_value,
					      		   tbr_duration = tbr_duration))
	
	logger.info(result)

	if result is True:
		update_arbitrary_row(TemplateLookup, 'template_number', template_number, 'configured', 1)
	
	return result

def get_tbr_template(template_number):
	logger.info('get_tbr_template')
	template =  get_row_for_object(TBRTemplate, TBRTemplate.template_number, template_number)
	return template

def write_bolus_template(template_number, flags, bolus_type, bolus_fast_amount, bolus_extended_amount, bolus_duration, bolus_delay_time, bolus_delivery_reason_correction, bolus_delivery_reason_meal):
	logger.info('write_bolus_template')
	
	template = get_row_for_object(TemplateLookup, TemplateLookup.template_number, template_number)
	if not template.configurable:
		logger.info('template not configurable')
		return False

	profile_exists = get_last_row_for_object(BolusTemplate, BolusTemplate.template_number, template_number)
	if profile_exists is not None:
		delete_row(BolusTemplate, BolusTemplate.template_number, template_number)

	result = add_entry(BolusTemplate(template_number = template_number,
						    		flags = flags,
						    		bolus_type = bolus_type,
									bolus_fast_amount = bolus_fast_amount,
									bolus_extended_amount = bolus_extended_amount,
									bolus_duration = bolus_duration,
									bolus_delay_time = bolus_delay_time,
									bolus_delivery_reason_correction = bolus_delivery_reason_correction,
									bolus_delivery_reason_meal = bolus_delivery_reason_meal))
	
	logger.info(result)

	if result is True:
		update_arbitrary_row(TemplateLookup, 'template_number', template_number, 'configured', 1)
	
	return result

def get_bolus_template(template_number):
	logger.info('get_bolus_template')
	template =  get_row_for_object(BolusTemplate, BolusTemplate.template_number, template_number)
	return template

def write_isf_template(flags, template_number, first_time_block_number_index, first_duration, first_isf, second_duration, second_isf, third_duration, third_isf):
	logger.info('write_isf_template')
	
	template = get_row_for_object(TemplateLookup, TemplateLookup.template_number, template_number)
	if not template.configurable:
		logger.info('template not configurable')
		return False

	profile_exists = get_last_row_for_object(ISFTemplate, ISFTemplate.template_number, template_number)
	if profile_exists is not None:
		delete_row(ISFTemplate, ISFTemplate.template_number, template_number)

	result = add_entry(ISFTemplate(flags = flags, 
						  		template_number = template_number,
						  		first_time_block_number_index = first_time_block_number_index,
						  		first_duration = first_duration,
						  		first_isf = first_isf,
					      		second_duration = second_duration,
						  		second_isf = second_isf,
						  		third_duration = third_duration,
						  		third_isf = third_isf))
	
	logger.info(result)

	if result is True:
		update_arbitrary_row(TemplateLookup, 'template_number', template_number, 'configured', 1)
	
	return result

def get_isf_template(template_number):
	logger.info('get_isf_template')
	template =  get_row_for_object(ISFTemplate, ISFTemplate.template_number, template_number)
	return template

def write_i2cho_template(flags, template_number, first_time_block_number_index, first_duration, first_ratio, second_duration, second_ratio, third_duration, third_ratio):
	logger.info('write_i2cho_template')
	
	template = get_row_for_object(TemplateLookup, TemplateLookup.template_number, template_number)
	if not template.configurable:
		logger.info('template not configurable')
		return False

	profile_exists = get_last_row_for_object(I2CHOTemplate, I2CHOTemplate.template_number, template_number)
	if profile_exists is not None:
		delete_row(I2CHOTemplate, I2CHOTemplate.template_number, template_number)

	result = add_entry(I2CHOTemplate(flags = flags,
									template_number = template_number,
									first_time_block_number_index = first_time_block_number_index,
									first_duration = first_duration,
									first_ratio = first_ratio,
									second_duration = second_duration,
									second_ratio = second_ratio,
									third_duration = third_duration,
									third_ratio = third_ratio))
	
	logger.info(result)

	if result is True:
		update_arbitrary_row(TemplateLookup, 'template_number', template_number, 'configured', 1)
	
	return result

def get_i2cho_template(template_number):
	logger.info('get_i2cho_template')
	template =  get_row_for_object(I2CHOTemplate, I2CHOTemplate.template_number, template_number)
	return template

def write_target_glucose_template(flags, template_number, first_time_block_number_index, first_duration, first_lower_target_glucose_limit, first_upper_target_glucose_limit, second_duration, second_lower_target_glucose_limit, second_upper_target_glucose_limit):
	logger.info('write_target_glucose_template')
	
	template = get_row_for_object(TemplateLookup, TemplateLookup.template_number, template_number)
	if not template.configurable:
		logger.info('template not configurable')
		return False

	profile_exists = get_last_row_for_object(TargetGlucoseTemplate, TargetGlucoseTemplate.template_number, template_number)
	if profile_exists is not None:
		delete_row(TargetGlucoseTemplate, TargetGlucoseTemplate.template_number, template_number)

	result = add_entry(TargetGlucoseTemplate(flags = flags,
											template_number = template_number,
											first_time_block_number_index = first_time_block_number_index,
											first_duration = first_duration,
											first_lower_target_glucose_limit = first_lower_target_glucose_limit,
											first_upper_target_glucose_limit = first_upper_target_glucose_limit,
											second_duration = second_duration,
											second_lower_target_glucose_limit = second_lower_target_glucose_limit,
											second_upper_target_glucose_limit = second_upper_target_glucose_limit))
	
	logger.info(result)

	if result is True:
		update_arbitrary_row(TemplateLookup, 'template_number', template_number, 'configured', 1)
	
	return result

def get_target_glucose_template(template_number):
	logger.info('get_target_glucose_template')
	template =  get_row_for_object(TargetGlucoseTemplate, TargetGlucoseTemplate.template_number, template_number)
	return template

def reset_template_status(template_number):
	logger.info('reset_template_status')
	result = update_arbitrary_row(TemplateLookup, 'template_number', str(template_number), 'active', 0)
	logger.info(result)
	return result

def activate_template(template_number):
	logger.info('activate_template')
	result = update_arbitrary_row(TemplateLookup, 'template_number', str(template_number), 'active', 1)
	logger.info(result)
	return result

def get_template(template_number):
	logger.info('get_template')
	template = get_row_for_object(TemplateLookup, TemplateLookup.template_number, template_number)
	logger.info(template)
	return template

def get_template_details(template_number):
	row = get_row_for_object(TemplateLookup, TemplateLookup.template_number, template_number)
	if row is not None:
		table = get_table_by_name(row.table_name)
		template = get_row_for_object(table, table.template_number, row.template_number)
		if template is not None:
			return template
		else:
			return None
	else:
		return None
