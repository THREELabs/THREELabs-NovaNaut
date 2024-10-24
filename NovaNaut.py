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
MAX_CHARGE = const(60)
BOSS_SPAWN_TIME = const(100)
POWER_UP_CHANCE = const(100)
UPGRADE_COST = const(50)
MAX_UPGRADE_LEVEL = const(3)
FLASH_INTERVAL = const(10)
SHAKE_DURATION = const(10)
SHAKE_INTENSITY = const(2)
POWERUP_DURATION = const(300)
COMBO_TIMEOUT = const(120)
MAX_COMBO = const(8)
MACHINE_GUN_HEAT_MAX = const(100)
HEAT_PER_SHOT = const(5)
COOLING_RATE = const(1)
MACHINE_GUN_RATE = const(5)

# Define POWERUP_TYPES as a regular tuple
POWERUP_TYPES = ('SPEED', 'SHIELD', 'MULTI')

# === BITMAPS ===
playerMap = bytearray([
    0b00000010,
    0b00000110,
    0b00001110,
    0b00011110,
    0b00111110,
    0b01111110,
    0b00111110,
    0b00011110,
    0b00001110,
    0b00000110,
    0b00000010,
    0b00000000,
    0b00000000,
    
    0b00000000,
    0b00000000,
    0b00100000,
    0b01110000,
    0b11111000,
    0b01110000,
    0b00100000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000
])

bulletMap = bytearray([7,15,7])
chargeBulletMap = bytearray([15,31,63,31,15])
spreadBulletMap = bytearray([7,15,7])

alienMaps = {
    'basic': bytearray([60,126,219,255,255,219,126,60]),
    'scout': bytearray([24,60,126,255,255,126,60,24]),
    'elite': bytearray([60,126,255,255,255,255,126,60]),
    'boss': bytearray([
        0,60,126,255,255,255,255,255,255,126,60,0,
        60,255,255,255,255,255,255,255,255,255,255,60
    ])
}

class PowerUp:
    def __init__(self, type, x, y):
        self.type = type
        self.x = x
        self.y = y
        self.active = False
        self.timer = 0
        self.width = 6
        self.height = 6
        
    def collect(self):
        self.active = True
        self.timer = POWERUP_DURATION
        
    def update(self):
        if self.active:
            self.timer -= 1
            return self.timer <= 0
        return False

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
        self.combo = 0
        self.combo_timer = 0
        self.current_powerup = None
        self.score_multiplier = 1
        self.wave_number = 1
        self.wave_enemies = 0
        self.wave_announcement_timer = 0
        self.floating_texts = []
        # Machine gun attributes
        self.heat_level = 0
        self.overheated = False
        self.machine_gun_timer = 0
        
    def update_combo(self):
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo = 0
                self.score_multiplier = 1
    
    def reset(self):
        self.__init__()

