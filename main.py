import math  # Модуль math будет полезен для вычисления угла наклона звездолёта
import os  # Модуль os нужен для работы с путями и файлами
import random  # Модуль random нужен для генерации случайных чисел
import sys  # Модуль sys понадобится нам для закрытия игры
import time  # Модуль time нужен для замера времени
from dataclasses import dataclass
from itertools import cycle
from typing import Tuple, List, Union, Dict

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
game_screen = pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
# Получим ширину и высоту игрового поля из объекта screen и сохраним в глобальную переменную.
# Мы будем использовать SCREEN_SIZE очень часто!
SCREEN_SIZE = game_screen.get_size()


@dataclass
class Weapon:
    type: str
    ammo: float
    fire_rate: float  # Темп огня (пауза в секундах между выстрелами)


@dataclass
class Ability:
    type: str
    amount: float
    active: bool
    sound: pygame.mixer.Sound


class GUI:
    """Класс, контролирующий отрисовку интерфейса"""
    interface_pictures = {"Normal_bullets": pygame.transform.rotate(
        pygame.image.load(os.path.join("images", "bullet.png")), 90),
        "Explosive_bullets": pygame.transform.rotate(
            pygame.image.load(os.path.join("images", "powered_bullet.png")), 90)}

    def __init__(self, screen: pygame.Surface, starship: pygame.sprite.Sprite):
        self.screen = screen
        self.starship = starship
        self.score = 0
        self.weapons = None
        self.weapon_type = None
        self.timed_abilities = None
        self.score_font = pygame.font.SysFont('Comic Sans MS', 30)
        self.gameover_font = pygame.font.SysFont('Comic Sans MS', 126)
        self.text_font = pygame.font.SysFont('Comic Sans MS', 56)
        self.score_position = np.array((SCREEN_SIZE[0] - 150, 0))  # Координаты надписи со счётом игрока
        self.abilities_position = np.array((5, SCREEN_SIZE[1] / 2))  # Координаты счётчиков способностей
        self.abilities_v_offset = np.array((0, 35))  # Сдвиг нового счётчика способностей относительно предыдущего
        self.weapon_panel_position = np.array((5, SCREEN_SIZE[1] / 4))  # Координаты панели с оружием
        self.weapons_v_offset = np.array((0, 35))  # Сдвиг очередного элемента на панели оружия
        self.switch_weapon_hint_timeout = 160  # Время подсказки о смене оружия (в кадрах)
        self.switch_weapon_hint_active = False  # Статус подсказки о смене оружия
        self.stasis_hint_timeout = 160  # Время подсказки о активации "стазиса"
        self.stasis_hint_active = False  # Статус подсказки о активации "стазиса"

    def update(self, score: int, weapon_type: str, weapons: Dict[str, Weapon], timed_abilities: Dict[str, Ability]):
        """Метод, обновляющий GUI"""
        self.score = score
        self.weapon_type = weapon_type
        self.weapons = weapons
        self.timed_abilities = timed_abilities
        self.draw()

    def draw(self):
        """Отрисовка всех стационарных компонентов GUI"""
        self.draw_score()
        self.draw_weapons()
        self.draw_abilities()
        self.draw_hints()

    def draw_score(self):
        """Отрисовка счёта игрока"""
        score_text = self.score_font.render(f'Score: {self.score}', False, (255, 255, 255))
        self.screen.blit(score_text, self.score_position)

    def draw_weapons(self):
        """Отрисовка списка доступного и активного оружия вместе с боезапасом"""
        vertical_offset = 1
        for weapon in self.weapons:
            active_offset = np.array((0, 0))  # Сдвиг для активного оружия (немного выступает из общего списка)
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
        """Отрисовка доступных способностей"""
        text = self.score_font.render(f'Stasis: {self.timed_abilities["Stasis"].amount:.0f}', False, (255, 255, 255))
        self.screen.blit(text, self.abilities_position)

    def draw_hints(self):
        """Отрисовка игровых подсказок"""
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
        """Вызывает экран окончания игры"""
        gameover_text = self.gameover_font.render('GAME OVER!', False, (255, 255, 255))
        info_text = self.text_font.render(f'Your score is {self.score}', False, (255, 255, 255))
        resume_text = self.text_font.render('Click to continue', False, (255, 255, 255))
        while True:  # Цикл ожидания действия игрока (выйти или продолжить)
            self.screen.blit(gameover_text, (SCREEN_SIZE[0] / 3.5, SCREEN_SIZE[1] / 3.5))
            self.screen.blit(info_text, (SCREEN_SIZE[0] / 3.5 * 1.2, SCREEN_SIZE[1] / 3.5 * 2))
            self.screen.blit(resume_text, (SCREEN_SIZE[0] / 3.5 * 1.2, SCREEN_SIZE[1] / 3.5 * 2.2))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()  # Выход из игры
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return  # Продолжение игры


