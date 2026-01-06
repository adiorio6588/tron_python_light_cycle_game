import pygame
import sys
import random

# -----------------------------
# CONFIG
# -----------------------------
CELL_SIZE = 20
GRID_WIDTH = 40
GRID_HEIGHT = 30
WIDTH = GRID_WIDTH * CELL_SIZE
HEIGHT = GRID_HEIGHT * CELL_SIZE
FPS = 12

BLACK = (0, 0, 0)
BLUE = (0, 200, 255)
RED = (255, 80, 80)
GRAY = (40, 40, 40)
WHITE = (240, 240, 240)
YELLOW = (255, 220, 80)

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRS = [UP, DOWN, LEFT, RIGHT]

# -----------------------------
# PLAYER CLASS
# -----------------------------
class LightCycle:
    def __init__(self, color, start_pos, direction, name="Player"):
        self.color = color
        self.direction = direction
        self.trail = [start_pos]
        self.alive = True
        self.name = name

    @property
    def head(self):
        return self.trail[-1]

    def move(self):
        if not self.alive:
            return
        x, y = self.head
        dx, dy = self.direction
        self.trail.append((x + dx, y + dy))

    def change_direction(self, new_dir):
        # Prevent reversing
        if (-new_dir[0], -new_dir[1]) != self.direction:
            self.direction = new_dir

    def draw(self, surface):
        for x, y in self.trail:
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, self.color, rect)


