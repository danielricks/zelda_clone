import pygame
from settings import *
from entity import Entity
from support import *

class Enemy(Entity):
	def __init__(self, monster_name, pos, groups, obstacle_sprites, damage_target, trigger_death_particles, add_exp, find_path):

		# general setup
		super().__init__(groups)
		self.sprite_type = 'enemy'

		# graphics setup
		self.import_graphics(monster_name)
		self.status = 'idle'
		self.image = self.animations[self.status][self.frame_index]

		# movement
		self.rect = self.image.get_rect(topleft = pos)
		self.hitbox = self.rect.inflate(HITBOX_OFFSET['enemy']['x'], HITBOX_OFFSET['enemy']['y'])
		self.obstacle_sprites = obstacle_sprites

		# stats
		self.monster_name = monster_name
		monster_info = monster_data[self.monster_name]
		self.health = monster_info['health']
		self.exp = monster_info['exp']
		self.speed = monster_info['speed']
		self.attack_damage = monster_info['damage']
		self.resistance = monster_info['resistance']
		self.attack_radius = monster_info['attack_radius']
		self.notice_radius = monster_info['notice_radius']
		self.attack_type = monster_info['attack_type']

		# target interaction
		self.can_attack = True
		self.attack_time = None
		self.attack_cooldown = 400
		self.damage_target = damage_target
		self.trigger_death_particles = trigger_death_particles
		self.add_exp = add_exp

		# invincibility timer
		self.vulnerable = True
		self.hit_time = None
		self.invincibility_duration = 300

		# sounds
		self.death_sound = pygame.mixer.Sound('../audio/death.wav')
		self.hit_sound = pygame.mixer.Sound('../audio/hit.wav')
		self.attack_sound = pygame.mixer.Sound(monster_info['attack_sound'])
		self.death_sound.set_volume(0.6)
		self.hit_sound.set_volume(0.6)
		self.attack_sound.set_volume(0.6)

		# pathfinding
		self.find_path = find_path
		self.has_path = False
		self.pathfinding_time = pygame.time.get_ticks()
		self.pathfinding_cooldown = 500
		self.path_index = 0
		self.waypoint = None

	def import_graphics(self, name):
		self.animations = {'idle':[],'move':[],'attack':[]}
		main_path = f'../graphics/monsters/{name}/'
		for animation in self.animations.keys():
			self.animations[animation] = import_folder(main_path + animation)
	
	def find_new_path(self, start, end):
		return self.find_path(start, end)

	def get_target_distance_direction(self, target):
		enemy_vec = pygame.math.Vector2(self.rect.center)
		target_vec = pygame.math.Vector2(target.rect.center)

		distance = (target_vec - enemy_vec).magnitude()

		if distance > 0:
			direction = (target_vec - enemy_vec).normalize()
		else:
			direction = pygame.math.Vector2()

		return (distance, direction, enemy_vec, target_vec)
	
	def get_waypoint_distance_direction(self, target_vec):
		enemy_vec = pygame.math.Vector2(self.rect.center)

		distance = (target_vec - enemy_vec).magnitude()

		if distance > 0:
			direction = (target_vec - enemy_vec).normalize()
		else:
			direction = pygame.math.Vector2()

		return (distance, direction, enemy_vec, target_vec)
	
	def follow_path(self, enemy_vec, waypoint_vec):
		if self.path_index < len(self.path) - 1:
			distance = (enemy_vec - waypoint_vec).magnitude()
			if distance <= TILESIZE / 2:
				self.waypoint = pygame.math.Vector2(self.path[self.path_index])
				self.path_index += 1

	def get_status(self, target):
		target_distance, _, enemy_vec, target_vec = self.get_target_distance_direction(target)

		if target_distance <= self.attack_radius and self.can_attack:
			if self.status != 'attack':
				self.frame_index = 0
			self.status = 'attack'
		elif target_distance <= self.notice_radius:
			self.status = 'move'
			if target_distance > self.attack_radius:
				if not self.has_path:
					self.pathfinding_time = pygame.time.get_ticks()
					self.path = self.find_new_path(enemy_vec, target_vec)
					print('returned', self.path)
					self.has_path = True
					self.path_index = 1
					
					if len(self.path) > 1:
						self.waypoint = self.path[self.path_index]
					elif len(self.path) == 1:
						self.waypoint = self.path[0]
					else:
						self.waypoint = None

				if self.has_path:
					if self.waypoint:
						distance, _, __, waypoint_vec = self.get_waypoint_distance_direction(pygame.math.Vector2(self.waypoint))
						self.follow_path(enemy_vec, waypoint_vec)
		else:
			self.status = 'idle'

	def actions(self, target):
		if self.status == 'attack':
			self.attack_time = pygame.time.get_ticks()
			self.damage_target(self.attack_damage, self.attack_type)
			self.attack_sound.play()
			self.waypoint = None
		elif self.status == 'move':
			if self.waypoint:
				self.direction = self.get_waypoint_distance_direction(pygame.math.Vector2(self.waypoint))[1]
			else:
				self.direction = self.get_target_distance_direction(target)[1]
		else:
			self.direction = pygame.math.Vector2()

	def animate(self):
		animation = self.animations[self.status]
		
		self.frame_index += self.animation_speed
		if self.frame_index >= len(animation):
			if self.status == 'attack':
				self.can_attack = False
			self.frame_index = 0

		self.image = animation[int(self.frame_index)]
		self.rect = self.image.get_rect(center = self.hitbox.center)

		if not self.vulnerable:
			alpha = self.wave_value()
			self.image.set_alpha(alpha)
		else:
			self.image.set_alpha(255)

	def cooldowns(self):
		current_time = pygame.time.get_ticks()
		if not self.can_attack:
			if current_time - self.attack_time >= self.attack_cooldown:
				self.can_attack = True

		if not self.vulnerable:
			if current_time - self.hit_time >= self.invincibility_duration:
				self.vulnerable = True
		
		if self.has_path:
			if current_time - self.pathfinding_time >= self.pathfinding_cooldown:
				self.has_path = False

	def get_damage(self, target, attack_type):
		if self.vulnerable:
			self.hit_sound.play()
			self.direction = self.get_target_distance_direction(target)[1]
			if attack_type == 'weapon':
				self.health -= target.get_full_weapon_damage()
			else:
				self.health -= target.get_full_magic_damage()
			self.hit_time = pygame.time.get_ticks()
			self.vulnerable = False

	def check_death(self):
		if self.health <= 0:
			self.kill()
			self.trigger_death_particles(self.rect.center, self.monster_name)
			self.add_exp(self.exp)
			self.death_sound.play()

	def hit_reaction(self):
		if not self.vulnerable:
			self.direction *= -self.resistance

	def update(self):
		self.hit_reaction()
		self.move(self.speed)
		self.animate()
		self.cooldowns()
		self.check_death()

	def enemy_update(self, target):
		self.get_status(target)
		self.actions(target)