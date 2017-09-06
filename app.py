#!/usr/bin/env python3
#http://blog.mrgibbs.io/bluez-5-39-ble-setup-on-the-raspberry-pi/

import dbus
import dbus.mainloop.glib

try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

mainloop = None

from bluetooth import *
from ids import *


class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(DeviceInformationService(bus, 0))
        self.add_service(BatteryService(bus, 1))
        self.add_service(IDSService(bus, 2))
        self.add_service(ImmediateAlertService(bus, 3))
        self.add_service(BondManagementService(bus, 4))

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        #print('GetManagedObjects')

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response

class DeviceAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid('1829')
        self.add_service_uuid('180F')
        #self.add_service_uuid('180D')
        #self.add_manufacturer_data(0xffff, [0x00, 0x01, 0x02, 0x03, 0x04])
        #self.add_service_data('9999', [0x00, 0x01, 0x02, 0x03, 0x04])
        self.include_tx_power = True

class CharacteristicUserDescriptionDescriptor(Descriptor):

    CUD_UUID = '2901'

    def __init__(self, bus, index, characteristic, description):
        self.writable = 'writable-auxiliaries' in characteristic.flags
        #self.value = array.array('B', b'This is a characteristic for testing')
        self.value = array.array('B', description)
        self.value = self.value.tolist()
        Descriptor.__init__(
            self, bus, index,
            self.CUD_UUID,
            ['read', 'write'],
            characteristic)

    def ReadValue(self, options):
        return self.value

    def WriteValue(self, value, options):
        if not self.writable:
            raise NotPermittedException()
        self.value = value

class BondManagementService(Service):
    BOND_MGMT_UUID = '181E'
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.BOND_MGMT_UUID, True)
        self.add_characteristic(BondManagementControlPointChrc(bus, 0, self))
        self.add_characteristic(BondManagementFeatureChrc(bus, 1, self))

class BondManagementControlPointChrc(Characteristic):
    BOND_MGMT_CP_UUID = '2aa4'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.BOND_MGMT_CP_UUID,
            ['write'],
            service)
        self.value = []
        self.notifying = False

    def WriteValue(self, value, options):
        print('BondManagementControlPointChrc write: ' + repr(value))
        self.value = value

class BondManagementFeatureChrc(Characteristic):
    BOND_MGMT_FEATURE_UUID = '2aa5'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.BOND_MGMT_FEATURE_UUID,
            ['write'],
            service)
        self.value = []
        self.notifying = False

    def ReadValue(self, options):
        return [0x00]

class ImmediateAlertService(Service):
    IA_UUID = '1802'
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.IA_UUID, True)
        self.add_characteristic(AlertLevelChrc(bus, 0, self))

class AlertLevelChrc(Characteristic):
    IA_ALERT_LEVEL_UUID = '2a06'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.IA_ALERT_LEVEL_UUID,
            ['write-without-response'],
            service)
        self.value = []
        self.notifying = False

    def WriteValue(self, value, options):
        print('AlertLevelChrc write: ' + repr(value))
        self.value = value

class DeviceInformationService(Service):
    DI_UUID = '180a'
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.DI_UUID, True)
        self.add_characteristic(ManufacturerNameChrc(bus, 0, self))
        self.add_characteristic(ModelNumberChrc(bus, 1, self))
        self.add_characteristic(SerialNumberChrc(bus, 2, self))
        self.add_characteristic(SystemIDChrc(bus, 3, self))
        self.add_characteristic(FirmwareRevisionChrc(bus, 4, self))

class ManufacturerNameChrc(Characteristic):
    DI_MANU_NAME_UUID = '2a29'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.DI_MANU_NAME_UUID,
            ['read'],
            service)
        self.notifying = False

    def ReadValue(self, options):
        return [0x55, 0x48, 0x4e]

class ModelNumberChrc(Characteristic):
    DI_MODEL_NUMBER_UUID = '2a24'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.DI_MODEL_NUMBER_UUID,
            ['read'],
            service)
        self.notifying = False

    def ReadValue(self, options):
        return [0x31, 0x30, 0x30]

