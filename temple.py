from ursina import *
import random
import os

app = Ursina()

# --- CONFIG ---
path_width = 6
segment_length = 12
initial_segments = 20
lanes = [-1, 0, 1]
obstacle_height = 4.5
blue_obstacle_height = 1.4  # Increased for reliable collisions
obstacles_every = 3
game_speed_base = 16
game_speed_max = 32
high_score_file = 'highscore.txt'

def get_stored_high_score():
    if os.path.exists(high_score_file):
        try:
            with open(high_score_file, 'r') as f:
                return int(f.read())
        except Exception:
            return 0
    return 0

def save_high_score(score):
    try:
        with open(high_score_file, 'w') as f:
            f.write(str(score))
    except Exception:
        pass

Sky()
window.color = color.rgb(110, 191, 255)
Entity(model='plane', scale=100, color=color.green.tint(.4), y=-2)

def path_pos_x(lane):
    return lane * path_width // 3

class PathSegment(Entity):
    def __init__(self, z):
        super().__init__(
            model='cube',
            scale=(path_width, 1.2, segment_length),
            color=color.rgb(120, 105, 95),
            position=(0, 0, z),
            texture='white_cube',
            texture_scale=(2, 5)
        )

# Only red and blue obstacles
obstacle_types = [
    {'color': color.red, 'height': obstacle_height, 'width': 1.2},
    {'color': color.violet, 'height': blue_obstacle_height, 'width': 1.5}
]

class Obstacle(Entity):
    def __init__(self, lane, z, typ):
        # Place bottom at y=0, top at y=height
        super().__init__(
            model='cube',
            color=typ['color'],
            scale=(typ['width'], typ['height'], 1.2),
            position=(path_pos_x(lane), typ['height'] / 2, z)  # CRITICAL: height/2 puts base on y=0
        )

class BallPlayer(Entity):
    def __init__(self):
        super().__init__(
            model='sphere', color=color.orange, scale=1.4, position=(0,2,2)
        )
        self.lane = 0
        self.jump_power = 13
        self.vertical_speed = 0
        self.grounded_y = self.y
        self.is_jumping = False
        self.rolling_angle = 0
        self.speed = game_speed_base

    def update(self):
        self.rolling_angle += 360 * self.speed * time.dt / (2.5 * math.pi)
        self.rotation_x = self.rolling_angle
        self.z += self.speed * time.dt
        target_x = path_pos_x(self.lane)
        self.x = lerp(self.x, target_x, 18 * time.dt)
        if self.is_jumping:
            self.vertical_speed -= 23 * time.dt
            self.y += self.vertical_speed * time.dt
            if self.y <= self.grounded_y:
                self.y = self.grounded_y
                self.is_jumping = False
                self.vertical_speed = 0

    def jump(self):
        if not self.is_jumping:
            self.vertical_speed = self.jump_power
            self.is_jumping = True

def megaman_explode(position, n=20):
    particles = []
    for _ in range(n):
        angle = random.uniform(0, 2 * pi)
        up = random.uniform(-.2, 1)
        spread = random.uniform(5, 16)
        velocity = Vec3(math.cos(angle), up, math.sin(angle)) * spread
        color_choice = color.orange if random.random() < 0.6 else color.yellow
        p = Entity(
            model='sphere',
            color=color_choice,
            scale=0.32 if random.random() < 0.5 else 0.19,
            position=position,
            add_to_scene_entities=False
        )
        p.direction = velocity
        p.life = random.uniform(0.65, 1.15)
        particles.append(p)
    def particle_update():
        dt = time.dt
        for p in particles[:]:
            if not p: continue
            p.life -= dt
            p.position += p.direction * dt
            p.direction *= 0.93
            p.scale *= 0.96
            if p.life < 0:
                destroy(p)
                particles.remove(p)
        if len(particles) == 0:
            destroy(SeqUpdater)
    SeqUpdater = invoke(particle_update, delay=0)
    SeqUpdater = Entity(update=particle_update)

score = 0
high_score = get_stored_high_score()
score_text = Text(
    text=f"Score: {score}   High Score: {high_score}",
    origin=(0,0), position=(-0.76,0.43),
    scale=2, color=color.white, background=True, background_color=color.rgba(0,0,0,120)
)
game_over = False
game_over_screen = None

path_segments = []
obstacles = []

for i in range(initial_segments):
    z = i * segment_length
    s = PathSegment(z)
    path_segments.append(s)
    if i > 1 and i % obstacles_every == 0:
        obs_count = 1 # Only 1 obstacle (winnable) until score 1000
        obs_lanes = random.sample(lanes, obs_count)
        for lane in obs_lanes:
            obs_type = random.choice(obstacle_types)
            obs = Obstacle(lane=lane, z=z+segment_length/2, typ=obs_type)
            obstacles.append(obs)

