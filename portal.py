import os
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random, math

app = Ursina()
window.title = "Ursina Portal Platformer"
window.borderless = False
editor_camera = EditorCamera(enabled=False)
total_worlds = 9
levels_per_world = 10
world = 1
level = 1
game_active = False

PLAYER_HEIGHT = 2
PLAYER_WIDTH = 0.7
base_platform_count = 10
platform_increase_rate = 3
BASE_MIN_GAP = Vec3(4.5, 2.0, 4.5)
BASE_MAX_GAP = Vec3(8, 4, 8)
GAP_INCREASE_WORLD = Vec3(2.1, 0.7, 2.1)
GAP_INCREASE_LEVEL = Vec3(1.1, 0.22, 1.1)
platform_scale = (12, 0.7, 12)
platforms = []
start_pos = Vec3(0, 2, 0)
sky = None
hazards = []

world_sky_textures = [
    'sky_sunset', 'sky_default', 'sky_sunset', 'shore', 'sky_default',
    'sky_sunset', 'shore', 'sky_default', 'sky_sunset'
]
world_sky_colors = [
    color.rgb(255,150,100), color.rgb(198,220,255), color.orange, color.rgb(80,160,255), color.gold,
    color.magenta, color.cyan, color.violet, color.lime
]
world_platform_textures = [
    'brick', 'white_cube', 'grass', 'shore', 'brick',
    'grass', 'white_cube', 'shore', 'brick'
]
world_platform_colors = [
    color.white, color.light_gray, color.lime, color.azure, color.red,
    color.pink, color.violet, color.cyan, color.yellow
]
world_weather_types = [
    'none',    # 1
    'rain',    # 2
    'none',    # 3
    'snow',    # 4
    'none',    # 5
    'rain',    # 6
    'snow',    # 7
    'rain',    # 8
    'none',    # 9
]
weather_particles = []
weather_type = 'none'

def spawn_weather_particles():
    global weather_particles
    for p in weather_particles: destroy(p)
    weather_particles = []
    if weather_type == 'none': return
    N = 60 if weather_type == 'rain' else 30
    area_size = 22
    min_y = 8
    max_y = 24
    colors = {'rain': color.color(210, .8, .6, .45), 'snow': color.white}
    model = 'cube' if weather_type == 'snow' else 'quad'
    scale = (0.09, 0.22, 0.08) if weather_type == 'rain' else (0.14, 0.14, 0.14)
    for i in range(N):
        px = random.uniform(-area_size, area_size)
        pz = random.uniform(-area_size, area_size)
        py = random.uniform(min_y, max_y)
        p = Entity(model=model, color=colors[weather_type], scale=scale, position=(px, py, pz), add_to_scene_entities=True)
        weather_particles.append(p)

def update_weather_particles():
    speed = 17 if weather_type == 'rain' else 5
    for p in weather_particles:
        p.y -= time.dt * speed * random.uniform(0.97,1.04)
        if weather_type == 'snow':
            p.x += math.sin(time.time()*2 + p.z)*0.015
        if p.y < 2:
            p.y = random.uniform(16, 25)
            p.x = random.uniform(-22, 22)
            p.z = random.uniform(-22, 22)

def set_world_theme():
    global sky, platform_texture_this_world, platform_color_this_world
    if sky is not None: destroy(sky)
    try: sky = Sky(texture=world_sky_textures[(world-1)%len(world_sky_textures)])
    except Exception: sky = Sky()
    platform_texture_this_world = world_platform_textures[(world-1)%len(world_platform_textures)]
    platform_color_this_world = world_platform_colors[(world-1)%len(world_platform_colors)]

def platform_gaps_for(world, level):
    min_gap = BASE_MIN_GAP + GAP_INCREASE_WORLD * (world-1) + GAP_INCREASE_LEVEL * (level-1)
    max_gap = BASE_MAX_GAP + GAP_INCREASE_WORLD * (world-1) * 1.35 + GAP_INCREASE_LEVEL * (level-1) * 1.2
    return min_gap, max_gap

