from __future__ import annotations
import os
import sys
import threading
import pygame
from enum import Enum, auto
import logging
import random
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
file_handler = logging.FileHandler('dining_philosophers.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


MULTIPLIER = 4
LEG = 6 * MULTIPLIER
MID = 17 * MULTIPLIER
XS = 240
YS = 250

class ButtonState(Enum):
    START = auto()
    RESTART = auto()
    ADDITION = auto()
    SUBTRACTION = auto()

# Fixes the File not found error when running from the command line.
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class BackgroundFurniture(pygame.sprite.Sprite):
    def __init__(self, image_file, location, scale_factor=1.0, horizontal_flip=False, vertical_flip=False):
        super().__init__()
        self.image = pygame.image.load(image_file)
        self.image = pygame.transform.flip(self.image, horizontal_flip, vertical_flip)
        self.image = pygame.transform.scale(
            self.image,
            (
                int(self.image.get_width() * scale_factor),
                int(self.image.get_height() * scale_factor)
            )
        )
        self.rect = self.image.get_rect(center=location)


class Fireplace(pygame.sprite.Sprite):
    def __init__(self, location, scale_factor=4.0):
        super().__init__()
        self.sprites = [pygame.image.load("assets/fireplace.png"),
                        pygame.image.load("assets/fireplace_2.png"),
                        pygame.image.load("assets/fireplace_3.png"),
                        pygame.image.load("assets/fireplace_4.png")]
        # Multiply the size of the sprites by the scale factor
        for i in range(len(self.sprites)):
            self.sprites[i] = pygame.transform.scale(self.sprites[i],
                                                     (int(self.sprites[i].get_width() * scale_factor),
                                                      int(self.sprites[i].get_height() * scale_factor)))
        self.image = self.sprites[0]
        self.rect = self.image.get_rect(center=location)
        self.sprite_counter = 0

    def update_fire_sprite_to_next(self):
        # Only update the sprite every 10 frames
        self.sprite_counter += 1
        if self.sprite_counter % 10 == 0:
            self.image = self.sprites[random.randint(0, 3)]
            self.image.get_rect(center=self.rect.center)


class TableFurniture(pygame.sprite.Sprite):
    def __init__(self, image_file, location, scale_factor=1.0, horizontal_flip=False, vertical_flip=False):
        super().__init__()
        self.image = pygame.image.load(image_file)
        self.image = pygame.transform.flip(self.image, horizontal_flip, vertical_flip)
        self.image = pygame.transform.scale(
            self.image,
            (
                int(self.image.get_width() * scale_factor),
                int(self.image.get_height() * scale_factor)
            )
        )
        self.rect = self.image.get_rect(x=location[0], y=location[1])


class Chair(pygame.sprite.Sprite):
    def __init__(self, image_file, location):
        super().__init__()
        self.image = pygame.image.load(image_file)
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*4, self.image.get_height()*4))
        self.rect = self.image.get_rect(x=location[0], y=location[1])


class Meal(pygame.sprite.Sprite):
    def __init__(self, location=(0, 0)):
        super().__init__()
        self.sprites = {'full':pygame.image.load("assets/spaghetti_full.png"),
                        'eating':pygame.image.load('assets/meal_eating_yum.png'),
                        'half_eating': pygame.image.load('assets/meal_one.png'),
                        'empty':pygame.image.load("assets/spaghetti_empty.png")}
        self.image = self.sprites['full']
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*1, self.image.get_height()*1))
        self.rect = self.image.get_rect(center=location)
        self.left_to_eat = 3

    def update_to_half_eating(self):
        self.image = self.sprites['half_eating']

    def update_to_eating(self):
        self.image = self.sprites['eating']

    def update_to_full(self):
        self.image = self.sprites['full']

    def take_a_bite(self):
        self.image = self.sprites['eating']
        time.sleep(random.randint(2, 7))
        self.left_to_eat -= 1
        self.image = self.sprites['full']
        if self.left_to_eat == 0:
            self.empty()

    def empty(self):
        self.image = self.sprites['empty']
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*1, self.image.get_height()*1))
        self.rect = self.image.get_rect(center=self.rect.center)

    def is_finished(self):
        return self.left_to_eat == 0

    def reset(self):
        self.left_to_eat = 10
        self.image = self.sprites['full']
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*1, self.image.get_height()*1))
        self.rect = self.image.get_rect(center=self.rect.center)

    def _set_coordinates(self, coordinates):
        self.rect.x = coordinates[0]
        self.rect.y = coordinates[1]


