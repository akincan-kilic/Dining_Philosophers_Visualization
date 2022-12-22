from __future__ import annotations
import os
import sys
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

class TableLocation(Enum):
    """Stores the round table locations as a tuple with (x, y)"""
    TOP = (400, 170)
    RIGHT = (580, 350)
    LEFT = (230, 340)
    BOTTOM = (400, 520)
    TOP_RIGHT = (500, 170)
    TOP_LEFT = (300, 170)
    BOTTOM_RIGHT = (500, 520)
    BOTTOM_LEFT = (300, 520)

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


class Chair(pygame.sprite.Sprite):
    def __init__(self, image_file, location):
        super().__init__()
        self.image = pygame.image.load(image_file)
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*4, self.image.get_height()*4))
        self.rect = self.image.get_rect(center=location)


class Meal(pygame.sprite.Sprite):
    def __init__(self, location=(0, 0)):
        super().__init__()
        self.image = pygame.image.load("assets/spaghetti_full.png")
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*1, self.image.get_height()*1))
        self.rect = self.image.get_rect(center=location)
        self.left_to_eat = 10

    def take_a_bite(self):
        self.left_to_eat -= 1
        if self.left_to_eat == 0:
            self.empty()

    def empty(self):
        self.image = pygame.image.load("assets/spaghetti_empty.png")
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*1, self.image.get_height()*1))
        self.rect = self.image.get_rect(center=self.rect.center)

    def is_finished(self):
        return self.left_to_eat == 0

    def _set_coordinates(self, coordinates):
        self.rect.x = coordinates[0]
        self.rect.y = coordinates[1]

class Character(pygame.sprite.Sprite):
    def __init__(self, character_id, state_id,  location, chopstick_1: Chopstick, chopstick_2: Chopstick):
        super().__init__()
        self.image = pygame.image.load("assets/characters.png")
        self.rect = self.image.get_rect(center=location)
        self.image = self.image.subsurface(pygame.Rect(abs(state_id)*16, character_id*16, 16, 16))
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*4, self.image.get_height()*4))
        if state_id < 0:
            self.image = pygame.transform.flip(self.image, True, False)
        self.direction = "right"
        self.moving = False
        self.speed = 5

        self.meal = Meal()
        self.chopstick_1 = chopstick_1
        self.chopstick_2 = chopstick_2

    def think(self):
        self.moving = False
        time.sleep(4)

    def eat(self):
        if self.meal.is_finished():
            return

        if not self.chopstick1.locked():
            self.chopstick1.acquire()
            time.sleep(random.random())
            if not self.chopstick2.locked():
                self.chopstick2.acquire()
                time.sleep(random.random())
                self.meal.take_a_bite()
                self.chopstick_1.release()
                self.chopstick_2.release()
            else:
                self.chopstick_1.release()

    def get_meal(self):
        return self.meal


class Text:
    def __init__(self, text, location, font_size=20, font_color=(0, 0, 0)):
        self.text = text
        self.font = pygame.font.Font("assets/PressStart2P.ttf", font_size)
        self.text_surface = self.font.render(self.text, True, font_color)
        self.text_rect = self.text_surface.get_rect(center=location)


