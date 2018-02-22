import logging
from db import *

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

def write_status(status):
	logger.info('write_status')
	result = add_entry(status)
	print(repr(result))
	return result

def get_current_status():
	logger.info('get_current_status')
	status =  get_last_row(Status)
	return status
