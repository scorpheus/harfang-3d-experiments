import gs
import os
import math
import vr_controller
import json
import helper_2d

plus = gs.GetPlus()


path_object_textures = ""
catalogue = None


def load_params(save, scn, openvr_frame_renderer, gui):
	global path_object_textures, catalogue
	if "path_object_textures_catalogue" in save:
		path_object_textures = save["path_object_textures_catalogue"]
		if os.path.exists(path_object_textures):
			with open(path_object_textures, 'r') as outfile:
				catalogue = json.load(outfile)


def save_params(save, scn, openvr_frame_renderer, gui):
	save["path_object_textures_catalogue"] = path_object_textures


def post_load_scene(scn, openvr_frame_renderer, gui):
	if catalogue is None or not len(catalogue):
		return
	# get the trigger
	for trigger_object, data in catalogue.items():
		node = scn.GetNode(trigger_object)
		if node is not None:
			catalogue[trigger_object]["node"] = node
			catalogue[trigger_object]["nb_texture"] = 0

			for name_object, data_object in data["object"].items():
				node = scn.GetNode(name_object)
				if node is not None:
					data_object["node"] = node

					# add the rigid body to raycast later
					if node.GetComponent("RigidBody") is None:
						node.AddComponent(gs.MakeRigidBody())
						mesh_col = gs.MakeMeshCollision()
						mesh_col.SetGeometry(gs.LoadCoreGeometry(node.GetObject().GetGeometry().GetName()))
						mesh_col.SetMass(0)
						node.AddComponent(mesh_col)
						node.SetIsStatic(True)

					# load all texture to gputexture
					data_object["diffuse_gpu"] = []
					for diffuse_map in data_object["diffuse_map"]:
						data_object["diffuse_gpu"].append(plus.GetRendererAsync().LoadTexture("export/"+diffuse_map))
						catalogue[trigger_object]["nb_texture"] += 1


def update_gui(scn, openvr_frame_renderer, gui):
	global catalogue, path_object_textures
	if gui.Button("Load switch object textures file"):
		current_filename = gs.OpenFileDialog("Load switch object textures file", "*.json", "")[1]
		if current_filename != "":
			with open(current_filename, 'r') as outfile:
				catalogue = json.load(outfile)
				path_object_textures = current_filename

				post_load_scene(scn, openvr_frame_renderer, gui)


button_pressed = False
current_room = "trigger_room"

width_car, height_card = 0.06, 0.09
radius_button = 0.042 / 2 + 0.01 + height_card / 2


