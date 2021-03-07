import pygame
import sys
import os
from math import sin, cos
import numpy as np
import math
import random
import time


BG_COLOR = (0, 0, 0)
SCREEN_SIZE = (1600, 900)

if hasattr(sys, '_MEIPASS'):
    print(sys._MEIPASS)


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.bg_image = pygame.image.load(os.path.join("images", "background.png")).convert()
        self.starship = Starship(os.path.join("images", "starship.png"))
        self.bullets = []
        self.asteroids = []
        self.booster = None
        self.booster_handlers = {"Booster1": self.rapid_fire, "Shield": self.shield,
                                 "Triple_bullets": self.triple_bullets}
        self.booster_last_time = time.time()
        self.fire_rate = 0.20
        self.mouse_pressed = False
        self.score = 0
        self.score_font = pygame.font.SysFont('Comic Sans MS', 30)

    def handle_events(self, frame):
        if frame % 50 == 0:
            self.cast_asteroid()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_pressed = True
            if event.type == pygame.MOUSEBUTTONUP:
                self.mouse_pressed = False
        if self.mouse_pressed and (time.time() - self.starship.last_bullet_time) > self.fire_rate:
            if self.booster and self.booster.active and self.booster.type == "Triple_bullets":
                new_bullets = [self.starship.fire(angle_shift) for angle_shift in (10, 0, -10)]
                self.bullets.extend(new_bullets)
            else:
                new_bullet = self.starship.fire()
                self.bullets.append(new_bullet)

    def manage_boosters(self):
        if not self.booster and (time.time() >= self.booster_last_time + 2):
            self.cast_booster()
        if self.booster and not self.booster.active and self.starship.rect.colliderect(self.booster.rect):
            self.booster.activate()
            self.booster_handlers[self.booster.type]("activate")
        if self.booster and self.booster.active and (time.time() - self.booster.time_activated >= 10):
            self.booster_handlers[self.booster.type]("deactivate")
            self.booster = None
            self.booster_last_time = time.time()

    def draw(self, *args):
        self.screen.fill(BG_COLOR)
        # self.screen.blit(self.bg_image, (0, 0))
        for objects in args:
            self.screen.blits(map(lambda x: (x.image, x.rect), objects))
        score_text = self.score_font.render(f'Score: {self.score}', False, (255, 255, 255))
        self.screen.blit(score_text, (SCREEN_SIZE[0] - 150, 0))
        pygame.display.update()

    def move_objects(self, *args):
        for i, _ in enumerate(args):
            for k, _ in enumerate(args[i]):
                args[i][k].move()

    def cast_asteroid(self):
        new_asteroid = Asteroid()
        self.asteroids.append(new_asteroid)

    def cast_booster(self):
        new_booster = Booster(random.choice(list(self.booster_handlers.keys())))
        self.booster = new_booster

    def rapid_fire(self, mode):
        if mode == "activate":
            self.fire_rate /= 2
        elif mode == "deactivate":
            self.fire_rate *= 2

    def shield(self, mode):
        if mode == "activate":
            self.starship = Starship(os.path.join("images", "Starship_with_shield.png"), self.starship.pos)
        elif mode == "deactivate":
            self.starship = Starship(os.path.join("images", "starship.png"), self.starship.pos)

    def triple_bullets(self, mode):
        pass

    def check_collisions(self):
        # Starship vs Asteroids 
        asteroids_rects = list(map(lambda x: x.rect, self.asteroids))
        hit = self.starship.rect.collidelist(asteroids_rects)
        if self.booster and self.booster.active and self.booster.type == "Shield":
            if hit != -1:
                del self.asteroids[hit]
                self.score += 1
        else:
            if hit != -1:
                return True
        # Bullets vs Asteroids
        for idx, bullet in enumerate(self.bullets):
            hit = self.bullets[idx].rect.collidelist(asteroids_rects)
            if hit != -1:
                try:
                    fragments = self.asteroids[hit].explode()
                    del self.asteroids[hit]
                    self.asteroids.extend(fragments)
                    del self.bullets[idx]
                    self.score += 1
                except IndexError:
                    pass
            # Bullets out of the border
            if bullet.pos[0] > SCREEN_SIZE[0] or bullet.pos[1] > SCREEN_SIZE[1] or (bullet.pos < 0).any():
                del self.bullets[idx]
        # Asteroids out of borders
        for idx, _ in enumerate(self.asteroids):
            self.asteroids[idx].check_borders()


    def game_over(self):
        gameover_font = pygame.font.SysFont('Comic Sans MS', 126)
        text_font = pygame.font.SysFont('Comic Sans MS', 56)
        gameover_text = gameover_font.render('GAME OVER!', False, (255, 255, 255))
        info_text = text_font.render(f'Your score is {self.score}', False, (255, 255, 255))
        resume_text = text_font.render('Click to continue', False, (255, 255, 255))
        while True:
            self.screen.blit(gameover_text, (SCREEN_SIZE[0] / 3, SCREEN_SIZE[1] / 3))
            self.screen.blit(info_text, (SCREEN_SIZE[0] / 3 * 1.2, SCREEN_SIZE[1] / 3 * 2))
            self.screen.blit(resume_text, (SCREEN_SIZE[0] / 3 * 1.2, SCREEN_SIZE[1] / 3 * 2.2))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return

    def run(self):
        frame = 0
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            self.handle_events(frame)
            self.manage_boosters()
            self.move_objects([self.starship], self.bullets, self.asteroids)
            if self.booster and not self.booster.active:
                self.draw([self.booster], [self.starship], self.bullets, self.asteroids)
            else:
                self.draw([self.starship], self.bullets, self.asteroids)
            if self.check_collisions():
                self.game_over()
                return
            frame += 1


