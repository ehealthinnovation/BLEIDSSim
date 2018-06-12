# BLEIDSSim

## Summary

This is an implementation of the Insulin Delivery Service v1.0 specification on a raspberry Pi. It is in beta form, and thus not all functionality is supported. 

All data is stored in a sqlite database with the filename ids.db. This file can be deleted before starting the IDS simulator to provide a clean working state.

Starting the IDS simulator is accomplished by executing the run.sh script. This will restart the bluetooth service, initialize the database, write a reference time history event, and then start advertising.

The IDS simulator works with the CCInsulinDelivery iOS collector application (https://github.com/ehealthinnovation/CCInsulinDelivery). This provides a complete reference implementation. 

## Requirements

* Raspberry pi 3
* Python 3.5
* Bluez 5.4
