import math  # Модуль math будет полезен для вычисления угла наклона звездолёта
import os  # Модуль os нужен для работы с путями и файлами
import random  # Модуль random нужен для генерации случайных чисел
import sys  # Модуль sys понадобится нам для закрытия игры
import time  # Модуль time нужен для замера времени
from dataclasses import dataclass
from itertools import cycle
from typing import Tuple, List

import numpy as np  # Модуль numpy нужен для поэлементного сложения векторов
import pygame  # Модуль pygame для реализации игровой логики
from pygame.sprite import RenderPlain, Sprite, spritecollide, collide_mask

from config import *  # Настройки для большинства игровых механик

# Инициализация модуля pygame
pygame.init()
pygame.mixer.init()
# Цвет фона в формате RGB (красный, синий, зелёный). (0, 0, 0) - чёрный цвет.
BG_COLOR = (0, 0, 0)
# Объект дисплея (0, 0) - полный экран, если задать (800, 600), то окно будет размером 800х600 пикселей
screen = pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
# Получим ширину и высоту игрового поля из объекта screen и сохраним в глобальную переменную.
# Мы будем использовать SCREEN_SIZE очень часто!
SCREEN_SIZE = screen.get_size()


@dataclass
class Weapon:
    type: str
    ammo: float
    fire_rate: float


@dataclass
class Ability:
    type: str
    amount: float
    active: bool
    sound: pygame.mixer.Sound


class GUI:
    interface_pictures = {"Normal_bullets": pygame.transform.rotate(
        pygame.image.load(os.path.join("images", "bullet.png")), 90),
        "Explosive_bullets": pygame.transform.rotate(
            pygame.image.load(os.path.join("images", "powered_bullet.png")), 90)}

    def __init__(self, screen, starship):
        self.screen = screen
        self.starship = starship
        self.score = 0
        self.weapons = None
        self.weapon_type = None
        self.timed_abilities = None
        self.score_font = pygame.font.SysFont('Comic Sans MS', 30)
        self.gameover_font = pygame.font.SysFont('Comic Sans MS', 126)
        self.text_font = pygame.font.SysFont('Comic Sans MS', 56)
        self.score_position = np.array((SCREEN_SIZE[0] - 150, 0))
        self.abilities_position = np.array((5, SCREEN_SIZE[1] / 2))
        self.abilities_v_offset = np.array((0, 35))
        self.weapon_panel_position = np.array((5, SCREEN_SIZE[1] / 4))
        self.weapons_v_offset = np.array((0, 35))
        self.switch_weapon_hint_timeout = 160
        self.switch_weapon_hint_active = False
        self.stasis_hint_timeout = 160
        self.stasis_hint_active = False

    def update(self, score, weapon_type, weapons, timed_abilities):
        self.score = score
        self.weapon_type = weapon_type
        self.weapons = weapons
        self.timed_abilities = timed_abilities
        self.draw()

    def draw(self):
        self.draw_score()
        self.draw_weapons()
        self.draw_abilities()
        self.draw_hints()

    def draw_score(self):
        score_text = self.score_font.render(f'Score: {self.score}', False, (255, 255, 255))
        self.screen.blit(score_text, self.score_position)

    def draw_weapons(self):
        vertical_offset = 1
        for weapon in self.weapons:
            active_offset = np.array((0, 0))
            horizontal_offset = np.array((self.interface_pictures[weapon].get_size()[0] + 10, 0))
            if weapon == self.weapon_type:
                active_offset[0] = 20
            abs_voff = vertical_offset * self.weapons_v_offset
            image_coords = self.weapon_panel_position + abs_voff + active_offset
            self.screen.blit(self.interface_pictures[weapon], image_coords)
            ammo = "Infinite" if (ammo := self.weapons[weapon].ammo) == float("inf") else str(ammo)
            ammo_text = self.score_font.render(ammo, False, (255, 255, 255))
            text_coords = self.weapon_panel_position + abs_voff + active_offset + horizontal_offset
            self.screen.blit(ammo_text, text_coords)
            vertical_offset += 1

    def draw_abilities(self):
        text = self.score_font.render(f'Stasis: {self.timed_abilities["Stasis"].amount:.0f}', False, (255, 255, 255))
        self.screen.blit(text, self.abilities_position)

    def draw_hints(self):
        if self.switch_weapon_hint_active and self.switch_weapon_hint_timeout:
            text = self.score_font.render(f'Нажмите "Пробел" для смены оружия', False, (255, 255, 255))
            self.screen.blit(text, self.starship.rect.topright)
            self.switch_weapon_hint_timeout -= 1
        if self.stasis_hint_active and self.stasis_hint_timeout:
            text = self.score_font.render(f'Зажмите "s" для активации стазиса', False, (255, 255, 255))
            self.screen.blit(text, self.starship.rect.topright)
            self.stasis_hint_timeout -= 1

    def activate_stasis_hint(self):
        self.stasis_hint_active = True

    def activate_weapon_switch_hint(self):
        self.switch_weapon_hint_active = True

    def game_over(self):
        gameover_text = self.gameover_font.render('GAME OVER!', False, (255, 255, 255))
        info_text = self.text_font.render(f'Your score is {self.score}', False, (255, 255, 255))
        resume_text = self.text_font.render('Click to continue', False, (255, 255, 255))
        while True:
            self.screen.blit(gameover_text, (SCREEN_SIZE[0] / 3.5, SCREEN_SIZE[1] / 3.5))
            self.screen.blit(info_text, (SCREEN_SIZE[0] / 3.5 * 1.2, SCREEN_SIZE[1] / 3.5 * 2))
            self.screen.blit(resume_text, (SCREEN_SIZE[0] / 3.5 * 1.2, SCREEN_SIZE[1] / 3.5 * 2.2))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return


