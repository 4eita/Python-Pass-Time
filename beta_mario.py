import pygame
import random
import json
import os
import math
import time

# --- CONSTANTS ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
LEVEL_WIDTH = 1600
FPS = 60
GRAVITY = 0.7
JUMP_STRENGTH = -13
PLAYER_SPEED = 5

# --- THEME DATA ---
WORLD_THEMES = [
    {"name": "Grassland", "bg_color": (106, 200, 80), "hazard_color": (255, 0, 0), "hazard_type": "spikes"},
    {"name": "Forest",    "bg_color": (34, 98, 79), "hazard_color": (173,113,60), "hazard_type": "logs"},
    {"name": "Desert",    "bg_color": (255, 242, 190), "hazard_color": (240, 220, 82), "hazard_type": "quicksand"},
    {"name": "Snow",      "bg_color": (197,230,255), "hazard_color": (210,210,255), "hazard_type": "ice"},
    {"name": "Volcano",   "bg_color": (130, 52, 12), "hazard_color": (244,78,0), "hazard_type": "lava"},
    {"name": "Ocean",     "bg_color": (78, 194, 246), "hazard_color": (0, 123, 255), "hazard_type": "water"},
    {"name": "Mountain",  "bg_color": (110, 105, 99), "hazard_color": (86,66,49), "hazard_type": "rock"},
    {"name": "Night",     "bg_color": (15, 15, 48), "hazard_color": (245,245,245), "hazard_type": "ghost"},
    {"name": "Sky",       "bg_color": (173, 216, 230), "hazard_color": (255,255,160), "hazard_type": "zap"},
]
WORLD_LIST = [w["name"].lower() for w in WORLD_THEMES]
LEVEL_LIST = [f"{w}_1" for w in WORLD_LIST]
CHECKPOINT_FILE = "checkpoint_save.json"

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mario Worlds - Enriched")
clock = pygame.time.Clock()

# --- SPRITE GROUPS ---
platforms = pygame.sprite.Group()
enemies = pygame.sprite.Group()
powerups = pygame.sprite.Group()
fireballs = pygame.sprite.Group()
hazards = pygame.sprite.Group()
checkpoints = pygame.sprite.Group()
coins = pygame.sprite.Group()
blocks = pygame.sprite.Group()
pipes = pygame.sprite.Group()
bushes = pygame.sprite.Group()
clouds = pygame.sprite.Group()
moving_platforms = pygame.sprite.Group()
goal = None

# --- Powerup States ---
POWER_NONE = "none"
POWER_MUSHROOM = "mushroom"
POWER_FLOWER = "flower"
POWER_STAR = "star"

