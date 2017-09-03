import gs
import os
import collections
import json

render_head = False

calibration_matrix = gs.Matrix4.Identity
calibration_fov = 42


def load_calibration():
	global calibration_matrix, calibration_fov
	if os.path.exists(current_filename+"_calibration.json"):
		with open(current_filename+"_calibration.json", 'r') as outfile:
			output = json.load(outfile)
			calibration_matrix = deserialize_matrix(output["m"])
			calibration_fov = output["fov"]


def serialize_matrix(m):
	return "{0:.6f};{1:.6f};{2:.6f};{3:.6f};{4:.6f};{5:.6f};{6:.6f};{7:.6f};{8:.6f};{9:.6f};{10:.6f};{11:.6f}".format(m.GetRow(0).x, m.GetRow(0).y, m.GetRow(0).z,
	                                                    m.GetRow(1).x, m.GetRow(1).y, m.GetRow(1).z,
	                                                    m.GetRow(2).x, m.GetRow(2).y, m.GetRow(2).z,
	                                                    m.GetRow(3).x, m.GetRow(3).y, m.GetRow(3).z)


def deserialize_matrix(s):
	f = s.split(";")
	m = gs.Matrix4()
	m.SetRow(0, gs.Vector3(float(f[0]), float(f[1]), float(f[2])))
	m.SetRow(1, gs.Vector3(float(f[3]), float(f[4]), float(f[5])))
	m.SetRow(2, gs.Vector3(float(f[6]), float(f[7]), float(f[8])))
	m.SetRow(3, gs.Vector3(float(f[9]), float(f[10]), float(f[11])))
	return m


current_filename = gs.OpenFileDialog("Load a record",  "*.json", "")[1]
# current_filename = "C:/boulot/works/VRViewer/source/capture_video/melanie1.json"

# pivot de camera sous max  (90, 0, -180)
if current_filename != "":
	with open(current_filename, 'r') as outfile:
		records = json.load(outfile)
		records = collections.OrderedDict(sorted(records.items(), key=lambda t: float(t[0])))
		load_calibration()

		def write_matrix(time, mat):
			def convert_to_max(pos):
				return gs.Vector3(pos.x, pos.z, pos.y)

			row0 = convert_to_max(mat.GetRow(0))
			row1 = convert_to_max(mat.GetRow(2))
			row2 = convert_to_max(mat.GetRow(1)) * -1.0
			row3 = convert_to_max(mat.GetRow(3))

			mat.SetRow(0, row0)
			mat.SetRow(1, row1)
			mat.SetRow(2, row2)
			mat.SetRow(3, row3)

			o.write("{},".format(time))

			for i in range(4):
				pos = mat.GetRow(i)
				o.write("{},{},{},".format(pos.x, pos.y, pos.z))
			o.write("\n")

		# with open(current_filename + "_test.csv", 'w') as o:
		# 	write_matrix("0", gs.Matrix4.Identity)
		# 	write_matrix("1", gs.Matrix4.TranslationMatrix((1, 0, 0)))
		# 	write_matrix("2", gs.Matrix4.TranslationMatrix((0, 1, 0)))
		# 	write_matrix("3", gs.Matrix4.TranslationMatrix((0, 0, 1)))
		# 	write_matrix("4", gs.Matrix4.RotationMatrix((1.57, 0, 0)))
		# 	write_matrix("5", gs.Matrix4.RotationMatrix((0, 1.57, 0)))
		# 	write_matrix("6", gs.Matrix4.RotationMatrix((0, 0, 1.57)))
		# 	write_matrix("7", gs.Matrix4.RotationMatrix((1.57, 1.57, 0)))
		# 	write_matrix("8", gs.Matrix4.RotationMatrix((0, 1.57, 1.57)))   #90, 0, 90
		# 	write_matrix("9", gs.Matrix4.RotationMatrix((1.57, 0, 1.57)))   #45 -90 45
		# 	write_matrix("10", gs.Matrix4.RotationMatrix((3.1415, 0, 0)))
		# 	write_matrix("11", gs.Matrix4.RotationMatrix((0, 3.1415, 0)))
		# 	write_matrix("12", gs.Matrix4.RotationMatrix((0, 0, 3.1415)))
		# 	write_matrix("13", gs.Matrix4.RotationMatrix((3.1415, 3.1415, 0))) #0 0 180
		# 	write_matrix("14", gs.Matrix4.RotationMatrix((0, 3.1415, 3.1415))) #180 0 0
		# 	write_matrix("15", gs.Matrix4.RotationMatrix((3.1415, 0, 3.1415))) #0 180 0

		if 'controller_1' in list(records.items())[0][1]:
			with open(current_filename+"_cam.csv", 'w') as o:
				for time, record in records.items():
					mat = deserialize_matrix(record['cam']) * deserialize_matrix(record['controller_1']) * calibration_matrix
					write_matrix(time, mat)

		if 'controller_1' in list(records.items())[0][1]:
			with open(current_filename+"_controller1.csv", 'w') as o:
				for time, record in records.items():
					mat = deserialize_matrix(record['cam']) * deserialize_matrix(record['controller_1'])
					write_matrix(time, mat)

		if 'controller_0' in list(records.items())[0][1]:
			with open(current_filename + "_controller0.csv", 'w') as o:
				for time, record in records.items():
					mat = deserialize_matrix(record['cam']) * deserialize_matrix(record['controller_0'])
					write_matrix(time, mat)

		if 'head_controller' in list(records.items())[0][1]:
			with open(current_filename + "_head_controller.csv", 'w') as o:
				for time, record in records.items():
					mat = deserialize_matrix(record['cam']) * deserialize_matrix(record['head_controller'])
					write_matrix(time, mat)


