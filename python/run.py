# import the necessary packages
from blob_detection import detect
from utils import triangulate, navigate, draw_vtm, draw_pts, draw_bot, draw_rts, display_msg, remove_vtm
import numpy as np
import cv2
import time
import requests

from multiprocessing.dummy import Pool

pool = Pool(10) # Creates a pool with ten threads; more threads = more concurrency.
                # "pool" is a module attribute; you can be sure there will only
                # be one of them in your application
                # as modules are cached after initialization.

# api-endpoint 
url = "http://192.168.43.224"

print("Enter the number of victims:")
num_vtms = int(input())

dev_mode = False

print("Starting camera...")

if dev_mode:
	cap = cv2.VideoCapture('capture.mp4')
	frame_rate = 30
else:
	cap = cv2.VideoCapture(1)
	frame_rate = 5

prev = 0

# Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
out = cv2.VideoWriter('output.avi',cv2.VideoWriter_fourcc(*'XVID'), 30.0, (640,480))

ret, frame = cap.read()
mask = cv2.imread('mask.png', 0)
calibrate = cv2.imread('calibrate.png', 0)

# Threshold of green in HSV space 
lower_green = np.array([30, 40, 40]) 
upper_green = np.array([70, 255, 255])

def find_vtms():
	while cap.isOpened():
		ret, frame = cap.read()
		vtms = detect(frame, mask, lower_green, upper_green)

		frame = cv2.bitwise_and(frame, frame, mask=calibrate)

		if len(vtms) < num_vtms:
			display_msg(frame, "{} victims found, {} remaining".format(len(vtms), 
				num_vtms - len(vtms)), (0, 0, 255))
		else:
			display_msg(frame, "{} victims found, {} extra".format(len(vtms), 
				len(vtms) - num_vtms), (0, 0, 255))

		draw_vtm(frame, vtms)

		# Write the frame into the file 'output.mp4'
		out.write(frame)

		cv2.imshow('frame', frame)
		if cv2.waitKey(1) == ord(' '):
			return vtms

vtms = find_vtms()

starting = True
returning = False
restarting = False
ending = False
finished = True

start = [np.array([60, 288]),np.array([345, 289])]
drop = [np.array([355, 278]), np.array([80, 280]), np.array([80, 160])]
restart = [np.array([70, 288]),np.array([345, 288])]
end = [np.array([60, 450])]

seq = 0

pos = np.array([60, 450])
dirn = np.array([0, -10])

marker = []

while cap.isOpened():
	time_elapsed = time.time() - prev
	ret, frame = cap.read()

	if time_elapsed > 1./frame_rate and not finished:
		prev = time.time()

		# Threshold of magenta in HSV space 
		lower_magenta = np.array([150, 40, 40]) 
		upper_magenta = np.array([180, 255, 255]) 

		pts = detect(frame, mask, lower_magenta, upper_magenta)

		if len(pts) >= 3:
			pos, dirn = triangulate(pts)

		if starting:
			marker = start
			rts, angle, dist = navigate(pos, dirn, start[seq:seq+1])
			if dist < 5 or cv2.waitKey(1) == ord(' '):
				seq += 1
				if seq == len(start):
					seq = 0
					dist = 0
					starting = False

		elif restarting:
			marker = restart
			rts, angle, dist = navigate(pos, dirn, restart[seq:seq+1])
			if dist < 5 or cv2.waitKey(1) == ord(' '):
				seq += 1
				if seq == len(restart):
					seq = 0
					dist = 0
					restarting = False

		elif returning:
			marker = drop
			rts, angle, dist = navigate(pos, dirn, drop[seq:seq+1])
			if dist < 5 or cv2.waitKey(1) == ord(' '):
				seq += 1
				if seq == len(drop):
					seq = 0
					dist = 0
					returning = False

					if not dev_mode:
						r = requests.get(url + "/drop")

					if len(vtms) == 0:
						ending = True
					else:
						restarting = True

		elif ending:
			marker = end
			rts, angle, dist = navigate(pos, dirn, end[seq:seq+1])
			if dist < 5 or cv2.waitKey(1) == ord(' '):
				seq += 1
				if seq == len(end):
					seq = 0
					dist = 0
					ending = False

					if not dev_mode:
						r = requests.get(url + "/stop")

					finished = True

		elif len(vtms) != 0:
			marker = []
			rts, angle, dist = navigate(pos, dirn, vtms)
			if dist < 50 or cv2.waitKey(1) == ord(' '):
				dist = 0
				returning = True
				remove_vtm(vtms, rts[0])

				if not dev_mode:
					r = requests.get(url + "/grab")

		# defining a params dict for the parameters to be sent to the API 
		parameters = {
			"angle": angle,
			"distance": dist
		} 
  
		# sending get request and saving the response as response object 
		pool.apply_async(requests.get, [url + "/move", parameters])

	draw_vtm(frame, vtms)

	if not finished:
		draw_pts(frame, marker)
		draw_bot(frame, pos, dirn)
		draw_rts(frame, pos, rts, angle, dist)

		display_msg(frame, "Angle={:.2f}, Distance={}".format(angle, dist), (0, 255, 0))

	# Write the frame into the file 'output.avi'
	out.write(frame)

	cv2.imshow('frame', frame)

	c = cv2.waitKey(1)

	if c == ord('\x1b'):
		break

	elif c == ord('p'):
		finished = not finished

	elif c == ord('r'):
		vtms = find_vtms()

		starting = True
		returning = False
		restarting = False
		ending = False
		finished = True

		seq = 0

		pos = np.array([60, 450])
		dirn = np.array([0, -10])

 
cap.release()
out.release()

cv2.destroyAllWindows()
