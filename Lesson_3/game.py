import sys
import time
import random
import os
import numpy as np
import pygame
import math


pygame.init()
BG_COLOR = (0, 0, 0)
screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
SCREEN_SIZE = screen.get_size()


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.starship = Starship()
        self.bullets = []
        self.asteroids = []
        self.boosters = []
        self.boosters_timeouts = {"Rapid_fire": 0, "Shield": 0, "Triple_bullets": 0}
        self.boosters_handlers = {"Rapid_fire": self.rapid_fire,
                                  "Shield": self.shield,
                                  "Triple_bullets": self.triple_bullets}
        self.color_picker = {Starship: (0, 255, 0), Bullet: (0, 0, 255), Asteroid: (255, 0, 0)}
        self.mouse_pressed = False
        self.fire_rate = 0.2
        self.max_bullets = 1

    def booster_manager(self, frame):
        boosters_rects = [booster.rect for booster in self.boosters]
        hit = self.starship.rect.collidelist(boosters_rects)
        if hit != -1:
            booster_type = self.boosters[hit].type
            if self.boosters_timeouts[booster_type] == 0:
                self.boosters_timeouts[booster_type] = time.time() + 10
                self.boosters_handlers[booster_type]("activate")
            elif self.boosters_timeouts[booster_type] > 0:
                self.boosters_timeouts[booster_type] += 10
            del self.boosters[hit]
            del boosters_rects[hit]
        for booster_type, timeout in self.boosters_timeouts.items():
            if time.time() > timeout > 0:
                self.boosters_timeouts[booster_type] = 0
                self.boosters_handlers[booster_type]("deactivate")
        if frame % 400 == 0 and frame != 0:
            self.boosters.append(Booster())

    def rapid_fire(self, mode):
        if mode == "activate":
            self.fire_rate /= 2
        elif mode == "deactivate":
            self.fire_rate *= 2

    def shield(self, mode):
        if mode == "activate":
            self.starship.original_image = pygame.image.load(os.path.join("images", "Starship_with_shield.png"))
        elif mode == "deactivate":
            self.starship.original_image = pygame.image.load(os.path.join("images", "starship.png"))

    def triple_bullets(self, mode):
        if mode == "activate":
            self.max_bullets = 3
        elif mode == "deactivate":
            self.max_bullets = 1

    def handle_events(self, frame):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_pressed = True
            if event.type == pygame.MOUSEBUTTONUP:
                self.mouse_pressed = False
        if self.mouse_pressed and (time.time() - self.starship.last_bullet_time) > self.fire_rate:
            new_bullets = self.starship.fire(self.max_bullets)
            self.bullets += new_bullets
        if frame % 50 == 0:
            self.cast_asteroid()

    def check_collisions(self):
        asteroids_rects = []
        for ast in self.asteroids:
            asteroids_rects.append(ast.rect)
        for idx, bullet in enumerate(self.bullets):
            if (bullet.pos[0] > SCREEN_SIZE[0] or bullet.pos[0] < 0 or bullet.pos[1] > SCREEN_SIZE[1] or bullet.pos[1] < 0):
                del self.bullets[idx]
            hit = bullet.rect.collidelist(asteroids_rects)
            if hit != -1:
                fragments = self.asteroids[hit].explode()
                self.asteroids += fragments
                del self.asteroids[hit]
                del asteroids_rects[hit]
                del self.bullets[idx]
        hit = self.starship.rect.collidelist(asteroids_rects)
        if hit != -1:
            if self.boosters_timeouts["Shield"] > 0:
                del self.asteroids[hit]
            else:
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
            self.booster_manager(frame)
            self.move_objects([[self.starship], self.bullets, self.asteroids])
            self.check_collisions()
            self.draw([self.boosters, [self.starship], self.bullets, self.asteroids], debug=False)
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

    def fire(self, bullet_num):
        self.last_bullet_time = time.time()
        new_bullets = []
        for i in range(bullet_num):
            if bullet_num == 1:
                angle_offset = 0
            else:
                angle_offset = -15 + 30 / (bullet_num - 1) * i
            new_bullets.append(Bullet(self.pos.copy(), angle_offset))
        return new_bullets