class Character(pygame.sprite.Sprite):
    def __init__(self, character_id, state_id,  location, chopstick_1: Chopstick, chopstick_2: Chopstick):
        super().__init__()
        self.image = pygame.image.load("assets/characters.png")
        self.rect = self.image.get_rect(x=location[0], y=location[1])
        self.image = self.image.subsurface(pygame.Rect(abs(state_id)*16, character_id*16, 16, 16))
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*4, self.image.get_height()*4))
        if state_id < 0:
            self.image = pygame.transform.flip(self.image, True, False)
        self.direction = "right"
        self.moving = False
        self.speed = 5
        self.force_stop = False
        self.eating = False

        self.meal = Meal()
        self.chopstick_1 = chopstick_1
        self.chopstick_2 = chopstick_2

    def think(self):
        time.sleep(random.randint(1, 10))

    def eat(self):
        if self.get_meal().is_finished():
            return
        if self.chopstick_1.locked():
            return
        self.chopstick_1.acquire()
        self.get_meal().update_to_half_eating()
        time.sleep(random.random())
        if not self.chopstick_2.locked():
            self.chopstick_2.acquire()
            time.sleep(random.random())
            self.eating = True
            self.meal.take_a_bite()
            self.chopstick_1.release()
            self.chopstick_2.release()
        else:
            time.sleep(random.random())
            self.chopstick_1.release()
            self.get_meal().update_to_full()

    def get_meal(self):
        return self.meal

    def start_process(self):
        while True:
            self.eat()
            self.think()
            if self.meal.is_finished() or self.force_stop:
                break

    def stop_process(self):
        self.force_stop = True
        self.meal.reset()


class Text:
    def __init__(self, text, location, font_size=20, font_color=(0, 0, 0)):
        self.text = text
        self.font = pygame.font.Font("assets/PressStart2P.ttf", font_size)
        self.text_surface = self.font.render(self.text, True, font_color)
        self.text_rect = self.text_surface.get_rect(center=location)


class Chopstick(pygame.sprite.Sprite):
    def __init__(self, location=(0, 0), image_name="assets/chopstick_up.png"):
        super().__init__()
        self.sprites = {'free':pygame.image.load(image_name),
                        'occupied': pygame.image.load("assets/empty.png")}
        self.image = self.sprites['free']
        self.rect = self.image.get_rect(center=location)
        self.original_rect = self.rect
        self.lock = threading.Lock()

    def locked(self):
        return self.lock.locked()

    def acquire(self):
        self.lock.acquire()
        self.image = self.sprites['occupied']

    def release(self):
        self.lock.release()
        self.image = self.sprites['free']
        self.reset_coordinates()
        # self.image = pygame.transform.scale(self.image, (self.image.get_width()*0.3, self.image.get_height()*0.3))
        # self.image = pygame.transform.rotate(self.image, self.angle)

    def _set_coordinates(self, coordinates):
        self.rect.x = coordinates[0]
        self.rect.y = coordinates[1]

    def reset_coordinates(self):
        self.rect = self.original_rect


class PhilosopherAddition(pygame.sprite.Sprite):
    def __init__(self, location: tuple, type: ButtonState, number: PhiloshoperNumber):
        super().__init__()
        self.type = type
        assert type in [ButtonState.ADDITION, ButtonState.SUBTRACTION]
        if type == ButtonState.ADDITION:
            self.image = pygame.image.load("assets/addition.png")
        elif type == ButtonState.SUBTRACTION:
            self.image = pygame.image.load("assets/subtraction.png")
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*3, self.image.get_height()*3))
        self.rect = self.image.get_rect(center=location)
        self.number = number

    def change_number(self):
        logger.info(f"{self.type} button pressed")
        if self.type == ButtonState.ADDITION:
            self.number.change_number(1)
        elif self.type == ButtonState.SUBTRACTION:
            self.number.change_number(-1)


class PhiloshoperNumber():
    def __init__(self, starting_number=None):
        self.MIN_LIMIT = 2
        self.MAX_LIMIT = 10
        if starting_number is None:
            self.number = random.randint(self.MIN_LIMIT, self.MAX_LIMIT)
        else:
            self.number = starting_number
        self.lock = False

    def change_number(self, change):
        if self.lock:
            return
        if self.number + change < self.MIN_LIMIT:
            self.number = self.MIN_LIMIT
        elif self.number + change > self.MAX_LIMIT:
            self.number = self.MAX_LIMIT
        else:
            self.number += change
        logger.info(f"Number of philosophers: {self.number}")

    def get_number(self):
        return self.number

    def lock_number(self):
        self.lock = True

    def unlock_number(self):
        self.lock = False

    def __str__(self) -> str:
        return str(self.number)

    def __repr__(self) -> str:
        return self.__str__()


