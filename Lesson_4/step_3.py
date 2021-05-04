import sys         # Модуль sys понадобится нам для закрытия игры
import os          # Модуль os нужен для работы с путями и файлами
import pygame      # Модуль pygame для реализации игровой логики   
import numpy as np # Модуль numpy нужен для поэлементного сложения векторов
import math        # Модуль math будет полезен для вычисления угла наклона звездолёта
import time        # Модуль time нужен для замера времени
import random      # Модуль random нужен для генерации случайных чисел


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
        self.boosters = []          # Список буcтеров для отрисовки
        self.boosters_timeouts = {"Rapid_fire": 0,
                                  "Shield": 0,
                                  "Triple_bullets": 0}  # Хранение времени деактивации бустеров
        self.booster_handlers = {"Rapid_fire": self.rapid_fire,
                                 "Shield": self.shield,
                                 "Triple_bullets": self.triple_bullets} # Словарь с функциями-активаторами бустеров
        self.mouse_pressed = False  # Cохраняет состояние кнопки мыши
        self.fire_rate = 0.2        # Пауза между выстрелами (в секундах)
        self.max_bullets = 1    # Кол-во пуль, которые звездолёт выстреливает за 1 раз

    def handle_events(self, frame):
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
            new_bullets = self.starship.fire(self.max_bullets)  # Создаём новые объекты пуль
            self.bullets += new_bullets  # И добавляем их в общий список
        if frame % 25 == 0:         # Каждый 25 кадр 
            self.cast_asteroid()    # Создаём астероид

    def boosters_manager(self, frame):
        """Метод - обработчик всех событий с бустерами в т.ч. столкновений"""
        boosters_rects = [boost.rect for boost in self.boosters]       # Хитбоксы бустеров для расчёта столкновений
        hit = self.starship.rect.collidelist(boosters_rects)       # Расчёт столкновений игрока и бустеров
        if hit != -1:                                              # Если столкновение есть...
            booster_type = self.boosters[hit].type                 # получаем тип бустера из атрибута type
            # Если бустер НЕ активирован (время деактивации равно 0)...
            if self.boosters_timeouts[booster_type] == 0:              
                self.boosters_timeouts[booster_type] = time.time() + 10 # задаём время деактивации через 10 секунд
                self.booster_handlers[booster_type]("activate")         # активируем бустер
            # Если бустер активирован (время деактивации больше 0)...
            elif self.boosters_timeouts[booster_type] > 0:
                self.boosters_timeouts[booster_type] += 10              # увеличиваем время действия на 10 секунд
            # Удаляем бустер после столкновения (картинка исчезнет, но его эффект будет активен)
            del self.boosters[hit]
        # Для каждого типа бустеров и времени его деактивации...
        for booster_type, timeout in self.boosters_timeouts.items():
            # Если бустер активен (timeout > 0), но активное время закончилось (time.time() > timeout)...
            if time.time() > timeout > 0:
                self.boosters_timeouts[booster_type] = 0     # задаём время деактивации равным 0 (отключённое состояние)
                self.booster_handlers[booster_type]("deactivate")  # деактивируем бустер (возвращаем исходное поведение)
        if frame % 400 == 0 and frame != 0:     # Каждые 400 кадров (кроме самого первого!)...
            self.boosters.append(Booster())     # ...размещаем новый бустер на игровом поле

    def move_objects(self, objects_list):  
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

    def check_collisions(self):       
        # Удаление пуль при вылете с игрового поля
        asteroids_rects = [ast.rect for ast in self.asteroids]   # Хитбоксы всех астероидов
        for idx, bullet in enumerate(self.bullets):   # Для каждой пули в игре...
            if bullet.pos[0] > SCREEN_SIZE[0] or bullet.pos[1] > SCREEN_SIZE[1] or (bullet.pos < 0).any():       # ...если центра пули вышел за границы
                del self.bullets[idx]      # удалить объект пули
        # Разрушение астероидов при контакте с пулями
        for idx, bullet in enumerate(self.bullets):
            # С каким из астероидов имеется столкновение?
            hit = bullet.rect.collidelist(asteroids_rects)
            if hit != -1:     # Если столкновение есть...
                fragments = self.asteroids[hit].explode()  # Разбиваем астероид на осколки
                del self.asteroids[hit]  # ...удалить астероид с индексом hit
                self.asteroids += fragments                # Добавляем эти осколки в общий список
                del self.bullets[idx]    # ...удалить пулю с индексом idx
        # Столкновение астероидов и игрока
        # Индекс астероида, столкнувшегося с игроком
        hit = self.starship.rect.collidelist(asteroids_rects) 
        if hit != -1:   # Если столкновение было... 
            # Если бустер "Щит" активен
            if self.boosters_timeouts["Shield"] > 0:  
                del self.asteroids[hit]               # Удалим астероид с которым столкнулись
            # ...иначе
            else: 
                sys.exit()  # ...выйти из игры  

    def cast_asteroid(self):  
        new_asteroid = Asteroid()   # Создаём астероид
        self.asteroids.append(new_asteroid)   # Добавляем его в список всех астероидов

    def rapid_fire(self, mode):  
        if mode == "activate":      # Если бустер нужно активировать...
            self.fire_rate /= 2     # ...уменьшаем паузу между пулями в 2 раза
        elif mode == "deactivate":  # Если бустер нужно отключить...
            self.fire_rate *= 2     # ...увеличиваем паузу между пулями в 2 раза (возвращаем к исходной)

    def shield(self, mode):
        if mode == "activate":
            # При активации подменяем оригинальную картинку звездолёта на картинку с щитком
            self.starship.original_image = pygame.image.load(os.path.join("images", "Starship_with_shield.png"))
        elif mode == "deactivate":
            # При деактивации возвращаем исходную картинку на место
            self.starship.original_image = pygame.image.load(os.path.join("images", "starship.png"))        

    def triple_bullets(self, mode):
        if mode == "activate":      # При активации...
            self.max_bullets = 3    # изменить кол-во пуль, которые звездолёт выстреливает за 1 раз на 3
        elif mode == "deactivate":  # При деактивации...
            self.max_bullets = 1    # вернуть значение обратно равным 1

    def run(self):
        """Главный цикл программы. Вызывается 1 раз за игру"""
        frame = 0
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            self.handle_events(frame)
            self.boosters_manager(frame)
            self.check_collisions()
            self.move_objects([[self.starship], self.bullets, self.asteroids])
            self.draw([self.boosters, [self.starship], self.bullets, self.asteroids])
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

    def fire(self, bullet_num):
        self.last_bullet_time = time.time()    # Сохраняем время последнего выстрела
        new_bullets = []                       # Создаём список, куда поместим все новые пули
        for i in range(bullet_num):            # Заданное количество раз...
            if bullet_num == 1:                # В случае одной пули...
                angle_offset = 0               # ...зададим смещение относительно направления взгляда равным 0
            else:                              # Иначе...
                angle_offset = -15 + 30 / (bullet_num - 1) * i   # ..расчитаем смещения для всех пуль
            new_bullets.append(Bullet(self.pos.copy(), angle_offset))    # Создаём пулю с заданным смещением
        return new_bullets     # Возвращаем список из созданных пуль (список из 1 элемента по-умолчанию)


