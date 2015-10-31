import os, json, logging
from sys import argv, exit
from time import sleep, time

from core.vars import BASE_DIR
from core.api import MPServerAPI
from core.utils import get_config, millis_to_time_str
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

		global_timekeeper = {
			'start_time' : 0,
			'last_pause_time' : 0,
			'position_at_last_pause' : 0,
			'master_video_index' : -1
		}

		self.db.set('global_timekeeper', json.dumps(global_timekeeper))
		self.db.set("current_video", self.dad_video)

		return self.play_video(self.dad_video, video_callback=self.video_listener_callback)	

	def video_listener_callback(self, info):
		global_timekeeper = json.loads(self.db.get('global_timekeeper'))
		
		# set the first timekeeper!
		if global_timekeeper['start_time'] == 0 and 'start_time' in info['info'].keys():
			global_timekeeper['start_time'] = info['info']['start_time']
			global_timekeeper['master_video_index'] = info['index']

		# TODO: take account for positioning...
		if 'with_extras' in info['info'].keys() and 'pos' in info['info']['with_extras'].keys():
			print "VID HAS POSITION EXTRAS!"
			global_timekeeper['position_debounce'] = info['info']['with_extras']['pos']
			print global_timekeeper['position_debounce']
			# x seconds FROM where i started!

		# of if paused...
		if 'position_at_last_pause' in info['info'].keys():
			old_position = global_timekeeper['position_at_last_pause']
			new_position = (old_position + abs(info['info']['last_pause_time'] - global_timekeeper['start_time']))

			global_timekeeper['position_at_last_pause'] = new_position
			global_timekeeper['last_pause_time'] = info['info']['last_pause_time']

		# and finally stopped...
		if 'stopped' in info['info'].keys():
			# start video in next position at pause time from current video
			self.play_video(video=self.db.get('current_video'), \
				with_extras={'pos' : millis_to_time_str(global_timekeeper['position_at_last_pause'] * 1000)}, \
				video_callback=self.video_listener_callback)

		self.db.set('global_timekeeper', json.dumps(global_timekeeper))

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
			global_timekeeper = json.loads(self.db.get('global_timekeeper'))

			# get video in current position
			current_video = self.db.get("current_video")
			next_video = self.kid_video if current_video == self.dad_video else self.dad_video
			
			# pause it
			self.pause_video(video=current_video, video_callback=self.video_listener_callback)

			# stop it
			self.stop_video(video=current_video, video_callback=self.video_listener_callback)
			
			# update db
			self.db.set('current_video', next_video)

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
		self.db.delete("global_timekeeper")

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