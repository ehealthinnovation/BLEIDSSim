import logging
from configparser import ConfigParser
import os
import collections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_config(path):
	if not os.path.exists(path):
		create_config(path)
 
	parser = ConfigParser()
	parser.read(path)
	return parser

def get_setting(path, section, setting):
	parser = ConfigParser()
	parser = get_config(path)
	value = parser.get(section, setting)
	#print ("{section} {setting} is {value}").format(
	#	section=section, setting=setting, value=value)
	return value

def update_setting(path, section, setting, value):
	logging.info('update_setting')
	parser = ConfigParser()
	parser = get_config(path)
	parser.set(section, setting, value)
	with open(path, "w") as config_file:
		parser.write(config_file)
	
def get_dict(path, section):
	parser = ConfigParser()
	parser = get_config(path)
	d = collections.OrderedDict(parser.items(section))
	return d
