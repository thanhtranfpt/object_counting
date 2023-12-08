import redis
import json
from multiprocessing import Process
import time
from utils.redis import serialize_img
from utils.redis import get_last
from utils.business_helper import update_in_out
from config.loader import cfg, CAMERAS, NUM_THREADS, REDIS_HOSTNAME, REDIS_PORT, STREAM_MAXLEN, LOGGER, LINE_IN, LINE_OUT, ZONE_IN, ZONE_OUT
from utils.logging_utils import Logger_multiprocessing


#----------------------- Initialize global variables: -----------------------
logger = Logger_multiprocessing(log_file_path=LOGGER['log_file_path'],
                                max_log_size=LOGGER['max_log_size'],
                                max_kept_size=LOGGER['max_kept_size'])

global last_ids
last_ids = {}
for index, camera_info in enumerate(CAMERAS):
    camera_id = camera_info['id']
    last_ids[camera_id] = 0

global list_in, list_out, entry_line, exit_line
list_in, list_out = {}, {}
entry_line, exit_line = {}, {}
for camera_info in CAMERAS:
    camera_id = camera_info['id']
    list_in[camera_id] = set()
    list_out[camera_id] = set()
    entry_line[camera_id] = LINE_IN[camera_id]
    exit_line[camera_id] = LINE_OUT[camera_id]
#----------------------- END OF Initialize global variables -----------------------

# Init Redis
conn = redis.Redis(host=REDIS_HOSTNAME, port=REDIS_PORT)
if not conn.ping():
    raise Exception("Redis unavailable")
logger.info("Connect Redis successfully", topic="business_service")

def business(tracking_results, camera_id):
    global list_in, list_out, entry_line, exit_line

    current_people, movement_history = tracking_results["current_people"], tracking_results["movement_history"]
    
    list_in[camera_id], list_out[camera_id] = update_in_out(movement_history=movement_history, current_people=current_people, entry_line=entry_line[camera_id], exit_line=exit_line[camera_id], list_in=list_in[camera_id], list_out=list_out[camera_id])

    business_results = {
        "list_in": list_in[camera_id],
        "list_out": list_out[camera_id],
        "entry_line": entry_line[camera_id],
        "exit_line": exit_line[camera_id],
        "current_people": current_people
    }

    return business_results

def run(camera_info):
    global last_ids

    camera_id = camera_info["id"]
    topic = f'tracking_camera:{camera_id}'

    while True:
        last_ids[camera_id], frame, json_data = get_last(conn, topic, last_id=last_ids[camera_id])
        if frame is None:
            continue

        # json_data = {
        #     "frame_info": frame_info,
        #     "tracking_results": tracking_results
        # }

        frame_info, tracking_results = json_data["frame_info"], json_data["tracking_results"]

        business_results = business(tracking_results, camera_id)

        # Create msg to push to redis:

        json_data = {
            "frame_info": frame_info,
            "business_results": business_results
        }

        msg = {
            "frame": serialize_img(frame),
            "json_data": json.dumps(json_data)
        }

        # Push to redis:

        conn.xadd(f'business_camera:{camera_id}', msg, maxlen=STREAM_MAXLEN)

        
if __name__ == '__main__':
    for index, camera_info in enumerate(CAMERAS):
        p = Process(target=run, args=(camera_info,))
        p.start()