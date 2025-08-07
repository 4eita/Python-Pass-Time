import pygame
import random
import os
import time

pygame.init()

# Écran
width, height = 600, 400
win = pygame.display.set_mode((width, height))
pygame.display.set_caption("🐍 Snake Game Deluxe")

# Couleurs
white = (255, 255, 255)
black = (0, 0, 0)
red = (200, 30, 30)
green = (0, 255, 0)
blue = (40, 100, 200)
yellow = (255, 255, 0)
gray = (100, 100, 100)

# Ressources
highscore_file = "highscore.txt"
snake_block = 10
clock = pygame.time.Clock()

# Police et son
font_style = pygame.font.SysFont("consolas", 24)
score_font = pygame.font.SysFont("consolas", 28, bold=True)

try:
    eat_sound = pygame.mixer.Sound("eat.wav")
    hit_sound = pygame.mixer.Sound("hit.wav")
except:
    eat_sound = hit_sound = None

# Fonctions utilitaires
def get_highscore():
    if not os.path.exists(highscore_file):
        return 0
    with open(highscore_file, "r") as f:
        return int(f.read())

def save_highscore(score):
    if score > get_highscore():
        with open(highscore_file, "w") as f:
            f.write(str(score))

def draw_text_center(msg, color, y_offset=0, size=font_style):
    mesg = size.render(msg, True, color)
    rect = mesg.get_rect(center=(width / 2, height / 2 + y_offset))
    win.blit(mesg, rect)

def draw_score(score, highscore, elapsed_time):
    text = score_font.render(f"Score: {score}  HS: {highscore}  Time: {int(elapsed_time)}s", True, white)
    win.blit(text, [10, 10])

def draw_snake(snake_list):
    for i, segment in enumerate(snake_list):
        color = yellow if i == len(snake_list) - 1 else black
        pygame.draw.rect(win, color, [segment[0], segment[1], snake_block, snake_block])

def draw_food(foodx, foody, pulse):
    green_pulse = (0, min(255, 200 + pulse), 0)
    pygame.draw.rect(win, green_pulse, [foodx, foody, snake_block, snake_block])

def draw_obstacles(obstacles):
    for obs in obstacles:
        pygame.draw.rect(win, gray, [obs[0], obs[1], snake_block, snake_block])

def generate_obstacles(count):
    return [[random.randrange(0, width // 10) * 10, random.randrange(0, height // 10) * 10] for _ in range(count)]

# Menus
def main_menu():
    while True:
        win.fill(blue)
        draw_text_center("🐍 Snake Game Deluxe", white, -60, score_font)
        draw_text_center("1 - Facile   2 - Moyen   3 - Difficile", white, -10)
        draw_text_center("Q - Quitter", white, 30)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 10, 5
                elif event.key == pygame.K_2:
                    return 15, 10
                elif event.key == pygame.K_3:
                    return 20, 20
                elif event.key == pygame.K_q:
                    pygame.quit(); quit()

# Jeu principal
def game_loop(start_speed, obstacle_count):
    x1, y1 = width / 2, height / 2
    x1_change, y1_change = 0, 0
    direction = "STOP"

    snake_list = []
    length_of_snake = 1
    snake_speed = start_speed
    highscore = get_highscore()

    foodx = round(random.randrange(0, width - snake_block) / 10.0) * 10
    foody = round(random.randrange(0, height - snake_block) / 10.0) * 10

    pulse = 0
    pulse_dir = 5
    obstacles = generate_obstacles(obstacle_count)
    game_over, paused = False, False
    start_time = time.time()

    while not game_over:
        elapsed_time = time.time() - start_time

        while paused:
            win.fill(blue)
            draw_text_center("Pause - P pour reprendre", white)
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    paused = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and direction != "RIGHT":
                    x1_change, y1_change = -snake_block, 0
                    direction = "LEFT"
                elif event.key == pygame.K_RIGHT and direction != "LEFT":
                    x1_change, y1_change = snake_block, 0
                    direction = "RIGHT"
                elif event.key == pygame.K_UP and direction != "DOWN":
                    x1_change, y1_change = 0, -snake_block
                    direction = "UP"
                elif event.key == pygame.K_DOWN and direction != "UP":
                    x1_change, y1_change = 0, snake_block
                    direction = "DOWN"
                elif event.key == pygame.K_p:
                    paused = True

        x1 += x1_change
        y1 += y1_change

        if x1 >= width or x1 < 0 or y1 >= height or y1 < 0:
            game_over = True
            if hit_sound: hit_sound.play()

        win.fill(blue)
        draw_obstacles(obstacles)

        draw_food(foodx, foody, pulse)
        pulse += pulse_dir
        if pulse > 55 or pulse < 0: pulse_dir *= -1

        snake_head = [x1, y1]
        snake_list.append(snake_head)
        if len(snake_list) > length_of_snake:
            del snake_list[0]

        if snake_head in snake_list[:-1] or snake_head in obstacles:
            game_over = True
            if hit_sound: hit_sound.play()

        draw_snake(snake_list)
        draw_score(length_of_snake - 1, highscore, elapsed_time)
        pygame.display.update()

        if x1 == foodx and y1 == foody:
            foodx = round(random.randrange(0, width - snake_block) / 10.0) * 10
            foody = round(random.randrange(0, height - snake_block) / 10.0) * 10
            length_of_snake += 1
            snake_speed += 0.5
            if eat_sound: eat_sound.play()

        clock.tick(snake_speed)

    # Fin
    score = length_of_snake - 1
    save_highscore(score)

    win.fill(blue)
    draw_text_center("💀 Game Over", red, -30)
    draw_text_center("R - Rejouer  |  Q - Quitter", white, 10)
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return
                elif event.key == pygame.K_q:
                    pygame.quit(); quit()

# Lancer le jeu
while True:
    speed, obs = main_menu()
    game_loop(speed, obs)