class StartGameButton(pygame.sprite.Sprite):
    def __init__(self, location: tuple):
        super().__init__()
        self.image = pygame.image.load("assets/start.png")
        self.image = pygame.transform.scale(self.image, (self.image.get_width() * 0.2, self.image.get_height() * 0.2))
        self.rect = self.image.get_rect(center=location)
        self.game_state = ButtonState.START
        self.philosophers = []
        self.philosophers_threads = []

    def start_game(self, philosophers: list):
        if self.game_state == ButtonState.START:
            logger.info("Start game button pressed")
            self.game_state = ButtonState.RESTART
            self.image = pygame.image.load("assets/restart.png")
            self.image = pygame.transform.scale(self.image, (self.image.get_width() * 0.1, self.image.get_height() * 0.1))
            self.philosophers = philosophers

            for philosopher in self.philosophers:
                thread = threading.Thread(target=philosopher.start_process)
                self.philosophers_threads.append(thread)

            for thread in self.philosophers_threads:
                thread.start()

    def restart_game(self):
        if self.game_state != ButtonState.RESTART:
            return
        logger.info("Restart game button pressed")
        self.game_state = ButtonState.START
        self.image = pygame.image.load("assets/start.png")
        self.image = pygame.transform.scale(self.image, (self.image.get_width() * 0.2, self.image.get_height() * 0.2))
        if len(self.philosophers_threads) > 0:
            for philosopher in self.philosophers:
                philosopher.stop_process()
            self.philosophers_threads = []
            self.philosophers = []
        else:
            logger.error("No philosophers to restart")

    def get_game_state(self):
        return self.game_state


