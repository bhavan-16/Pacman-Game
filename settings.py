# settings.py

TILE_SIZE = 16

# Map size: 28 cols × 27 rows (see LEVEL_MAP)
COLS = 28
ROWS = 27
HUD_HEIGHT = 72

SCREEN_WIDTH = COLS * TILE_SIZE
SCREEN_HEIGHT = ROWS * TILE_SIZE + HUD_HEIGHT
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)          # Blinky
PINK = (255, 105, 180)     # Pinky
CYAN = (0, 255, 255)       # Inky
ORANGE = (255, 165, 0)     # Clyde
BLUE = (0, 0, 255)         # Walls
HUD_BG = (10, 10, 10)

# Speeds (pixels per frame)
PACMAN_SPEED = 2
GHOST_SPEED = 2
FRIGHTENED_SPEED = 1

# Scoring
PELLET_POINTS = 10
POWER_POINTS = 50
GHOST_POINTS = [200, 400, 800, 1600]

# Timings (ms)
POWER_DURATION = 6000
RESPAWN_INVINCIBLE = 2000

# Scatter/Chase schedule in seconds (classic-ish)
SCATTER_CHASE_CYCLE = [7, 20, 7, 20, 5, 20, 5]  # scatter, chase, ...