class Bullet:
    # Объектов класса Bullet будет создаваться довольно много, поэтому мы
    # хотим загрузить картинку только 1 раз
    original_image = pygame.image.load(os.path.join("images", "bullet.png"))
    def __init__(self, pos, angle_offset=0):
        self.pos = pos
        # Направление пули не изменяется с течением времени, поэтому его можно
        # вычислить внутри конструктора
        mouse_pos = pygame.mouse.get_pos()
        self.direction = (mouse_pos - pos)
        asr = math.pi / 180 * angle_offset    # Переводим величину смещения в радиан из градусов
        # "Поворачиваем" первую координату направления
        self.direction[0] = self.direction[0] * math.cos(asr) - self.direction[1] * math.sin(asr)
        # "Поворачиваем" первую координату направления
        self.direction[1] = self.direction[0] * math.sin(asr) + self.direction[1] * math.cos(asr) 
        self.speed = self.direction / max(abs(self.direction)) * 10
        # Угол также не изменяется
        self.angle = self.calculate_angle(mouse_pos) - angle_offset  # Расчёт угла поворота
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


class Asteroid:
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
    
    def __init__(self, pos=None, speed=None, ast_type=None):    # Конструктор класса Asteroid
        # Если координаты, скорость и тип заданы...
        if (pos is not None) and (speed is not None) and (ast_type is not None):                         
            self.init_asteroid_fragment(pos, speed, ast_type) # ...инициализировать осколок
        else:                                                   # Иначе (координаты, скорость и тип НЕ заданы)...
            self.init_rand_asteroid()                         # ...инициализировать обычный астероид

    def init_asteroid_fragment(self, pos, speed, ast_type):
        """Метод инициализирует осколок астероида, принимая на вход его координаты (pos), скорость (speed) и тип (ast_type)"""
        # Отбираем только картинки с астероидами заданного типа
        ast_type_variants = list(filter(lambda x: x[0] == ast_type, self.ast_variants))
        # Берём случайную картинку астероида заданного типа
        self.type, self.original_image, hitbox_shape = random.choice(ast_type_variants)  
        self.pos = pos      # Координаты осколка задаём НЕ случайно
        self.w, self.h = hitbox_shape        
        self.image = self.original_image   
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)
        self.speed = speed             # Задаём направление (скорость) НЕ случайно
        
    def init_rand_asteroid(self):
        """Метод инициализирует обычный астероид случайными типом и координатам"""
        # Случайный выбор типа и картинки астероида
        self.type, self.original_image, hitbox_shape = random.choice(self.ast_variants)
        self.image = self.original_image 
        self.w, self.h = hitbox_shape # Сохраняем длину и ширину хитбокса
        self.pos = random.choice([self.left_pos, self.top_pos,      # Генерируем случайную начальную позицию
                                  self.right_pos, self.bottom_pos])()
        # Получаем хитбокс с заданными размерами
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)
        self.direction = pygame.mouse.get_pos() - self.pos          # Вычисляем направление
        self.speed = self.direction / 300                           # Расчитываем скорость
        
    def left_pos(self):
        """Генерация позиции слева"""
        return np.array((-150, random.uniform(0, SCREEN_SIZE[1])))

    def right_pos(self):
        """Генерация позиции справа"""
        return np.array((SCREEN_SIZE[0] + 150, random.uniform(0, SCREEN_SIZE[1])))

    def top_pos(self):
        """Генерация позиции сверху"""
        return np.array((random.uniform(0, SCREEN_SIZE[0]), -150))

    def bottom_pos(self):
        """Генерация позиции снизу"""
        return np.array((random.uniform(0, SCREEN_SIZE[0]), SCREEN_SIZE[1] + 150))

    def speed_offset(self):
        # Уменьшаем скорость в 2 раза и изменяем её составляющие по x и y на небольшую величину
        offset = self.speed * 0.5 + np.random.uniform(-0.5, 0.5, 2)
        return offset

    def pos_offset(self):        
        # Возвращаем немного смещённые координаты центра астероида
        offset = self.pos + np.random.uniform(-10, 10, 2)
        return offset

    def check_borders(self):
        # Если центр астероида за нижней границей...
        if self.pos[0] > (SCREEN_SIZE[0] + 150):   
            self.pos[0] = -150       # ...перемещаем его на верхнюю
        # Если центр астероида за верхней границей...
        elif (self.pos[0] + 150) < 0:
            self.pos[0] = SCREEN_SIZE[0] + 150  # ...перемещаем его на нижнюю
        # Если центр астероида за правой границей...
        if (self.pos[1] - 150) > SCREEN_SIZE[1]:
            self.pos[1] = -150     # ...перемещаем его на левую
        # Если центр астероида за левой границей...
        elif (self.pos[1] + 150) < 0:
            self.pos[1] = SCREEN_SIZE[1] + 150    # ...перемещаем его на правую
        # Обновляем хитбокс, так как произошло перемещение
        self.rect = self.image.get_rect(center=self.pos)

    def move(self):
        self.check_borders()  # Обработка выхода за границы
        self.pos += self.speed
        self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)

    def explode(self):    # Метод explode класса Asteroid
        fragments = []                                                      # Список с осколками астероидов
        if self.type == "large":                                            # Если астероид большой...
            for _ in range(2):
                # Генерируем новые смещённые параметры для осколков
                pos, speed = self.pos_offset(), self.speed_offset()   
                fragments.append(Asteroid(pos, speed, "medium"))    # Передаём их в конструктор астероида
        if self.type == "medium":                                           # Если астероид средний...
            for _ in range(3):
                # Генерируем новые смещённые параметры для осколков
                pos, speed = self.pos_offset(), self.speed_offset()   
                fragments.append(Asteroid(pos, speed, "small"))    # Передаём их в конструктор астероида
        if self.type == "small":                                            # Если астероид маленький...
            pass                                                            # ...не делать ничего
        return fragments


class Booster:
    """Класс представляющий картинку бустера на игровом поле. Все эффекты от бустеров не будут непосредственно связаны с объектами данного класса и будут описаны внутри класса Game"""
    # Типы возможных бустеров и их картинки
    booster_types = {"Rapid_fire": pygame.image.load(os.path.join("images", "Rapid_fire.png")),
                     "Shield": pygame.image.load(os.path.join("images", "Shield.png")),
                     "Triple_bullets": pygame.image.load(os.path.join("images", "Triple_bullets.png"))}    
    def __init__(self):
        self.type = random.choice(list(self.booster_types.keys()))  # Выбор случайного типа для бустера
        self.image = self.booster_types[self.type]                # Выбор картинки бустера
        self.pos = np.array([random.randint(100, SCREEN_SIZE[0] - 100),   # Генерация случайных координат для бустера
                             random.randint(100, SCREEN_SIZE[1] - 100)])
        self.rect = self.image.get_rect(center=self.pos)                  # Получение хитбокса бустера




game = Game(screen)     # Создание и запуск игры
game.run()
