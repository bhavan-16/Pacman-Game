# game/ghost.py
import random
from collections import deque
import pygame
from settings import TILE_SIZE, GHOST_SPEED, FRIGHTENED_SPEED, RED, PINK, CYAN, ORANGE

VEC = pygame.math.Vector2
DIRS = [VEC(1, 0), VEC(-1, 0), VEC(0, 1), VEC(0, -1)]

def aligned_to_grid(rect):
    return rect.left % TILE_SIZE == 0 and rect.top % TILE_SIZE == 0

def tile_of(rect):
    return rect.left // TILE_SIZE, rect.top // TILE_SIZE

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def neighbors(game_map, tx, ty):
    """Cardinal neighbors, respecting walls and *only* wrapping on tunnel rows."""
    cols, rows = game_map.cols, game_map.rows
    nb = []
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx, ny = tx + dx, ty + dy
        # vertical bounds
        if ny < 0 or ny >= rows:
            continue
        # horizontal wrap only on tunnel rows
        if nx < 0 or nx >= cols:
            if ny in game_map.tunnel_rows:
                nx %= cols
            else:
                continue
        if not game_map.tile_blocked(nx, ny):
            nb.append((nx, ny))
    return nb

def first_step_bfs(game_map, start, goal):
    """Return the first step (dx,dy) from start toward goal using BFS; None if no path."""
    if start == goal:
        return None
    q = deque([start])
    came_from = {start: None}
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for nxt in neighbors(game_map, *cur):
            if nxt not in came_from:
                came_from[nxt] = cur
                q.append(nxt)
    if goal not in came_from:
        return None
    # backtrack to find the first step
    step = goal
    while came_from[step] != start:
        step = came_from[step]
        if step is None:
            return None
    dx = step[0] - start[0]
    dy = step[1] - start[1]
    return VEC(dx, dy)

