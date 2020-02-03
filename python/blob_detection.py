# import the necessary packages
from imutils import contours
from skimage import measure
import numpy as np
import imutils
import cv2

def detect(frame, mask, lower, upper):
	# It converts the BGR color space of image to HSV color space 
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) 

	# apply mask to image
	hsv = cv2.bitwise_and(hsv, hsv, mask=mask)

	# preparing the mask to overlay 
	thresh = cv2.inRange(hsv, lower, upper) 

	# perform a series of erosions and dilations to remove
	# any small blobs of noise from the thresholded image
	thresh = cv2.erode(thresh, None, iterations=1)
	thresh = cv2.dilate(thresh, None, iterations=1)

	# set up the detector with custom parameters
	params = cv2.SimpleBlobDetector_Params()
	params.filterByArea = True
	params.minArea = 30
	params.maxArea = 1000
	params.filterByCircularity = False
	params.filterByColor = False
	params.filterByConvexity = False
	params.filterByInertia = False

	detector = cv2.SimpleBlobDetector_create(params)

	# detect blobs and save keypoints as np array
	kps = detector.detect(thresh)
	pts = [np.array([kp.pt[0], kp.pt[1]]).astype(int) for kp in kps] 

	return pts