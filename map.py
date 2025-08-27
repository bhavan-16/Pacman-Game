# game/map.py
import pygame
from settings import TILE_SIZE, BLUE, WHITE

# 28 columns × 27 rows
LEVEL_MAP = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "######.##### ## #####.######",
    "######.##          ##.######",
    "######.## ###GGGG####.######",
    "######.## #      #   .######",
    "######.## #      #   .######",
    "######.## ########   .######",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o..##................##..o#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....P.....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################",
]

WALL = "#"
PELLET = "."
POWER = "o"
PACMAN_SPAWN = "P"
GHOST_SPAWN = "G"
EMPTY = " "

class GameMap:
    def __init__(self):
        self.rows = len(LEVEL_MAP)
        self.cols = len(LEVEL_MAP[0])
        self.walls = []
        self.wall_grid = [[False]*self.cols for _ in range(self.rows)]
        self.pellets = []
        self.power_pellets = []
        self.pacman_spawn = None
        self.ghost_spawns = []

        for r, row in enumerate(LEVEL_MAP):
            for c, ch in enumerate(row):
                x, y = c*TILE_SIZE, r*TILE_SIZE
                if ch == WALL:
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.walls.append(rect)
                    self.wall_grid[r][c] = True
                elif ch == PELLET:
                    self.pellets.append(pygame.Rect(x+6, y+6, 4, 4))
                elif ch == POWER:
                    self.power_pellets.append(pygame.Rect(x+4, y+4, 8, 8))
                elif ch == PACMAN_SPAWN:
                    self.pacman_spawn = (x, y)
                elif ch == GHOST_SPAWN:
                    self.ghost_spawns.append((x, y))

        # tunnel columns (wrap)
        self.tunnel_rows = {9, 17, 22}  # a few rows with long horizontal corridors

    def tile_blocked(self, tx, ty):
        if ty < 0 or ty >= self.rows:
            return True
        # horizontal wrap allowed on tunnel rows
        tx %= self.cols
        return self.wall_grid[ty][tx]

    def draw(self, screen):
        for wall in self.walls:
            pygame.draw.rect(screen, BLUE, wall)
        for p in self.pellets:
            pygame.draw.circle(screen, WHITE, p.center, 2)
        for p in self.power_pellets:
            pygame.draw.circle(screen, WHITE, p.center, 6)