class Chopstick(pygame.sprite.Sprite):
    def __init__(self, angle, location=(0, 0)):
        super().__init__()
        self.image = pygame.image.load("assets/chopstick.png")
        self.image = pygame.transform.scale(self.image, (self.image.get_width()*0.3, self.image.get_height()*0.3))
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=location)


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
    def __init__(self, location: tuple, type: ButtonState, scale: float):
        super().__init__()
        self.type = type
        assert type in [ButtonState.START, ButtonState.RESTART]
        if type == ButtonState.START:
            self.image = pygame.image.load("assets/start.png")
        elif type == ButtonState.RESTART:
            self.image = pygame.image.load("assets/restart.png")
        self.image = pygame.transform.scale(self.image, (self.image.get_width() * scale, self.image.get_height() * scale))
        self.rect = self.image.get_rect(center=location)

    def start_game(self):
        if self.type == ButtonState.START:
            logger.info("Start game button pressed")
            return True

    def restart_game(self):
        if self.type == ButtonState.RESTART:
            logger.info("Restart game button pressed")
            return True


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
    background_group_objects.append(BackgroundFurniture("assets/fireplace.png", (WIDTH//2, 60), 4))
    background_group_objects.append(BackgroundFurniture("assets/music_player.png", (720, 90), 4))
    background_group_objects.append(BackgroundFurniture("assets/sofa_front.png", (560, 80), 4))
    background_group_objects.append(BackgroundFurniture("assets/sofa_single_right.png", (740, 200), 4))
    background_group_objects.append(BackgroundFurniture("assets/stairs.png", (700, 440), 4, True))
    background_group_objects.append(BackgroundFurniture("assets/desk.png", (170, 120), 3))

    ### TABLE ###
    title_text = Text("Dining Philosophers", (WIDTH//2 - 100, HEIGHT - 50), 24, (200, 255, 200))

    philosopher_number = PhiloshoperNumber(starting_number=5)
    addition = PhilosopherAddition((0 + 145, HEIGHT - 60), ButtonState.ADDITION, philosopher_number)
    subtraction = PhilosopherAddition((0 + 60, HEIGHT - 60), ButtonState.SUBTRACTION, philosopher_number)
    addition_group = pygame.sprite.Group()
    addition_group.add(addition, subtraction)

    start_game_button = StartGameButton((WIDTH - 250, HEIGHT - 60), type=ButtonState.START, scale=0.2)
    restart_game_button = StartGameButton((WIDTH - 100, HEIGHT - 60), type=ButtonState.RESTART, scale=0.1)
    game_state_group = pygame.sprite.Group()
    game_state_group.add(start_game_button, restart_game_button)

    number_lock = False

    def load_position(number):
        """Loads a pre-defined position for the philosophers, chairs, meals and chopsticks based on the number of philosophers
        Parameters
        ----------
        number : int
            The number of philosophers
        Returns
        -------
        meal_group : pygame.sprite.Group
            The group of meals
        philosopher_group : pygame.sprite.Group
            The group of philosophers
        """
        if number == 2:
            pass
        elif number == 3:
            pass
        elif number == 4:
            chopstick_0 = Chopstick(225, (WIDTH//2 + 0, HEIGHT//2 ))
            chopstick_1 = Chopstick(160, (WIDTH//2 + 55, HEIGHT//2 ))
            chopstick_2 = Chopstick(75, (WIDTH//2 , HEIGHT//2))
            chopstick_3 = Chopstick(15, (WIDTH//2 - 40, HEIGHT//2 + 10))
            chopstick_4 = Chopstick(290, (WIDTH//2 - 55, HEIGHT//2 - 35))
            chair_0 = Chair("assets/chair_front_2.png", (WIDTH//2 - 40, HEIGHT//2 - 110))
            chair_1 = Chair("assets/chair_front_2.png", (WIDTH//2 + 40, HEIGHT//2 - 110))
            chair_2 = Chair("assets/chair_right_2.png", (WIDTH//2 + 130, HEIGHT//2 - 10))
            chair_3 = Chair("assets/chair_back_2.png", (WIDTH//2, HEIGHT//2 + 100))
            chair_4 = Chair("assets/chair_left_2.png", (WIDTH//2 - 130, HEIGHT//2 - 10))
            philosopher_0 = Character(6, 0, (WIDTH//2 + 10, HEIGHT//2 + 30), chopstick_0, chopstick_1)
            philosopher_1 = Character(0, 0, (WIDTH//2 + 90, HEIGHT//2 + 30), chopstick_1, chopstick_2)
            philosopher_2 = Character(4, -2, (WIDTH//2 + 160, HEIGHT//2 + 100), chopstick_2, chopstick_3)
            philosopher_3 = Character(10, 1, (WIDTH//2 + 45, HEIGHT//2 + 180), chopstick_3, chopstick_4)
            philosopher_4 = Character(2, 2, (WIDTH//2 - 65, HEIGHT//2 + 100), chopstick_4, chopstick_0)
            philosopher_0.get_meal()._set_coordinates((WIDTH//2 - 40, HEIGHT//2 - 50))
            philosopher_1.get_meal()._set_coordinates((WIDTH//2 + 40, HEIGHT//2 - 50))
            philosopher_2.get_meal()._set_coordinates((WIDTH//2 + 60, HEIGHT//2 - 15))
            philosopher_3.get_meal()._set_coordinates((WIDTH//2 + 0, HEIGHT//2 - 10))
            philosopher_4.get_meal()._set_coordinates((WIDTH//2 - 60, HEIGHT//2 - 15))


            philosopher_group = pygame.sprite.Group()
            philosopher_group.add([chair_0, chair_1, chair_2, chair_4, philosopher_0, philosopher_1, philosopher_2, philosopher_3, philosopher_4, chair_3, chopstick_0, chopstick_1, chopstick_2, chopstick_3, chopstick_4])

            meals = []
            meal_group = pygame.sprite.Group()
            for char in [philosopher_0, philosopher_1, philosopher_2, philosopher_3, philosopher_4]:
                meals.append(char.get_meal())
            meal_group.add(meals)

            table = BackgroundFurniture("assets/table_vertical.png", (WIDTH//2, HEIGHT//2), 4)
            table2 = BackgroundFurniture("assets/table_vertical.png", (WIDTH//2 + 50, HEIGHT//2), 4)
            table_group = pygame.sprite.Group()
            table_group.add(table)
            table_group.add(table2)

            return meal_group, philosopher_group, table_group
        elif number == 5:
            chopstick_0 = Chopstick(225, (WIDTH//2 + 0, HEIGHT//2 - 60))
            chopstick_1 = Chopstick(160, (WIDTH//2 + 55, HEIGHT//2 - 35))
            chopstick_2 = Chopstick(75, (WIDTH//2 + 40, HEIGHT//2 + 10))
            chopstick_3 = Chopstick(15, (WIDTH//2 - 40, HEIGHT//2 + 10))
            chopstick_4 = Chopstick(290, (WIDTH//2 - 55, HEIGHT//2 - 35))
            chair_0 = Chair("assets/chair_front_2.png", (WIDTH//2 - 40, HEIGHT//2 - 110))
            chair_1 = Chair("assets/chair_front_2.png", (WIDTH//2 + 40, HEIGHT//2 - 110))
            chair_2 = Chair("assets/chair_right_2.png", (WIDTH//2 + 130, HEIGHT//2 - 10))
            chair_3 = Chair("assets/chair_back_2.png", (WIDTH//2, HEIGHT//2 + 100))
            chair_4 = Chair("assets/chair_left_2.png", (WIDTH//2 - 130, HEIGHT//2 - 10))
            philosopher_0 = Character(6, 0, (WIDTH//2 + 10, HEIGHT//2 + 30), chopstick_0, chopstick_1)
            philosopher_1 = Character(0, 0, (WIDTH//2 + 90, HEIGHT//2 + 30), chopstick_1, chopstick_2)
            philosopher_2 = Character(4, -2, (WIDTH//2 + 160, HEIGHT//2 + 100), chopstick_2, chopstick_3)
            philosopher_3 = Character(10, 1, (WIDTH//2 + 45, HEIGHT//2 + 180), chopstick_3, chopstick_4)
            philosopher_4 = Character(2, 2, (WIDTH//2 - 65, HEIGHT//2 + 100), chopstick_4, chopstick_0)
            philosopher_0.get_meal()._set_coordinates((WIDTH//2 - 40, HEIGHT//2 - 50))
            philosopher_1.get_meal()._set_coordinates((WIDTH//2 + 40, HEIGHT//2 - 50))
            philosopher_2.get_meal()._set_coordinates((WIDTH//2 + 60, HEIGHT//2 - 15))
            philosopher_3.get_meal()._set_coordinates((WIDTH//2 + 0, HEIGHT//2 - 10))
            philosopher_4.get_meal()._set_coordinates((WIDTH//2 - 60, HEIGHT//2 - 15))


            philosopher_group = pygame.sprite.Group()
            philosopher_group.add([chair_0, chair_1, chair_2, chair_4, philosopher_0, philosopher_1, philosopher_2, philosopher_3, philosopher_4, chair_3, chopstick_0, chopstick_1, chopstick_2, chopstick_3, chopstick_4])

            meals = []
            meal_group = pygame.sprite.Group()
            for char in [philosopher_0, philosopher_1, philosopher_2, philosopher_3, philosopher_4]:
                meals.append(char.get_meal())
            meal_group.add(meals)

            table = BackgroundFurniture("assets/table_horizontal.png", (WIDTH//2, HEIGHT//2), 4)
            table_group = pygame.sprite.Group()
            table_group.add(table)

            return meal_group, philosopher_group, table_group
        elif number == 6:
            pass
        elif number == 7:
            pass
        elif number == 8:
            pass
        elif number == 9:
            pass
        elif number == 10:
            pass
        else:
            raise Exception("Number of philosophers must be between 2 and 10")
    meal_group, philosopher_group, table_group = load_position(5)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # If the mouse is clicked on the addition sprite, add a new philosopher
            if event.type == pygame.MOUSEBUTTONDOWN:
                print(pygame.mouse.get_pos())
                if number_lock == False:
                    if addition.rect.collidepoint(event.pos):
                        addition.change_number()
                        meal_group, philosopher_group, table_group = load_position(addition.number.get_number())
                    if subtraction.rect.collidepoint(event.pos):
                        subtraction.change_number()
                        logger.debug(f"Trying to load position {subtraction.number.get_number()}")
                        meal_group, philosopher_group, table_group = load_position(subtraction.number.get_number())
                if start_game_button.rect.collidepoint(event.pos):
                    start_game_button.start_game()
                    number_lock = True
                if restart_game_button.rect.collidepoint(event.pos):
                    restart_game_button.restart_game()
                    number_lock = False

        # DRAWING ORDER: Background, Table, Title, Meals, Philosophers, Buttons
        # Background objects
        background_group = pygame.sprite.Group()
        background_group.add(background_group_objects)
        background_group.draw(screen)

        # Eating Table
        table_group.draw(screen)

        # Game title
        screen.blit(title_text.text_surface, title_text.text_rect)

        # Meals of the philosophers
        meal_group.draw(screen)

        # Philosophers
        philosopher_group.draw(screen)

        # Game Control Buttons
        addition_group.draw(screen)
        game_state_group.draw(screen)


        # Game Clock
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()
