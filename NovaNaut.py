import thumby
import math
import random
import time
import json
from micropython import const

# === CONSTANTS ===
SCREEN_WIDTH = const(72)
SCREEN_HEIGHT = const(40)
FPS = const(60)
STAR_LAYERS = const(3)
MAX_ALIENS = const(5)
MAX_CHARGE = const(60)
BOSS_SPAWN_TIME = const(100)
POWER_UP_CHANCE = const(100)
UPGRADE_COST = const(50)  # Reduced for better game balance
MAX_UPGRADE_LEVEL = const(3)
FLASH_INTERVAL = const(10)
SHAKE_DURATION = const(10)
SHAKE_INTENSITY = const(2)

# === BITMAPS ===
playerMap = bytearray([
    # Top row - Sharp nose and wing edges
    0b00000010,  # Sharp point
    0b00000110,  # Forward tip
    0b00001110,  # Front section
    0b00011110,  # Mid-front
    0b00111110,  # Middle section
    0b01111110,  # Main body
    0b00111110,  # Rear section
    0b00011110,  # Back edge
    0b00001110,  # Tail
    0b00000110,  # Rear tip
    0b00000010,  # Final point
    0b00000000,
    0b00000000,
    
    # Bottom row - Wing details and fold lines
    0b00000000,  # Clean tip
    0b00000000,  # Forward section
    0b00100000,  # Left fold line
    0b01110000,  # Left wing
    0b11111000,  # Main fold
    0b01110000,  # Center fold
    0b00100000,  # Right wing
    0b00000000,  # Back section
    0b00000000,  # Tail section
    0b00000000,  # Clean end
    0b00000000,
    0b00000000,
    0b00000000
])
# Enhanced bullet patterns
bulletMap = bytearray([7,15,7])
chargeBulletMap = bytearray([15,31,63,31,15])
spreadBulletMap = bytearray([7,15,7])

# More detailed alien designs
alienMaps = {
    'basic': bytearray([60,126,219,255,255,219,126,60]),
    'scout': bytearray([24,60,126,255,255,126,60,24]),
    'elite': bytearray([60,126,255,255,255,255,126,60]),
    'boss': bytearray([
        0,60,126,255,255,255,255,255,255,126,60,0,
        60,255,255,255,255,255,255,255,255,255,255,60
    ])
}

# === PARTICLE SYSTEM ===
class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def emit(self, x, y, count, velocity_range=(0.5, 2.0), lifetime_range=(20, 40)):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(*velocity_range)
            self.particles.append({
                'x': x,
                'y': y,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'life': random.randint(*lifetime_range)
            })
    
    def update(self):
        for particle in self.particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self):
        for particle in self.particles:
            x, y = int(particle['x']), int(particle['y'])
            if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                thumby.display.setPixel(x, y, 1)

# === GAME STATE ===
class GameState:
    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.lives = 3
        self.level = 1
        self.charge = 0
        self.shield_active = False
        self.shield_power = 100
        self.upgrades = {
            'speed': 0,
            'power': 0,
            'shield': 0
        }
        self.powerups = []
        self.boss_active = False
        self.shake_frames = 0
        self.flash_frames = 0
        self.credits = 0
        
    def reset(self):
        self.__init__()

