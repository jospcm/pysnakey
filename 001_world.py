import sys
import pygame
import random
import numpy

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

        # Try comparing to our representation
        elif isinstance(other, int):
            if KeyPress.is_valid(other):
                return self.value == other
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
class Element():
    def __init__(self, representation):
        if representation is None:
            raise ValueError("Invalid argument provided for the element representation")
        self._repr = representation

class EmptyElement(Element):
    def __init__(self):
        super(EmptyElement, self).__init__(0)
        pass

# ----------------------------------------------------
class Space():
    """
    A representation of our snakey world
    """
    def __init__(self, dimensions, quantum, border_width = 0):
        self._space = self._quantize(dimensions, quantum, border_width)
        pass
    
    def get_random_unoccupied_position(self):
        free = []
        for x, row in enumerate(self._space):
            for y, elm in enumerate(row):
                if isinstance(elm, EmptyElement):
                    free.append([x,y])
        return random.choice(free)


    def occupy(self, position, value):
        x, y = position
        self._space[x][y] = value

    def free(self, position):
        x, y = position
        elm  = self._space[x][y]
        self._space[x][y] = EmptyElement()
    
    def contains(self, who):
        """
        Returns true if the element is already present in our universe
        """
        return numpy.isin(who, self._space)

    def where(self, who):
        """
        Returns the position of the element, assuming it's already present in our universe. 
        """
        position = numpy.where(self._space == who)
        if (position):
            position = position[0][0], position[1][0]

        return position


    def _quantize(self, dimensions, quantum, border_width):
        # usable axis quanta => dimension[axis] - (border_width  * 2) / quantum
        def get_range(axis):
            return (axis - (border_width  * 2)) // quantum 
        
        space_range = get_range(dimensions[0]), get_range(dimensions[1])
        return numpy.full(space_range, EmptyElement())

    # Python magic
    # def __setitem__(self, key, value):
    #     try:
    #         x, y = key
    #         self._space[x][y] = value
    #     except Exception as e:
    #         # Bad.
    #         raise ValueError("Cannot set space item. Invalid key provided. Expected: sequence with 2+ elements.")

    # def __getitem__(self, key):
    #     try:
    #         x, y = key
    #         return self._space[x][y]
    #     except Exception as e:
    #         # Bad.
    #         raise ValueError("Cannot retrieve space item. Invalid key provided. Expected: sequence with 2+ elements.")

    def __iter__(self):
        return self._space.__iter__()

    def __next__(self):
        return self._space.__next__()

# ----------------------------------------------------
class Snake():

    class Node():
        """
        Represents a part of the snake, contains a position and an associated velocity.
        """
        def __init__(self, position, velocity):
            self._position = position
            self._velocity = velocity

    def __init__(self, position = None, direction = None):
        if position is None:
            raise ValueError("Invalid initial provided to the mighty snake. Cannot proceed.")

        if direction is None:
            raise ValueError("Invalid initial vector to the mighty snake. Cannot proceed.")
        
        self._nodes = []
        for pos in position:
            self._nodes.append(Snake.Node(pos, self._derive_vector(direction)))

        self._direction = direction
        pass

    def update(self, space, direction):
        # Updating the snake is essentially creating a new node, and destroying the last one.

        new_velocity = self._derive_vector(direction)
        new_position = list(numpy.add(new_velocity, self._nodes[-1]._position))
        
        self._nodes.append(Snake.Node(new_position, new_velocity))

        # Delete the last one
        last = self._nodes.pop(0)
        
        # Free the last position
        space.free(last._position)
        
        for pos in self._nodes:
            space.occupy(pos._position, self)
        
    def _derive_vector(self, direction):
        if (direction == KeyPress.LEFT):
            return (-1, 0)
        elif (direction == KeyPress.UP):
            return (0, -1)
        elif (direction == KeyPress.RIGHT):
            return (1, 0)
        elif (direction == KeyPress.DOWN):
            return (0, 1)
        else:
            raise ValueError("Invalid direction ({}) provided. Cannot proceed.".format(direction))