class Game:
    """Основной класс игры. В нём представлены основные методы для управления игровыми объектами, а также сами
    объекты """

    def __init__(self, screen):
        self.screen = screen
        self.starship = Starship()  # Объект класса Starship (игрок)
        self.enemies = RenderPlain()  # Хранение объектов врагов (Enemy)
        self.bullets = RenderPlain()  # Хранение объектов пуль (Bullet)
        self.enemy_bullets = RenderPlain()  # Хранение объектов вражеских пуль (они имеют отличное от обычных поведение)
        self.asteroids = RenderPlain()  # Хранение объектов астероидов (Asteroid)
        self.boosters = RenderPlain()  # Хранение объектов бустеров (Booster)
        self.explosions = RenderPlain()  # Хранение объектов взрывов (Explosions)
        self.gui = GUI(screen, self.starship)  # Объект интерфейса пользователя
        # Время отключения бустера (0 означает, что бустер неактивен)
        self.boosters_timeouts = {"Rapid_fire": 0,
                                  "Shield": 0,
                                  "Triple_bullets": 0,
                                  "Health": 0}
        # Обработчики активации бустеров
        self.booster_handlers = {"Rapid_fire": self.rapid_fire,
                                 "Shield": self.shield,
                                 "Triple_bullets": self.triple_bullets,
                                 "Explosive_bullets": self.explosive_bullets,
                                 "Health": self.health,
                                 "Stasis": self.stasis}
        # Доступное в игре оружие. Каждое имеет тип, боезапас и темп огня.
        self.weapons = {"Normal_bullets": Weapon("normal", float("inf"), NORMAL_BULLETS_FIRE_RATE),
                        "Explosive_bullets": Weapon("explosive", DEFAULT_EXPLOSIVE_AMMO, EXPLOSIVE_BULLETS_FIRE_RATE)}
        self.weapon_selector = cycle(self.weapons.keys())  # Селектор оружия (оружие переключается по кругу)
        self.weapon_type = next(self.weapon_selector)  # Активное в данный момент оружие (первое на очереди в селекторе)
        # Звук переключения оружия
        self.weapon_switch_sound = pygame.mixer.Sound(os.path.join("sounds", "weapon_switch.wav"))
        # Способности активируемые игроком на определённое время.
        # Объекты содержат тип, боезапас (в кадрах), статус и звук.
        self.timed_abilities = {"Stasis": Ability("Stasis", DEFAULT_STASIS_AMMO, False,
                                                  pygame.mixer.Sound(os.path.join("sounds", "clock_ticks_1.wav")))}
        self.mouse_pressed = False  # Cохраняет состояние кнопки мыши
        self.max_bullets = DEFAULT_MAX_BULLETS  # Кол-во пуль, которые звездолёт выстреливает за 1 раз
        self.score_trigger = SCORE_TRIGGER  # Счёт по достижении которого появляется босс (150, 300, 450 и т.д.)
        self.score = 0  # Текущий счёт

    def switch_weapon(self):
        """Переключение оружия "по кругу" """
        self.weapon_type = next(self.weapon_selector)
        self.weapon_switch_sound.play()

    def handle_events(self, frame: int):
        """Метод - обработчик всех игровых событий. Выполняет те же действия, что и в базовом шаблоне"""
        # Обработка ввода пользователем
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Если окно программы закрывается
                sys.exit()  # Завершить выполнение программы
            if event.type == pygame.MOUSEBUTTONDOWN:  # Нажатие на кнопку мыши
                self.mouse_pressed = True  # Сохраняем состояние кнопки
            if event.type == pygame.MOUSEBUTTONUP:  # Отпускание кнопки мыши
                self.mouse_pressed = False  # Сохраняем состояние кнопки
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.switch_weapon()  # При нажатии на "пробел" меняем оружие
            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:  # При зажатии кнопки "s" активируется "стазис"
                self.timed_abilities["Stasis"].active = True
                self.timed_abilities["Stasis"].sound.play()
            if event.type == pygame.KEYUP and event.key == pygame.K_s:  # При отпускании кнопки происходит деактивация
                self.timed_abilities["Stasis"].active = False
                self.timed_abilities["Stasis"].sound.stop()

        # Обработка выстрелов игроком
        # Если кнопка нажата и с последнего выстрела прошло больше fire_rate секунд... (контроль скорости стрельбы)
        if self.mouse_pressed and \
                (time.time() - self.starship.last_bullet_time) > self.weapons[self.weapon_type].fire_rate and \
                self.weapons[self.weapon_type].ammo > 0:
            # Создание новых пуль заданного типа (выстрел)
            new_bullets = self.starship.fire(pygame.mouse.get_pos(), BULLET_SPEED,
                                             self.max_bullets, self.weapons[self.weapon_type].type)
            self.bullets.add(*new_bullets)  # Добавление пуль в игру
            self.weapons[self.weapon_type].ammo -= 1  # Обновление боезапаса

        # Обработка выстрелов врагами
        for enemy in self.enemies:
            # Для врагов также соблюдается темп огня, кроме того их пули не могут двигаться во время действия "стазиса"
            if time.time() - enemy.last_bullet_time > enemy.fire_rate and not self.timed_abilities["Stasis"].active:
                # Для каждого типа врагов пули имеют заданные свойства (скорость и их количество)
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
                self.enemy_bullets.add(*new_bullets)  # Добавление пуль в игру

        # Спавн игровых объектов
        if not self.timed_abilities["Stasis"].active:  # Во время действия "стазиса" новые объекты не появляются
            if frame % ASTEROIDS_SPAWN_RATE == 0:  # Каждый ASTEROIDS_SPAWN_RATE кадр
                self.cast_asteroid()  # Создаём астероид
            # Каждый 700 кадр появляются обычные враги или босс (в зависимости от счёта)
            if frame % ENEMY_SPAWN_RATE == 0 and frame != 0:
                if self.score < self.score_trigger:
                    self.spawn_enemy("normal")
                else:
                    self.spawn_enemy("boss")
                    self.score_trigger += SCORE_TRIGGER

    def boosters_manager(self, frame: int):
        """Метод - обработчик всех событий с бустерами в т.ч. столкновений.
        В игре есть 3 вида "бустеров": временно активируемые при подборе, боеприпасы для оружия и заряды способностей.
        Каждый из них обрабатывается отдельно, так как оно имеют различное поведение"""
        # Активация бустеров
        hits = spritecollide(self.starship, self.boosters, False)  # Детектирование столкновений с бустером
        for booster in hits:
            booster_type = booster.type
            if booster_type in self.boosters_timeouts:
                self.timed_booster_handler(booster_type)  # Обработка бустеров активируемых при подборе
            elif booster_type in self.weapons:
                self.weapons_handler(booster_type)  # Обработка подбора боеприпасов для оружия
            elif booster_type in self.timed_abilities:
                self.booster_handlers[booster_type]("activate")  # Обработка подобранных зарядов способностей
            booster.pickup_sound.play()  # Проигрывание звука, ассоциированного с бустером определённого типа
            booster.kill()  # Удаление бустера из игры

        # Деактивация бустеров
        for booster_type, timeout in self.boosters_timeouts.items():
            # Если бустер активен (timeout > 0), но активное время закончилось (time.time() > timeout)...
            if time.time() > timeout > 0:
                self.boosters_timeouts[booster_type] = 0  # задаём время деактивации равным 0 (отключённое состояние)
                self.booster_handlers[booster_type]("deactivate")  # деактивируем бустер (возвращаем исходное поведение)
        for booster_type, weapon in self.weapons.items():
            # Обработка данных событий не требуется, но присутствует для сохранения совместимости
            if weapon.ammo <= 0:
                self.weapons[booster_type].ammo = 0
                self.booster_handlers[booster_type]("deactivate")
        for booster_type, ability in self.timed_abilities.items():
            status = self.timed_abilities[booster_type].active
            if ability.amount <= 0 and status:  # Если "боезапас" способности закончился, но она ещё активна
                self.timed_abilities[booster_type].active = False  # Деактивируем способность
                self.timed_abilities[booster_type].amount = 0  # Обнуляем боезапас
                self.timed_abilities[booster_type].sound.stop()  # Отключаем звук способности
            elif ability.amount > 0 and status:  # Уменьшаем боезапас на каждой итерации
                self.timed_abilities[booster_type].amount -= status

        # Спавн бустеров
        if frame % BOOSTER_SPAWN_RATE == 0 and frame != 0:
            self.boosters.add(Booster())  # ...размещаем новый бустер на игровом поле

    def timed_booster_handler(self, booster_type: str):
        """Обработка бустеров, активируемых при подборе"""
        if self.boosters_timeouts[booster_type] == 0:  # Если бустер неактивен (timeout = 0)
            # Задаётся новое время отключения через BOOSTER_DURATION секунд
            self.boosters_timeouts[booster_type] = time.time() + BOOSTER_DURATION
            self.booster_handlers[booster_type]("activate")  # Частичная активация эффекта бустера
        elif self.boosters_timeouts[booster_type] > 0:  # Если бустер уже активен
            self.boosters_timeouts[booster_type] += BOOSTER_DURATION  # Увеличиваем время до деактивации

    def weapons_handler(self, booster_type: str):
        """Обработчик подбора боеприпасов для оружия"""
        if self.weapons[booster_type].ammo == 0:
            self.booster_handlers[booster_type]("activate")  # Активация (показ подсказки при 1 подборе)
        self.weapons[booster_type].ammo += BOOSTER_AMMO_GAIN

    @staticmethod
    def update_objects(sprite_groups: list):
        """Обновить игровые объекты"""
        for sprite_group in sprite_groups:
            sprite_group.update()

    @staticmethod
    def update_enemies(enemies: pygame.sprite.RenderPlain, player: pygame.sprite.Sprite):
        """Обновить врагов (перемещение в сторону игрока)"""
        enemies.update(player)

    @staticmethod
    def draw_enemies(enemies: pygame.sprite.RenderPlain, screen: pygame.Surface):
        """Отрисовка врагов и их полос здоровья"""
        enemies.draw(screen)
        for enemy in enemies:
            enemy.draw_health_bar(screen)

    def draw(self, player: pygame.sprite.RenderPlain, sprite_groups: list,
             enemies: pygame.sprite.RenderPlain, debug: bool = False):
        """Метод отрисовки объектов. Переносит на игровое поле все объекты переданные ему внутри аргумена
        objects_list """
        self.screen.fill(BG_COLOR)  # Залить экран одним цветом (необходимо для корректной отрисовки каждого кадра)
        player.draw(self.screen)  # Отрисовка игрока
        for sprite_group in sprite_groups:
            sprite_group.draw(self.screen)  # Отрисовка всех объектов кроме игрока и врагов
        self.draw_enemies(enemies, self.screen)  # Отрисовка врагов
        player.sprites()[0].draw_health_bar(self.screen)  # Отрисовка полосы здоровья игрока
        if debug:  # Дебаг режим позволяет отобразить хитбоксы всех объектов в игре
            pygame.draw.rect(self.screen, (255, 0, 0), self.starship.rect, 3)
            for asteroid in self.asteroids.sprites():
                pygame.draw.rect(self.screen, (0, 255, 0), asteroid.rect, 3)
            for bullet in self.bullets.sprites():
                pygame.draw.rect(self.screen, (0, 0, 255), bullet.rect, 3)
            for enemy in self.enemies.sprites():
                pygame.draw.rect(self.screen, (255, 0, 255), enemy.rect, 3)
            for booster in self.boosters.sprites():
                pygame.draw.rect(self.screen, (255, 255, 0), booster.rect, 3)

    def handle_collisions(self):
        """Метод обрабатывает все столкновения в игре (кроме бустеров).
        Возвращает True в случае столкновения, которое должно привести к концу игры, иначе False"""
        # Обработка столкновений пуль
        for bullet in self.bullets.sprites():
            # Обработка выхода пуль за игровое поле
            if bullet.pos[0] > SCREEN_SIZE[0] or bullet.pos[1] > SCREEN_SIZE[1] or (bullet.pos < 0).any():
                bullet.kill()  # Уничтожить пулю

            # Обработка столкновений пуль с астероидами
            # Детектирование столкновений. Здесь используются битовые маски объектов,
            # данный подход снижает производительность, но обеспечивает максимально точное детектирование столкновений
            hits = [ast for ast in self.asteroids if collide_mask(bullet, ast)]
            if hits:
                for asteroid in hits:
                    fragments = asteroid.explode()  # Разбиваем астероид на осколки
                    self.score += 1  # Начисляем очки игроку
                    asteroid.kill()  # Уничтожаем начальный астероид
                    self.asteroids.add(fragments)  # Вводим в игру осколки начального астероида
                if bullet.type == "explosive":
                    self.explosions.add(bullet.explode())  # Взрываем пулю, если она взрывающаяся
                bullet.kill()  # Уничтожаем пулю

            # Обработка столкновений пуль с врагами
            hits = spritecollide(bullet, self.enemies, False)  # Детектирование столкновений
            if hits:
                for enemy in hits:
                    if not enemy.damage():  # True если у врага осталось 0 HP, вызов метода damage наносит урон врагу
                        self.score += enemy.score_gain  # Увеличиваем счёт за убийство
                        enemy.kill()  # Уничтожаем врага
                if bullet.type == "explosive":
                    self.explosions.add(bullet.explode())
                bullet.kill()

        # Обработка столкновений вражеских пуль
        for en_bullet in self.enemy_bullets.sprites():
            # Обработка выхода вражеских пуль за игровое поле
            if en_bullet.pos[0] > SCREEN_SIZE[0] or en_bullet.pos[1] > SCREEN_SIZE[1] or (en_bullet.pos < 0).any():
                en_bullet.kill()

            # Обработка столкновений вражеских пуль с астероидами
            hits = [ast for ast in self.asteroids if collide_mask(en_bullet, ast)]
            if hits:
                for asteroid in hits:
                    fragments = asteroid.explode()
                    asteroid.kill()
                    self.asteroids.add(fragments)
                en_bullet.kill()

            # Обработка столкновений вражеских пуль с игроком
            if collide_mask(en_bullet, self.starship):  # Детектирование столкновения
                if self.boosters_timeouts["Shield"] == 0 and self.starship.damage_animation_timeout == 0:
                    # Нанести урон игроку + анимация попадания (во время нее игрок неуязвим)
                    return self.starship.damage()

        # Обработка столкновений с взрывами
        for explosion in self.explosions.sprites():  # Перебор всех взрывов в игре на данный момент
            hits = spritecollide(explosion, self.asteroids, dokill=True)  # Взрывы мгновенно разрушают любые астероиды
            self.score += len(hits)
            spritecollide(explosion, self.enemy_bullets, dokill=True)  # Взрывы разрушают вражеские пули
            hits = spritecollide(explosion, self.enemies, dokill=False)  # Детектирование попаданий во врагов
            if hits:
                for enemy in hits:
                    # True если у врага осталось 0 HP. -1/16 HP за каждый кадр контакта со взрывом
                    if not enemy.damage(1 / 16):
                        self.score += enemy.score_gain  # Начисление очков за убийство врага
                        enemy.kill()  # Уничтожение врага
            spritecollide(explosion, self.boosters, dokill=True)  # Взрывы разрушают не подобранные бустеры

        # Обработка столкновений астероидов и игрока
        hits = [ast for ast in self.asteroids if collide_mask(self.starship, ast)]  # Детектирование столкновения
        if hits:
            # Если бустер "Щит" активен
            if self.boosters_timeouts["Shield"] > 0:
                [ast.kill() for ast in hits]  # Мнгновенно уничтожить астероиды
            # Если анимация попадания активна, то игрок неуязвим
            elif self.starship.damage_animation_timeout != 0:
                pass
            else:
                # Нанесение урона игроку + анимация попадания. Возвращает True если осталось 0 HP
                return self.starship.damage()
        return False

    def cast_asteroid(self):
        """Создаёт астероид и добавляет его в игру"""
        new_asteroid = Asteroid()  # Создаём астероид
        self.asteroids.add(new_asteroid)  # Добавляем его в список всех астероидов

    def spawn_enemy(self, strength: str):
        """Создаёт врагов заданного типа на игровом поле"""
        # Здесь в new_enemy может быть сохранён босс, поэтому он добавляется отдельно
        new_enemy = Enemy(strength=strength)
        new_enemies = [new_enemy]
        if new_enemy.type == "type_3":
            new_enemies += [Enemy("type_3") for _ in range(5)]
        elif new_enemy.type == "type_1":
            new_enemies += [Enemy("type_1") for _ in range(2)]
        self.enemies.add(*new_enemies)  # Добавить созданных врагов в игру

    def rapid_fire(self, mode: str):
        """Обработчик бустера, увеличивающего темп огня"""
        if mode == "activate":  # Если бустер нужно активировать...
            self.weapons[self.weapon_type].fire_rate /= RAPID_FIRE_MULTIPLIER
        elif mode == "deactivate":  # Если бустер нужно отключить...
            self.weapons[self.weapon_type].fire_rate *= RAPID_FIRE_MULTIPLIER

    def shield(self, mode: str):
        """Обработчик бустера, дающего щит"""
        if mode == "activate":
            # При активации подменяем оригинальную картинку звездолёта на картинку с щитком
            self.starship.original_image = pygame.image.load(os.path.join("images", "Starship_with_shield.png"))
        elif mode == "deactivate":
            # При деактивации возвращаем исходную картинку на место
            self.starship.original_image = pygame.image.load(os.path.join("images", "starship.png"))

    # TODO. Переименовать метод, так как игра позволяет делать более 3 пуль. Например, "multiple_bullets"
    def triple_bullets(self, mode: str):
        """Обработчик бустера, увеличивающего количество одновременно выстреливаемых пуль"""
        if mode == "activate":  # При активации...
            self.max_bullets = MAX_BULLETS  # изменить кол-во пуль, которые звездолёт выстреливает за 1 раз на 3
        elif mode == "deactivate":  # При деактивации...
            self.max_bullets = DEFAULT_MAX_BULLETS  # вернуть значение обратно

    def stasis(self, mode: str):
        """Обработчик способности, позволяющий остановить все движущиеся объекты кроме пуль и игрока"""
        current_amount = self.timed_abilities["Stasis"].amount  # "Боезапас" способности
        if mode == "activate" and current_amount < MAXIMUM_STASIS_AMMO:  # Максимальный заряд "стазиса"
            self.gui.activate_stasis_hint()  # Вывести подсказку по использованию
            if MAXIMUM_STASIS_AMMO - current_amount < STASIS_AMMO_GAIN:  # Обработка выхода за максимальное количество
                self.timed_abilities["Stasis"].amount = MAXIMUM_STASIS_AMMO
            else:
                self.timed_abilities["Stasis"].amount += STASIS_AMMO_GAIN

    def health(self, mode: str):
        """Обработчик бустера, восстанавливающего здоровье"""
        if mode == "activate":
            # Обработка выхода за максимальное количество HP
            if (diff := self.starship.max_hp - self.starship.hp) <= BOOSTER_HP_GAIN:
                self.starship.hp += diff  # Начисление очков здоровья
            else:
                self.starship.hp += BOOSTER_HP_GAIN  # Начисление очков здоровья
        elif mode == "deactivate":
            pass

    def explosive_bullets(self, mode: str):
        """Обработчик подбора взрывных боеприпасов"""
        if mode == "activate":
            self.gui.activate_weapon_switch_hint()  # Вызов подсказки по смене оружия
        elif mode == "deactivate":
            pass

    def run(self):
        """Главный цикл программы. Вызывается 1 раз за игру"""
        frame = 0  # Счётчик кадров для планирования игровых событий (удобнее работать, чем с временем)
        clock = pygame.time.Clock()  # Ограничитель FPS
        while True:
            clock.tick(MAX_FPS)  # Ограничение FPS. Напрямую влияет на скорость игры. Рекомендованная величина - 60
            self.handle_events(frame)  # Обработка событий
            self.boosters_manager(frame)  # Обработка подбора и эффектов бустеров
            self.update_objects([self.starship, self.bullets])  # Перемещение игрока и пуль
            # Если способность "стазис" активна, то обновления остальных объектов не происходит
            if not self.timed_abilities["Stasis"].active:
                self.update_objects([self.enemy_bullets, self.asteroids, self.explosions])
                self.update_enemies(self.enemies, self.starship)
            # Отрисовка всех объектов
            self.draw(RenderPlain(self.starship), [self.boosters, self.bullets, self.enemy_bullets, self.asteroids,
                                                   self.explosions], enemies=self.enemies, debug=False)
            # Обновление GUI
            self.gui.update(self.score, self.weapon_type, self.weapons, self.timed_abilities)
            pygame.display.update()
            if self.handle_collisions():  # Обработка столкновений (если у игрока осталось 0 HP, то конеу игры)
                self.gui.game_over()
                return
            frame += 1


