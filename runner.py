import pygame
import sys
import random
import math

WIDTH, HEIGHT = 1600, 900
FPS = 60
SKY_DAY = (135, 206, 250)
SKY_NIGHT = (25, 25, 112)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_COLOR = (255, 255, 255)
OBSTACLE_COLOR = (220, 20, 60)
POWERUP_COLOR = (34, 139, 34)
GROUND_COLOR = (139, 69, 19)
CLOUD_COLOR = (255, 255, 255)
DUST_COLOR = (200, 200, 200)
BIRD_COLOR = (0, 0, 0)
SUN_COLOR = (255, 223, 0)
MOON_COLOR = (240, 240, 255)
GRAVITY = 1
JUMP_VELOCITY = -15
DUCK_DURATION = 30
NUM_STARS = 60

patterns = [
    # Simple jump
    [(0, 0, 20, 40)],
    # Low wall, small wall
    [(0, 0, 20, 20), (80, 0, 20, 40)],
    # 3 short blocks in sequence
    [(0, 0, 20, 20), (40, 0, 20, 20), (80, 0, 20, 20)],
    # Zig-zag: low, tall, low
    [(0, 0, 20, 20), (60, -20, 20, 60), (120, 0, 20, 20)],
    # Jump-jump pattern
    [(0, 0, 20, 40), (100, 0, 20, 40)],
]

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

