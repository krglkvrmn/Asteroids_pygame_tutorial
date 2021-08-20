# Шаг 1. Добавление столкновений
import sys  # Модуль sys понадобится нам для закрытия игры
import os  # Модуль os нужен для работы с путями и файлами
import pygame  # Модуль pygame для реализации игровой логики
import numpy as np  # Модуль numpy нужен для поэлементного сложения векторов
import math  # Модуль math будет полезен для вычисления угла наклона звездолёта
import time  # Модуль time нужен для замера времени
import random  # Модуль random нужен для генерации случайных чисел

# Инициализация модуля pygame
pygame.init()
# Цвет фона в формате RGB (красный, синий, зелёный). (0, 0, 0) - чёрный цвет.
BG_COLOR = (0, 0, 0)
# Объект дисплея (0, 0) - полный экран, если задать (800, 600), то окно будет размером 800х600 пикселей
screen = pygame.display.set_mode((600, 500), pygame.RESIZABLE)
# Получим ширину и высоту игрового поля из объекта screen и сохраним в глобальную переменную.
# Мы будем использовать SCREEN_SIZE очень часто!
SCREEN_SIZE = screen.get_size()


class Game:
    """Основной класс игры. В нём представлены основные методы для управления игровыми объектами, а также сами
    объекты """

    def __init__(self, screen):
        self.screen = screen
        self.starship = Starship()  # Объект класса Starship (игрок)
        self.bullets = []  # Хранение объектов пуль (Bullet)
        self.asteroids = []  # Заготовка для хранения объектов астероидов
        # Выбор цветов для дебаг режима по типу объекта
        self.color_picker = {Starship: (0, 255, 0), Bullet: (0, 0, 255), Asteroid: (255, 0, 0)}
        self.mouse_pressed = False  # Cохраняет состояние кнопки мыши
        self.fire_rate = 0.2  # Пауза между выстрелами (в секундах)

    def handle_events(self, frame):
        """Метод - обработчик событий. Выполняет те же действия, что и в базовом шаблоне"""
        # Цикл обработки событий (нажатия кнопок, движения мыши и т.д.)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Нажатие на "Х" на окне программы.
                sys.exit()  # Выход из программы
            if event.type == pygame.MOUSEBUTTONDOWN:  # Нажатие на кнопку мыши
                self.mouse_pressed = True  # Сохраняем состояние кнопки
            if event.type == pygame.MOUSEBUTTONUP:  # Отпускание кнопки мыши
                self.mouse_pressed = False  # Сохраняем состояние кнопки
        # Если кнопка нажата и с последнего выстрела прошло больше self.fire_rate секунд...
        if self.mouse_pressed and (time.time() - self.starship.last_bullet_time) > self.fire_rate:
            new_bullet = self.starship.fire()  # ...создать новую пулю...
            self.bullets.append(new_bullet)  # ...и добавить её в список всех пуль
        if frame % 25 == 0:  # Каждый 25 кадр
            self.cast_asteroid()  # Создаём астероид

    def move_objects(self, objects_list):
        for objects in objects_list:  # Перебор групп объектов (asteroids, bullets)
            for obj in objects:  # Перебор объектов внутри групп
                obj.move()  # Перемещение объекта

    def draw(self, objects_list, debug=False):
        """Метод отрисовки объектов. Переносит на игровое поле все объекты переданные ему внутри аргумента
        objects_list """
        screen.fill(BG_COLOR)  # Заливка экрана чёрным цветом
        for objects in objects_list:  # Перебираем типы объектов (корабль, пули, астероиды и т.д.)
            for obj in objects:  # Перебираем сами объекты
                self.screen.blit(obj.image, obj.rect)  # Рисуем изображение объекта на экране
        if debug:  # Дебаг режим позволяет отобразить хитбоксы всех объектов
            for objects in objects_list:
                for obj in objects:
                    # Отрисовка прямоугольника c цветом, соответствующим типу переменной
                    pygame.draw.rect(self.screen, self.color_picker[type(obj)], obj.rect, 2)
        pygame.display.update()  # Применение изменений

    def check_collisions(self):
        # Удаление пуль при вылете с игрового поля
        asteroids_rects = [ast.rect for ast in self.asteroids]  # Хитбоксы всех астероидов
        for idx, bullet in enumerate(self.bullets):  # Для каждой пули в игре...
            if bullet.pos[0] > SCREEN_SIZE[0] or bullet.pos[1] > SCREEN_SIZE[1] or (
                    bullet.pos < 0).any():  # ...если центра пули вышел за границы
                del self.bullets[idx]  # удалить объект пули
        # Разрушение астероидов при контакте с пулями
        for idx, bullet in enumerate(self.bullets):
            # С каким из астероидов имеется столкновение?
            hit = bullet.rect.collidelist(asteroids_rects)
            if hit != -1:  # Если столкновение есть...
                del self.asteroids[hit]  # ...удалить астероид с индексом hit
                del self.bullets[idx]  # ...удалить пулю с индексом idx
        # Столкновение астероидов и игрока
        # Индекс астероида, столкнувшегося с игроком
        hit = self.starship.rect.collidelist(asteroids_rects)
        if hit != -1:  # Если столкновение было...
            sys.exit()  # ...выйти из игры      

    def cast_asteroid(self):
        new_asteroid = Asteroid()  # Создаём астероид
        self.asteroids.append(new_asteroid)  # Добавляем его в список всех астероидов

    def run(self):
        """Главный цикл программы. Вызывается 1 раз за игру"""
        frame = 0
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            self.handle_events(frame)
            self.check_collisions()
            self.move_objects([[self.starship], self.bullets, self.asteroids])
            self.draw([[self.starship], self.bullets, self.asteroids], debug=True)
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
        angle = self.calculate_angle(mouse_pos)  # Расчёт угла наклона корабля
        self.speed = direction / 40  # Новое значение скорости
        self.pos += self.speed  # Движение - обновление координат
        self.image = pygame.transform.rotate(self.original_image, int(angle))  # Вращение картинки
        self.rect = self.image.get_rect(center=self.pos)  # Перемещение хитбокса

    def calculate_angle(self, mouse_pos):
        rel_x, rel_y = mouse_pos - self.pos  # x и у составляющие вектора направления
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90  # Расчёт угла
        return angle

    def fire(self):
        self.last_bullet_time = time.time()  # Сохраняем время последнего выстрела
        return Bullet(self.pos.copy())  # Создание новой пули на том же месте где находится игрок