class Starship(Sprite):
    """Класс представляющий игрока"""

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.pos = np.array([SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2])  # Координаты центра игрока
        self.original_image = pygame.image.load(os.path.join("images", "starship.png"))  # Неизменеямая картинка игрока
        # Модель игрока при получении урона
        self.damage_image = pygame.image.load(os.path.join("images", "starship_damage.png"))
        self.to_transform_image = self.original_image
        self.image = self.original_image  # Отображаемая картинка
        # Битовая маска картинки (нужна для точных расчётов столкновений)
        self.mask = pygame.mask.from_surface(self.image)
        # Хитбокс объекта также нужен для расчёта столкновений
        self.rect = self.image.get_rect(center=self.pos)
        self.speed = 0  # Скорость игрока
        self.max_hp = MAX_HP  # Максимальное количество очков здоровья (HP)
        self.hp = self.max_hp  # Текущее количество очков здоровья
        self.damage_animation_timeout = 0  # Оставшееся время анимации попадания (в кадрах). 0 - анимация неактивна
        self.last_bullet_time = 0  # Время последнего выстрела, необходимо для ограничения темпа огня.

    def update(self):
        """Обновить объект игрока (перемещение + анимация попадания)"""
        self.animate_damage()
        self.move()

    def animate_damage(self):
        """Анимация попадания в игрока пулей или астероидом"""
        if time.time() < self.damage_animation_timeout:  # Если время деактивации анимации ещё не наступило
            self.to_transform_image = self.damage_image  # Подменим картинку игрока
        elif time.time() > self.damage_animation_timeout:  # Если пришло время деактивировать анимацию
            self.damage_animation_timeout = 0  # Обнуляем время деактивации
            self.to_transform_image = self.original_image  # Возвращаем картинку обратно

    def damage(self, d: int = BASE_DAMAGE):
        """Наносит урон "d" игроку. Возвращает True при достижении 0 HP. Запускает анимацию попадания."""
        self.hp -= d
        # Запуск анимации попадания на 0.3 секунды (со след. кадра)
        self.damage_animation_timeout = time.time() + INVULNERABILITY_PERIOD
        return self.hp <= 0

    def draw_health_bar(self, screen: pygame.Surface):
        """Отрисовка полосы здоровья игрока"""
        # Расчёт ширины полосы как доли текущего здоровья от максимального.
        current_width = (self.original_image.get_width() + 10) / self.max_hp * self.hp
        pygame.draw.rect(screen, (0, 200, 0), [*self.rect.topleft, current_width, 5])  # Отрисовка прямоугольника

    def move(self):
        """Перемещение игрока к курсору мыши. Чем дальше курсор находится от игрока, тем выше скорость передвижения"""
        mouse_pos = np.array(pygame.mouse.get_pos())  # Получение координат курсора
        direction = mouse_pos - self.pos  # Вычисление вектора направления
        angle = self._calculate_angle(mouse_pos)  # Расчёт угла поворота к курсору
        self.speed = direction / SHIP_SPEED  # Расчёт вектора скорости (нормализация вектора направления)
        self.pos += self.speed  # Изменение координат игрока в соответствии с вектором скорости
        self.image = pygame.transform.rotate(self.to_transform_image, int(angle))  # Поворот изображения игрока
        self.mask = pygame.mask.from_surface(self.image)  # Обновление битовой маски в связи с поворотом картинки
        self.rect = self.image.get_rect(center=self.pos)  # Обновление хитбокса в связи с появлением нового центра

    def _calculate_angle(self, mouse_pos: np.ndarray):
        """Расчёт необходимого угла поворота картинки игрока в сторону курсора"""
        rel_x, rel_y = mouse_pos - self.pos  # x и у составляющие вектора направления
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90  # Расчёт угла (в градусах)
        return angle

    def fire(self, target_pos: Union[np.ndarray, Tuple],
             rel_speed: np.ndarray, bullet_num: int, bullet_type: str = "normal"):
        """Создание пуль при выстреле с заданными свойствами"""
        self.last_bullet_time = time.time()  # Сохраняем время последнего выстрела
        new_bullets = []  # Создаём список, куда поместим все новые пули
        for i in range(bullet_num):  # Заданное количество раз...
            if bullet_num == 1:  # В случае одной пули...
                angle_offset = 0  # ...зададим смещение относительно направления взгляда равным 0
            else:  # Иначе...
                angle_offset = -15 + 30 / (bullet_num - 1) * i  # ..расчитаем смещения для всех пуль
            new_bullets.append(Bullet(self.pos.copy(), target_pos, rel_speed, angle_offset, bullet_type))

        if isinstance(self, Enemy):  # Если выстрел производит враг (Enemy, наследник Starship)
            new_bullets[0].enemy_launch_sound.play()  # Проиграть звук выстрела врага
        else:
            new_bullets[0].launch_sound.play()  # Иначе воспроизвести звук выстрела игрока
        return new_bullets  # Возвращаем список из созданных пуль (список из 1 элемента по-умолчанию)


