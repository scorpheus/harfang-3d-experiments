import gs
import helper_2d

# def authorise_show_gui():
# 	return not vcr.playing_record_frame
#
#
# def update_gui(scn, openvr_frame_renderer, gui):
# 	clap_beep.update_clap(gui)
#
# 	vcr.record_and_play(scn, openvr_frame_renderer, gui)
# 	vcr.calibration(scn, openvr_frame_renderer, gui)
#
#
# def authorise_update_controller():
# 	return not vcr.playing and not vcr.playing_record_frame
#
#
# def authorise_update_camera_move():
# 	return not vcr.playing and not vcr.playing_record_frame
#
#
# def pre_update(scn, openvr_frame_renderer):
# 	vcr.pre_update(scn, openvr_frame_renderer)

render_tgt_a = None
gpu_texture_a = None
render_tgt_b = None
gpu_texture_b = None
render_tgt_scene = None
gpu_texture_scene = None
single_texture_shader = None

scn_glow = None

plus = gs.GetPlus()


def create_scene_render_target(w, h):
	renderer = plus.GetRendererAsync()
	tex = renderer.NewTexture()
	renderer.CreateTexture(tex, w, h, gs.GpuTexture.RGBAF)

	rtt = renderer.NewRenderTarget()
	renderer.CreateRenderTarget(rtt)
	renderer.SetRenderTargetColorTexture(rtt, tex)

	return rtt, tex


def pre_update(scn, openvr_frame_renderer):
	if render_tgt_scene is not None:
		plus.GetRendererAsync().SetRenderTarget(render_tgt_scene)

vtxs = None
uvs = None

app_stages = [{"name_group": "groupe_all", "sound": "plugins/grotte/voice/groupe_all_1.ogg"},
              {"name_group": "groupe_01_02", "sound": "plugins/grotte/voice/groupe_01_02.ogg"},
              {"name_group": "groupe_01", "sound": "plugins/grotte/voice/groupe_01.ogg"},
              {"name_group": "groupe_09", "sound": "plugins/grotte/voice/groupe_09.ogg"},
              {"name_group": "groupe_07", "sound": "plugins/grotte/voice/groupe_07.ogg"},
              {"name_group": "groupe_10", "sound": "plugins/grotte/voice/groupe_10.ogg"},
              {"name_group": "groupe_08", "sound": "plugins/grotte/voice/groupe_08.ogg"},
              {"name_group": "groupe_04", "sound": "plugins/grotte/voice/groupe_04.ogg"},
              {"name_group": "groupe_05_06_01", "sound": "plugins/grotte/voice/groupe_05_06_01.ogg"},
              {"name_group": "groupe_01_02_05_06_09", "sound": "plugins/grotte/voice/groupe_01_02_05_06_09.ogg"},
              {"name_group": "groupe_05_06_08", "sound": "plugins/grotte/voice/groupe_05_06_08.ogg"},
              {"name_group": "groupe_05", "sound": "plugins/grotte/voice/groupe_05.ogg"},
              {"name_group": "groupe_05_06_02", "sound": "plugins/grotte/voice/groupe_05_06_02.ogg"},
              {"name_group": "groupe_all", "sound": "plugins/grotte/voice/groupe_all_2.ogg"}
              ]
current_stages = 0
current_node_groupe = None
current_audio_group = None
counter_wait = -1.0


def change_groupe(scn, gui, openvr_frame_renderer):
	global current_stages, current_node_groupe, current_audio_group, counter_wait

	counter_wait -= plus.GetClockDt().to_sec()

	# switch highlighted group
	if (counter_wait < 0.0 and current_audio_group is None and current_node_groupe is None) or plus.KeyPress(gs.InputDevice.KeySpace):
		counter_wait = 1.0
		for node in scn_glow.GetNodes():
			node.SetEnabled(False)

		node = scn_glow.GetNode(app_stages[current_stages]["name_group"])
		if node is not None:
			node.SetEnabled(True)
			current_node_groupe = node
		else:
			current_node_groupe = None

		current_stages += 1
		if current_stages >= len(app_stages):
			current_stages = 0

	# launch audio after 1 sec, and if the user find it
	if counter_wait < 0.0 and current_audio_group is None and not gui.WantCaptureMouse():
		controller0 = gs.GetInputSystem().GetDevice("openvr_controller_0")
		# if slighlty press gachette
		if openvr_frame_renderer is not None and controller0 is not None and controller0.GetValue(gs.InputDevice.InputButton2) > 0.2:
			mat_controller = controller0.GetMatrix(gs.InputDevice.MatrixHead)

			pos_cam = scn.GetCurrentCamera().GetTransform().GetPosition()
			pos_laser = mat_controller.GetTranslation() + pos_cam
			dir_laser = mat_controller.GetZ()

			hit, trace = scn.GetPhysicSystem().Raycast(pos_laser, dir_laser, 4)
			if hit:
				scene_simple_graphic = scn.GetComponent("SceneOverlay")
				helper_2d.draw_line(scene_simple_graphic, pos_laser, trace.GetPosition(), gs.Color(238 / 255, 235 / 255, 92 / 255))

				name = trace.GetNode().GetName()
				if name == app_stages[current_stages]["name_group"] and controller0.GetValue(gs.InputDevice.InputButton2) == 1.0:
					current_audio_group = plus.GetMixer().Stream(app_stages[current_stages]["sound"])
		elif openvr_frame_renderer is None:
			current_audio_group = plus.GetMixer().Stream(app_stages[current_stages]["sound"])

	# if the audio finish, enable the switch group
	if current_audio_group is not None and plus.GetMixer().GetPlayState(current_audio_group) != gs.MixerPlaying:
		current_audio_group = None
		current_node_groupe = None
		counter_wait = 1.0


