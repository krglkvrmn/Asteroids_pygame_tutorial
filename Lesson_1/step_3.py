# Шаг 3 - базовая реализация движения

import sys
import os
import pygame
import numpy as np

pygame.init()
BG_COLOR = (0, 0, 0)
screen = pygame.display.set_mode((600, 500), pygame.RESIZABLE)
SCREEN_SIZE = screen.get_size()


class Game:
    """Основной класс игры. В нём представлены основные методы для управления игровыми объектами, а также сами
    объекты """

    def __init__(self, screen):
        self.screen = screen
        self.starship = Starship()  # Объект класса Starship (игрок)
        self.bullets = []  # Заготовка для хранения объектов пуль
        self.asteroids = []  # Заготовка для хранения объектов астероидов

    def handle_events(self):
        # Цикл обработки событий (нажатия кнопок, движения мыши и т.д.)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Нажатие на "Х" на окне программы.
                sys.exit()   # Выход из программы

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
                    pygame.draw.rect(self.screen, (0, 255, 0), obj.rect, 2)  # Отрисовка прямоугольника зелёного цвета
        pygame.display.update()  # Применение изменений

    def run(self):
        """Главный цикл программы. Вызывается 1 раз за игру"""
        while True:
            self.handle_events()
            self.move_objects([[self.starship]])
            self.draw([[self.starship]], debug=True)


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

    def move(self):
        mouse_pos = pygame.mouse.get_pos()  # Текущая позиция курсора мыши
        direction = mouse_pos - self.pos  # Текущее направление
        self.speed = direction / 40  # Новое значение скорости
        self.pos += self.speed  # Движение - обновление координат
        self.rect = self.image.get_rect(center=self.pos)  # Перемещение хитбокса


game = Game(screen)  # Создание и запуск игры
game.run()
