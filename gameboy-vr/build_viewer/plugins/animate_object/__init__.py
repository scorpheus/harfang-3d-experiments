import gs
import json


def range_adjust(k, a, b, u, v):
	return (k - a) / (b - a) * (v - u) + u


def clamp(v, a, b):
	if a < b:
		return max(a, min(v, b))
	else:
		return max(b, min(v, a))


playing = False
animations = None
timer = 0.0
max_timer = 10.0


def update_gui(scn, openvr_frame_renderer, gui):
	global playing, timer, max_timer, animations
	if gui.CollapsingHeader("Animate Object"):
		gui.Indent()

		if gui.Button("Play Animation"):
			current_filename = gs.OpenFileDialog("Load an animation file",  "*.json", "")[1]
			animations = None
			if current_filename != "":
				with open(current_filename, 'r') as outfile:
					animations = json.load(outfile)

					# get the max timer
					max_timer = 0.0
					for key, obj in animations.items():
						max_obj = max([float(i["time"]) for i in obj])
						if max_timer < max_obj:
							max_timer = max_obj

					# remove anim key
					for key, obj in animations.items():
						for obj_key in obj:
							n = scn.GetNode(obj_key["object_name"])
							if n is not None:
								n.SetEnabled(False)

					playing = True
		gui.SameLine()
		if gui.Button("Stop Animation"):
			playing = False

		timer = gui.SliderFloat("Timeline animation", timer, 0, max_timer)[1]
		# loop
		if timer > max_timer:
			timer = 0.0

		gui.Unindent()


def update(scn, gui, openvr_frame_renderer):
	global timer
	if playing:
		timer += gs.GetPlus().GetClockDt().to_sec()

		# find object and update there position
		for key, obj in animations.items():
			if key == "camera":
				node = scn.GetCurrentCamera()
			else:
				node = scn.GetNode(key)

			if node is not None:
				# get anim key
				key_a = 0
				for i in range(len(obj)):
					if obj[i]["time"] > timer:
						key_a = i - 1
						break
				# animate only if there is key after to interpolate
				if 0 <= key_a < len(obj)-1:
					# get the 2 key node
					node_a = scn.GetNode(obj[key_a]["object_name"])
					node_b = scn.GetNode(obj[key_a + 1]["object_name"])
					if node_a is not None and node_b is not None:
						# interpolate between the 2 key
						pos_a = node_a.GetTransform().GetWorld().GetTranslation()
						quat_a = gs.Quaternion.FromMatrix3(node_a.GetTransform().GetWorld().GetRotationMatrix())
						pos_b = node_b.GetTransform().GetWorld().GetTranslation()
						quat_b = gs.Quaternion.FromMatrix3(node_b.GetTransform().GetWorld().GetRotationMatrix())

						time_a = obj[key_a]["time"]
						time_b = obj[key_a+1]["time"]

						t = range_adjust(timer, time_a, time_b, 0, 1)

						pos = pos_a + (pos_b - pos_a) * t
						quat = gs.Quaternion.Slerp(t, quat_a, quat_b)

						# if it's for the camera and in case of no vr, up the camera to 1.75
						if key == "camera" and openvr_frame_renderer is None:
							pos.y = pos.y + 1.75

						node.GetTransform().SetWorld(gs.Matrix4.TransformationMatrix(pos, quat.ToMatrix3()))