def update(scn, gui, openvr_frame_renderer):
	global render_tgt_a, render_tgt_b, render_tgt_scene, gpu_texture_a, gpu_texture_b, gpu_texture_scene, scn_glow, single_texture_shader, vtxs, uvs

	if not scn.IsReady():
		return

	screen_size = plus.GetRendererAsync().GetCurrentOutputWindow().GetSize()
	if render_tgt_a is None:
		render_tgt_a, gpu_texture_a = create_scene_render_target(screen_size.x, screen_size.y)
		render_tgt_b, gpu_texture_b = create_scene_render_target(screen_size.x, screen_size.y)

		render_tgt_scene, gpu_texture_scene = create_scene_render_target(screen_size.x, screen_size.y)

		scn_glow = plus.NewScene(False, False)
		plus.AddEnvironment(scn_glow, gs.Color.Transparent)  # clear color to transparent

		scn_glow.SetCurrentCamera(plus.AddCamera(scn_glow, scn.GetCurrentCamera().GetTransform().GetWorld()))

		# find all node with name group, insert in the scn_glow and remove from the other
		for node in scn.GetNodes():
			if "group" in node.GetName():
				new_node = plus.AddGeometry(scn_glow, node.GetObject().GetGeometry().GetName(), node.GetTransform().GetWorld())
				new_node.SetName(node.GetName())
				# remove from the old
				scn.RemoveNode(node)

		plus.UpdateScene(scn_glow, gs.time(0))
		plus.UpdateScene(scn_glow, gs.time(0))

		single_texture_shader = plus.GetRendererAsync().LoadShader("assets/blur_texture.isl")

		vtxs = [gs.Vector3(0, 0, 0.5), gs.Vector3(0, screen_size.y, 0.5), gs.Vector3(screen_size.x, screen_size.y, 0.5), gs.Vector3(0, 0, 0.5), gs.Vector3(screen_size.x, screen_size.y, 0.5), gs.Vector3(screen_size.x, 0, 0.5)]
		uvs = [gs.Vector2(0, 1), gs.Vector2(0, 0), gs.Vector2(1, 0), gs.Vector2(0, 1), gs.Vector2(1, 0), gs.Vector2(1, 1)]

	# check if change groupe
	change_groupe(scn, gui, openvr_frame_renderer)

	# render the geo in the first render target
	plus.GetRendererAsync().SetRenderTarget(render_tgt_a)
	plus.GetRendererAsync().Clear(gs.Color(0, 0, 0, 0))
	plus.GetRendererAsync().SetViewport(gs.fRect(0, 0, screen_size.x, screen_size.y))

	if scn_glow.GetCurrentCamera() is not None:
		scn_glow.GetCurrentCamera().GetTransform().SetWorld(scn.GetCurrentCamera().GetTransform().GetWorld())
	plus.UpdateScene(scn_glow, gs.time(0))

	# render the first picture into the main scene second picture
	def blur(tgt_1, pict_1, tgt_2, pict_2):
		plus.GetRendererAsync().SetRenderTarget(tgt_2)
		plus.GetRendererAsync().SetViewport(gs.fRect(0, 0, screen_size.x, screen_size.y))
		plus.GetRendererAsync().Set2DMatrices()
		plus.GetRendererAsync().EnableBlending(True)
		plus.GetRendererAsync().SetShader(single_texture_shader)
		plus.GetRenderSystemAsync().SetShaderEngineValues()
		horizontal = 0
		for i in range(5):
			plus.GetRendererAsync().SetRenderTarget(tgt_2)
			plus.GetRendererAsync().Clear(gs.Color(0, 0, 0, 0))
			plus.GetRendererAsync().SetShaderTexture("u_tex", pict_1)
			plus.GetRendererAsync().SetShaderValue("horizontal", horizontal)
			plus.GetRenderSystemAsync().DrawTriangleUV(2, vtxs, uvs)

			plus.GetRendererAsync().DrawFrame()
			plus.GetRendererAsync().Sync()
			tgt_1, tgt_2 = tgt_2, tgt_1
			pict_1, pict_2 = pict_2, pict_1
			horizontal = (horizontal + 1) % 2

		return pict_1

	if single_texture_shader is not None and single_texture_shader.IsReady():
		gpu_texture_blur = gpu_texture_a #blur(render_tgt_a, gpu_texture_a, render_tgt_b, gpu_texture_b)

		# render the final picture
		plus.GetRendererAsync().SetRenderTarget(None)
		plus.GetRendererAsync().SetViewport(gs.fRect(0, 0, screen_size.x, screen_size.y))

		# render the slow scene output
		plus.Texture2D(0, 0, 1, gpu_texture_scene, gs.Color.White, False, True)
		plus.SetBlend2D(gs.BlendAlpha)
		plus.Texture2D(0, 0, 1, gpu_texture_blur, gs.Color.White, False, True)
		plus.SetBlend2D(gs.BlendOpaque)


