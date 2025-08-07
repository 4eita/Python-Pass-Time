import pygame
import sys
import random
import math

pygame.init()
WIDTH, HEIGHT = 600, 650
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Isometric Stacking – Animated Floor Depth")
FPS = 60
clock = pygame.time.Clock()

TILE_SIZE = 80
BLOCK_HEIGHT = 40
SHADOW_OFFSET = 14

# For background depth
BG_TILE_SIZE = 56
FLOOR_DEPTH = 22      # Number of rows "rec" into the background

COLOR_LIST = [
    (255, 50, 80),   # Red
    (255, 175, 44),  # Orange
    (86, 214, 104),  # Green
    (54, 161, 255),  # Blue
    (180, 65, 255),  # Purple
    (255, 250, 80),  # Yellow
    (70, 245, 213),  # Aqua
]

BASE_COLOR = (190, 136, 54)
SHADOW_COLOR = (28, 28, 40, 120)
OUTLINE_COLOR = (26, 28, 50)
TEXT_COLOR = (255, 255, 255)
font = pygame.font.SysFont("Arial", 26, bold=True)

def iso_coords(x, y, z, camera_z=0):
    cx, cy = WIDTH // 2, HEIGHT // 2 + 100
    sy_cam = cy + int(camera_z)
    sx = cx + (x - y) * (TILE_SIZE // 2)
    sy = sy_cam + (x + y) * (TILE_SIZE // 4) - z * BLOCK_HEIGHT
    return (int(sx), int(sy))

def draw_hollow_iso_square(x, y, z, size, camera_z=0,
                           color_edge=(60,220,255), color_floor=(50, 60, 110), outline=True, shadow=True):
    x = int(round(x))
    y = int(round(y))
    size = int(round(size))
    # Outer top rim (big diamond)
    p0 = iso_coords(x, y, z, camera_z)
    p1 = iso_coords(x + size, y, z, camera_z)
    p2 = iso_coords(x + size, y + size, z, camera_z)
    p3 = iso_coords(x, y + size, z, camera_z)
    # Shadow
    if shadow:
        shadow_pts = [(px + SHADOW_OFFSET, py + SHADOW_OFFSET) for (px, py) in [p0, p1, p2, p3]]
        sh_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(sh_surface, SHADOW_COLOR, shadow_pts)
        SCREEN.blit(sh_surface, (0, 0))
    # Bottom rim (in Z)
    p0b = iso_coords(x, y, z-1, camera_z)
    p1b = iso_coords(x + size, y, z-1, camera_z)
    p2b = iso_coords(x + size, y + size, z-1, camera_z)
    p3b = iso_coords(x, y + size, z-1, camera_z)
    # Draw all outer edges (top+vertical sides)
    edge = color_edge
    pygame.draw.lines(SCREEN, edge, True, [p0, p1, p2, p3], 3)
    pygame.draw.line(SCREEN, edge, p0, p0b, 3)
    pygame.draw.line(SCREEN, edge, p1, p1b, 3)
    pygame.draw.line(SCREEN, edge, p2, p2b, 3)
    pygame.draw.line(SCREEN, edge, p3, p3b, 3)
    pygame.draw.lines(SCREEN, edge, True, [p0b, p1b, p2b, p3b], 2)
    # Draw inner floor ("rim", inset square/diamond)
    INSET = 0.18  # rim width as percentage of tile
    q0 = iso_coords(x + INSET*size, y + INSET*size, z, camera_z)
    q1 = iso_coords(x + size - INSET*size, y + INSET*size, z, camera_z)
    q2 = iso_coords(x + size - INSET*size, y + size - INSET*size, z, camera_z)
    q3 = iso_coords(x + INSET*size, y + size - INSET*size, z, camera_z)
    pygame.draw.polygon(SCREEN, color_floor, [q0, q1, q2, q3])
    pygame.draw.lines(SCREEN, edge, True, [q0, q1, q2, q3], 2)

def get_block_palette(main_color):
    r, g, b = main_color
    top = (min(r+60,255), min(g+60,255), min(b+60,255))
    left = (max(r-30,0), max(g-30,0), max(b-30,0))
    right = (max(r-55,0), max(g-55,0), max(b-55,0))
    return top, left, right

class Block:
    def __init__(self, x, y, size, z, color=(60,220,255), active=True, base=False):
        self.x = float(x)
        self.y = float(y)
        self.size = int(size)
        self.z = z
        self.active = active
        self.base = base
        self.color = color
        self.floor_color = (70, 82, 160) if not self.base else (80, 50, 20)
    def draw(self, camera_z):
        edge_col = self.color if not self.base else BASE_COLOR
        draw_hollow_iso_square(
            self.x, self.y, self.z, self.size, camera_z,
            color_edge=edge_col, color_floor=self.floor_color, shadow=True
        )

class TrimFragment:
    def __init__(self, x, y, size, z, vx, vy, vz, color, camera_z):
        self.x = x
        self.y = y
        self.size = size
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.oz = z
        self.color = color
        self.floor_color = (60, 75, 120)
        self.camera_z = camera_z
        self.age = 0
    def update(self, gravity=0.07):
        self.x += self.vx
        self.y += self.vy
        self.vz -= gravity
        self.z += self.vz
        self.age += 1
    def draw(self, camera_z):
        draw_hollow_iso_square(
            self.x, self.y, self.z, self.size, camera_z,
            color_edge=self.color, color_floor=self.floor_color, shadow=True
        )

def trim_block_with_trim(prev, curr, color):
    prev_x = int(round(prev.x))
    prev_y = int(round(prev.y))
    curr_x = int(round(curr.x))
    curr_y = int(round(curr.y))
    prev_size = prev.size
    curr_size = curr.size
    overlap_left = max(prev_x, curr_x)
    overlap_top = max(prev_y, curr_y)
    overlap_right = min(prev_x + prev_size, curr_x + curr_size)
    overlap_bottom = min(prev_y + prev_size, curr_y + curr_size)
    overlap_w = overlap_right - overlap_left
    overlap_h = overlap_bottom - overlap_top
    overlap_size = min(overlap_w, overlap_h)
    trim_pieces = []
    # Left trim
    if curr_x < overlap_left:
        trim_pieces.append({
            'x': curr_x,
            'y': overlap_top,
            'size': overlap_left - curr_x,
            'z': prev.z + 1,
            'vx': -0.06, 'vy': 0.02, 'vz': 0.8,
        })
    # Right trim
    if curr_x + curr_size > overlap_right:
        trim_pieces.append({
            'x': overlap_right,
            'y': overlap_top,
            'size': (curr_x + curr_size) - overlap_right,
            'z': prev.z + 1,
            'vx': 0.06, 'vy': 0.02, 'vz': 0.8,
        })
    # Back trim
    if curr_y < overlap_top:
        trim_pieces.append({
            'x': overlap_left,
            'y': curr_y,
            'size': overlap_top - curr_y,
            'z': prev.z + 1,
            'vx': 0.02, 'vy': -0.06, 'vz': 0.8,
        })
    # Front trim
    if curr_y + curr_size > overlap_bottom:
        trim_pieces.append({
            'x': overlap_left,
            'y': overlap_bottom,
            'size': (curr_y + curr_size) - overlap_bottom,
            'z': prev.z + 1,
            'vx': 0.02, 'vy': 0.06, 'vz': 0.8,
        })
    if overlap_size <= 0:
        return None, []
    trimmed_block = Block(overlap_left, overlap_top, overlap_size, prev.z + 1, color=color, active=False, base=False)
    return trimmed_block, trim_pieces

def get_entry_pos(base_block, size, direction):
    base_x, base_y, base_s, z = base_block.x, base_block.y, base_block.size, base_block.z
    if direction == "left":   return base_x - size, base_y
    elif direction == "right":return base_x + base_s, base_y
    elif direction == "front":return base_x, base_y - size
    elif direction == "back": return base_x, base_y + base_s
    else: raise ValueError("Invalid direction: " + direction)

def get_velocity(direction, score):
    base = 0.08
    peak = 0.2
    peak_score = 20   
    min_speed = 0.08
    # Parabola: -a(x-h)^2 + k
    a = (base - peak) / (peak_score ** 2)
    speed = a * (score - peak_score) ** 2 + peak
    speed = max(min_speed, speed)
    speed = min(speed, 0.7)  # absolute upper cap for sanity
    if direction == "left":    return speed, 0.0
    elif direction == "right": return -speed, 0.0
    elif direction == "front": return 0.0, speed
    elif direction == "back":  return 0.0, -speed



def get_bounce_limits(base_block, curr_block, direction):
    base_x, base_y, base_s = base_block.x, base_block.y, base_block.size
    size = curr_block.size
    if direction == "left" or direction == "right":
        min_x = base_x - size + 0.02
        max_x = base_x + base_s - 0.02
        return min_x, max_x
    elif direction == "front" or direction == "back":
        min_y = base_y - size + 0.02
        max_y = base_y + base_s - 0.02
        return min_y, max_y
    else:
        raise ValueError

def draw_night_sky_bg(frame, camera_z):
    # Smooth night-sky vertical gradient
    NIGHT_TOP = (30, 40, 80)
    NIGHT_BOT = (6, 8, 24)
    for y in range(HEIGHT):
        blend = y / HEIGHT
        color = (
            int(NIGHT_TOP[0] * (1 - blend) + NIGHT_BOT[0] * blend),
            int(NIGHT_TOP[1] * (1 - blend) + NIGHT_BOT[1] * blend),
            int(NIGHT_TOP[2] * (1 - blend) + NIGHT_BOT[2] * blend),
        )
        pygame.draw.line(SCREEN, color, (0, y), (WIDTH, y), 1)
    # Animated/parallax stars
    random.seed(46)  # Seed for consistent star pattern
    NUM_STARS = 90
    for i in range(NUM_STARS):
        # Spread stars, some farther back (smaller, dimmer, slower)
        layer = random.randint(1, 3)
        # x, y base positions
        x = random.randint(0, WIDTH)
        base_y = random.randint(0, HEIGHT)
        # Parallax amounts
        y = base_y + int(camera_z * 0.16 / layer)
        y = y % HEIGHT
        # Pulsing alpha
        alpha = 120 + int(100 * math.fabs(math.sin(frame * 0.01 + i)))
        color = (255, 255, 230, alpha)
        s = pygame.Surface((layer+1, layer+1), pygame.SRCALPHA)
        pygame.draw.circle(s, color, ((layer)//2, (layer)//2), layer//2)
        SCREEN.blit(s, (x, y))

def draw_text(msg, y):
    text = font.render(msg, True, TEXT_COLOR)
    rect = text.get_rect(center=(WIDTH // 2, y))
    SCREEN.blit(text, rect)

def game():
    BASE_POS = (-2, 0)
    BASE_SIZE = 4
    base_block = Block(BASE_POS[0], BASE_POS[1], BASE_SIZE, 0, color=BASE_COLOR, base=True)
    stack = [base_block]
    curr_z = 1
    curr_direction = random.choice(["front", "back", "left", "right"])
    curr_x, curr_y = get_entry_pos(base_block, BASE_SIZE, curr_direction)
    curr_color = random.choice(COLOR_LIST)
    curr = Block(curr_x, curr_y, BASE_SIZE, curr_z, color=curr_color)
    score = 0
    vx, vy = get_velocity(curr_direction, score)
    game_over = False
    camera_z = 0
    camera_target_z = 0
    camera_lerp = 0.14
    falling_pieces = []
    frame = 0
    while True:
        clock.tick(FPS)
        frame += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                return game()
            if not game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                new_color = random.choice(COLOR_LIST)
                trimmed, trims = trim_block_with_trim(stack[-1], curr, color=new_color)
                if trimmed is None:
                    game_over = True
                else:
                    stack.append(trimmed)
                    score += 1
                    for frag in trims:
                        frag_color = curr.color if hasattr(curr, 'color') else (90,190,255)
                        falling_pieces.append(TrimFragment(
                            frag['x'], frag['y'], frag['size'], frag['z'],
                            frag['vx'] + random.uniform(-0.015,0.015),
                            frag['vy'] + random.uniform(-0.015,0.015),
                            frag['vz'] + random.uniform(-0.02,0.02),
                            frag_color,
                            camera_z
                        ))
                    curr_z += 1
                    curr_direction = random.choice(["front", "back", "left", "right"])
                    curr_x, curr_y = get_entry_pos(trimmed, trimmed.size, curr_direction)
                    curr_color = random.choice(COLOR_LIST)
                    curr = Block(curr_x, curr_y, trimmed.size, curr_z, color=curr_color)
                    vx, vy = get_velocity(curr_direction, score)
                    camera_target_z = trimmed.z * BLOCK_HEIGHT - 2 * BLOCK_HEIGHT

        camera_z += (camera_target_z - camera_z) * camera_lerp

        draw_night_sky_bg(frame, camera_z)
        for block in stack:
            block.draw(camera_z)
        for f in falling_pieces[:]:
            f.update()
            f.draw(camera_z)
            if f.z < -8 or f.size < 0.7 or f.age > 130:
                falling_pieces.remove(f)

        if not game_over:
            if curr_direction == "left" or curr_direction == "right":
                min_x, max_x = get_bounce_limits(stack[-1], curr, curr_direction)
                curr.x += vx
                if curr.x < min_x:
                    curr.x = min_x
                    vx = abs(vx)
                elif curr.x > max_x:
                    curr.x = max_x
                    vx = -abs(vx)
            elif curr_direction == "front" or curr_direction == "back":
                min_y, max_y = get_bounce_limits(stack[-1], curr, curr_direction)
                curr.y += vy
                if curr.y < min_y:
                    curr.y = min_y
                    vy = abs(vy)
                elif curr.y > max_y:
                    curr.y = max_y
                    vy = -abs(vy)
            curr.draw(camera_z)
        else:
            draw_text("GAME OVER! Press R to restart", HEIGHT // 2 + 40)

        draw_text(f"Score: {score}", 32)
        pygame.display.flip()

game()
pygame.quit()