class Bullet:
    original_image = pygame.image.load(os.path.join("images", "bullet.png"))

    def __init__(self, pos, angle_offset=0):
        self.pos = pos
        mouse_pos = pygame.mouse.get_pos()
        self.direction = mouse_pos - self.pos
        direction_copy = self.direction.copy()
        angle_radians = math.pi / 180 * angle_offset
        self.direction[0] = direction_copy[0] * math.cos(angle_radians) - direction_copy[1] * math.sin(angle_radians)
        self.direction[1] = direction_copy[0] * math.sin(angle_radians) + direction_copy[1] * math.cos(angle_radians)
        self.speed = self.direction / max(abs(self.direction)) * 10
        self.angle = self.calculate_angle(mouse_pos) - angle_offset
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
    ast_variants = [("small", pygame.image.load(os.path.join("images", "ast1_small.png"))),
                    ("small", pygame.image.load(os.path.join("images", "ast2_small.png"))),
                    ("small", pygame.image.load(os.path.join("images", "ast3_small.png"))),
                    ("small", pygame.image.load(os.path.join("images", "ast4_small.png"))),
                    ("medium", pygame.image.load(os.path.join("images", "ast1_medium.png"))),
                    ("medium", pygame.image.load(os.path.join("images", "ast2_medium.png"))),
                    ("medium", pygame.image.load(os.path.join("images", "ast3_medium.png"))),
                    ("medium", pygame.image.load(os.path.join("images", "ast4_medium.png"))),
                    ("large", pygame.image.load(os.path.join("images", "ast1_large.png"))),
                    ("large", pygame.image.load(os.path.join("images", "ast2_large.png"))),
                    ("large", pygame.image.load(os.path.join("images", "ast3_large.png"))),
                    ("large", pygame.image.load(os.path.join("images", "ast4_large.png")))]

    def __init__(self, pos=None, speed=None, ast_type=None):
        if (pos is None) and (speed is None) and (ast_type is None):
            self.init_rand_asteroid()
        else:
            self.init_asteroid_fragment(pos, speed, ast_type)

    def init_rand_asteroid(self):
        self.pos = random.choice([self.left_pos, self.right_pos, self.top_pos, self.bottom_pos])()
        self.type, self.image = random.choice(self.ast_variants)
        self.rect = self.image.get_rect(center=self.pos)
        self.direction = pygame.mouse.get_pos() - self.pos
        self.speed = self.direction / 300

    def init_asteroid_fragment(self, pos, speed, ast_type):
        ast_variants = [variant for variant in self.ast_variants if variant[0] == ast_type]
        self.type, self.original_image = random.choice(ast_variants)
        self.pos = pos
        self.image = self.original_image
        self.rect = self.image.get_rect(center=self.pos)
        self.speed = speed

    def move(self):
        self.check_borders()
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

    def check_borders(self):
        if self.pos[0] > (SCREEN_SIZE[0] + 150):
            self.pos[0] = -150
        elif (self.pos[0] + 150) < 0:
            self.pos[0] = SCREEN_SIZE[0] + 150
        elif self.pos[1] > SCREEN_SIZE[1] + 150:
            self.pos[1] = -150
        elif (self.pos[1] + 150) < 0:
            self.pos[1] = SCREEN_SIZE[1] + 150

    def speed_offset(self):
        offset = self.speed / 2 + np.random.uniform(-0.5, 0.5, 2)
        return offset

    def pos_offset(self):
        offset = self.pos + np.random.uniform(-20, 20, 2)
        return offset

    def explode(self):
        fragments = []
        if self.type == "large":
            for _ in range(2):
                fragments.append(Asteroid(self.pos_offset(), self.speed_offset(), "medium"))
        elif self.type == "medium":
            for _ in range(3):
                fragments.append(Asteroid(self.pos_offset(), self.speed_offset(), "small"))
        elif self.type == "small":
            pass
        return fragments


class Booster:
    booster_types = {"Rapid_fire": pygame.image.load(os.path.join("images", "Rapid_fire.png")),
                     "Shield": pygame.image.load(os.path.join("images", "Shield.png")),
                     "Triple_bullets": pygame.image.load(os.path.join("images", "Triple_bullets.png"))}

    def __init__(self):
        self.type = random.choice(list(self.booster_types.keys()))
        self.pos = np.array([random.randint(100, SCREEN_SIZE[0] - 100), random.randint(100, SCREEN_SIZE[1] - 100)])
        self.image = self.booster_types[self.type]
        self.rect = self.image.get_rect(center=self.pos)


game = Game(screen)
game.run()