def generate_platforms():
    global platforms
    pos = start_pos
    platforms.clear()
    prev_pos = pos
    cluster_length = 0
    platform_count = base_platform_count + platform_increase_rate * (world-1) + int((level-1)*platform_increase_rate/levels_per_world)
    min_gap, max_gap = platform_gaps_for(world, level)
    for i in range(platform_count):
        if i == 0:
            plat = Entity(model='cube', texture=platform_texture_this_world,
                color=platform_color_this_world if world > 1 else color.white,
                scale=platform_scale, position=pos, collider='box')
        elif i == platform_count-1:
            goal_scale = (platform_scale[0]*1.15, platform_scale[1], platform_scale[2]*1.1)
            pos = prev_pos + Vec3(random.uniform(4,10), random.uniform(2,5), random.uniform(4,12))
            plat = Entity(model='cube', color=color.gold, scale=goal_scale, position=pos, collider='box')
        else:
            if cluster_length > 0:
                dx = random.uniform(5, 8) * random.choice([1, -1]) * (1 + 0.10*world)
                dz = random.uniform(5, 8) * random.choice([1, -1]) * (1 + 0.10*world)
                dy = random.uniform(-1, 1) * 0.24 * (1 + 0.14*world)
                cluster_length -= 1
            else:
                dx = random.uniform(min_gap.x, max_gap.x) * random.choice([1, -1])
                dz = random.uniform(min_gap.z, max_gap.z) * random.choice([1, -1])
                dy = random.uniform(min_gap.y, max_gap.y) * random.choice([1, -1])
                cluster_length = random.randint(1, min(world+1, 3))
            plat = Entity(model='cube', texture=platform_texture_this_world,
                color=platform_color_this_world if world > 1 else color.white,
                scale=(platform_scale[0] * random.uniform(0.9,1.18),
                       platform_scale[1],
                       platform_scale[2] * random.uniform(0.8,1.12)),
                position=prev_pos + Vec3(dx, dy, dz), collider='box')
            pos = plat.position
        platforms.append(plat)
        prev_pos = plat.position

