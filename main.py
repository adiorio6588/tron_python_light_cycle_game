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

# Difficulty presets (you can tweak later)
DIFFICULTY = {
    "Easy":   {"fps": 8,  "aggression": 0.20},
    "Normal": {"fps": 12, "aggression": 0.45},
    "Hard":   {"fps": 16, "aggression": 0.70},
}

ROUNDS_TO_WIN = 3  # best of 5

ASSET_TITLE = "assets/title_screen.png"
MUSIC_PATH = "sound/background_music.wav"

# NEW: sprite paths
BLUE_SPRITE_PATH = "assets/blue_cycle.png"
RED_SPRITE_PATH  = "assets/red_cycle.png"

# -----------------------------
# PLAYER CLASS
# -----------------------------
class LightCycle:
    def __init__(self, color, start_pos, direction, name="Player", sprite=None):
        self.color = color
        self.direction = direction
        self.trail = [start_pos]
        self.alive = True
        self.name = name
        self.sprite = sprite  # pygame.Surface or None

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

    def _rotated_sprite(self):
        """Rotate sprite so it faces current direction.
        Assumes the base sprite faces RIGHT by default.
        """
        if self.sprite is None:
            return None

        if self.direction == RIGHT:
            angle = 0
        elif self.direction == DOWN:
            angle = -90
        elif self.direction == LEFT:
            angle = 180
        else:  # UP
            angle = 90

        return pygame.transform.rotate(self.sprite, angle)

    def draw(self, surface):
        # draw trail as colored blocks (excluding head)
        for x, y in self.trail[:-1]:
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, self.color, rect)

        # draw head as sprite (fallback to block if missing)
        hx, hy = self.head
        head_rect = pygame.Rect(hx * CELL_SIZE, hy * CELL_SIZE, CELL_SIZE, CELL_SIZE)

        spr = self._rotated_sprite()
        if spr:
            # center sprite on the cell
            r = spr.get_rect(center=head_rect.center)
            surface.blit(spr, r)
        else:
            pygame.draw.rect(surface, self.color, head_rect)

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
        occ.update(p.trail)
    return occ

def next_pos_from(head, direction):
    x, y = head
    dx, dy = direction
    return (x + dx, y + dy)

def safe_directions(head, current_dir, occupied):
    candidates = []
    for d in DIRS:
        if (-d[0], -d[1]) == current_dir:
            continue
        np = next_pos_from(head, d)
        if in_bounds(np) and np not in occupied:
            candidates.append(d)
    return candidates

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def choose_ai_direction(ai, human, occupied, aggression=0.45):
    candidates = safe_directions(ai.head, ai.direction, occupied)
    if not candidates:
        return ai.direction

    hunt = random.random() < aggression
    best = ai.direction
    best_score = -10**9

    for d in candidates:
        np = next_pos_from(ai.head, d)

        occ2 = set(occupied)
        occ2.add(np)
        space_score = len(safe_directions(np, d, occ2)) * 10

        dist_score = 0
        if hunt:
            dist_score = (50 - manhattan(np, human.head))

        straight_bonus = 2 if d == ai.direction else 0
        score = space_score + dist_score + straight_bonus + random.randint(-2, 2)

        if score > best_score:
            best_score = score
            best = d

    return best

