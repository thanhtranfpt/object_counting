import cv2
import redis
import time
from multiprocessing import Process
import json
import numpy as np
from utils.redis import serialize_img
from utils.camera_helper import re_read_camera
from config.loader import cfg, CAMERAS, NUM_THREADS, REDIS_HOSTNAME, REDIS_PORT, STREAM_MAXLEN, resized_height, resized_width, LOGGER
from utils.logging_utils import Logger_multiprocessing


#----------------------- Initialize global variables: -----------------------
logger = Logger_multiprocessing(log_file_path=LOGGER['log_file_path'],
                                max_log_size=LOGGER['max_log_size'],
                                max_kept_size=LOGGER['max_kept_size'])
#----------------------- END OF Initialize global variables. -----------------------

# Init Redis
conn = redis.Redis(host=REDIS_HOSTNAME, port=REDIS_PORT)
if not conn.ping():
    raise Exception("Redis unavailable")
logger.info("Connect Redis successfully", topic="camera_service")

def read_camera(camera_info, cfg):
    camera_id = camera_info['id']
    camera_rtsp = camera_info['rtsp']
    cap = cv2.VideoCapture(camera_rtsp)

    logger.info(f'Starting process to read camera id: {camera_id}')

    frame_count = 0

    while True:
        grabbed = cap.grab()
        if not grabbed:
            cap = re_read_camera(cap, camera_id, camera_rtsp)
            continue
        ret, frame = cap.retrieve()
        if not ret:
            cap = re_read_camera(cap, camera_id, camera_rtsp)
            continue
        if frame is None:
            continue

        frame_count += 1

        if frame_count % (cfg["NUM_FRAMES_SKIP"] + 1) != 0:
            continue
        
        frame = cv2.resize(frame, (resized_width, resized_height))

        # Create msg to push to redis:

        frame_to_redis = serialize_img(frame)

        frame_info = {
            "frame_id": str(camera_id) + "_" + str(frame_count),
            "timestamp": time.time()
            }
          
        json_data = {
            "frame_info": frame_info
        }

        msg = {
            "frame": frame_to_redis,
            "json_data": json.dumps(json_data)
        }

        # Push to redis:
        
        conn.xadd(f'camera:{camera_id}', msg, maxlen=STREAM_MAXLEN)


if __name__ == '__main__':
    for index, camera_info in enumerate(CAMERAS):
        p = Process(target=read_camera, args=(camera_info, cfg))
        p.start()