class Game:
    """Основной класс игры. В нём представлены основные методы для управления игровыми объектами, а также сами
    объекты """

    def __init__(self, screen):
        self.screen = screen
        self.starship = Starship()  # Объект класса Starship (игрок)
        self.enemies = RenderPlain()
        self.bullets = RenderPlain()  # Хранение объектов пуль (Bullet)
        self.enemy_bullets = RenderPlain()
        self.asteroids = RenderPlain()  # Заготовка для хранения объектов астероидов
        self.boosters = RenderPlain()  # Список буcтеров для отрисовки
        self.explosions = RenderPlain()
        self.gui = GUI(screen, self.starship)
        self.boosters_timeouts = {"Rapid_fire": 0,
                                  "Shield": 0,
                                  "Triple_bullets": 0,
                                  "Health": 0}
        self.booster_handlers = {"Rapid_fire": self.rapid_fire,
                                 "Shield": self.shield,
                                 "Triple_bullets": self.triple_bullets,
                                 "Explosive_bullets": self.explosive_bullets,
                                 "Health": self.health,
                                 "Stasis": self.stasis}
        self.weapons = {"Normal_bullets": Weapon("normal", float("inf"), 0.2),
                        "Explosive_bullets": Weapon("explosive", 0, 0.5)}
        self.weapon_selector = cycle(self.weapons.keys())
        self.weapon_type = next(self.weapon_selector)
        self.weapon_switch_sound = pygame.mixer.Sound(os.path.join("sounds", "weapon_switch.wav"))
        self.timed_abilities = {"Stasis": Ability("Stasis", 0, False,
                                                  pygame.mixer.Sound(os.path.join("sounds", "clock_ticks_1.wav")))}
        self.mouse_pressed = False  # Cохраняет состояние кнопки мыши
        self.fire_rate = FIRE_RATE  # Пауза между выстрелами (в секундах)
        self.max_bullets = 1  # Кол-во пуль, которые звездолёт выстреливает за 1 раз
        self.score_font = pygame.font.SysFont('Comic Sans MS', 30)
        self.score_trigger = 150
        self.score = 0

    def switch_weapon(self):
        self.weapon_type = next(self.weapon_selector)
        self.weapon_switch_sound.play()

    def handle_events(self, frame):
        """Метод - обработчик событий. Выполняет те же действия, что и в базовом шаблоне"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:  # Нажатие на кнопку мыши
                self.mouse_pressed = True  # Сохраняем состояние кнопки
            if event.type == pygame.MOUSEBUTTONUP:  # Отпускание кнопки мыши
                self.mouse_pressed = False  # Сохраняем состояние кнопки
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.switch_weapon()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                self.timed_abilities["Stasis"].active = True
                self.timed_abilities["Stasis"].sound.play()
            if event.type == pygame.KEYUP and event.key == pygame.K_s:
                self.timed_abilities["Stasis"].active = False
                self.timed_abilities["Stasis"].sound.stop()
        # Если кнопка нажата и с последнего выстрела прошло больше self.fire_rate секунд...
        if self.mouse_pressed and \
                (time.time() - self.starship.last_bullet_time) > self.weapons[self.weapon_type].fire_rate and \
                self.weapons[self.weapon_type].ammo > 0:
            new_bullets = self.starship.fire(pygame.mouse.get_pos(), BULLET_SPEED,
                                             self.max_bullets, self.weapons[self.weapon_type].type)
            self.bullets.add(*new_bullets)  # И добавляем их в общий список
            self.weapons[self.weapon_type].ammo -= 1
        for enemy in self.enemies:
            if time.time() - enemy.last_bullet_time > enemy.fire_rate and not self.timed_abilities["Stasis"].active:
                if enemy.type == "type_1":
                    new_bullets = enemy.fire(self.starship.pos, 5, enemy.max_bullets)  # Создаём новые объекты пуль
                elif enemy.type == "type_2":
                    new_bullets = enemy.fire(self.starship.pos, 2, enemy.max_bullets)  # Создаём новые объекты пуль
                elif enemy.type == "type_3":
                    new_bullets = enemy.fire(self.starship.pos, 5, enemy.max_bullets)  # Создаём новые объекты пуль
                elif enemy.type == "type_4":
                    new_bullets = enemy.fire(pygame.mouse.get_pos(), 10, enemy.max_bullets)
                else:
                    new_bullets = []
                self.enemy_bullets.add(*new_bullets)  # И добавляем их в общий список
        if not self.timed_abilities["Stasis"].active:
            if frame % ASTEROIDS_SPAWN_RATE == 0:  # Каждый ASTEROIDS_SPAWN_RATE кадр
                self.cast_asteroid()  # Создаём астероид
            if frame % 700 == 0 and frame != 0:
                if self.score < self.score_trigger:
                    self.spawn_enemy("normal")
                else:
                    self.spawn_enemy("boss")
                    self.score_trigger += 150

    def boosters_manager(self, frame):
        """Метод - обработчик всех событий с бустерами в т.ч. столкновений"""
        hits = spritecollide(self.starship, self.boosters, False)
        for booster in hits:
            booster_type = booster.type
            if booster_type in self.boosters_timeouts:
                self.timed_booster_handler(booster_type)
            elif booster_type in self.weapons:
                self.weapons_handler(booster_type)
            elif booster_type in self.timed_abilities:
                self.booster_handlers[booster_type]("activate")
            booster.pickup_sound.play()
            booster.kill()

        for booster_type, timeout in self.boosters_timeouts.items():
            # Если бустер активен (timeout > 0), но активное время закончилось (time.time() > timeout)...
            if time.time() > timeout > 0:
                self.boosters_timeouts[booster_type] = 0  # задаём время деактивации равным 0 (отключённое состояние)
                self.booster_handlers[booster_type]("deactivate")  # деактивируем бустер (возвращаем исходное поведение)
        for booster_type, weapon in self.weapons.items():
            if weapon.ammo <= 0:
                self.weapons[booster_type].ammo = 0
                self.booster_handlers[booster_type]("deactivate")
        for booster_type, ability in self.timed_abilities.items():
            status = self.timed_abilities[booster_type].active
            if ability.amount <= 0 and status:
                self.timed_abilities[booster_type].active = False
                self.timed_abilities[booster_type].amount = 0
                self.timed_abilities[booster_type].sound.stop()
            elif ability.amount > 0 and status:
                self.timed_abilities[booster_type].amount -= status

        if frame % BOOSTER_SPAWN_RATE == 0 and frame != 0:
            self.boosters.add(Booster())  # ...размещаем новый бустер на игровом поле

    def timed_booster_handler(self, booster_type):
        if self.boosters_timeouts[booster_type] == 0:
            self.boosters_timeouts[booster_type] = time.time() + BOOSTER_DURATION
            self.booster_handlers[booster_type]("activate")
        elif self.boosters_timeouts[booster_type] > 0:
            self.boosters_timeouts[booster_type] += BOOSTER_DURATION

    def weapons_handler(self, booster_type):
        if self.weapons[booster_type].ammo == 0:
            self.booster_handlers[booster_type]("activate")
        self.weapons[booster_type].ammo += 20

    @staticmethod
    def update_objects(sprite_groups):
        for sprite_group in sprite_groups:
            sprite_group.update()

    @staticmethod
    def update_enemies(enemies, player):
        enemies.update(player)

    @staticmethod
    def draw_enemies(enemies, screen):
        enemies.draw(screen)
        for enemy in enemies:
            enemy.draw_health_bar(screen)

    def draw(self, player, sprite_groups, enemies, debug=False):
        """Метод отрисовки объектов. Переносит на игровое поле все объекты переданные ему внутри аргумена
        objects_list """
        screen.fill(BG_COLOR)
        player.draw(self.screen)
        for sprite_group in sprite_groups:
            sprite_group.draw(self.screen)
        self.draw_enemies(enemies, self.screen)
        player.sprites()[0].draw_health_bar(self.screen)
        if debug:
            pygame.draw.rect(self.screen, (255, 0, 0), self.starship.rect, 3)
            for asteroid in self.asteroids.sprites():
                pygame.draw.rect(self.screen, (0, 255, 0), asteroid.rect, 3)
            for bullet in self.bullets.sprites():
                pygame.draw.rect(self.screen, (0, 0, 255), bullet.rect, 3)
            for enemy in self.enemies.sprites():
                pygame.draw.rect(self.screen, (255, 0, 255), enemy.rect, 3)
            for booster in self.boosters.sprites():
                pygame.draw.rect(self.screen, (255, 255, 0), booster.rect, 3)

    def check_collisions(self):
        for bullet in self.bullets.sprites():
            if bullet.pos[0] > SCREEN_SIZE[0] or bullet.pos[1] > SCREEN_SIZE[1] or (bullet.pos < 0).any():
                bullet.kill()
            # С каким из астероидов имеется столкновение?
            hits = [ast for ast in self.asteroids if collide_mask(bullet, ast)]
            if hits:
                for asteroid in hits:
                    fragments = asteroid.explode()  # Разбиваем астероид на осколки
                    self.score += 1
                    asteroid.kill()
                    self.asteroids.add(fragments)
                if bullet.type == "explosive":
                    self.explosions.add(bullet.explode())
                bullet.kill()

            hits = spritecollide(bullet, self.enemies, False)
            if hits:
                for enemy in hits:
                    if not enemy.damage():  # У врага осталось 0 HP
                        self.score += enemy.score_gain
                        enemy.kill()
                if bullet.type == "explosive":
                    self.explosions.add(bullet.explode())
                bullet.kill()

        for en_bullet in self.enemy_bullets.sprites():
            if en_bullet.pos[0] > SCREEN_SIZE[0] or en_bullet.pos[1] > SCREEN_SIZE[1] or (en_bullet.pos < 0).any():
                en_bullet.kill()

            hits = [ast for ast in self.asteroids if collide_mask(en_bullet, ast)]
            if hits:
                for asteroid in hits:
                    fragments = asteroid.explode()  # Разбиваем астероид на осколки
                    asteroid.kill()
                    self.asteroids.add(*fragments)
                en_bullet.kill()

            if collide_mask(en_bullet, self.starship):
                if self.boosters_timeouts["Shield"] == 0 and self.starship.damage_animation_timeout == 0:
                    return self.starship.damage()

        for explosion in self.explosions.sprites():
            hits = spritecollide(explosion, self.asteroids, dokill=True)
            self.score += len(hits)
            spritecollide(explosion, self.enemy_bullets, dokill=True)
            hits = spritecollide(explosion, self.enemies, dokill=False)
            if hits:
                for enemy in hits:
                    if not enemy.damage(1 / 16):  # У врага осталось 0 HP
                        self.score += enemy.score_gain
                        enemy.kill()
            spritecollide(explosion, self.boosters, dokill=True)

        # Столкновение астероидов и игрока
        # Индекс астероида, столкнувшегося с игроком
        hits = [ast for ast in self.asteroids if collide_mask(self.starship, ast)]
        if hits:  # Если столкновение было...
            # Если бустер "Щит" активен
            if self.boosters_timeouts["Shield"] > 0:
                [ast.kill() for ast in hits]
            elif self.starship.damage_animation_timeout != 0:
                pass
            else:
                return self.starship.damage()
        return False

    def cast_asteroid(self):
        new_asteroid = Asteroid()  # Создаём астероид
        self.asteroids.add(new_asteroid)  # Добавляем его в список всех астероидов

    def spawn_enemy(self, strength):
        new_enemy = Enemy(strength=strength)
        new_enemies = [new_enemy]
        if new_enemy.type == "type_3":
            new_enemies += [Enemy("type_3") for _ in range(5)]
        elif new_enemy.type == "type_1":
            new_enemies += [Enemy("type_1") for _ in range(2)]
        self.enemies.add(*new_enemies)

    def rapid_fire(self, mode):
        if mode == "activate":  # Если бустер нужно активировать...
            self.weapons[self.weapon_type].fire_rate /= RAPID_FIRE_MULTIPLIER
        elif mode == "deactivate":  # Если бустер нужно отключить...
            self.weapons[self.weapon_type].fire_rate *= RAPID_FIRE_MULTIPLIER

    def shield(self, mode):
        if mode == "activate":
            # При активации подменяем оригинальную картинку звездолёта на картинку с щитком
            self.starship.original_image = pygame.image.load(os.path.join("images", "Starship_with_shield.png"))
        elif mode == "deactivate":
            # При деактивации возвращаем исходную картинку на место
            self.starship.original_image = pygame.image.load(os.path.join("images", "starship.png"))

    def triple_bullets(self, mode):
        if mode == "activate":  # При активации...
            self.max_bullets = MAX_BULLETS  # изменить кол-во пуль, которые звездолёт выстреливает за 1 раз на 3
        elif mode == "deactivate":  # При деактивации...
            self.max_bullets = 1  # вернуть значение обратно равным 1

    def stasis(self, mode):
        current_amount = self.timed_abilities["Stasis"].amount
        if mode == "activate" and current_amount < 1000:
            self.gui.activate_stasis_hint()
            if 1000 - current_amount < 200:
                self.timed_abilities["Stasis"].amount = 1000
            else:
                self.timed_abilities["Stasis"].amount += 200

    def health(self, mode):
        if mode == "activate":
            if (diff := self.starship.max_hp - self.starship.hp) <= 2:
                self.starship.hp += diff
            else:
                self.starship.hp += 2
        elif mode == "deactivate":
            pass

    def explosive_bullets(self, mode):
        if mode == "activate":
            self.gui.activate_weapon_switch_hint()

    def run(self):
        """Главный цикл программы. Вызывается 1 раз за игру"""
        frame = 0
        clock = pygame.time.Clock()
        while True:
            clock.tick(MAX_FPS)
            self.handle_events(frame)
            self.boosters_manager(frame)
            self.update_objects([self.starship, self.bullets])
            if not self.timed_abilities["Stasis"].active:
                self.update_objects([self.enemy_bullets, self.asteroids, self.explosions])
                self.update_enemies(self.enemies, self.starship)
            self.draw(RenderPlain(self.starship), [self.boosters, self.bullets, self.enemy_bullets, self.asteroids,
                                                   self.explosions], enemies=self.enemies)
            self.gui.update(self.score, self.weapon_type, self.weapons, self.timed_abilities)
            pygame.display.update()
            if self.check_collisions():
                self.gui.game_over()
                return
            frame += 1


class Starship(Sprite):
    """Класс представляющий игрока"""

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.pos = np.array([SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2])
        self.original_image = pygame.image.load(os.path.join("images", "starship.png"))
        self.damage_image = pygame.image.load(os.path.join("images", "starship_damage.png"))
        self.to_transform_image = self.original_image
        self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=self.pos)
        self.max_hp = 5
        self.hp = self.max_hp
        self.damage_animation_timeout = 0
        self.last_bullet_time = 0

    def update(self):
        self.animate_damage()
        self.move()

    def animate_damage(self):
        if time.time() < self.damage_animation_timeout:
            self.to_transform_image = self.damage_image
        elif time.time() > self.damage_animation_timeout:
            self.damage_animation_timeout = 0
            self.to_transform_image = self.original_image

    def damage(self, d=1):
        self.hp -= d
        self.damage_animation_timeout = time.time() + 0.3
        return self.hp <= 0

    def draw_health_bar(self, screen: pygame.Surface):
        current_width = (self.original_image.get_width() + 10) / self.max_hp * self.hp
        pygame.draw.rect(screen, (0, 200, 0), (*self.rect.topleft, current_width, 5))

    def move(self):
        mouse_pos = pygame.mouse.get_pos()
        direction = mouse_pos - self.pos
        angle = self._calculate_angle(mouse_pos)
        self.speed = direction / SHIP_SPEED
        self.pos += self.speed
        self.image = pygame.transform.rotate(self.to_transform_image, int(angle))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=self.pos)

    def _calculate_angle(self, mouse_pos):  # Starship._calculate_angle
        rel_x, rel_y = mouse_pos - self.pos  # x и у составляющие вектора направления
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90  # Расчёт угла
        return angle

    def fire(self, target_pos: np.ndarray, rel_speed, bullet_num, bullet_type="normal"):
        self.last_bullet_time = time.time()  # Сохраняем время последнего выстрела
        new_bullets = []  # Создаём список, куда поместим все новые пули
        for i in range(bullet_num):  # Заданное количество раз...
            if bullet_num == 1:  # В случае одной пули...
                angle_offset = 0  # ...зададим смещение относительно направления взгляда равным 0
            else:  # Иначе...
                angle_offset = -15 + 30 / (bullet_num - 1) * i  # ..расчитаем смещения для всех пуль
            new_bullets.append(
                Bullet(self.pos.copy(), target_pos, rel_speed, angle_offset, bullet_type))
        if isinstance(self, Enemy):
            new_bullets[0].enemy_launch_sound.play()
        else:
            new_bullets[0].launch_sound.play()
        return new_bullets  # Возвращаем список из созданных пуль (список из 1 элемента по-умолчанию)


@dataclass
class EnemyType:
    type_: str
    strength: str
    original_image: pygame.Surface
    damage_image: pygame.Surface
    rel_speed: float
    hitbox: Tuple[int, int]
    hp: int
    fire_rate: float
    max_bullets: int
    score_gain: int


class Enemy(Starship):
    variants = [EnemyType(type_="type_1", original_image=pygame.image.load(os.path.join("images", "enemy_1.png")),
                          damage_image=pygame.image.load(os.path.join("images", "enemy_1_damage.png")),
                          hitbox=(35, 40), hp=3, fire_rate=1.5, max_bullets=1, rel_speed=1, score_gain=2,
                          strength="normal"),
                EnemyType(type_="type_2", original_image=pygame.image.load(os.path.join("images", "enemy_2.png")),
                          damage_image=pygame.image.load(os.path.join("images", "enemy_2_damage.png")),
                          hitbox=(80, 80), hp=30, fire_rate=2, max_bullets=7, rel_speed=0.5, score_gain=10,
                          strength="boss"),
                EnemyType(type_="type_3", original_image=pygame.image.load(os.path.join("images", "enemy_3.png")),
                          damage_image=pygame.image.load(os.path.join("images", "enemy_3_damage.png")),
                          hitbox=(20, 20), hp=1, fire_rate=2, max_bullets=1, rel_speed=2, score_gain=1,
                          strength="normal"),
                EnemyType(type_="type_4", original_image=pygame.image.load(os.path.join("images", "enemy_4.png")),
                          damage_image=pygame.image.load(os.path.join("images", "enemy_4_damage.png")),
                          hitbox=(40, 40), hp=5, fire_rate=0.5, max_bullets=1, rel_speed=1, score_gain=10,
                          strength="boss")
                ]

    def __init__(self, type_="random", strength="normal"):
        super(Enemy, self).__init__()
        self.pos = random.choice([Asteroid._left_pos, Asteroid._top_pos,  # Генерируем случайную начальную позицию
                                  Asteroid._right_pos, Asteroid._bottom_pos])()
        subset = list(filter(lambda x: x.strength == strength, self.variants))
        if type_ == "random":
            enemy_type = random.choice(subset)
        else:
            enemy_type = random.choice(list(filter(lambda x: x.type_ == type_, subset)))
        self.strength = strength
        self.type = enemy_type.type_
        self.original_image = enemy_type.original_image
        self.damage_image = enemy_type.damage_image
        self.to_transform_image = self.original_image
        self.w, self.h = enemy_type.hitbox
        self.rel_speed = enemy_type.rel_speed
        self.max_hp = enemy_type.hp
        self.hp = enemy_type.hp
        self.fire_rate = enemy_type.fire_rate
        self.max_bullets = enemy_type.max_bullets
        self.score_gain = enemy_type.score_gain
        self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)
        self.damage_animation_timeout = 0
        self.last_bullet_time = time.time() + random.uniform(0.5, 1.5)
        self.damage_sound = pygame.mixer.Sound(os.path.join("sounds", "explosion_enemy_1.wav"))
        self.kill_sound = pygame.mixer.Sound(os.path.join("sounds", "explosion_enemy_1.wav"))

    def update(self, player):
        self.animate_damage()
        self.rotate(player)
        self.move(player)

    def rotate(self, player):
        angle = self._calculate_angle(player.pos)
        self.image = pygame.transform.rotate(self.to_transform_image, int(angle))
        self.mask = pygame.mask.from_surface(self.image)

    def animate_damage(self):
        if time.time() < self.damage_animation_timeout:
            self.to_transform_image = self.damage_image
        elif time.time() > self.damage_animation_timeout:
            self.damage_animation_timeout = 0
            self.to_transform_image = self.original_image

    def move(self, player: Starship):
        direction = player.pos - self.pos
        self.speed = direction / max(abs(direction)) * self.rel_speed
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)

    def damage(self, d=1):
        self.hp -= d
        self.damage_animation_timeout = time.time() + 0.1
        if status := self.hp > 0:
            return status
        else:
            self.kill_sound.play()
            return status

    def draw_health_bar(self, screen: pygame.Surface):
        screen_size = screen.get_size()
        if self.strength == "boss":
            current_width = (screen_size[0] - 20) / self.max_hp * self.hp
            pygame.draw.rect(screen, (200, 0, 0), (10, 10, current_width, 20))
        elif self.strength == "normal":
            current_width = (self.w + 10) / self.max_hp * self.hp
            pygame.draw.rect(screen, (200, 0, 0), (*self.rect.topleft, current_width, 5))


@dataclass
class BulletType:
    type: str
    original_image: pygame.Surface
    launch_sounds: List[pygame.mixer.Sound]
    enemy_launch_sounds: List[pygame.mixer.Sound]
    hit_sounds: List[pygame.mixer.Sound]
    explosion_sounds: List[pygame.mixer.Sound]


class Bullet(Sprite):
    # Объектов класса Bullet будет создаваться довольно много, поэтому мы
    # хотим загрузить картинку только 1 раз
    bullet_types = {"normal": BulletType("normal", pygame.image.load(os.path.join("images", "bullet.png")),
                                         [pygame.mixer.Sound(os.path.join("sounds", "blaster_short_1.wav")),
                                          pygame.mixer.Sound(os.path.join("sounds", "blaster_short_2.wav")),
                                          pygame.mixer.Sound(os.path.join("sounds", "blaster_short_3.wav"))],
                                         [pygame.mixer.Sound(os.path.join("sounds", "blaster_short_4.wav")),
                                          pygame.mixer.Sound(os.path.join("sounds", "blaster_short_5.wav"))],
                                         [None], [None]),
                    "explosive": BulletType("explosive",
                                            pygame.image.load(os.path.join("images", "powered_bullet.png")),
                                            [pygame.mixer.Sound(os.path.join("sounds", "explosive_bullet_1.wav")),
                                             pygame.mixer.Sound(os.path.join("sounds", "explosive_bullet_2.wav"))],
                                            [pygame.mixer.Sound(os.path.join("sounds", "explosive_bullet_1.wav")),
                                             pygame.mixer.Sound(os.path.join("sounds", "explosive_bullet_2.wav"))],
                                            [None],
                                            [pygame.mixer.Sound(os.path.join("sounds", "explosion_bullet_1.wav"))])}

    def __init__(self, pos, target_pos: np.ndarray, rel_speed, angle_offset=0, type="normal"):
        pygame.sprite.Sprite.__init__(self)
        self.type = type
        self.setup = self.bullet_types[self.type]
        self.original_image = self.setup.original_image
        self.pos = pos
        self.direction = target_pos - pos
        asr = math.pi / 180 * angle_offset
        self.direction[0] = self.direction[0] * math.cos(asr) - self.direction[1] * math.sin(asr)
        self.direction[1] = self.direction[0] * math.sin(asr) + self.direction[1] * math.cos(asr)
        self.speed = self.direction / max(abs(self.direction)) * rel_speed
        self.angle = self._calculate_angle(target_pos) - angle_offset  # Расчёт угла поворота
        self.image = pygame.transform.rotate(self.original_image, int(self.angle))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=self.pos)
        self.launch_sound = random.choice(self.setup.launch_sounds)
        self.enemy_launch_sound = random.choice(self.setup.enemy_launch_sounds)
        self.hit_sound = random.choice(self.setup.hit_sounds)
        self.explosion_sound = random.choice(self.setup.explosion_sounds)

    def update(self):
        self.move()

    def move(self):
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos)

    def explode(self):
        self.explosion_sound.play()
        return ExplosionAnimation(self.pos.copy())

    def _calculate_angle(self, target_pos):
        rel_x, rel_y = target_pos - self.pos
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90
        return angle


class Asteroid(Sprite):
    # Оригинальные картинки астероидов
    ast_variants = [("small", pygame.image.load(os.path.join("images", "ast1_small.png")), (10, 10)),
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

    def __init__(self, pos=None, speed=None, ast_type=None):  # Конструктор класса Asteroid
        pygame.sprite.Sprite.__init__(self)
        # Если координаты, скорость и тип заданы...
        if (pos is not None) and (speed is not None) and (ast_type is not None):
            self.init_asteroid_fragment(pos, speed, ast_type)  # ...инициализировать осколок
        else:  # Иначе (координаты, скорость и тип НЕ заданы)...
            self.init_rand_asteroid()  # ...инициализировать обычный астероид
        self.angle = 0
        self.angle_inc = random.uniform(-2, 2)
        self.explosion_sound = pygame.mixer.Sound(os.path.join("sounds", "explosion_1.wav"))

    def init_asteroid_fragment(self, pos, speed, ast_type):
        """Метод инициализирует осколок астероида, принимая на вход его координаты (pos), скорость (speed) и тип (
        ast_type) """
        # Отбираем только картинки с астероидами заданного типа
        ast_type_variants = list(filter(lambda x: x[0] == ast_type, self.ast_variants))
        # Берём случайную картинку астероида заданного типа
        self.type, self.original_image, hitbox_shape = random.choice(ast_type_variants)
        self.pos = pos  # Координаты осколка задаём НЕ случайно
        self.w, self.h = hitbox_shape
        self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)
        self.speed = speed  # Задаём направление (скорость) НЕ случайно

    def init_rand_asteroid(self):
        """Метод инициализирует обычный астероид случайными типом и координатам"""
        # Случайный выбор типа и картинки астероида
        self.type, self.original_image, hitbox_shape = random.choice(self.ast_variants)
        self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.w, self.h = hitbox_shape  # Сохраняем длину и ширину хитбокса
        self.pos = random.choice([self._left_pos, self._top_pos,  # Генерируем случайную начальную позицию
                                  self._right_pos, self._bottom_pos])()
        # Получаем хитбокс с заданными размерами
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)
        self.direction = pygame.mouse.get_pos() - self.pos  # Вычисляем направление
        self.speed = self.direction / ASTEROID_SPEED  # Расчитываем скорость

    @staticmethod
    def _left_pos():
        """Генерация позиции слева"""
        return np.array((-150, random.uniform(0, SCREEN_SIZE[1])))

    @staticmethod
    def _right_pos():
        """Генерация позиции справа"""
        return np.array((SCREEN_SIZE[0] + 150, random.uniform(0, SCREEN_SIZE[1])))

    @staticmethod
    def _top_pos():
        """Генерация позиции сверху"""
        return np.array((random.uniform(0, SCREEN_SIZE[0]), -150))

    @staticmethod
    def _bottom_pos():
        """Генерация позиции снизу"""
        return np.array((random.uniform(0, SCREEN_SIZE[0]), SCREEN_SIZE[1] + 150))

    def speed_offset(self):
        # Уменьшаем скорость в 2 раза и изменяем её составляющие по x и y на небольшую величину
        offset = self.speed * FRAGMENTS_SPEED + np.random.uniform(-0.5, 0.5, 2)
        return offset

    def pos_offset(self):
        # Возвращаем немного смещённые координаты центра астероида
        offset = self.pos + np.random.uniform(-10, 10, 2)
        return offset

    def check_borders(self):
        # Если центр астероида за нижней границей...
        if self.pos[0] > (SCREEN_SIZE[0] + 150):
            self.pos[0] = -150  # ...перемещаем его на верхнюю
        # Если центр астероида за верхней границей...
        elif (self.pos[0] + 150) < 0:
            self.pos[0] = SCREEN_SIZE[0] + 150  # ...перемещаем его на нижнюю
        # Если центр астероида за правой границей...
        if (self.pos[1] - 150) > SCREEN_SIZE[1]:
            self.pos[1] = -150  # ...перемещаем его на левую
        # Если центр астероида за левой границей...
        elif (self.pos[1] + 150) < 0:
            self.pos[1] = SCREEN_SIZE[1] + 150  # ...перемещаем его на правую
        # Обновляем хитбокс, так как произошло перемещение
        self.rect = self.image.get_rect(center=self.pos)

    def update(self):
        self.check_borders()  # Обработка выхода за границы
        self.rotate()
        self.move()

    def rotate(self):
        self.angle += self.angle_inc
        self.image = pygame.transform.rotate(self.original_image, self.angle)

    def move(self):
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos)

    def explode(self):  # Метод explode класса Asteroid
        fragments = []  # Список с осколками астероидов
        if self.type == "large":  # Если астероид большой...
            for _ in range(2):
                # Генерируем новые смещённые параметры для осколков
                pos, speed = self.pos_offset(), self.speed_offset()
                fragments.append(Asteroid(pos, speed, "medium"))  # Передаём их в конструктор астероида
        if self.type == "medium":  # Если астероид средний...
            for _ in range(3):
                # Генерируем новые смещённые параметры для осколков
                pos, speed = self.pos_offset(), self.speed_offset()
                fragments.append(Asteroid(pos, speed, "small"))  # Передаём их в конструктор астероида
        if self.type == "small":  # Если астероид маленький...
            pass  # ...не делать ничего
        self.explosion_sound.play()
        return fragments


@dataclass
class BoosterType:
    type: str
    original_image: pygame.Surface
    pickup_sound: pygame.mixer.Sound


class Booster(Sprite):
    """Класс представляющий картинку бустера на игровом поле. Все эффекты от бустеров не будут непосредственно
    связаны с объектами данного класса и будут описаны внутри класса Game """
    # Типы возможных бустеров и их картинки
    booster_types = {
        "Rapid_fire": BoosterType("Rapid_fire", pygame.image.load(os.path.join("images", "Rapid_fire.png")),
                                  pygame.mixer.Sound(os.path.join("sounds", "booster_1.wav"))),
        "Shield": BoosterType("Shield", pygame.image.load(os.path.join("images", "Shield.png")),
                              pygame.mixer.Sound(os.path.join("sounds", "booster_1.wav"))),
        "Triple_bullets": BoosterType("Triple_bullets",
                                      pygame.image.load(os.path.join("images", "Triple_bullets.png")),
                                      pygame.mixer.Sound(os.path.join("sounds", "booster_1.wav"))),
        "Explosive_bullets": BoosterType("Explosive_bullets",
                                         pygame.image.load(os.path.join("images", "Explosive_bullets.png")),
                                         pygame.mixer.Sound(os.path.join("sounds", "booster_ammo.wav"))),
        "Health": BoosterType("Health", pygame.image.load(os.path.join("images", "health.png")),
                              pygame.mixer.Sound(os.path.join("sounds", "heal_1.wav"))),
        "Stasis": BoosterType("Stasis", pygame.image.load(os.path.join("images", "Stasis.png")),
                              pygame.mixer.Sound(os.path.join("sounds", "booster_1.wav")))}

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.setup = self.booster_types[random.choice(list(self.booster_types.keys()))]
        self.type = self.setup.type
        self.image = self.setup.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.pos = np.array([random.randint(100, SCREEN_SIZE[0] - 100),  # Генерация случайных координат для бустера
                             random.randint(100, SCREEN_SIZE[1] - 100)])
        self.rect = self.image.get_rect(center=self.pos)  # Получение хитбокса бустера
        self.pickup_sound = self.setup.pickup_sound


class ExplosionAnimation(Sprite):
    original_images = [pygame.image.load(os.path.join("images", "explosion_animation", file)) for file in
                       sorted(os.listdir(os.path.join("images", "explosion_animation")))]

    def __init__(self, center):
        Sprite.__init__(self)
        self.center = center
        self.current_idx = 0
        self.image = self.original_images[self.current_idx]
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.current_idx += 1
        if self.current_idx < len(self.original_images):
            self.image = self.original_images[self.current_idx]
            self.rect = self.image.get_rect(center=self.center)
            self.mask = pygame.mask.from_surface(self.image)
        else:
            self.kill()


while True:
    game = Game(screen)  # Создание и запуск игры
    game.run()
