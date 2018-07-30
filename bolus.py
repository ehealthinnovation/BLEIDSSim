import logging
import os
from db import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Bolus(Base):
    __tablename__ = 'boluses'

    id = Column(Integer, primary_key=True)
    flags = Column("Flags", Integer, default=0)
    bolus_id = Column("Bolus ID", Integer, default=0)
    bolus_type = Column("Bolus Type", Integer, default=0)
    fast_amount = Column("Fast Amount", Float, default=0)
    extended_amount = Column("Extended Amount", Float, default=0)
    duration = Column("Duration", Integer, default=0)
    delay_time = Column("Delay Time", Integer, default=0)
    template_number = Column("Template Number", Integer, default=0)
    activation_type = Column("Activation Type", Integer, default=0)
    active = Column("Active", Integer, default=0)
    remaining = Column("Remaining", Integer, default=0)
    #programmed = amount
    #delivered = amount-remaining

def store_bolus(bolus_id, bolus_type, fast_amount, extended_amount, duration, delay_time, template_number, activation_type, active):
    logger.info('store_bolus')
    result = add_entry(Bolus(bolus_id = bolus_id,
                             bolus_type = bolus_type,
                             fast_amount = fast_amount,
                             extended_amount = extended_amount,
                             duration = duration,
                             delay_time = delay_time,
                             template_number = template_number,
                             activation_type = activation_type,
                             active = active))
    logger.info(result)
    return result

def get_bolus(bolus_id):
    logger.info('get_bolus')
    logger.info(bolus_id)
    bolus = get_row_for_object(Bolus, Bolus.bolus_id, bolus_id)
    logger.info(bolus)
    return bolus

def activate_bolus(bolus_id):
    logger.info('activate_bolus')
    result = update_arbitrary_row(Bolus, 'bolus_id', bolus_id, 'active', 1)

def deactivate_bolus(bolus_id):
    logger.info('deactivate_bolus')
    result = update_arbitrary_row(Bolus, 'bolus_id', bolus_id, 'active', 0)

def get_next_available_bolus_id():
    logger.info('get_next_available_bolus_id')
    row_count = get_row_count(Bolus)
    return row_count + 1

def get_active_bolus_ids():
    logger.info('get_active_bolus_ids')
    boluses = []
    active_boluses = get_rows(Bolus, Bolus.active, 1)
    return active_boluses

def update_bolus_remaining_amount(bolus_id, remaining_amount):
    logger.info('update_bolus_remaining_amount')
    logger.info(bolus_id)
    logger.info(round(remaining_amount,2))
    result = update_arbitrary_row(Bolus, 'bolus_id', bolus_id, 'remaining', remaining_amount)

