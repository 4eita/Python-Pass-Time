import pygame
import sys
import math
import random
from pygame.locals import *
from pygame.math import Vector3
from pygame import gfxdraw

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FOV = 70
PLAYER_HEIGHT = 1.5
CAMERA_DISTANCE = 6.0
CAMERA_HEIGHT = 4.0
CAMERA_SMOOTHNESS = 0.08
MIN_VELOCITY_FOR_CAMERA_OFFSET = 0.1
BALL_ROTATION_SPEED = 12.0
JUMP_POWER = 6.5
MOVEMENT_FORCE = 15.0
FRICTION = 0.92

# Color clamping function to ensure valid values
def clamp_color(color):
    if len(color) == 3:  # RGB
        return (
            max(0, min(255, color[0])),
            max(0, min(255, color[1])),
            max(0, min(255, color[2]))
        )
    elif len(color) == 4:  # RGBA
        return (
            max(0, min(255, color[0])),
            max(0, min(255, color[1])),
            max(0, min(255, color[2])),
            max(0, min(255, color[3]))
        )
    return color

# Colors with clamping
COLORS = {
    'sky': clamp_color((135, 206, 250)),
    'sky_gradient': clamp_color((70, 130, 180)),
    'ground': clamp_color((120, 120, 120)),
    'grass': clamp_color((50, 205, 50)),
    'ball': clamp_color((220, 60, 60)),
    'banana': clamp_color((255, 225, 25)),
    'banana_dark': clamp_color((200, 160, 20)),
    'hazard': clamp_color((255, 50, 50)),
    'hazard_glow': clamp_color((255, 150, 150)),
    'text': clamp_color((255, 255, 255)),
    'platform': clamp_color((220, 220, 220)),
    'wall': clamp_color((180, 180, 180)),
    'shadow': clamp_color((0, 0, 0, 100))
}

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Super Monkey Ball')
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)

# Helper function to create gradient surfaces
def create_gradient_surface(width, height, top_color, bottom_color):
    surf = pygame.Surface((width, height))
    for y in range(height):
        ratio = y / height
        color = (
            int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio),
            int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio),
            int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        )
        pygame.draw.line(surf, color, (0, y), (width, y))
    return surf

# Create graphics assets
def create_banana_surface(size):
    surf = pygame.Surface((size*2, size), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, COLORS['banana_dark'], (0, 0, size*2, size))
    pygame.draw.ellipse(surf, COLORS['banana'], (2, 2, size*2-4, size-4))
    return surf

def create_hazard_surface(size):
    surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
    pygame.draw.circle(surf, COLORS['hazard_glow'], (size, size), size)
    pygame.draw.circle(surf, COLORS['hazard'], (size, size), size-3)
    return surf