class SerialNumberChrc(Characteristic):
    DI_SERIAL_NUMBER_UUID = '2a25'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.DI_SERIAL_NUMBER_UUID,
            ['read'],
            service)
        self.notifying = False

    def ReadValue(self, options):
        return [0x31, 0x32, 0x33, 0x34, 0x35]

class SystemIDChrc(Characteristic):
    DI_SYSTEM_ID_UUID = '2a23'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.DI_SYSTEM_ID_UUID,
            ['read'],
            service)
        self.notifying = False

    def ReadValue(self, options):
        return [0x30, 0x30, 0x30, 0x30, 0x30]

class FirmwareRevisionChrc(Characteristic):
    DI_FIRMWARE_REVISION_UUID = '2a26'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.DI_FIRMWARE_REVISION_UUID,
            ['read'],
            service)
        self.notifying = False

    def ReadValue(self, options):
        return [0x31, 0x2E, 0x30]

class BatteryService(Service):
    BATTERY_UUID = '180f'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.BATTERY_UUID, True)
        self.add_characteristic(BatteryLevelCharacteristic(bus, 0, self))

class BatteryLevelCharacteristic(Characteristic):
    BATTERY_LVL_UUID = '2a19'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.BATTERY_LVL_UUID,
            ['read', 'notify'],
            service)
        self.notifying = False
        self.battery_lvl = 100
        #GObject.timeout_add(5000, self.drain_battery)

    def notify_battery_level(self):
        if not self.notifying:
            return
        self.PropertiesChanged(
            GATT_CHRC_IFACE,
            {'Value': [dbus.Byte(self.battery_lvl)]}, [])

    def drain_battery(self):
        if self.battery_lvl > 0:
            self.battery_lvl -= 2
            if self.battery_lvl < 0:
                self.battery_lvl = 0
        #print('Battery Level drained: ' + repr(self.battery_lvl))
        self.notify_battery_level()
        return True

    def ReadValue(self, options):
        print('Battery Level read: ' + repr(self.battery_lvl))
        return [dbus.Byte(self.battery_lvl)]

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True
        self.notify_battery_level()

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False

class IDSService(Service):
    IDS_UUID = '1829'
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.IDS_UUID, True)
        self.add_characteristic(IDDStatusChangedChrc(bus, 0, self))
        self.add_characteristic(IDDStatusChrc(bus, 1, self))
        self.add_characteristic(IDDAnnunciationStatusChrc(bus, 2, self))
        self.add_characteristic(IDDFeaturesChrc(bus, 3, self))
        self.add_characteristic(IDDStatusReaderControlPointChrc(bus, 4, self))
        self.add_characteristic(IDDCommandControlPointChrc(bus, 5, self))
        self.add_characteristic(IDDCommandDataChrc(bus, 6, self))
        self.add_characteristic(IDDHistoryDataChrc(bus, 7, self))
        self.add_characteristic(RecordAccessControlPointChrc(bus, 8, self))

class IDDStatusChangedChrc(Characteristic):
    IDS_STATUS_CHANGED_UUID = '2adb'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.IDS_STATUS_CHANGED_UUID,
            ['read', 'indicate'],
            service)
        self.notifying = False
        self.add_descriptor(
            CharacteristicUserDescriptionDescriptor(bus, 2, self, 'IDD Status Changed'))

    def ReadValue(self, options):
        return get_ids_status_changed()

class IDDStatusChrc(Characteristic):
    IDS_STATUS_UUID = '2adc'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.IDS_STATUS_UUID,
            ['read', 'indicate'],
            service)
        self.notifying = False
        self.add_descriptor(
            CharacteristicUserDescriptionDescriptor(bus, 2, self, 'IDD Status'))

    def ReadValue(self, options):
        return get_ids_status()

class IDDAnnunciationStatusChrc(Characteristic):
    IDS_ANNUNCIATION_STATUS_UUID = '2add'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.IDS_ANNUNCIATION_STATUS_UUID,
            ['read', 'indicate'],
            service)
        self.notifying = False
        self.add_descriptor(
            CharacteristicUserDescriptionDescriptor(bus, 2, self, 'IDD Annunciation Status'))

    def ReadValue(self, options):
        return [0x00]

