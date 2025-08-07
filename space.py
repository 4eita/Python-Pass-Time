import pygame
import random
import math

# Initialize pygame
pygame.init()

# Screen
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Space Invaders")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# Player
player_width = 50
player_height = 40
player_x = screen_width // 2 - player_width // 2
player_y = screen_height - player_height - 10
player_speed = 5

# Bullet
bullet_radius = 5
bullet_speed = 7
bullet_x = 0
bullet_y = player_y
bullet_state = "ready"  # "ready" or "fire"

# Enemy
enemy_width = 40
enemy_height = 30
enemy_speed = 3
enemy_drop = 40
num_enemies = 6
enemies = []

for _ in range(num_enemies):
    x = random.randint(0, screen_width - enemy_width)
    y = random.randint(50, 150)
    dx = enemy_speed
    enemies.append([x, y, dx])

# Score
score = 0
font = pygame.font.Font(None, 36)

# Game Over
game_over = False

def draw_player(x, y):
    pygame.draw.rect(screen, BLUE, (x, y, player_width, player_height))

def draw_enemy(x, y):
    pygame.draw.rect(screen, RED, (x, y, enemy_width, enemy_height))

def fire_bullet(x, y):
    pygame.draw.circle(screen, WHITE, (x + player_width // 2, y), bullet_radius)

def is_collision(ex, ey, bx, by):
    dist = math.hypot(ex + enemy_width // 2 - bx, ey + enemy_height // 2 - by)
    return dist < 27

def draw_score():
    score_text = font.render("Score: " + str(score), True, WHITE)
    screen.blit(score_text, (10, 10))

def draw_game_over():
    over_text = font.render("GAME OVER", True, WHITE)
    screen.blit(over_text, (screen_width // 2 - 100, screen_height // 2))

# Game loop
running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BLACK)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Key input
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_x -= player_speed
    if keys[pygame.K_RIGHT]:
        player_x += player_speed
    if keys[pygame.K_SPACE] and bullet_state == "ready":
        bullet_x = player_x
        bullet_y = player_y
        bullet_state = "fire"

    # Clamp player
    player_x = max(0, min(player_x, screen_width - player_width))

    # Move bullet
    if bullet_state == "fire":
        fire_bullet(bullet_x, bullet_y)
        bullet_y -= bullet_speed
        if bullet_y < 0:
            bullet_state = "ready"

    # Move enemies
    for enemy in enemies:
        x, y, dx = enemy
        x += dx

        # Change direction
        if x <= 0 or x >= screen_width - enemy_width:
            dx *= -1
            y += enemy_drop

        # Update position
        enemy[0] = x
        enemy[1] = y
        enemy[2] = dx

        # Game over
        if y + enemy_height >= player_y:
            game_over = True

        # Check collision
        if bullet_state == "fire":
            if is_collision(x, y, bullet_x + player_width // 2, bullet_y):
                bullet_state = "ready"
                bullet_y = player_y
                score += 1
                # Reset enemy
                enemy[0] = random.randint(0, screen_width - enemy_width)
                enemy[1] = random.randint(50, 150)

        draw_enemy(x, y)

    draw_player(player_x, player_y)
    draw_score()

    if game_over:
        draw_game_over()
        pygame.display.update()
        pygame.time.delay(3000)
        break

    pygame.display.update()
    clock.tick(60)

pygame.quit()
