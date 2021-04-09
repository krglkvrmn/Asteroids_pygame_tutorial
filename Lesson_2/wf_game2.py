import sys         # Модуль sys понадобится нам для закрытия игры
import os          # Модуль os нужен для работы с путями и файлами
import pygame      # Модуль pygame для реализации игровой логики   
import numpy as np # Модуль numpy нужен для поэлементного сложения векторов
import math        # Модуль math будет полезен для вычисления угла наклона звездолёта
import time        # Модуль time нужен для замера времени


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
    """Основной класс игры. В нём представлены основные методы для управления игровыми объектами, а также сами объекты"""
    def  __init__(self, screen):     
        self.screen = screen         
        self.starship = Starship()  # Объект класса Starship (игрок)
        self.bullets = []           # Хранение объектов пуль (Bullet)
        self.asteroids = []         # Заготовка для хранения объектов астероидов
        self.mouse_pressed = False  # Cохраняет состояние кнопки мыши
        self.fire_rate = 0.2        # Пауза между выстрелами (в секундах)

    def handle_events(self):
        """Метод - обработчик событий. Выполняет те же действия, что и в базовом шаблоне"""
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:  # Нажатие на кнопку мыши
                self.mouse_pressed = True             # Сохраняем состояние кнопки
            if event.type == pygame.MOUSEBUTTONUP:    # Отпускание кнопки мыши
                self.mouse_pressed = False            # Сохраняем состояние кнопки
        # Если кнопка нажата и с последнего выстрела прошло больше self.fire_rate секунд...
        if self.mouse_pressed and (time.time() - self.starship.last_bullet_time) > self.fire_rate:
            new_bullet = self.starship.fire()  # ...создать новую пулю...
            self.bullets.append(new_bullet)    # ...и добавить её в список всех пуль

    def move_objects(self, objects_list):     # Game.move_objects
        for obj_idx, _ in enumerate(objects_list):  # Перебор групп объектов (asteroids, bullets)
            for o_idx, _ in enumerate(objects_list[obj_idx]): # Перебор объектов внутри групп
                objects_list[obj_idx][o_idx].move()   # Перемещение объекта


    def draw(self, objects_list):
        """Метод отрисовки объектов. Переносит на игровое поле все объекты переданные ему внутри аргумена objects_list"""
        screen.fill(BG_COLOR)
        for objects in objects_list:
            for obj in objects:
                self.screen.blit(obj.image, obj.rect)
        pygame.display.update()

    def check_collisions(self):            # Game.check_collisions
        for idx, bullet in enumerate(self.bullets):   # Для каждой пули в игре...
            if bullet.pos[0] > SCREEN_SIZE[0] or bullet.pos[1] > SCREEN_SIZE[1] or (bullet.pos < 0).any():       # ...если центра пули вышел за границы
                del self.bullets[idx]      # удалить объект пули

    def run(self):
        """Главный цикл программы. Вызывается 1 раз за игру"""
        while True:
            self.handle_events()
            self.check_collisions()
            self.move_objects([[self.starship], self.bullets])
            self.draw([[self.starship], self.bullets])

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

    def move(self):                       # Starship.move
        mouse_pos = pygame.mouse.get_pos()    # Текущая позиция курсора мыши
        direction = mouse_pos - self.pos      # Текущее направление
        angle = self.calculate_angle(mouse_pos) # Расчёт угла наклона корабля
        self.speed = direction / 40           # Новое значение скорости
        self.pos += self.speed                # Движение - обновление координат
        self.image = pygame.transform.rotate(self.original_image, int(angle)) # Вращение картинки
        self.rect = self.image.get_rect(center=self.pos) # Перемещение хитбокса

    def calculate_angle(self, mouse_pos):     # Starship._calculate_angle
        rel_x, rel_y = mouse_pos - self.pos   # x и у составляющие вектора направления
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90  # Расчёт угла
        return angle

    def fire(self):
        self.last_bullet_time = time.time()    # Сохраняем время последнего выстрела
        return Bullet(self.pos.copy())         # Создание новой пули на том же месте где находится игрок


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
        self.rect = self.image.get_rect(center=self.pos) # Получение хитбокса

    def move(self):
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos)

    def calculate_angle(self, mouse_pos):
        rel_x, rel_y = mouse_pos - self.pos
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) + 90
        return angle


game = Game(screen)     # Создание и запуск игры
game.run()
