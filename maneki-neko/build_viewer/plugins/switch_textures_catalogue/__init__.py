import switch_textures_catalogue


def load_params(save, scn, openvr_frame_renderer, gui):
	switch_textures_catalogue.load_params(save, scn, openvr_frame_renderer, gui)


def save_params(save, scn, openvr_frame_renderer, gui):
	switch_textures_catalogue.save_params(save, scn, openvr_frame_renderer, gui)


def post_load_scene(scn, openvr_frame_renderer, gui):
	switch_textures_catalogue.post_load_scene(scn, openvr_frame_renderer, gui)


def update_gui(scn, openvr_frame_renderer, gui):
	if gui.CollapsingHeader("Switch Texture Catalogue"):
		gui.Indent()
		switch_textures_catalogue.update_gui(scn, openvr_frame_renderer, gui)
		gui.Unindent()


def update(scn, gui, openvr_frame_renderer):
	switch_textures_catalogue.update(scn, openvr_frame_renderer)