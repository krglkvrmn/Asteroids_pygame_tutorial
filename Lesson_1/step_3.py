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
    """Основной класс игры. В нём представлены основные методы для управления игровыми объектами, а также сами объекты"""
    def  __init__(self, screen):     
        self.screen = screen         
        self.starship = Starship()  # Объект класса Starship (игрок)
        self.bullets = []           # Заготовка для хранения объектов пуль
        self.asteroids = []         # Заготовка для хранения объектов астероидов

    def handle_events(self):
        """Метод - обработчик событий. Выполняет те же действия, что и в базовом шаблоне"""
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                sys.exit()

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

    def run(self):
        """Главный цикл программы. Вызывается 1 раз за игру"""
        while True:
            self.handle_events()
            self.move_objects([[self.starship]])
            self.draw([[self.starship]])

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

    def move(self):                       # Starship.move
        mouse_pos = pygame.mouse.get_pos()    # Текущая позиция курсора мыши
        direction = mouse_pos - self.pos      # Текущее направление
        self.speed = direction / 40           # Новое значение скорости
        self.pos += self.speed                # Движение - обновление координат
        self.rect = self.image.get_rect(center=self.pos) # Перемещение хитбокса


game = Game(screen)     # Создание и запуск игры
game.run()
