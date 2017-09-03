import gs
import os
import vr_controller
import json

plus = gs.GetPlus()


path_object_textures = ""
switch_object_textures = None


def load_params(save, scn, openvr_frame_renderer, gui):
	global path_object_textures, switch_object_textures
	if "path_object_textures" in save:
		path_object_textures = save["path_object_textures"]
		if os.path.exists(path_object_textures):
			with open(path_object_textures, 'r') as outfile:
				switch_object_textures = json.load(outfile)


def save_params(save, scn, openvr_frame_renderer, gui):
	save["path_object_textures"] = path_object_textures


def post_load_scene(scn, openvr_frame_renderer, gui):
	if switch_object_textures is None or not len(switch_object_textures):
		return

	for name_object, data in switch_object_textures.items():
		node = scn.GetNode(name_object)
		if node is not None:
			switch_object_textures[name_object]["node"] = node

			# add the rigid body to raycast later
			if node.GetComponent("RigidBody") is None:
				node.AddComponent(gs.MakeRigidBody())
				mesh_col = gs.MakeMeshCollision()
				mesh_col.SetGeometry(gs.LoadCoreGeometry(node.GetObject().GetGeometry().GetName()))
				mesh_col.SetMass(0)
				node.AddComponent(mesh_col)
				node.SetIsStatic(True)


def update_gui(scn, openvr_frame_renderer, gui):
	global switch_object_textures, path_object_textures
	if gui.Button("Load switch object textures file"):
		current_filename = gs.OpenFileDialog("Load switch object textures file", "*.json", "")[1]
		if current_filename != "":
			with open(current_filename, 'r') as outfile:
				switch_object_textures = json.load(outfile)
				path_object_textures = current_filename

				post_load_scene(scn, openvr_frame_renderer, gui)


button_pressed = False
selected_material = None
selected = {"n": None, "m": None}


def update(scn, openvr_frame_renderer):
	global button_pressed, selected_material
	if switch_object_textures is None or len(switch_object_textures) <= 0:
		return

	if selected_material is None:  # load the selected material
		selected_material = plus.LoadMaterial("assets/selected.mat")

	controller0 = gs.GetInputSystem().GetDevice("openvr_controller_0")

	# restore material
	if selected["n"] is not None:
		geo = selected["n"].GetObject().GetGeometry()
		for m in range(geo.GetMaterialCount()):
			geo.SetMaterial(m, selected["m"][m])
		selected["n"] = None
		selected["m"] = None

	pos_laser = None
	dir_laser = None
	click_on_switch = False

	if openvr_frame_renderer is not None and controller0 is not None:
		if controller0.GetValue(gs.InputDevice.InputButton2) > 0.2:
			mat_controller = controller0.GetMatrix(gs.InputDevice.MatrixHead)

			pos_cam = scn.GetCurrentCamera().GetTransform().GetPosition()
			pos_laser = mat_controller.GetTranslation() + pos_cam
			dir_laser = mat_controller.GetZ()

			if controller0.GetValue(gs.InputDevice.InputButton2) == 1.0:
				click_on_switch = True
	else:
		if plus.KeyDown(gs.InputDevice.KeySpace) or plus.KeyDown(gs.InputDevice.KeyW):
			pos_laser = scn.GetCurrentCamera().GetTransform().GetPosition()
			dir_laser = scn.GetCurrentCamera().GetTransform().GetWorld().GetZ()

		if plus.KeyDown(gs.InputDevice.KeyW):
			click_on_switch = True

	if pos_laser is not None:
		hit, trace = scn.GetPhysicSystem().Raycast(pos_laser, dir_laser, 1)
		if hit:
			# helper_2d.draw_line(scene_simple_graphic, pos_laser, trace.GetPosition(),
			#                     gs.Color(238 / 255, 235 / 255, 92 / 255))
			# if not use_vr:
			# 	helper_2d.draw_cross(scene_simple_graphic, trace.GetPosition(),
			# 	                     gs.Color(238 / 255, 235 / 255, 92 / 255))

			name = trace.GetNode().GetName()
			if name in switch_object_textures:
				selected_node = switch_object_textures[name]["node"]

				# if need to switch to selected material
				current_material = selected_node.GetObject().GetGeometry().GetMaterial(0)
				if current_material != selected_material:
					selected["n"] = selected_node
					selected["m"] = []
					geo = selected_node.GetObject().GetGeometry()
					for m in range(geo.GetMaterialCount()):
						selected["m"].append(geo.GetMaterial(m))
						geo.SetMaterial(m, selected_material)
						selected_material.SetTexture("diffuse_map", current_material.GetTexture("diffuse_map"))

				# switch if the trigger is triggered
				if click_on_switch and not button_pressed:
					if len(selected["m"]) > 0:
						new_diffuse_tex = plus.GetRendererAsync().LoadTexture(switch_object_textures[name]["diffuse_map"][switch_object_textures[name]["index"]])
						switch_object_textures[name]["index"] += 1
						if switch_object_textures[name]["index"] >= len(switch_object_textures[name]["diffuse_map"]):
							switch_object_textures[name]["index"] = 0

						selected_material.SetTexture("diffuse_map", new_diffuse_tex)
						selected["m"][0].SetTexture("diffuse_map", new_diffuse_tex)



					# else:
		# 	helper_2d.draw_line(scene_simple_graphic, pos_laser, pos_laser + dir_laser * 10,
		# 	                    gs.Color(238 / 255, 235 / 255, 92 / 255))
		# 	if not use_vr:
		# 		helper_2d.draw_cross(scene_simple_graphic, pos_laser + dir_laser * 0.2,
		# 		                     gs.Color(238 / 255, 235 / 255, 92 / 255), 0.01)

	if click_on_switch:
		if not button_pressed:
			button_pressed = True
	else:
		button_pressed = False