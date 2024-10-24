import thumby
import math
import random
import time
from micropython import const

# === CONSTANTS ===
SCREEN_WIDTH = const(72)
SCREEN_HEIGHT = const(40)
FPS = const(60)
STAR_LAYERS = const(3)
MAX_CHARGE = const(60)
POWER_UP_CHANCE = const(0.2)  # Changed from 100 to 0.2 for clarity
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

# Simplified tuple definition
POWERUP_TYPES = ('SPEED', 'SHIELD', 'MULTI')

# Pre-calculated bitmap for optimization
playerMap = bytearray([
    0b00000010, 0b00000110, 0b00001110, 0b00011110,
    0b00111110, 0b01111110, 0b00111110, 0b00011110,
    0b00001110, 0b00000110, 0b00000010, 0b00000000,
    0b00000000, 0b00000000, 0b00000000, 0b00100000,
    0b01110000, 0b11111000, 0b01110000, 0b00100000,
    0b00000000, 0b00000000, 0b00000000, 0b00000000,
    0b00000000, 0b00000000
])

# Simplified alien maps using fewer bytes
alienMaps = {
    'basic': bytearray([60, 126, 219, 255, 255, 219, 126, 60]),
    'scout': bytearray([24, 60, 126, 255, 255, 126, 60, 24]),
    'elite': bytearray([60, 126, 255, 255, 255, 255, 126, 60]),
    'boss': bytearray([60, 126, 255, 255, 255, 255, 126, 60] * 2)  # Simplified boss sprite
}

class PowerUp:
    __slots__ = ('type', 'x', 'y', 'active', 'timer', 'width', 'height')
    
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
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            self.particles.append({
                'x': x, 'y': y, 'dx': dx, 'dy': dy,
                'life': random.randint(*lifetime_range)
            })
    
    def update(self):
        i = len(self.particles) - 1
        while i >= 0:
            particle = self.particles[i]
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.pop(i)
            i -= 1
    
    def draw(self):
        for p in self.particles:
            x, y = int(p['x']), int(p['y'])
            if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                thumby.display.setPixel(x, y, 1)

class GameState:
    __slots__ = ('score', 'high_score', 'lives', 'level', 'charge', 'shield_active',
                'shield_power', 'upgrades', 'powerups', 'boss_active', 'shake_frames',
                'flash_frames', 'credits', 'combo', 'combo_timer', 'current_powerup',
                'score_multiplier', 'wave_number', 'wave_enemies', 'wave_announcement_timer',
                'floating_texts', 'heat_level', 'overheated', 'machine_gun_timer')
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.score = 0
        self.high_score = 0
        self.lives = 3
        self.level = 1
        self.charge = 0
        self.shield_active = False
        self.shield_power = 100
        self.upgrades = {'speed': 0, 'power': 0, 'shield': 0}
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
        self.heat_level = 0
        self.overheated = False
        self.machine_gun_timer = 0
    
    def update_combo(self):
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo = 0
                self.score_multiplier = 1

