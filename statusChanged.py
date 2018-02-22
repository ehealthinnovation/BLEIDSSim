import logging
from db import *
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

def write_status_changed(status_changed_object):
	logger.info('write_status_changed')
	print(repr(status_changed_object))
	result = add_entry(status_changed_object)
	return result

def get_current_status_changed():
	logger.info('get_current_status_changed')
	status_changed =  get_last_row(StatusChanged)
	return status_changed