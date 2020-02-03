# import the necessary packages
from blob_detection import detect
from utils import triangulate, navigate, draw_vtm, draw_bot, draw_rts, display_msg, remove_vtm
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

dev_mode = True

print("Starting camera...")

if dev_mode:
	cap = cv2.VideoCapture('capture.mp4')
else:
	cap = cv2.VideoCapture(1)

has_vtm = False
starting = False
restarting = False
ending = False

# Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
out = cv2.VideoWriter('output.avi',cv2.VideoWriter_fourcc(*'XVID'), 30.0, (640,480))

ret, frame = cap.read()
mask = cv2.imread('mask.png', 0)

# Threshold of green in HSV space 
lower_green = np.array([40, 40, 40]) 
upper_green = np.array([70, 255, 255])

vtms = []

while cap.isOpened() and len(vtms) != num_vtms:
	ret, frame = cap.read()
	vtms = detect(frame, mask, lower_green, upper_green)

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
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

frame_rate = 30
prev = 0

drop_vtm = [np.array([340, 280]), np.array([80, 280]), np.array([80, 160])]
start = [np.array([60, 285]),np.array([345, 285])]
restart = [np.array([60, 290]),np.array([345, 285])]
end = [np.array([60, 450])]

seq = 0

pos = np.array([60, 450])
dirn = np.array([0, -10])

while cap.isOpened():
	time_elapsed = time.time() - prev
	ret, frame = cap.read()

	# frame = cv2.bitwise_and(frame, frame, mask=mask)

	if time_elapsed > 1./frame_rate:
		prev = time.time()

		# Threshold of magenta in HSV space 
		lower_magenta = np.array([160, 40, 40]) 
		upper_magenta = np.array([180, 255, 255]) 

		pts = detect(frame, mask, lower_magenta, upper_magenta)

		if len(pts) >= 3:
			pos, dirn = triangulate(pts)

		if starting:
			rts, angle, dist = navigate(pos, dirn, start[seq:seq+1])
			if dist < 10:
			# if cv2.waitKey(1) & 0xFF == ord('n'):
				seq += 1
				if seq == len(start):
					seq = 0
					starting = False
		elif restarting:
			rts, angle, dist = navigate(pos, dirn, restart[seq:seq+1])
			if dist < 10:
			# if cv2.waitKey(1) & 0xFF == ord('n'):
				seq += 1
				if seq == len(restart):
					seq = 0
					restarting = False
		elif has_vtm:
			rts, angle, dist = navigate(pos, dirn, drop_vtm[seq:seq+1])
			if dist < 10:
			# if cv2.waitKey(1) & 0xFF == ord('n'):
				seq += 1
				if seq == len(drop_vtm):
					seq = 0
					has_vtm = False

					# r = requests.get(url + "/drop")

					if len(vtms) == 0:
						ending = True
					else:
						restarting = True
		elif ending:
			rts, angle, dist = navigate(pos, dirn, end[seq:seq+1])
			if dist < 10:
			# if cv2.waitKey(1) & 0xFF == ord('n'):
				seq += 1
				if seq == len(end):
					seq = 0
					ending = False
		else:
			rts, angle, dist = navigate(pos, dirn, vtms)
			if dist < 50:
			# if cv2.waitKey(1) & 0xFF == ord('n'):
				has_vtm = True
				remove_vtm(vtms, rts[0])

				# r = requests.get(url + "/grab")

		# defining a params dict for the parameters to be sent to the API 
		parameters = {
			"angle": angle,
			"distance": dist
		} 
  
		# sending get request and saving the response as response object 
		pool.apply_async(requests.get, [url + "/move", parameters])

	draw_vtm(frame, vtms)
	draw_bot(frame, pos, dirn)
	draw_rts(frame, pos, rts, angle, dist)

	display_msg(frame, "Angle={:.2f}, Distance={}".format(angle, dist), (0, 255, 0))

	# Write the frame into the file 'output.avi'
	out.write(frame)

	cv2.imshow('frame', frame)

	if cv2.waitKey(1) & 0xFF == ord('q'):
		break
 
cap.release()
out.release()

cv2.destroyAllWindows()
