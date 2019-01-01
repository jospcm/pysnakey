import sys
import pygame
import random
import numpy

# Optional, only for PC, this is why we override the previous space definition
SPACE_DIMENSIONS = (520, 520)
SPACE_BORDER_WIDTH = 10
SPACE_QUANTUM = 50
SPACE_FPS = 20

# Affects the speed of the game
GAME_DIFFICULTY = 10
GAME_QUANTUM = SPACE_FPS * GAME_DIFFICULTY
GAME_QUANTUM_EVENT = pygame.USEREVENT

# ----------------------------------------------------
class GameOver(BaseException):
    def __init__(self, str, *args, **kwargs):
        print(str)

class InvalidPositionGameOver(GameOver):
    def __init__(self, str, *args, **kwargs):
        super(InvalidPositionGameOver, self).__init__(args, kwargs)

class AteItselfGameOver(GameOver):
    def __init__(self, str, *args, **kwargs):
        super(AteItselfGameOver, self).__init__(args, kwargs)

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

# ----------------------------------------------------
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

    def is_valid(self, position):
        x, y = position        
        return (0 <= x < len(self._space)) and (0 <= y < len(self._space[0]))

    def occupy(self, position, value):
        x, y = position
        if self.is_valid(position):
            self._space[x][y] = value
        else:
            raise ValueError("Invalid position passed to occupy. Giving up.")

    def free(self, position):
        x, y = position
        elm  = self._space[x][y]
        self._space[x][y] = EmptyElement()

    def is_occupied(self, position):
        if self.is_valid(position):
            x, y = position
            return self._space[x][y] != EmptyElement()
        else:
            raise ValueError("Invalid position provided. Giving up.")

    def is_of_type(self, position, which_type):
        """ 
        Returns true if element at the specified position is of the given type
        """
        if self.is_valid(position):
            x, y = position
            return isinstance(self._space[x][y], which_type)
        return False

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

    def __setitem__(self, key, value):
        try:
            x, y = key
            self._space[x][y] = value
        except Exception as e:
            # Bad.
            raise ValueError("Cannot set space item. Invalid key provided. Expected: sequence with 2+ elements.")

    def __getitem__(self, key):
        try:
            x, y = key
            return self._space[x][y]
        except Exception as e:
            # Bad.
            raise ValueError("Cannot retrieve space item. Invalid key provided. Expected: sequence with 2+ elements.")

    def __iter__(self):
        return self._space.__iter__()

    def __next__(self):
        return self._space.__next__()

# ----------------------------------------------------
class Snake(Element):
    class Node():
        """
        Represents a part of the snake.
        """
        def __init__(self, position):
            self._position = position

    def __init__(self, position = None, direction = None):
        if position is None:
            raise ValueError("Invalid initial provided to the mighty snake. Cannot proceed.")

        if direction is None:
            raise ValueError("Invalid initial vector to the mighty snake. Cannot proceed.")
        
        self._nodes = []
        for pos in position:
            self._nodes.append(Snake.Node(pos))

        self._direction = direction
        pass

    def update(self, game, direction):
        # Updating the snake is essentially creating a new node, and destroying the last one.
        new_velocity = self._derive_vector(direction)
        new_position = list(numpy.add(new_velocity, self._nodes[-1]._position))
        
        should_grow = game.should_grow(new_position)
        self._nodes.append(Snake.Node(new_position))

        # Delete the last one, unless we have to grow.
        if not should_grow:
            last = self._nodes.pop(0)
            
            # Free the last position, so it can be redrawn
            game.free(last._position)
        
        for pos in self._nodes:
            game.occupy(pos._position, self)

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
class Edible(Element):
    def __init__(self, position = None):
        if position is None:
            raise ValueError("Invalid position provided to the delicious edible. Cannot proceed.")
        self._position = position
        self._new_position = position
        pass

    def set_position(self, position):
        self._new_position = position

    def update(self, game):
        if self._position != self._new_position:
            self._position = self._new_position

        game.occupy(self._position, self)
        pass