player = BallPlayer()
last_player_position = player.position

def update_camera():
    target_pos = player.position if not game_over else last_player_position
    camera.position = (target_pos.x, target_pos.y+10, target_pos.z-22)
    camera.look_at(target_pos+Vec3(0,2,5))

for _ in range(8):
    Entity(model='cube', color=color.azure.tint(-.12),
           scale=(random.uniform(20,50), 25, random.uniform(18,44)),
           position=(random.choice([-1,1]) * random.uniform(28,60), 12, random.uniform(100,480)),
           rotation_y=random.uniform(0,360))

def show_game_over_screen():
    global game_over_screen
    hs_string = ""
    if score == high_score:
        hs_string = "\n(New High Score!)"
    game_over_screen = Entity(
        parent=camera.ui,
        model='quad',
        scale=(1.05, 0.6),
        color=color.rgba(0,0,0,180),
        z=-10
    )
    Text(
        parent=game_over_screen,
        text=f'\nGAME OVER\n\nYour Score: {score}{hs_string}\nHigh Score: {high_score}\n\nPress [R] to Retry\n(Esc to quit)',
        origin=(0,0),
        position=(0, 0),
        scale=2.1,
        color=color.white,
        z=-11,
        align='center'
    )

def hide_game_over_screen():
    global game_over_screen
    if game_over_screen:
        destroy(game_over_screen)
        game_over_screen = None

def reset_game():
    global score, high_score, game_over, player, path_segments, obstacles, last_player_position
    hide_game_over_screen()
    score = 0
    path_segments = []
    obstacles = []
    for e in scene.entities[:]:
        if isinstance(e, (PathSegment, Obstacle)) or (hasattr(e, 'parent') and e.parent == None and isinstance(e, BallPlayer)):
            destroy(e)
    for i in range(initial_segments):
        z = i * segment_length
        s = PathSegment(z)
        path_segments.append(s)
        if i > 1 and i % obstacles_every == 0:
            obs_count = 1
            obs_lanes = random.sample(lanes, obs_count)
            for lane in obs_lanes:
                obs_type = random.choice(obstacle_types)
                obs = Obstacle(lane=lane, z=z+segment_length/2, typ=obs_type)
                obstacles.append(obs)
    player = BallPlayer()
    last_player_position = player.position
    game_over = False
    update_camera()
    score_text.text = f"Score: {score}   High Score: {high_score}"

def get_obstacle_count(score):
    if score < 5000:
        return 1
    else:
        return 2 if random.random() < 0.5 else 1

def update():
    global score, game_over, high_score, last_player_position, player
    if not game_over:
        player.update()
        last_player_position = player.position

    update_camera()

    if game_over:
        return

    factor = min(score / 60, 1)
    player.speed = lerp(game_speed_base, game_speed_max, factor)

    new_score = int(player.z // 2)
    if new_score > score:
        score = new_score
        score_text.text = f"Score: {score}   High Score: {high_score}"

    max_z = max(s.z for s in path_segments)
    while player.z + 80 > max_z:
        z = max_z + segment_length
        s = PathSegment(z)
        path_segments.append(s)

        obs_count = get_obstacle_count(score)
        obs_lanes = random.sample(lanes, obs_count)
        for lane in obs_lanes:
            obs_type = random.choice(obstacle_types)
            obs = Obstacle(lane=lane, z=z+segment_length/2, typ=obs_type)
            obstacles.append(obs)
        max_z = z

    for s in path_segments[:]:
        if s.z < player.z - 40:
            destroy(s)
            path_segments.remove(s)
    for o in obstacles[:]:
        if o.z < player.z - 28:
            destroy(o)
            obstacles.remove(o)

    # Precise collision: bottom of ball below top of obstacle
    for o in obstacles[:]:
        player_bottom = player.y - player.scale_y/2
        obstacle_top = o.y + o.scale_y/2
        if abs(player.x - o.x) < 1.3 and abs(player.z-o.z) < 1.2:
            if player_bottom < obstacle_top:
                megaman_explode(player.position, n=32)
                destroy(player)
                game_over = True
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
                show_game_over_screen()
                score_text.text = f"Score: {score}   High Score: {high_score}"
                break

def input(key):
    global game_over
    if key == 'escape':
        application.quit()
    if game_over:
        if key == 'r':
            reset_game()
        return
    if key in ('a', 'left arrow'):
        if player.lane > min(lanes):
            player.lane -= 1
    if key in ('d', 'right arrow'):
        if player.lane < max(lanes):
            player.lane += 1
    if key == 'space':
        player.jump()

app.run()
