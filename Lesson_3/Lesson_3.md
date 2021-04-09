# Добавление осколков астероидов

На данный момент астероиды в нашей игре исчезают после попадания пулей, но мы хотим, чтобы поведение было более интересное. Мы сделаем 3 типа астероидов: большие, средние и маленькие. При попадании в большой астероид он будет разлетаться на несколько средних, каждый из которых развалится на несколько маленьких при попадании, маленькие же будут исчезать.

Для этого нам понадобятся картинки для всех типов астероидов. Изначально мы имели только 4 картинки с астероидами среднего размера. Для того чтобы не искать в интернете и не рисовать новые, мы просто сделаем копии существующих картинок с уменьшенным и увеличенным размером. Таким образом мы получим 12 картинок (по 4 на каждый тип астероида). Также нам нужно учесть, что астероиды различного размера будут иметь различные хитбоксы. Учитывая всё это, обновим атрибут класса *Asteroid* в который загружаются картинки.

```python
# Атрибут ast_variants класса Asteroid
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
```

Запись выглядит довольно сложно, но это всего лишь спискок, где каждый элемент это кортеж из *типа астероида* (small, medium, large), *картинки* и *длины и ширины хитбокса*. Мы изменили название атрибута на *ast_variants*, так как изменился тип данных хранимых в нём (*original_images* могло ввести в заблуждение).

Теперь, поскольку мы обновили атрибут, хранящий параметры астероидов, нам нужно внести правки в конструктор класса *Asteroids*, чтобы при создании объекта он сохранял его тип и хитбокс.

```python
def __init__(self):      # Конструктор класса Asteroid
    # Случайный выбор типа и картинки астероида
    self.type, self.original_image, hitbox_shape = random.choice(self.ast_variants)  # <---- 
    self.image = self.original_image   # <---- 
    self.w, self.h = hitbox_shape # <---- Сохраняем длину и ширину хитбокса
    self.pos = random.choice([self._left_pos, self._top_pos,
                              self._right_pos, self._bottom_pos])()
    # Получаем хитбокс с заданными размерами
    self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)  # <-----
    self.direction = pygame.mouse.get_pos() - self.pos
    self.speed = self.direction / 300       
```

Здесь мы не видим ничего необычного. Сначала мы выбираем случайный элемент из атрибута *ast_variants*, этот элемент содержит тип астероида, картинку и размеры хитбокса, которые мы сохраняем в атрибуты объекта. Заметьте, что вероятности выбрать астероиды каждого класса равны, так как для каждого из них существует по 4 элемента списка.

Далее мы создаём атрибут *self.image*, так как оригинальное изображение может пригодится нам в будущем.

Сохраняем в отдельные атрибуты ширину (*self.w*) и высоту (*self.h*) хитбокса для более короткой их записи.

Поскольку каждый тип астероида должен иметь свой размер хитбокса, нам необходимо обозначить данные параметры при его получении, передав его ширину и высоту в качестве аргументов *width* и *height* при вызове *self.image.get_rect*. Размеры хитбокса можно было бы и не задавать, но в таком случае размеры хитбокса стали бы равны размеру изображения, что, как мы знаем, слишком много и может приводить к "ложным" столкновениям.

Аналогично конструктору изменим параметры получения хитбокса в методе *move*.

```python
def move(self):     # Метод move класса Asteroid
    self.check_borders()
    self.pos += self.speed
    self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)  # <----
```

Отлично, теперь при запуске игры мы увидим разные типы астероидов с правильными хитбоксами, при этом они пока всё ещё разрушаются одним выстрелом.

![image-20210404133049885](/home/roman/.config/Typora/typora-user-images/image-20210404133049885.png)

Давайте опишем сам механизм разрушения астероидов на маленькие.

```python
def explode(self):    # Метод explode класса Asteroid  (черновая версия)
    fragments = []         # Список с осколками астероидов
    if self.type == "large":              # Если астероид большой...
        for _ in range(2):
            fragments.append(Asteroid())  # ..добавить 2 астероида в список
    if self.type == "medium":             # Если астероид средний...
        for _ in range(3):
            fragments.append(Asteroid())  # ...добавить 3 астероида в список
    if self.type == "small":              # Если астероид маленький...
        pass                              # ...не делать ничего
    return fragments
```

Метод *explode* является ключевым в данном механизме. Он будет вызываться при столкновении астероида и пули, а элементы списка осколков будут добавляться в основной список астероидов.

