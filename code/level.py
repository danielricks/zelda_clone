import pygame 
from settings import *
from tile import Tile
from player import Player
from debug import debug
from support import *
from random import choice, randint
from weapon import Weapon
from ui import UI
from enemy import Enemy
from particles import AnimationPlayer
from magic import MagicPlayer
from upgrade import Upgrade
from input import *

import numpy as np
from math import floor

from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement

class Level:
	def __init__(self, joystick):

		# get the display surface 
		self.display_surface = pygame.display.get_surface()
		self.game_paused = False

		# sprite group setup
		self.visible_sprites = YSortCameraGroup()
		self.obstacle_sprites = pygame.sprite.Group()

		# attack sprites
		self.current_attack = None
		self.attack_sprites = pygame.sprite.Group()
		self.attackable_sprites = pygame.sprite.Group()

		# input
		self.joystick = joystick

		# sprite setup
		self.create_map()

		# user interface 
		self.ui = UI()
		self.upgrade = Upgrade(self.player, self.joystick)

		# particles
		self.animation_player = AnimationPlayer()
		self.magic_player = MagicPlayer(self.animation_player)

	def create_map(self):
		layouts = {
			'boundary': import_csv_layout('../map/map_FloorBlocks.csv'),
			'grass': import_csv_layout('../map/map_Grass.csv'),
			'object': import_csv_layout('../map/map_Objects.csv'),
			'entities': import_csv_layout('../map/map_Entities.csv')
		}
		graphics = {
			'grass': import_folder('../graphics/grass'),
			'objects': import_folder('../graphics/objects')
		}

		# create pathfinding matrix
		boundary = np.array([[int(num) for num in line] for line in layouts['boundary']])
		grass = np.array([[int(num) for num in line] for line in layouts['grass']])
		objects = np.array([[int(num) for num in line] for line in layouts['object']])
		pathfinding_matrix = np.add(boundary, grass)
		pathfinding_matrix = np.add(pathfinding_matrix, objects)
		self.pathfinding_matrix = np.ma.masked_greater(pathfinding_matrix < 0, pathfinding_matrix).mask.tolist()

		for style, layout in layouts.items():
			for row_index, row in enumerate(layout):
				for col_index, col in enumerate(row):
					if col != '-1':
						x = col_index * TILESIZE
						y = row_index * TILESIZE
						if style == 'boundary':
							Tile((x, y), [self.obstacle_sprites], 'invisible')
						if style == 'grass':
							random_grass_image = choice(graphics['grass'])
							Tile(
								(x, y),
								[self.visible_sprites, self.obstacle_sprites, self.attackable_sprites],
								'grass',
								random_grass_image)

						if style == 'object':
							surf = graphics['objects'][int(col)]
							Tile((x, y), [self.visible_sprites, self.obstacle_sprites], 'object', surf)
							self.add_object_to_pathfinding((x, y))

						if style == 'entities':
							if col == '394':
								self.player = Player(
									(x, y),
									[self.visible_sprites],
									self.obstacle_sprites,
									self.joystick,
									self.create_attack,
									self.destroy_attack,
									self.create_magic)
							else:
								if col == '390': monster_name = 'bamboo'
								elif col == '391': monster_name = 'spirit'
								elif col == '392': monster_name = 'raccoon'
								else:
									monster_name = 'squid'
								Enemy(
									monster_name,
									(x, y),
									[self.visible_sprites, self.attackable_sprites],
									self.obstacle_sprites,
									self.damage_player,
									self.trigger_death_particles,
									self.add_exp,
									self.find_path)

		self.grid = Grid(matrix = self.pathfinding_matrix)
		self.finder = AStarFinder(diagonal_movement = DiagonalMovement.only_when_no_obstacle)

	def create_attack(self):
		self.current_attack = Weapon(self.player, [self.visible_sprites, self.attack_sprites])

	def create_magic(self, style, strength, cost, magic_sound):
		if style == 'heal':
			self.magic_player.heal(self.player, strength, cost, magic_sound, [self.visible_sprites])

		if style == 'flame':
			self.magic_player.flame(self.player, cost, magic_sound, [self.visible_sprites, self.attack_sprites])

	def destroy_attack(self):
		if self.current_attack:
			self.current_attack.kill()
		self.current_attack = None

	def player_attack_logic(self):
		if self.attack_sprites:
			for attack_sprite in self.attack_sprites:
				collision_sprites = pygame.sprite.spritecollide(attack_sprite, self.attackable_sprites, False)
				if collision_sprites:
					for target_sprite in collision_sprites:
						if target_sprite.sprite_type == 'grass':
							pos = target_sprite.rect.topleft
							offset = pygame.math.Vector2(0, 75)
							for leaf in range(randint(3,6)):
								self.animation_player.create_grass_particles(pos - offset, [self.visible_sprites])
							target_sprite.kill()
							self.remove_from_pathfinding(pos)
						else:
							target_sprite.get_damage(self.player, attack_sprite.sprite_type)

	def damage_player(self, amount, attack_type):
		if self.player.vulnerable:
			self.player.health -= amount
			self.player.vulnerable = False
			self.player.hurt_time = pygame.time.get_ticks()
			self.animation_player.create_particles(attack_type, self.player.rect.center, [self.visible_sprites])

	def trigger_death_particles(self, pos, particle_type):
		self.animation_player.create_particles(particle_type, pos, self.visible_sprites)

	def add_exp(self, amount):
		self.player.exp += amount

	def toggle_menu(self):
		self.game_paused = not self.game_paused

	def convert_to_matrix_coordinates(self, coord):
		return floor(coord / TILESIZE)
	
	def convert_back_to_world_coordinates(self, coord):
		return coord * TILESIZE

	def get_from_pathfinding_matrix(self, pos):
		return self.pathfinding_matrix[pos[1], pos[0]]
	
	def set_pathfinding_matrix(self, pos, boolean):
		self.pathfinding_matrix[pos[1]][pos[0]] = boolean

	def find_path(self, start, end):
		print('requesting path', start, end, pygame.time.get_ticks())
		start = self.grid.node(self.convert_to_matrix_coordinates(start[0]), self.convert_to_matrix_coordinates(start[1]))
		end = self.grid.node(self.convert_to_matrix_coordinates(end[0]), self.convert_to_matrix_coordinates(end[1]))
		path, _ = self.finder.find_path(start, end, self.grid)
		self.grid.cleanup()
		return [(self.convert_back_to_world_coordinates(x) + 32, self.convert_back_to_world_coordinates(y) + 32) for (x, y) in path]
	
	def add_object_to_pathfinding(self, pos):
		# add to position in matrix
		x = self.convert_to_matrix_coordinates(pos[0])
		y = self.convert_to_matrix_coordinates(pos[1])
		if x < len(self.pathfinding_matrix) - 1 and y < len(self.pathfinding_matrix[0]) - 1 and x > 1 and y > 1:
			self.set_pathfinding_matrix((x+1, y), False) # one right

	def remove_from_pathfinding(self, pos):
		# remove from position in matrix
		x = self.convert_to_matrix_coordinates(pos[0])
		y = self.convert_to_matrix_coordinates(pos[1])
		self.set_pathfinding_matrix((x, y), True)
		# update grid and finder
		self.grid = Grid(matrix = self.pathfinding_matrix)
		self.finder = AStarFinder(diagonal_movement = DiagonalMovement.only_when_no_obstacle)

	def run(self):
		self.visible_sprites.custom_draw(self.player)
		self.ui.display(self.player)
		
		if self.game_paused:
			self.upgrade.display()
		else:
			self.visible_sprites.update()
			self.visible_sprites.enemy_update(self.player)
			self.player_attack_logic()