@dataclass
class EnemyType:
    """Класс необходимый для создания уникальных типов врагов с разными характеристиками"""
    type_: str  # Название типа
    strength: str  # Сила. Принимает значения "boss" или "normal"
    original_image: pygame.Surface
    damage_image: pygame.Surface
    rel_speed: float  # Модификатор скорости
    hitbox: Tuple[int, int]  # Размеры хитбокса
    hp: int  # Количество очков здоровья
    fire_rate: float  # Темп огня (пауза между выстрелами в секундах)
    max_bullets: int  # Кол-во выстреливаемых пуль
    score_gain: int  # Кол-во очков, получаемых за уничтожение врага


class Enemy(Starship):
    """Класс представляющий врага, наследуется от Starship, так как имеет очень сходное поведение"""
    # Описание возможных вариантов врагов
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

    def __init__(self, type_: str = "random", strength: str = "normal"):
        super(Enemy, self).__init__()
        # Враги вылетают из-за границы игрового поля так же как и астероиды, поэтому здесь используются методы
        # класса Asteroid для генерации начальной позиции
        self.pos = random.choice([Asteroid._left_pos, Asteroid._top_pos,  # Генерируем случайную начальную позицию
                                  Asteroid._right_pos, Asteroid._bottom_pos])()
        subset = list(filter(lambda x: x.strength == strength, self.variants))  # Отбираем всех врагов с заданной силой
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
        # Звук попадания во врага
        self.damage_sound = pygame.mixer.Sound(os.path.join("sounds", "explosion_enemy_1.wav"))
        # Звук убийства врага
        self.kill_sound = pygame.mixer.Sound(os.path.join("sounds", "explosion_enemy_1.wav"))

    def update(self, player: pygame.sprite.Sprite):
        """Обновить врага (анимация, перемещение, вращение)"""
        self.animate_damage()
        self.rotate(player)
        self.move(player)

    def rotate(self, player: pygame.sprite.Sprite):
        angle = self._calculate_angle(player.pos)
        self.image = pygame.transform.rotate(self.to_transform_image, int(angle))
        self.mask = pygame.mask.from_surface(self.image)

    def animate_damage(self):
        if time.time() < self.damage_animation_timeout:
            self.to_transform_image = self.damage_image
        elif time.time() > self.damage_animation_timeout:
            self.damage_animation_timeout = 0
            self.to_transform_image = self.original_image

    def move(self, player: pygame.sprite.Sprite):
        direction = player.pos - self.pos  # Враг движется к игроку, а не к курсору
        self.speed = direction / max(abs(direction)) * self.rel_speed
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)

    def damage(self, d: int = BASE_DAMAGE):
        self.hp -= d
        self.damage_animation_timeout = time.time() + ENEMY_INVULNERABILITY_PERIOD
        if status := self.hp > 0:
            return status
        else:
            self.kill_sound.play()
            return status

    def draw_health_bar(self, screen: pygame.Surface):
        """Отрисовка полосы здоровья, отличается у обычных врагов и боссов"""
        screen_size = screen.get_size()
        if self.strength == "boss":
            # У боссов полоса здоровья занимает почти всё ширину экрана сверху
            current_width = (screen_size[0] - 20) / self.max_hp * self.hp
            pygame.draw.rect(screen, (200, 0, 0), [10, 10, current_width, 20])
        elif self.strength == "normal":
            current_width = (self.w + 10) / self.max_hp * self.hp
            pygame.draw.rect(screen, (200, 0, 0), [*self.rect.topleft, current_width, 5])


