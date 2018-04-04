import logging
from db import *
from helper import *
from response import *
from sqlalchemy.util import OrderedDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatusChanged(Base):
	__tablename__ = 'status_changed'

	id = Column(Integer, primary_key=True)
	therapy_control_state_changed = Column("Therapy Control State Changed", Integer)
	operational_state_changed = Column("Operational State Changed", Integer)
	reservoir_status_changed = Column("Reservoir Status Changed", Integer)
	annunciation_status_changed = Column("Annunciation Status Changed", Integer)
	total_daily_insulin_status_changed = Column("Total Daily Insulin Status Changed", Integer)
	active_basal_rate_status_changed = Column("Active Basal Rate Status Changed", Integer)
	active_bolus_status_changed = Column("Active Bolus Status Changed", Integer)
	history_event_recorded = Column("History Event Recorded", Integer)

	def __str__(self):
		return "<StatusChanged(therapy_control_state_changed,='%s', operational_state_changed='%s', reservoir_status_changed='%s', annunciation_status_changed='%s', total_daily_insulin_status_changed='%s', active_basal_rate_status_changed='%s', active_bolus_status_changed='%s', history_event_recorded='%s')>" % (
			self.therapy_control_state_changed, self.operational_state_changed, self.reservoir_status_changed, self.annunciation_status_changed, self.total_daily_insulin_status_changed, self.active_basal_rate_status_changed, self.active_bolus_status_changed, self.history_event_recorded)

	def as_dict(self):
		status_changed_dict = OrderedDict((
		('therapy_control_state_changed', self.therapy_control_state_changed),
		('operational_state_changed', self.operational_state_changed),
		('reservoir_status_changed', self.reservoir_status_changed),
		('annunciation_status_changed', self.annunciation_status_changed),
		('total_daily_insulin_status_changed', self.total_daily_insulin_status_changed),
		('active_basal_rate_status_changed', self.active_basal_rate_status_changed),
		('active_bolus_status_changed', self.active_bolus_status_changed),
		('history_event_recorded', self.history_event_recorded)
		))
		return status_changed_dict

def status_changed_init():
	logger.info('status_changed_init')
	status_changed_object = StatusChanged(therapy_control_state_changed = 0,
									   operational_state_changed = 0,
									   reservoir_status_changed = 0,
									   annunciation_status_changed = 0,
									   total_daily_insulin_status_changed = 0,
									   active_basal_rate_status_changed = 0,
									   active_bolus_status_changed = 0,
									   history_event_recorded = 0)
	result = add_entry(status_changed_object)

def status_changed_reset():
	status_changed_object = StatusChanged(therapy_control_state_changed = 0,
									   operational_state_changed = 0,
									   reservoir_status_changed = 0,
									   annunciation_status_changed = 0,
									   total_daily_insulin_status_changed = 0,
									   active_basal_rate_status_changed = 0,
									   active_bolus_status_changed = 0,
									   history_event_recorded = 0)
	result = add_entry(status_changed_object)

	data = [dbus.Byte(0x00),
			dbus.Byte(0x00)]
	packet = build_response_packet(None, data)
	send_response(IDSServiceCharacteristics.status_changed, packet)

def update_status_changed(status_changed_bits):
	logger.info('update_status_changed')
	
	status_changed_byte = 0
	status_changed = get_current_status_changed()
	status_changed_dict = status_changed.as_dict()
	
	# convert statusChanged object to byte
	for key in status_changed_dict:
		if status_changed_dict[key] == 1:
			status_changed_byte = set_bit(status_changed_byte, int(list(status_changed_dict.keys()).index(key)))

	# set bits as necessary
	for x in range(0, 8):
		if(bit(status_changed_byte, x)) is not bit(status_changed_bits, x):
			status_changed_byte = set_bit(status_changed_byte, x)
			#if bit(status_changed_bits, x) == 0:
			#	status_changed_byte = clear_bit(status_changed_byte, x)
			#else:
			#	status_changed_byte = set_bit(status_changed_byte, x)

			
	data = [dbus.Byte(status_changed_byte & 0xff),
			dbus.Byte(status_changed_byte >> 8)]
	packet = build_response_packet(None, data)
	send_response(IDSServiceCharacteristics.status_changed, packet)

	status_changed.therapy_control_state_changed = bit(status_changed_byte, 0)
	status_changed.operational_state_changed = bit(status_changed_byte, 1)
	status_changed.reservoir_status_changed = bit(status_changed_byte, 2)
	status_changed.annunciation_status_changed = bit(status_changed_byte, 3)
	status_changed.total_daily_insulin_status_changed = bit(status_changed_byte, 4)
	status_changed.active_basal_rate_status_changed = bit(status_changed_byte, 5)
	status_changed.active_bolus_status_changed = bit(status_changed_byte, 6)
	status_changed.history_event_recorded = bit(status_changed_byte, 7)
	result = add_entry(status_changed)

def write_status_changed(status_changed_object):
	logger.info('write_status_changed')
	print(repr(status_changed_object))
	result = add_entry(status_changed_object)
	return result

def get_current_status_changed():
	logger.info('get_current_status_changed')
	status_changed =  get_last_row(StatusChanged)
	return status_changed