class IDDFeaturesChrc(Characteristic):
    IDS_FEATURES_UUID = '2ade'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.IDS_FEATURES_UUID,
            ['read'],
            service)
        self.notifying = False
        self.add_descriptor(
            CharacteristicUserDescriptionDescriptor(bus, 2, self, 'IDD Features'))

    def ReadValue(self, options):
        return get_ids_features()

class IDDStatusReaderControlPointChrc(Characteristic):
    IDS_STATUS_READER_CP_UUID = '2adf'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.IDS_STATUS_READER_CP_UUID,
            ['write', 'indicate'],
            service)
        self.notifying = False
        self.add_descriptor(
            CharacteristicUserDescriptionDescriptor(bus, 2, self, 'IDD Status Reader Control Point'))

    def ReadValue(self, options):
        return [0x00]

class IDDCommandControlPointChrc(Characteristic):
    IDS_COMMAND_CP_UUID = '2b00'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.IDS_COMMAND_CP_UUID,
            ['write', 'indicate'],
            service)
        self.notifying = False
        self.add_descriptor(
            CharacteristicUserDescriptionDescriptor(bus, 2, self, 'IDD Command Control Point'))

    def ReadValue(self, options):
        return [0x00]

class IDDCommandDataChrc(Characteristic):
    IDS_COMMAND_DATA_UUID = '2b01'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.IDS_COMMAND_DATA_UUID,
            ['notify'],
            service)
        self.notifying = False
        self.add_descriptor(
            CharacteristicUserDescriptionDescriptor(bus, 2, self, 'IDD Command Data'))

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return
        self.notifying = True

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return
        self.notifying = False

class IDDHistoryDataChrc(Characteristic):
    IDS_HISTORY_DATA_UUID = '2b02'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.IDS_HISTORY_DATA_UUID,
            ['notify'],
            service)
        self.notifying = False
        self.add_descriptor(
            CharacteristicUserDescriptionDescriptor(bus, 2, self, 'IDD History Data'))

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return
        self.notifying = True

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return
        self.notifying = False

class RecordAccessControlPointChrc(Characteristic):
    RACP_UUID = '2a52'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.RACP_UUID,
            ['write', 'indicate'],
            service)
        self.notifying = False
        self.add_descriptor(
            CharacteristicUserDescriptionDescriptor(bus, 2, self, 'Record Access Control Point'))

def register_ad_cb():
   	"""
    Callback if registering advertisement was successful
    """
	print('Advertisement registered')


def register_ad_error_cb(error):
    """
    Callback if registering advertisement failed
    """
    print('Failed to register advertisement: ' + str(error))
    mainloop.quit()


def register_app_cb():
    """
    Callback if registering GATT application was successful
    """
    print('GATT application registered')


def register_app_error_cb(error):
    """
    Callback if registering GATT application failed.
    """
    print('Failed to register application: ' + str(error))
    mainloop.quit()

def cleanup():
    print('Cleaning up')

    print('Unregistering advertisement')
    ad_manager.UnregisterAdvertisement(device_advertisement.get_path())

    print('Unregistering application')
    service_manager.UnregisterApplication(app.get_path())
    mainloop.quit()

def main():
    global mainloop
    global ad_manager
    global device_advertisement
    global service_manager
    global app

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    # Get ServiceManager and AdvertisingManager
    service_manager = get_service_manager(bus)
    ad_manager = get_ad_manager(bus) #fails

    device_advertisement = DeviceAdvertisement(bus, 0)

    app = Application(bus)

    mainloop = GObject.MainLoop()

    # Register advertisement
    print('Registering advertisement')
    ad_manager.RegisterAdvertisement(device_advertisement.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)

    # Register gatt services
    print('Registering application')
    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)

    ids_init()

    mainloop.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('W: interrupt received')
    finally:
        cleanup()
