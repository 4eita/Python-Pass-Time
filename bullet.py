import pygame
import random
import math

pygame.init()


WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bullet Hell Space Game")
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SPACE_BASE = (10, 10, 30)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 128, 255)
PURPLE = (200, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
level = 1

stars = [{'x': random.randint(0, WIDTH), 'y': random.randint(0, HEIGHT), 'twinkle': random.uniform(0.002, 0.008), 'phase': random.uniform(0, math.pi)} for _ in range(100)]

SPACE = list(SPACE_BASE)
def update_background_color():
    intensity = min(score / 100.0, 1.0)
    SPACE[0] = min(SPACE_BASE[0] + int(100 * intensity), 255)
    SPACE[1] = min(SPACE_BASE[1] + int(20 * intensity), 255)
    SPACE[2] = min(SPACE_BASE[2] + int(100 * intensity), 255)


def draw_stars(day_factor):
    for star in stars:
        t = pygame.time.get_ticks() * star['twinkle'] + star['phase']
        alpha = int((180 + math.sin(t) * 60) * (1 - day_factor))
        size = 1 + int((0.6 + 0.4 * math.sin(t)) > 1.1)
        star_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(star_surf, (255, 255, 255, alpha), (2, 2), size)
        screen.blit(star_surf, (star['x'], star['y']))

def check_level_change(score, bosses):
    global level
    if level == 1 and not bosses and score >= 20:
        bosses.append(Boss())
        level = 2
    elif level == 2 and not bosses and score >= 50:
        b1 = Boss()
        b2 = Boss()
        b1.base_x = WIDTH // 3
        b1.x = WIDTH // 3
        b2.base_x = 2 * WIDTH // 3
        b2.x = 2 * WIDTH // 3
        bosses.append(b1)
        bosses.append(b2)
        level = 3 

explosions = []
class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.life = 15

    def update(self):
        self.life -= 1

    def draw(self):
        if self.life > 0:
            alpha = max(0, 255 * self.life // 15)
            pygame.draw.circle(screen, (255, 100, 0, alpha), (int(self.x), int(self.y)), 20 - self.life)


class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 50
        self.speed = 5
        self.size = 20
        self.cooldown = 0
        self.hp = 3
        self.invincible = 0
        self.glow_phase = 0
        self.bombs = 3  
        self.bomb_cooldown = 0 

        self.trail = []
        self.trail_length = 18

    def move(self, keys):
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
        if keys[pygame.K_UP]:
            self.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.y += self.speed

        self.x = max(0, min(WIDTH, self.x))
        self.y = max(0, min(HEIGHT, self.y))

    def shoot(self):
        if self.cooldown == 0:
            bullets.append(Bullet(self.x, self.y, -8, YELLOW))
            self.cooldown = 10

    def use_bomb(self):
        if self.bombs > 0 and self.bomb_cooldown == 0:
            self.bombs -= 1
            self.bomb_cooldown = 60  

            boss_damage = 7  
            boss_bullets.clear()
            enemy_bullets.clear()
            enemies.clear()
            for boss in bosses:
                boss.hit(boss_damage)
                explosions.append(Explosion(boss.x, boss.y))
            for i in range(18):  
                explosions.append(Explosion(self.x + random.randint(-70, 70), self.y + random.randint(-70, 70)))

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
        self.glow_phase += 0.1
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)
        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1

    def draw(self):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(120 * i / self.trail_length)
            color = (0, 255, 255, alpha)
            trail_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, color, (self.size // 2, self.size // 2), self.size // 2)
            screen.blit(trail_surf, (tx - self.size // 2, ty - self.size // 2))

        glow_alpha = int(100 + 50 * math.sin(self.glow_phase))
        glow_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (0, 255, 255, glow_alpha), (self.size, self.size), self.size)
        screen.blit(glow_surface, (self.x - self.size, self.y - self.size))
        color = GREEN if self.invincible % 10 < 5 else YELLOW if self.invincible > 0 else GREEN
        pygame.draw.ellipse(screen, color, (self.x - self.size // 2, self.y - self.size, self.size, self.size * 2))
        pygame.draw.circle(screen, WHITE, (self.x, self.y - self.size), 4)


class Bullet:
    def __init__(self, x, y, speed, color):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.radius = 4

    def update(self):
        self.y += self.speed

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class EnemyBullet:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = 4

    def update(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius)

class BaseEnemy:
    def __init__(self, color=RED):
        self.x = random.randint(20, WIDTH - 20)
        self.y = random.randint(-100, -40)
        self.speed = random.uniform(1.0, 2.5)
        self.size = 20
        self.cooldown = random.randint(60, 120)
        self.color = color

    def update(self):
        self.y += self.speed
        if self.cooldown == 0:
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.hypot(dx, dy)
            if dist != 0:
                dx /= dist
                dy /= dist
            enemy_bullets.append(EnemyBullet(self.x, self.y, dx * 4, dy * 4))
            self.cooldown = random.randint(90, 150)
        else:
            self.cooldown -= 1

    def draw(self):
        pygame.draw.ellipse(screen, self.color, (self.x - self.size//2, self.y - self.size//2, self.size, self.size))
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 5)


class Boss:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = 90
        self.base_x = self.x
        self.base_y = self.y
        self.hp = 70
        self.max_hp = 70
        self.cooldown = 0
        self.pattern_phase = 0

    def update(self):
        self.pattern_phase += 1

        self.x = self.base_x + math.sin(pygame.time.get_ticks() / 700) * 120
        self.y = self.base_y + math.sin(pygame.time.get_ticks() / 1400) * 20


        enraged = self.hp < (self.max_hp * 0.15)

        if self.cooldown == 0:
            if enraged:

                if self.pattern_phase % 2 == 0:
         
                    boss_bullets.append(BossTrackingBullet(self.x, self.y))
                    boss_bullets.append(BossTrackingBullet(self.x + 10, self.y))
                else:

                    boss_bullets.append(BossBouncyBullet(self.x - 25, self.y + 12, -5, 3))
                    boss_bullets.append(BossBouncyBullet(self.x + 25, self.y + 12, 5, 3))
                    boss_bullets.append(BossBouncyBullet(self.x, self.y + 18, 0, 5))
                self.cooldown = 18  
            else:

                pattern = self.pattern_phase % 3
                if pattern == 0:
                    for angle in range(0, 360, 45):
                        rad = math.radians(angle)
                        boss_bullets.append(EnemyBullet(self.x, self.y, math.cos(rad) * 3, math.sin(rad) * 3))
                elif pattern == 1:
                    for angle in range(22, 382, 45):  
                        rad = math.radians(angle)
                        boss_bullets.append(EnemyBullet(self.x, self.y, math.cos(rad) * 3.5, math.sin(rad) * 3.5))
                else:
                    for angle in range(0, 360, 30):
                        rad = math.radians(angle)
                        boss_bullets.append(EnemyBullet(self.x, self.y, math.cos(rad) * 2.3, math.sin(rad) * 2.3))
                self.cooldown = 27
        else:
            self.cooldown -= 1

    def draw(self):
        pygame.draw.ellipse(screen, (120, 0, 180), (self.x - 36, self.y - 18, 72, 36))
        pygame.draw.circle(screen, (255, 230, 40), (int(self.x), int(self.y)), 16)
        pygame.draw.circle(screen, (130, 45, 255), (int(self.x), int(self.y)), 25, 3)
        pygame.draw.polygon(screen, (80, 200, 255), [(self.x - 40, self.y), (self.x - 60, self.y + 8), (self.x - 40, self.y + 20)])
        pygame.draw.polygon(screen, (80, 200, 255), [(self.x + 40, self.y), (self.x + 60, self.y + 8), (self.x + 40, self.y + 20)])
 
        pygame.draw.rect(screen, RED,   (self.x - 40, self.y - 28, 80, 6))
        pygame.draw.rect(screen, GREEN, (self.x - 40, self.y - 28, max(0, 80 * self.hp / self.max_hp), 6))

    def hit(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0


def enemy_hit(enemy):
    explosions.append(Explosion(enemy.x, enemy.y))

class BossBullet:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = 4

    def update(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)

class BossBouncyBullet(EnemyBullet):
    def __init__(self, x, y, dx, dy):
        super().__init__(x, y, dx, dy)
        self.radius = 5
        self.color = ORANGE
        self.life = 250
        self.max_life = 240
        self.trail = []

    def update(self):
        self.x += self.dx
        self.y += self.dy

        if self.x < 0 or self.x > WIDTH:
            self.dx *= -1
        if self.y < 0 or self.y > HEIGHT:
            self.dy *= -1
        self.life -= 1
        self.trail.append((self.x, self.y))
        if len(self.trail) > 30:
            self.trail.pop(0)

    def draw(self):
        fade = max(0, int(255 * self.life / self.max_life))

        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(fade * i / len(self.trail)) if self.trail else 0
            trail_surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)

            pygame.draw.circle(trail_surf, (255, 140, 0), (self.radius, self.radius), self.radius)
            trail_surf.set_alpha(alpha)
            screen.blit(trail_surf, (tx - self.radius, ty - self.radius))

        bouncy_surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(bouncy_surf, (255, 140, 0), (self.radius, self.radius), self.radius)
        bouncy_surf.set_alpha(fade)
        screen.blit(bouncy_surf, (self.x - self.radius, self.y - self.radius))




class BossTrackingBullet(EnemyBullet):
    def __init__(self, x, y):
        super().__init__(x, y, 0, 0)
        self.radius = 6
        self.color = CYAN
        self.speed = 4
        self.tracking_time = 60 
        self.life = 180  
        self.trail = []

    def update(self):

        if self.tracking_time > 0:
            dx, dy = player.x - self.x, player.y - self.y
            dist = math.hypot(dx, dy) or 1
            self.dx = dx / dist * self.speed
            self.dy = dy / dist * self.speed
            self.tracking_time -= 1
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

        self.trail.append((self.x, self.y))
        if len(self.trail) > 24:
            self.trail.pop(0)

    def draw(self):
        fade = max(0, int(255 * self.life / 180))
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(fade * i / len(self.trail)) if self.trail else 0
            trail_surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (0, 255, 255, alpha), (self.radius, self.radius), self.radius)
            screen.blit(trail_surf, (tx - self.radius, ty - self.radius))
        bullet_surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(bullet_surf, (0, 255, 255, fade), (self.radius, self.radius), self.radius)
        screen.blit(bullet_surf, (self.x - self.radius, self.y - self.radius))

class BouncyEnemy(BaseEnemy):
    def __init__(self):
        super().__init__(ORANGE)
        self.dx = random.choice([-2, 2])

    def update(self):
        super().update()
        self.x += self.dx
        if self.x < 0 or self.x > WIDTH:
            self.dx *= -1

class TrackingEnemy(BaseEnemy):
    def __init__(self):
        super().__init__(CYAN)

    def update(self):
        angle = math.atan2(player.y - self.y, player.x - self.x)
        self.x += math.cos(angle) * self.speed
        self.y += math.sin(angle) * self.speed
        if self.cooldown == 0:
            enemy_bullets.append(EnemyBullet(self.x, self.y, math.cos(angle) * 4, math.sin(angle) * 4))
            self.cooldown = random.randint(100, 140)
        else:
            self.cooldown -= 1

player = Player()
bullets = []
enemies = []
boss = None
boss_bullets = []
enemy_bullets = []
score = 0
font = pygame.font.SysFont(None, 36)

running = True
bosses = []
score = 0

while running:
    update_background_color()
    screen.fill(SPACE)
    draw_stars(0)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if keys[pygame.K_SPACE]:
        player.shoot()
    elif keys[pygame.K_x]:
        player.use_bomb()

    player.move(keys)
    player.update()
    player.draw()

    for bullet in bullets[:]:
        bullet.update()
        if bullet.y < 0:
            bullets.remove(bullet)
        else:
            bullet.draw()

    if not bosses and level == 1:
        if random.random() < 0.02:
            enemy_type = random.choice([BaseEnemy, BouncyEnemy, TrackingEnemy])
            enemies.append(enemy_type())

    for boss in bosses[:]:
        boss.update()
        boss.draw()
        for bullet in bullets[:]:
            if abs(boss.x - bullet.x) < 40 and abs(boss.y - bullet.y) < 20:
                boss.hit(1)
                explosions.append(Explosion(boss.x, boss.y))
                bullets.remove(bullet)
                if boss.hp <= 0:
                    # Mega explosion on death
                    for _ in range(12):
                        ex = Explosion(boss.x + random.randint(-32, 32), boss.y + random.randint(-18,18))
                        explosions.append(ex)
                    bosses.remove(boss)
                break

    check_level_change(score, bosses)

    for enemy in enemies[:]:
        enemy.update()
        enemy.draw()
        if enemy.y > HEIGHT:
            enemies.remove(enemy)
            continue
        for bullet in bullets[:]:
            if abs(enemy.x - bullet.x) < 20 and abs(enemy.y - bullet.y) < 20:
                explosions.append(Explosion(enemy.x, enemy.y))
                enemies.remove(enemy)
                bullets.remove(bullet)
                score += 1
                break

    for b in boss_bullets[:]:
        b.update()
        b.draw()
        remove_bullet = False
        if abs(b.x - player.x) < 10 and abs(b.y - player.y) < 10 and player.invincible == 0:
            player.hp -= 1
            player.invincible = 60
            remove_bullet = True
        if hasattr(b, 'life') and b.life <= 0:
            remove_bullet = True
        elif (b.x < -40 or b.x > WIDTH + 40 or b.y < -40 or b.y > HEIGHT + 40):
            remove_bullet = True
        if remove_bullet:
            boss_bullets.remove(b)

    for b in enemy_bullets[:]:
        b.update()
        b.draw()
        if abs(b.x - player.x) < 10 and abs(b.y - player.y) < 10 and player.invincible == 0:
            player.hp -= 1
            player.invincible = 60
            enemy_bullets.remove(b)

    if player.hp <= 0:
        running = False


    for i in range(player.hp):
        pygame.draw.rect(screen, GREEN, (WIDTH - 30 * (i + 1), 10, 20, 20))

    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    for i in range(player.bombs):
        pygame.draw.circle(screen, CYAN, (WIDTH - 30 * (i + 1), 40), 10)
    bomb_text = font.render(f"Bombs: {player.bombs}", True, CYAN)
    screen.blit(bomb_text, (WIDTH - 120, 40))

    for explosion in explosions[:]:
        explosion.update()
        explosion.draw()
        if explosion.life <= 0:
            explosions.remove(explosion)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