def update(scn, openvr_frame_renderer):
	global button_pressed
	if catalogue is None or len(catalogue) <= 0:
		return


	controller0 = gs.GetInputSystem().GetDevice("openvr_controller_0")

	pos_laser = None
	dir_laser = None
	click_on_switch = False

	if openvr_frame_renderer is not None and controller0 is not None:
		# if controller0.GetValue(gs.InputDevice.InputButton2) > 0.2:
		mat_controller = controller0.GetMatrix(gs.InputDevice.MatrixHead)

		pos_cam = scn.GetCurrentCamera().GetTransform().GetPosition()
		pos_laser = mat_controller.GetTranslation() + pos_cam
		dir_laser = mat_controller.GetZ()

		if controller0.GetValue(gs.InputDevice.InputButton2) == 1.0:
			click_on_switch = True
	else:
		# if plus.KeyDown(gs.InputDevice.KeySpace) or plus.KeyDown(gs.InputDevice.KeyW):
		pos_laser = scn.GetCurrentCamera().GetTransform().GetPosition()
		dir_laser = scn.GetCurrentCamera().GetTransform().GetWorld().GetZ()

		if plus.KeyDown(gs.InputDevice.KeyW):
			click_on_switch = True


	# draw card
	controller1 = gs.GetInputSystem().GetDevice("openvr_controller_1")

	if openvr_frame_renderer is not None and controller1 is not None:
		# draw the current cards
		mat_controller = gs.Matrix4.TranslationMatrix(scn.GetCurrentCamera().GetTransform().GetPosition()) * controller1.GetMatrix(gs.InputDevice.MatrixHead)
		mat_controller = mat_controller * gs.Matrix4.TranslationMatrix((0, 0.0053, -0.049)) * gs.Matrix4.RotationMatrix((-6.0 * 3.1415 / 180.0, 0, 0))
	else:
		mat_controller = gs.Matrix4.TranslationMatrix(scn.GetCurrentCamera().GetTransform().GetWorld().GetZ() * 5) * scn.GetCurrentCamera().GetTransform().GetWorld()

	min_angle, max_angle = 0, 3.1415
	for name_object, data_object in catalogue[current_room]["object"].items():
		if "diffuse_gpu" in data_object:
			for id_diffuse, diffuse_gpu in enumerate(data_object["diffuse_gpu"]):
				angle = min_angle + (max_angle - min_angle) * (id_diffuse / catalogue[current_room]["nb_texture"])
				mat = mat_controller * gs.Matrix4.RotationMatrix((-math.pi, 0, 0)) * gs.Matrix4.RotationMatrix((0, angle, 0)) * gs.Matrix4.TranslationMatrix((0, 0, radius_button))
				helper_2d.draw_quad(scn.GetComponents("SceneOverlay")[0], mat, width_car, height_card, diffuse_gpu)


				# test collision
				p0 = scn.GetCurrentCamera().GetTransform().GetPosition()
				p1 = mat.GetTranslation()

				p0 = pos_laser
				p1 = pos_laser + dir_laser

				p_co = mat.GetTranslation()
				p_no = mat.GetZ()
				point_on_plane = helper_2d.intersect_line_plane(p0, p1, p_co, p_no)

				if point_on_plane is not None:
					inv_mat = mat.InversedFast()
					pos = mat.GetTranslation()
					axis = [mat.GetX() * width_car / 2, mat.GetY(), mat.GetZ() * height_card / 2]
					poly_card = [(pos - axis[0] - axis[2]) * inv_mat,
					             (pos + axis[0] - axis[2]) * inv_mat,
					             (pos + axis[0] + axis[2]) * inv_mat,
					             (pos - axis[0] + axis[2]) * inv_mat]

					point_on_plane = point_on_plane * inv_mat

					if helper_2d.point_in_poly_2d(point_on_plane, poly_card):
						print("collide on {}".format(data_object["diffuse_map"][id_diffuse]))


	#
	# controller0 = gs.GetInputSystem().GetDevice("openvr_controller_0")
	#
	# pos_laser = None
	# dir_laser = None
	# click_on_switch = False
	#
	# if openvr_frame_renderer is not None and controller0 is not None:
	# 	if controller0.GetValue(gs.InputDevice.InputButton2) > 0.2:
	# 		mat_controller = controller0.GetMatrix(gs.InputDevice.MatrixHead)
	#
	# 		pos_cam = scn.GetCurrentCamera().GetTransform().GetPosition()
	# 		pos_laser = mat_controller.GetTranslation() + pos_cam
	# 		dir_laser = mat_controller.GetZ()
	#
	# 		if controller0.GetValue(gs.InputDevice.InputButton2) == 1.0:
	# 			click_on_switch = True
	# else:
	# 	if plus.KeyDown(gs.InputDevice.KeySpace) or plus.KeyDown(gs.InputDevice.KeyW):
	# 		pos_laser = scn.GetCurrentCamera().GetTransform().GetPosition()
	# 		dir_laser = scn.GetCurrentCamera().GetTransform().GetWorld().GetZ()
	#
	# 	if plus.KeyDown(gs.InputDevice.KeyW):
	# 		click_on_switch = True
	#
	# if pos_laser is not None:
	# 	hit, trace = scn.GetPhysicSystem().Raycast(pos_laser, dir_laser, 1)
	# 	if hit:
	# 		# if need to switch to selected material
	# 		current_material = selected_node.GetObject().GetGeometry().GetMaterial(0)
	# 		if current_material != selected_material:
	# 			geo = selected_node.GetObject().GetGeometry()
	# 			for m in range(geo.GetMaterialCount()):
	# 				geo.SetMaterial(m, selected_material)
	# 				selected_material.SetTexture("diffuse_map", current_material.GetTexture("diffuse_map"))
	#
	# 			new_diffuse_tex = plus.GetRendererAsync().LoadTexture(catalogue[name]["diffuse_map"][catalogue[name]["index"]])
	#
	# 			selected_material.SetTexture("diffuse_map", new_diffuse_tex)
	# 			selected["m"][0].SetTexture("diffuse_map", new_diffuse_tex)