import gs
import os
import math
import vr_controller
import json

recording = False
playing = False
playing_record_frame = False
render_head = False
timer = 0
record_frame = False
counter_frame = 0
records = None
saved_cam_matrix = None
do_calibration = False
records_output_folder = "E:\\frame_exports"
records_save_folder = ""
calibration_matrix = gs.Matrix4.Identity
calibration_fov = 42
current_filename = "camera_pos.json"
show_live_cam = False
draw_calibration_picture = False

fps_record = 25


lts = gs.LuaTaskSystem()
lts.Start(8)  # use a single worker thread

task = lts.PrepareTask("""
-- retrieve the task input values
local pic, name = ...
pic:Convert(gs.Picture.RGB8)
gs.SavePicture(pic, name, "IJG", "q:95")
pic:Free()
""")


def load_params(save, scn, openvr_frame_renderer, gui):
	global records_output_folder, fps_record, records_save_folder
	if "vcr_default_output_folder" in save:
		records_output_folder = save["vcr_default_output_folder"]
	if "vcr_default_save_folder" in save:
		records_save_folder = save["vcr_default_save_folder"]
	if "vcr_default_fps" in save:
		fps_record = int(save["vcr_default_fps"])


def save_params(save, scn, openvr_frame_renderer, gui):
	save["vcr_default_output_folder"] = records_output_folder
	save["vcr_default_save_folder"] = records_save_folder
	save["vcr_default_fps"] = fps_record


def authorise_show_gui():
	return not playing_record_frame


def start_record():
	global recording, records, timer
	recording = True
	records = None
	timer = 0


def stop_record():
	global recording, records, current_filename, records_save_folder
	recording = False
	current_filename = gs.SaveFileDialog("Save a record",  "*.json", records_save_folder)[1]

	if current_filename != "":
		records_save_folder = os.path.dirname(current_filename)

		if os.path.splitext(current_filename)[1] != ".json":
			current_filename += ".json"
		with open(current_filename, 'w') as outfile:
			json.dump(records, outfile)
			save_calibration()


def load_record(scn, openvr_frame_renderer):
	global records, current_filename, saved_cam_matrix, records_save_folder
	current_filename = gs.OpenFileDialog("Load a record",  "*.json", records_save_folder)[1]
	records = None
	if current_filename != "":
		records_save_folder = os.path.dirname(current_filename)
		with open(current_filename, 'r') as outfile:
			records = json.load(outfile)
			load_calibration()

			saved_cam_matrix = scn.GetCurrentCamera().GetTransform().GetWorld()
			scn.GetCurrentCamera().GetCamera().SetZoomFactor(gs.FovToZoomFactor(calibration_fov*3.1415/180.0))
			# remove vr
			if openvr_frame_renderer is not None:
				scn.GetSystem("Renderable").SetFrameRenderer(None)


def start_play(scn, openvr_frame_renderer, record_frame_=False):
	global playing, timer, saved_cam_matrix, record_frame, playing_record_frame, counter_frame, records_output_folder

	load_record(scn, openvr_frame_renderer)
	if records is not None:
		timer = 0
		record_frame = record_frame_
		if record_frame:
			# select the output folder
			current_output_folder = gs.OpenFolderDialog("Select output folder", records_output_folder)[1]
			records_output_folder = "E:\\frame_exports"
			if current_output_folder != "":
				records_output_folder = current_output_folder
			else:
				return

			playing_record_frame = True
			counter_frame = 0
		else:
			playing = True


def stop_play(scn, openvr_frame_renderer):
	global playing, playing_record_frame
	playing = False
	playing_record_frame = False

	if saved_cam_matrix is not None:
		scn.GetCurrentCamera().GetTransform().SetWorld(saved_cam_matrix)
	# reset vr
	if openvr_frame_renderer is not None:
		scn.GetSystem("Renderable").SetFrameRenderer(openvr_frame_renderer)


def save_calibration():
	with open(current_filename+"_calibration.json", 'w') as outfile:
		json.dump({"m": serialize_matrix(calibration_matrix), "fov": calibration_fov}, outfile)


def load_calibration():
	global calibration_matrix, calibration_fov
	if os.path.exists(current_filename+"_calibration.json"):
		with open(current_filename+"_calibration.json", 'r') as outfile:
			output = json.load(outfile)
			calibration_matrix = deserialize_matrix(output["m"])
			calibration_fov = output["fov"]