class Starship:
    def __init__(self, original_image=os.path.join("images", "starship.png"),
                       pos=np.array([SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2])):
        self.original_image = pygame.image.load(original_image)
        self.image = self.original_image
        self.pos = pos
        self.speed = np.array([0., 0.])
        self.rect = self.image.get_rect(center=self.pos)
        self.last_bullet_time = 0

    def move(self):
        mouse_pos = pygame.mouse.get_pos()
        direction = mouse_pos - self.pos
        self.speed = direction / 40
        angle = self._calculate_angle(mouse_pos)
        self.image = pygame.transform.rotate(self.original_image, int(angle))
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos, width=35, height=42)

    def _calculate_angle(self, mouse_pos):
        rel_x, rel_y = mouse_pos - self.pos
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90
        return angle

    def fire(self, angle_shift=0):
        self.last_bullet_time = time.time()
        return Bullet(self.pos.copy(), pygame.mouse.get_pos(), angle_shift)   # Copy is important


class Bullet:
    original_image = pygame.image.load(os.path.join("images", "bullet.png"))
    def __init__(self, pos, mouse_pos, angle_shift=0):
        self.pos = pos
        self.direction = (mouse_pos - pos)
        asr = math.pi / 180 * angle_shift
        self.direction[0] = self.direction[0] * cos(asr) - self.direction[1] * sin(asr)
        self.direction[1] = self.direction[0] * sin(asr) + self.direction[1] * cos(asr)
        self.speed = self.direction / max(abs(self.direction)) * 10
        self.angle = self._calculate_angle(mouse_pos) - angle_shift
        self.rect = self.original_image.get_rect(center=self.pos)
        self.image = pygame.transform.rotate(self.original_image, int(self.angle))

    def move(self):
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos)

    def _calculate_angle(self, mouse_pos):
        rel_x, rel_y = mouse_pos - self.pos
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90
        return angle


