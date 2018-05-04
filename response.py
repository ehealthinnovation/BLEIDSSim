import logging
import dbus
import dbus.mainloop.glib
from bluetooth import *
from service import *
from crc import *
import ids

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def next_crc_counter_value():
	return 0

def build_response_packet(opcode, data):
	logger.info('build_response_packet')
	packet = []

	logger.info("opcode: " + str(opcode))
	logger.info("opcode length: " + str(len(str(opcode))))

	if opcode is not None:
		if len(str(opcode)) == 1:
			packet.append(dbus.Byte(opcode))
		else:
			packet.append(dbus.Byte(opcode & 0xff))
			packet.append(dbus.Byte(opcode >> 8))
	
	logger.info('data: ' + repr(data))
	for byte in data:
		packet.append(byte)

	packet.append(dbus.Byte(next_crc_counter_value()))
	crc = crc_calculate(packet)
	packet.append(dbus.Byte(crc & 0xff))
	packet.append(dbus.Byte(crc >> 8))
	logger.info('packet: ' + repr(packet))
	return packet

def send_response(target, data):
	logger.info('send_response')
	logger.info(ids.app)
	for service in ids.app.services:
			if service.uuid == '1829':
				for characteristic in service.characteristics:
					if characteristic.uuid == target:
						logger.info('found characteristic')
						characteristic.PropertiesChanged(
							GATT_CHRC_IFACE,
							{'Value': data}, [])
