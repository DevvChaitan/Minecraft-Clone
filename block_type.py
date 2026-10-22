import collider

import models.cube


class Block_type:
	def __init__(self, texture_manager, name="unknown", block_face_textures={"all": "cobblestone"}, model=models.cube):
		self.name = name
		self.block_face_textures = block_face_textures
		self.model = model

		self.transparent = model.transparent
		self.is_cube = model.is_cube
		self.glass = model.glass

		self.colliders = []
		for _collider in model.colliders:
			self.colliders.append(collider.Collider(*_collider))

		self.vertex_positions = model.vertex_positions
		self.tex_coords = model.tex_coords.copy()
		self.shading_values = model.shading_values

		def set_block_face(face, texture):
			if face > len(self.tex_coords) - 1:
				return

			self.tex_coords[face] = self.tex_coords[face].copy()

			for vertex in range(4):
				self.tex_coords[face][vertex * 3 + 2] = texture

			# If two-sided (like liquid with 12 faces), also assign matching inward face
			if len(self.tex_coords) == 12 and face < 6:
				inward_face = face + 6
				self.tex_coords[inward_face] = self.tex_coords[inward_face].copy()
				for vertex in range(4):
					self.tex_coords[inward_face][vertex * 3 + 2] = texture

		for face in block_face_textures:
			texture = block_face_textures[face]
			texture_manager.add_texture(texture)

			texture_index = texture_manager.textures.index(texture)

			if face == "all":
				for i in range(len(self.tex_coords)):
					set_block_face(i, texture_index)

			elif face == "sides":
				set_block_face(0, texture_index)
				set_block_face(1, texture_index)
				set_block_face(4, texture_index)
				set_block_face(5, texture_index)

			elif face == "x":
				set_block_face(0, texture_index)
				set_block_face(1, texture_index)

			elif face == "y":
				set_block_face(2, texture_index)
				set_block_face(3, texture_index)

			elif face == "z":
				set_block_face(4, texture_index)
				set_block_face(5, texture_index)

			else:
				faces_list = ["right", "left", "top", "bottom", "front", "back"]
				if face in faces_list:
					set_block_face(faces_list.index(face), texture_index)
