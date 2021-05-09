import math  # Модуль math будет полезен для вычисления угла наклона звездолёта
import os  # Модуль os нужен для работы с путями и файлами
import random  # Модуль random нужен для генерации случайных чисел
import sys  # Модуль sys понадобится нам для закрытия игры
import time  # Модуль time нужен для замера времени
from dataclasses import dataclass
from typing import Tuple

import numpy as np  # Модуль numpy нужен для поэлементного сложения векторов
import pygame  # Модуль pygame для реализации игровой логики

from config import *  # Настройки для большинства игровых механик

# Инициализация модуля pygame
pygame.init()
# Цвет фона в формате RGB (красный, синий, зелёный). (0, 0, 0) - чёрный цвет.
BG_COLOR = (0, 0, 0)
# Объект дисплея (0, 0) - полный экран, если задать (800, 600), то окно будет размером 800х600 пикселей
screen = pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
# Получим ширину и высоту игрового поля из объекта screen и сохраним в глобальную переменную.
# Мы будем использовать SCREEN_SIZE очень часто!
SCREEN_SIZE = screen.get_size()


class Game:
    """Основной класс игры. В нём представлены основные методы для управления игровыми объектами, а также сами
    объекты """

    def __init__(self, screen):
        self.screen = screen
        self.starship = Starship()  # Объект класса Starship (игрок)
        self.enemies = []
        self.bullets = []  # Хранение объектов пуль (Bullet)
        self.enemy_bullets = []
        self.asteroids = []  # Заготовка для хранения объектов астероидов
        self.boosters = []  # Список буcтеров для отрисовки
        self.boosters_timeouts = {"Rapid_fire": 0,
                                  "Shield": 0,
                                  "Triple_bullets": 0}  # Хранение времени деактивации бустеров
        self.booster_counts = {"Explosive_bullets": 0}
        self.booster_handlers = {"Rapid_fire": self.rapid_fire,
                                 "Shield": self.shield,
                                 "Triple_bullets": self.triple_bullets,
                                 "Explosive_bullets": self.explosive_bullets}  # Словарь с функциями-активаторами бустеров
        self.weapon_type = "normal"
        self.mouse_pressed = False  # Cохраняет состояние кнопки мыши
        self.fire_rate = FIRE_RATE  # Пауза между выстрелами (в секундах)
        self.max_bullets = 1  # Кол-во пуль, которые звездолёт выстреливает за 1 раз
        self.score_font = pygame.font.SysFont('Comic Sans MS', 30)
        self.score_trigger = 50
        self.score = 0

    def handle_events(self, frame):
        """Метод - обработчик событий. Выполняет те же действия, что и в базовом шаблоне"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:  # Нажатие на кнопку мыши
                self.mouse_pressed = True  # Сохраняем состояние кнопки
            if event.type == pygame.MOUSEBUTTONUP:  # Отпускание кнопки мыши
                self.mouse_pressed = False  # Сохраняем состояние кнопки
        # Если кнопка нажата и с последнего выстрела прошло больше self.fire_rate секунд...
        if self.mouse_pressed and (time.time() - self.starship.last_bullet_time) > self.fire_rate:
            new_bullets = self.starship.fire(pygame.mouse.get_pos(), BULLET_SPEED,
                                             self.max_bullets, self.weapon_type)  # Создаём новые объекты пуль
            self.bullets += new_bullets  # И добавляем их в общий список
            if self.booster_counts["Explosive_bullets"] > 0:
                self.booster_counts["Explosive_bullets"] -= 1
        for enemy in self.enemies:
            if time.time() - enemy.last_bullet_time > enemy.fire_rate:
                if enemy.type == "type_1":
                    new_bullets = enemy.fire(self.starship.pos, 5, enemy.max_bullets)  # Создаём новые объекты пуль
                elif enemy.type == "type_2":
                    new_bullets = enemy.fire(self.starship.pos, 2, enemy.max_bullets)  # Создаём новые объекты пуль
                elif enemy.type == "type_3":
                    new_bullets = enemy.fire(self.starship.pos, 5, enemy.max_bullets)  # Создаём новые объекты пуль
                elif enemy.type == "type_4":
                    new_bullets = enemy.fire(pygame.mouse.get_pos(), 10, enemy.max_bullets)  # Создаём новые объекты пуль
                else:
                    new_bullets = []
                self.enemy_bullets += new_bullets  # И добавляем их в общий список
        if frame % ASTEROIDS_SPAWN_RATE == 0:  # Каждый ASTEROIDS_SPAWN_RATE кадр
            self.cast_asteroid()  # Создаём астероид
        if frame % 700 == 0 and frame != 0:
            if self.score < self.score_trigger:
                self.spawn_enemy("normal")
            else:
                self.spawn_enemy("boss")
                self.score_trigger += 70

    def boosters_manager(self, frame):
        """Метод - обработчик всех событий с бустерами в т.ч. столкновений"""
        boosters_rects = [boost.rect for boost in self.boosters]  # Хитбоксы бустеров для расчёта столкновений
        hit = self.starship.rect.collidelist(boosters_rects)  # Расчёт столкновений игрока и бустеров
        if hit != -1:  # Если столкновение есть...
            booster_type = self.boosters[hit].type  # получаем тип бустера из атрибута type
            if booster_type in self.boosters_timeouts:
                self.timed_booster_handler(booster_type)
            elif booster_type in self.booster_counts:
                self.counted_booster_handler(booster_type)
            # Удаляем бустер после столкновения (картинка исчезнет, но его эффект будет активен)
            del self.boosters[hit]
        # Для каждого типа бустеров и времени его деактивации...
        for booster_type, timeout in self.boosters_timeouts.items():
            # Если бустер активен (timeout > 0), но активное время закончилось (time.time() > timeout)...
            if time.time() > timeout > 0:
                self.boosters_timeouts[booster_type] = 0  # задаём время деактивации равным 0 (отключённое состояние)
                self.booster_handlers[booster_type]("deactivate")  # деактивируем бустер (возвращаем исходное поведение)
        for booster_type, count in self.booster_counts.items():
            if count <= 0:
                self.booster_counts[booster_type] = 0
                self.booster_handlers[booster_type]("deactivate")
        if frame % BOOSTER_SPAWN_RATE == 0 and frame != 0:
            self.boosters.append(Booster())  # ...размещаем новый бустер на игровом поле

    def timed_booster_handler(self, booster_type):
        if self.boosters_timeouts[booster_type] == 0:
            self.boosters_timeouts[booster_type] = time.time() + BOOSTER_DURATION
            self.booster_handlers[booster_type]("activate")
        elif self.boosters_timeouts[booster_type] > 0:
            self.boosters_timeouts[booster_type] += BOOSTER_DURATION

    def counted_booster_handler(self, booster_type):
        if self.booster_counts[booster_type] == 0:
            self.booster_counts[booster_type] += 20
            self.booster_handlers[booster_type]("activate")

    @staticmethod
    def move_objects(objects_list):
        for obj_idx, _ in enumerate(objects_list):  # Перебор групп объектов (asteroids, bullets)
            for o_idx, _ in enumerate(objects_list[obj_idx]):  # Перебор объектов внутри групп
                objects_list[obj_idx][o_idx].move()  # Перемещение объекта

    @staticmethod
    def move_enemies(enemies, player):
        for obj_idx, _ in enumerate(enemies):  # Перебор групп объектов (asteroids, bullets)
            enemies[obj_idx].move(player)  # Перемещение объекта

    def draw(self, objects_list):
        """Метод отрисовки объектов. Переносит на игровое поле все объекты переданные ему внутри аргумена
        objects_list """
        screen.fill(BG_COLOR)
        for objects in objects_list:
            for obj in objects:
                self.screen.blit(obj.image, obj.rect)
                if isinstance(obj, Enemy):
                    obj.draw_health_bar(self.screen)
        score_text = self.score_font.render(f'Score: {self.score}', False, (255, 255, 255))
        self.screen.blit(score_text, (SCREEN_SIZE[0] - 150, 0))
        if self.booster_counts["Explosive_bullets"]:
            explosive_text = self.score_font.render(f'{self.booster_counts["Explosive_bullets"]}', False, (255, 255, 255))
            self.screen.blit(explosive_text, (5, 30))
        pygame.display.update()

    def check_collisions(self):
        # Удаление пуль при вылете с игрового поля
        asteroids_rects = [ast.rect for ast in self.asteroids]  # Хитбоксы всех астероидов
        enemies_rects = [enemy.rect for enemy in self.enemies]  # Хитбоксы всех врагов
        # Разрушение астероидов и врагов при контакте с пулями
        for idx, bullet in enumerate(self.bullets):
            if bullet.pos[0] > SCREEN_SIZE[0] or bullet.pos[1] > SCREEN_SIZE[1] or (
                    bullet.pos < 0).any():  # ...если центра пули вышел за границы
                del self.bullets[idx]  # удалить объект пули
            # С каким из астероидов имеется столкновение?
            hit = bullet.rect.collidelist(asteroids_rects)
            if hit != -1:  # Если столкновение есть...
                fragments = self.asteroids[hit].explode()  # Разбиваем астероид на осколки
                self.score += 1
                del self.asteroids[hit]  # ...удалить астероид с индексом hit
                del asteroids_rects[hit]
                self.asteroids += fragments  # Добавляем эти осколки в общий список
                del self.bullets[idx]  # ...удалить пулю с индексом idx
                break
            hit = bullet.rect.collidelist(enemies_rects)
            if hit != -1:
                if not self.enemies[hit].damage():  # У врага осталось 0 HP
                    self.score += self.enemies[hit].score_gain
                    del self.enemies[hit]
                    del enemies_rects[hit]
                del self.bullets[idx]
                break
        for idx, bullet in enumerate(self.enemy_bullets):
            if bullet.pos[0] > SCREEN_SIZE[0] or bullet.pos[1] > SCREEN_SIZE[1] or (
                    bullet.pos < 0).any():  # ...если центра пули вышел за границы
                del self.enemy_bullets[idx]  # удалить объект пули
                # С каким из астероидов имеется столкновение?
            hit = bullet.rect.collidelist(asteroids_rects)
            if hit != -1:  # Если столкновение есть...
                fragments = self.asteroids[hit].explode()  # Разбиваем астероид на осколки
                del self.asteroids[hit]  # ...удалить астероид с индексом hit
                del asteroids_rects[hit]
                self.asteroids += fragments  # Добавляем эти осколки в общий список
                del self.enemy_bullets[idx]  # ...удалить пулю с индексом idx
                break
            if bullet.rect.colliderect(self.starship.rect):
                if self.boosters_timeouts["Shield"] == 0:
                    return True
        # Столкновение астероидов и игрока
        # Индекс астероида, столкнувшегося с игроком
        hit = self.starship.rect.collidelist(asteroids_rects)
        if hit != -1:  # Если столкновение было...
            # Если бустер "Щит" активен
            if self.boosters_timeouts["Shield"] > 0:
                del self.asteroids[hit]  # Удалим астероид с которым столкнулись
            # ...иначе
            else:
                return True  # ...выйти из игры
        return False

    def cast_asteroid(self):
        new_asteroid = Asteroid()  # Создаём астероид
        self.asteroids.append(new_asteroid)  # Добавляем его в список всех астероидов

    def spawn_enemy(self, strength):
        new_enemy = Enemy(strength=strength)
        new_enemies = [new_enemy]
        if new_enemy.type == "type_3":
            new_enemies += [Enemy("type_3") for _ in range(5)]
        elif new_enemy.type == "type_1":
            new_enemies += [Enemy("type_1") for _ in range(2)]
        self.enemies += new_enemies

    def rapid_fire(self, mode):
        if mode == "activate":  # Если бустер нужно активировать...
            self.fire_rate /= RAPID_FIRE_MULTIPLIER  # ...уменьшаем паузу между пулями в RAPID_FIRE_MULTIPLIER раз
        elif mode == "deactivate":  # Если бустер нужно отключить...
            self.fire_rate *= RAPID_FIRE_MULTIPLIER

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

    def explosive_bullets(self, mode):
        if mode == "activate":
            self.weapon_type = "explosive"
        elif mode == "deactivate":
            self.weapon_type = "normal"

    def game_over(self):
        gameover_font = pygame.font.SysFont('Comic Sans MS', 126)
        text_font = pygame.font.SysFont('Comic Sans MS', 56)
        gameover_text = gameover_font.render('GAME OVER!', False, (255, 255, 255))
        info_text = text_font.render(f'Your score is {self.score}', False, (255, 255, 255))
        resume_text = text_font.render('Click to continue', False, (255, 255, 255))
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

    def run(self):
        """Главный цикл программы. Вызывается 1 раз за игру"""
        frame = 0
        clock = pygame.time.Clock()
        while True:
            clock.tick(MAX_FPS)
            self.handle_events(frame)
            self.boosters_manager(frame)
            self.move_objects([[self.starship], self.bullets, self.enemy_bullets, self.asteroids])
            self.move_enemies(self.enemies, self.starship)
            self.draw([self.boosters, [self.starship], self.enemies, self.bullets, self.enemy_bullets, self.asteroids])
            if self.check_collisions():
                self.game_over()
                return
            frame += 1


class Starship:
    """Класс представляющий игрока"""

    def __init__(self):
        # Текущие координаты (в пикселях)
        self.pos = np.array([SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2])
        # Оригинальное изображение
        self.original_image = pygame.image.load(os.path.join("images", "starship.png"))
        # Изображение для отрисовки
        self.image = self.original_image
        # Границы модельки корабля (хитбокс)    
        self.rect = self.image.get_rect(center=self.pos)
        # Время последнего выстрела
        self.last_bullet_time = 0

    def move(self):
        mouse_pos = pygame.mouse.get_pos()  # Текущая позиция курсора мыши
        direction = mouse_pos - self.pos  # Текущее направление
        angle = self._calculate_angle(mouse_pos)  # Расчёт угла наклона корабля
        self.speed = direction / SHIP_SPEED  # Новое значение скорости
        self.pos += self.speed  # Движение - обновление координат
        self.image = pygame.transform.rotate(self.original_image, int(angle))  # Вращение картинки
        self.rect = self.image.get_rect(center=self.pos, width=30, height=30)  # Перемещение хитбокса

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
        self.w, self.h = enemy_type.hitbox
        self.rel_speed = enemy_type.rel_speed
        self.max_hp = enemy_type.hp
        self.hp = enemy_type.hp
        self.fire_rate = enemy_type.fire_rate
        self.max_bullets = enemy_type.max_bullets
        self.score_gain = enemy_type.score_gain
        self.image = self.original_image
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)
        self.damage_animation_timeout = 0
        self.last_bullet_time = time.time() + random.uniform(0.5, 1.5)

    def move(self, player: Starship):
        player_pos = player.pos
        direction = player_pos - self.pos
        self.speed = direction / max(abs(direction)) * self.rel_speed
        angle = self._calculate_angle(player_pos)
        if time.time() < self.damage_animation_timeout:
            self.image = pygame.transform.rotate(self.damage_image, int(angle))
        else:
            self.damage_animation_timeout = 0
            self.image = pygame.transform.rotate(self.original_image, int(angle))
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)

    def damage(self):
        self.hp -= 1
        self.damage_animation_timeout = time.time() + 0.1
        return self.hp

    def draw_health_bar(self, screen: pygame.Surface):
        screen_size = screen.get_size()
        if self.strength == "boss":
            current_width = (screen_size[0] - 20) / self.max_hp * self.hp
            pygame.draw.rect(screen, (200, 0, 0), (10, 10, current_width, 20))
        elif self.strength == "normal":
            current_width = (self.w + 10) / self.max_hp * self.hp
            pygame.draw.rect(screen, (200, 0, 0), (*self.rect.topleft, current_width, 5))


class Bullet:
    # Объектов класса Bullet будет создаваться довольно много, поэтому мы
    # хотим загрузить картинку только 1 раз
    original_images = {"normal": pygame.image.load(os.path.join("images", "bullet.png")),
                       "explosive": pygame.image.load(os.path.join("images", "powered_bullet.png"))}

    def __init__(self, pos, target_pos: np.ndarray, rel_speed, angle_offset=0, type="normal"):
        self.type = type
        self.original_image = self.original_images[type]
        self.pos = pos
        # Направление пули не изменяется с течением времени, поэтому его можно
        # вычислить внутри конструктора
        self.direction = target_pos - pos
        asr = math.pi / 180 * angle_offset  # Переводим величину смещения в радиан из градусов
        # "Поворачиваем" первую координату направления
        self.direction[0] = self.direction[0] * math.cos(asr) - self.direction[1] * math.sin(asr)
        # "Поворачиваем" первую координату направления
        self.direction[1] = self.direction[0] * math.sin(asr) + self.direction[1] * math.cos(asr)
        self.speed = self.direction / max(abs(self.direction)) * rel_speed
        # Угол также не изменяется
        self.angle = self._calculate_angle(target_pos) - angle_offset  # Расчёт угла поворота
        # Угол не изменяется, поэтому картинку тоже можно повернуть сразу в конструкторе
        self.image = pygame.transform.rotate(self.original_image, int(self.angle))
        self.rect = self.image.get_rect(center=self.pos)  # Получение хитбокса

    def move(self):
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos)

    def _calculate_angle(self, target_pos):
        rel_x, rel_y = target_pos - self.pos
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90
        return angle


class Asteroid(pygame.sprite.Sprite):
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
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)
        self.speed = speed  # Задаём направление (скорость) НЕ случайно

    def init_rand_asteroid(self):
        """Метод инициализирует обычный астероид случайными типом и координатам"""
        # Случайный выбор типа и картинки астероида
        self.type, self.original_image, hitbox_shape = random.choice(self.ast_variants)
        self.image = self.original_image
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

    def move(self):
        self.check_borders()  # Обработка выхода за границы
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)

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
        return fragments


class Booster:
    """Класс представляющий картинку бустера на игровом поле. Все эффекты от бустеров не будут непосредственно
    связаны с объектами данного класса и будут описаны внутри класса Game """
    # Типы возможных бустеров и их картинки
    booster_types = {"Rapid_fire": pygame.image.load(os.path.join("images", "Rapid_fire.png")),
                     "Shield": pygame.image.load(os.path.join("images", "Shield.png")),
                     "Triple_bullets": pygame.image.load(os.path.join("images", "Triple_bullets.png")),
                     "Explosive_bullets": pygame.image.load(os.path.join("images", "starship.png"))}

    def __init__(self):
        self.type = random.choice(list(self.booster_types.keys()))  # Выбор случайного типа для бустера
        self.image = self.booster_types[self.type]  # Выбор картинки бустера
        self.pos = np.array([random.randint(100, SCREEN_SIZE[0] - 100),  # Генерация случайных координат для бустера
                             random.randint(100, SCREEN_SIZE[1] - 100)])
        self.rect = self.image.get_rect(center=self.pos)  # Получение хитбокса бустера


while True:
    game = Game(screen)  # Создание и запуск игры
    game.run()