# --- SPRITES ---

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.color = (255, 100, 100)
        self.width = 34
        self.height = 60
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill(self.color)
        self.rect = self.image.get_rect(midbottom=(100, SCREEN_HEIGHT - 100))
        self.vel_y = 0
        self.on_ground = True
        self.state = 'idle'
        self.facing_right = True
        self.step = 0
        self.score = 0
        # Powerup properties:
        self.power = POWER_NONE
        self.flower = False            # Fire flower
        self.has_mushroom = False      # Big Mario/Growth
        self.star_active = False       # Invincible
        self.star_end_time = 0

    def input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False
        if keys[pygame.K_f] and self.flower:
            if not hasattr(self, "last_shot") or time.time() - self.last_shot > 0.25:
                direction = 1 if self.facing_right else -1
                fireball = Fireball(self.rect.centerx, self.rect.centery, direction)
                fireballs.add(fireball)
                self.last_shot = time.time()

    def apply_gravity(self):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        self.on_ground = False

        for platform in platforms:
            if self.rect.colliderect(platform.rect) and self.vel_y >= 0:
                if self.rect.bottom <= platform.rect.bottom:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True

        for mplat in moving_platforms:
            if self.rect.colliderect(mplat.rect) and self.vel_y >= 0:
                if self.rect.bottom <= mplat.rect.bottom:
                    self.rect.bottom = mplat.rect.top
                    self.vel_y = 0
                    self.on_ground = True

        for pipe in pipes:
            if self.rect.colliderect(pipe.rect) and self.vel_y >= 0:
                if self.rect.bottom <= pipe.rect.bottom:
                    self.rect.bottom = pipe.rect.top
                    self.vel_y = 0
                    self.on_ground = True

    def animate(self):
        self.image.fill((0, 0, 0, 0))
        if self.star_active:
            color = (255,255,0)
        elif self.flower:
            color = (255,120,0)
        elif self.has_mushroom:
            color = (255,255,255)
        else:
            color = self.color
        if not self.on_ground:
            pygame.draw.ellipse(self.image, color, [0, 0, self.width, self.height])
        elif self.state == 'run':
            offset = 5 if (self.step // 5) % 2 == 0 else -5
            pygame.draw.rect(self.image, color, [0, offset, self.width, self.height])
            self.step += 1
        else:
            pygame.draw.rect(self.image, color, [0, 0, self.width, self.height])

    def move(self):
        keys = pygame.key.get_pressed()
        self.state = 'idle'
        orig_pos = self.rect.x
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED
            self.state = 'run'
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED
            self.state = 'run'
        if self.rect.x < orig_pos:
            self.facing_right = False
        if self.rect.x > orig_pos:
            self.facing_right = True

    def check_enemy_collision(self):
        for enemy in list(enemies):
            if self.rect.colliderect(enemy.rect):
                if self.rect.bottom <= enemy.rect.top + 10 and self.vel_y > 0:
                    enemies.remove(enemy)
                    self.vel_y = JUMP_STRENGTH / 2
                elif self.star_active:
                    enemies.remove(enemy)
                elif self.has_mushroom:  # big mario loses mushroom but survives
                    self.has_mushroom = False
                    self.flower = False
                    self.power = POWER_NONE
                else:
                    pygame.quit()
                    exit()

    def check_powerup_collision(self):
        for powerup in list(powerups):
            if self.rect.colliderect(powerup.rect):
                if powerup.power_type == POWER_MUSHROOM:
                    self.has_mushroom = True
                    self.flower = False
                elif powerup.power_type == POWER_FLOWER:
                    self.flower = True
                    self.has_mushroom = True
                elif powerup.power_type == POWER_STAR:
                    self.star_active = True
                    self.star_end_time = time.time() + powerup.duration
                powerups.remove(powerup)

    def check_hazard_collision(self):
        for hazard in hazards:
            if self.rect.colliderect(hazard.rect):
                if not self.star_active and not self.flower and not self.has_mushroom:
                    pygame.quit()
                    exit()
                elif self.star_active:
                    pass
                elif self.flower:
                    self.flower = False
                elif self.has_mushroom:
                    self.has_mushroom = False

    def check_checkpoint_collision(self, current_level_name):
        for checkpoint in checkpoints:
            if self.rect.colliderect(checkpoint.rect):
                save_checkpoint(current_level_name, self.rect.midbottom, self.flower or self.has_mushroom)

    def collect_coins_and_blocks(self):
        for coin in list(coins):
            if self.rect.colliderect(coin.rect):
                coins.remove(coin)
                self.score += 1

        for block in blocks:
            if not block.popped and self.rect.colliderect(block.rect) and self.vel_y < 0 and abs(self.rect.top - block.rect.bottom) < 20:
                block.popped = True
                # Randomize powerup/coin if marked
                if block.contains == "coin":
                    coins.add(Coin(block.rect.centerx, block.rect.top - 18))
                elif block.contains == "mushroom":
                    powerups.add(PowerUp(block.rect.centerx, block.rect.top - 20, POWER_MUSHROOM))
                elif block.contains == "flower":
                    powerups.add(PowerUp(block.rect.centerx, block.rect.top - 20, POWER_FLOWER))
                elif block.contains == "star":
                    powerups.add(PowerUp(block.rect.centerx, block.rect.top - 20, POWER_STAR))
                elif block.contains == "?" and True:
                    ptype = random.choice([POWER_MUSHROOM, POWER_FLOWER, POWER_STAR])
                    powerups.add(PowerUp(block.rect.centerx, block.rect.top - 20, ptype))

    def handle_star_timer(self):
        if self.star_active and time.time() > self.star_end_time:
            self.star_active = False

    def falling_in_pit(self):
        if self.rect.top > SCREEN_HEIGHT + 100:
            pygame.quit()
            exit()

    def update(self, level_manager):
        self.input()
        self.apply_gravity()
        self.move()
        self.animate()
        self.check_enemy_collision()
        self.check_powerup_collision()
        self.check_hazard_collision()
        self.collect_coins_and_blocks()
        self.handle_star_timer()
        self.check_checkpoint_collision(level_manager.current_level)
        self.falling_in_pit()

class Goomba(pygame.sprite.Sprite):
    def __init__(self, x, y, platform_list):
        super().__init__()
        self.size = 34
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (160,80,50), [0,3,self.size,self.size-3])
        pygame.draw.ellipse(self.image, (0,0,0), [8,22,8,9])
        pygame.draw.ellipse(self.image, (0,0,0), [20,22,8,9])
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.direction = -1
        self.home_platforms = platform_list
        matching_tops = [pf.rect.left for pf in self.home_platforms if abs(y - pf.rect.top) < 3]
        if any(matching_tops):
            self.platform_left = min([pf.rect.left for pf in self.home_platforms if abs(y - pf.rect.top) < 3])
            self.platform_right = max([pf.rect.right for pf in self.home_platforms if abs(y - pf.rect.top) < 3])
        else:
            self.platform_left = 0
            self.platform_right = LEVEL_WIDTH

    def update(self):
        self.rect.x += self.direction * 2
        if self.rect.left < self.platform_left or self.rect.right > self.platform_right:
            self.direction *= -1
            if self.rect.left < self.platform_left:
                self.rect.left = self.platform_left
            else:
                self.rect.right = self.platform_right

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((139, 69, 19))
        self.rect = self.image.get_rect(topleft=(x, y))

