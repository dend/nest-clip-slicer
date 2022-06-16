# Outline of the process:
#
# Step 1: Get available videos: https://nexusapi-us1.camera.home.nest.com/get_available?uuid=CAMERA_ID&end_time=1651804500&_=1655319452488
#     Response will be similar to:
#       [
#         {
#           "connect": 1650150728,
#           "end": 1650151328,
#           "has_video": true,
#           "start": 1650150728
#         },
#         {
#           "connect": 1650154328,
#           "end": 1650154628,
#           "has_video": true,
#           "start": 1650154328
#         }
#       ]
#
# Step 2: Send a request to create a clip: https://webapi.camera.home.nest.com/api/clips.request
#     The contents of the body will contain the start time and end times.
#     Response will be similar to:
#       {
#           "status": 0,
#           "items": [
#               {
#                   "length_in_seconds": 2100.0,
#                   "nest_user_id": "1526894",
#                   "camera_id": CAMERA_ID_SHORT,
#                   "clip_type": "",
#                   "public_link": "https://www.dropcam.com/c/FILE_ID.mp4",
#                   "is_played": false,
#                   "title": "new exp",
#                   "camera_uuid": "CAMERA_ID",
#                   "download_url": "https://clips.dropcam.com/FILE_ID.mp4",
#                   "filename": "FILE_ID.mp4",
#                   "is_user_generated": true,
#                   "generated_time": null,
#                   "nest_structure_id": "structure.ffb5d360-7b02-11ec-b2e5-12524d022643",
#                   "is_error": false,
#                   "embed_url": "https://video.nest.com/embedded/clip/FILE_ID.mp4",
#                   "description": "",
#                   "start_time": 1650508500.0,
#                   "public_url": "https://video.nest.com/clip/FILE_ID.mp4",
#                   "play_count": 0,
#                   "is_public": false,
#                   "notes": "",
#                   "server": "clips.dropcam.com",
#                   "thumbnail_url": "https://clips.dropcam.com/FILE_ID.jpg",
#                   "id": VIDEO_CREATED_ID,
#                   "aspect_ratio": "16x9",
#                   "is_generated": false
#               }
#           ],
#           "status_description": "ok",
#           "status_detail": ""
#       }
#
# Step 3: Check if a video is completed based on its ID: https://webapi.camera.home.nest.com/api/clips.get?id=VIDEO_CREATED_ID
#     This will return a blob that contains status information.
#     From this response you can infer the download URL.
#
# Step 4: Download the video locally.
#
# Step 5: Delete the video from the list of clips: https://webapi.camera.home.nest.com/api/clips.delete
#     The video ID is captured in the body of the request.
#
# Step 6: Proceed to the next video processing request.

import json
import requests
from datetime import datetime
import time

def LoadConfiguration():
	with open('config.json') as file:
		data = json.load(file)
		print (f'Camera ID: {data["camera_id"]}')
		print (f'Timestamp threshold: {data["threshold"]}')
		print (f'Cookie value: {data["cookie"]}')
		return data

def GetAvailableClips(config):
	request_url = f'https://nexusapi-us1.camera.home.nest.com/get_available?uuid={config["camera_id"]}&end_time={config["threshold"]}'
	request_headers = { "Cookie": config["cookie"], "Origin": "https://home.nest.com", "Referer": "https://home.nest.com/"}
	response = requests.get(request_url, headers=request_headers)
	return json.loads(response.content)

def CreateClip(config, start, duration, title):
	request_url = "https://webapi.camera.home.nest.com/api/clips.request"
	request_body = {"uuid": config["uuid"], "title": title, "start_date": start, "is_public": "false", "length": duration, "target_length": "false", "donate_video": "false"}
	request_headers = { "Cookie": config["cookie"], "Origin": "https://home.nest.com", "Referer": "https://home.nest.com/"}
	response = requests.post(request_url, data=request_body, headers=request_headers)
	return json.loads(response.content)

def CheckClip(config, id):
	request_url = f'https://webapi.camera.home.nest.com/api/clips.get?id={id}'
	request_headers = { "Cookie": config["cookie"], "Origin": "https://home.nest.com", "Referer": "https://home.nest.com/"}
	response = requests.get(request_url, headers=request_headers)
	return json.loads(response.content)

def DownloadClip(config, clip_state):
	file_name = f"{clip_state['items'][0]['title']}.mp4"
	request_url = clip_state['items'][0]['download_url']
	request_headers = { "Cookie": config["cookie"], "Origin": "https://home.nest.com", "Referer": "https://home.nest.com/"}
	response = requests.get(request_url, headers=request_headers)

	try:
		with open(file_name, "wb") as video_file:
			print ("Downloading MP4 chunks...")
			video_file.write(response.content)
			return True
	except:
		return False

def DeleteClip(config, clip_state)
	request_url = f'https://webapi.camera.home.nest.com/api/clips.delete'
	request_body = {"id": clip_state["items"][0]["id"]}
	request_headers = { "Cookie": config["cookie"], "Origin": "https://home.nest.com", "Referer": "https://home.nest.com/"}
	response = requests.get(request_url, headers=request_headers)
	return json.loads(response.content)

config = LoadConfiguration()
clips = GetAvailableClips(config)

for clip in clips:
	clip_start = clip["start"]
	clip_end = clip["end"]
	duration = clip_end - clip_start
	clip_data = CreateClip(config, clip_start, duration, datetime.fromtimestamp(int(clip_start)).strftime("%Y%m%d-%H%M%S"))
	if clip_data is not None:
		clip_id = clip_data["items"][0]["id"]
		print(f'Got clip information: {clip_id}')

		clip_state = {}
		is_clip_ready = False
		while is_clip_ready == False:
			print('Checking clip state...')
			clip_state = CheckClip(config, clip_id)
			if clip_state["items"][0]["is_generated"] == True:
				print('Clip is ready')
				is_clip_ready = True
			else:
				print('Clip is not ready. Waiting 10 seconds...')
				time.sleep(10)

		print('Downloading clip...')
		result = DownloadClip(config, clip_state);
		print(f'Clip download attempt for {clip_state["items"][0]["title"]}.mp4 ended with result {result}')
		
		if result == True:
			print('Deleting old clip...')
			delete_result = DeleteClip(config, clip_state);
			if delete_result is not None:
				print(f'Clip deletion ended with result: {delete_result["status_description"]}')

print("Done processing.")

