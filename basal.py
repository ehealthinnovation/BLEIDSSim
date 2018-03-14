import logging
import os
from db import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Basal(Base):
    __tablename__ = 'basals'

    id = Column(Integer, primary_key=True)
    flags = Column("Flags", Integer, default=0)
    basal_rate_profile_template_number = Column("Basal Rate Profile Template Number", Integer, default=0)
    first_time_block_number_index = Column("First Time Block Number Index", Integer, default=0)
    first_duration = Column("First Duration", Integer, default=0)
    first_rate = Column("First Rate", Integer, default=0)
    second_duration = Column("Second Duration", Integer, default=0)
    second_rate = Column("Second Rate", Integer, default=0)
    third_duration = Column("Third Duration", Integer, default=0)
    third_rate = Column("Third Rate", Integer, default=0)

def store_basal(basal_rate_profile_template_number, first_time_block_number_index, first_duration, first_rate, second_duration, second_rate, third_duration, third_rate):
    logger.info('store_basal')
    result = add_entry(Basal(basal_rate_profile_template_number = basal_rate_profile_template_number,
                             first_time_block_number_index = first_time_block_number_index,
                             first_duration = first_duration,
                             first_rate = first_rate,
                             second_duration = second_duration,
                             second_rate = second_rate,
                             third_duration = third_duration,
                             third_rate = third_rate))
    logger.info(result)
    return result

def get_basal(basal_rate_profile_template_number):
    logger.info('get_basal')
    logger.info(basal_rate_profile_template_number)
    basal = get_row_for_object(Basal, Basal.basal_rate_profile_template_number, basal_rate_profile_template_number)
    print(repr(basal))
    return basal