class MovingPlatform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, dx, dy, dist):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((120, 139, 69))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_pos = pygame.Vector2(x, y)
        self.dx = dx
        self.dy = dy
        self.dist = dist
        self.time_offset = random.randint(0, 100)

    def update(self):
        t = pygame.time.get_ticks() / 1000. + self.time_offset
        self.rect.x = int(self.start_pos.x + self.dist * self.dx * (0.5 + 0.5 * math.sin(t)))
        self.rect.y = int(self.start_pos.y + self.dist * self.dy * (0.5 + 0.5 * math.sin(t)))

class Goal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 80))
        self.image.fill((255, 215, 0))
        self.rect = self.image.get_rect(bottomleft=(x, y))

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, ptype=POWER_MUSHROOM):
        super().__init__()
        self.power_type = ptype
        self.duration = 6 if self.power_type == POWER_STAR else 0
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        if self.power_type == POWER_MUSHROOM:
            pygame.draw.rect(self.image, (255,0,0), (0,0,20,10))
            pygame.draw.rect(self.image, (255,255,255), (0,10,20,10))
        elif self.power_type == POWER_FLOWER:
            self.image.fill((245, 160, 55))
            pygame.draw.circle(self.image, (255,255,255), (10,10), 8)
            pygame.draw.circle(self.image, (255,140,0), (10,10), 7, 3)
            pygame.draw.circle(self.image, (0,180,0), (10,14), 4,2)
        elif self.power_type == POWER_STAR:
            pygame.draw.polygon(self.image, (255,255,0), [(10,0),(13,7),(20,7),(15,12),(17,20),(10,16),(3,20),(5,12),(0,7),(7,7)])          
        else:
            self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect(center=(x, y))

class Fireball(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((12,12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255,80,30), (6,6), 6)
        pygame.draw.circle(self.image, (255,160,60), (6,6), 4)
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.vx = 7 * direction
        self.vy = -4

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.vy += GRAVITY*0.25
        # Platform bounce
        for g in platforms:
            if self.rect.colliderect(g.rect) and self.vy > 0:
                self.vy = -4  # bounce up
        # Remove out of bounds
        if self.rect.left > LEVEL_WIDTH or self.rect.right < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()
        # Hit enemy
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                enemies.remove(enemy)
                self.kill()

class Hazard(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

class Checkpoint(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 60))
        self.image.fill((0, 200, 255))
        self.rect = self.image.get_rect(midbottom=(x, y))

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 223, 0), (8,8), 8)
        pygame.draw.circle(self.image, (180,140,0), (8,8), 8, 2)
        self.rect = self.image.get_rect(center=(x, y))

