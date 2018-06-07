import logging
from db import *
from response import *
from shortfloat import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Status(Base):
	__tablename__ = 'status'

	id = Column(Integer, primary_key=True)
	therapy_control_state = Column("Therapy Control State", Integer)
	operational_state = Column("Operational State", Integer)
	reservoir_remaining_amount = Column("Reservoir Remaining Amount", Integer)
	reservoir_attached = Column("Reservoir Attached", Integer)
	
	def __str__(self):
		return "<Status(therapy_control_state,='%s', operational_state='%s', reservoir_remaining_amount='%s', reservoir_attached='%s')>" % (
			self.therapy_control_state, self.operational_state, self.reservoir_remaining_amount, self.reservoir_attached)

def status_init():
	logger.info('status_init')	

def write_status(status):
	logger.info('write_status')
	result = add_entry(status)
	print(repr(result))
	return result

def get_current_status():
	logger.info('get_current_status')
	status =  get_last_row(Status)
	return status

def update_status(status_field, value):
	logger.info('update_status')
	current_status = get_current_status()
	setattr(current_status, status_field, value)
	write_status(current_status)

	reservoir_remaining = float_to_shortfloat(current_status.reservoir_remaining_amount)
	
	data = []	
	data.append(dbus.Byte(current_status.therapy_control_state))
	data.append(dbus.Byte(current_status.operational_state))
	data.append(dbus.Byte(reservoir_remaining & 0xff))
	data.append(dbus.Byte(reservoir_remaining >> 8))
	data.append(dbus.Byte(current_status.reservoir_attached))
	packet = build_response_packet(None, data)
	send_response(IDSServiceCharacteristics.status, packet)
