import switch_textures


def load_params(save, scn, openvr_frame_renderer, gui):
	switch_textures.load_params(save, scn, openvr_frame_renderer, gui)


def save_params(save, scn, openvr_frame_renderer, gui):
	switch_textures.save_params(save, scn, openvr_frame_renderer, gui)


def post_load_scene(scn, openvr_frame_renderer, gui):
	switch_textures.post_load_scene(scn, openvr_frame_renderer, gui)


def update_gui(scn, openvr_frame_renderer, gui):
	if gui.CollapsingHeader("Switch Texture"):
		gui.Indent()
		switch_textures.update_gui(scn, openvr_frame_renderer, gui)
		gui.Unindent()


def update(scn, gui, openvr_frame_renderer):
	switch_textures.update(scn, openvr_frame_renderer)