# -----------------------------
# HELPERS
# -----------------------------
def draw_grid(surface):
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(surface, GRAY, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(surface, GRAY, (0, y), (WIDTH, y))

def in_bounds(pos):
    x, y = pos
    return 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT

def build_occupied(players):
    occ = set()
    for p in players:
        # include full trail
        occ.update(p.trail)
    return occ

def will_collide(next_pos, occupied):
    return (not in_bounds(next_pos)) or (next_pos in occupied)

def next_pos_from(head, direction):
    x, y = head
    dx, dy = direction
    return (x + dx, y + dy)

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def safe_directions(head, current_dir, occupied):
    # Try forward/left/right first feel, but we will score anyway.
    candidates = []
    for d in DIRS:
        # don’t allow reverse
        if (-d[0], -d[1]) == current_dir:
            continue
        np = next_pos_from(head, d)
        if not will_collide(np, occupied):
            candidates.append(d)
    return candidates

def choose_ai_direction(ai, human, occupied, aggression=0.35):
    """
    Simple AI:
    1) Only choose moves that are safe (no immediate collision).
    2) Score each safe move by:
       - how much free space it gives (basic lookahead)
       - (sometimes) how much it reduces distance to the human
    """
    candidates = safe_directions(ai.head, ai.direction, occupied)
    if not candidates:
        return ai.direction  # doomed, keep moving

    hunt = random.random() < aggression

    best = None
    best_score = -10**9

    for d in candidates:
        np = next_pos_from(ai.head, d)

        # --- tiny lookahead: count how many safe options we'd have next turn
        # (crude "space" metric)
        # Temporarily mark next position as occupied (since AI leaves trail)
        occ2 = set(occupied)
        occ2.add(np)
        future_moves = safe_directions(np, d, occ2)
        space_score = len(future_moves) * 10

        # --- distance score (lower is better) if hunting
        dist_score = 0
        if hunt:
            dist_score = (50 - manhattan(np, human.head))  # higher is better

        # --- keep moving straight preference (smoothness)
        straight_bonus = 2 if d == ai.direction else 0

        score = space_score + dist_score + straight_bonus

        # add a small random jitter so AI isn't too predictable
        score += random.randint(-1, 1)

        if score > best_score:
            best_score = score
            best = d

    return best if best is not None else ai.direction


def reset_game(mode):
    # mode: "1P" or "2P"
    p1 = LightCycle(BLUE, (10, GRID_HEIGHT // 2), RIGHT, name="Player 1")
    if mode == "2P":
        p2 = LightCycle(RED, (GRID_WIDTH - 10, GRID_HEIGHT // 2), LEFT, name="Player 2")
    else:
        p2 = LightCycle(RED, (GRID_WIDTH - 10, GRID_HEIGHT // 2), LEFT, name="AI")
    return p1, p2

# -----------------------------
# UI
# -----------------------------
def draw_center_text(screen, font, text, y, color=WHITE):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, y))
    screen.blit(surf, rect)

def menu_loop(screen, clock):
    title_font = pygame.font.SysFont(None, 72)
    font = pygame.font.SysFont(None, 36)

    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "1P"
                if event.key == pygame.K_2:
                    return "2P"

        screen.fill(BLACK)
        draw_grid(screen)

        draw_center_text(screen, title_font, "TRON", HEIGHT // 2 - 120, YELLOW)
        draw_center_text(screen, font, "Press 1: Single Player vs AI", HEIGHT // 2 - 20)
        draw_center_text(screen, font, "Press 2: Two Player", HEIGHT // 2 + 20)
        draw_center_text(screen, font, "WASD = P1   Arrows = P2", HEIGHT // 2 + 70, GRAY)

        pygame.display.flip()

def game_over_overlay(screen, font, winner_text):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))
    draw_center_text(screen, font, "GAME OVER", HEIGHT // 2 - 40, WHITE)
    draw_center_text(screen, font, winner_text, HEIGHT // 2, YELLOW)
    draw_center_text(screen, font, "Press R to Restart | ESC for Menu", HEIGHT // 2 + 50, WHITE)

# -----------------------------
# MAIN GAME
# -----------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TRON Light Cycles")
    clock = pygame.time.Clock()

    hud_font = pygame.font.SysFont(None, 28)
    big_font = pygame.font.SysFont(None, 44)

    mode = menu_loop(screen, clock)
    player1, player2 = reset_game(mode)
    game_over = False
    winner_text = ""

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Global
                if event.key == pygame.K_ESCAPE:
                    mode = menu_loop(screen, clock)
                    player1, player2 = reset_game(mode)
                    game_over = False
                    winner_text = ""
                    continue

                if game_over:
                    if event.key == pygame.K_r:
                        player1, player2 = reset_game(mode)
                        game_over = False
                        winner_text = ""
                    continue

                # Player 1 controls (always human)
                if event.key == pygame.K_w:
                    player1.change_direction(UP)
                elif event.key == pygame.K_s:
                    player1.change_direction(DOWN)
                elif event.key == pygame.K_a:
                    player1.change_direction(LEFT)
                elif event.key == pygame.K_d:
                    player1.change_direction(RIGHT)

                # Player 2 controls only in 2P mode
                if mode == "2P":
                    if event.key == pygame.K_UP:
                        player2.change_direction(UP)
                    elif event.key == pygame.K_DOWN:
                        player2.change_direction(DOWN)
                    elif event.key == pygame.K_LEFT:
                        player2.change_direction(LEFT)
                    elif event.key == pygame.K_RIGHT:
                        player2.change_direction(RIGHT)

        if not game_over:
            # AI picks direction (only in 1P mode)
            if mode == "1P":
                occupied_now = build_occupied([player1, player2])
                # IMPORTANT: allow AI's current head because it will move off it
                # (occupied set includes head, which is fine because next_pos differs)
                player2.change_direction(choose_ai_direction(player2, player1, occupied_now, aggression=0.40))

            # Move both
            player1.move()
            player2.move()

            # Collision check with trails + walls:
            players = [player1, player2]
            occupied_after = build_occupied(players)

            # Each player collides if their head is out of bounds or hits any trail (including opponent)
            def player_dead(p):
                h = p.head
                if not in_bounds(h):
                    return True
                # if head appears earlier in ANY trail => collision
                for other in players:
                    if h in other.trail[:-1]:
                        return True
                return False

            p1_dead = player_dead(player1)
            p2_dead = player_dead(player2)

            if p1_dead or p2_dead:
                game_over = True
                player1.alive = not p1_dead
                player2.alive = not p2_dead

                if p1_dead and p2_dead:
                    winner_text = "Draw!"
                elif p2_dead:
                    winner_text = "Player 1 Wins!"
                else:
                    winner_text = ("AI Wins!" if mode == "1P" else "Player 2 Wins!")

        # Draw
        screen.fill(BLACK)
        draw_grid(screen)
        player1.draw(screen)
        player2.draw(screen)

        # HUD
        mode_text = "1P vs AI" if mode == "1P" else "2P"
        hud = hud_font.render(f"Mode: {mode_text}   (ESC = Menu)", True, GRAY)
        screen.blit(hud, (10, 10))

        if game_over:
            game_over_overlay(screen, big_font, winner_text)

        pygame.display.flip()


if __name__ == "__main__":
    main()
