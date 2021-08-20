import sys
import time
import random
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
        self.color_picker = {Starship: (0, 255, 0), Bullet: (0, 0, 255), Asteroid: (255, 0, 0)}
        self.mouse_pressed = False
        self.fire_rate = 0.2

    def handle_events(self, frame):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_pressed = True
            if event.type == pygame.MOUSEBUTTONUP:
                self.mouse_pressed = False
        if self.mouse_pressed and (time.time() - self.starship.last_bullet_time) > self.fire_rate:
            new_bullet = self.starship.fire()
            self.bullets.append(new_bullet)
        if frame % 50 == 0:
            self.cast_asteroid()


    def check_collisions(self):
        for idx, bullet in enumerate(self.bullets):
            if (bullet.pos[0] > SCREEN_SIZE[0] or bullet.pos[0] < 0 or bullet.pos[1] > SCREEN_SIZE[1] or bullet.pos[1] < 0):
                del self.bullets[idx]

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
                    color = self.color_picker[type(obj)]
                    pygame.draw.rect(self.screen, color, obj.rect, 2)
        pygame.display.update()

    def cast_asteroid(self):
        self.asteroids.append(Asteroid())

    def run(self):
        clock = pygame.time.Clock()
        frame = 0
        while True:
            clock.tick(60)
            self.handle_events(frame)
            self.move_objects([[self.starship], self.bullets, self.asteroids])
            self.check_collisions()
            self.draw([[self.starship], self.bullets, self.asteroids], debug=True)
            frame += 1


class Starship:
    def __init__(self):
        self.pos = np.array([SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2])
        self.original_image = pygame.image.load(os.path.join("images", "starship.png"))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=self.pos)
        self.last_bullet_time = 0

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

    def fire(self):
        self.last_bullet_time = time.time()
        return Bullet(self.pos.copy())


class Bullet:
    original_image = pygame.image.load(os.path.join("images", "bullet.png"))

    def __init__(self, pos):
        self.pos = pos
        mouse_pos = pygame.mouse.get_pos()
        self.direction = mouse_pos - self.pos
        self.speed = self.direction / max(abs(self.direction)) * 10
        self.angle = self.calculate_angle(mouse_pos)
        self.image = pygame.transform.rotate(self.original_image, int(self.angle))
        self.rect = self.image.get_rect(center=self.pos)

    def move(self):
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos)

    def calculate_angle(self, mouse_pos):
        rel_x, rel_y = mouse_pos - self.pos
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90
        return angle


class Asteroid:
    original_images = [pygame.image.load(os.path.join("images", "ast1_medium.png")),
                       pygame.image.load(os.path.join("images", "ast2_medium.png")),
                       pygame.image.load(os.path.join("images", "ast3_medium.png")),
                       pygame.image.load(os.path.join("images", "ast4_medium.png"))]

    def __init__(self):
        self.pos = random.choice([self.left_pos, self.right_pos, self.top_pos, self.bottom_pos])()
        self.image = random.choice(self.original_images)
        self.rect = self.image.get_rect(center=self.pos)
        self.direction = pygame.mouse.get_pos() - self.pos
        self.speed = self.direction / 300

    def move(self):
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos)

    def left_pos(self):
        return np.array([-150, random.uniform(0, SCREEN_SIZE[1])])

    def right_pos(self):
        return np.array([SCREEN_SIZE[0] + 150, random.uniform(0, SCREEN_SIZE[1])])

    def top_pos(self):
        return np.array([random.uniform(0, SCREEN_SIZE[0]), -150])

    def bottom_pos(self):
        return np.array([random.uniform(0, SCREEN_SIZE[0]), SCREEN_SIZE[1] + 150])


game = Game(screen)
game.run()