class NovaNaut:
    def __init__(self):
        self.state = GameState()
        self.particles = ParticleSystem()
        self.title_flash_timer = 0
        self.setup_game()
        thumby.display.setFPS(FPS)
    
    def setup_game(self):
        self.setup_sprites()
        self.setup_stars()
    
    def setup_sprites(self):
        self.player = thumby.Sprite(13, 11, playerMap)
        self.player.x = 5
        self.player.y = SCREEN_HEIGHT // 2
        self.bullets = []
        self.aliens = []
        self.player_velocity = {'x': 0, 'y': 0}
        self.powerups = []
    
    def __init__(self):
        self.state = GameState()
        self.particles = ParticleSystem()
        self.title_flash_timer = 0
        self.player = None
        self.bullets = []
        self.aliens = []
        self.stars = []
        self.powerups = []
        self.floating_texts = []  # Added missing initialization
        self.player_velocity = {'x': 0, 'y': 0}
        self.max_aliens = 5
        thumby.display.setFPS(FPS)
        self.setup_game()
    
    def setup_game(self):
        self.setup_sprites()
        self.setup_stars()
        # Reset all game-specific lists
        self.bullets = []
        self.aliens = []
        self.powerups = []
        self.floating_texts = []
        self.player_velocity = {'x': 0, 'y': 0}
    
    def setup_sprites(self):
        self.player = thumby.Sprite(13, 11, playerMap)
        self.player.x = 5
        self.player.y = SCREEN_HEIGHT // 2
    
    def update_floating_texts(self):
        i = len(self.floating_texts) - 1
        while i >= 0:
            text = self.floating_texts[i]
            text['y'] += text['dy']
            text['timer'] -= 1
            if text['timer'] <= 0:
                self.floating_texts.pop(i)
            i -= 1

    def handle_alien_destroyed(self, alien):
        points = 20 if alien['type'] == 'elite' else 10
        
        self.state.combo = min(self.state.combo + 1, MAX_COMBO)
        self.state.combo_timer = COMBO_TIMEOUT
        self.state.score_multiplier = 1 + (self.state.combo * 0.2)
        
        final_points = int(points * self.state.score_multiplier)
        self.state.score += final_points
        
        # Add new floating text
        if not hasattr(self, 'floating_texts'):
            self.floating_texts = []
        
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

    def reset_game_state(self):
        """Reset all game-related state when starting a new game"""
        self.state.reset()
        self.bullets = []
        self.aliens = []
        self.powerups = []
        self.floating_texts = []
        self.player_velocity = {'x': 0, 'y': 0}
        self.setup_game()

    def run(self):
        while True:
            action = self.show_menu()
            
            if action == "START":
                self.reset_game_state()  # Use new reset method
                self.game_loop()
                self.show_game_over()
            elif action == "UPGRADE":
                self.show_upgrade_menu()
            elif action == "SCORES":
                self.show_scores()
    
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

    def handle_input(self):
        accel = 0.2 + (self.state.upgrades['speed'] * 0.1)
        max_speed = 2 + (self.state.upgrades['speed'] * 0.5)
        
        # Movement input
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
        
        # Weapon input
        if thumby.buttonA.pressed():
            self.state.charge = min(self.state.charge + 1, MAX_CHARGE)
        elif self.state.charge > 0:
            self.fire_bullet(charged=True)
            self.state.charge = 0
        elif thumby.buttonB.pressed() and not self.state.overheated:
            if self.state.machine_gun_timer <= 0:
                if self.state.heat_level < MACHINE_GUN_HEAT_MAX:
                    self.fire_bullet()
                    self.state.heat_level += HEAT_PER_SHOT
                    self.state.machine_gun_timer = MACHINE_GUN_RATE
                    
                    if self.state.heat_level >= MACHINE_GUN_HEAT_MAX:
                        self.state.overheated = True
                        thumby.audio.play(100, 100)
        
        if self.state.machine_gun_timer > 0:
            self.state.machine_gun_timer -= 1

    def spawn_powerup(self, x, y):
        if random.random() < POWER_UP_CHANCE:
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

    def handle_player_hit(self):
        if not self.state.shield_active:
            self.state.lives -= 1
            self.state.flash_frames = FLASH_INTERVAL
            self.state.shake_frames = SHAKE_DURATION
            thumby.audio.play(100, 200)

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

    def update(self):
        self.update_player_position()
        self.update_bullets()
        self.update_aliens()
        self.particles.update()
        self.update_stars()
        self.check_collisions()
        self.state.update_combo()
        self.update_powerups()
        self.update_floating_texts()
        self.update_heat()
        
        if self.state.shake_frames > 0:
            self.state.shake_frames -= 1
        if self.state.flash_frames > 0:
            self.state.flash_frames -= 1
        if self.state.wave_announcement_timer > 0:
            self.state.wave_announcement_timer -= 1

    def draw_powerups(self):
        for powerup in self.powerups:
            x, y = int(powerup.x), int(powerup.y)
            if powerup.type == 'SPEED':
                thumby.display.drawFilledRectangle(x, y, 6, 6, 1)
                thumby.display.drawLine(x + 1, y + 3, x + 4, y + 3, 0)
            elif powerup.type == 'SHIELD':
                thumby.display.drawRectangle(x, y, 6, 6, 1)
                thumby.display.drawLine(x, y + 3, x + 5, y + 3, 1)
                thumby.display.drawLine(x + 3, y, x + 3, y + 5, 1)
            elif powerup.type == 'MULTI':
                thumby.display.drawFilledRectangle(x, y, 6, 6, 1)
                thumby.display.drawText("2", x + 1, y + 1, 0)

    def draw_powerup_indicator(self):
        if self.state.current_powerup:
            icon_x, icon_y = 2, 12
            if self.state.current_powerup.type == 'SPEED':
                thumby.display.drawLine(icon_x, icon_y + 3, icon_x + 5, icon_y + 3, 1)
                thumby.display.drawLine(icon_x + 3, icon_y + 1, icon_x + 5, icon_y + 3, 1)
                thumby.display.drawLine(icon_x + 3, icon_y + 5, icon_x + 5, icon_y + 3, 1)
            elif self.state.current_powerup.type == 'SHIELD':
                thumby.display.drawRectangle(icon_x + 1, icon_y + 1, 4, 4, 1)
            elif self.state.current_powerup.type == 'MULTI':
                thumby.display.drawText("×2", icon_x, icon_y, 1)
            
            bar_width = int((self.state.current_powerup.timer / POWERUP_DURATION) * 10)
            thumby.display.drawRectangle(icon_x, icon_y + 6, 10, 2, 1)
            thumby.display.drawFilledRectangle(icon_x, icon_y + 6, bar_width, 2, 1)

    def draw_shield(self):
        if self.state.shield_active:
            t = time.ticks_ms() / 200
            radius = 8
            segments = 8
            center_x = self.player.x + 6
            center_y = self.player.y + 5
            
            for i in range(segments):
                angle = (i / segments) * 2 * math.pi
                next_angle = ((i + 1) / segments) * 2 * math.pi
                
                x1 = int(center_x + math.cos(angle + t) * radius)
                y1 = int(center_y + math.sin(angle + t) * radius)
                x2 = int(center_x + math.cos(next_angle + t) * radius)
                y2 = int(center_y + math.sin(next_angle + t) * radius)
                
                if (0 <= x1 < SCREEN_WIDTH and 0 <= y1 < SCREEN_HEIGHT and
                    0 <= x2 < SCREEN_WIDTH and 0 <= y2 < SCREEN_HEIGHT):
                    thumby.display.drawLine(x1, y1, x2, y2, 1)

    def draw_combo_indicator(self):
        if self.state.combo > 1:
            text = f"{self.state.combo}x"
            x = SCREEN_WIDTH - len(text) * 6 - 2
            y = 10
            thumby.display.drawText(text, x, y, 1)
            
            bar_width = int((self.state.combo_timer / COMBO_TIMEOUT) * 10)
            thumby.display.drawRectangle(x, y + 8, 10, 2, 1)
            thumby.display.drawFilledRectangle(x, y + 8, bar_width, 2, 1)

    def draw_wave_announcement(self):
        if self.state.wave_announcement_timer > 0:
            text = f"WAVE {self.state.wave_number}"
            x = (SCREEN_WIDTH - len(text) * 6) // 2
            y = (SCREEN_HEIGHT - 8) // 2
            thumby.display.drawText(text, x, y, 1)

    def draw_floating_texts(self):
        for text in self.floating_texts:
            x = int(text['x'])
            y = int(text['y'])
            if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                thumby.display.drawText(text['text'], x, y, 1)

    def draw_stars(self):
        shake_x = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY) if self.state.shake_frames > 0 else 0
        shake_y = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY) if self.state.shake_frames > 0 else 0
        
        for layer in self.stars:
            for star in layer:
                x = int(star['x']) + shake_x
                y = int(star['y']) + shake_y
                if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                    thumby.display.setPixel(x, y, 1)

    def draw_hud(self):
        # Score
        score_text = str(self.state.score)
        thumby.display.drawText(score_text, 0, 0, 1)
        
        # Lives
        for i in range(self.state.lives):
            thumby.display.drawFilledRectangle(SCREEN_WIDTH - 4 - (i * 5), 0, 3, 3, 1)
        
        # Shield meter
        if self.state.shield_active:
            shield_width = (self.state.shield_power * 10) // 100
            thumby.display.drawRectangle(0, SCREEN_HEIGHT - 4, 10, 3, 1)
            thumby.display.drawFilledRectangle(0, SCREEN_HEIGHT - 4, shield_width, 3, 1)
        
        # Level and credits
        level_text = f"L{self.state.level}"
        thumby.display.drawText(level_text, SCREEN_WIDTH - 12, SCREEN_HEIGHT - 8, 1)
        credit_text = f"C:{self.state.credits}"
        thumby.display.drawText(credit_text, 0, SCREEN_HEIGHT - 8, 1)

    def draw_heat_gauge(self):
        gauge_height = 20
        gauge_y = 10
        filled_height = int((self.state.heat_level / MACHINE_GUN_HEAT_MAX) * gauge_height)
        
        thumby.display.drawRectangle(2, gauge_y, 3, gauge_height, 1)
        
        if filled_height > 0:
            thumby.display.drawFilledRectangle(2, gauge_y + (gauge_height - filled_height), 
                                             3, filled_height, 1)
        
        if self.state.heat_level > MACHINE_GUN_HEAT_MAX * 0.8:
            if (time.ticks_ms() // 100) % 2:
                thumby.display.drawText("!", 1, gauge_y + gauge_height + 2, 1)

        if self.state.overheated:
            if (time.ticks_ms() // 200) % 2:
                thumby.display.drawText("HOT", 6, gauge_y + 8, 1)

    def draw_charge_bar(self):
        if self.state.charge > 0:
            charge_width = (self.state.charge * 20) // MAX_CHARGE
            thumby.display.drawRectangle(26, 36, 20, 3, 1)
            thumby.display.drawFilledRectangle(26, 36, charge_width, 3, 1)

    def draw_flash_effect(self):
        if self.state.flash_frames > 0:
            alpha = self.state.flash_frames / FLASH_INTERVAL
            for _ in range(SCREEN_WIDTH * SCREEN_HEIGHT // 16):
                if random.random() < alpha:
                    x = random.randint(0, SCREEN_WIDTH - 1)
                    y = random.randint(0, SCREEN_HEIGHT - 1)
                    thumby.display.setPixel(x, y, 1)

    def start_new_wave(self):
        self.state.wave_number += 1
        self.state.wave_announcement_timer = 60
        self.state.wave_enemies = self.state.wave_number * 5
        self.max_aliens = min(5 + self.state.wave_number, 8)

    def check_wave_completion(self):
        if self.state.wave_enemies <= 0 and len(self.aliens) == 0:
            self.start_new_wave()

    def game_loop(self):
        self.start_new_wave()  # Initialize first wave
        while self.state.lives > 0:
            self.handle_input()
            self.update()
            self.check_wave_completion()
            self.draw()

    def show_menu(self):
        menu_items = ["START", "UPGRADE", "SCORES"]
        selected = 0
        
        while True:
            thumby.display.fill(0)
            
            title = "NOVANAUT"
            title_x = (SCREEN_WIDTH - len(title) * 6) // 2
            self.title_flash_timer = (self.title_flash_timer + 1) % 30
            if self.title_flash_timer < 20:
                thumby.display.drawText(title, title_x, 4, 1)
            
            for i, item in enumerate(menu_items):
                y = 15 + i * 8
                x = (SCREEN_WIDTH - len(item) * 6) // 2
                if i == selected:
                    thumby.display.drawRectangle(x - 2, y - 1, len(item) * 6 + 3, 9, 1)
                thumby.display.drawText(item, x, y, 1 if i != selected else 0)
            
            thumby.display.update()
            
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
            
            thumby.display.drawText("UPGRADES", 16, 0, 1)
            thumby.display.drawText(f"Credits: {self.state.credits}", 8, 8, 1)
            
            for i, (name, key) in enumerate(upgrades):
                y = 20 + i * 8
                level = self.state.upgrades[key]
                cost = UPGRADE_COST * (level + 1)
                
                if i == selected:
                    thumby.display.drawRectangle(0, y - 1, SCREEN_WIDTH, 9, 1)
                
                text = f"{name}: {level}/{MAX_UPGRADE_LEVEL} ({cost})"
                thumby.display.drawText(text, 2, y, 1 if i != selected else 0)
            
            thumby.display.drawText("B:BACK", 2, SCREEN_HEIGHT - 8, 1)
            thumby.display.update()
            
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
            
            thumby.display.drawText("B:MENU", 2, SCREEN_HEIGHT - 8, 1)
            
            thumby.display.update()
            
            if thumby.buttonB.justPressed():
                return

    def fire_bullet(self, charged=False):
        power = 1 + (self.state.upgrades['power'] * 0.5)
        is_multi = (self.state.current_powerup and 
                   self.state.current_powerup.type == 'MULTI')
        
        if charged:
            power *= 2
            if self.state.charge >= MAX_CHARGE or is_multi:
                angles = [-15, 0, 15]
                for angle in angles:
                    cos_angle = math.cos(math.radians(angle))
                    sin_angle = math.sin(math.radians(angle))
                    self.bullets.append({
                        'x': self.player.x + 11,
                        'y': self.player.y + 5,
                        'dx': cos_angle * 3,
                        'dy': sin_angle,
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
                self.bullets.extend([
                    {
                        'x': self.player.x + 11,
                        'y': self.player.y + 3,
                        'dx': 2,
                        'dy': 0,
                        'power': power
                    },
                    {
                        'x': self.player.x + 11,
                        'y': self.player.y + 7,
                        'dx': 2,
                        'dy': 0,
                        'power': power
                    }
                ])
            else:
                self.bullets.append({
                    'x': self.player.x + 11,
                    'y': self.player.y + 5,
                    'dx': 2,
                    'dy': 0,
                    'power': power
                })
        
        thumby.audio.play(1000 if charged else 800, 50)

    def draw(self):
        thumby.display.fill(0)
        
        # Calculate shake offset once for efficiency
        shake_x = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY) if self.state.shake_frames > 0 else 0
        shake_y = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY) if self.state.shake_frames > 0 else 0
        
        # Draw background elements
        self.draw_stars()
        self.particles.draw()
        
        # Draw game elements with screen shake
        for bullet in self.bullets:
            x = int(bullet['x']) + shake_x
            y = int(bullet['y']) + shake_y
            if 0 <= x < SCREEN_WIDTH-3 and 0 <= y < SCREEN_HEIGHT-2:
                thumby.display.drawFilledRectangle(x, y, 3, 2, 1)
        
        for alien in self.aliens:
            x = int(alien['x']) + shake_x
            y = int(alien['y']) + shake_y
            if -8 <= x < SCREEN_WIDTH and -8 <= y < SCREEN_HEIGHT:
                alien['sprite'].x = x
                alien['sprite'].y = y
                thumby.display.drawSprite(alien['sprite'])
        
        # Draw player with bounds checking
        player_x = self.player.x + shake_x
        player_y = self.player.y + shake_y
        if -13 <= player_x < SCREEN_WIDTH and -11 <= player_y < SCREEN_HEIGHT:
            self.player.x = player_x
            self.player.y = player_y
            thumby.display.drawSprite(self.player)
            self.player.x = player_x - shake_x
            self.player.y = player_y - shake_y
        
        # Draw UI elements
        self.draw_shield()
        self.draw_charge_bar()
        self.draw_powerups()
        self.draw_powerup_indicator()
        self.draw_combo_indicator()
        self.draw_wave_announcement()
        self.draw_floating_texts()
        self.draw_hud()
        self.draw_heat_gauge()
        
        if self.state.flash_frames > 0:
            self.draw_flash_effect()
        
        thumby.display.update()

    def run(self):
        while True:
            action = self.show_menu()
            
            if action == "START":
                self.state.reset()
                self.setup_game()
                self.game_loop()
                self.show_game_over()
            elif action == "UPGRADE":
                self.show_upgrade_menu()
            elif action == "SCORES":
                self.show_scores()

# Start the game with error handling
if __name__ == "__main__":
    try:
        game = NovaNaut()
        game.run()
    except Exception as e:
        thumby.display.fill(0)
        thumby.display.drawText("ERROR:", 0, 0, 1)
        msg = str(e)[:36]  # Limit error message length
        for i in range(0, len(msg), 12):
            thumby.display.drawText(msg[i:i+12], 0, 10 + (i // 12) * 8, 1)
        thumby.display.update()
        time.sleep(5)
        raise