def main():
    WIDTH = 800
    HEIGHT = 600
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Dining Philosophers")
    screen.fill((255, 255, 255))
    clock = pygame.time.Clock()

    background_group = pygame.sprite.Group()
    floors = [ BackgroundFurniture("assets/floor.png", (x, y)) for x in range(0, WIDTH+100, 62) for y in range(0, HEIGHT+100, 46)]
    background_group_objects = []
    background_group_objects.extend(floors)
    background_group_objects.append(BackgroundFurniture("assets/carpet.png", (WIDTH//2, HEIGHT//2), 12))
    background_group_objects.append(BackgroundFurniture("assets/music_player.png", (720, 90), 4))
    background_group_objects.append(BackgroundFurniture("assets/sofa_front.png", (560, 80), 4))
    background_group_objects.append(BackgroundFurniture("assets/sofa_single_right.png", (740, 200), 4))
    background_group_objects.append(BackgroundFurniture("assets/stairs.png", (700, 440), 4, True))
    background_group_objects.append(BackgroundFurniture("assets/desk.png", (170, 120), 3))
    background_group = pygame.sprite.Group()
    background_group.add(background_group_objects)
    fireplace = Fireplace((WIDTH//2, 60), 4)

    ### TABLE ###
    title_text = Text("Dining Philosophers", (WIDTH//2 - 150, HEIGHT - 120), 24, (200, 255, 200))

    philosopher_number = PhiloshoperNumber(starting_number=5)
    addition = PhilosopherAddition((0 + 145, HEIGHT - 60), ButtonState.ADDITION, philosopher_number)
    subtraction = PhilosopherAddition((0 + 60, HEIGHT - 60), ButtonState.SUBTRACTION, philosopher_number)
    addition_group = pygame.sprite.Group()
    addition_group.add(addition, subtraction)

    start_game_button = StartGameButton((WIDTH - 250, HEIGHT - 60))
    game_state_group = pygame.sprite.Group()
    game_state_group.add(start_game_button)

    number_lock = False

    def create_table(philosopher_number: int) -> list:
        table_group = []
        table_left = TableFurniture("assets/table_left.png", (XS, YS), MULTIPLIER)

        added_middle_count = 0

        if philosopher_number < 2 or philosopher_number > 10:
            raise ValueError("Number of philosophers must be between 2 and 10")

        if philosopher_number <= 4:
            table_middle_0 = TableFurniture("assets/table_middle.png", (XS + LEG, YS), MULTIPLIER)
            added_middle_count = 1
            table_group.append(table_middle_0)

        elif philosopher_number > 4 and philosopher_number <= 6:
            table_middle_0 = TableFurniture("assets/table_middle.png", (XS + LEG, YS), MULTIPLIER)
            table_middle_1 = TableFurniture("assets/table_middle.png", (XS + MID + LEG, YS), MULTIPLIER)
            added_middle_count = 2
            table_group.extend([table_middle_0, table_middle_1])

        elif philosopher_number > 6 and philosopher_number <= 8:
            table_middle_0 = TableFurniture("assets/table_middle.png", (XS + LEG, YS), MULTIPLIER)
            table_middle_1 = TableFurniture("assets/table_middle.png", (XS + MID + LEG, YS), MULTIPLIER)
            table_middle_2 = TableFurniture("assets/table_middle.png", (XS + (MID * 2) + LEG, YS), MULTIPLIER)
            added_middle_count = 3
            table_group.extend([table_middle_0, table_middle_1, table_middle_2])

        else:
            table_middle_0 = TableFurniture("assets/table_middle.png", (XS + LEG, YS), MULTIPLIER)
            table_middle_1 = TableFurniture("assets/table_middle.png", (XS + MID + LEG, YS), MULTIPLIER)
            table_middle_2 = TableFurniture("assets/table_middle.png", (XS + (MID * 2) + LEG, YS), MULTIPLIER)
            table_middle_3 = TableFurniture("assets/table_middle.png", (XS + (MID * 3) + LEG, YS), MULTIPLIER)
            added_middle_count = 4

            table_group.extend([table_middle_0, table_middle_1, table_middle_2, table_middle_3])


        table_right = TableFurniture("assets/table_right.png", (XS + (MID * added_middle_count) + LEG, YS), MULTIPLIER)
        table_group.extend([table_left, table_right])
        return table_group


    def load_position(number):
        """Loads a pre-defined position for the philosophers, chairs, meals and chopsticks based on the number of philosophers
        Parameters
        ----------
        number : int
            The number of philosophers

        Returns
        -------
        meals : list
            A list of meals for the philosophers

        philosophers : list
            A list of philosophers

        table_group : pygame.sprite.Group
            A group of table furniture, chairs and chopsticks
        """

        if number == 2:
            chopstick_0 = Chopstick((284,300), image_name='assets/chopstick_45.png')
            chopstick_1 = Chopstick((313, 268),image_name='assets/chopstick_45.png' )

            chair_0 = Chair("assets/chair_left_2.png", (190,255))
            chair_1 = Chair("assets/chair_right_2.png", (350,260))

            philosopher_0 = Character(5, 2, (190,255), chopstick_0, chopstick_1)
            philosopher_1 = Character(14, -2, (350,260), chopstick_1, chopstick_0)

            philosopher_0.get_meal()._set_coordinates((250,270))
            philosopher_1.get_meal()._set_coordinates((315,270))

            chopsticks = [chopstick_0, chopstick_1]
            chairs = [chair_0, chair_1]
            philosophers = [philosopher_0, philosopher_1]
            meals = [p.get_meal() for p in philosophers]

        elif number == 3:
            chopstick_0 = Chopstick((284,300), image_name='assets/chopstick_45.png')
            chopstick_1 = Chopstick((300, 266),image_name='assets/chopstick_up.png' )
            chopstick_2 = Chopstick((315,300), image_name='assets/chopstick_45r.png')

            chair_0 = Chair("assets/chair_left_2.png", (190,255))
            chair_1 = Chair("assets/chair_right_2.png", (350,260))
            chair_2 = Chair("assets/chair_back_2.png", (270,344))

            philosopher_0 = Character(5, 2, (190,255), chopstick_0, chopstick_1)
            philosopher_1 = Character(14, -2, (350,260), chopstick_1, chopstick_2)
            philosopher_2 = Character(11, 1, (270,320), chopstick_2, chopstick_0 )

            philosopher_0.get_meal()._set_coordinates((250,270))
            philosopher_1.get_meal()._set_coordinates((315,270))
            philosopher_2.get_meal()._set_coordinates((285,290))

            chopsticks = [chopstick_0, chopstick_1, chopstick_2]
            chairs = [chair_0, chair_1, chair_2]
            philosophers = [philosopher_0, philosopher_1, philosopher_2]
            meals = [p.get_meal() for p in philosophers]

        elif number == 4:
            chopstick_0 = Chopstick((280,305), image_name='assets/chopstick_45.png')
            chopstick_1 = Chopstick((325,270),image_name='assets/chopstick_45.png' )
            chopstick_2 = Chopstick((325,310), image_name='assets/chopstick_45r.png')
            chopstick_3 = Chopstick((270,270), image_name='assets/chopstick_45r.png')

            chair_0 = Chair("assets/chair_left_2.png", (190,255))
            chair_1 = Chair("assets/chair_right_2.png", (350,260))
            chair_2 = Chair("assets/chair_back_2.png", (270,344))
            chair_3 = Chair("assets/chair_front_2.png", (270,160))

            philosopher_0 = Character(5, 2, (190,255), chopstick_0, chopstick_3)
            philosopher_1 = Character(14, -2, (350,260), chopstick_1, chopstick_2)
            philosopher_2 = Character(11, 1, (270,320), chopstick_2, chopstick_0 )
            philosopher_3 = Character(15, 4, (270,170), chopstick_3, chopstick_1)

            philosopher_0.get_meal()._set_coordinates((250,270))
            philosopher_1.get_meal()._set_coordinates((315,270))
            philosopher_2.get_meal()._set_coordinates((285,290))
            philosopher_3.get_meal()._set_coordinates((285,255))

            chopsticks = [chopstick_0, chopstick_1, chopstick_2, chopstick_3]
            chairs = [chair_0, chair_1, chair_2, chair_3]
            philosophers = [philosopher_0, philosopher_1, philosopher_2, philosopher_3]
            meals = [p.get_meal() for p in philosophers]


        elif number == 5:
            chopstick_0 = Chopstick((280,305), image_name='assets/chopstick_45.png')
            chopstick_1 = Chopstick((380,275),image_name='assets/chopstick_45.png' )
            chopstick_2 = Chopstick((370,310), image_name='assets/chopstick_45r.png')
            chopstick_3 = Chopstick((270,270), image_name='assets/chopstick_45r.png')
            chopstick_4 = Chopstick((325, 270), image_name='assets/chopstick_up.png')

            chair_0 = Chair("assets/chair_left_2.png", (190,255))
            chair_1 = Chair("assets/chair_right_2.png", (420,260))
            chair_2 = Chair("assets/chair_back_2.png", (300,344))
            chair_3 = Chair("assets/chair_front_2.png", (270,160))
            chair_4 = Chair("assets/chair_front_2.png", (350,160))

            philosopher_0 = Character(5, 2, (190,255), chopstick_0, chopstick_3)
            philosopher_1 = Character(14, -2, (415,260), chopstick_1, chopstick_2)
            philosopher_2 = Character(11, 1, (300,320), chopstick_2, chopstick_0 )
            philosopher_3 = Character(15, 4, (270,170), chopstick_3, chopstick_4)
            philosopher_4 = Character(3, 4, (350,170), chopstick_4, chopstick_1)

            philosopher_0.get_meal()._set_coordinates((250,270))
            philosopher_1.get_meal()._set_coordinates((380,270))
            philosopher_2.get_meal()._set_coordinates((320,290))
            philosopher_3.get_meal()._set_coordinates((285,255))
            philosopher_4.get_meal()._set_coordinates((340,255))

            chopsticks = [chopstick_0, chopstick_1, chopstick_2, chopstick_3, chopstick_4]
            chairs = [chair_0, chair_1, chair_2, chair_3, chair_4]
            philosophers = [philosopher_0, philosopher_1, philosopher_2, philosopher_3, philosopher_4]
            meals = [p.get_meal() for p in philosophers]

        elif number == 6:
            chopstick_0 = Chopstick((280,305), image_name='assets/chopstick_45.png')
            chopstick_1 = Chopstick((380,275),image_name='assets/chopstick_45.png' )
            chopstick_2 = Chopstick((325,310), image_name='assets/chopstick_up.png')
            chopstick_3 = Chopstick((270,270), image_name='assets/chopstick_45r.png')
            chopstick_4 = Chopstick((325, 270), image_name='assets/chopstick_up.png')
            chopstick_5 = Chopstick((390,310), image_name='assets/chopstick_45r.png')

            chair_0 = Chair("assets/chair_left_2.png", (190,255))
            chair_1 = Chair("assets/chair_right_2.png", (420,260))
            chair_2 = Chair("assets/chair_back_2.png", (270,344))
            chair_3 = Chair("assets/chair_front_2.png", (270,160))
            chair_4 = Chair("assets/chair_front_2.png", (350,160))
            chair_5 = Chair("assets/chair_back_2.png", (350,344))

            philosopher_0 = Character(5, 2, (190,255), chopstick_0, chopstick_3)
            philosopher_1 = Character(14, -2, (415,260), chopstick_1, chopstick_5)
            philosopher_2 = Character(11, 1, (270,320), chopstick_2, chopstick_0 )
            philosopher_3 = Character(15, 4, (270,170), chopstick_3, chopstick_4)
            philosopher_4 = Character(3, 4, (350,170), chopstick_4, chopstick_1)
            philosopher_5 = Character(12, 1, (350,320), chopstick_5, chopstick_2)

            philosopher_0.get_meal()._set_coordinates((250,270))
            philosopher_1.get_meal()._set_coordinates((380,270))
            philosopher_2.get_meal()._set_coordinates((285,290))
            philosopher_3.get_meal()._set_coordinates((285,255))
            philosopher_4.get_meal()._set_coordinates((340,255))
            philosopher_5.get_meal()._set_coordinates((340,290))

            chopsticks = [chopstick_0, chopstick_1, chopstick_2, chopstick_3, chopstick_4,chopstick_5]
            chairs = [chair_0, chair_1, chair_2, chair_3, chair_4, chair_5]
            philosophers = [philosopher_0, philosopher_1, philosopher_2, philosopher_3, philosopher_4,philosopher_5]
            meals = [p.get_meal() for p in philosophers]

        elif number == 7:
            chopstick_0 = Chopstick((280,305), image_name='assets/chopstick_45.png')
            chopstick_1 = Chopstick((460,275),image_name='assets/chopstick_45.png' )
            chopstick_2 = Chopstick((350,310), image_name='assets/chopstick_up.png')
            chopstick_3 = Chopstick((270,270), image_name='assets/chopstick_45r.png')
            chopstick_4 = Chopstick((350, 270), image_name='assets/chopstick_up.png')
            chopstick_5 = Chopstick((420,310), image_name='assets/chopstick_up.png')
            chopstick_6 = Chopstick((420,270), image_name='assets/chopstick_UP.png')

            chair_0 = Chair("assets/chair_left_2.png", (190,255))
            chair_1 = Chair("assets/chair_right_2.png", (490,260))
            chair_2 = Chair("assets/chair_back_2.png", (270,344))
            chair_3 = Chair("assets/chair_front_2.png", (270,160))
            chair_4 = Chair("assets/chair_front_2.png", (350,160))
            chair_5 = Chair("assets/chair_back_2.png", (350,344))
            chair_6 = Chair("assets/chair_FRONT_2.png", (430,160))

            philosopher_0 = Character(5, 2, (190,255), chopstick_0, chopstick_3)
            philosopher_1 = Character(14, -2, (480,260), chopstick_1, chopstick_5)
            philosopher_2 = Character(11, 1, (270,320), chopstick_2, chopstick_0 )
            philosopher_3 = Character(15, 4, (270,170), chopstick_3, chopstick_4)
            philosopher_4 = Character(3, 4, (350,170), chopstick_4, chopstick_6)
            philosopher_5 = Character(12, 1, (350,320), chopstick_5, chopstick_2)
            philosopher_6 = Character(1, 4, (420,170), chopstick_6, chopstick_1)


            philosopher_0.get_meal()._set_coordinates((250,270))
            philosopher_1.get_meal()._set_coordinates((455,270))
            philosopher_2.get_meal()._set_coordinates((285,290))
            philosopher_3.get_meal()._set_coordinates((285,255))
            philosopher_4.get_meal()._set_coordinates((370,255))
            philosopher_5.get_meal()._set_coordinates((370,290))
            philosopher_6.get_meal()._set_coordinates((420,255))


            chopsticks = [chopstick_0, chopstick_1, chopstick_2, chopstick_3, chopstick_4,chopstick_5, chopstick_6]
            chairs = [chair_0, chair_1, chair_2, chair_3, chair_4, chair_5, chair_6]


            philosophers = [philosopher_0, philosopher_1, philosopher_2, philosopher_3, philosopher_4,philosopher_5,philosopher_6]
            meals = [p.get_meal() for p in philosophers]

        elif number == 8:
            chopstick_0 = Chopstick((280,305), image_name='assets/chopstick_45.png')
            chopstick_1 = Chopstick((460,275),image_name='assets/chopstick_45.png' )
            chopstick_2 = Chopstick((350,310), image_name='assets/chopstick_up.png')
            chopstick_3 = Chopstick((270,270), image_name='assets/chopstick_45r.png')
            chopstick_4 = Chopstick((350, 270), image_name='assets/chopstick_up.png')
            chopstick_5 = Chopstick((420,310), image_name='assets/chopstick_up.png')
            chopstick_6 = Chopstick((420,270), image_name='assets/chopstick_UP.png')
            chopstick_7 = Chopstick((460,310),image_name='assets/chopstick_45r.png' )

            chair_0 = Chair("assets/chair_left_2.png", (190,255))
            chair_1 = Chair("assets/chair_right_2.png", (490,260))
            chair_2 = Chair("assets/chair_back_2.png", (270,344))
            chair_3 = Chair("assets/chair_front_2.png", (270,160))
            chair_4 = Chair("assets/chair_front_2.png", (350,160))
            chair_5 = Chair("assets/chair_back_2.png", (350,344))
            chair_6 = Chair("assets/chair_FRONT_2.png", (430,160))
            chair_7 = Chair("assets/chair_back_2.png", (430,344))

            philosopher_0 = Character(5, 2, (190,255), chopstick_0, chopstick_3)
            philosopher_1 = Character(14, -2, (480,260), chopstick_1, chopstick_7)
            philosopher_2 = Character(11, 1, (270,320), chopstick_2, chopstick_0 )
            philosopher_3 = Character(15, 4, (270,170), chopstick_3, chopstick_4)
            philosopher_4 = Character(3, 4, (350,170), chopstick_4, chopstick_6)
            philosopher_5 = Character(12, 1, (350,320), chopstick_5, chopstick_2)
            philosopher_6 = Character(1, 4, (420,170), chopstick_6, chopstick_1)
            philosopher_7 = Character(6, 1, (420,320), chopstick_7, chopstick_5)


            philosopher_0.get_meal()._set_coordinates((250,270))
            philosopher_1.get_meal()._set_coordinates((455,270))
            philosopher_2.get_meal()._set_coordinates((285,290))
            philosopher_3.get_meal()._set_coordinates((285,255))
            philosopher_4.get_meal()._set_coordinates((370,255))
            philosopher_5.get_meal()._set_coordinates((370,290))
            philosopher_6.get_meal()._set_coordinates((420,255))
            philosopher_7.get_meal()._set_coordinates((420,290))


            chopsticks = [chopstick_0, chopstick_1, chopstick_2, chopstick_3, chopstick_4,chopstick_5, chopstick_6, chopstick_7 ]
            chairs = [chair_0, chair_1, chair_2, chair_3, chair_4, chair_5, chair_6, chair_7]


            philosophers = [philosopher_0, philosopher_1, philosopher_2, philosopher_3, philosopher_4,philosopher_5,philosopher_6,philosopher_7]
            meals = [p.get_meal() for p in philosophers]

        elif number == 9:
            chopstick_0 = Chopstick((280,305), image_name='assets/chopstick_45.png')
            chopstick_1 = Chopstick((525,275),image_name='assets/chopstick_45.png' )
            chopstick_2 = Chopstick((350,310), image_name='assets/chopstick_up.png')
            chopstick_3 = Chopstick((270,270), image_name='assets/chopstick_45r.png')
            chopstick_4 = Chopstick((350, 270), image_name='assets/chopstick_up.png')
            chopstick_5 = Chopstick((420,310), image_name='assets/chopstick_up.png')
            chopstick_6 = Chopstick((420,270), image_name='assets/chopstick_UP.png')
            chopstick_7 = Chopstick((460,310),image_name='assets/chopstick_up.png' )
            chopstick_8 = Chopstick((460,270),image_name='assets/chopstick_up.png' )

            chair_0 = Chair("assets/chair_left_2.png", (190,255))
            chair_1 = Chair("assets/chair_right_2.png", (560,260))
            chair_2 = Chair("assets/chair_back_2.png", (270,344))
            chair_3 = Chair("assets/chair_front_2.png", (270,160))
            chair_4 = Chair("assets/chair_front_2.png", (350,160))
            chair_5 = Chair("assets/chair_back_2.png", (350,344))
            chair_6 = Chair("assets/chair_FRONT_2.png", (430,160))
            chair_7 = Chair("assets/chair_back_2.png", (430,344))
            chair_8 = Chair("assets/chair_front_2.png", (500,160))

            philosopher_0 = Character(5, 2, (190,255), chopstick_0, chopstick_3)
            philosopher_1 = Character(14, -2, (560,260), chopstick_1, chopstick_7)
            philosopher_2 = Character(11, 1, (270,320), chopstick_2, chopstick_0 )
            philosopher_3 = Character(15, 4, (270,170), chopstick_3, chopstick_4)
            philosopher_4 = Character(3, 4, (350,170), chopstick_4, chopstick_6)
            philosopher_5 = Character(12, 1, (350,320), chopstick_5, chopstick_2)
            philosopher_6 = Character(1, 4, (420,170), chopstick_6, chopstick_8)
            philosopher_7 = Character(6, 1, (420,320), chopstick_7, chopstick_5)
            philosopher_8 = Character(8, 4, (500,170), chopstick_8, chopstick_1)

            philosopher_0.get_meal()._set_coordinates((250,270))
            philosopher_1.get_meal()._set_coordinates((520,270))
            philosopher_2.get_meal()._set_coordinates((285,290))
            philosopher_3.get_meal()._set_coordinates((285,255))
            philosopher_4.get_meal()._set_coordinates((370,255))
            philosopher_5.get_meal()._set_coordinates((370,290))
            philosopher_6.get_meal()._set_coordinates((420,255))
            philosopher_7.get_meal()._set_coordinates((420,290))
            philosopher_8.get_meal()._set_coordinates((480,255))

            chopsticks = [chopstick_0, chopstick_1, chopstick_2, chopstick_3, chopstick_4,chopstick_5, chopstick_6, chopstick_7,chopstick_8 ]
            chairs = [chair_0, chair_1, chair_2, chair_3, chair_4, chair_5, chair_6, chair_7, chair_8]

            philosophers = [philosopher_0, philosopher_1, philosopher_2, philosopher_3, philosopher_4,philosopher_5,philosopher_6,philosopher_7, philosopher_8]
            meals = [p.get_meal() for p in philosophers]

        elif number == 10:
            chopstick_0 = Chopstick((280,305), image_name='assets/chopstick_45.png')
            chopstick_1 = Chopstick((525,275),image_name='assets/chopstick_45.png' )
            chopstick_2 = Chopstick((350,310), image_name='assets/chopstick_up.png')
            chopstick_3 = Chopstick((270,270), image_name='assets/chopstick_45r.png')
            chopstick_4 = Chopstick((350, 270), image_name='assets/chopstick_up.png')
            chopstick_5 = Chopstick((420,310), image_name='assets/chopstick_up.png')
            chopstick_6 = Chopstick((420,270), image_name='assets/chopstick_UP.png')
            chopstick_7 = Chopstick((460,310),image_name='assets/chopstick_up.png' )
            chopstick_8 = Chopstick((460,270),image_name='assets/chopstick_up.png' )
            chopstick_9 = Chopstick((525,310),image_name='assets/chopstick_45r.png' )

            chair_0 = Chair("assets/chair_left_2.png", (190,255))
            chair_1 = Chair("assets/chair_right_2.png", (560,260))
            chair_2 = Chair("assets/chair_back_2.png", (270,344))
            chair_3 = Chair("assets/chair_front_2.png", (270,160))
            chair_4 = Chair("assets/chair_front_2.png", (350,160))
            chair_5 = Chair("assets/chair_back_2.png", (350,344))
            chair_6 = Chair("assets/chair_FRONT_2.png", (430,160))
            chair_7 = Chair("assets/chair_back_2.png", (430,344))
            chair_8 = Chair("assets/chair_front_2.png", (500,160))
            chair_9 = Chair("assets/chair_back_2.png", (500,344))

            philosopher_0 = Character(5, 2, (190,255), chopstick_0, chopstick_3)
            philosopher_1 = Character(14, -2, (560,260), chopstick_1, chopstick_9)
            philosopher_2 = Character(11, 1, (270,320), chopstick_2, chopstick_0 )
            philosopher_3 = Character(15, 4, (270,170), chopstick_3, chopstick_4)
            philosopher_4 = Character(3, 4, (350,170), chopstick_4, chopstick_6)
            philosopher_5 = Character(12, 1, (350,320), chopstick_5, chopstick_2)
            philosopher_6 = Character(1, 4, (420,170), chopstick_6, chopstick_8)
            philosopher_7 = Character(6, 1, (420,320), chopstick_7, chopstick_5)
            philosopher_8 = Character(8, 4, (500,170), chopstick_8, chopstick_1)
            philosopher_9 = Character(7, 1, (500,320), chopstick_9, chopstick_7)

            philosopher_0.get_meal()._set_coordinates((250,270))
            philosopher_1.get_meal()._set_coordinates((520,270))
            philosopher_2.get_meal()._set_coordinates((285,290))
            philosopher_3.get_meal()._set_coordinates((285,255))
            philosopher_4.get_meal()._set_coordinates((370,255))
            philosopher_5.get_meal()._set_coordinates((370,290))
            philosopher_6.get_meal()._set_coordinates((420,255))
            philosopher_7.get_meal()._set_coordinates((420,290))
            philosopher_8.get_meal()._set_coordinates((480,255))
            philosopher_9.get_meal()._set_coordinates((480,290))

            chopsticks = [chopstick_0, chopstick_1, chopstick_2, chopstick_3, chopstick_4,chopstick_5, chopstick_6, chopstick_7,chopstick_8,chopstick_9 ]
            chairs = [chair_0, chair_1, chair_2, chair_3, chair_4, chair_5, chair_6, chair_7, chair_8, chair_9]
            philosophers = [philosopher_0, philosopher_1, philosopher_2, philosopher_3, philosopher_4,philosopher_5,philosopher_6,philosopher_7, philosopher_8,philosopher_9]
            meals = [p.get_meal() for p in philosophers]

        else:
            raise Exception("Number of philosophers must be between 2 and 10")

        table_group = pygame.sprite.Group()
        table_group.add(chairs)
        table_group.add(create_table(number))
        table_group.add(chopsticks)

        return meals, philosophers, table_group

    # Load the default position
    meals, philosophers, table_group = load_position(5)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.display.quit()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                print(pygame.mouse.get_pos())

                if number_lock == False:

                    if addition.rect.collidepoint(event.pos):
                        addition.change_number()
                        meals, philosophers, table_group = load_position(addition.number.get_number())

                    if subtraction.rect.collidepoint(event.pos):
                        subtraction.change_number()
                        meals, philosophers, table_group = load_position(subtraction.number.get_number())

                if start_game_button.rect.collidepoint(event.pos):
                    if start_game_button.get_game_state() == ButtonState.START:
                        start_game_button.start_game(philosophers=philosophers)
                        number_lock = True

                    elif start_game_button.get_game_state() == ButtonState.RESTART:
                        start_game_button.restart_game()
                        number_lock = False

        # DRAWING ORDER: Background, Table, Title, Meals, Philosophers, Buttons
        # Background objects
        fireplace.update_fire_sprite_to_next()
        background_group.add(fireplace)
        background_group.draw(screen)

        # Eating Table
        table_group.draw(screen)

        # Game title
        screen.blit(title_text.text_surface, title_text.text_rect)
        philo_number_text = Text(f"Number of Philosophers: {addition.number.get_number()}", (265,HEIGHT- 10), 20, (255,255,255))
        screen.blit(philo_number_text.text_surface, philo_number_text.text_rect)

        # Meals of the philosophers
        meal_group = pygame.sprite.Group()
        for meal in meals:
            meal_group.add(meal)
        meal_group.draw(screen)

        # Philosophers
        philosopher_group = pygame.sprite.Group()
        for philosopher in philosophers:
            philosopher_group.add(philosopher)
        philosopher_group.draw(screen)

        # Game Control Buttons
        addition_group.draw(screen)
        game_state_group.draw(screen)

        # Game Clock
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()
