from itertools import combinations
import numpy as np
import cv2

class Edge:
	def __init__(self, a, b):
		self.a = a
		self.b = b
		self.length = np.linalg.norm(a - b)

	def __lt__(self, other):
		return self.length < other.length

def angle_btwn(a, b):
	a = a / np.linalg.norm(a)
	b = b / np.linalg.norm(b)
	n = np.cross(a, b)

	if n > 0:
		return np.arccos(np.dot(a, b))
	else:
		return -np.arccos(np.dot(a, b))

def triangulate(pts):
	edges = [Edge(a, b) for (a, b) in list(combinations(pts, 2))]
	edges.sort()

	diag = edges[2]

	cnrs = []
	for i in range(3):
		cnrs.append(edges[i].a)
		cnrs.append(edges[i].b)

	pos = (diag.a + diag.b)/2
	top_left = np.zeros(2)

	for p in cnrs:
		if not np.array_equal(p, diag.a) and not np.array_equal(p, diag.b):
			top_left = p

	theta = np.radians(45)
	c, s = np.cos(theta), np.sin(theta)
	R = np.array(((c,-s), (s, c)))

	dirn = R.dot(top_left - pos)

	return [pos.astype(int), dirn.astype(int)]

def navigate(pos, dirn, vtms):
	rts = [Edge(pos, vtm) for vtm in vtms]
	rts.sort()

	rt = rts[0]
	
	if rt.length == 0:
		angle = 0
	else:
		angle = angle_btwn(dirn, (rt.b - rt.a))

	return [rts, angle, int(rt.length)]


def draw_vtm(frame, vtms):
	for vtm in vtms:
		cv2.circle(frame, tuple(vtm), 10,
			(0, 0, 255), 1)
		cv2.putText(frame, "({},{})".format(vtm[0], vtm[1]), tuple(vtm - 20),
			cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

def draw_pts(frame, pts):
	for pt in pts:
		cv2.drawMarker(frame, tuple(pt), (0, 255, 0), cv2.MARKER_TILTED_CROSS, 10, 1, 8)
		cv2.putText(frame, "({},{})".format(pt[0], pt[1]), tuple(pt - 20),
			cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

def draw_bot(frame, pos, dirn):
	cv2.line(frame, tuple(pos), tuple(pos + dirn), (0, 0, 255), 1) 

def draw_rts(frame, pos, rts, angle, dist):
	for (i, rt) in enumerate(rts):
		if i == 0:
			cv2.line(frame, tuple(rt.a), tuple(rt.b), (0, 255, 0), 1) 
		if i != 0:
			cv2.line(frame, tuple(rt.a), tuple(rt.b), (0, 0, 255), 1)

def display_msg(frame, msg, color):
	cv2.putText(frame, msg, (10, 30),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

def remove_vtm(vtms, rt):
	for (i, vtm) in enumerate(vtms):
		if np.array_equal(vtm, rt.b):
			vtms.pop(i)

		