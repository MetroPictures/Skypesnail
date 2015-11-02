import os, json, logging, requests
from sys import argv, exit
from time import sleep, time

from core.vars import BASE_DIR
from core.api import MPServerAPI
from core.utils import get_config, micros_to_time_str
from core.video_pad import MPVideoPad

# time in micros

DAD_VID = 0
KID_VID = 1
VID_DIFFERENTIAL = 497831000/2

class Skypesnail(MPServerAPI, MPVideoPad):
	def __init__(self):
		MPServerAPI.__init__(self)
		self.conf['d_files'].update({
			'vid' : {
				'log' : os.path.join(BASE_DIR, ".monitor", "%s.log.txt" % self.conf['rpi_id'])
			},
			'video_listener_callback' : {
				'log' : os.path.join(BASE_DIR, ".monitor", "%s.log.txt" % self.conf['rpi_id']),
				'pid' : os.path.join(BASE_DIR, ".monitor", "video_listener_callback.pid.txt")
			}
		})

		MPVideoPad.__init__(self)
		logging.basicConfig(filename=self.conf['d_files']['module']['log'], level=logging.DEBUG)

	def start_skypesnail(self):
		logging.debug("Starting the whole thing")

		return self.play_video("SKYPESNAIL_MERGED.mp4", \
			with_extras={'loop' : ""}, \
			video_callback=self.video_listener_callback)	

	def video_listener_callback(self, info):
		print info

		try:
			video_info = self.get_video_info(info['index'])
			video_info.update(info['info'])
		except Exception as e:
			video_info = info['info']

		self.db.set("video_%d" % info['index'], json.dumps(video_info))		

	def press(self, key):
		logging.debug("press overridden.")
		return self.toggle_placement()

	def toggle_placement(self):
		try:
			# get current position
			current_position = self.get_video_position()
			if current_position is None:
				self.signal_restart()

			# get video in current position
			current_video = DAD_VID if current_position <= VID_DIFFERENTIAL else KID_VID
			
			# set new position
			new_position = (current_position + VID_DIFFERENTIAL) if current_video == DAD_VID \
				else (current_position - VID_DIFFERENTIAL)

			if new_position is None:
				self.signal_restart()

			logging.debug("Current Position: %d" % current_position)
			logging.debug("New Position: %d" % new_position)
			self.set_video_position(new_position, video_callback=self.video_listener_callback)

			return True

		except Exception as e:
			logging.error("COULD NOT MOVE VIDEOS!")
			print e, type(e)

		return False

	def stop(self):
		if not super(Skypesnail, self).stop():
			return False

		return self.stop_video_pad()

	def start(self):
		if not super(Skypesnail, self).start():
			return False

		# auto-start!
		sleep(3)
		try:
			r = requests.get("http://localhost:%d/pick_up" % self.conf['api_port'])
			return json.loads(r.content)['ok']
		except Exception as e:
			logging.error("Could not start?")
			print e, type(e)

		return False

	def on_hang_up(self):
		self.stop_video_pad()
		return super(Skypesnail, self).on_hang_up()

	def run_script(self):
		super(Skypesnail, self).run_script()
		self.start_skypesnail()

if __name__ == "__main__":
	res = False
	ss = Skypesnail()

	if argv[1] in ['--stop', '--restart']:
		res = ss.stop()
		sleep(5)

	if argv[1] in ['--start', '--restart']:
		res = ss.start()

	exit(0 if res else -1)