def generate_hazards():
    global hazards
    for h in hazards:
        destroy(h)
    hazards = []
    if world == 1:
        return
    hazard_count = min(3 + world + level//2, len(platforms)-2)
    used_indexes = set([0, len(platforms)-1])
    for i in range(hazard_count):
        while True:
            platform_index = random.randint(1, len(platforms)-2)
            if platform_index not in used_indexes:
                used_indexes.add(platform_index)
                break
        plat = platforms[platform_index]
        x = plat.x + random.uniform(-plat.scale_x/2 + 1, plat.scale_x/2 - 1)
        z = plat.z + random.uniform(-plat.scale_z/2 + 1, plat.scale_z/2 - 1)
        y = plat.y + plat.scale_y/2 + 0.5
        hazard_type = 'cube' if (world % 2 == 0) else 'sphere'
        hazard_color = color.red if hazard_type=='cube' else color.violet
        hazard = Entity(
            model=hazard_type,
            color=hazard_color,
            scale=(1,1,1),
            position=(x,y,z),
            collider='box',
            texture=None,
            rotation=Vec3(
                random.uniform(0,360),
                random.uniform(0,360),
                random.uniform(0,360)
            ) if hazard_type=='cube' else Vec3(0,0,0)
        )
        hazards.append(hazard)

def check_hazard_collision():
    for h in hazards:
        if distance(h.world_position, player.world_position) < 0.9:
            player.world_position = player_start_pos()
            if hasattr(player, 'velocity'):
                player.velocity = Vec3(0,0,0)
            return

def player_start_pos():
    return start_pos + Vec3(0, PLAYER_HEIGHT/2+1, 0)

player = FirstPersonController(
    y=player_start_pos().y,
    origin_y=-.5,
    speed=7,
    collider='box',
    jump_height=2.8
)
player.gravity = 1.4
RUN_SPEED = 12
WALK_SPEED = 7
player.can_double_jump = True

def create_oval_portal(color_):
    return Entity(
        model='quad',
        color=color_,
        enabled=False,
        collider='box',
        scale=(1.7, 3.1, 0.13),    # OVAL
        texture='circle',          # built-in alpha circle
        double_sided=True
    )
blue_portal = create_oval_portal(color.azure)
red_portal = create_oval_portal(color.red)

# ---- Swirl overlays for animated energy (Option 1) ----
blue_swirl = Entity(
    model='quad', parent=blue_portal, position=Vec3(0,0,0.01), scale=(1.0,1.0,1.0),
    texture='circle', # replace with "swirl.png" or "magic_circle.png" for max style
    color=color.white33, double_sided=True, visible=False
)
red_swirl = Entity(
    model='quad', parent=red_portal, position=Vec3(0,0,0.01), scale=(1.0,1.0,1.0),
    texture='circle', color=color.white33, double_sided=True, visible=False
)

crosshair = Entity(
    parent=camera.ui, model='quad', color=color.white, texture='circle', scale=0.035, position=(0,0,0)
)
crosshair.visible = False
portal_gun = Entity(
    parent=camera.ui, model='cube', color=color.light_gray, scale=(0.11, 0.30, 0.13),
    position=(0.19, -0.18, 0.1), rotation=(10,-20,15), texture=None
)
portal_gun.visible = False

def get_yaw_from_forward_vector(forward):
    angle = math.atan2(forward.x, forward.z)
    return math.degrees(angle)

can_shoot_blue = True
can_shoot_red = True

def place_portal(which):
    ignore=[player]
    start = camera.world_position
    hit = raycast(start, camera.forward, distance=50, ignore=ignore, traverse_target=scene)
    if hit.hit and hit.entity in platforms:
        portal = blue_portal if which == 'blue' else red_portal
        normal = hit.world_normal
        portal.position = hit.world_point + normal * 0.06
        if abs(normal.y) > 0.95:
            up_dir = camera.right
        else:
            up_dir = Vec3(0,1,0)
        portal.look_at(hit.world_point - normal, up=up_dir)
        portal.portal_forward = -normal
        portal.enabled = True
        portal.scale_z = 0.01
        portal.animate_scale_z(0.13, duration=.11, curve=curve.out_back)
        portal.placing = False

def aim_highlight():
    hit = raycast(camera.world_position, camera.forward, distance=50, ignore=[player], traverse_target=scene)
    crosshair.color = color.azure if (hit.hit and hit.entity in platforms) else color.white

# === Option 5: Fake "crystal ball" preview effect ===
def fake_portal_preview(portal):
    # Take screenshot, load as texture and overlay on the portal for a 'preview' effect
    filename = f'portal_preview_temp_{random.randint(0,999999)}.png'
    application.screenshot(name=filename)
    def show_preview():
        tex = load_texture(filename)
        preview = Entity(
            parent=portal,
            model='quad',
            position=Vec3(0,0,0.03),
            origin=(0,0),
            scale=(0.95, 0.95, 1),
            texture=tex,
            color=color.white,
            double_sided=True
        )
        preview.alpha = 0.7
        def _fade_out():
            preview.animate('alpha', 0, duration=0.8)
            invoke(destroy, preview, delay=1.0)
        invoke(_fade_out, delay=1.1)
        # Destroy texture file later (optional cleanup)
        invoke(lambda: os.remove(filename) if os.path.exists(filename) else None, delay=2)
    # Give the engine a moment to generate the screenshot
    invoke(show_preview, delay=0.1)


def input(key):
    global can_shoot_blue, can_shoot_red, level, world, game_active
    if not game_active:
        return
    if key == 'space' or key == 'up arrow':
        if player.grounded:
            player.can_double_jump = True
            player.jump()
        elif player.can_double_jump:
            player.can_double_jump = False
            player.jump()
    if key == 'left mouse down':
        if can_shoot_blue: place_portal('blue')
        can_shoot_blue = False
    if key == 'left mouse up':
        can_shoot_blue = True
    if key == 'right mouse down':
        if can_shoot_red: place_portal('red')
        can_shoot_red = False
    if key == 'right mouse up':
        can_shoot_red = True
    if key == 'r':
        reset_level(world, level)
    if key == 'tab':
        editor_camera.enabled = not editor_camera.enabled
        player.enabled = not editor_camera.enabled
        mouse.locked = not editor_camera.enabled
    # Option 5: crystal ball snapshot effect
    if key == 'g' and blue_portal.enabled:
        fake_portal_preview(blue_portal)
    if key == 'h' and red_portal.enabled:
        fake_portal_preview(red_portal)

Entity(ignore_paused=True, input=input)

def portal_transition(start_pos, end_pos, end_forward, duration=0.19):
    overlay = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2,2), alpha=0)
    def fade_in(): overlay.animate('alpha', 1, duration/2, curve=curve.linear)
    def fade_out(): overlay.animate('alpha', 0, duration/2, curve=curve.linear)
    def move_player():
        player.world_position = end_pos
        yaw = get_yaw_from_forward_vector(end_forward)
        player.rotation_y = yaw
    s = Sequence(
        Func(fade_in), Wait(duration/2),
        Func(move_player),
        Func(fade_out), Wait(duration/2),
        Func(overlay.disable)
    )
    s.start()