class QuestionBlock(pygame.sprite.Sprite):
    def __init__(self, x, y, contains="coin"):
        super().__init__()
        self.image = pygame.Surface((32,32), pygame.SRCALPHA)
        self.contains = contains
        self.popped = False
        self.render_block()
        self.rect = self.image.get_rect(topleft=(x,y))

    def render_block(self):
        self.image.fill((0,0,0,0))
        col = (220,180,80) if not self.popped else (170,130,70)
        pygame.draw.rect(self.image, col, (0,0,32,32))
        pygame.draw.rect(self.image, (160,120,40), (0,0,32,32), 2)
        if not self.popped:
            font = pygame.font.SysFont(None, 28)
            q = font.render("?", True, (190,120,40))
            self.image.blit(q, (8, 0))
        else:
            pygame.draw.rect(self.image, (180,120,70), (7,7,18,18))

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, height=70):
        super().__init__()
        width = 48
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill((32,192,64))
        pygame.draw.rect(self.image, (20, 130, 44), (0, 0, width, 15))
        pygame.draw.rect(self.image, (70,230,80), (0,2, width, 8))
        self.rect = self.image.get_rect(bottomleft=(x, y))

class Bush(pygame.sprite.Sprite):
    def __init__(self, x, y, w=50):
        super().__init__()
        self.image = pygame.Surface((w, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (34,139,34), (0, 0, w, 24))
        self.rect = self.image.get_rect(bottomleft=(x, y))

class Cloud(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        w, h = 60, 20
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (255,255,255), (0,0,w,h))
        pygame.draw.ellipse(self.image, (255,255,255), (15, -6, 50, 25))
        self.rect = self.image.get_rect(center=(x, y))

# --- LEVEL DATA ---
WORLD_DATA = {}
# Grassland has all powerups in demo!
WORLD_DATA["grassland_1"] = {
    "platforms": [
        (0, SCREEN_HEIGHT - 50, 600, 50), (800, SCREEN_HEIGHT - 50, 800, 50),
        (300, 470, 220, 20), (700, 400, 200, 16)
    ],
    "enemies": [(380, 470), (830, 399)],
    "coins": [(330,440), (360,440), (390,440), (420,440), (450,440)],
    "blocks": [(750, 370, "coin"), (360, 440, "mushroom"), (450, 370, "flower"), (800, 370, "star")],
    "pipes": [(620, SCREEN_HEIGHT-50, 90)],
    "bushes": [(440, SCREEN_HEIGHT-50, 70)],
    "clouds": [(100,140),(900,90)],
    "hazards": [
        (1100, SCREEN_HEIGHT-50, 80, 20),
    ],
    "goal_y": SCREEN_HEIGHT-50
}
WORLD_DATA["forest_1"] = {
    "platforms": [(0, SCREEN_HEIGHT-70, 500, 70), (550, SCREEN_HEIGHT-70, 600, 70),(370, 400, 120, 16)],
    "enemies": [(140, SCREEN_HEIGHT-70), (610, 399)],
    "coins": [(400,380),(620,380),(800,540)],
    "blocks": [(390,370,"powerup")],
    "pipes": [(950, SCREEN_HEIGHT-70, 100)],
    "hazards": [(500, SCREEN_HEIGHT-70, 50, 14)],
    "bushes": [(50, SCREEN_HEIGHT-70, 60)],
    "clouds": [(210,110),(950,90)],
    "goal_y": SCREEN_HEIGHT-70
}
WORLD_DATA["desert_1"] = {
    "platforms": [(0, SCREEN_HEIGHT-50, 400, 50), (420, SCREEN_HEIGHT-80, 200, 30),(700, SCREEN_HEIGHT-50, 900, 50)],
    "enemies": [(470, SCREEN_HEIGHT-80)],
    "coins": [(480, SCREEN_HEIGHT-120),(520, SCREEN_HEIGHT-120)],
    "blocks": [(720,20+SCREEN_HEIGHT-50,"coin")],
    "pipes": [(1150, SCREEN_HEIGHT-50, 70)],
    "hazards": [(401, SCREEN_HEIGHT-40, 19, 30),(1320, SCREEN_HEIGHT-50, 70, 16)],
    "goal_y": SCREEN_HEIGHT-50
}
WORLD_DATA["snow_1"] = {
    "platforms": [(0, SCREEN_HEIGHT-60, 500, 60), (550, SCREEN_HEIGHT-100, 200, 30),(800, SCREEN_HEIGHT-60, 600, 60)],
    "enemies": [(700, SCREEN_HEIGHT-60)],
    "coins": [(510, SCREEN_HEIGHT-140), (720, 20+SCREEN_HEIGHT-100)],
    "blocks": [(650, SCREEN_HEIGHT-130, "coin")],
    "pipes": [],
    "hazards": [(900, SCREEN_HEIGHT-60, 60, 16)],
    "clouds": [(600,50),(1200,80)],
    "goal_y": SCREEN_HEIGHT-60
}
WORLD_DATA["volcano_1"] = {
    "platforms": [(0, SCREEN_HEIGHT-40, 500, 40), (540, SCREEN_HEIGHT-90, 200, 20),
        (800, SCREEN_HEIGHT-40, 700, 40)],
    "enemies": [(700, SCREEN_HEIGHT-90)],
    "coins": [(600, SCREEN_HEIGHT-110),(630, SCREEN_HEIGHT-110)],
    "blocks": [(900,SCREEN_HEIGHT-70,"powerup")],
    "pipes": [(1150, SCREEN_HEIGHT-40, 100)],
    "hazards": [(470, SCREEN_HEIGHT-40, 40, 40),(950, SCREEN_HEIGHT-40, 90, 30)],
    "clouds": [(740,110)],
    "goal_y": SCREEN_HEIGHT-40
}
WORLD_DATA["ocean_1"] = {
    "platforms": [(0, SCREEN_HEIGHT-50, 350, 50), (380, SCREEN_HEIGHT-110, 120, 12),(520, SCREEN_HEIGHT-160, 120, 12), (700, SCREEN_HEIGHT-50, 700, 50)],
    "enemies": [(400, SCREEN_HEIGHT-110)],
    "coins": [(550, SCREEN_HEIGHT-190), (560, SCREEN_HEIGHT-190)],
    "pipes": [(900, SCREEN_HEIGHT-50, 90)],
    "hazards": [(351, SCREEN_HEIGHT-45, 349, 45)],
    "clouds": [(540,40)],
    "goal_y": SCREEN_HEIGHT-50
}
WORLD_DATA["mountain_1"] = {
    "platforms": [(0, SCREEN_HEIGHT-70, 320, 70), (350, SCREEN_HEIGHT-200, 160, 18),(530, SCREEN_HEIGHT-320, 200, 18), (800, SCREEN_HEIGHT-70, 700, 70)],
    "enemies": [(400, SCREEN_HEIGHT-200), (600, SCREEN_HEIGHT-320)],
    "coins": [(520, SCREEN_HEIGHT-300), (570, SCREEN_HEIGHT-290)],
    "pipes": [],
    "hazards": [(680, SCREEN_HEIGHT-70, 40, 70), (900, SCREEN_HEIGHT-70, 80, 10)],
    "bushes": [],
    "clouds": [],
    "goal_y": SCREEN_HEIGHT-70
}
WORLD_DATA["night_1"] = {
    "platforms": [(0, SCREEN_HEIGHT-80, 500, 80), (600, SCREEN_HEIGHT-80, 500, 80),(350, 400, 100, 10)],
    "enemies": [(150, SCREEN_HEIGHT-80), (800, SCREEN_HEIGHT-80)],
    "coins": [(375, 380), (415,380), (650,530)],
    "pipes": [(950, SCREEN_HEIGHT-80, 100)],
    "hazards": [(820, SCREEN_HEIGHT-80, 60, 20)],
    "clouds": [],
    "goal_y": SCREEN_HEIGHT-80
}
WORLD_DATA["sky_1"] = {
    "platforms": [(0, SCREEN_HEIGHT-120, 350, 20), (370, SCREEN_HEIGHT-150, 150, 15),
        (600, SCREEN_HEIGHT-180, 140, 15), (800, SCREEN_HEIGHT-220, 700, 15)],
    "enemies": [(380, SCREEN_HEIGHT-150), (680, SCREEN_HEIGHT-180)],
    "coins": [(370, SCREEN_HEIGHT-170), (410, SCREEN_HEIGHT-200), (600, SCREEN_HEIGHT-200)],
    "blocks": [(480, SCREEN_HEIGHT-170, "powerup")],
    "clouds": [(400,80),(1050,60),(1250,100)],
    "pipes": [],
    "hazards": [(350, SCREEN_HEIGHT-121, 50, 9)],
    "goal_y": SCREEN_HEIGHT-120
}

def save_checkpoint(level, pos, powered):
    checkpoint_data = {
        "level": level,
        "player_pos": list(pos),
        "player_powered": powered
    }
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint_data, f)

