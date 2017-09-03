import camera
import gs

spawnpoints = []
index_spawnpoint = -1


def post_load_scene(scn, openvr_frame_renderer, gui):
	global spawnpoints, index_spawnpoint

	index_spawnpoint = -1
	spawnpoints = []
	for node in scn.GetNodes():
		if "spawnpoint" in node.GetName() or "spawn point" in node.GetName():
			spawnpoints.append(node.GetName())


def update_gui(scn, openvr_frame_renderer, gui):
	global index_spawnpoint
	if gui.CollapsingHeader("Spawnpoint List") or index_spawnpoint == -1:
		gui.Indent()

		if len(spawnpoints) > 1:
			new_index_spawnpoint = gui.Combo("spawnpoint", spawnpoints, index_spawnpoint)
			if new_index_spawnpoint != index_spawnpoint:
				index_spawnpoint = new_index_spawnpoint
				camera.reset_view(scn, scn.GetCurrentCamera(), openvr_frame_renderer, scn.GetNode(spawnpoints[index_spawnpoint]))

		if gui.Button("Reset camera to the spanwpoint position") or index_spawnpoint == -1:
			if index_spawnpoint == -1:
				index_spawnpoint = 0
			if 0 <= index_spawnpoint < len(spawnpoints):
				camera.reset_view(scn, scn.GetCurrentCamera(), openvr_frame_renderer, scn.GetNode(spawnpoints[index_spawnpoint]))

		gui.Unindent()