recent_tp_flag = {'active': False}
def check_portal_tp():
    if not game_active:
        return
    if recent_tp_flag['active']:
        return
    for src, dst in [(blue_portal, red_portal), (red_portal, blue_portal)]:
        if not src.enabled or not dst.enabled:
            continue
        min_corner = src.world_position - Vec3(src.scale_x/2, src.scale_y/2, 0.35)
        max_corner = src.world_position + Vec3(src.scale_x/2, src.scale_y/2, 0.35)
        if (
            min_corner.x < player.x < max_corner.x and
            min_corner.y < player.y < max_corner.y and
            min_corner.z < player.z < max_corner.z
        ):
            tp_offset = dst.portal_forward * (PLAYER_WIDTH/2 + 0.21)
            new_pos = dst.world_position + tp_offset
            if hasattr(player, 'velocity'):
                player.velocity = dst.portal_forward * player.speed
            portal_transition(player.world_position, new_pos, dst.portal_forward)
            recent_tp_flag['active'] = True
            invoke(lambda: recent_tp_flag.update({'active': False}), delay=0.5)
            break

def reset_level(w, l):
    global level, world, weather_type
    for p in platforms:
        destroy(p)
    set_world_theme()
    world_index = (w-1) % len(world_weather_types)
    weather_type = world_weather_types[world_index]
    spawn_weather_particles()
    generate_platforms()
    generate_hazards()
    player.world_position = player_start_pos()
    if hasattr(player, 'velocity'):
        player.velocity = Vec3(0,0,0)
    blue_portal.enabled = False
    red_portal.enabled = False
    world = w
    level = l

def celebrate():
    print_on_screen(f"Congratulations!\nYou completed all {total_worlds} worlds!", scale=2, duration=5)
    application.pause()

def next_level():
    global level, world
    level += 1
    if level > levels_per_world:
        level = 1
        world += 1
        if world > total_worlds:
            celebrate()
            return
    reset_level(world, level)

