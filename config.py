import configparser
import os
import collections

def get_config(path):
	if not os.path.exists(path):
		create_config(path)
 
	config = configparser.ConfigParser()
	config.read(path)
	return config

def get_setting(path, section, setting):
	config = get_config(path)
	value = config.get(section, setting)
	print ("{section} {setting} is {value}").format(
		section=section, setting=setting, value=value)
	return value

def update_setting(path, section, setting, value):
	config = get_config(path)
	config.set(section, setting, value)
	with open(path, "wb") as config_file:
		config.write(config_file)

def get_dict(path, section):
	config = get_config(path)
	d = collections.OrderedDict(config.items(section))
	return d