class YSortCameraGroup(pygame.sprite.Group):
	def __init__(self):

		# general setup 
		super().__init__()
		self.display_surface = pygame.display.get_surface()
		self.half_width = self.display_surface.get_size()[0] // 2
		self.half_height = self.display_surface.get_size()[1] // 2
		self.offset = pygame.math.Vector2()

		# creating the floor
		self.floor_surf = pygame.image.load('../graphics/tilemap/ground.png').convert()
		self.floor_rect = self.floor_surf.get_rect(topleft = (0,0))

	def custom_draw(self, player):

		# getting the offset 
		self.offset.x = player.rect.centerx - self.half_width
		self.offset.y = player.rect.centery - self.half_height

		# drawing the floor
		floor_offset_pos = self.floor_rect.topleft - self.offset
		self.display_surface.blit(self.floor_surf, floor_offset_pos)

		# for sprite in self.sprites():
		for sprite in sorted(self.sprites(),key = lambda sprite: sprite.rect.centery):
			offset_pos = sprite.rect.topleft - self.offset
			self.display_surface.blit(sprite.image, offset_pos)

	def enemy_update(self, player):
		enemy_sprites = [sprite for sprite in self.sprites() if hasattr(sprite,'sprite_type') and sprite.sprite_type == 'enemy']
		for enemy in enemy_sprites:
			enemy.enemy_update(player)

			show_pathfinding = True
			if show_pathfinding:
				if enemy.has_path:
					if len(enemy.path) > 1:
						new_points = []
						for point_pair in enemy.path:
							new_points.append(point_pair - self.offset)
						pygame.draw.lines(self.display_surface, 'red', False, new_points, 5)