clouds = [pygame.Rect(random.randint(0, WIDTH), random.randint(20, 100), 60, 30) for _ in range(5)]
birds = []
ground_scroll = 0
particles = []
time_of_day = 0
stars = []
NUM_STARS = 60
stars = []
for _ in range(NUM_STARS):
    x = random.randint(0, WIDTH)
    y = random.randint(5, HEIGHT // 2)
    twinkle_speed = random.uniform(0.005, 0.02)
    phase = random.uniform(0, math.pi*2)
    stars.append({'x': x, 'y': y, 'twinkle': twinkle_speed, 'phase': phase})


class Bird:
    def __init__(self, player):
        self.rect = pygame.Rect(WIDTH + random.randint(0, 200), random.randint(30, 150), 30, 15)
        self.speed = random.randint(5, 7)
        self.dive_speed = 4
        self.state = 'attack'
        self.target = player  

    def update(self):

        self.rect.x -= self.speed
        target_y = self.target.base_y  
        target_y += self.target.h // 3

        if abs(self.rect.centery - target_y) > self.dive_speed:
            if self.rect.centery < target_y:

                new_y = min(self.rect.centery + self.dive_speed, target_y)
                self.rect.centery = min(new_y, target_y)
            elif self.rect.centery > target_y:
                new_y = max(self.rect.centery - self.dive_speed, target_y)
                self.rect.centery = max(new_y, target_y)
        if self.rect.bottom > self.target.base_y + self.target.h:
            self.rect.bottom = self.target.base_y + self.target.h
        if self.rect.top < 0:
            self.rect.top = 0


    def draw(self):
        pygame.draw.polygon(screen, BIRD_COLOR, [
            (self.rect.x, self.rect.y + self.rect.height // 2),
            (self.rect.x + self.rect.width // 2, self.rect.y),
            (self.rect.x + self.rect.width, self.rect.y + self.rect.height // 2),
            (self.rect.x + self.rect.width // 2, self.rect.y + self.rect.height)
        ])

    def off_screen(self):
        return self.rect.right < 0

def draw_vertical_gradient(top_color, bottom_color):
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        col = (
            int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio),
            int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio),
            int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        )
        pygame.draw.line(screen, col, (0, y), (WIDTH, y))


def draw_stars(day_factor):
    for star in stars:
        t = pygame.time.get_ticks() * star['twinkle'] + star['phase']
        alpha = int((180 + math.sin(t) * 60) * (1 - day_factor))
        size = 1 + int((0.6 + 0.4 * math.sin(t)) > 1.1)

        star_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(star_surf, (255, 255, 255, alpha), (2, 2), size)
        screen.blit(star_surf, (star['x'], star['y']))


def draw_hills(offset, color, base_y, height, speed_factor):
    for x in range(-WIDTH, WIDTH * 2, 120):
        pygame.draw.ellipse(
            screen,
            color,
            (x + int(ground_scroll * speed_factor) % (WIDTH * 2), base_y, 180, height)
        )


def draw_background(speed):
    global ground_scroll, clouds, time_of_day, birds

    time_of_day += 0.001
    day_factor = (math.sin(time_of_day) + 1) / 2

    # Gradient sky (optional)
    top_sky = (
        int(SKY_NIGHT[0] + (SKY_DAY[0]-SKY_NIGHT[0]) * day_factor),
        int(SKY_NIGHT[1] + (SKY_DAY[1]-SKY_NIGHT[1]) * day_factor),
        int(SKY_NIGHT[2] + (SKY_DAY[2]-SKY_NIGHT[2]) * day_factor)
    )
    bottom_sky = (
        int(SKY_NIGHT[0] + (SKY_DAY[0]-SKY_NIGHT[0]) * day_factor * 0.5),
        int(SKY_NIGHT[1] + (SKY_DAY[1]-SKY_NIGHT[1]) * day_factor * 0.5),
        int(SKY_NIGHT[2] + (SKY_DAY[2]-SKY_NIGHT[2]) * day_factor * 0.5)
    )
    draw_vertical_gradient(top_sky, bottom_sky)

    # Sun and moon as before
    sun_x = int(WIDTH / 2 + math.cos(time_of_day) * WIDTH)
    sun_y = int(180 + math.sin(time_of_day) * 100)
    pygame.draw.circle(screen, SUN_COLOR, (sun_x % WIDTH, sun_y), 30)
    moon_x = int(WIDTH / 2 + math.cos(time_of_day + math.pi) * WIDTH)
    moon_y = int(180 + math.sin(time_of_day + math.pi) * 100)
    pygame.draw.circle(screen, MOON_COLOR, (moon_x % WIDTH, moon_y), 20)

    # Parallax hills
    draw_hills(offset=0, color=(61,46,61), base_y=HEIGHT-100, height=46, speed_factor=0.15)
    draw_hills(offset=0, color=(34,77,34), base_y=HEIGHT-54, height=36, speed_factor=0.3)

    # Stars at night
    if day_factor < 0.4:
        draw_stars(day_factor)

    # Clouds
    for cloud in clouds:
        pygame.draw.ellipse(screen, CLOUD_COLOR, cloud)
        cloud.x -= 1
        if cloud.right < 0:
            cloud.x = WIDTH + random.randint(20, 100)
            cloud.y = random.randint(20, 100)

    # Ground
    ground_scroll = (ground_scroll - speed) % WIDTH
    for i in range(2):
        pygame.draw.rect(screen, GROUND_COLOR, (i * WIDTH - ground_scroll, HEIGHT - 20, WIDTH, 20))

    update_particles()


def update_particles():
    for p in particles[:]:
        p['x'] += p['dx']
        p['y'] += p['dy']
        p['life'] -= 1
        if p['life'] <= 0:
            particles.remove(p)
        else:
            pygame.draw.circle(screen, DUST_COLOR, (int(p['x']), int(p['y'])), p['size'])

def emit_dust(x, y):
    for _ in range(5):
        particles.append({
            'x': x + random.randint(-5, 5),
            'y': y + random.randint(0, 5),
            'dx': random.uniform(-1, 1),
            'dy': random.uniform(-1, 0.5),
            'life': random.randint(10, 20),
            'size': random.randint(1, 3)
        })

class Player:
    def __init__(self):
        self.x = 100
        self.base_y = HEIGHT - 60
        self.y = self.base_y
        self.w = 40
        self.h = 40
        self.vel_x = 0 
        self.target_w = 40
        self.target_h = 40
        self.vel_y = 0
        self.on_ground = True
        self.is_ducking = False
        self.can_double_jump = True 
        self.duck_timer = 0
        self.form = 'square'
        self.invincible = 0
        self.pending_duck = False

        # Enhanced controls
        self.coyote_timer = 0     # coyote time (frames after leaving ground)
        self.jump_buffer = 0      # jump buffer (if pressed before landing)
        self.max_coyote = 8
        self.max_jump_buffer = 8

    def update(self):
        if self.on_ground:
            self.coyote_timer = self.max_coyote
        else:
            self.coyote_timer = max(0, self.coyote_timer - 1)

        if self.jump_buffer > 0:
            self.jump_buffer -= 1

        if self.jump_buffer > 0 and (self.on_ground or self.coyote_timer > 0):
            self.vel_y = self.buffered_jump_velocity
            self.on_ground = False
            self.form = 'circle'
            self.jump_buffer = 0
            emit_dust(self.x + self.w // 2, self.y + self.h)

        if not self.on_ground:
            self.vel_y += GRAVITY * 0.85  
            self.y += self.vel_y
            if self.y >= self.base_y:
                self.y = self.base_y
                self.vel_y = 0
                self.on_ground = True
                self.form = 'square'
                self.vel_x = 0      
                self.can_double_jump = True  
                emit_dust(self.x + self.w // 2, self.y + self.h)

                if self.pending_duck and not self.is_ducking:
                    self.is_ducking = True
                    self.duck_timer = DUCK_DURATION
                    self.target_h = 20
                    self.y = self.base_y + 20
                    self.form = 'circle'
                    self.pending_duck = False

        if self.is_ducking:
            self.duck_timer -= 1
            if self.duck_timer <= 0:
                self.is_ducking = False
                self.target_h = 40
                self.y = self.base_y
                self.form = 'square'

        self.w += (self.target_w - self.w) * 0.2
        self.h += (self.target_h - self.h) * 0.2

        if self.invincible > 0:
            self.invincible -= 1

    def jump(self):
        if self.on_ground or self.coyote_timer > 0:
            self.is_ducking = False
            self.target_h = 40
            self.y = self.base_y
            self.form = 'circle'
            self.vel_y = JUMP_VELOCITY      
            self.on_ground = False
            self.can_double_jump = True    
            emit_dust(self.x + self.w // 2, self.y + self.h)
        elif self.can_double_jump:
            self.vel_y = JUMP_VELOCITY // 1.25   
            self.can_double_jump = False
            emit_dust(self.x + self.w // 2, self.y + self.h)


    def duck(self):
        if self.on_ground and not self.is_ducking:
            self.is_ducking = True
            self.duck_timer = DUCK_DURATION
            self.target_h = 20
            self.y = self.base_y + 20
            self.form = 'circle'
            self.pending_duck = False
        elif not self.on_ground:
            self.vel_y = 20
            self.pending_duck = True

    def draw(self, screen):
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        color = PLAYER_COLOR if self.invincible % 20 < 10 else (255, 215, 0)
        if self.form == 'circle':
            pygame.draw.ellipse(screen, color, rect)
        else:
            pygame.draw.rect(screen, color, rect)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


class Obstacle:
    def __init__(self, x, y, w, h, speed, kind='normal', chasing=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.speed = speed
        self.kind = kind
        self.chasing = chasing  

    def update(self, player=None):  
        self.rect.x -= self.speed

        if self.chasing and player is not None:

            if self.rect.x > player.x + player.w:
                chase_speed = 4 
                self.rect.x -= chase_speed


    def draw(self, screen):
        color = OBSTACLE_COLOR
        if self.kind == 'ceiling':
            color = (255, 128, 0)  
        pygame.draw.rect(screen, color, self.rect)

    def is_off_screen(self):
        return self.rect.right < 0

class FallingObstacle(Obstacle):
    def __init__(self, speed):
        x = WIDTH + 20
        w, h = 40, 20
        y = -20
        super().__init__(x, y, w, h, speed)
        self.fall_speed = 3.5

    def update(self):
        self.rect.x -= self.speed

        if self.rect.bottom < HEIGHT - 40:
            self.rect.y += self.fall_speed

        if self.rect.bottom > HEIGHT - 20:
            self.rect.bottom = HEIGHT - 20

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 128, 0), self.rect)



class PowerUp:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.speed = 6

    def update(self):
        self.rect.x -= self.speed

    def draw(self, screen):
        pygame.draw.ellipse(screen, POWERUP_COLOR, self.rect)

    def is_off_screen(self):
        return self.rect.right < 0

def spawn_pattern(speed):
    pattern = random.choice(patterns)
    base_x = WIDTH + 20
    obs_list = []
    for (x_off, y_off, w, h) in pattern:
        x = base_x + x_off
        y = HEIGHT - h - 20 + y_off 
        obs_list.append(Obstacle(x, y, w, h, speed, 'normal'))
    return obs_list

def spawn_obstacle(speed):
    obstacle_types = ['pattern', 'chasing', 'ceiling', 'falling']
    kind = random.choices(obstacle_types, weights=[4, 1, 1, 1])[0]

    if kind == 'pattern':
        return spawn_pattern(speed)
    elif kind == 'chasing':
        height = random.choice([20, 40])
        return [Obstacle(WIDTH + 20, HEIGHT - height - 20, 20, height, speed, 'normal', chasing=True)]
    elif kind == 'ceiling':
        return [Obstacle(WIDTH + 20, HEIGHT - 70, 60, 18, speed, 'ceiling')]
    elif kind == 'falling':
        return [FallingObstacle(speed)]



def spawn_powerup():
    return PowerUp(WIDTH + 20, HEIGHT - 100)

def draw_text(text, x, y):
    img = font.render(text, True, BLACK)
    screen.blit(img, (x, y))

def load_high_score(filename="highscore_runner.txt"):
    try:
        with open(filename, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_high_score(score, filename="highscore_runner.txt"):
    with open(filename, "w") as f:
        f.write(str(score))


def main():
    while True:
        score = 0
        speed = 6  
        game_over = False
        obstacles = []
        birds = []
        powerups = []
        frames_since_start = 0
        spawn_timer = random.randint(50, 90)
        power_timer = random.randint(400, 800)
        player = Player()  
        high_score = load_high_score()

        while not game_over:
            frames_since_start += 1
            draw_background(speed)

            if frames_since_start > FPS * 2:  
                if random.random() < 0.003:
                    if len(birds) < 2:
                        bird_y = None
                        safe_margin = 80 
                        while bird_y is None:
                            candidate = random.randint(30, 150)
                            if abs(candidate - player.base_y) > safe_margin:
                                bird_y = candidate
                        bird = Bird(player)
                        bird.rect.y = bird_y
                        birds.append(bird)


            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_SPACE:
                        player.jump()
                    elif event.key == pygame.K_DOWN:
                        player.duck()


            player.update()
            if player.on_ground and not player.is_ducking:
                emit_dust(player.x, player.y + player.h - 2)
            player.draw(screen)

            spawn_timer -= 1
            if spawn_timer <= 0:
                new_obs = spawn_obstacle(speed)
                obstacles.extend(new_obs)
                spawn_timer = random.randint(50, 90)


            power_timer -= 1
            if power_timer <= 0:
                powerups.append(spawn_powerup())
                power_timer = random.randint(400, 800)

            for obstacle in obstacles[:]:
                obstacle.update()
                obstacle.draw(screen)
                if obstacle.is_off_screen():
                    obstacles.remove(obstacle)
                elif player.get_rect().colliderect(obstacle.rect):
                    if player.invincible <= 0:
                        game_over = True

            for powerup in powerups[:]:
                powerup.update()
                powerup.draw(screen)
                if powerup.is_off_screen():
                    powerups.remove(powerup)
                elif player.get_rect().colliderect(powerup.rect):
                    player.invincible = 200
                    powerups.remove(powerup)

            if random.random() < 0.003:    
                if len(birds) < 1:      
                    birds.append(Bird(player))

            for bird in birds[:]:
                bird.update()
                bird.draw()
                if player.get_rect().colliderect(bird.rect) and not player.is_ducking:
                    if player.invincible <= 0:
                        game_over = True
                if bird.off_screen():
                    birds.remove(bird)



            score += 1
            speed = 6 + score / 1000  


            draw_text(f"Score: {score}", 10, 10)
            draw_text(f"High Score: {high_score}", 10, 40)
            pygame.display.flip()
            clock.tick(FPS)

        if score > high_score:
            high_score = score
            save_high_score(high_score)
        draw_text("Game Over - Press R to Restart", WIDTH//2 - 160, HEIGHT//2)
        pygame.display.flip()

        waiting = True


        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        waiting = False

if __name__ == "__main__":
    main()
