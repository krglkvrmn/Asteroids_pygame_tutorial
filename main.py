import pygame
import sys
import numpy as np
import math
import random
import time


BG_COLOR = (0, 0, 0)
SCREEN_SIZE = (1600, 900)


class Starship:
    original_image = pygame.image.load("starship.png")
    def __init__(self):
        self.image = self.original_image
        self.pos = np.array([SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2])
        self.speed = np.array([0., 0.])
        self.rect = self.image.get_rect(center=self.pos)

    def move(self):
        mouse_pos = pygame.mouse.get_pos()
        direction = mouse_pos - self.pos
        self.speed = direction / 70
        angle = self._calculate_angle(mouse_pos)
        self.image = pygame.transform.rotate(self.original_image, int(angle))
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos, width=44, height=35)
        self.rect.move(self.speed)

    def _calculate_angle(self, mouse_pos):
        rel_x, rel_y = mouse_pos - self.pos
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90
        return angle

    def check_collisions(self, asteroid_rects):
        hit = self.rect.collidelist(asteroids_rects)
        if hit != -1:
            return True
        return False




class Bullet:
    original_image = pygame.image.load("bullet.png")
    def __init__(self, pos, mouse_pos):
        self.pos = pos
        self.direction = (mouse_pos - pos)
        self.speed = self.direction / max(abs(self.direction)) * 6
        self.angle = self._calculate_angle(mouse_pos)
        self.rect = self.original_image.get_rect(center=self.pos)
        self.image = pygame.transform.rotate(self.original_image, int(self.angle))

    def move(self):
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos)
        self.rect.move(self.speed)

    def _calculate_angle(self, mouse_pos):
        rel_x, rel_y = mouse_pos - self.pos
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90
        return angle

    def check_collisions(self):
        if self.pos[0] > SCREEN_SIZE[0] or self.pos[1] > SCREEN_SIZE[1] or (self.pos < 0).any():
            return True
        else:
            return False


class Asteroid:
    images = [pygame.image.load("ast1.png"),
              pygame.image.load("ast2.png"),
              pygame.image.load("ast3.png"),
              pygame.image.load("ast4.png")]

    def __init__(self):
        self.image = random.choice(self.images)
        self.pos = next(random.choice([self._left_pos(),
                                       self._top_pos(),
                                       self._right_pos(),
                                       self._bottom_pos()]))
        self.rect = self.image.get_rect(center=self.pos)
        self.direction = (pygame.mouse.get_pos() - self.pos)
        self.speed = self.direction / 1000

    def move(self):
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos, width=40, height=40)
        self.rect.move(self.speed)

    def _left_pos(self):
        while True:
            yield np.array((random.uniform(-50, 0), random.uniform(0, SCREEN_SIZE[1])))

    def _right_pos(self):
        while True:
            yield np.array((random.uniform(SCREEN_SIZE[0], SCREEN_SIZE[0] + 50), random.uniform(0, SCREEN_SIZE[1])))

    def _top_pos(self):
        while True:
            yield np.array((random.uniform(0, SCREEN_SIZE[0]), random.uniform(-50, 0)))

    def _bottom_pos(self):
        while True:
            yield np.array((random.uniform(0, SCREEN_SIZE[0]), random.uniform(SCREEN_SIZE[1], SCREEN_SIZE[1] + 50)))

    def check_collisions(self):
        if self.pos[0] > (SCREEN_SIZE[0] + 50):
            self.pos[0] = 0
        elif (self.pos[0] + 50) < 0:
            self.pos[0] = SCREEN_SIZE[0]
        if (self.pos[1] - 50) > SCREEN_SIZE[1]:
            self.pos[1] = 0
        elif (self.pos[1] + 50) < 0:
            self.pos[1] = SCREEN_SIZE[1]
        self.rect = self.image.get_rect(center=self.pos)


def game_over(score):
    gameover_font = pygame.font.SysFont('Comic Sans MS', 126)
    text_font = pygame.font.SysFont('Comic Sans MS', 56)
    gameover_text = gameover_font.render('GAME OVER!', False, (255, 255, 255))
    info_text = text_font.render(f'Your score is {score}', False, (255, 255, 255))
    resume_text = text_font.render('Click to continue', False, (255, 255, 255))
    while True:
        screen.blit(gameover_text, (SCREEN_SIZE[0] / 3, SCREEN_SIZE[1] / 3))
        screen.blit(info_text, (SCREEN_SIZE[0] / 3 * 1.2, SCREEN_SIZE[1] / 3 * 2))
        screen.blit(resume_text, (SCREEN_SIZE[0] / 3 * 1.2, SCREEN_SIZE[1] / 3 * 2.2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                return


pygame.init()
pygame.font.init()
score_font = pygame.font.SysFont('Comic Sans MS', 30)
screen = pygame.display.set_mode(SCREEN_SIZE)
while True:
    starship = Starship()
    bullets = []
    asteroids = []
    pressed = False
    last_bullet_time = 0
    frame = 0
    score = 0
    while True:
        if frame % 25 == 0:
            new_asteroid = Asteroid()
            asteroids.append(new_asteroid)
        asteroids_rects = list(map(lambda x: x.rect, asteroids))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pressed = True
            if event.type == pygame.MOUSEBUTTONUP:
                pressed = False
        if pressed and (time.time() - last_bullet_time) > 0.25:
            try:
                bullets.append(Bullet(starship.pos.copy(), event.pos))  # Copy is important
                last_bullet_time = time.time()
            except AttributeError:
                pass


        starship.move()
        if starship.check_collisions(asteroids_rects):
            game_over(score)
            break

        for idx, bullet in enumerate(bullets):
            if bullet.check_collisions():
                del bullets[idx]
            else:
                hit = bullets[idx].rect.collidelist(asteroids_rects)
                if hit != -1:
                    del asteroids[hit]
                    del bullets[idx]
                    score += 1
                    continue
                bullets[idx].move()

        for idx, asteroid in enumerate(asteroids):
            asteroids[idx].check_collisions()
            asteroids[idx].move()

        score_text = score_font.render(f'Score: {score}', False, (255, 255, 255))

        screen.fill(BG_COLOR)
        screen.blits(map(lambda x: (x.image, x.rect), bullets))
        screen.blits(map(lambda x: (x.image, x.rect), asteroids))
        screen.blit(starship.image, starship.rect)
        screen.blit(score_text, (SCREEN_SIZE[0] - 150, 0))
        pygame.display.flip()
        frame += 1