# UPDATED: pass sprites into reset_round
def reset_round(vs_ai: bool, blue_sprite=None, red_sprite=None):
    p1 = LightCycle(BLUE, (10, GRID_HEIGHT // 2), RIGHT, name="Player 1", sprite=blue_sprite)
    if vs_ai:
        p2 = LightCycle(RED, (GRID_WIDTH - 10, GRID_HEIGHT // 2), LEFT, name="AI", sprite=red_sprite)
    else:
        p2 = LightCycle(RED, (GRID_WIDTH - 10, GRID_HEIGHT // 2), LEFT, name="Player 2", sprite=red_sprite)
    return p1, p2

# -----------------------------
# UI SCREENS
# -----------------------------
def draw_center_text(screen, font, text, y, color=WHITE):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, y))
    screen.blit(surf, rect)

def title_screen(screen, clock, title_image):
    font = pygame.font.SysFont(None, 30)
    blink_timer = 0
    show = True

    while True:
        clock.tick(30)
        blink_timer += 1
        if blink_timer % 20 == 0:
            show = not show

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                return

        screen.blit(title_image, (0, 0))
        if show:
            txt = font.render("PRESS ANY KEY", True, WHITE)
            rect = txt.get_rect(center=(WIDTH // 2, HEIGHT - 11))
            screen.blit(txt, rect)

        pygame.display.flip()

def mode_select_screen(screen, clock):
    title_font = pygame.font.SysFont(None, 54)
    font = pygame.font.SysFont(None, 30)
    small = pygame.font.SysFont(None, 24)

    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return {"vs_ai": True, "best_of": 1}
                if event.key == pygame.K_2:
                    return {"vs_ai": True, "best_of": 5}
                if event.key == pygame.K_3:
                    return {"vs_ai": False, "best_of": 1}
                if event.key == pygame.K_4:
                    return {"vs_ai": False, "best_of": 5}

        screen.fill(BLACK)
        draw_grid(screen)

        draw_center_text(screen, title_font, "SELECT MODE", 90, YELLOW)
        draw_center_text(screen, font, "1) 1-time play vs AI", 170, WHITE)
        draw_center_text(screen, font, "2) Best of 5 vs AI", 210, WHITE)
        draw_center_text(screen, font, "3) 1-time play (2 Player)", 260, WHITE)
        draw_center_text(screen, font, "4) Best of 5 (2 Player)", 300, WHITE)
        draw_center_text(screen, small, "P1 = Arrow Keys | P2 = WASD (2P only)", 360, YELLOW)
        draw_center_text(screen, small, "ESC to quit", 390, YELLOW)

        pygame.display.flip()

# -----------------------------
# MAIN
# -----------------------------
def main():
    pygame.init()

    # Init audio + play background music (loop)
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(MUSIC_PATH)
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1, fade_ms=1500)
    except Exception as e:
        print(f"[WARN] Music not playing: {MUSIC_PATH}\n{e}")

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TRON Light Cycles")
    clock = pygame.time.Clock()

    # Load title image from assets/
    try:
        title_img = pygame.image.load(ASSET_TITLE).convert()
        title_img = pygame.transform.scale(title_img, (WIDTH, HEIGHT))
    except Exception as e:
        print(f"[WARN] Could not load title screen image: {ASSET_TITLE}\n{e}")
        title_img = None

    if title_img:
        title_screen(screen, clock, title_img)

    # Pick mode after title screen
    settings = mode_select_screen(screen, clock)
    vs_ai = settings["vs_ai"]
    best_of = settings["best_of"]

    # Difficulty (kept simple: Normal defaults)
    difficulty = "Normal"
    fps = DIFFICULTY[difficulty]["fps"]
    aggression = DIFFICULTY[difficulty]["aggression"]

    # NEW: load cycle sprites and scale to cell size
    def load_cycle_sprite(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (CELL_SIZE, CELL_SIZE))
            return img
        except Exception as e:
            print(f"[WARN] Could not load sprite: {path}\n{e}")
            return None

    blue_sprite = load_cycle_sprite(BLUE_SPRITE_PATH)
    red_sprite = load_cycle_sprite(RED_SPRITE_PATH)

    # Scores only used in best-of-5
    scores = {"P1": 0, "P2": 0}
    rounds_to_win = 1 if best_of == 1 else ROUNDS_TO_WIN

    # Start first round (UPDATED)
    player1, player2 = reset_round(vs_ai, blue_sprite=blue_sprite, red_sprite=red_sprite)
    round_over = False
    winner_text = ""

    hud_font = pygame.font.SysFont(None, 28)
    big_font = pygame.font.SysFont(None, 44)

    while True:
        clock.tick(fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    pygame.quit()
                    sys.exit()

                if round_over:
                    if event.key == pygame.K_r:
                        # If match already ended, reset match scores
                        if best_of == 5 and (scores["P1"] >= rounds_to_win or scores["P2"] >= rounds_to_win):
                            scores = {"P1": 0, "P2": 0}
                        # UPDATED
                        player1, player2 = reset_round(vs_ai, blue_sprite=blue_sprite, red_sprite=red_sprite)
                        round_over = False
                        winner_text = ""
                    continue

                # Player 1 = ARROW KEYS
                if event.key == pygame.K_UP:
                    player1.change_direction(UP)
                elif event.key == pygame.K_DOWN:
                    player1.change_direction(DOWN)
                elif event.key == pygame.K_LEFT:
                    player1.change_direction(LEFT)
                elif event.key == pygame.K_RIGHT:
                    player1.change_direction(RIGHT)

                # Player 2 = WASD (only in 2P)
                if not vs_ai:
                    if event.key == pygame.K_w:
                        player2.change_direction(UP)
                    elif event.key == pygame.K_s:
                        player2.change_direction(DOWN)
                    elif event.key == pygame.K_a:
                        player2.change_direction(LEFT)
                    elif event.key == pygame.K_d:
                        player2.change_direction(RIGHT)

        if not round_over:
            # AI move
            if vs_ai:
                occ_now = build_occupied([player1, player2])
                player2.change_direction(
                    choose_ai_direction(player2, player1, occ_now, aggression=aggression)
                )

            # Move
            player1.move()
            player2.move()

            players = [player1, player2]

            def player_dead(p):
                h = p.head
                if not in_bounds(h):
                    return True
                for other in players:
                    if h in other.trail[:-1]:
                        return True
                return False

            p1_dead = player_dead(player1)
            p2_dead = player_dead(player2)

            if p1_dead or p2_dead:
                round_over = True

                if p1_dead and p2_dead:
                    winner_text = "Draw!"
                elif p2_dead:
                    winner_text = "Player 1 Wins!"
                    if best_of == 5:
                        scores["P1"] += 1
                else:
                    winner_text = "AI Wins!" if vs_ai else "Player 2 Wins!"
                    if best_of == 5:
                        scores["P2"] += 1

        # Draw
        screen.fill(BLACK)
        draw_grid(screen)
        player1.draw(screen)
        player2.draw(screen)

        # Score (ONLY for best-of-5)
        if best_of == 5:
            right_name = "AI" if vs_ai else "P2"
            hud = hud_font.render(
                f"BEST OF 5  |  {scores['P1']} - {scores['P2']} {right_name}",
                True,
                WHITE
            )
            screen.blit(hud, (10, 10))

        # Round/match overlay
        if round_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            screen.blit(overlay, (0, 0))

            match_over = (best_of == 5) and (scores["P1"] >= rounds_to_win or scores["P2"] >= rounds_to_win)
            if match_over:
                if scores["P1"] > scores["P2"]:
                    final = "PLAYER 1 WINS THE MATCH!"
                else:
                    final = "AI WINS THE MATCH!" if vs_ai else "PLAYER 2 WINS THE MATCH!"

                txt1 = big_font.render("MATCH OVER", True, WHITE)
                txt2 = big_font.render(final, True, YELLOW)
                screen.blit(txt1, txt1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
                screen.blit(txt2, txt2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))
                txt3 = hud_font.render("Press R to play again | ESC to quit", True, WHITE)
                screen.blit(txt3, txt3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))
            else:
                txt1 = big_font.render("ROUND OVER", True, WHITE)
                txt2 = big_font.render(winner_text, True, YELLOW)
                screen.blit(txt1, txt1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
                screen.blit(txt2, txt2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))
                txt3 = hud_font.render("Press R for next round | ESC to quit", True, WHITE)
                screen.blit(txt3, txt3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))

        pygame.display.flip()

if __name__ == "__main__":
    main()
