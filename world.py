import math

import save
import chunk

import block_type
import texture_manager

# import custom block models

import models


class World:
	def __init__(self):
		self.texture_manager = texture_manager.Texture_manager(16, 16, 256)
		self.block_types = [None]

		# parse block type data file

		blocks_data_file = open("data/blocks.mcpy")
		blocks_data = blocks_data_file.readlines()
		blocks_data_file.close()

		for block in blocks_data:
			if block[0] in ["\n", "#"]:
				continue

			number, props = block.split(":", 1)
			number = int(number)

			name = "Unknown"
			model = models.cube
			texture = {"all": "unknown"}

			for prop in props.split(","):
				prop = prop.strip()
				prop = list(filter(None, prop.split(" ", 1)))

				if prop[0] == "sameas":
					sameas_number = int(prop[1])

					name = self.block_types[sameas_number].name
					texture = dict(self.block_types[sameas_number].block_face_textures)
					model = self.block_types[sameas_number].model

				elif prop[0] == "name":
					name = eval(prop[1])

				elif prop[0][:7] == "texture":
					_, side = prop[0].split(".")
					texture[side] = prop[1].strip()

				elif prop[0] == "model":
					model = eval(prop[1])

			_block_type = block_type.Block_type(self.texture_manager, name, texture, model)

			if number < len(self.block_types):
				self.block_types[number] = _block_type
			else:
				self.block_types.append(_block_type)

		self.texture_manager.generate_mipmaps()

		# load the world

		self.save = save.Save(self)
		self.chunks = {}
		self.save.load()

		for chunk_position in list(self.chunks.keys()):
			self.chunks[chunk_position].update_subchunk_meshes()
			self.chunks[chunk_position].update_mesh()

		# Load queue for all remaining chunks from the 8x8 saved map (-4..3)
		self.load_queue = []
		for x in range(-4, 4):
			for z in range(-4, 4):
				pos = (x, 0, z)
				if pos not in self.chunks:
					self.load_queue.append(pos)

	def generate_procedural_chunk(self, chunk_position):
		cx, cy, cz = chunk_position
		if cy != 0:
			return None

		new_chunk = chunk.Chunk(self, chunk_position)

		for lx in range(chunk.CHUNK_WIDTH):
			wx = cx * chunk.CHUNK_WIDTH + lx
			for lz in range(chunk.CHUNK_LENGTH):
				wz = cz * chunk.CHUNK_LENGTH + lz

				h = int(32 + 8 * math.sin(wx * 0.04) * math.cos(wz * 0.04) + 4 * math.sin((wx + wz) * 0.07))
				h = max(10, min(chunk.CHUNK_HEIGHT - 10, h))

				for y in range(h + 1):
					if y == 0:
						new_chunk.blocks[lx][y][lz] = 7  # bedrock
					elif y < h - 4:
						new_chunk.blocks[lx][y][lz] = 1  # stone
					elif y < h:
						new_chunk.blocks[lx][y][lz] = 3  # dirt
					else:
						new_chunk.blocks[lx][y][lz] = 12 if h <= 28 else 2  # sand or grass

				# Water level up to 28
				for y in range(h + 1, 29):
					new_chunk.blocks[lx][y][lz] = 9  # stationary water

		return new_chunk

	def process_chunk_queue(self):
		# Process up to 2 queued chunks per tick for smooth streaming
		for _ in range(2):
			if not self.load_queue:
				break

			pos = self.load_queue.pop(0)
			loaded = self.save.load_chunk(pos)
			if not loaded:
				# Generate procedural chunk if not in save file
				gen_chunk = self.generate_procedural_chunk(pos)
				if gen_chunk:
					self.chunks[pos] = gen_chunk

			if pos in self.chunks:
				self.chunks[pos].update_subchunk_meshes()
				self.chunks[pos].update_mesh()

				# update neighbor chunks at border to cull border faces
				cx, cy, cz = pos
				for n_pos in [(cx + 1, cy, cz), (cx - 1, cy, cz), (cx, cy, cz + 1), (cx, cy, cz - 1)]:
					if n_pos in self.chunks:
						self.chunks[n_pos].update_subchunk_meshes()
						self.chunks[n_pos].update_mesh()

	def get_chunk_position(self, position):
		x, y, z = position
		return (
			math.floor(x / chunk.CHUNK_WIDTH),
			math.floor(y / chunk.CHUNK_HEIGHT),
			math.floor(z / chunk.CHUNK_LENGTH),
		)

	def get_local_position(self, position):
		x, y, z = position
		return (int(x % chunk.CHUNK_WIDTH), int(y % chunk.CHUNK_HEIGHT), int(z % chunk.CHUNK_LENGTH))

	def get_block_number(self, position):
		x, y, z = position
		chunk_position = self.get_chunk_position(position)

		if chunk_position not in self.chunks:
			return 0

		lx, ly, lz = self.get_local_position(position)
		return self.chunks[chunk_position].blocks[lx][ly][lz]

	def is_opaque_block(self, position):
		block_type_obj = self.block_types[self.get_block_number(position)]
		if not block_type_obj:
			return False
		return not block_type_obj.transparent

	def set_block(self, position, number):
		x, y, z = position
		chunk_position = self.get_chunk_position(position)

		if chunk_position not in self.chunks:
			if number == 0:
				return
			self.chunks[chunk_position] = chunk.Chunk(self, chunk_position)

		if self.get_block_number(position) == number:
			return

		lx, ly, lz = self.get_local_position(position)

		self.chunks[chunk_position].blocks[lx][ly][lz] = number
		self.chunks[chunk_position].modified = True

		self.chunks[chunk_position].update_at_position((x, y, z))
		self.chunks[chunk_position].update_mesh()

		cx, cy, cz = chunk_position

		def try_update_chunk_at_position(chunk_pos, pos):
			if chunk_pos in self.chunks:
				self.chunks[chunk_pos].update_at_position(pos)
				self.chunks[chunk_pos].update_mesh()

		if lx == chunk.CHUNK_WIDTH - 1:
			try_update_chunk_at_position((cx + 1, cy, cz), (x + 1, y, z))
		if lx == 0:
			try_update_chunk_at_position((cx - 1, cy, cz), (x - 1, y, z))

		if ly == chunk.CHUNK_HEIGHT - 1:
			try_update_chunk_at_position((cx, cy + 1, cz), (x, y + 1, z))
		if ly == 0:
			try_update_chunk_at_position((cx, cy - 1, cz), (x, y - 1, z))

		if lz == chunk.CHUNK_LENGTH - 1:
			try_update_chunk_at_position((cx, cy, cz + 1), (x, y, z + 1))
		if lz == 0:
			try_update_chunk_at_position((cx, cy, cz - 1), (x, y, z - 1))

	def try_set_block(self, pos, num, collider):
		if not num:
			return self.set_block(pos, 0)

		for block_collider in self.block_types[num].colliders:
			if collider & (block_collider + pos):
				return

		self.set_block(pos, num)

	def draw(self):
		for chunk_position in self.chunks:
			self.chunks[chunk_position].draw()