class Bullet:
    # Объектов класса Bullet будет создаваться довольно много, поэтому мы
    # хотим загрузить картинку толлько 1 раз
    original_image = pygame.image.load(os.path.join("images", "bullet.png"))

    def __init__(self, pos):
        self.pos = pos
        # Направление пули не изменяется с течением времени, поэтому его можно
        # вычислить внутри конструктора
        mouse_pos = pygame.mouse.get_pos()
        self.direction = (mouse_pos - pos)
        self.speed = self.direction / max(abs(self.direction)) * 10
        # Угол также не изменяется
        self.angle = self.calculate_angle(mouse_pos)  # Расчёт угла поворота
        # Угол не изменяется, поэтому картинку тоже можно повернуть сразу в конструкторе
        self.image = pygame.transform.rotate(self.original_image, int(self.angle))
        self.rect = self.image.get_rect(center=self.pos)  # Получение хитбокса

    def move(self):
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos)

    def calculate_angle(self, mouse_pos):
        rel_x, rel_y = mouse_pos - self.pos
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90
        return angle


class Asteroid:
    # Оригинальные картинки астероидов
    original_images = [pygame.image.load(os.path.join("images", "ast1_medium.png")),
                       pygame.image.load(os.path.join("images", "ast2_medium.png")),
                       pygame.image.load(os.path.join("images", "ast3_medium.png")),
                       pygame.image.load(os.path.join("images", "ast4_medium.png"))]

    def __init__(self):
        self.image = random.choice(self.original_images)  # Выбираем случайную картинку для астероида
        self.pos = random.choice([self.left_pos, self.top_pos,  # Генерируем случайную начальную позицию
                                  self.right_pos, self.bottom_pos])()
        self.rect = self.image.get_rect(center=self.pos)  # Получаем хитбокс
        self.direction = pygame.mouse.get_pos() - self.pos  # Вычисляем направление
        self.speed = self.direction / 300  # Расчитываем скорость

    def left_pos(self):
        """Генерация позиции слева"""
        return np.array((-150, random.uniform(0, SCREEN_SIZE[1])))

    def right_pos(self):
        """Генерация позиции справа"""
        return np.array((SCREEN_SIZE[0] + 150,
                         random.uniform(0, SCREEN_SIZE[1])))

    def top_pos(self):
        """Генерация позиции сверху"""
        return np.array((random.uniform(0, SCREEN_SIZE[0]), -150))

    def bottom_pos(self):
        """Генерация позиции снизу"""
        return np.array((random.uniform(0, SCREEN_SIZE[0]),
                         SCREEN_SIZE[1] + 150))

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
        self.rect = self.image.get_rect(center=self.pos)


game = Game(screen)  # Создание и запуск игры
game.run()
