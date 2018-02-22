#https://stackoverflow.com/questions/12435211/python-threading-timer-repeat-function-every-n-seconds

from threading import Timer, Thread, Event
from datetime import datetime
import signal
import time

class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass
 
def service_shutdown(signum, frame):
    print('Caught signal %d' % signum)
    raise ServiceExit

class perpetualTimer():

	def __init__(self, t, hFunction):
		self.t = t
		self.hFunction = hFunction
		self.thread = Timer(self.t, self.handle_function)

	def handle_function(self):
		self.hFunction()
		self.thread = Timer(self.t, self.handle_function)
		self.thread.start()

	def start(self):
		self.thread.start()

	def cancel(self):
		self.thread.cancel()


def printer():
	tempo = datetime.today()
	print("{}:{}:{}".format(tempo.hour, tempo.minute, tempo.second))

def notice():
	print('notice')

def main():
	# Register the signal handlers
	signal.signal(signal.SIGTERM, service_shutdown)
	signal.signal(signal.SIGINT, service_shutdown)
 
	print('Starting main program')
 
	# Start the job threads
	try:
		t = perpetualTimer(1, printer)
		t.start()

		r = perpetualTimer(2, notice)
		r.start()

		# Keep the main thread running, otherwise signals are ignored.
		while True:
			time.sleep(0.5)

	except ServiceExit:
		# Terminate the running threads.
		# Set the shutdown flag on each thread to trigger a clean shutdown of each thread.
		t.cancel()
		r.cancel()
 
	print('Exiting main program')
 
 
if __name__ == '__main__':
	main()