# ----------------------------------------------------
class Edible():
    def __init__(self, position = None):
        if position is None:
            raise ValueError("Invalid position provided to the delicious edible. Cannot proceed.")
        self._position = position
        pass

    def set_position(self, position):
        self._position = position

    def update(self, space):
        space.occupy(self._position, self)
        pass

# ----------------------------------------------------
class SnakeGame():
    """
    Holds the logic of the game. Essentially controls how the parts fit together.
 
    This assumes that any entity occupies a single pixel on the screen, and leaves the overhead of the rendering
    to the responsible module. Or it will do that, at some point.
    """
    POSITIONAL_AXES = ( (KeyPress(KeyPress.LEFT), KeyPress(KeyPress.RIGHT)), (KeyPress(KeyPress.UP), KeyPress(KeyPress.DOWN)) )

    # TODO: DRAWING PART, TO BE REFACTORED!
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (128, 0, 0)
    GREEN = (0, 128, 0)

    def __init__(self):
        # A snapshot of our snakey universe.
        self._space = Space(SPACE_DIMENSIONS, SPACE_QUANTUM, SPACE_BORDER_WIDTH)        

        # Movement
        self._direction = KeyPress(KeyPress.random_key())

        # TODO: JPM DEBUGGING
        # Snake expects a list of positions, even though the list is one.
        self._direction = KeyPress(KeyPress.DOWN)
        self._snake = Snake([[4, 0], [4, 1], [4, 2]], self._direction)
        # self._snake = Snake([self._space.get_random_unoccupied_position()], self._direction)
        self._edible = Edible(self._space.get_random_unoccupied_position())

        # Engine specific code
        pygame.init()
        self._timer = pygame.time.Clock()
        pygame.time.set_timer(GAME_QUANTUM_EVENT, GAME_QUANTUM)

        # Indicate when to quit
        self._keep_running = True

        # TODO: DRAWING PART, TO BE REFACTORED!
        self._screen = pygame.display.set_mode(SPACE_DIMENSIONS)

    def update(self):
        """ 
        Updates the internal state of the game 
        """
        self._snake.update(self._space, self._direction)
        self._edible.update(self._space)

    def draw(self):
        """ 
        Draws the game to the default output 
        """
        self._screen.fill(self.WHITE)
        self._draw_borders()

        # TODO: DRAWING PART, TO BE REFACTORED! 
        self._draw_space(self._space)
        
        pygame.display.flip()

    def _draw_space(self, space):
        """ 
        # TODO: DRAWING PART, TO BE REFACTORED! 
        # """
        for x, row in enumerate(self._space):
            # Take offset into account in this hack
            for y, elm in enumerate(row):
                if isinstance(elm, EmptyElement):
                    position = self._translate_coords(x, y)
                    pygame.draw.rect(self._screen, self.WHITE, (position[0], position[1], SPACE_QUANTUM, SPACE_QUANTUM))

                elif isinstance(elm, Edible):
                    position = self._translate_coords(x, y)
                    pygame.draw.rect(self._screen, self.RED, (position[0], position[1], SPACE_QUANTUM, SPACE_QUANTUM))

                elif isinstance(elm, Snake):
                    position = self._translate_coords(x, y)
                    pygame.draw.rect(self._screen, self.GREEN, (position[0], position[1], SPACE_QUANTUM, SPACE_QUANTUM))

                    # Shouldn't happen.
                else:
                    print ("- BAD: ({},{}) -> {}".format(x, y, elm))

    # TODO: TO BE REFACTORED
    def _translate_coords(self, x, y):
        """ 
        Translates our cartesian representation to the coordinate sytem understood by pygame
        """
        return SPACE_BORDER_WIDTH + (x * SPACE_QUANTUM), SPACE_BORDER_WIDTH + (y * SPACE_QUANTUM)

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
                    self._keep_running = False

                # TODO: JPM to remove this.
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_d):
                    print ("DEBUG DEBUGDEBUGDEBUGDEBUG")
                    #self._edible.set_position(self._space.get_random_unoccupied_position())
                    #self._space.free((3,5))
                    self.update()

                # Tick
                elif event.type == GAME_QUANTUM_EVENT:
                    # self.update()
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

        # Out of the loop.                    
        pygame.quit()


# ----------------------------------------------------
if __name__ == "__main__":
    game = SnakeGame()
    game.run()