import tornado.web, os, json, re, logging
from sys import argv, exit
from time import sleep

from core.vars import BASE_DIR
from core.api import MPServerAPI
from core.utils import get_config
from core.video_pad import MPVideoPad

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

		self.dad_video = "SKYPESNAIL_1.mp4"
		self.kid_video = "SKYPESNAIL_2.mp4"

		MPVideoPad.__init__(self)
		logging.basicConfig(filename=self.conf['d_files']['module']['log'], level=logging.DEBUG)

	def start_skypesnail(self):
		logging.debug("Starting the whole thing")

		return self.play_video(self.dad_video, video_callback=self.video_listener_callback)	

	def video_listener_callback(self, info):
		try:
			video_info = self.get_video_info(info['index'])
			video_info.update(info['info'])
		except Exception as e:
			video_info = info['info']

		self.db.set("video_%d" % info['index'], json.dumps(video_info))		
		logging.info("VIDEO INFO UPDATED: %s" % self.db.get("video_%d" % info['index']))

	def press(self, key):
		logging.debug("press overridden.")
		return self.toggle_placement()

	def toggle_placement(self):
		try:
			# get video in position 0
			# pause it
			# stop it
			# start video in position 1 at pause time from video 0

			# update db

			return True

		except Exception as e:
			logging.error("COULD NOT MOVE VIDEOS!")
			print e, type(e)

		return False

	def stop(self):
		if not super(Skypesnail, self).stop():
			return False

		return self.stop_video_pad()

	def reset_for_call(self):
		for video_mapping in self.video_mappings:
			self.db.delete("video_%s" % video_mapping.index)

		super(Skypesnail, self).reset_for_call()

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