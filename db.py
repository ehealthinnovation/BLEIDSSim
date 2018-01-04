import logging
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exc

Base = declarative_base()
Session = sessionmaker()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def db_init():
	global session
	logger.info('db_init')
	engine = create_engine('sqlite:///ids.db')
	Session.configure(bind=engine)
	Base.metadata.create_all(engine)
	session = Session()

def add_entry(Object):
	logger.info('db: add_entry')
	session.add(Object)
	try:
		session.commit()
	except exc.SQLAlchemyError:
		logger.info('commit failed')

def get_row_count(Object):
	logger.info('get_row_count')
	rows = session.query(Object).count()
	return rows

def get_first_row(Object):
	logger.info('get_first_row')
	row = session.query(Object).order_by('id').first()
	return row

def get_last_row(Object):
	logger.info('get_last_row')
	row = session.query(Object).order_by(desc('id')).first()
	return row

def get_events(Object, field, value):
	logger.info('get_events')
	rows = session.query(Object).filter(field == value).all()
	return rows

def get_first_event(Object, field, value):
	logger.info('get_events')
	row = session.query(Object).filter(field == value).order_by('id').first()
	return row

def get_last_event(Object, field, value):
	logger.info('get_events')
	row = session.query(Object).filter(field == value).order_by(desc('id')).first()
	return row
