from flask import Flask, render_template, Response, redirect, request, jsonify
from flask_cors import CORS
import os
import yaml
import ast
import json
from config_helper import *


app = Flask(__name__, template_folder='./templates')
CORS(app)


#----------------------- Initialize global variables: -----------------------
micro_services = ["camera_service",
                  "tracking_service",
                  "business_service",
                  "visualization_service"]
#----------------------- END OF Initialize global variables. -----------------------


@app.route('/')
def index():
    return redirect('/config')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route('/config')
def config():
    return render_template("config.html")

@app.route('/demo')
def view_demo():
    with open("visualization_service/config/config.yaml", "r") as file:
        data = yaml.safe_load(file)
    FLASK_HOSTNAME_visualization = data["FLASK_HOSTNAME"]
    FLASK_PORT_visualization = data["FLASK_PORT"]
    return redirect(f"http://{FLASK_HOSTNAME_visualization}:{FLASK_PORT_visualization}/")

# --------------------------- START OF add camera: ---------------------------
@app.route('/add-camera', methods = ['GET', 'POST'])
def add_camera():
    if request.method == 'GET':
        return render_template("add_camera.html")
    
    data = request.get_json()
    camera_id = data['camera_id']
    camera_rtsp = data['camera_rtsp']
    
    response = add_camera_helper(camera_id=camera_id, camera_rtsp=camera_rtsp, micro_services=micro_services)

    return jsonify(response)

# --------------------------- END OF add camera. ---------------------------

# --------------------------- START OF config camera: ---------------------------
@app.route('/config-camera', methods = ['GET', 'POST'])
def config_camera():
    if request.method == 'GET':
        return render_template("config_camera.html")
    
    data = request.get_json()
    CAMERA_FPS = data["CAMERA_FPS"]
    NUM_FRAMES_SKIP = data["NUM_FRAMES_SKIP"]
    resized_height = data["resized_height"]
    resized_width = data["resized_width"]

    response = config_camera_helper(CAMERA_FPS=CAMERA_FPS, NUM_FRAMES_SKIP=NUM_FRAMES_SKIP, resized_height=resized_height, resized_width=resized_width)

    return jsonify(response)

# --------------------------- END OF config camera. ---------------------------

# --------------------------- START OF config tracking: ---------------------------
@app.route('/config-tracking', methods = ['GET', 'POST'])
def config_tracking():
    if request.method == 'GET':
        return render_template("config_tracking.html")
    
    data = request.get_json()
    YOLO_MODEL_PATH = data["YOLO_MODEL_PATH"]

    response = config_tracking_helper(YOLO_MODEL_PATH=YOLO_MODEL_PATH)

    return jsonify(response)

# --------------------------- END OF config tracking. ---------------------------

# --------------------------- START OF config business: ---------------------------
@app.route('/config-business', methods = ['GET'])
def config_business():
    line_in, line_out = config_business_helper()
    
    return f"You choose LINE_IN: {str(line_in)} - and LINE_OUT: {str(line_out)}"

# --------------------------- END OF config business. ---------------------------

# --------------------------- START OF config visualization: ---------------------------
@app.route('/config-visualization', methods = ['GET', 'POST'])
def config_visualization():
    if request.method == 'GET':
        return render_template("config_visualization.html")
    
    # Code that may raise an exception:
    data = request.get_json()

    response = config_visualization_helper(data=data)

    return jsonify(response)

# --------------------------- END OF config visualization. ---------------------------

# --------------------------- START OF config env: ---------------------------
@app.route('/config-env', methods = ['GET', 'POST'])
def config_env():
    if request.method == 'GET':
        envs_list = get_envs()
        return render_template("config_env.html", envs_list = envs_list)
    
    data = request.get_json()

    response = config_env_helper(data=data, micro_services=micro_services)

    return jsonify(response)

# --------------------------- END OF config env. ---------------------------

# --------------------------- START OF config logger: ---------------------------
@app.route('/config-logger', methods = ['GET', 'POST'])
def config_logger():
    if request.method == 'GET':
        return render_template("config_logger.html")
    
    # Code that may raise an exception:
    data = request.get_json()

    response = config_logger_helper(data=data, micro_services=micro_services)

    return jsonify(response)

# --------------------------- END OF config logger. ---------------------------

# --------------------------- START OF config redis: ---------------------------
@app.route('/config-redis', methods = ['GET', 'POST'])
def config_redis():
    if request.method == 'GET':
        return render_template("config_redis.html")
    
    # Code that may raise an exception:
    data = request.get_json()

    response = config_redis_helper(data=data, micro_services=micro_services)

    return jsonify(response)

# --------------------------- END OF config redis. ---------------------------


if __name__ == '__main__':
    app.run(host = "0.0.0.0", port = 5000, debug = True)