def update():
    if not game_active:
        return
    if held_keys['shift']:
        player.speed = RUN_SPEED
    else:
        player.speed = WALK_SPEED
    if player.grounded:
        player.can_double_jump = True
    check_portal_tp()
    aim_highlight()
    # --- Option 1 (swirl and pulse energy for portals)
    t = time.time()
    for portal, swirl, base_color in [
        (blue_portal, blue_swirl, color.azure),
        (red_portal, red_swirl, color.red)
    ]:
        swirl.visible = portal.enabled  # Show only if portal is active
        if portal.enabled:
            portal.color = lerp(base_color, color.white, (math.sin(t*2)+1)*0.12)
            swirl.rotation_z += time.dt * 90
            swirl.alpha = 0.66 + 0.34*math.sin(t*3.1)
    for h in hazards:
        h.rotation_y += time.dt * 80
        c = (math.sin(time.time()*h.x + h.z)+1)/2
        h.color = color.rgb(200 + int(55*c), 30+int(100*(1-c)), 35+int(50*c))
    if weather_type != 'none':
        update_weather_particles()
    if player.y < -15:
        player.world_position = player_start_pos()
    if distance(player.world_position, platforms[-1].world_position) < 2:
        if world < total_worlds or level < levels_per_world:
            print_on_screen(f"World {world}, Level {level} complete!\nPress N for next.", scale=2, duration=1.2)
        else:
            print_on_screen(f"Victory!\nPress N.", scale=2, duration=1.2)
        if held_keys['n']:
            next_level()

menu_entities = []
current_menu = {'active': True}
def world_menu():
    global menu_entities, game_active
    title = Text("PORTAL PLATFORMER\nChoose a World", parent=camera.ui, origin=(0,0), position=(0,0.38), scale=2, z=2)
    menu_entities.append(title)
    grid_size = 3
    spacing = 0.23
    rect_size = (0.19, 0.19)
    for w in range(1, total_worlds+1):
        col = (w-1) % grid_size
        row = (w-1) // grid_size
        x = (col - 1) * spacing
        y = 0.11 - row * spacing

        group = Entity(parent=camera.ui, position=(x,y,0), z=2)
        btn = Button(
            parent=group,
            scale=rect_size,
            text='',
            color=color.rgba(30,50,80,160),
            highlight_color=color.azure,
            pressed_color=color.cyan,
            z=0
        )
        sky_half = Entity(parent=group,
            model='quad',
            color=world_sky_colors[w-1],
            scale=(rect_size[0]*0.96, rect_size[1]*0.51),
            y=rect_size[1]/4,
            z=-0.01
        )
        plat_half = Entity(parent=group,
            model='quad',
            color=world_platform_colors[w-1],
            texture=world_platform_textures[w-1],
            scale=(rect_size[0]*0.96, rect_size[1]*0.51),
            y=-rect_size[1]/4,
            z=-0.01
        )
        num = Text(str(w), parent=group, y=0, z=0.03, scale=2, color=color.black, origin=(0,0))
        menu_entities += [group, btn, sky_half, plat_half, num]
        def make_on_click(selected_world):
            def on_click():
                start_game(selected_world)
            return on_click
        btn.on_click = make_on_click(w)
    current_menu['active'] = True

def menu_input(key):
    if not current_menu['active']:
        return
    if key in [str(i) for i in range(1, total_worlds+1)]:
        start_game(int(key))

def start_game(selected_world):
    global world, level, menu_entities, game_active, weather_type
    world = selected_world
    level = 1
    for e in menu_entities:
        destroy(e)
    menu_entities.clear()
    game_active = True
    current_menu['active'] = False
    crosshair.visible = True
    portal_gun.visible = True
    set_world_theme()
    world_index = (selected_world-1) % len(world_weather_types)
    weather_type = world_weather_types[world_index]
    spawn_weather_particles()
    generate_platforms()
    generate_hazards()
    player.world_position = player_start_pos()
    if hasattr(player, 'velocity'):
        player.velocity = Vec3(0,0,0)
    blue_portal.enabled = False
    red_portal.enabled = False

game_active = False
world_menu()

def global_input(key):
    if not game_active:
        menu_input(key)
Entity(ignore_paused=True, input=global_input)

app.run()