def load_checkpoint():
    try:
        with open(CHECKPOINT_FILE, "r") as f:
            cp = json.load(f)
            return cp['level'], tuple(cp['player_pos']), cp['player_powered']
    except Exception:
        return None

def clear_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

class LevelManager:
    def __init__(self, player):
        self.player = player
        self.completed_levels = []
        self.current_level = LEVEL_LIST[0]

    def load_level(self, level_name, player_restore_pos=None, powered=False):
        global platforms, enemies, powerups, fireballs, hazards, checkpoints
        global coins, blocks, pipes, bushes, clouds, moving_platforms, goal
        platforms.empty(); enemies.empty(); powerups.empty(); fireballs.empty()
        hazards.empty(); checkpoints.empty(); coins.empty(); blocks.empty()
        pipes.empty(); bushes.empty(); clouds.empty(); moving_platforms.empty()
        if level_name not in WORLD_DATA:
            print(f"Level '{level_name}' not found.")
            return
        lvl = WORLD_DATA[level_name]
        wname = level_name.split('_')[0]
        widx  = WORLD_LIST.index(wname)
        hazard_color = WORLD_THEMES[widx]["hazard_color"]
        plat_objs = []
        for plat in lvl.get("platforms", []):
            pf = Platform(*plat)
            platforms.add(pf)
            plat_objs.append(pf)
        mplat_objs = []
        for mplat in lvl.get("moving_platforms", []):
            mpf = MovingPlatform(*mplat)
            moving_platforms.add(mpf)
            mplat_objs.append(mpf)
        for ex, ey in lvl.get("enemies", []):
            all_plats = plat_objs + mplat_objs
            home_plats = [pf for pf in all_plats if abs(pf.rect.top - ey) < 3]
            if not home_plats and all_plats:
                home_plats = [min(all_plats, key=lambda pf: abs(pf.rect.top - ey))]
            enemies.add(Goomba(ex, ey, home_plats))
        for px,py in lvl.get("powerups", []): powerups.add(PowerUp(px,py,POWER_MUSHROOM))
        for hx, hy, hw, hh in lvl.get("hazards", []):
            hazards.add(Hazard(hx, hy, hw, hh, hazard_color))
        for cx,cy in lvl.get("checkpoints", []): checkpoints.add(Checkpoint(cx,cy))
        for coinx, coiny in lvl.get("coins", []): coins.add(Coin(coinx, coiny))
        for bx, by, content in lvl.get("blocks", []): blocks.add(QuestionBlock(bx, by, content))
        for piped in lvl.get("pipes", []): pipes.add(Pipe(*piped))
        for bushd in lvl.get("bushes", []): bushes.add(Bush(*bushd))
        for cloudpos in lvl.get("clouds", []): clouds.add(Cloud(*cloudpos))
        if "goal_y" in lvl:
            goal_y = lvl["goal_y"]
        else:
            goal_y = SCREEN_HEIGHT-50
        globals()['goal'] = Goal(LEVEL_WIDTH - 56, goal_y)
        if player_restore_pos:
            self.player.rect.midbottom = player_restore_pos
        else:
            self.player.rect.midbottom = (70, goal_y-5)
        self.player.flower = powered  # fallback to flower if saved as True
        self.player.has_mushroom = (not powered and self.player.has_mushroom)
        self.current_level = level_name

    def goal_reached(self):
        if self.current_level not in self.completed_levels:
            self.completed_levels.append(self.current_level)
        overworld_select(self)