# ----------------------------------------------------
class SnakeUI():
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (128, 0, 0)
    GREEN = (0, 128, 0)

    def __init__(self):
        self._screen = pygame.display.set_mode(SPACE_DIMENSIONS)
        pass

    def draw(self, space):
        self._screen.fill(SnakeUI.BLACK)
        self._draw_borders()

        # Effectively draws the game.
        self._draw_space(space)
        
        pygame.display.flip()

    def _draw_space(self, space):
        """ 
        # TODO: DRAWING PART, TO BE REFACTORED! 
        # """
        for x, row in enumerate(space):
            # Take offset into account in this hack
            for y, elm in enumerate(row):
                if isinstance(elm, EmptyElement):
                    position = self._translate_coords(x, y)
                    pygame.draw.rect(self._screen, SnakeUI.WHITE, (position[0], position[1], SPACE_QUANTUM, SPACE_QUANTUM))

                elif isinstance(elm, Edible):
                    position = self._translate_coords(x, y)
                    pygame.draw.rect(self._screen, SnakeUI.RED, (position[0], position[1], SPACE_QUANTUM, SPACE_QUANTUM))

                elif isinstance(elm, Snake):
                    position = self._translate_coords(x, y)
                    pygame.draw.rect(self._screen, SnakeUI.GREEN, (position[0], position[1], SPACE_QUANTUM, SPACE_QUANTUM))

                else:
                    # Shouldn't happen.
                    print ("- BAD: ({},{}) -> {}".format(x, y, elm))

    def _draw_borders(self):
        """ 
        Borders are nothing but a hollow rectangular shape encompassing the screen. 
        """
        pygame.draw.rect(self._screen, SnakeUI.BLACK, (0, 0, SPACE_DIMENSIONS[0], SPACE_DIMENSIONS[1]), SPACE_BORDER_WIDTH)

    def _translate_coords(self, x, y):
        """ 
        Translates our cartesian representation to the coordinate sytem understood by pygame
        """
        return SPACE_BORDER_WIDTH + (x * SPACE_QUANTUM), SPACE_BORDER_WIDTH + (y * SPACE_QUANTUM)

# ----------------------------------------------------
class SnakeGame():
    """
    Holds the logic of the game. Essentially controls how the parts fit together.
 
    This assumes that any entity occupies a single pixel on the screen, and leaves the overhead of the rendering
    to the responsible module. Or it will do that, at some point.
    """
    POSITIONAL_AXES = ( (KeyPress(KeyPress.LEFT), KeyPress(KeyPress.RIGHT)), (KeyPress(KeyPress.UP), KeyPress(KeyPress.DOWN)) )

    class Logic:
        def __init__(self, space):
            self._space = space

        def should_grow(self, potential_position):
            if not self._space.is_valid(potential_position):
                raise InvalidPositionGameOver("The snake has hit a wall! Game Over!")
            
            # If space is not occupied, it's all fine.
            if not self._space.is_occupied(potential_position):
                return False

            # It seems that the snake has eaten itself!
            if self._space.is_of_type(potential_position, Snake):
                raise AteItselfGameOver("The snake has eaten itself! Game Over!")

            # Space seems to be occupied, so it's either by the snake (game over) or by an edible
            if self._space.is_of_type(potential_position, Edible):
                self._space[potential_position].set_position(self._space.get_random_unoccupied_position())
                return True

            return False
        
        def occupy(self, position, who):
            self._space.occupy(position, who)
        
        def free(self, position):
            self._space.free(position)
    
    def __init__(self, ui):
        # A snapshot of our snakey universe.
        self._space = Space(SPACE_DIMENSIONS, SPACE_QUANTUM, SPACE_BORDER_WIDTH)
        self._game = SnakeGame.Logic(self._space)

        # Movement
        self._pressed_key = None
        
        # Snake expects a list of positions, even though the list is one.
        self._direction = KeyPress(KeyPress.DOWN)
        self._snake = Snake([[4, 0]], self._direction)
        self._edible = Edible([1,0])

        # Engine specific code
        pygame.init()
        self._timer = pygame.time.Clock()
        pygame.time.set_timer(GAME_QUANTUM_EVENT, GAME_QUANTUM)

        # Indicate when to quit
        self._keep_running = True
        self._ui = ui

    def update_position(self):
        current_direction = self._direction
        proposed_direction = self._pressed_key

        # Check if change of movement is valid
        if proposed_direction is not None:
            valid_movement = self._is_movement_valid(current_direction, proposed_direction)
            if valid_movement:
                self._direction.set(self._pressed_key)
                print("+ direction:", str(proposed_direction))
            else:
                print ("Invalid direction passed: ", str(proposed_direction))

    def update(self):
        """ 
        Updates the internal state of the game 
        """
        try:
            self._snake.update(self._game, self._direction)
        except GameOver as e:
            print ("You've died!")
            print(e)
            self._keep_running = False

        self._edible.update(self._game)

    # ----------------- DRAWING BELOW
    def draw(self):
        """ 
        Draws the game to the default output 
        """
        self._ui.draw(self._space)

    # ----------------- DRAWING ABOVE.
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

                # Tick
                elif event.type == GAME_QUANTUM_EVENT:
                    self.update_position()
                    self.update()
                    self.draw()

                elif event.type == pygame.KEYDOWN:
                    # Cache the previous movement in case the change is not valid.
                    parsed_key = self._parse_key_press(event.key)
                    if KeyPress.is_valid(parsed_key):
                        self._pressed_key = KeyPress(parsed_key)
                        
                        current_direction = self._direction
                        proposed_direction = self._pressed_key
                        
                        print("+ proposed direction:", str(proposed_direction))
    
                        
        # Out of the loop.                    
        pygame.quit()

# ----------------------------------------------------
if __name__ == "__main__":
    game = SnakeGame(SnakeUI())
    game.run()