def record_and_play(scn, openvr_frame_renderer, gui):
	global timer, render_head, fps_record
	temp_recording = gui.Checkbox("Click to Record", recording and not playing and not playing_record_frame)
	if temp_recording and temp_recording != recording:
		start_record()
	elif temp_recording != recording:
		stop_record()

	gui.SameLine()
	temp_playing = gui.Checkbox("Play video", playing and not recording and not playing_record_frame)
	if temp_playing and temp_playing != playing:
		start_play(scn, openvr_frame_renderer)
	elif temp_playing != playing:
		stop_play(scn, openvr_frame_renderer)

	temp_playing = gui.Checkbox("Play and save frame", playing_record_frame and not recording)
	if temp_playing and temp_playing != playing_record_frame:
		start_play(scn, openvr_frame_renderer, True)
	elif temp_playing != playing_record_frame:
		stop_play(scn, openvr_frame_renderer)

	gui.SameLine()
	render_head = gui.Checkbox("Save With Render Head Matrix", render_head)

	fps_record = gui.SliderInt("Recording FPS", fps_record, 1, 128)[1]

	if records is not None and (playing or playing_record_frame):
		timer = gui.SliderFloat("Timeline", timer, 0, max([float(i) for i in records.keys()]))[1]


def calibration(scn, openvr_frame_renderer, gui):
	global calibration_matrix, do_calibration, timer, calibration_fov, show_live_cam, draw_calibration_picture

	show_live_cam = gui.Checkbox("Show live cam", show_live_cam)

	temp_calibration = gui.Checkbox("Calibration", do_calibration)
	if temp_calibration:
		if not show_live_cam and temp_calibration != do_calibration:
			load_record(scn, openvr_frame_renderer)

		# draw alpha picture
		draw_calibration_picture = gui.Checkbox("Draw calibration picture", draw_calibration_picture)
		if draw_calibration_picture:
			gs.GetPlus().Image2D(0, 0, 1.0, "calibration.png", gs.Color(1, 1, 1 ,0.5))

		if gui.Button("Calibrate live from ground"):
			controller1 = gs.GetInputSystem().GetDevice("openvr_controller_1")
			if controller1 is not None:
				calibration_matrix = controller1.GetMatrix(gs.InputDevice.MatrixHead).InversedFast()

		delta = 0.01
		pos_calibration = calibration_matrix.GetTranslation()
		if gui.Button("PosX -"):
			pos_calibration.x -= delta
		gui.SameLine()
		if gui.Button("PosX +"):
			pos_calibration.x += delta
		gui.SameLine()
		pos_calibration.x = gui.InputFloat("px", pos_calibration.x)[1]
		if gui.Button("PosY -"):
			pos_calibration.y -= delta
		gui.SameLine()
		if gui.Button("PosY +"):
			pos_calibration.y += delta
		gui.SameLine()
		pos_calibration.y = gui.InputFloat("py", pos_calibration.y)[1]
		if gui.Button("PosZ -"):
			pos_calibration.z -= delta
		gui.SameLine()
		if gui.Button("PosZ +"):
			pos_calibration.z += delta
		gui.SameLine()
		pos_calibration.z = gui.InputFloat("pz", pos_calibration.z)[1]
		# pos_calibration = gui.InputVector3("Pos", pos_calibration)[1]

		rot_calibration = calibration_matrix.GetRotation()

		if gui.Button("RotX -"):
			rot_calibration.x -= delta
		gui.SameLine()
		if gui.Button("RotX +"):
			rot_calibration.x += delta
		gui.SameLine()
		rot_calibration.x = gui.InputFloat("rx", rot_calibration.x * 180.0/3.1415)[1] * 3.1415 / 180.0
		if gui.Button("RotY -"):
			rot_calibration.y -= delta
		gui.SameLine()
		if gui.Button("RotY +"):
			rot_calibration.y += delta
		gui.SameLine()
		rot_calibration.y = gui.InputFloat("ry", rot_calibration.y * 180.0/3.1415)[1] * 3.1415 / 180.0
		if gui.Button("RotZ -"):
			rot_calibration.z -= delta
		gui.SameLine()
		if gui.Button("RotZ +"):
			rot_calibration.z += delta
		gui.SameLine()
		rot_calibration.z = gui.InputFloat("rz", rot_calibration.z * 180.0/3.1415)[1] * 3.1415 / 180.0

		calibration_matrix = gs.Matrix4.TransformationMatrix(pos_calibration, rot_calibration)

		changed, calibration_fov = gui.SliderFloat("FOV (deg)", calibration_fov, 1, 180)
		if changed:
			scn.GetCurrentCamera().GetCamera().SetZoomFactor(gs.FovToZoomFactor(calibration_fov * 3.1415 / 180.0))

		if records is not None:
			timer = gui.SliderFloat("Timeline", timer, 0, max([float(i) for i in records.keys()]))[1]
	else:
		if temp_calibration != do_calibration:
			save_calibration()
			stop_play(scn, openvr_frame_renderer)

	do_calibration = temp_calibration


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


