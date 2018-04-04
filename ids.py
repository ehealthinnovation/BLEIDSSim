import queue
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

q = None
app = None

def init():
	logger.info('ids init')
	global q
	q = queue.Queue()
	global app
	app = None