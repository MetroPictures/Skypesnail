import tornado.web, os, json, re, logging
from sys import argv, exit
from time import sleep

from core.vars import BASE_DIR
from core.api import MPServerAPI
from core.utils import get_config
from core.video_pad import MPVideoPad

BIG_POSITION, LITTLE_POSITION = get_config('video_placements')

DEFAULT_POSITIONS = {
	'dad_video' : BIG_POSITION,
	'kid_video' : LITTLE_POSITION
}

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

		self.dad_video = ""
		self.kid_video = ""

		MPVideoPad.__init__(self)
		logging.basicConfig(filename=self.conf['d_files']['module']['log'], level=logging.DEBUG)

	def start_skypesnail(self):
		logging.debug("Starting the whole thing")

		return self.play_video(self.dad_video, \
			with_extras={'pos' : DEFAULT_POSITIONS['dad_video'], 'vol' : 0}, \
			video_callback=self.video_listener_callback) and \
		self.play_video(self.kid_video, \
			with_extras={'pos' : DEFAULT_POSITIONS['kid_video']}, \
			video_callback=self.video_listener_callback)		

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
			for video in [self.dad_video, self.kid_video]:
				video_mapping = self.get_video_mapping_by_filename(video)
				current_placement = self.get_video_placement(video_mapping.index)

				if current_placement is None:
					DEFAULT_POSITIONS['dad_video' if video == self.dad_video else 'kid_video']
				
				if not self.move_video(video, \
					BIG_POSITION if current_placement == LITTLE_POSITION else LITTLE_POSITION, \
					with_extras={'vol' : 0} if video == self.dad_video else None, \
					video_callback=self.video_listener_callback):
					return False

			return True

		except Exception as e:
			logging.error("COULD NOT MOVE VIDEOS!")
			print e, type(e)

		return False

	def get_video_placement(self, index):
		try:
			return self.get_video_info(index)['current_placement']
		except Exception as e:
			logging.error("COULD NOT GET ANY PLACEMENT FOR VIDEO %s" % video)
			print e, type(e)
		
		return None

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