def update_recording(scn):
	global records, timer
	if records is None:
		records = {}
		timer = 0

	record = {}

	record['cam'] = serialize_matrix(scn.GetCurrentCamera().GetTransform().GetWorld())

	head_controller = gs.GetInputSystem().GetDevice("openvr_hmd")
	if head_controller is not None:
		record['head_controller'] = serialize_matrix(head_controller.GetMatrix(gs.InputDevice.MatrixHead))

	controller0 = gs.GetInputSystem().GetDevice("openvr_controller_0")
	if controller0 is not None:
		record['controller_0'] = serialize_matrix(controller0.GetMatrix(gs.InputDevice.MatrixHead))

	controller1 = gs.GetInputSystem().GetDevice("openvr_controller_1")
	if controller1 is not None:
		record['controller_1'] = serialize_matrix(controller1.GetMatrix(gs.InputDevice.MatrixHead))

	if gs.GetPlus().KeyDown(gs.InputDevice.KeyN):
		record['clap'] = True

	records[str(timer)] = record
	timer += gs.GetPlus().GetClockDt().to_sec()


def update_play(scn, openvr_frame_renderer):
	global timer, playing, counter_frame
	if records is not None:
		nearest_key = min(records.keys(), key=lambda k: abs(float(k) - timer))
		records_list = list(sorted(records))
		index = records_list.index(nearest_key)
		if float(nearest_key) > timer and index - 1 >= 0:
			first_key = records_list[index-1]
			second_key = records_list[index]
		elif index + 1 < len(records_list):
			first_key = records_list[index]
			second_key = records_list[index+1]
		else:
			first_key = records_list[0]
			second_key = records_list[1]

		def interpolate_mat(name_record):
			first_mat = deserialize_matrix(records[first_key][name_record])
			second_mat = deserialize_matrix(records[second_key][name_record])
			t = (timer - float(first_key)) / (float(second_key) - float(first_key))

			pos = first_mat.GetTranslation() + (second_mat.GetTranslation() - first_mat.GetTranslation())*t
			rot = gs.Quaternion.Slerp(t, gs.Quaternion.FromMatrix3(first_mat.GetRotationMatrix()), gs.Quaternion.FromMatrix3(second_mat.GetRotationMatrix())).ToMatrix3()

			return gs.Matrix4.TransformationMatrix(pos, rot)

		cam = scn.GetCurrentCamera()
		if cam is not None:
			if render_head:
				cam.GetTransform().SetWorld(interpolate_mat('cam') * interpolate_mat('head_controller'))
			else:
				cam.GetTransform().SetWorld(interpolate_mat('cam') * interpolate_mat('controller_1') * calibration_matrix)

		for id_controller, controller in enumerate(vr_controller.controller_nodes):
			if controller.GetTransform() is not None:
				if 'controller_{}'.format(id_controller) in records[first_key]:
					controller.GetTransform().SetWorld(interpolate_mat('cam') * interpolate_mat('controller_{}'.format(id_controller)))

		if vr_controller.helmet_node is not None and vr_controller.helmet_node.GetTransform() is not None:
			vr_controller.helmet_node.GetTransform().SetWorld(interpolate_mat('cam') * interpolate_mat('head_controller'))

		if not do_calibration:
			if record_frame:
				pic = gs.Picture()
				if gs.GetPlus().GetRendererAsync().CaptureFramebuffer(pic).get():
					if "clap" in records[first_key]:
						pic.ClearRGBA(1, 0, 1)

					render_path = "{0}\\{1}".format(records_output_folder, os.path.splitext(os.path.basename(current_filename))[0])
					if render_head:
						render_path = "{0}\\{1}_head".format(records_output_folder, os.path.splitext(os.path.basename(current_filename))[0])

					if not os.path.exists(render_path):
						os.mkdir(render_path)
					lts.RunTask(task, [pic, "{0}\\{1}_{2:08d}.jpg".format(render_path, os.path.splitext(os.path.basename(current_filename))[0], counter_frame)])
					counter_frame += 1

				timer += 1.0/fps_record
			else:
				timer += gs.GetPlus().GetClockDt().to_sec()

			if timer > max([float(i) for i in records.keys()]):
				stop_play(scn, openvr_frame_renderer)


def update_gui(scn, openvr_frame_renderer, gui):
	record_and_play(scn, openvr_frame_renderer, gui)
	calibration(scn, openvr_frame_renderer, gui)


def authorise_update_controller():
	return not playing and not playing_record_frame


def authorise_update_camera_move():
	return not playing and not playing_record_frame


