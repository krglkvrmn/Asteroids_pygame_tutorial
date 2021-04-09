# Шаг 1 - пустой шаблон игры на pygame

import sys         # Модуль sys понадобится нам для закрытия игры
import os          # Модуль os нужен для работы с путями и файлами
import pygame      # Модуль pygame для реализации игровой логики

# Инициализация модуля pygame
pygame.init()
# Цвет фона в формате RGB (красный, синий, зелёный). (0, 0, 0) - чёрный цвет.
BG_COLOR = (0, 0, 0)
# Объект дисплея (0, 0) - полный экран, если задать (800, 600), то окно будет размером 800х600 пикселей
screen = pygame.display.set_mode((600, 500), pygame.RESIZABLE)
# Загрузка картинки звездолёта.
# os.path.join позволяет составлять путь до файла.
# На Windows можно просто написать pygame.image.load("images\\starship.png")
starship = pygame.image.load(os.path.join("images", "starship.png"))
# Получаем размеры (хитбокс) картинки
starship_rect = starship.get_rect()

# Игровой цикл (главный цикл)
while True:
    # Цикл обработки событий (нажатия кнопок, движения мыши и т.д.)
    for event in pygame.event.get():     
        if event.type == pygame.QUIT:    # Нажатие на "Х" на окне программы.
            sys.exit()
        # Обработка других событий

    screen.fill(BG_COLOR)  # Закрасить экран чёрным цветом
    screen.blit(starship, starship_rect)   # Нарисовать изображение на экране "screen" в области "starship_rect"
    pygame.display.update()  # Обновить изображение на экране 