def overworld_select(level_manager):
    font = pygame.font.SysFont("Arial", 36)
    small_font = pygame.font.SysFont("Arial", 26)
    sel = 0
    while True:
        screen.fill((92,215,255))
        start_x = 60
        y = SCREEN_HEIGHT//2 + 35
        for idx, lvl in enumerate(LEVEL_LIST):
            lx = start_x + idx * 85
            wtheme = WORLD_THEMES[idx]['bg_color']
            pygame.draw.circle(screen, wtheme, (lx, y), 38)
            txt = font.render(str(idx+1), True, (40,40,40))
            wname = small_font.render(WORLD_THEMES[idx]['name'], True, (60,60,60))
            screen.blit(txt, (lx-12, y-22))
            screen.blit(wname, (lx-35, y+44))
            if lvl in level_manager.completed_levels:
                pygame.draw.circle(screen, (225,200,90), (lx, y), 44, 7)
            if idx == sel:
                pygame.draw.circle(screen, (255,245,200), (lx, y), 48, 5)
            if idx < len(LEVEL_LIST)-1:
                pygame.draw.line(screen, (50,43,30), (lx+38, y), (lx+47, y), 5)
        screen.blit(small_font.render("Left/Right to select, ENTER to play (F=Fire)", True, (30,30,30)), (60, y+100))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    sel = min(sel+1, len(LEVEL_LIST)-1)
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    sel = max(sel-1, 0)
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    level_manager.load_level(LEVEL_LIST[sel])
                    return