```python
def check_collisions(self):            # Метод check_collisions класса Game
    asteroids_rects = [ast.rect for ast in self.asteroids]
    for idx, bullet in enumerate(self.bullets):
        if bullet.pos[0] > SCREEN_SIZE[0] or bullet.pos[1] > SCREEN_SIZE[1] or (bullet.pos < 0).any():
            del self.bullets[idx]
    for idx, bullet in enumerate(self.bullets):
        hit = bullet.rect.collidelist(asteroids_rects)
        if hit != -1:
            fragments = self.asteroids[hit].explode() # <---- Разбиваем астероид на осколки
            del self.asteroids[hit]
            self.asteroids += fragments               # <---- Добавляем эти осколки в общий список
            del self.bullets[idx]
    hit = self.starship.rect.collidelist(asteroids_rects)  
    if hit != -1:   
        sys.exit()  
```

Проблема состоит в том, что новые астероиды (осколки) будут создаваться по тому же принципу, что и обычные астероиды (за пределами экрана и двигаться в сторону курсора). Это приводит к тому, что количество астероидов начинает очень быстро увеличиваться.

![image-20210404144239988](/home/roman/.config/Typora/typora-user-images/image-20210404144239988.png)



 Однако мы хотели бы, чтобы осколки  сохраняли направление начального астероида и появлялись на его месте. Для этого нам необходимо передать в конструктор объекта класса *Asteroid* все необходимые параметры: его тип, координаты и направление. Поскольку данные параметры не являются случайными (как в случае обычных астероидов), нам понадобится совершенно другая логика создания объекта. Всё это можно описать внутри конструктора через набор условий, однако такой код будет перегружен и крайне сложен для чтения. Вместо этого мы можем создать 2 метода **имитирующих** конструктор. Каждый из них будет создавать необходимые атрибуты в зависимости от типа астероида (обычный или осколок). Затем мы вызовем их из основного конструктора в зависимости от типа астероида.

```python
def __init_rand_asteroid(self):     # Метод __init_rand_asteroid класса Asteroid
    """Метод инициализирует обычный астероид случайными типом и координатам"""
    self.type, self.original_image, hitbox_shape = random.choice(self.ast_variants)
    self.image = self.original_image 
    self.w, self.h = hitbox_shape 
    self.pos = random.choice([self._left_pos, self._top_pos,
                              self._right_pos, self._bottom_pos])()
    self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)
    self.direction = pygame.mouse.get_pos() - self.pos
    self.speed = self.direction / 300     
```

Метод *__init_rand_asteroid* будет инициализировать обычный астероид. На самом деле мы просто скопировали текущий код конструктора в этот метод, так как логика создания обычных астероидов не изменится.

```python
def __init_asteroid_fragment(self, pos, speed, ast_type):  # Метод __init_asteroid_fragment класса Asteroid
    """Метод инициализирует осколок астероида, принимая на вход его координаты (pos), скорость (speed) и тип (ast_type)"""
    # Отбираем только картинки с астероидами заданного типа
    ast_type_variants = list(filter(lambda x: x[0] == ast_type, self.variants))
    # Берём случайную картинку астероида заданного типа
    self.type, self.original_image, hitbox_shape = random.choice(ast_type_variants)  
    self.pos = pos      # Координаты осколка задаём НЕ случайно
    self.w, self.h = hitbox_shape        
    self.image = self.original_image   
    self.rect = self.image.get_rect(center=self.pos, width=self.w, height=self.h)
    self.speed = speed             # Задаём направление (скорость) НЕ случайно
```

Метод *__init_asteroid_fragment* будет инициализировать осколок астероида.  На вход он будет принимать позицию (*pos*) и направление (*direction*) родительского астероида (т. е. астероида в который попала пуля и он развалился на осколки, которые мы сейчас инициализируем). Тип осколка (*ast_type*) мы будем задавать в методе *explode*.

*ast_type_variants* &mdash; здесь мы отбираем картинки астероидов имеющие заданный класс (*ast_type*) из атрибута класса *ast_variants* при помощи функции filter.

*self.pos = pos* &mdash; задаём координаты осколка равными координатам родительского астероида (так они будут появляться в том же месте).

*self.speed = speed* &mdash; задаём скорость осколка равным скорости родительского астероида (скорость хранит внутри себя направление, так что нам не нужно заботиться об этом отдельно).