class Camera:
    def __init__(self, position, target):
        self.position = Vector3(position)
        self.target = Vector3(target)
        self.up = Vector3(0, 1, 0)
        self.fov = FOV
        self.aspect_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        self.last_valid_direction = Vector3(0, 0, -1)
        self.shake_time = 0
        self.shake_intensity = 0
        
    def project_point(self, point):
        """Project a 3D point to 2D screen coordinates"""
        # Apply camera shake if active
        if self.shake_time > 0:
            shake_offset = Vector3(
                random.uniform(-1, 1) * self.shake_intensity,
                random.uniform(-1, 1) * self.shake_intensity,
                0
            )
            point = Vector3(point) + shake_offset
        else:
            point = Vector3(point)
            
        # Convert to camera space
        forward = (self.target - self.position)
        if forward.length_squared() > 0:
            forward = forward.normalize()
        else:
            forward = Vector3(0, 0, 1)
            
        right = self.up.cross(forward)
        if right.length_squared() > 0:
            right = right.normalize()
        up = forward.cross(right)
        
        # Camera space coordinates
        point_vec = point - self.position
        camera_x = point_vec.dot(right)
        camera_y = point_vec.dot(up)
        camera_z = point_vec.dot(forward)
        
        if camera_z <= 0:  # Behind camera
            return None
        
        # Perspective projection
        f = 1 / math.tan(math.radians(self.fov / 2))
        sx = (camera_x * f / self.aspect_ratio) / camera_z
        sy = (camera_y * f) / camera_z
        
        # Convert to screen coordinates
        screen_x = (sx + 1) * 0.5 * SCREEN_WIDTH
        screen_y = (1 - sy) * 0.5 * SCREEN_HEIGHT
        
        return (screen_x, screen_y, camera_z)
    
    def update(self, target_position, ball_velocity, dt):
        """Update camera to follow the ball"""
        # Calculate movement direction
        movement_direction = Vector3(ball_velocity.x, 0, ball_velocity.z)
        
        # Only update last valid direction if we have significant movement
        if movement_direction.length() > MIN_VELOCITY_FOR_CAMERA_OFFSET:
            self.last_valid_direction = movement_direction.normalize()
        
        # Calculate target offset using last valid direction
        target_offset = self.last_valid_direction * -CAMERA_DISTANCE
        target_offset.y = CAMERA_HEIGHT
        
        ideal_position = Vector3(target_position) + target_offset
        
        # Smooth camera movement
        self.position += (ideal_position - self.position) * CAMERA_SMOOTHNESS
        self.target = Vector3(target_position)
        
        # Update camera shake
        if self.shake_time > 0:
            self.shake_time -= dt
            self.shake_intensity = self.shake_time * 0.5
    
    def apply_shake(self, duration=0.5):
        self.shake_time = duration
        self.shake_intensity = 0.3