@dataclass
class BulletType:
    """Класс для создания уникальных объектов пуль с заданными картинками и звуками"""
    type: str  # Название типа пули
    original_image: pygame.Surface
    launch_sounds: List[Union[pygame.mixer.Sound, None]]  # Звуки запуска пули игроком (желательно несколько вариантов(
    enemy_launch_sounds: List[Union[pygame.mixer.Sound, None]]  # Звуки запуска пули врагом (также несколько вариантов)
    hit_sounds: List[Union[pygame.mixer.Sound, None]]  # Звуки попадания
    explosion_sounds: List[Union[pygame.mixer.Sound, None]]  # Звуки взрыва


class Bullet(Sprite):
    """Класс на основе которого создаётся объекты пуль"""
    # Объектов класса Bullet будет создаваться довольно много, поэтому мы хотим загрузить картинку только 1 раз
    # Возможные варианты типов пуль
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

    def __init__(self, pos: np.ndarray, target_pos: np.ndarray, rel_speed: np.ndarray,
                 angle_offset: float = 0, type_: str = "normal"):
        pygame.sprite.Sprite.__init__(self)
        self.type = type_  # Тип пули (описаны в атрибуте класса variants)
        self.setup = self.bullet_types[self.type]  # Объект типа пули
        self.original_image = self.setup.original_image
        self.pos = pos
        self.direction = target_pos - pos
        asr = math.pi / 180 * angle_offset  # Угол поворота пули в радианах (при выстреле нескольких пуль, иначе 0)
        # Поворот вектора направления полёта пули
        self.direction[0] = self.direction[0] * math.cos(asr) - self.direction[1] * math.sin(asr)
        self.direction[1] = self.direction[0] * math.sin(asr) + self.direction[1] * math.cos(asr)
        # Вычисление постоянной скорости с учётом модификатора "rel_speed"
        self.speed = self.direction / max(abs(self.direction)) * rel_speed
        self.angle = self._calculate_angle(target_pos) - angle_offset  # Расчёт угла поворота
        # Поворот картинки (так как пуля летит прямо, мы делаем это только 1 раз)
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
        """Взрывает пулю и возвращает объект взрыва"""
        self.explosion_sound.play()
        return ExplosionAnimation(self.pos.copy())

    def _calculate_angle(self, target_pos: np.ndarray):
        rel_x, rel_y = target_pos - self.pos
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90
        return angle