# === GAME CLASS ===
class NovaNaut:
    def __init__(self):
        self.state = GameState()
        self.particles = ParticleSystem()
        self.title_flash_timer = 0
        self.setup_sprites()
        self.setup_stars()
        thumby.display.setFPS(FPS)

    def setup_sprites(self):
        self.player = thumby.Sprite(13, 11, playerMap)
        self.player.x = 5
        self.player.y = SCREEN_HEIGHT // 2
        self.bullets = []
        self.aliens = []
        self.player_velocity = {'x': 0, 'y': 0}

    def setup_stars(self):
        self.stars = []
        for layer in range(STAR_LAYERS):
            speed = (layer + 1) * 0.5
            self.stars.append([{
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'speed': speed
            } for _ in range(10 - layer * 2)])
    
    def handle_input(self):
        # Smoother movement with acceleration
        accel = 0.2 + (self.state.upgrades['speed'] * 0.1)
        max_speed = 2 + (self.state.upgrades['speed'] * 0.5)
        
        if thumby.buttonU.pressed():
            self.player_velocity['y'] = max(-max_speed, self.player_velocity['y'] - accel)
        elif thumby.buttonD.pressed():
            self.player_velocity['y'] = min(max_speed, self.player_velocity['y'] + accel)
        else:
            self.player_velocity['y'] *= 0.9
            
        if thumby.buttonL.pressed():
            self.player_velocity['x'] = max(-max_speed, self.player_velocity['x'] - accel)
        elif thumby.buttonR.pressed():
            self.player_velocity['x'] = min(max_speed, self.player_velocity['x'] + accel)
        else:
            self.player_velocity['x'] *= 0.9
            
        # Handle shooting
        if thumby.buttonA.pressed():
            self.state.charge = min(self.state.charge + 1, MAX_CHARGE)
        elif self.state.charge > 0:
            self.fire_bullet(charged=True)
            self.state.charge = 0
        elif thumby.buttonB.justPressed():
            self.fire_bullet()

    def fire_bullet(self, charged=False):
        power = 1 + (self.state.upgrades['power'] * 0.5)
        if charged:
            power *= 2
            if self.state.charge >= MAX_CHARGE:
                # Fire spread shot
                angles = [-15, 0, 15]
                for angle in angles:
                    self.bullets.append({
                        'x': self.player.x + 11,
                        'y': self.player.y + 5,
                        'dx': math.cos(math.radians(angle)) * 3,
                        'dy': math.sin(math.radians(angle)),
                        'power': power
                    })
            else:
                self.bullets.append({
                    'x': self.player.x + 11,
                    'y': self.player.y + 5,
                    'dx': 3,
                    'dy': 0,
                    'power': power
                })
        else:
            self.bullets.append({
                'x': self.player.x + 11,
                'y': self.player.y + 5,
                'dx': 2,
                'dy': 0,
                'power': power
            })
        
        thumby.audio.play(1000 if charged else 800, 50)
    
    def update(self):
        # Update player position
        self.player.x += self.player_velocity['x']
        self.player.y += self.player_velocity['y']
        
        # Keep player on screen
        self.player.x = max(0, min(SCREEN_WIDTH - 13, self.player.x))
        self.player.y = max(0, min(SCREEN_HEIGHT - 11, self.player.y))
        
        # Update bullets
        for bullet in self.bullets[:]:
            bullet['x'] += bullet['dx']
            bullet['y'] += bullet['dy']
            if bullet['x'] > SCREEN_WIDTH:
                self.bullets.remove(bullet)
        
        # Update aliens
        self.update_aliens()
        
        # Update particles
        self.particles.update()
        
        # Update stars
        self.update_stars()
        
        # Handle collisions
        self.check_collisions()
        
        # Update effects
        if self.state.shake_frames > 0:
            self.state.shake_frames -= 1
        if self.state.flash_frames > 0:
            self.state.flash_frames -= 1
    
    def update_aliens(self):
        # Spawn new aliens
        if len(self.aliens) < MAX_ALIENS and random.random() < 0.02:
            alien_type = random.choice(['basic', 'scout', 'elite']) if random.random() > 0.8 else 'basic'
            self.aliens.append({
                'sprite': thumby.Sprite(8, 8, alienMaps[alien_type]),
                'type': alien_type,
                'health': 2 if alien_type == 'elite' else 1,
                'x': SCREEN_WIDTH,
                'y': random.randint(0, SCREEN_HEIGHT - 8)
            })
        
        # Update alien positions
        for alien in self.aliens[:]:
            speed = 1.5 if alien['type'] == 'scout' else 1
            alien['x'] -= speed
            if alien['x'] < -8:
                self.aliens.remove(alien)
    
    def update_stars(self):
        for layer in self.stars:
            for star in layer:
                star['x'] -= star['speed']
                if star['x'] < 0:
                    star['x'] = SCREEN_WIDTH
                    star['y'] = random.randint(0, SCREEN_HEIGHT)
    
    def check_collisions(self):
        for alien in self.aliens[:]:
            # Check bullet collisions
            for bullet in self.bullets[:]:
                if (abs(alien['x'] - bullet['x']) < 8 and 
                    abs(alien['y'] - bullet['y']) < 8):
                    alien['health'] -= bullet['power']
                    self.bullets.remove(bullet)
                    if alien['health'] <= 0:
                        self.handle_alien_destroyed(alien)
                        break
            
            # Check player collision
            if (abs(self.player.x + 6 - (alien['x'] + 4)) < 8 and 
                abs(self.player.y + 5 - (alien['y'] + 4)) < 8):
                if self.state.shield_active:
                    self.state.shield_power -= 25
                    if self.state.shield_power <= 0:
                        self.state.shield_active = False
                    self.aliens.remove(alien)
                else:
                    self.handle_player_hit()
                    self.aliens.remove(alien)

    def handle_alien_destroyed(self, alien):
        points = 20 if alien['type'] == 'elite' else 10
        self.state.score += points
        self.state.credits += 1
        self.particles.emit(alien['x'] + 4, alien['y'] + 4, 10)
        self.aliens.remove(alien)
        self.state.shake_frames = 5
        thumby.audio.play(200, 100)
    
    def handle_player_hit(self):
        self.state.lives -= 1
        self.state.flash_frames = FLASH_INTERVAL
        self.state.shake_frames = SHAKE_DURATION
        self.particles.emit(self.player.x + 6, self.player.y + 5, 20)
        thumby.audio.play(100, 200)

    def draw_hud(self):
        # Draw score
        score_text = str(self.state.score)
        thumby.display.drawText(score_text, 0, 0, 1)
        
        # Draw lives
        for i in range(self.state.lives):
            thumby.display.drawFilledRectangle(SCREEN_WIDTH - 4 - (i * 5), 0, 3, 3, 1)
        
        # Draw shield power if active
        if self.state.shield_active:
            shield_width = (self.state.shield_power * 10) // 100
            thumby.display.drawRectangle(0, SCREEN_HEIGHT - 4, 10, 3, 1)
            thumby.display.drawFilledRectangle(0, SCREEN_HEIGHT - 4, shield_width, 3, 1)
        
        # Draw level indicator
        level_text = f"L{self.state.level}"
        thumby.display.drawText(level_text, SCREEN_WIDTH - 12, SCREEN_HEIGHT - 8, 1)
        
        # Draw credits
        credit_text = f"C:{self.state.credits}"
        thumby.display.drawText(credit_text, 0, SCREEN_HEIGHT - 8, 1)

    def draw_shield(self):
        t = time.ticks_ms() / 200
        radius = 8
        segments = 8
        for i in range(segments):
            angle = (i / segments) * 2 * math.pi
            x1 = int(self.player.x + 6 + math.cos(angle + t) * radius)
            y1 = int(self.player.y + 5 + math.sin(angle + t) * radius)
            x2 = int(self.player.x + 6 + math.cos(angle + t + 0.8) * radius)
            y2 = int(self.player.y + 5 + math.sin(angle + t + 0.8) * radius)
            thumby.display.drawLine(x1, y1, x2, y2, 1)
    
    def draw(self):
        thumby.display.fill(0)
        
        # Apply screen shake
        shake_x = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY) if self.state.shake_frames > 0 else 0
        shake_y = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY) if self.state.shake_frames > 0 else 0
        
        # Draw stars
        for layer in self.stars:
            for star in layer:
                x = int(star['x']) + shake_x
                y = int(star['y']) + shake_y
                if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                    thumby.display.setPixel(x, y, 1)
        
        # Draw particles
        self.particles.draw()
        
        # Draw bullets
        for bullet in self.bullets:
            x = int(bullet['x']) + shake_x
            y = int(bullet['y']) + shake_y
            thumby.display.drawFilledRectangle(x, y, 3, 2, 1)
        
        # Draw aliens
        for alien in self.aliens:
            alien['sprite'].x = int(alien['x']) + shake_x
            alien['sprite'].y = int(alien['y']) + shake_y
            thumby.display.drawSprite(alien['sprite'])
        
        # Draw player
        self.player.x += shake_x
        self.player.y += shake_y
        thumby.display.drawSprite(self.player)
        self.player.x -= shake_x
        self.player.y -= shake_y
        
        # Draw shield if active
        if self.state.shield_active:
            self.draw_shield()
        
        # Draw charge meter
        if self.state.charge > 0:
            charge_width = (self.state.charge * 20) // MAX_CHARGE
            thumby.display.drawRectangle(26, 36, 20, 3, 1)
            thumby.display.drawFilledRectangle(26, 36, charge_width, 3, 1)
        
        # Draw HUD
        self.draw_hud()
        
        # Draw flash effect
        if self.state.flash_frames > 0:
            alpha = self.state.flash_frames / FLASH_INTERVAL
            for i in range(0, SCREEN_WIDTH * SCREEN_HEIGHT // 16):
                if random.random() < alpha:
                    x = random.randint(0, SCREEN_WIDTH - 1)
                    y = random.randint(0, SCREEN_HEIGHT - 1)
                    thumby.display.setPixel(x, y, 1)
        
        thumby.display.update()

    def show_menu(self):
        menu_items = ["START", "UPGRADE", "SCORES"]
        selected = 0
        
        while True:
            thumby.display.fill(0)
            
            # Draw flashing title
            title = "NOVANAUT"
            title_x = (SCREEN_WIDTH - len(title) * 6) // 2
            self.title_flash_timer = (self.title_flash_timer + 1) % 30
            if self.title_flash_timer < 20:  # Show title for 20 frames, hide for 10
                thumby.display.drawText(title, title_x, 4, 1)
            
            # Draw menu items (moved up)
            for i, item in enumerate(menu_items):
                y = 15 + i * 8  # Changed from 20 to 15 to move items up
                x = (SCREEN_WIDTH - len(item) * 6) // 2
                if i == selected:
                    thumby.display.drawRectangle(x - 2, y - 1, len(item) * 6 + 3, 9, 1)
                thumby.display.drawText(item, x, y, 1)
            
            # Handle input
            if thumby.buttonU.justPressed() and selected > 0:
                selected -= 1
                thumby.audio.play(800, 50)
            elif thumby.buttonD.justPressed() and selected < len(menu_items) - 1:
                selected += 1
                thumby.audio.play(800, 50)
            elif thumby.buttonA.justPressed():
                thumby.audio.play(1000, 100)
                return menu_items[selected]
            
            thumby.display.update()
            
    def show_upgrade_menu(self):
        upgrades = [
            ("SPEED", 'speed'),
            ("POWER", 'power'),
            ("SHIELD", 'shield')
        ]
        selected = 0
        
        while True:
            thumby.display.fill(0)
            
            # Draw title
            thumby.display.drawText("UPGRADES", 16, 0, 1)
            thumby.display.drawText(f"Credits: {self.state.credits}", 8, 8, 1)
            
            # Draw upgrade options
            for i, (name, key) in enumerate(upgrades):
                y = 20 + i * 8
                level = self.state.upgrades[key]
                cost = UPGRADE_COST * (level + 1)
                
                if i == selected:
                    thumby.display.drawRectangle(0, y - 1, SCREEN_WIDTH, 9, 1)
                
                text = f"{name}: {level}/{MAX_UPGRADE_LEVEL} ({cost})"
                thumby.display.drawText(text, 2, y, 1 if i != selected else 0)
            
            # Handle input
            if thumby.buttonU.justPressed() and selected > 0:
                selected -= 1
                thumby.audio.play(800, 50)
            elif thumby.buttonD.justPressed() and selected < len(upgrades) - 1:
                selected += 1
                thumby.audio.play(800, 50)
            elif thumby.buttonA.justPressed():
                key = upgrades[selected][1]
                level = self.state.upgrades[key]
                cost = UPGRADE_COST * (level + 1)
                
                if level < MAX_UPGRADE_LEVEL and self.state.credits >= cost:
                    self.state.credits -= cost
                    self.state.upgrades[key] += 1
                    thumby.audio.play(1000, 100)
            elif thumby.buttonB.justPressed():
                return
            
            thumby.display.update()

    def show_game_over(self):
        if self.state.score > self.state.high_score:
            self.state.high_score = self.state.score
        
        while True:
            thumby.display.fill(0)
            
            # Draw game over text
            text = "GAME OVER"
            x = (SCREEN_WIDTH - len(text) * 6) // 2
            thumby.display.drawText(text, x, 8, 1)
            
            # Draw score
            score_text = f"SCORE: {self.state.score}"
            x = (SCREEN_WIDTH - len(score_text) * 6) // 2
            thumby.display.drawText(score_text, x, 20, 1)
            
            # Draw high score
            hi_text = f"HIGH: {self.state.high_score}"
            x = (SCREEN_WIDTH - len(hi_text) * 6) // 2
            thumby.display.drawText(hi_text, x, 28, 1)
            
            if thumby.buttonA.justPressed():
                return
            
            thumby.display.update()

    def run(self):
        while True:
            action = self.show_menu()
            
            if action == "START":
                self.state.reset()
                self.setup_sprites()
                self.game_loop()
                self.show_game_over()
            elif action == "UPGRADE":
                self.show_upgrade_menu()
            elif action == "SCORES":
                while True:
                    thumby.display.fill(0)
                    text = "HIGH SCORE"
                    x = (SCREEN_WIDTH - len(text) * 6) // 2
                    thumby.display.drawText(text, x, 10, 1)
                    
                    score = str(self.state.high_score)
                    x = (SCREEN_WIDTH - len(score) * 6) // 2
                    thumby.display.drawText(score, x, 20, 1)
                    
                    if thumby.buttonB.justPressed():
                        break
                    thumby.display.update()

    def game_loop(self):
        while self.state.lives > 0:
            self.handle_input()
            self.update()
            self.draw()

# Start the game
if __name__ == "__main__":
    game = NovaNaut()
    game.run()
        