class NovaNaut:
    def __init__(self):
        self.state = GameState()
        self.particles = ParticleSystem()
        self.title_flash_timer = 0
        self.powerups = []
        self.floating_texts = []
        self.max_aliens = 5
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

    def update_heat(self):
        if self.state.overheated:
            self.state.heat_level = max(0, self.state.heat_level - COOLING_RATE * 2)
            if self.state.heat_level == 0:
                self.state.overheated = False
        else:
            self.state.heat_level = max(0, self.state.heat_level - COOLING_RATE)

    def draw_heat_gauge(self):
        gauge_height = 20
        gauge_y = 10
        filled_height = int((self.state.heat_level / MACHINE_GUN_HEAT_MAX) * gauge_height)
        
        # Draw gauge outline
        thumby.display.drawRectangle(2, gauge_y, 3, gauge_height, 1)
        
        # Draw fill level
        if filled_height > 0:
            thumby.display.drawFilledRectangle(2, gauge_y + (gauge_height - filled_height), 
                                             3, filled_height, 1)
        
        # Draw warning indicator when close to overheating
        if self.state.heat_level > MACHINE_GUN_HEAT_MAX * 0.8:
            if (time.ticks_ms() // 100) % 2:  # Flashing effect
                thumby.display.drawText("!", 1, gauge_y + gauge_height + 2, 1)

        # Show "HOT" text when overheated
        if self.state.overheated:
            if (time.ticks_ms() // 200) % 2:  # Flashing effect
                thumby.display.drawText("HOT", 6, gauge_y + 8, 1)

    def handle_input(self):
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
        elif thumby.buttonB.pressed() and not self.state.overheated:  # Machine gun
            if self.state.machine_gun_timer <= 0:
                if self.state.heat_level < MACHINE_GUN_HEAT_MAX:
                    self.fire_bullet()
                    self.state.heat_level += HEAT_PER_SHOT
                    self.state.machine_gun_timer = MACHINE_GUN_RATE
                    
                    if self.state.heat_level >= MACHINE_GUN_HEAT_MAX:
                        self.state.overheated = True
                        thumby.audio.play(100, 100)  # Overheat sound
        
        # Update machine gun timer
        if self.state.machine_gun_timer > 0:
            self.state.machine_gun_timer -= 1

    def spawn_powerup(self, x, y):
        if random.random() < 0.2:
            powerup_type = random.choice(POWERUP_TYPES)
            self.powerups.append(PowerUp(powerup_type, x, y))
    
    def update_powerups(self):
        if self.state.current_powerup:
            if self.state.current_powerup.update():
                self.state.current_powerup = None
        
        for powerup in self.powerups[:]:
            if (abs(self.player.x + 6 - powerup.x) < 8 and 
                abs(self.player.y + 5 - powerup.y) < 8):
                powerup.collect()
                self.state.current_powerup = powerup
                self.powerups.remove(powerup)
                thumby.audio.play(1200, 50)

    def update_floating_texts(self):
        for text in self.floating_texts[:]:
            text['y'] += text['dy']
            text['timer'] -= 1
            if text['timer'] <= 0:
                self.floating_texts.remove(text)

    def handle_alien_destroyed(self, alien):
        points = 20 if alien['type'] == 'elite' else 10
        
        self.state.combo = min(self.state.combo + 1, MAX_COMBO)
        self.state.combo_timer = COMBO_TIMEOUT
        self.state.score_multiplier = 1 + (self.state.combo * 0.2)
        
        final_points = int(points * self.state.score_multiplier)
        self.state.score += final_points
        
        self.floating_texts.append({
            'text': f'+{final_points}',
            'x': alien['x'],
            'y': alien['y'],
            'timer': 30,
            'dy': -0.5
        })
        
        self.state.credits += 1
        self.spawn_powerup(alien['x'], alien['y'])
        self.particles.emit(alien['x'] + 4, alien['y'] + 4, 10)
        self.aliens.remove(alien)
        self.state.shake_frames = 5
        thumby.audio.play(200, 100)
        
    def show_menu(self):
        menu_items = ["START", "UPGRADE", "SCORES"]
        selected = 0
        
        while True:
            thumby.display.fill(0)
            
            # Draw title
            title = "NOVANAUT"
            title_x = (SCREEN_WIDTH - len(title) * 6) // 2
            self.title_flash_timer = (self.title_flash_timer + 1) % 30
            if self.title_flash_timer < 20:
                thumby.display.drawText(title, title_x, 4, 1)
            
            # Draw menu items
            for i, item in enumerate(menu_items):
                y = 15 + i * 8
                x = (SCREEN_WIDTH - len(item) * 6) // 2
                if i == selected:
                    thumby.display.drawRectangle(x - 2, y - 1, len(item) * 6 + 3, 9, 1)
                thumby.display.drawText(item, x, y, 1 if i != selected else 0)
            
            thumby.display.update()
            
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

    def show_upgrade_menu(self):
        upgrades = [
            ("SPEED", 'speed'),
            ("POWER", 'power'),
            ("SHIELD", 'shield')
        ]
        selected = 0
        
        while True:
            thumby.display.fill(0)
            
            # Draw header
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
            
            # Draw return instruction
            thumby.display.drawText("B:BACK", 2, SCREEN_HEIGHT - 8, 1)
            
            thumby.display.update()
            
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

    def show_scores(self):
        while True:
            thumby.display.fill(0)
            
            text = "HIGH SCORE"
            x = (SCREEN_WIDTH - len(text) * 6) // 2
            thumby.display.drawText(text, x, 10, 1)
            
            score = str(self.state.high_score)
            x = (SCREEN_WIDTH - len(score) * 6) // 2
            thumby.display.drawText(score, x, 20, 1)
            
            # Draw return instruction
            thumby.display.drawText("B:BACK", 2, SCREEN_HEIGHT - 8, 1)
            
            thumby.display.update()
            
            if thumby.buttonB.justPressed():
                return

    def show_game_over(self):
        if self.state.score > self.state.high_score:
            self.state.high_score = self.state.score
        
        while True:
            thumby.display.fill(0)
            
            text = "GAME OVER"
            x = (SCREEN_WIDTH - len(text) * 6) // 2
            thumby.display.drawText(text, x, 8, 1)
            
            score_text = f"SCORE: {self.state.score}"
            x = (SCREEN_WIDTH - len(score_text) * 6) // 2
            thumby.display.drawText(score_text, x, 20, 1)
            
            hi_text = f"HIGH: {self.state.high_score}"
            x = (SCREEN_WIDTH - len(hi_text) * 6) // 2
            thumby.display.drawText(hi_text, x, 28, 1)
            
            # Draw return instruction
            thumby.display.drawText("B:MENU", 2, SCREEN_HEIGHT - 8, 1)
            
            thumby.display.update()
            
            if thumby.buttonB.justPressed():
                return

    def update_player_position(self):
        speed_multiplier = 1.5 if (self.state.current_powerup and 
                                 self.state.current_powerup.type == 'SPEED') else 1.0
        
        self.player.x += self.player_velocity['x'] * speed_multiplier
        self.player.y += self.player_velocity['y'] * speed_multiplier
        
        self.player.x = max(0, min(SCREEN_WIDTH - 13, self.player.x))
        self.player.y = max(0, min(SCREEN_HEIGHT - 11, self.player.y))

    def update_stars(self):
        for layer in self.stars:
            for star in layer:
                star['x'] -= star['speed']
                if star['x'] < 0:
                    star['x'] = SCREEN_WIDTH
                    star['y'] = random.randint(0, SCREEN_HEIGHT)

    def update_aliens(self):
        if len(self.aliens) < self.max_aliens and self.state.wave_enemies > 0 and random.random() < 0.02:
            alien_type = random.choice(['basic', 'scout', 'elite']) if random.random() > 0.8 else 'basic'
            self.aliens.append({
                'sprite': thumby.Sprite(8, 8, alienMaps[alien_type]),
                'type': alien_type,
                'health': 2 if alien_type == 'elite' else 1,
                'x': SCREEN_WIDTH,
                'y': random.randint(0, SCREEN_HEIGHT - 8)
            })
            self.state.wave_enemies -= 1
        
        for alien in self.aliens[:]:
            speed = 1.5 if alien['type'] == 'scout' else 1
            alien['x'] -= speed
            if alien['x'] < -8:
                self.aliens.remove(alien)

    def update_bullets(self):
        for bullet in self.bullets[:]:
            bullet['x'] += bullet['dx']
            bullet['y'] += bullet['dy']
            if bullet['x'] > SCREEN_WIDTH:
                self.bullets.remove(bullet)

    def check_collisions(self):
        for alien in self.aliens[:]:
            for bullet in self.bullets[:]:
                if (abs(alien['x'] - bullet['x']) < 8 and 
                    abs(alien['y'] - bullet['y']) < 8):
                    alien['health'] -= bullet['power']
                    self.bullets.remove(bullet)
                    if alien['health'] <= 0:
                        self.handle_alien_destroyed(alien)
                        break
            
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

    def fire_bullet(self, charged=False):
        power = 1 + (self.state.upgrades['power'] * 0.5)
        is_multi = (self.state.current_powerup and 
                   self.state.current_powerup.type == 'MULTI')
        
        if charged:
            power *= 2
            if self.state.charge >= MAX_CHARGE or is_multi:
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
            if is_multi:
                self.bullets.append({
                    'x': self.player.x + 11,
                    'y': self.player.y + 3,
                    'dx': 2,
                    'dy': 0,
                    'power': power
                })
                self.bullets.append({
                    'x': self.player.x + 11,
                    'y': self.player.y + 7,
                    'dx': 2,
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

    def game_loop(self):
        self.start_new_wave()  # Initialize first wave
        while self.state.lives > 0:
            self.handle_input()
            self.update()
            self.check_wave_completion()
            self.draw()

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
                self.show_scores()

# Start the game
if __name__ == "__main__":
    try:
        game = NovaNaut()
        game.run()
    except Exception as e:
        # Simple error display on screen
        thumby.display.fill(0)
        thumby.display.drawText("ERROR:", 0, 0, 1)
        error_msg = str(e)
        # Split error message into lines of 12 chars
        for i in range(0, len(error_msg), 12):
            line = error_msg[i:i+12]
            y_pos = 10 + (i // 12) * 8
            if y_pos < SCREEN_HEIGHT - 8:
                thumby.display.drawText(line, 0, y_pos, 1)
        thumby.display.update()
        time.sleep(5)  # Show error for 5 seconds
        raise