class Ball:
    def __init__(self, position):
        self.position = Vector3(position)
        self.velocity = Vector3(0, 0, 0)
        self.radius = 0.5
        self.rotation = Vector3(0, 0, 0)
        self.score = 0
        self.lives = 3
        self.on_ground = True
        self.jump_power = JUMP_POWER
        self.invincible_time = 0
        self.last_ground_position = Vector3(position)
    
    def update(self, dt, platforms):
        # Apply gravity
        if not self.on_ground:
            self.velocity.y -= 9.8 * dt
        
        # Apply friction when on ground
        if self.on_ground:
            self.velocity.x *= FRICTION
            self.velocity.z *= FRICTION
        
        # Update position
        self.position += self.velocity * dt
        
        # Check platform collisions
        landed = False
        for platform in platforms:
            if (platform.is_point_on_top(self.position) and 
                self.position.y - self.radius <= platform.position.y + 0.1):
                self.position.y = platform.position.y + self.radius
                self.velocity.y = max(0, self.velocity.y)
                landed = True
                self.last_ground_position = Vector3(self.position)

        self.on_ground = landed  # Set after checking all platforms
                
        # Check if fell off
        if self.position.y < -5:
            self.lives -= 1
            if self.lives > 0:
                self.reset_position()
        
        # Update rotation based on velocity
        if self.on_ground and self.velocity.length() > 0.1:
            self.rotation.x += self.velocity.z * dt * BALL_ROTATION_SPEED
            self.rotation.z -= self.velocity.x * dt * BALL_ROTATION_SPEED
        
        # Update invincibility timer
        if self.invincible_time > 0:
            self.invincible_time -= dt
    
    def reset_position(self):
        self.position = Vector3(self.last_ground_position)
        self.velocity = Vector3(0, 0, 0)
        self.on_ground = True
        self.invincible_time = 1.0
    
    def draw(self, surface, camera):
        # Project ball position
        ball_screen_pos = camera.project_point(self.position)
        if not ball_screen_pos:
            return
        
        # Calculate apparent size based on distance
        screen_x, screen_y, distance = ball_screen_pos
        apparent_radius = int(self.radius * SCREEN_HEIGHT * 0.5 / distance)
        
        if apparent_radius <= 0:
            return
        
        # Draw shadow
        shadow_pos = camera.project_point(Vector3(self.position.x, 0, self.position.z))
        if shadow_pos:
            shadow_size = max(5, apparent_radius * 1.5)
            shadow_alpha = min(150, 100 + int(50 * (1 - min(1, self.position.y / 5))))
            shadow_color = (*COLORS['shadow'][:3], shadow_alpha)
            shadow_color = clamp_color(shadow_color)
            
            shadow_surf = pygame.Surface((shadow_size*2, shadow_size*2), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surf, shadow_color, (shadow_size, shadow_size), shadow_size)
            surface.blit(shadow_surf, (int(shadow_pos[0] - shadow_size), 
                          int(shadow_pos[1] - shadow_size)))
        
        # Draw ball with gradient
        for i in range(apparent_radius, 0, -2):
            alpha = 255 - int(100 * (1 - i/apparent_radius))
            color = (
                min(255, COLORS['ball'][0] + 30 * (1 - i/apparent_radius)),
                min(255, COLORS['ball'][1] + 30 * (1 - i/apparent_radius)),
                min(255, COLORS['ball'][2] + 30 * (1 - i/apparent_radius))
            )
            color = clamp_color(color)
            
            if self.invincible_time > 0 and int(pygame.time.get_ticks() / 100) % 2 == 0:
                color = (*color[:3], alpha) if len(color) == 3 else color
            else:
                color = color[:3]  # Ensure we don't pass alpha if not needed
            
            pygame.gfxdraw.filled_circle(surface, int(screen_x), int(screen_y), i, color)
        
        # Draw monkey face
        face_angle = math.atan2(self.velocity.z, self.velocity.x) if self.velocity.length() > 0.1 else 0
        face_x = screen_x + math.cos(face_angle) * apparent_radius * 0.6
        face_y = screen_y + math.sin(face_angle) * apparent_radius * 0.6
        face_radius = apparent_radius // 3
        
        # Face outline
        face_color = clamp_color((255, 240, 220))
        outline_color = clamp_color((200, 180, 150))
        pygame.gfxdraw.filled_circle(surface, int(face_x), int(face_y), face_radius, face_color)
        pygame.gfxdraw.aacircle(surface, int(face_x), int(face_y), face_radius, outline_color)
        
        # Eyes
        eye_offset = face_radius // 2
        eye_radius = face_radius // 3
        pygame.gfxdraw.filled_circle(surface, int(face_x - eye_offset), int(face_y - eye_offset//2), 
                                    eye_radius, (255, 255, 255))
        pygame.gfxdraw.filled_circle(surface, int(face_x + eye_offset), int(face_y - eye_offset//2), 
                                    eye_radius, (255, 255, 255))
        
        # Pupils
        pupil_radius = eye_radius // 2
        pygame.gfxdraw.filled_circle(surface, int(face_x - eye_offset), int(face_y - eye_offset//2), 
                                    pupil_radius, (0, 0, 0))
        pygame.gfxdraw.filled_circle(surface, int(face_x + eye_offset), int(face_y - eye_offset//2), 
                                    pupil_radius, (0, 0, 0))
        
        # Mouth
        mouth_rect = (face_x - eye_offset, face_y + eye_offset//2, eye_offset*2, eye_radius)
        pygame.gfxdraw.arc(surface, int(face_x), int(face_y + eye_offset//2), eye_offset, 
                          0, 180, (0, 0, 0))

class Platform:
    def __init__(self, position, size, color, has_banana=False, is_hazard=False):
        self.position = Vector3(position)
        self.size = size
        self.color = clamp_color(color)
        self.has_banana = has_banana
        self.is_hazard = is_hazard
        self.banana_surf = create_banana_surface(20)
        self.hazard_surf = create_hazard_surface(15)
    
    def is_point_on_top(self, point):
        half_size = self.size / 2
        return (abs(point.x - self.position.x) <= half_size and 
                abs(point.z - self.position.z) <= half_size and
                point.y >= self.position.y)
    
    def draw(self, surface, camera):
        # Define platform corners
        half_size = self.size / 2
        corners = [
            Vector3(self.position.x - half_size, self.position.y, self.position.z - half_size),
            Vector3(self.position.x + half_size, self.position.y, self.position.z - half_size),
            Vector3(self.position.x + half_size, self.position.y, self.position.z + half_size),
            Vector3(self.position.x - half_size, self.position.y, self.position.z + half_size)
        ]
        
        # Project corners
        projected = []
        for corner in corners:
            proj = camera.project_point(corner)
            if proj:
                projected.append((proj[0], proj[1]))
        
        # Draw platform if at least 3 corners are visible
        if len(projected) >= 3:
            # Calculate center point
            center_x = sum(p[0] for p in projected) / len(projected)
            center_y = sum(p[1] for p in projected) / len(projected)
            
            # Draw each triangle with gradient
            for i, (x, y) in enumerate(projected):
                next_i = (i + 1) % len(projected)
                
                # Calculate gradient color
                dist_to_center = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                max_dist = math.sqrt((projected[0][0] - center_x)**2 + (projected[0][1] - center_y)**2)
                color_factor = 0.8 + 0.2 * (1 - dist_to_center/max_dist)
                shaded_color = (
                    int(self.color[0] * color_factor),
                    int(self.color[1] * color_factor),
                    int(self.color[2] * color_factor)
                )
                shaded_color = clamp_color(shaded_color)
                
                pygame.draw.polygon(surface, shaded_color, [(x, y), projected[next_i], (center_x, center_y)])
            
            # Draw platform outline
            outline_color = clamp_color((self.color[0]//2, self.color[1]//2, self.color[2]//2))
            pygame.draw.polygon(surface, outline_color, projected, 2)
            
            # Draw banana if present
            if self.has_banana:
                banana_pos = Vector3(self.position.x, self.position.y + 0.2, self.position.z)
                banana_proj = camera.project_point(banana_pos)
                if banana_proj:
                    banana_size = max(10, int(40 / banana_proj[2]))
                    scaled_banana = pygame.transform.scale(
                        self.banana_surf, 
                        (banana_size*2, banana_size)
                    )
                    angle = math.sin(pygame.time.get_ticks() * 0.003) * 10
                    rotated_banana = pygame.transform.rotate(scaled_banana, angle)
                    surface.blit(
                        rotated_banana, 
                        (banana_proj[0] - rotated_banana.get_width()//2, 
                         banana_proj[1] - rotated_banana.get_height()//2)
                    )
            
            # Draw hazard if present
            if self.is_hazard:
                hazard_pos = Vector3(self.position.x, self.position.y + 0.1, self.position.z)
                hazard_proj = camera.project_point(hazard_pos)
                if hazard_proj:
                    hazard_size = max(15, int(30 / hazard_proj[2]))
                    pulse = 1 + 0.1 * math.sin(pygame.time.get_ticks() * 0.005)
                    scaled_hazard = pygame.transform.scale(
                        self.hazard_surf, 
                        (int(hazard_size*2 * pulse), int(hazard_size*2 * pulse))
                    )
                    surface.blit(
                        scaled_hazard, 
                        (hazard_proj[0] - scaled_hazard.get_width()//2, 
                         hazard_proj[1] - scaled_hazard.get_height()//2)
                    )

class Wall:
    def __init__(self, position, size, height, color):
        self.position = Vector3(position)
        self.size = size
        self.height = height
        self.color = clamp_color(color)
    
    def draw(self, surface, camera):
        half_size = self.size / 2
        
        # Define wall corners
        bottom_corners = [
            Vector3(self.position.x - half_size, self.position.y, self.position.z - half_size),
            Vector3(self.position.x + half_size, self.position.y, self.position.z - half_size),
            Vector3(self.position.x + half_size, self.position.y, self.position.z + half_size),
            Vector3(self.position.x - half_size, self.position.y, self.position.z + half_size)
        ]
        
        top_corners = [
            Vector3(self.position.x - half_size, self.position.y + self.height, self.position.z - half_size),
            Vector3(self.position.x + half_size, self.position.y + self.height, self.position.z - half_size),
            Vector3(self.position.x + half_size, self.position.y + self.height, self.position.z + half_size),
            Vector3(self.position.x - half_size, self.position.y + self.height, self.position.z + half_size)
        ]
        
        # Project all corners
        projected_bottom = []
        projected_top = []
        
        for i in range(4):
            proj_bottom = camera.project_point(bottom_corners[i])
            proj_top = camera.project_point(top_corners[i])
            
            if proj_bottom and proj_top:
                projected_bottom.append((proj_bottom[0], proj_bottom[1]))
                projected_top.append((proj_top[0], proj_top[1]))
        
        # Draw walls if visible
        if len(projected_bottom) >= 3 and len(projected_top) >= 3:
            # Draw sides with gradient
            for i in range(len(projected_bottom)):
                next_i = (i + 1) % len(projected_bottom)
                
                bottom_color = clamp_color((
                    int(self.color[0] * 0.7),
                    int(self.color[1] * 0.7),
                    int(self.color[2] * 0.7)
                ))
                top_color = clamp_color((
                    int(self.color[0] * 0.9),
                    int(self.color[1] * 0.9),
                    int(self.color[2] * 0.9)
                ))
                
                pygame.draw.polygon(surface, bottom_color, 
                                  [projected_bottom[i], projected_bottom[next_i], 
                                   projected_top[next_i]])
                pygame.draw.polygon(surface, top_color, 
                                  [projected_bottom[i], projected_top[next_i], 
                                   projected_top[i]])
            
            # Draw top with highlight
            highlight_color = clamp_color((
                min(255, self.color[0] + 30),
                min(255, self.color[1] + 30),
                min(255, self.color[2] + 30)
            ))
            outline_color = clamp_color((
                self.color[0]//2, 
                self.color[1]//2, 
                self.color[2]//2
            ))
            
            pygame.draw.polygon(surface, highlight_color, projected_top)
            pygame.draw.polygon(surface, outline_color, projected_top, 2)

class Game:
    def __init__(self):
        self.ball = Ball(Vector3(0, PLAYER_HEIGHT, 0))
        self.camera = Camera(Vector3(0, CAMERA_HEIGHT, -CAMERA_DISTANCE), self.ball.position)
        self.platforms = []
        self.walls = []
        self.game_over = False
        self.win = False
        self.level = 1
        self.generate_level()
        self.background_offset = 0
        self.particles = []
        self.background = create_gradient_surface(
            SCREEN_WIDTH, SCREEN_HEIGHT, 
            COLORS['sky'], COLORS['sky_gradient']
        )
    
    def generate_level(self):
        # Clear existing level
        self.platforms = []
        self.walls = []
        
        # Create central platform
        self.platforms.append(Platform(Vector3(0, 0, 0), 6.0, COLORS['grass']))
        
        # Create surrounding platforms
        platform_count = 8 + self.level * 2
        max_distance = 8 + self.level * 2
        floating_count = 3 + self.level
        
        for i in range(platform_count):
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(4, max_distance)
            x = math.cos(angle) * distance
            z = math.sin(angle) * distance
            height = random.uniform(-2, 2)
            
            platform = Platform(
                Vector3(x, height, z),
                random.uniform(2.5, 4.5),
                COLORS['grass'],
                has_banana=random.random() < 0.8,
                is_hazard=random.random() < 0.1 + 0.02 * self.level
            )
            self.platforms.append(platform)
            
            # Add walls to some platforms
            if random.random() < 0.3 + 0.05 * self.level:
                self.walls.append(Wall(
                    Vector3(x, height, z),
                    platform.size,
                    random.uniform(0.3, 1.0),
                    COLORS['wall']
                ))
        
        # Add floating platforms
        for i in range(floating_count):
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(6, max_distance + 4)
            x = math.cos(angle) * distance
            z = math.sin(angle) * distance
            height = random.uniform(3, 5 + self.level * 0.5)
            
            self.platforms.append(Platform(
                Vector3(x, height, z),
                random.uniform(1.5, 3.0),
                COLORS['platform'],
                has_banana=True,
                is_hazard=random.random() < 0.15 + 0.03 * self.level
            ))
    
    def update(self, dt):
        if self.game_over or self.win:
            return
        
        # Update ball
        self.ball.update(dt, self.platforms)
        
        # Update camera
        self.camera.update(self.ball.position, self.ball.velocity, dt)
        
        # Update background parallax
        self.background_offset += self.ball.velocity.x * dt * 0.1
        
        # Update particles
        self.particles = [p for p in self.particles if p['life'] > 0]
        for p in self.particles:
            p['position'] += p['velocity'] * dt
            p['life'] -= dt
        
        # Check for banana collection
        for platform in self.platforms:
            if (platform.has_banana and 
                platform.is_point_on_top(self.ball.position) and 
                self.ball.position.y - self.ball.radius <= platform.position.y + 0.2):
                platform.has_banana = False
                self.ball.score += 10
                
                # Create collection particles
                for _ in range(10):
                    self.particles.append({
                        'position': Vector3(self.ball.position),
                        'velocity': Vector3(
                            random.uniform(-1, 1),
                            random.uniform(0, 1),
                            random.uniform(-1, 1)
                        ) * 2,
                        'color': COLORS['banana'],
                        'size': random.uniform(2, 5),
                        'life': random.uniform(0.5, 1.0)
                    })
        
        # Check for hazards
        if self.ball.invincible_time <= 0:
            for platform in self.platforms:
                if (platform.is_hazard and 
                    platform.is_point_on_top(self.ball.position) and 
                    self.ball.position.y - self.ball.radius <= platform.position.y + 0.2):
                    self.ball.lives -= 1
                    self.camera.apply_shake()
                    self.ball.reset_position()
                    
                    # Create explosion particles
                    for _ in range(20):
                        self.particles.append({
                            'position': Vector3(self.ball.position),
                            'velocity': Vector3(
                                random.uniform(-3, 3),
                                random.uniform(-1, 3),
                                random.uniform(-3, 3)
                            ),
                            'color': COLORS['hazard'],
                            'size': random.uniform(3, 8),
                            'life': random.uniform(0.7, 1.2)
                        })
                    break
        
        # Check win condition
        bananas_left = sum(1 for platform in self.platforms if platform.has_banana)
        if bananas_left == 0:
            self.win = True
            self.level += 1
            
            # Create celebration particles
            for _ in range(50):
                self.particles.append({
                    'position': Vector3(self.ball.position),
                    'velocity': Vector3(
                        random.uniform(-5, 5),
                        random.uniform(-5, 5),
                        random.uniform(-5, 5)
                    ),
                    'color': random.choice([COLORS['banana'], COLORS['ball'], (255, 255, 255)]),
                    'size': random.uniform(3, 7),
                    'life': random.uniform(1.0, 2.0)
                })
        
        # Check game over
        if self.ball.lives <= 0:
            self.game_over = True
    
    def draw_background(self, surface):
        # Draw pre-rendered gradient background
        surface.blit(self.background, (0, 0))
        
        # Draw distant mountains (parallax effect)
        mountain_offset = self.background_offset % SCREEN_WIDTH
        for i in range(-1, 2):
            x_pos = mountain_offset + i * SCREEN_WIDTH
            pygame.draw.polygon(surface, (80, 80, 100), [
                (x_pos, SCREEN_HEIGHT),
                (x_pos + 300, SCREEN_HEIGHT - 150),
                (x_pos + 600, SCREEN_HEIGHT)
            ])
            pygame.draw.polygon(surface, (60, 60, 80), [
                (x_pos + 400, SCREEN_HEIGHT),
                (x_pos + 600, SCREEN_HEIGHT - 200),
                (x_pos + 800, SCREEN_HEIGHT)
            ])
    
    def draw_particles(self, surface, camera):
        for p in self.particles:
            proj_pos = camera.project_point(p['position'])
            if proj_pos:
                size = max(1, int(p['size'] * SCREEN_HEIGHT * 0.5 / proj_pos[2]))
                alpha = int(255 * (p['life'] / p.get('initial_life', 1.0)))
                color = p['color']
                
                if len(color) == 3:  # RGB
                    color = (*color, alpha)
                
                color = clamp_color(color)
                
                if size > 1:
                    surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, color, (size, size), size)
                    surface.blit(surf, (int(proj_pos[0] - size), int(proj_pos[1] - size)))
                else:
                    surface.set_at((int(proj_pos[0]), int(proj_pos[1])), color[:3])  # set_at doesn't support alpha
    
    def draw(self, surface):
        # Draw background
        self.draw_background(surface)
        
        # Draw all walls first (for proper depth)
        for wall in self.walls:
            wall.draw(surface, self.camera)
        
        # Draw all platforms
        for platform in self.platforms:
            platform.draw(surface, self.camera)
        
        # Draw particles
        self.draw_particles(surface, self.camera)
        
        # Draw ball
        self.ball.draw(surface, self.camera)
        
        # Draw UI
        score_text = font.render(f'Bananas: {self.ball.score}', True, COLORS['text'])
        lives_text = font.render(f'Lives: {self.ball.lives}', True, COLORS['text'])
        level_text = font.render(f'Level: {self.level}', True, COLORS['text'])
        
        # UI background
        pygame.draw.rect(surface, (0, 0, 0, 150), (5, 5, 200, 110))
        surface.blit(score_text, (10, 10))
        surface.blit(lives_text, (10, 50))
        surface.blit(level_text, (10, 90))
        
        # Draw game over or win message
        if self.game_over:
            game_over_text = big_font.render('GAME OVER', True, (255, 50, 50))
            restart_text = font.render('Press R to restart or ESC to quit', True, COLORS['text'])
            
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
            
            pygame.draw.rect(surface, (0, 0, 0, 200), text_rect.inflate(40, 40))
            pygame.draw.rect(surface, (0, 0, 0, 200), restart_rect.inflate(40, 20))
            
            surface.blit(game_over_text, text_rect)
            surface.blit(restart_text, restart_rect)
        
        if self.win:
            win_text = big_font.render('LEVEL COMPLETE!', True, COLORS['banana'])
            next_text = font.render('Press N for next level or ESC to quit', True, COLORS['text'])
            
            text_rect = win_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
            next_rect = next_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
            
            pygame.draw.rect(surface, (0, 0, 0, 200), text_rect.inflate(40, 40))
            pygame.draw.rect(surface, (0, 0, 0, 200), next_rect.inflate(40, 20))
            
            surface.blit(win_text, text_rect)
            surface.blit(next_text, next_rect)

def main():
    game = Game()
    last_time = pygame.time.get_ticks()
    
    while True:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0
        dt = min(dt, 0.033)  # Cap dt to prevent physics issues
        last_time = current_time
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == KEYDOWN:
                if event.key == K_r and (game.game_over or game.win):
                    game = Game()
                
                if event.key == K_n and game.win:
                    game.win = False
                    game.generate_level()
                    game.ball.reset_position()
                
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                
                if event.key == K_SPACE and game.ball.on_ground:
                    game.ball.velocity.y = game.ball.jump_power
                    game.ball.on_ground = False
        
        if not game.game_over and not game.win:
            # Handle ball movement with analog-like controls
            keys = pygame.key.get_pressed()
            force = MOVEMENT_FORCE * dt
            
            # Get camera forward and right vectors
            forward = (game.camera.target - game.camera.position)
            forward.y = 0
            if forward.length_squared() > 0:
                forward = forward.normalize()
            
            right = Vector3(-forward.z, 0, forward.x)
            
            # Calculate movement vector
            move_vector = Vector3(0, 0, 0)
            
            if keys[K_UP] or keys[K_w]:
                move_vector += forward
            if keys[K_DOWN] or keys[K_s]:
                move_vector -= forward
            if keys[K_LEFT] or keys[K_a]:
                move_vector -= right
            if keys[K_RIGHT] or keys[K_d]:
                move_vector += right
            
            # Normalize diagonal movement
            if move_vector.length_squared() > 0:
                move_vector = move_vector.normalize()
            
            # Apply force with momentum
            game.ball.velocity += move_vector * force * (1.0 if game.ball.on_ground else 0.3)
            
            # Limit maximum speed
            max_speed = 10.0 if game.ball.on_ground else 5.0
            if game.ball.velocity.length() > max_speed:
                game.ball.velocity = game.ball.velocity.normalize() * max_speed
        
        game.update(dt)
        game.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    main()