class Ghost:
    def __init__(self, x, y, name="blinky", color=RED, home_tile=None):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.color = color
        self.name = name

        # Modes: scatter | chase | frightened | eaten
        self.mode = "scatter"
        self._prev_mode = self.mode

        self.speed = GHOST_SPEED
        self.dir = VEC(1, 0)  # start moving right

        # Scatter corners (approx)
        self.scatter_target = {
            "blinky": (27, 0),
            "pinky": (0, 0),
            "inky": (27, 26),
            "clyde": (0, 26),
        }[name]

        # Home tile (reachable outside door); provided by factory
        self.home_tile = home_tile if home_tile is not None else tile_of(self.rect)

        # Non-Blinky ghosts wait briefly before leaving at game start
        self.leave_counter = 60 if name != "blinky" else 0
        self.in_house = (name != "blinky")

        # Eaten/respawn bookkeeping
        self.eaten_time = None          # ms timestamp when eaten
        self.respawn_delay = 2000       # ms to wait at home before respawn

    def legal_dirs(self, game_map):
        tx, ty = tile_of(self.rect)
        opts = []
        for d in DIRS:
            nx, ny = tx + int(d.x), ty + int(d.y)
            # respect the same wrap rule as movement
            if ny < 0 or ny >= game_map.rows:
                continue
            if nx < 0 or nx >= game_map.cols:
                if ty in game_map.tunnel_rows:
                    nx %= game_map.cols
                else:
                    continue
            if not game_map.tile_blocked(nx, ny):
                opts.append(d)
        return opts

    def choose_dir_greedy(self, game_map, target, forbid_dir):
        """Greedy Manhattan step toward target. Optionally forbid immediate reverse."""
        tx, ty = tile_of(self.rect)
        best = None
        bestdist = 1e9
        for d in self.legal_dirs(game_map):
            if forbid_dir and d.x == -forbid_dir.x and d.y == -forbid_dir.y:
                continue
            nx, ny = tx + int(d.x), ty + int(d.y)
            dist = manhattan((nx, ny), target)
            if dist < bestdist:
                bestdist = dist
                best = d
        if best is None:
            # dead end -> reverse if possible
            best = VEC(-forbid_dir.x, -forbid_dir.y) if forbid_dir else VEC(0, 0)
        return best

    def frightened_step(self, game_map):
        choices = self.legal_dirs(game_map)
        if self.dir != VEC(0, 0) and len(choices) > 1:
            # avoid reversing unless forced
            choices = [d for d in choices if not (d.x == -self.dir.x and d.y == -self.dir.y)] or choices
        return random.choice(choices) if choices else VEC(0,0)

    def target_tile(self, pac_tile, pac_dir, blinky_tile):
        if self.name == "blinky":
            return pac_tile
        if self.name == "pinky":
            return (pac_tile[0] + int(pac_dir.x) * 4,
                    pac_tile[1] + int(pac_dir.y) * 4)
        if self.name == "inky":
            ahead = (pac_tile[0] + int(pac_dir.x) * 2,
                     pac_tile[1] + int(pac_dir.y) * 2)
            vx, vy = ahead[0] - blinky_tile[0], ahead[1] - blinky_tile[1]
            return (ahead[0] + vx, ahead[1] + vy)
        if self.name == "clyde":
            if manhattan(pac_tile, tile_of(self.rect)) >= 8:
                return pac_tile
            return self.scatter_target
        return pac_tile

    def update(self, game_map, pacman, blinky_tile, frightened=False):
        now = pygame.time.get_ticks()
        just_switched = (self.mode != self._prev_mode)
        self._prev_mode = self.mode

        if aligned_to_grid(self.rect):
            # 1) initial house wait
            if self.in_house:
                self.leave_counter -= 1
                if self.leave_counter > 0:
                    return  # hold position in house
                self.in_house = False  # leave next decision

            pac_tile = tile_of(pacman.rect)
            pac_dir = pacman.dir

            if self.mode == "frightened":
                self.speed = FRIGHTENED_SPEED
                # allow reverse on switch-in to frightened
                self.dir = self.frightened_step(game_map) if not just_switched \
                           else self.choose_dir_greedy(game_map, tile_of(self.rect), None)

            elif self.mode == "eaten":
                self.speed = GHOST_SPEED + 1
                start_tile = tile_of(self.rect)

                # Use BFS for eaten -> home path (reliable even in tricky mazes)
                step = first_step_bfs(game_map, start_tile, self.home_tile)
                if step is None:
                    # fallback to greedy; allow reverse on mode switch
                    self.dir = self.choose_dir_greedy(
                        game_map, self.home_tile, None if just_switched else self.dir
                    )
                else:
                    self.dir = step

                # Snap and wait when close to home
                hx, hy = self.home_tile[0] * TILE_SIZE, self.home_tile[1] * TILE_SIZE
                if abs(self.rect.left - hx) < 4 and abs(self.rect.top - hy) < 4:
                    self.rect.topleft = (hx, hy)
                    self.dir = VEC(0, 0)
                    if self.eaten_time is None:
                        self.eaten_time = now
                    if now - self.eaten_time >= self.respawn_delay:
                        self.mode = "scatter"
                        self.eaten_time = None
                    return  # stay parked until respawn

            else:
                # scatter / chase
                self.speed = GHOST_SPEED
                target = self.scatter_target if self.mode == "scatter" \
                         else self.target_tile(pac_tile, pac_dir, blinky_tile)
                # permit reverse on scatter<->chase switch
                self.dir = self.choose_dir_greedy(
                    game_map, target, None if just_switched else self.dir
                )

        # move (wrapping only on tunnel rows)
        self.rect.left += int(self.dir.x) * self.speed
        self.rect.top  += int(self.dir.y) * self.speed

        cols = game_map.cols
        if self.rect.top // TILE_SIZE in game_map.tunnel_rows:
            if self.rect.left < 0:
                self.rect.left = (cols - 1) * TILE_SIZE
            elif self.rect.left >= cols * TILE_SIZE:
                self.rect.left = 0

    def draw(self, screen):
        color = self.color
        if self.mode == "frightened":
            color = (0, 0, 255)
        elif self.mode == "eaten":
            color = (255, 255, 255)  # white while eyes would be nicer; easy to add later
        pygame.draw.rect(screen, color, self.rect)

# --------- factory ----------------------------------------------------------
def _compute_home_outside(spawns, game_map):
    """
    Compute a reachable 'home' just outside the ghost house:
    - Take the span of G columns and look one row ABOVE the top-most G row.
    - Pick the first non-wall tile across that span.
    - If none, try one row BELOW. If still none, widen search a bit.
    """
    if not spawns:
        return (14, 11)  # fallback

    tiles = [(x // TILE_SIZE, y // TILE_SIZE) for (x, y) in spawns]
    min_x = min(tx for tx, _ in tiles)
    max_x = max(tx for tx, _ in tiles)
    top_y = min(ty for _, ty in tiles)
    rows = [top_y - 1, top_y + 1, top_y - 2, top_y + 2]  # search order

    for ry in rows:
        if ry < 0 or ry >= game_map.rows:
            continue
        for cx in range(min_x, max_x + 1):
            if not game_map.tile_blocked(cx, ry):
                return (cx, ry)

    # ultimate fallback: center column, above top_y if possible
    cx = (min_x + max_x) // 2
    ry = max(0, top_y - 1)
    return (cx, ry)

def make_ghosts(spawns):
    """
    spawns: list of (x_px, y_px) positions for 'G' tiles from the map.
    We compute a reachable 'home-outside' tile and give it to each ghost.
    """
    # We need a GameMap instance to compute home; import lazily to avoid circular import
    from game.map import GameMap
    gmap = GameMap()
    home_outside = _compute_home_outside(spawns, gmap)

    names_colors = [("blinky", RED), ("pinky", PINK), ("inky", CYAN), ("clyde", ORANGE)]
    ghosts = []
    for (x, y), (nm, col) in zip(spawns, names_colors):
        ghosts.append(Ghost(x, y, nm, col, home_outside))
    return ghosts
