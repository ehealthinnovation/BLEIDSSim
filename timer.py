#https://stackoverflow.com/questions/12435211/python-threading-timer-repeat-function-every-n-seconds

import logging
from threading import Timer, Thread, Event
from datetime import datetime
import signal
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class perpetualTimer():
	def __init__(self, t, hFunction, argument, callback):
		self.t = t
		self.hFunction = hFunction
		self.callback = callback
		self.thread = Timer(self.t, self.handle_function)
		self.argument = argument

	def handle_function(self):
		logger.info('handle_function')
		keep_going = self.hFunction(self.argument)
		if keep_going:
			self.thread = Timer(self.t, self.handle_function)
			self.thread.start()
		else:
			self.callback()

	def start(self):
		self.thread.start()

	def cancel(self):
		self.thread.cancel()
