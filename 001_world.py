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

# ----------------------------------------------------
class KeyPress():
    LEFT, UP, RIGHT, DOWN = range(0, 4)

    def __init__(self, value = None):
        self.set(value)

    @staticmethod
    def random_key():
        return random.randint(KeyPress.LEFT, KeyPress.DOWN)

    @staticmethod
    def is_valid(value):
        return True if value in range(0, 4) else False

    def set(self, value):
        if not KeyPress.is_valid(value):
            raise ValueError("Invalid value provided for keypress: {}".format(str(value)))
        self.value = value 

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, KeyPress):
            return self.value == other.value
        return False

    def __str__(self):
        if self.value == self.LEFT:
            return "left"
        elif self.value == self.UP:
            return "up"
        elif self.value == self.RIGHT:
            return "right"
        elif self.value == self.DOWN:
            return "down"
        else:
            raise ValueError()
        return ""

# ----------------------------------------------------
# class Screen():
#     """
#     UI representation of our game
#     """
    
#     def __init__(self, space):
#         pass

# ----------------------------------------------------
class Snake():
    _position = []

    def __init__(self):
        pass

    def grow(self):
        pass

    def update(self):
        #print("- update: Snake")
        pass

# ----------------------------------------------------
class Edible():
    _position = []

    def __init__(self, position = None):
        pass

    def set_position(self, position):
        print("Position given: ", position)

    def update(self):
        #print("- update: Edible")
        pass

# ----------------------------------------------------
class SnakeGame():
    """
    Holds the logic of the game. Essentially controls how the parts fit together.

    This assumes that any entity occupies a single pixel on the screen, and leaves the overhead of the rendering
    to the responsible module. Or it will do that, at some point.
    
    """
    POSITIONAL_AXES = ( (KeyPress(KeyPress.LEFT), KeyPress(KeyPress.RIGHT)), (KeyPress(KeyPress.UP), KeyPress(KeyPress.DOWN)) )

    # Colours
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)

    def __init__(self):
        # A snapshot of our snakey universe.
        self._space = self._quantize_space(SPACE_DIMENSIONS, SPACE_QUANTUM, SPACE_BORDER_WIDTH)
        
        # 
        self._snake = Snake()
        self._edible = Edible()

        # Movement
        self._direction = KeyPress(KeyPress.random_key())

        # Engine specific code
        pygame.init()
        self._timer = pygame.time.Clock()
        pygame.time.set_timer(GAME_QUANTUM_EVENT, GAME_QUANTUM)

        # Indicate when to quit
        self._keep_running = True

        # DRAWING PART, TO BE REFACTORED!
        self._screen = pygame.display.set_mode(SPACE_DIMENSIONS)

    def update(self):
        """ 
        Updates the internal state of the game 
        """
        print ("game tick!")
    
        self._snake.update()
        self._edible.update()

    def draw(self):
        """ 
        Draws the game to the default output 
        """
        self._screen.fill(self.RED)
        self._draw_borders()
        pygame.display.flip()

    def _quantize_space(self, dimensions, quantum, border_width = 0):
        # usable axis quanta => dimension[axis] - (border_width  * 2) / quantum
        def get_range(axis):
            return (axis - (border_width  * 2)) // quantum 
        
        space_range = get_range(dimensions[0]), get_range(dimensions[1])
        return [[0] * (space_range[0]), [0] * (space_range[1])]

    def _draw_borders(self):
        """ 
        Borders are nothing but a hollow rectangular shape encompassing the screen. 
        """
        pygame.draw.rect(self._screen, self.BLACK, (0, 0, SPACE_DIMENSIONS[0], SPACE_DIMENSIONS[1]), SPACE_BORDER_WIDTH)

    def _is_movement_valid(self, current_dir, proposed_dir):
        """ 
        Checks if the current movement respects the unbreakable laws of snake physics.
        It's assumed that both the current direction as well as the proposed direction as valid.
        """
        current_axis = ('x' if current_dir in self.POSITIONAL_AXES[0] else 'y')
        proposed_axis = ('x' if proposed_dir in self.POSITIONAL_AXES[0] else 'y')
        
        # If the current direction differs from the proposed one, and they belong to the same axis, then 
        # the change is invalid, otherwise it's all fine.
        if current_dir != proposed_dir:
            return current_axis != proposed_axis
        else:
            return True

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
        print(self._direction)
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
                        proposed_direction = KeyPress(parsed_key)
                        
                        # Check if change of movement is valid
                        valid_movement = self._is_movement_valid(current_direction, proposed_direction)
                        if valid_movement:
                            self._direction.set(parsed_key)
                            print("+ direction:", str(proposed_direction))
                        else:
                            print ("Invalid direction passed: ", str(proposed_direction))
                            


# ----------------------------------------------------
if __name__ == "__main__":
    game = SnakeGame()
    game.run()