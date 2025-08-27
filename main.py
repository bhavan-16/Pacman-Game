import pygame
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, HUD_HEIGHT, FPS, WHITE, HUD_BG,
                      GHOST_POINTS, POWER_DURATION)
from game.map import GameMap
from game.pacman import Pacman
from game.ghost import make_ghosts

def reset_world():
    gmap = GameMap()
    pac = Pacman(*gmap.pacman_spawn)
    ghosts = make_ghosts(gmap.ghost_spawns)
    return gmap, pac, ghosts

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pac-Man")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)
    bigfont = pygame.font.SysFont(None, 64)   # Bigger for GAME OVER
    midfont = pygame.font.SysFont(None, 36)   # Medium for Restart text

    game_map, pacman, ghosts = reset_world()

    # mode timers
    schedule = []
    t = 0
    scatter = True
    for i, secs in enumerate([7,20,7,20,5,20,5]):
        schedule.append((t*1000, "scatter" if scatter else "chase"))
        t += secs
        scatter = not scatter
    cycle_length = t*1000

    start_time = pygame.time.get_ticks()
    frightened_until = 0
    eaten_chain = 0
    game_over = False

    running = True
    while running:
        now = pygame.time.get_ticks()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if game_over:
            if keys[pygame.K_r]:
                game_map, pacman, ghosts = reset_world()
                start_time = pygame.time.get_ticks()
                frightened_until = 0
                eaten_chain = 0
                game_over = False
            # Still draw frame
        else:
            pacman.handle_input()
            ate_power = pacman.update(game_map, now)

            # set ghost global mode (scatter/chase) unless frightened/eaten
            elapsed = (now - start_time) % cycle_length
            mode = "chase"
            for ts, m in schedule:
                if elapsed >= ts:
                    mode = m

            if ate_power:
                frightened_until = now + POWER_DURATION
                eaten_chain = 0
                for g in ghosts:
                    if g.mode != "eaten":
                        g.mode = "frightened"

            # update ghosts
            blinky_tile = ghosts[0].rect.left // 16, ghosts[0].rect.top // 16
            for g in ghosts:
                if now < frightened_until and g.mode != "eaten":
                    g.mode = "frightened"
                elif g.mode != "eaten":
                    g.mode = mode
                g.update(game_map, pacman, blinky_tile)

            # collisions
            for g in ghosts:
                if pacman.rect.colliderect(g.rect):
                    if g.mode == "frightened":
                        pacman.score += GHOST_POINTS[min(eaten_chain, 3)]
                        eaten_chain += 1
                        g.mode = "eaten"
                        g.eaten_time = now
                    elif g.mode != "eaten" and now >= pacman.invincible_until:
                        pacman.hit_by_ghost(now)
                        if pacman.lives <= 0:
                            game_over = True

            # win: all pellets eaten
            if not game_over and not game_map.pellets and not game_map.power_pellets:
                game_over = True

        # ----- draw -----
        screen.fill((0,0,0))
        # play area
        game_map.draw(screen)
        pacman.draw(screen, flashing=(now < pacman.invincible_until))
        for g in ghosts:
            g.draw(screen)

        # HUD
        pygame.draw.rect(screen, HUD_BG, (0, SCREEN_HEIGHT-HUD_HEIGHT, SCREEN_WIDTH, HUD_HEIGHT))
        score_text = font.render(f"Score: {pacman.score}", True, WHITE)
        lives_text = font.render(f"Lives: {max(0, pacman.lives)}", True, WHITE)
        screen.blit(score_text, (16, SCREEN_HEIGHT-HUD_HEIGHT+24))
        screen.blit(lives_text, (200, SCREEN_HEIGHT-HUD_HEIGHT+24))

        # GAME OVER message
        if game_over:
            msg1 = bigfont.render("GAME OVER", True, (255, 60, 60))
            msg2 = midfont.render("Press R to Restart", True, WHITE)

            msg1_rect = msg1.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
            msg2_rect = msg2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))

            screen.blit(msg1, msg1_rect)
            screen.blit(msg2, msg2_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
