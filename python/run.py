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

# User input for the number of victims to be rescued
print("Enter the number of victims:")
num_vtms = int(input())

# If the program is running in dev environment
dev_mode = True

print("Starting camera...")

# Specify the video input and frame rate
if dev_mode:
	cap = cv2.VideoCapture('capture.avi')
	frame_rate = 30
else:
	cap = cv2.VideoCapture(1)
	frame_rate = 5

# Variable to store the previous time of analysed frame
prev = 0

# Define the codec and create VideoWriter object.The output is stored in 'output.avi' file.
out = cv2.VideoWriter('output.avi',cv2.VideoWriter_fourcc(*'XVID'), 30.0, (640,480))

# Load the mask for calibration and removing unwanted area from frames
mask = cv2.imread('images/mask.png', 0)
calibrate = cv2.imread('images/calibrate.png', 0)

# Threshold of green in HSV space 
lower_green = np.array([40, 40, 40]) 
upper_green = np.array([60, 255, 255])

# Find the victims and return their locations
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

		# Write the frame into the file 'output.avi'
		out.write(frame)

		cv2.imshow('frame', frame)

		# Return when the space key is pressed
		if cv2.waitKey(1) == ord(' '):
			return vtms

vtms = find_vtms()

# Define variables for sequential control
starting = True
returning = False
restarting = False
ending = False
finished = True

# Sequence of markers for robot movement
start = [np.array([60, 288]),np.array([345, 289])]
drop = [np.array([355, 278]), np.array([80, 282]), np.array([80, 160])]
restart = [np.array([70, 290]),np.array([345, 288])]
end = [np.array([60, 450])]

seq = 0

# Variables to store the location and orientation of robot
pos = np.array([60, 450])
dirn = np.array([0, -10])

marker = []

# Main loop
while cap.isOpened():
	time_elapsed = time.time() - prev
	ret, frame = cap.read()

	if time_elapsed > 1./frame_rate and not finished:
		prev = time.time()

		# Threshold of magenta in HSV space 
		lower_magenta = np.array([150, 20, 180]) 
		upper_magenta = np.array([180, 255, 255]) 

		pts = detect(frame, mask, lower_magenta, upper_magenta)

		# Determine whether the robot is found
		if len(pts) >= 3:
			pos, dirn = triangulate(pts)

		# Initiate the starting sequence
		if starting:
			marker = start
			rts, angle, dist = navigate(pos, dirn, start[seq:seq+1])
			if dist < 5 or cv2.waitKey(1) == ord(' '):
				seq += 1
				if seq == len(start):
					seq = 0
					dist = 0
					starting = False

		# Initiate the restarting sequence
		elif restarting:
			marker = restart
			rts, angle, dist = navigate(pos, dirn, restart[seq:seq+1])
			if dist < 5 or cv2.waitKey(1) == ord(' '):
				seq += 1
				if seq == len(restart):
					seq = 0
					dist = 0
					restarting = False

		# Initiate the returning sequence
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

		# Initialise the ending sequence
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

		# Defining a params dict for the parameters to be sent to the API 
		parameters = {
			"angle": angle,
			"distance": dist
		} 
  
		# Sending get request and saving the response as response object 
		pool.apply_async(requests.get, [url + "/move", parameters])

	# Draw annotations on every frame
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

	# Exit program when Esc key is pressed
	if c == ord('\x1b'):
		break

	# Pause the sequence when p is pressed
	elif c == ord('p'):
		finished = not finished

	# Restart the sequence when r is pressed
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
