import pygame
import random
import math
import os
import time

# Game config
WIDTH, HEIGHT = 900, 700  # window size is now bigger
MAP_WIDTH, MAP_HEIGHT = 3200, 2400
FPS = 60
SNAKE_RADIUS = 8
FOOD_RADIUS = 4
SNAKE_SPEED = 2
BOT_COUNT = 18
BOOST_MULTIPLIER = 2
BOOST_COST = 0.2
BOT_RESPAWN_DELAY = 5.0
FOOD_COUNT = 200

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
DARK_BG = (20, 20, 30)

BOT_COLORS = [
    (0,255,0), (255,0,0), (0,192,255), (255,128,0), (255,0,255),
    (255,255,0), (128,0,255), (0,255,255), (255,80,80), (130,255,67),
    (240,164,96), (200,120,40), (255,0,120), (80,189,255), (0,176,96),
    (220,200,0), (0,100,255), (0,225,205)
]
SNAKE_FACES = ["😀", "😈", "😁", "😎", "🤪", "🥶", "🥳", "😏", "😭", "😬", "🐍", "👽", "🥸", "😅"]

def get_unique_bot_color(idx):
    if idx < len(BOT_COLORS):
        return BOT_COLORS[idx]
    r = lambda: random.randint(100,255)
    return (r(), r(), r())

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Local Slither.io")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 24)
face_font = pygame.font.SysFont("Segoe UI Emoji, DejaVu Sans", 32, bold=True)

HIGH_SCORE_FILE = "highscore.txt"

def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        with open(HIGH_SCORE_FILE, "r") as f:
            return int(f.read())
    return 0

def save_high_score(score):
    with open(HIGH_SCORE_FILE, "w") as f:
        f.write(str(score))

def make_glow_surface(color, radius=16):
    surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    center = radius
    for r in range(radius, 0, -1):
        alpha = int(255 * (r / radius)**2 * 0.24)
        pygame.draw.circle(surf, (*color, alpha), (center, center), r)
    pygame.draw.circle(surf, color, (center, center), FOOD_RADIUS)
    return surf

