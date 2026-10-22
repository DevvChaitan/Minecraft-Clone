import math
import random
import pyglet

pyglet.options["shadow_window"] = False
pyglet.options["debug_gl"] = False

import pyglet.gl as gl

import shader
import player
import chunk
import world
import hit

# Default starter hotbar: 9 essential Minecraft blocks
DEFAULT_HOTBAR = [
	(2, "Grass"),
	(3, "Dirt"),
	(1, "Stone"),
	(4, "Cobblestone"),
	(5, "Planks"),
	(17, "Oak Log"),
	(20, "Glass"),
	(12, "Sand"),
	(44, "Bricks"),
]


class Window(pyglet.window.Window):
	def __init__(self, **args):
		super().__init__(**args)

		# create world
		self.world = world.World()

		# create shader
		self.shader = shader.Shader("vert.glsl", "frag.glsl")
		self.shader_sampler_location = self.shader.find_uniform(b"texture_array_sampler")
		self.shader.use()

		# pyglet clock
		pyglet.clock.schedule_interval(self.update, 1.0 / 60)
		self.mouse_captured = False

		# player
		self.player = player.Player(self.world, self.shader, self.width, self.height)

		# Inventory & Hotbar system (9 slots)
		self.hotbar = [item[0] for item in DEFAULT_HOTBAR]
		self.inventory = {item[0]: 64 for item in DEFAULT_HOTBAR}
		self.selected_slot = 0  # 0 to 8
		self.holding = self.hotbar[self.selected_slot]

		# Notification toast
		self.toast_text = "Press 1-9 or Scroll to change blocks | F: Fly | O: Save | R: Teleport"
		self.toast_timer = 5.0

		# UI / HUD elements
		self.crosshair = pyglet.text.Label(
			"+", font_name="Arial", font_size=20, weight="bold",
			x=self.width // 2, y=self.height // 2,
			anchor_x="center", anchor_y="center",
			color=(255, 255, 255, 220)
		)

		self.hotbar_label = pyglet.text.Label(
			"", font_name="Arial", font_size=12, weight="bold",
			x=self.width // 2, y=14,
			anchor_x="center", anchor_y="bottom",
			color=(255, 255, 255, 255)
		)

		self.info_label = pyglet.text.Label(
			"", font_name="Arial", font_size=11,
			x=12, y=self.height - 14,
			anchor_x="left", anchor_y="top",
			color=(240, 240, 240, 230)
		)

		self.toast_label = pyglet.text.Label(
			"", font_name="Arial", font_size=13, weight="bold",
			x=self.width // 2, y=self.height - 40,
			anchor_x="center", anchor_y="top",
			color=(120, 255, 140, 255)
		)

	def get_block_name(self, block_id):
		if 0 < block_id < len(self.world.block_types):
			b = self.world.block_types[block_id]
			if b:
				return b.name
		return f"Block #{block_id}"

	def update(self, delta_time):
		if not self.mouse_captured:
			self.player.input = [0, 0, 0]

		self.player.update(delta_time)

		# Progressively stream remaining world chunks
		self.world.process_chunk_queue()

		# Toast timer
		if self.toast_timer > 0:
			self.toast_timer -= delta_time

	def on_draw(self):
		self.player.update_matrices()

		# Bind texture array
		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.world.texture_manager.texture_array)
		gl.glUniform1i(self.shader_sampler_location, 0)

		# 3D Depth & Face Culling
		gl.glEnable(gl.GL_DEPTH_TEST)
		gl.glEnable(gl.GL_CULL_FACE)

		# Dynamic sky color: underwater blue if submerged, else sky blue daylight
		if self.player.in_water:
			gl.glClearColor(0.12, 0.35, 0.65, 1.0)
		else:
			gl.glClearColor(0.53, 0.81, 0.98, 1.0)

		self.clear()
		self.world.draw()
		gl.glFinish()

		# 2D HUD Rendering
		self.draw_hud()

	def draw_hud(self):
		# Crosshair at center
		self.crosshair.x = self.width // 2
		self.crosshair.y = self.height // 2
		self.crosshair.draw()

		# Build hotbar text with highlighted selected slot
		hotbar_parts = []
		for i, block_id in enumerate(self.hotbar):
			name = self.get_block_name(block_id)
			count = self.inventory.get(block_id, 0)
			slot_num = i + 1
			if i == self.selected_slot:
				hotbar_parts.append(f"[{slot_num}: {name} ({count})]*")
			else:
				hotbar_parts.append(f"{slot_num}:{name}")

		self.hotbar_label.x = self.width // 2
		self.hotbar_label.text = "   ".join(hotbar_parts)
		self.hotbar_label.draw()

		# Top stats info
		pos = self.player.position
		fly_status = " [FLYING]" if self.player.flying else ""
		water_status = " [SWIMMING]" if self.player.in_water else ""
		active_name = self.get_block_name(self.holding)
		self.info_label.y = self.height - 12
		self.info_label.text = (
			f"Pos: X={pos[0]:.1f} Y={pos[1]:.1f} Z={pos[2]:.1f}{fly_status}{water_status} | "
			f"Holding: Slot {self.selected_slot + 1} ({active_name}) | "
			f"Chunks: {len(self.world.chunks)}"
		)
		self.info_label.draw()

		# Toast notification
		if self.toast_timer > 0:
			self.toast_label.x = self.width // 2
			self.toast_label.y = self.height - 35
			self.toast_label.text = self.toast_text
			self.toast_label.draw()

	# Input handling

	def on_resize(self, width, height):
		gl.glViewport(0, 0, width, height)
		self.player.view_width = width
		self.player.view_height = height

	def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
		if scroll_y != 0:
			# Scroll through hotbar slots
			self.selected_slot = (self.selected_slot - int(scroll_y)) % len(self.hotbar)
			self.holding = self.hotbar[self.selected_slot]
			self.toast_text = f"Selected: {self.get_block_name(self.holding)}"
			self.toast_timer = 1.5

	def on_mouse_press(self, x, y, button, modifiers):
		if not self.mouse_captured:
			self.mouse_captured = True
			self.set_exclusive_mouse(True)
			return

		def hit_callback(current_block, next_block):
			if button == pyglet.window.mouse.RIGHT:
				# Place block from active hotbar slot
				if self.holding:
					self.world.try_set_block(current_block, self.holding, self.player.collider)
			elif button == pyglet.window.mouse.LEFT:
				# Break block and collect it into inventory
				broken_num = self.world.get_block_number(next_block)
				if broken_num and broken_num not in (7, 8, 9, 10, 11):  # Can't collect bedrock or fluid
					name = self.get_block_name(broken_num)
					self.inventory[broken_num] = self.inventory.get(broken_num, 0) + 1
					self.toast_text = f"+1 {name} (Total: {self.inventory[broken_num]})"
					self.toast_timer = 2.0
				self.world.set_block(next_block, 0)
			elif button == pyglet.window.mouse.MIDDLE:
				# Pick block under cursor into active hotbar slot
				picked_num = self.world.get_block_number(next_block)
				if picked_num:
					self.hotbar[self.selected_slot] = picked_num
					self.holding = picked_num
					name = self.get_block_name(picked_num)
					self.toast_text = f"Picked: {name} into Slot {self.selected_slot + 1}"
					self.toast_timer = 2.0

		x_pos, y_pos, z_pos = self.player.position
		y_pos += self.player.eyelevel
		hit_ray = hit.Hit_ray(self.world, self.player.rotation, (x_pos, y_pos, z_pos))

		while hit_ray.distance < hit.HIT_RANGE:
			if hit_ray.step(hit_callback):
				break

	def on_mouse_motion(self, x, y, delta_x, delta_y):
		if self.mouse_captured:
			sensitivity = 0.004
			self.player.rotation[0] += delta_x * sensitivity
			self.player.rotation[1] += delta_y * sensitivity
			self.player.rotation[1] = max(-math.tau / 4, min(math.tau / 4, self.player.rotation[1]))

	def on_mouse_drag(self, x, y, delta_x, delta_y, buttons, modifiers):
		self.on_mouse_motion(x, y, delta_x, delta_y)

	def on_key_press(self, key, modifiers):
		if not self.mouse_captured:
			return

		# Number keys 1-9 to select hotbar slots
		number_keys = [
			pyglet.window.key._1,
			pyglet.window.key._2,
			pyglet.window.key._3,
			pyglet.window.key._4,
			pyglet.window.key._5,
			pyglet.window.key._6,
			pyglet.window.key._7,
			pyglet.window.key._8,
			pyglet.window.key._9,
		]
		if key in number_keys:
			self.selected_slot = number_keys.index(key)
			self.holding = self.hotbar[self.selected_slot]
			self.toast_text = f"Slot {self.selected_slot + 1}: {self.get_block_name(self.holding)}"
			self.toast_timer = 1.5
			return

		if key == pyglet.window.key.D:
			self.player.input[0] += 1
		elif key == pyglet.window.key.A:
			self.player.input[0] -= 1
		elif key == pyglet.window.key.W:
			self.player.input[2] += 1
		elif key == pyglet.window.key.S:
			self.player.input[2] -= 1

		elif key == pyglet.window.key.SPACE:
			self.player.input[1] += 1
		elif key == pyglet.window.key.LSHIFT:
			self.player.input[1] -= 1
		elif key == pyglet.window.key.LCTRL:
			self.player.target_speed = player.SPRINTING_SPEED

		elif key == pyglet.window.key.F:
			self.player.flying = not self.player.flying
			self.toast_text = "Flight Mode: ON" if self.player.flying else "Flight Mode: OFF"
			self.toast_timer = 1.5

		elif key == pyglet.window.key.G:
			# Randomize current hotbar slot to any available game block
			new_id = random.randint(1, len(self.world.block_types) - 1)
			self.hotbar[self.selected_slot] = new_id
			self.holding = new_id
			name = self.get_block_name(new_id)
			self.toast_text = f"Selected: {name} (Slot {self.selected_slot + 1})"
			self.toast_timer = 2.0

		elif key == pyglet.window.key.O:
			self.world.save.save()
			self.toast_text = "World saved to disk successfully!"
			self.toast_timer = 2.0

		elif key == pyglet.window.key.R:
			# Teleport to a random surface location on solid ground (ignoring water)
			max_y = 0
			max_x, max_z = (0, 0)
			min_x, min_z = (0, 0)

			for pos in self.world.chunks:
				x, y, z = pos
				max_y = max(max_y, (y + 1) * chunk.CHUNK_HEIGHT)
				max_x = max(max_x, (x + 1) * chunk.CHUNK_WIDTH)
				min_x = min(min_x, x * chunk.CHUNK_WIDTH)
				max_z = max(max_z, (z + 1) * chunk.CHUNK_LENGTH)
				min_z = min(min_z, z * chunk.CHUNK_LENGTH)

			x = random.randint(min_x, max_x)
			z = random.randint(min_z, max_z)

			for y in range(chunk.CHUNK_HEIGHT - 1, -1, -1):
				num = self.world.get_block_number((x, y, z))
				if not num:
					continue
				if num in (8, 9, 10, 11):  # Don't teleport into water or lava
					continue

				self.player.teleport((x, y + 1, z))
				self.toast_text = f"Teleported to ({x}, {y + 1}, {z})"
				self.toast_timer = 2.0
				break

		elif key == pyglet.window.key.ESCAPE:
			self.mouse_captured = False
			self.set_exclusive_mouse(False)

	def on_key_release(self, key, modifiers):
		if not self.mouse_captured:
			return

		if key == pyglet.window.key.D:
			self.player.input[0] -= 1
		elif key == pyglet.window.key.A:
			self.player.input[0] += 1
		elif key == pyglet.window.key.W:
			self.player.input[2] -= 1
		elif key == pyglet.window.key.S:
			self.player.input[2] += 1

		elif key == pyglet.window.key.SPACE:
			self.player.input[1] -= 1
		elif key == pyglet.window.key.LSHIFT:
			self.player.input[1] += 1
		elif key == pyglet.window.key.LCTRL:
			self.player.target_speed = player.WALKING_SPEED


class Game:
	def __init__(self):
		self.config = gl.Config(double_buffer=True, major_version=3, minor_version=3, depth_size=16)
		self.window = Window(
			config=self.config, width=1280, height=720, caption="Minecraft Clone", resizable=True, vsync=False
		)

	def run(self):
		pyglet.app.run()


if __name__ == "__main__":
	game = Game()
	game.run()