def calibrate_offset(scn):
	global calibration_matrix
	temp_timer = 1
	with open("axe_x.json", 'r') as outfile:
		axe_json = json.load(outfile)
		record = axe_json[min(axe_json.keys(), key=lambda k: abs(float(k) - temp_timer))]
		controller_mat_vr = gs.Matrix4.TranslationMatrix(deserialize_matrix(record["controller_1"]).GetTranslation())
		origin_vr = deserialize_matrix(record["controller_0"]).GetTranslation()

		axe_x = (deserialize_matrix(record["head_controller"]).GetTranslation() - origin_vr).Normalized()

	temp_timer = 5
	with open("axe_z.json", 'r') as outfile:
		axe_json = json.load(outfile)
		record = axe_json[min(axe_json.keys(), key=lambda k: abs(float(k) - temp_timer))]
		axe_z = (deserialize_matrix(record["head_controller"]).GetTranslation() - origin_vr).Normalized()

	axe_y = axe_x.Cross(axe_z)

	# change origin
	origin_vr_rotation_mat = gs.Matrix3()
	origin_vr_rotation_mat.SetX(axe_x)
	origin_vr_rotation_mat.SetY(axe_y)
	origin_vr_rotation_mat.SetZ(axe_z)
	origin_vr_mat = gs.Matrix4.TransformationMatrix(origin_vr, origin_vr_rotation_mat)

	controller_mat = origin_vr_mat.InversedFast() * controller_mat_vr
	gs.GetPlus().AddCube(scn, controller_mat, 0.1, 0.1, 0.1)

	cam_mat = gs.Matrix4.TranslationMatrix((3.75, 1.23, 3.02))
	#cam_mat = cam_mat.LookAt(gs.Vector3(0, 0, 0))
	gs.GetPlus().AddCube(scn, cam_mat, 0.1, 0.1, 0.1, "assets/material_diffuse_color_blue.mat")

	#gs.GetPlus().AddCube(scn, gs.Matrix4.Identity, 0.1, 0.1, 0.1, "assets/material_diffuse_color_green.mat")
	#gs.GetPlus().AddCube(scn, origin_vr_mat, 0.1, 0.1, 0.1)
	gs.GetPlus().AddCube(scn, gs.Matrix4.TransformationMatrix(origin_vr, gs.Matrix3.LookAt(axe_x, (0, 1, 0))), 0.01, 0.01, 10, "assets/material_diffuse_color_red.mat")
	gs.GetPlus().AddCube(scn, gs.Matrix4.TransformationMatrix(origin_vr, gs.Matrix3.LookAt(axe_y, (1, 0, 0))), 0.01, 0.01, 10, "assets/material_diffuse_color_green.mat")
	gs.GetPlus().AddCube(scn, gs.Matrix4.TransformationMatrix(origin_vr, gs.Matrix3.LookAt(axe_z, (0, 1, 0))), 0.01, 0.01, 10, "assets/material_diffuse_color_blue.mat")

	#gs.GetPlus().AddCube(scn, controller_mat, 0.1, 0.1, 0.1, "assets/material_diffuse_color_red.mat")


def pre_update(scn, openvr_frame_renderer):
	global saved_cam_matrix
	if show_live_cam:
		saved_cam_matrix = scn.GetCurrentCamera().GetTransform().GetWorld()
		cam = scn.GetCurrentCamera()
		if cam is not None:
			controller1 = gs.GetInputSystem().GetDevice("openvr_controller_1")
			if controller1 is not None:
				cam.GetTransform().SetWorld(saved_cam_matrix * controller1.GetMatrix(gs.InputDevice.MatrixHead) * calibration_matrix)


def update(scn, openvr_frame_renderer):
	if calibration_matrix is None:
		load_calibration()

	if recording:
		update_recording(scn)
	elif playing or playing_record_frame or do_calibration:
		update_play(scn, openvr_frame_renderer)

	if show_live_cam:
		plus = gs.GetPlus()
		size = plus.GetRendererAsync().GetCurrentOutputWindow().GetSize()

		if openvr_frame_renderer is not None:
			scn.GetSystem("Renderable").SetFrameRenderer(None)

		plus.GetRendererAsync().SetViewport(gs.fRect(0, 0, size.x * 0.5, size.y * 0.5))
		plus.GetRendererAsync().SetClippingRect(gs.fRect(0, 0, size.x * 0.5, size.y * 0.5))
		plus.GetRendererAsync().Clear(gs.Color.Black)

		scn.GetCurrentCamera().GetTransform().SetWorld(saved_cam_matrix)

		scn.Update(gs.time(0))
		scn.WaitUpdate()
		scn.Commit()
		scn.WaitCommit()

		plus.GetRendererAsync().SetViewport(gs.fRect(0, 0, size.x, size.y))
		plus.GetRendererAsync().SetClippingRect(gs.fRect(0, 0, size.x, size.y))

		if openvr_frame_renderer is not None:
			scn.GetSystem("Renderable").SetFrameRenderer(openvr_frame_renderer)
