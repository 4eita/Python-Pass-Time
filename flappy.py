import pygame
import random
import sys
import os


pygame.init()
WIDTH, HEIGHT = 400, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 32)

GRAVITY = 0.25
BIRD_X = 50
PIPE_GAP = 150
PIPE_FREQ = 1500
BASE_Y = HEIGHT - 100
HIGH_SCORE_FILE = "highscore_flappy.txt"

SKY_BLUE = (135, 206, 235)
BIRD_COLOR = (255, 255, 0)
PIPE_COLOR = (0, 200, 0)
BASE_COLOR = (222, 184, 135)
SUN_COLOR = (255, 255, 100)
CLOUD_COLOR = (255, 255, 255)
DARK_GREEN = (0, 100, 0)
BONUS_COLOR = (255, 215, 0)

class Bird:
    def __init__(self):
        self.y = HEIGHT // 2
        self.vel = 0
        self.tick = 0
        self.radius = 12
        self.wing_up = True

    def flap(self):
        self.vel = -6
        self.tick = 0

    def update(self):
        self.tick += 1
        self.vel += GRAVITY
        self.y += self.vel
        self.wing_up = not self.wing_up

    def draw(self):
        pygame.draw.circle(SCREEN, BIRD_COLOR, (BIRD_X, int(self.y)), self.radius)
        wing_offset = -6 if self.wing_up else 6
        pygame.draw.line(SCREEN, (255, 165, 0), (BIRD_X, int(self.y)), (BIRD_X - 10, int(self.y) + wing_offset), 4)
        pygame.draw.polygon(SCREEN, (255, 165, 0), [
            (BIRD_X + self.radius, int(self.y)),
            (BIRD_X + self.radius + 8, int(self.y) - 4),
            (BIRD_X + self.radius + 8, int(self.y) + 4)
        ])

    @property
    def rect(self):
        return pygame.Rect(BIRD_X - self.radius, int(self.y - self.radius), self.radius * 2, self.radius * 2)

class Pipe:
    def __init__(self, speed):
        self.x = WIDTH
        self.height = random.randint(100, 400)
        self.width = 52
        self.speed = speed
        self.top = pygame.Rect(self.x, 0, self.width, self.height - PIPE_GAP // 2)
        self.bottom = pygame.Rect(self.x, self.height + PIPE_GAP // 2, self.width, HEIGHT)

    def update(self):
        self.top.x -= self.speed
        self.bottom.x -= self.speed

    def draw(self):
        pygame.draw.rect(SCREEN, PIPE_COLOR, self.top)
        pygame.draw.polygon(SCREEN, DARK_GREEN, [
            (self.top.x - 5, self.top.bottom - 10),
            (self.top.x + self.width + 5, self.top.bottom - 10),
            (self.top.x + self.width // 2, self.top.bottom + 10)
        ])
        pygame.draw.rect(SCREEN, PIPE_COLOR, self.bottom)
        pygame.draw.polygon(SCREEN, DARK_GREEN, [
            (self.bottom.x - 5, self.bottom.top + 10),
            (self.bottom.x + self.width + 5, self.bottom.top + 10),
            (self.bottom.x + self.width // 2, self.bottom.top - 10)
        ])

    def off_screen(self):
        return self.top.right < 0

    def collide(self, bird):
        return self.top.colliderect(bird.rect) or self.bottom.colliderect(bird.rect)

class Bonus:
    def __init__(self, pipe):
        self.x = pipe.top.x + pipe.width // 2
        self.y = (pipe.top.bottom + pipe.bottom.top) // 2
        self.radius = 8
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

    def update(self, speed):
        self.x -= speed
        self.rect.x = self.x - self.radius

    def draw(self):
        pygame.draw.circle(SCREEN, BONUS_COLOR, (self.x, self.y), self.radius)

    def collide(self, bird):
        return self.rect.colliderect(bird.rect)


def game_over_screen(score):
    high_score = load_high_score()
    if score > high_score:
        save_high_score(score)
        high_score = score
    while True:
        SCREEN.fill((0, 0, 0))
        msg = FONT.render(f"Game Over! Score: {score}", True, (255, 255, 255))
        high_msg = FONT.render(f"High Score: {high_score}", True, (255, 255, 255))
        restart_msg = FONT.render("Press R to Restart or Q to Quit", True, (255, 255, 255))
        SCREEN.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 60))
        SCREEN.blit(high_msg, (WIDTH // 2 - high_msg.get_width() // 2, HEIGHT // 2 - 20))
        SCREEN.blit(restart_msg, (WIDTH // 2 - restart_msg.get_width() // 2, HEIGHT // 2 + 20))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()


def load_high_score():
    if not os.path.isfile(HIGH_SCORE_FILE):
        return 0
    with open(HIGH_SCORE_FILE, 'r') as f:
        return int(f.read())

def save_high_score(score):
    with open(HIGH_SCORE_FILE, 'w') as f:
        f.write(str(score))


def main():
    bird = Bird()
    pipes = []
    bonuses = []
    score = 0
    last_pipe = pygame.time.get_ticks()
    cloud_offset = 0

    running = True
    while running:
        CLOCK.tick(60)
        SCREEN.fill(SKY_BLUE)


        pygame.draw.circle(SCREEN, SUN_COLOR, (WIDTH - 60, 60), 40)
        cloud_offset = (cloud_offset + 1) % WIDTH
        pygame.draw.circle(SCREEN, CLOUD_COLOR, ((80 + cloud_offset) % WIDTH, 100), 20)
        pygame.draw.circle(SCREEN, CLOUD_COLOR, ((100 + cloud_offset) % WIDTH, 90), 30)
        pygame.draw.circle(SCREEN, CLOUD_COLOR, ((130 + cloud_offset) % WIDTH, 100), 20)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                bird.flap()

        bird.update()

        now = pygame.time.get_ticks()
        pipe_speed = 3 + score // 10

        if now - last_pipe > PIPE_FREQ:
            new_pipe = Pipe(pipe_speed)
            pipes.append(new_pipe)
            if random.random() < 0.5:
                bonuses.append(Bonus(new_pipe))
            last_pipe = now

        for pipe in pipes[:]:
            pipe.update()
            if pipe.collide(bird):
                game_over_screen(score)
                return main()
            if pipe.top.centerx + pipe_speed < BIRD_X <= pipe.top.centerx + pipe_speed + 3:
                score += 1
            if pipe.off_screen():
                pipes.remove(pipe)
            pipe.draw()

        for bonus in bonuses[:]:
            bonus.update(pipe_speed)
            if bonus.collide(bird):
                score += 5
                bonuses.remove(bonus)
            elif bonus.x + bonus.radius < 0:
                bonuses.remove(bonus)
            bonus.draw()

        pygame.draw.rect(SCREEN, BASE_COLOR, pygame.Rect(0, BASE_Y, WIDTH, 100))

        bird.draw()

        score_surface = FONT.render(str(score), True, (255, 255, 255))
        SCREEN.blit(score_surface, (WIDTH//2 - score_surface.get_width()//2, 50))

        if bird.y > BASE_Y or bird.y < -50:
            game_over_screen(score)
            return main()

        pygame.display.update()

if __name__ == "__main__":
    main()
    pygame.quit()