class Asteroid(Sprite):
    """Класс для создания объектов астероидов"""
    # Оригинальные картинки астероидов
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

    def __init__(self, pos: np.ndarray = None, speed: np.ndarray = None, ast_type: str = None):
        pygame.sprite.Sprite.__init__(self)
        # Если координаты, скорость и тип заданы...
        if (pos is not None) and (speed is not None) and (ast_type is not None):
            self.init_asteroid_fragment(pos, speed, ast_type)  # ...инициализировать осколок
        else:  # Иначе (координаты, скорость и тип НЕ заданы)...
            self.init_rand_asteroid()  # ...инициализировать обычный астероид
        self.angle = 0  # Угол поворота астероида
        self.angle_inc = random.uniform(-2, 2)  # Величина изменения угла поворота астероида
        self.explosion_sound = pygame.mixer.Sound(os.path.join("sounds", "explosion_1.wav"))  # Звук взрыва астероидов

    def init_asteroid_fragment(self, pos: np.ndarray, speed: np.ndarray, ast_type: str):
        """Метод инициализирует осколок астероида, принимая на вход его координаты (pos), скорость (speed) и тип (
        ast_type) """
        # Отбираем только картинки с астероидами заданного типа
        ast_type_variants = list(filter(lambda x: x[0] == ast_type, self.ast_variants))
        # Берём случайную картинку астероида заданного типа
        self.type, self.original_image = random.choice(ast_type_variants)
        self.pos = pos  # Координаты осколка задаём НЕ случайно
        self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=self.pos)
        self.speed = speed  # Задаём направление (скорость) НЕ случайно

    def init_rand_asteroid(self):
        """Метод инициализирует обычный астероид случайными типом и координатам"""
        # Случайный выбор типа и картинки астероида
        self.type, self.original_image = random.choice(self.ast_variants)
        self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.pos = random.choice([self._left_pos, self._top_pos,  # Генерируем случайную начальную позицию
                                  self._right_pos, self._bottom_pos])()
        # Получаем хитбокс с заданными размерами
        self.rect = self.image.get_rect(center=self.pos)
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
        """Генерация вектора скорости с небольшим сдвигом от изначального направления"""
        # Уменьшаем скорость в 2 раза и изменяем её составляющие по x и y на небольшую величину
        offset = self.speed * FRAGMENTS_SPEED + np.random.uniform(-0.5, 0.5, 2)
        return offset

    def pos_offset(self):
        """Генерация позиции с нембольшим сдвигом от изначального положения"""
        # Возвращаем немного смещённые координаты центра астероида
        offset = self.pos + np.random.uniform(-10, 10, 2)
        return offset

    def check_borders(self):
        """Обработчик выхода астероидов за границы игрового поля.
        Астереиды не уничтожаются, а появляются с противоположной стороны игрового поля"""
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

    def explode(self):
        """Взрыв астероида. Функция возвращает список астероидов-осколков"""
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
        self.explosion_sound.play()  # Воспроизвести звук взрыва астероида
        return fragments


