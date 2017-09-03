import vcr
import clap_beep


def load_params(save, scn, openvr_frame_renderer, gui):
	vcr.load_params(save, scn, openvr_frame_renderer, gui)


def save_params(save, scn, openvr_frame_renderer, gui):
	vcr.save_params(save, scn, openvr_frame_renderer, gui)


def authorise_show_gui():
	return not vcr.playing_record_frame


def update_gui(scn, openvr_frame_renderer, gui):
	if gui.CollapsingHeader("VCR"):
		gui.Indent()

		clap_beep.update_clap(gui)

		vcr.record_and_play(scn, openvr_frame_renderer, gui)
		vcr.calibration(scn, openvr_frame_renderer, gui)

		gui.Unindent()


def authorise_update_controller():
	return not vcr.playing and not vcr.playing_record_frame


def authorise_update_camera_move():
	return not vcr.playing and not vcr.playing_record_frame


def pre_update(scn, openvr_frame_renderer):
	vcr.pre_update(scn, openvr_frame_renderer)


def update(scn, gui, openvr_frame_renderer):
	vcr.update(scn, openvr_frame_renderer)