def create_gradient_bg(width, height):
    bg = pygame.Surface((width, height))
    center = (width // 2, height // 2)
    max_radius = int(math.hypot(center[0], center[1]))
    for r in range(max_radius, 0, -2):
        v = r / max_radius
        lum = int(18 + 24 * ((1 - v) ** 1.7))
        color = (lum, lum, int(lum * 1.15))
        pygame.draw.circle(bg, color, center, r)
    vignette = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        for x in range(width):
            dx = (x - center[0]) / width
            dy = (y - center[1]) / height
            dist = dx * dx + dy * dy
            alpha = int(120 * min(1, dist*2))
            vignette.set_at((x, y), (0,0,0, alpha))
    bg.blit(vignette, (0, 0))
    return bg

class Food:
    surface_cache = {}
    def __init__(self, pos=None, color=(255,180,180)):
        self.pos = list(pos) if pos else [random.randint(0, MAP_WIDTH), random.randint(0, MAP_HEIGHT)]
        self.color = color
        key = color[:3]
        if key not in Food.surface_cache:
            Food.surface_cache[key] = make_glow_surface(color)
        self.glow_surf = Food.surface_cache[key]
    def draw(self, offset):
        base_pos = self.pos
        for dx in (-MAP_WIDTH, 0, MAP_WIDTH):
            for dy in (-MAP_HEIGHT, 0, MAP_HEIGHT):
                draw_x = base_pos[0] + dx
                draw_y = base_pos[1] + dy
                camx, camy = offset
                screenx = int(draw_x - camx)
                screeny = int(draw_y - camy)
                if -40 < screenx < WIDTH+40 and -40 < screeny < HEIGHT+40:
                    rect = self.glow_surf.get_rect(center=(screenx, screeny))
                    screen.blit(self.glow_surf, rect)

def collect_food_along_path(snake, path_end, food_items):
    if not snake.alive:
        return
    head = snake.body[0]
    for food in food_items[:]:
        fx, fy = food.pos
        x0, y0 = head
        x1, y1 = path_end
        dx, dy = x1 - x0, y1 - y0
        if dx == 0 and dy == 0:
            dist = math.hypot(fx - x0, fy - y0)
        else:
            t = ((fx - x0) * dx + (fy - y0) * dy) / (dx * dx + dy * dy)
            t = max(0.0, min(1.0, t))
            closest_x = x0 + t * dx
            closest_y = y0 + t * dy
            dist = math.hypot(fx - closest_x, fy - closest_y)
        if dist < SNAKE_RADIUS + FOOD_RADIUS:
            snake.grow()
            food_items.remove(food)

class Snake:
    bot_counter = 0
    bot_colors_used = {}

    def __init__(self, color, x, y, name="Bot", face=None):
        self.color = color
        self.body = [[x, y]]
        self.direction = [random.choice([-1, 1]), random.choice([-1, 1])]
        self.length = 10
        self.alive = True
        self.name = name
        self.face = face if face is not None else random.choice(SNAKE_FACES)
        self.respawn_time = 0
        self.last_turn = 0
        self.ai_target_type = None
        self.ai_target_timer = 0
        self.ai_last_target = None

    @classmethod
    def create_bot(cls):
        idx = cls.bot_counter
        cls.bot_counter += 1
        clr = get_unique_bot_color(idx)
        face = random.choice(SNAKE_FACES)
        name = f"Bot{cls.bot_counter}"
        safe = False
        while not safe:
            x = random.randint(100, MAP_WIDTH - 100)
            y = random.randint(100, MAP_HEIGHT - 100)
            if (MAP_WIDTH//2-250 > x or x > MAP_WIDTH//2+250) or (MAP_HEIGHT//2-250 > y or y > MAP_HEIGHT//2+250):
                safe = True
        return Snake(clr, x, y, name=name, face=face)

    def respawn(self):
        x, y = 0, 0
        safe = False
        while not safe:
            x = random.randint(100, MAP_WIDTH - 100)
            y = random.randint(100, MAP_HEIGHT - 100)
            if (MAP_WIDTH//2-250 > x or x > MAP_WIDTH//2+250) or (MAP_HEIGHT//2-250 > y or y > MAP_HEIGHT//2+250):
                safe = True
        self.body = [[x, y]]
        self.length = 10
        self.alive = True
        self.direction = [random.choice([-1,1]), random.choice([-1,1])]
        self.respawn_time = 0
        self.ai_last_target = None
        self.ai_target_timer = 0

    def update(self, target=None, boosting=False, food_items=None, avoid=None):
        if not self.alive:
            return
        if hasattr(self, "is_bot") and self.last_turn != 0 and random.random() < 0.1:
            angle = math.atan2(self.direction[1], self.direction[0])
            angle += random.uniform(-0.15, 0.15)
            self.direction = [math.cos(angle), math.sin(angle)]
        head = self.body[0][:]
        speed = SNAKE_SPEED * BOOST_MULTIPLIER if boosting else SNAKE_SPEED
        if avoid:
            avoid_angle = math.atan2(head[1]-avoid[1], head[0]-avoid[0])
            main_angle = math.atan2(self.direction[1], self.direction[0])
            angle = (main_angle*0.85 + avoid_angle*0.15)
            self.direction = [math.cos(angle), math.sin(angle)]
        if target:
            angle = math.atan2(target[1] - head[1], target[0] - head[0])
            if hasattr(self, "is_bot"):
                main_angle = math.atan2(self.direction[1], self.direction[0])
                angle = main_angle * 0.8 + angle * 0.2
            self.direction = [math.cos(angle), math.sin(angle)]
        new_head = [
            (head[0] + self.direction[0] * speed) % MAP_WIDTH,
            (head[1] + self.direction[1] * speed) % MAP_HEIGHT
        ]
        if food_items is not None:
            collect_food_along_path(self, new_head, food_items)
        self.body.insert(0, new_head)
        if len(self.body) > self.length:
            self.body.pop()
        if boosting and self.length > 10:
            self.length -= BOOST_COST

    def grow(self):
        self.length += 5
    def score(self):
        return int(self.length - 10)
    def check_collision(self, snakes, food_items):
        if not self.alive:
            return
        head = self.body[0]
        for snake in snakes:
            if snake is self or not snake.alive:
                continue
            for segment in snake.body[1:]:
                if math.hypot(head[0] - segment[0], head[1] - segment[1]) < SNAKE_RADIUS * 2:
                    for seg in self.body:
                        food_items.append(Food(pos=seg, color=self.color))
                    self.alive = False
                    self.died_at = time.time()
                    return

    def draw(self, offset):
        if not self.alive:
            return
        head_drawn = False
        for segi, seg in enumerate(self.body):
            for dx in (-MAP_WIDTH, 0, MAP_WIDTH):
                for dy in (-MAP_HEIGHT, 0, MAP_HEIGHT):
                    segx = seg[0] + dx
                    segy = seg[1] + dy
                    camx, camy = offset
                    screenx = int(segx - camx)
                    screeny = int(segy - camy)
                    if -20 < screenx < WIDTH+20 and -20 < screeny < HEIGHT+20:
                        color = (
                            min(255, self.color[0] + segi * 2),
                            min(255, self.color[1] + segi * 2),
                            min(255, self.color[2] + segi * 2),
                        )
                        pygame.draw.circle(screen, color, (screenx, screeny), SNAKE_RADIUS)
                        # Draw the face at the head (segi == 0) only once per segment
                        if not head_drawn and segi == 0:
                            face_surf = face_font.render(self.face, True, (255,255,255))
                            f_rect = face_surf.get_rect(center=(screenx, screeny))
                            screen.blit(face_surf, f_rect)
                            head_drawn = True

def show_game_over():
    text = font.render("Game Over! Press R to Restart", True, YELLOW)
    rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, rect)
    pygame.display.flip()

def draw_score(player, high_score):
    score_text = small_font.render(f"Score: {player.score()}  High: {high_score}", True, WHITE)
    screen.blit(score_text, (10, 10))

def draw_minimap(player, bots):
    minimap_size = 120
    minimap = pygame.Surface((minimap_size, minimap_size))
    minimap.fill((30, 30, 30))
    scale_x = minimap_size / MAP_WIDTH
    scale_y = minimap_size / MAP_HEIGHT
    for bot in bots:
        if bot.alive:
            x, y = bot.body[0]
            pygame.draw.circle(minimap, bot.color, (int(x * scale_x), int(y * scale_y)), 2)
            label = small_font.render(str(bot.name), True, bot.color)
            minimap.blit(label, (int(x * scale_x) + 4, int(y * scale_y)))
    if player.alive:
        x, y = player.body[0]
        pygame.draw.circle(minimap, BLUE, (int(x * scale_x), int(y * scale_y)), 3)
        label = small_font.render("You", True, BLUE)
        minimap.blit(label, (int(x * scale_x) + 4, int(y * scale_y)))
    screen.blit(minimap, (WIDTH - minimap_size - 10, 10))

def bot_avoid_target(bot, threats):
    closest = None
    threat_dist = 70 + bot.length
    min_dist = 999999
    for other in threats:
        if not other.alive:
            continue
        hx, hy = bot.body[0]
        ox, oy = other.body[0]
        dist = math.hypot(hx - ox, hy - oy)
        # Avoid if the other snake is significantly bigger or closer
        if (other.length > bot.length+4 and dist < threat_dist):
            if dist < min_dist:
                closest = other.body[0]
                min_dist = dist
    return closest

def bot_ai_decision(bot, bots, player, food_items, framecount):
    # Avoid big snakes that are too close
    threats = [sn for sn in [player]+bots if sn is not bot and sn.alive and sn.length > bot.length+4]
    avoid = bot_avoid_target(bot, threats)

    # Target nearby eatable snake if I'm big enough, else food
    prey_candidates = [sn for sn in [player]+bots
                       if sn is not bot and sn.alive and sn.length <= bot.length+8]
    prey = None
    prey_dist = 99999999
    for other in prey_candidates:
        hx, hy = bot.body[0]
        ox, oy = other.body[0]
        d = math.hypot(hx - ox, hy - oy)
        if d < 180 and d < prey_dist:
            prey, prey_dist = other, d
    if prey and bot.length > 15:
        target = prey.body[0]
        boosting = True
    else:
        # Find nearest visible food
        if food_items:
            head = bot.body[0]
            nearest_food = min(food_items, key=lambda f: math.hypot(f.pos[0]-head[0], f.pos[1]-head[1]))
            target = nearest_food.pos
            boosting = (bot.length > 20) and random.random() < 0.10
        else:
            target = None
            boosting = False

    # Occasionally, stick to a previous target for a few frames for realism
    if hasattr(bot, "ai_last_target") and bot.ai_last_target and bot.ai_target_timer > 0:
        target = bot.ai_last_target
        bot.ai_target_timer -= 1
    else:
        bot.ai_last_target = target
        bot.ai_target_timer = random.randint(8,20)
    return target, avoid, boosting

def main():
    def reset_game():
        Snake.bot_counter = 0
        player = Snake(BLUE, MAP_WIDTH // 2, MAP_HEIGHT // 2, name="You", face=random.choice(SNAKE_FACES))
        player.is_bot = False
        bots = []
        for _ in range(BOT_COUNT):
            bot = Snake.create_bot()
            bot.is_bot = True
            bots.append(bot)
        food_items = [Food() for _ in range(FOOD_COUNT)]
        return player, bots, food_items

    BG_CANVAS_SIZE = max(WIDTH, HEIGHT)*2
    bg_surface = create_gradient_bg(BG_CANVAS_SIZE, BG_CANVAS_SIZE)

    high_score = load_high_score()
    player, bots, food_items = reset_game()
    last_bot_respawn = time.time()
    running = True
    paused = False
    game_over = False
    framecount = 0

    while running:
        clock.tick(FPS)
        pygame.display.set_caption(f"Local Slither.io - FPS: {clock.get_fps():.1f}")
        now = time.time()
        framecount += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                player, bots, food_items = reset_game()
                game_over = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                paused = not paused
        if paused:
            continue
        cam_offset = [player.body[0][0] - WIDTH // 2, player.body[0][1] - HEIGHT // 2]
        bx = int(cam_offset[0] % (BG_CANVAS_SIZE-WIDTH))
        by = int(cam_offset[1] % (BG_CANVAS_SIZE-HEIGHT))
        screen.blit(bg_surface, (-bx, -by))
        if not game_over:
            mx, my = pygame.mouse.get_pos()
            world_target = [player.body[0][0] - WIDTH // 2 + mx, player.body[0][1] - HEIGHT // 2 + my]
            boosting = pygame.mouse.get_pressed()[0]
            player.update(target=world_target, boosting=boosting, food_items=food_items)
            alive_bots = [b for b in bots if b.alive]
            dead_bots = [b for b in bots if not b.alive and getattr(b, "died_at", 0) > 0]
            bots_to_respawn = [b for b in dead_bots if now - b.died_at >= BOT_RESPAWN_DELAY]
            if bots_to_respawn:
                bots_to_respawn[0].respawn()
                bots_to_respawn[0].is_bot = True
                bots_to_respawn[0].died_at = 0
            bots[:] = [b for b in bots if b.alive or (hasattr(b, "died_at") and now - b.died_at < 15)]
            if len([b for b in bots if b.alive]) < BOT_COUNT and now - last_bot_respawn >= BOT_RESPAWN_DELAY:
                bot = Snake.create_bot()
                bot.is_bot = True
                bots.append(bot)
                last_bot_respawn = now
            for bot in bots:
                if not bot.alive:
                    continue
                target, avoid, boosting = bot_ai_decision(bot, bots, player, food_items, framecount)
                bot.update(target=target, food_items=food_items, avoid=avoid, boosting=boosting)
            all_snakes = [player] + bots
            for snake in all_snakes:
                snake.check_collision(all_snakes, food_items)
            if not player.alive:
                game_over = True
                if player.score() > high_score:
                    high_score = player.score()
                    save_high_score(high_score)
            while len(food_items) < FOOD_COUNT:
                food_items.append(Food())
        for food in food_items:
            food.draw(offset=cam_offset)
        player.draw(offset=cam_offset)
        for bot in bots:
            bot.draw(offset=cam_offset)
        if game_over:
            show_game_over()
        draw_score(player, high_score)
        draw_minimap(player, bots)
        pygame.display.flip()
    pygame.quit()

if __name__ == '__main__':
    main()
