import sys
from AudioIn import AudioIn
import numpy as np
import pygame
import random
import sys
import time

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (10, 188, 0)
GREY = (210, 210, 210)
RED = (250, 34, 34)
ORANGE = (255, 215, 0)

CELL_SIZE = 20
BOARD_HEIGHT = 20
BOARD_WIDTH = 40
WALL_SIZE = 1

SCREENWIDTH = CELL_SIZE * BOARD_WIDTH
SCREENHEIGHT = CELL_SIZE * BOARD_HEIGHT

def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)


class Spectrum:

    def __init__(self, fps=10):
        pygame.init()

        size = (SCREENWIDTH, SCREENHEIGHT)
        self.screen = pygame.display.set_mode(size)
        pygame.display.set_caption("Cells")

        self.fps = fps

        # This will be a list that will contain all the sprites we intend to use in our game.
        self.all_sprites_list = pygame.sprite.Group()
        self.all_cells_rows = list()

        self.init_cells()

        # save the last value for every frequency
        self.max_values = [0 for _ in range (BOARD_WIDTH)]

        # init pyaudio input device at default device (None)
        #print(self.myaudio.get_input_devices_info())
        self.myaudio = AudioIn()
        self.myaudio.start_stream(output=False, device=None)
        self.show_spectrum = True

        # Allowing the user to close the window...
        carry_on = True
        clock = pygame.time.Clock()

        while carry_on:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    carry_on = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_KP_MINUS]:
                self.fps -= 1
            if keys[pygame.K_KP_PLUS]:
                self.fps += 1
            if keys[pygame.K_ESCAPE]:
                pygame.quit()
                sys.exit()
            if keys[pygame.K_SPACE]:
                time.sleep(0.1)
                if self.show_spectrum:
                    self.myaudio.stop_stream()
                    self.show_spectrum = False
                else:
                    self.myaudio.start_stream(output=False, device=None)
                    self.show_spectrum = True

            # Game Logic
            # self.all_sprites_list.update()
            data = self.make_spectrum_data(self.myaudio.audio)
            self.update_cells(data)

            # draw all the sprites in one go
            self.all_sprites_list.draw(self.screen)

            # draw fps
            #self.draw_fps()

            # Refresh Screen
            pygame.display.flip()

            # Number of frames per second
            clock.tick(self.fps)

        pygame.quit()

    def make_spectrum_data(self, data):

        # define spectrogram
        t = np.linspace(0, 1, len(data))
        s = data
        T = t[1] - t[0]  # sampling interval
        N = s.size
        fft = np.fft.fft(data)
        # 1/T = frequency
        f = np.linspace(0, 1 / T, N)
        abs_data = np.abs(fft)
        bar_data = abs_data[:N // 2] * 1 / N

        l = len(bar_data)
        r = int(l / BOARD_WIDTH)
        the_data = []
        for i in range(BOARD_WIDTH):
            m = 0
            for p in range(r):
                m += bar_data[i * r + p]
            the_data.append(int(m / r))
        return the_data

    def update_cells(self, the_data):
        #the_data = [random.randint(0, BOARD_HEIGHT) for x in range(BOARD_WIDTH)]
        #print(the_data)
        if not self.show_spectrum:
            the_data = [0 for x in range (BOARD_WIDTH)]
        for i, val in enumerate(the_data):
            if val > self.max_values[i]:
                if val > BOARD_HEIGHT:
                    self.max_values[i] = BOARD_HEIGHT
                else:
                    self.max_values[i] = val
            elif self.max_values[i] > 0:
                self.max_values[i] -= 1

        for x in range(BOARD_WIDTH):
            for y in range(BOARD_HEIGHT):
                if y < BOARD_HEIGHT - self.max_values[x]:
                    color = WHITE
                elif y < 2:
                    color = RED
                elif y < 5:
                    color = ORANGE
                else:
                    color = GREEN
                cell = self.all_cells_rows[y][x]
                cell.fill(color)
                cell.draw_walls()

    # initiates all cells with WHITE bg and saves them to all sprites and to all_cells_rows
    def init_cells(self):
        for y in range(BOARD_HEIGHT):
            row = list()
            for x in range(BOARD_WIDTH):
                cell = Cell(WHITE, CELL_SIZE, CELL_SIZE)
                cell.rect.x = x * CELL_SIZE
                cell.rect.y = y * CELL_SIZE
                # Add the car to the list of objects
                self.all_sprites_list.add(cell)
                row.append(cell)
            self.all_cells_rows.append(row)

    def draw_fps(self):
        # defining a font
        smallfont = pygame.font.SysFont('Corbel', 35)
        # rendering text
        text = smallfont.render("fps: "+str(self.fps), True, BLACK)
        # superimposing the text onto our button
        self.screen.blit(text, (SCREENWIDTH - 100, SCREENHEIGHT - 50))


class Cell(pygame.sprite.Sprite):
    # This class represents a cell. It derives from the "Sprite" class in Pygame.

    def __init__(self, color, width, height):
        # Call the parent class (Sprite) constructor
        super().__init__()

        self.width = width
        self.height = height
        self.visited = False
        self.wall_right = True
        self.wall_below = True
        self.wall_left = True
        self.wall_above = True

        # Set the background color and set it to be transparent
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        # self.image.set_colorkey(BLACK)

        # Fetch the rectangle object that has the dimensions of the image.
        self.rect = self.image.get_rect()

    def fill(self, color):
        # self.image.fill(color)
        pygame.draw.rect(self.image, color, [0, 0, self.width, self.height])

    def draw_walls(self):
        if self.wall_left:
            r = pygame.Rect(
                (0, 0),
                (WALL_SIZE, CELL_SIZE + WALL_SIZE))
            # self.image.fill(BLACK)
            pygame.draw.rect(self.image, BLACK, r, 0)
        if self.wall_right:
            r = pygame.Rect(
                (CELL_SIZE - WALL_SIZE, 0),
                (WALL_SIZE, CELL_SIZE + WALL_SIZE))
            pygame.draw.rect(self.image, BLACK, r, 0)
        if self.wall_above:
            r = pygame.Rect(
                (0, 0),
                (CELL_SIZE + WALL_SIZE, WALL_SIZE))
            pygame.draw.rect(self.image, BLACK, r, 0)
        if self.wall_below:
            r = pygame.Rect(
                (0, CELL_SIZE - WALL_SIZE),
                (CELL_SIZE + WALL_SIZE, WALL_SIZE))
            pygame.draw.rect(self.image, BLACK, r, 0)

if __name__ == '__main__':
    cells = Spectrum(fps=20)
