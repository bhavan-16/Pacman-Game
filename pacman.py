# game/pacman.py
import pygame
from settings import TILE_SIZE, PACMAN_SPEED, YELLOW, PELLET_POINTS, POWER_POINTS, RESPAWN_INVINCIBLE

VEC = pygame.math.Vector2
DIRS = {
    "UP": VEC(0, -1),
    "DOWN": VEC(0, 1),
    "LEFT": VEC(-1, 0),
    "RIGHT": VEC(1, 0),
    "NONE": VEC(0, 0),
}

def aligned_to_grid(rect):
    return rect.left % TILE_SIZE == 0 and rect.top % TILE_SIZE == 0

class Pacman:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.dir = DIRS["NONE"]
        self.want = DIRS["NONE"]
        self.speed = PACMAN_SPEED
        self.score = 0
        self.lives = 3
        self.invincible_until = 0

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.want = DIRS["UP"]
        elif keys[pygame.K_DOWN]:
            self.want = DIRS["DOWN"]
        elif keys[pygame.K_LEFT]:
            self.want = DIRS["LEFT"]
        elif keys[pygame.K_RIGHT]:
            self.want = DIRS["RIGHT"]

    def can_move(self, game_map, direction):
        nx = self.rect.left + int(direction.x) * TILE_SIZE
        ny = self.rect.top + int(direction.y) * TILE_SIZE
        tx, ty = nx // TILE_SIZE, ny // TILE_SIZE
        return not game_map.tile_blocked(tx, ty)

    def update(self, game_map, now_ms):
        # try turn on grid
        if aligned_to_grid(self.rect) and self.want != self.dir and self.can_move(game_map, self.want):
            self.dir = self.want

        # block if next tile is wall
        if aligned_to_grid(self.rect) and not self.can_move(game_map, self.dir):
            self.dir = DIRS["NONE"]

        # move
        self.rect.left += int(self.dir.x) * self.speed
        self.rect.top  += int(self.dir.y) * self.speed

        # horizontal wrap on tunnels
        cols = game_map.cols
        if self.rect.top // TILE_SIZE in game_map.tunnel_rows:
            if self.rect.left < 0:
                self.rect.left = (cols-1)*TILE_SIZE
            elif self.rect.left >= cols*TILE_SIZE:
                self.rect.left = 0

        # eat pellets
        ate_power = False
        for p in game_map.pellets[:]:
            if self.rect.colliderect(p):
                game_map.pellets.remove(p)
                self.score += PELLET_POINTS
        for p in game_map.power_pellets[:]:
            if self.rect.colliderect(p):
                game_map.power_pellets.remove(p)
                self.score += POWER_POINTS
                ate_power = True
        return ate_power

    def hit_by_ghost(self, now_ms):
        if now_ms >= self.invincible_until and self.lives > 0:
            self.lives -= 1
            self.invincible_until = now_ms + RESPAWN_INVINCIBLE
            # simple respawn near spawn tile
            self.rect.topleft = (self.rect.left//TILE_SIZE*TILE_SIZE, self.rect.top//TILE_SIZE*TILE_SIZE)
            self.dir = DIRS["NONE"]
            self.want = DIRS["NONE"]

    def draw(self, screen, flashing=False):
        if flashing:
            # blink while invincible
            if (pygame.time.get_ticks() // 120) % 2 == 0:
                return
        pygame.draw.circle(screen, YELLOW, self.rect.center, TILE_SIZE//2)