player = Player()
checkpoint_data = load_checkpoint()
level_manager = LevelManager(player)
if checkpoint_data:
    level, pos, powered = checkpoint_data
    if level not in WORLD_DATA:
        print(f"Checkpoint level {level} not found, starting from beginning!")
        clear_checkpoint()
        overworld_select(level_manager)
    else:
        level_manager.current_level = level
        level_manager.load_level(level, player_restore_pos=pos, powered=powered)
else:
    overworld_select(level_manager)
player_group = pygame.sprite.Group(player)

def check_goal_and_checkpoint(player, level_manager):
    if goal and player.rect.colliderect(goal.rect):
        level_manager.goal_reached()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player_group.update(level_manager)
    enemies.update()
    moving_platforms.update()
    fireballs.update()

    cur_worldname = level_manager.current_level.split('_')[0]
    theme_idx = WORLD_LIST.index(cur_worldname) if cur_worldname in WORLD_LIST else 0
    bg_color = WORLD_THEMES[theme_idx]['bg_color']

    camera_x = player.rect.centerx - SCREEN_WIDTH // 2
    camera_x = max(0, min(camera_x, LEVEL_WIDTH - SCREEN_WIDTH))

    screen.fill(bg_color)
    for cloud in clouds:
        screen.blit(cloud.image, (cloud.rect.x - int(camera_x * 0.8), cloud.rect.y))
    for bush in bushes:
        screen.blit(bush.image, (bush.rect.x - camera_x, bush.rect.y))
    for plat in platforms:
        screen.blit(plat.image, (plat.rect.x - camera_x, plat.rect.y))
    for mplat in moving_platforms:
        screen.blit(mplat.image, (mplat.rect.x - camera_x, mplat.rect.y))
    for pipe in pipes:
        screen.blit(pipe.image, (pipe.rect.x - camera_x, pipe.rect.y))
    for block in blocks:
        block.render_block()
        screen.blit(block.image, (block.rect.x - camera_x, block.rect.y))
    for coin in coins:
        screen.blit(coin.image, (coin.rect.x - camera_x, coin.rect.y))
    for enemy in enemies:
        screen.blit(enemy.image, (enemy.rect.x - camera_x, enemy.rect.y))
    for fireball in fireballs:
        screen.blit(fireball.image, (fireball.rect.x - camera_x, fireball.rect.y))
    for powerup in powerups:
        screen.blit(powerup.image, (powerup.rect.x - camera_x, powerup.rect.y))
    for hazard in hazards:
        screen.blit(hazard.image, (hazard.rect.x - camera_x, hazard.rect.y))
    for checkpoint in checkpoints:
        screen.blit(checkpoint.image, (checkpoint.rect.x - camera_x, checkpoint.rect.y))
    if goal is not None:
        screen.blit(goal.image, (goal.rect.x - camera_x, goal.rect.y))
    for entity in player_group:
        screen.blit(entity.image, (entity.rect.x - camera_x, entity.rect.y))
    font = pygame.font.SysFont(None, 32)
    score_img = font.render(f"Coins: {player.score}", True, (40,80,40))
    screen.blit(score_img, (25,15))

    check_goal_and_checkpoint(player, level_manager)

    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()
