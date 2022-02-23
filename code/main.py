import pygame, sys
from settings import *
from level import Level
from input import *

class Game:
	def __init__(self):

		# general setup
		pygame.init()
		self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
		pygame.display.set_caption('Zelda')
		self.clock = pygame.time.Clock()

		# input
		self.joystick = get_joystick()

		# level
		self.level = Level(self.joystick)

		# sound 
		main_sound = pygame.mixer.Sound('../audio/main.ogg')
		main_sound.set_volume(0.5)
		main_sound.play(loops = -1)

		self.pushable = True
		self.pushable_time = None
		self.pushable_duration = 500

	def cooldowns(self):
		current_time = pygame.time.get_ticks()
		if not self.pushable:
			if current_time - self.pushable_time >= self.pushable_duration:
				self.pushable = True

	def run(self):
		while True:
			up, down, left, right, attack_1, attack_2, switch_1, switch_2, menu = get_current_input(self.joystick)

			if menu and self.pushable:
				self.level.toggle_menu()
				self.pushable_time = pygame.time.get_ticks()
				self.pushable = False

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()

			self.screen.fill(WATER_COLOR)
			self.level.run()
			pygame.display.update()
			self.clock.tick(FPS)
			self.cooldowns()

if __name__ == '__main__':
	game = Game()
	game.run()
