import sys
import os
import numpy as np
import pygame
import math


pygame.init()
BG_COLOR = (0, 0, 0)
screen = pygame.display.set_mode((600, 500), pygame.RESIZABLE)
SCREEN_SIZE = screen.get_size()


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.starship = Starship()
        self.bullets = []
        self.asteroids = []

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

    def move_objects(self, objects_list):
        for objects in objects_list:
            for obj in objects:
                obj.move()

    def draw(self, objects_list, debug=False):
        screen.fill(BG_COLOR)
        for objects in objects_list:
            for obj in objects:
                screen.blit(obj.image, obj.rect)
        if debug:
            for objects in objects_list:
                for obj in objects:
                    pygame.draw.rect(self.screen, (0, 255, 0), obj.rect, 2)
        pygame.display.update()

    def run(self):
        while True:
            self.handle_events()
            self.move_objects([[self.starship]])
            self.draw([[self.starship]], debug=True)


class Starship:
    def __init__(self):
        self.pos = np.array([SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2])
        self.original_image = pygame.image.load(os.path.join("images", "starship.png"))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=self.pos)

    def move(self):
        mouse_pos = pygame.mouse.get_pos()
        direction = mouse_pos - self.pos
        angle = self.calculate_angle(mouse_pos)
        self.speed = direction / 40
        self.pos += self.speed
        self.image = pygame.transform.rotate(self.original_image, int(angle))
        self.rect = self.image.get_rect(center=self.pos)

    def calculate_angle(self, mouse_pos):
        rel_x, rel_y = mouse_pos - self.pos
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90
        return angle


game = Game(screen)
game.run()