@dataclass
class BoosterType:
    """Класс для создания типов бустеров."""
    type: str
    original_image: pygame.Surface
    pickup_sound: pygame.mixer.Sound  # Звук подбора бустера


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
        # Выбор случайного типа бустера
        self.setup = self.booster_types[random.choice(list(self.booster_types.keys()))]
        self.type = self.setup.type
        self.image = self.setup.original_image
        self.mask = pygame.mask.from_surface(self.image)
        # Генерация случайных координат для бустера
        # Отступы в 100 пикселей необходимы для более простого взаимодействия с ними вблизи границы игрового поля
        self.pos = np.array([random.randint(100, SCREEN_SIZE[0] - 100),
                             random.randint(100, SCREEN_SIZE[1] - 100)])
        self.rect = self.image.get_rect(center=self.pos)  # Получение хитбокса бустера
        self.pickup_sound = self.setup.pickup_sound


class ExplosionAnimation(Sprite):
    """Класс для создания анимаций взрыва пуль.
    Изображения для анимации сохранены в отдельной папке и все загружаются в атрибут "original_images" """
    original_images = [pygame.image.load(os.path.join("images", "explosion_animation", file)) for file in
                       sorted(os.listdir(os.path.join("images", "explosion_animation")))]

    def __init__(self, center: np.ndarray):
        Sprite.__init__(self)
        self.center = center
        self.current_idx = 0  # Текущий кадр анимации
        self.image = self.original_images[self.current_idx]  # Изображение текущего кадра
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        """Обновление анимации"""
        self.current_idx += 1  # Переход на следующий кадр
        if self.current_idx < len(self.original_images):  # Если анимация ещё не закончилась
            self.image = self.original_images[self.current_idx]  # Получаем новое изображение
            self.rect = self.image.get_rect(center=self.center)  # Получаем новый хитбокс
            self.mask = pygame.mask.from_surface(self.image)  # Получаем новую битовую маску
        else:  # Если анимация закончилась
            self.kill()  # Удалить её


# Межигровой цикл. Каждая итерация цикла соответствует одной завершённой игре (т.е. состоянием "game over")
while True:
    game = Game(game_screen)  # Создание и запуск игры
    game.run()