```python
def __init__(self, pos=None, speed=None, ast_type=None):   # <---- Конструктор класса Asteroid
    # Если координаты, скорость и тип заданы...
    if (pos is None) and (speed is not None) and (ast_type is not None):                         
        self.__init_asteroid_fragment(pos, speed, ast_type)# ...инициализировать осколок
    else:                                                  # Иначе (координаты, скорость и тип НЕ заданы)...
        self.__init_rand_asteroid()                        # ...инициализировать обычный астероид
```

Имея эти два метода для инициализации астероидов мы полностью переписываем конструктор, а также добавляем ему возможность принимать в качестве аргументов координаты, скорость и тип астероида. 

Теперь, когда конструктор полностью готов к работе с осколками и обычными астероидами, мы можем вернуться к методу *explode*.

```python
def explode(self):    # Метод explode класса Asteroid
    fragments = []         												# Список с осколками астероидов
    if self.type == "large":                                            # Если астероид большой...
        for _ in range(2):
            # ...добавить 2 средних астероида в список
            fragments.append(Asteroid(self.pos.copy(), self.speed.copy(), "medium"))
    if self.type == "medium":             								# Если астероид средний...
        for _ in range(3):
            # ...добавить 3 маленьких астероида в список
            fragments.append(Asteroid(self.pos.copy(), self.speed.copy(), "small")) 
    if self.type == "small":              								# Если астероид маленький...
        pass                              								# ...не делать ничего
    return fragments
```

Здесь мы инициализируем осколки с координатами (*self.pos*), скоростью (*self.speed*) и типом на 1 меньше, чем родитель.

Казалось бы всё должно работать. Однако проблема состоит в том, что все осколки имеют одинаковую траекторию, они появляются в одном месте и все летят в одну сторону. Мы хотим, чтобы осколки в целом сохраняли направление родителя, но случайно отклонялись на небольшой угол. Также мы хотим, чтобы осколки немного замедлялись (из-за столкновения с пулей). Если мы внесём данные изменения поведение астероидов будет станет очень правдоподобным.

Для этих целей мы добавим два метода, которые будут генерировать небольшое случайное отклонение для скорости и координат.

```python
def _speed_offset(self):            # Метод _speed_offset класса Asteroid
    # Уменьшаем скорость в 2 раза и изменяем её составляющие по x и y на небольшую величину
	offset = self.speed * 0.5 + np.random.uniform(-0.5, 0.5, 2)
	return offset

def _pos_offset(self):              # Метод _pos_offset класса Asteroid
    # Возвращаем немного смещённые координаты центра астероида
	offset = self.pos + np.random.uniform(-10, 10, 2)
	return offset
```

*self.speed \* 0.5* &mdash; уменьшение скорости в 2 раза. *np.random.uniform(-0.5, 0.5, 2)* &mdash; случайный сдвиг направления вектора скорости (так как 0.5 это довольно немного, направление осколков в целом будет совпадать с направлением родителя).

*np.random.uniform(-10, 10, 2)* &mdash; случайный сдвиг координат центра осколков относительно родительского цента, это предотвратит их появление в одной точке.

Теперь перепишем метод *explode* с учётом сдвигов.

```python
def explode(self):    # Метод explode класса Asteroid
    fragments = []         		
    if self.type == "large":                          
        for _ in range(2):
            # Генерируем новые смещённые параметры для осколков
            pos, speed = self._pos_offset(), self._speed_offset()   
            fragments.append(Asteroid(pos, speed, "medium"))    # <--- Передаём их в конструктор астероида
    if self.type == "medium":             								
        for _ in range(3):
            # Генерируем новые смещённые параметры для осколков
            pos, speed = self._pos_offset(), self._speed_offset()
            fragments.append(Asteroid(pos, speed, "small"))     # <--- Передаём их в конструктор астероида
    if self.type == "small":              					
        pass                              						
    return fragments
```

Замечательно, всё работает как мы хотели! При желании мы можем варьировать количество осколков, образующихся при попадании пули.

# Добавление усилений (бустеров)

Чтобы игровой процесс был более интересным мы можем добавить различные усиления, которые будут облегчать игру. Их реализация может быть довольно сложна, так как обычно разные бустеры затрагивают разные части игры, что требует очень хорошей организации кода. Мы реализуем один из самых простых бустеров, он будет увеличивать темп огня. Но реализованные интерфейсы помогут нам более легко подключать новые усиления.

Сначала нам нужно описать класс на основе которого будут создаваться бустеры.

```python

```

