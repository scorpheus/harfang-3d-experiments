

def load_params(save, scn, openvr_frame_renderer, gui):
	pass


def save_params(save, scn, openvr_frame_renderer, gui):
	pass


def post_load_scene(scn, openvr_frame_renderer, gui):
	pass


def authorise_show_gui():
	return True


def update_gui(scn, openvr_frame_renderer, gui):
	if gui.CollapsingHeader("Plugin Name"):
		gui.Indent()
		gui.Unindent()


def authorise_update_controller():
	return True


def pre_update(scn, openvr_frame_renderer):
	pass


def authorise_update_camera_move():
	return True


def update(scn, gui, openvr_frame_renderer):
	pass