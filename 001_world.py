import sys
import pygame
import random


# CONFIGURATIONS
SPACE_DIMENSIONS = (500, 500)
SPACE_QUANTUM = 50
SPACE_FPS = 20

# Optional, only for PC, this is why we override the previous space definition
SPACE_DIMENSIONS = (520, 520)
SPACE_BORDER_WIDTH = 10

# Affects the speed of the game
GAME_DIFFICULTY = 25
GAME_QUANTUM = SPACE_FPS * GAME_DIFFICULTY
GAME_QUANTUM_EVENT = pygame.USEREVENT

class KeyPress():
    LEFT, UP, RIGHT, DOWN = range(0, 4)

    def __init__(self, value = None):
        if value not in range(0, 4):
            raise ValueError("Invalid value provided for keypress" % value)
        self.key = value

    @staticmethod
    def random_key():
        return random.randint(KeyPress.LEFT, KeyPress.DOWN)

    @staticmethod
    def is_valid(value):
        return True if value in range(0, 4) else False

    def set(self, value):
        if not KeyPress.is_valid(value):
            raise ValueError("Invalid value provided for keypress" % str(value))
        self.key = value 

    def __str__(self):
        if self.key == self.LEFT:
            return "left"
        elif self.key == self.UP:
            return "up"
        elif self.key == self.RIGHT:
            return "right"
        elif self.key == self.DOWN:
            return "down"
        else:
            raise ValueError()
        return ""

# ----------------------------------------------------
class Snake():
    def __init__(self):
        self._position = []

    def update(self):
        #print("- update: Snake")
        pass

# ----------------------------------------------------
class Edible():
    def __init__(self):
        self._position = []

    def update(self):
        #print("- update: Edible")
        pass

# ----------------------------------------------------
class SnakeGame():
    POSITIONAL_AXES = ((KeyPress.LEFT, KeyPress.RIGHT), (KeyPress.UP, KeyPress.DOWN))

    def __init__(self):
        self._snake = Snake()
        self._edible = Edible()

        # Movement
        self._direction = KeyPress(KeyPress.random_key())

        # Engine specific code
        pygame.init()
        self._screen = pygame.display.set_mode(SPACE_DIMENSIONS)
        self._timer = pygame.time.Clock()
        pygame.time.set_timer(GAME_QUANTUM_EVENT, GAME_QUANTUM)

        # Indicate when to quit
        self._keep_running = True

    def update(self):
        """ Updates the internal state of the game """
        print ("game tick!")
    
        self._snake.update()
        self._edible.update()

    def draw(self):
        """ Draws the game to the default output """
        self._screen.fill((255,0,0))
        self._draw_borders()
        pygame.display.flip()

    def _draw_borders(self):
        """ Borders are nothing but a hollow rectangular shape encompassing the screen. """
        pygame.draw.rect(self._screen, (0, 0, 0), (0, 0, SPACE_DIMENSIONS[0], SPACE_DIMENSIONS[1]), SPACE_BORDER_WIDTH)

    def _is_movement_valid(self, current_dir, proposed_dir):
        """ 
        Checks if the current movement respects the unbreakable laws of snake physics.
        It's assumed that both the current direction as well as the proposed direction as valid.
        """
        print ("Direction", repr(current_dir))

        current_axis = 0 if current_dir in self.POSITIONAL_AXES[0] else 1
        print (current_axis)

    def _parse_key_press(self, pygame_key):
        if pygame_key == pygame.K_LEFT:
            return KeyPress.LEFT
        elif pygame_key == pygame.K_UP:
            return KeyPress.UP
        elif pygame_key == pygame.K_RIGHT:
            return KeyPress.RIGHT
        elif pygame_key == pygame.K_DOWN:
            return KeyPress.DOWN
        else:
            return None


    def run(self):
        # First run:
        self.update()
        self.draw()

        while self._keep_running:
            self._timer.tick(SPACE_FPS)

            # Triggering the quit
            for event in pygame.event.get():
                # Hardcore ciao event
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                    sys.exit()

                # Tick
                elif event.type == GAME_QUANTUM_EVENT:
                    self.update()
                    self.draw()

                # Keypress
                elif event.type == pygame.KEYDOWN:
                    # Cache the previous movement in case the change is not valid.
                    current_direction = self._direction
                    parsed_key = self._parse_key_press(event.key)
                    if KeyPress.is_valid(parsed_key):
                        self._direction.set(parsed_key)

                        # Check if change of movement is valid
                        self._is_movement_valid(current_direction, self._direction)


# ----------------------------------------------------
if __name__ == "__main__":
    game = SnakeGame()
    game.run()