class Asteroid:
    variants = [("small", pygame.image.load(os.path.join("images", "ast1_small.png")), (10, 10)),
                ("small", pygame.image.load(os.path.join("images", "ast2_small.png")), (10, 10)),
                ("small", pygame.image.load(os.path.join("images", "ast3_small.png")), (10, 10)),
                ("small", pygame.image.load(os.path.join("images", "ast4_small.png")), (10, 10)),
                ("medium", pygame.image.load(os.path.join("images", "ast1_medium.png")), (40, 40)),
                ("medium", pygame.image.load(os.path.join("images", "ast2_medium.png")), (40, 40)),
                ("medium", pygame.image.load(os.path.join("images", "ast3_medium.png")), (40, 40)),
                ("medium", pygame.image.load(os.path.join("images", "ast4_medium.png")), (40, 40)),
                ("large", pygame.image.load(os.path.join("images", "ast1_large.png")), (105, 105)),
                ("large", pygame.image.load(os.path.join("images", "ast2_large.png")), (105, 105)),
                ("large", pygame.image.load(os.path.join("images", "ast3_large.png")), (105, 105)),
                ("large", pygame.image.load(os.path.join("images", "ast4_large.png")), (105, 105))]

    def __init__(self, pos="random", direction="player", ast_type="random"):
        if ast_type == "random":
            self.type, self.image, self.hitbox = random.choice(self.variants)
        else:
            self.type, self.image, self.hitbox = random.choice(list(filter(lambda x: x[0] == ast_type, self.variants)))
        if pos == "random":
            self.pos = random.choice([self._left_pos, self._top_pos,
                                      self._right_pos, self._bottom_pos])()
        else:
            self.pos = pos
        self.w, self.h = self.hitbox
        self.rect = self.image.get_rect(center=self.pos)
        if direction == "player":
            self.direction = (pygame.mouse.get_pos() - self.pos)
            self.speed = self.direction / 300
        else:
            self.speed = direction

    def move(self):
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)

    def check_borders(self):
        if self.pos[0] > (SCREEN_SIZE[0] + 50):
            self.pos[0] = 0
        elif (self.pos[0] + 50) < 0:
            self.pos[0] = SCREEN_SIZE[0]
        if (self.pos[1] - 50) > SCREEN_SIZE[1]:
            self.pos[1] = 0
        elif (self.pos[1] + 50) < 0:
            self.pos[1] = SCREEN_SIZE[1]
        self.rect = self.image.get_rect(center=self.pos)

    def _left_pos(self):
        return np.array((random.uniform(-50, 0),
                        random.uniform(0, SCREEN_SIZE[1])))

    def _right_pos(self):
        return np.array((random.uniform(SCREEN_SIZE[0], SCREEN_SIZE[0] + 50),
                        random.uniform(0, SCREEN_SIZE[1])))

    def _top_pos(self):
        return np.array((random.uniform(0, SCREEN_SIZE[0]),
                        random.uniform(-50, 0)))

    def _bottom_pos(self):
        return np.array((random.uniform(0, SCREEN_SIZE[0]),
                        random.uniform(SCREEN_SIZE[1], SCREEN_SIZE[1] + 50)))

    def _speed_offset(self):
        offset = self.speed * 0.5 + np.random.uniform(-0.5, 0.5, 2)
        return offset

    def _pos_offset(self):
        offset = self.pos + np.random.uniform(-10, 10, 2)
        return offset

    def explode(self):
        if self.type == "large":
            return [Asteroid(self._pos_offset(), self._speed_offset(), "medium") for _ in range(2)]
        if self.type == "medium":
            return [Asteroid(self._pos_offset(), self._speed_offset(), "small") for _ in range(3)]
        if self.type == "small":
            return []

class Booster:
    def __init__(self, boost_type):
        self.type = boost_type
        self.image = pygame.image.load(os.path.join("images", boost_type + ".png"))
        self.pos = np.array([random.randint(100, SCREEN_SIZE[0] - 100),
                             random.randint(100, SCREEN_SIZE[1] - 100)])
        self.rect = self.image.get_rect(center=self.pos)
        self.active = False
        self.time_activated = None

    def activate(self):
        self.active = True
        self.time_activated = time.time()


pygame.init()
pygame.font.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
while True:
    game = Game(screen)
    game.run()
