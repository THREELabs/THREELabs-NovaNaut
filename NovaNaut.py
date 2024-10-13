import thumby
import random
import time
import math

# Constants
STAR_LAYERS = 3
MAX_ALIENS = 5
MAX_CHARGE = 60

# Musical notes
C4 = 262
D4 = 294
E4 = 330
F4 = 349
G4 = 392
A4 = 440
B4 = 494
C5 = 523

# Simple background melody
background_melody = [
    (C4, 200), (E4, 200), (G4, 200), (C5, 200),
    (B4, 200), (G4, 200), (E4, 200), (C4, 200)
]

# Bitmaps
playerMap = bytearray([16,8,4,60,194,74,66,74,194,60,4,8,16,0,0,0,0,1,0,0,0,1,0,0,0,0])
bulletMap = bytearray([5,7,5])
alienMap = bytearray([36,24,126,90,255,90,36,102])
explosionMaps = [
    bytearray([0,36,24,60,60,24,36,0]),
    bytearray([0,66,60,126,126,60,66,0]),
    bytearray([66,129,195,231,231,195,129,66]),
    bytearray([129,66,36,24,24,36,66,129])
]
bossMap = bytearray([0,0,60,126,255,255,255,255,255,255,255,255,126,60,0,0,0,60,255,255,255,255,255,255,255,255,255,255,255,255,60,0])
miniBossMap = bytearray([0,60,126,255,255,255,255,255,255,126,60,0,60,255,255,255,255,255,255,255,255,255,255,60])
inkMap = bytearray([24,60,126,255,255,126,60,24])
starMap = bytearray([0,0,20,42,127,42,20,0])
spaceJellyMap = bytearray([60,126,255,255,60,36,36,24])
cosmicRayMap = bytearray([63,127,255,255,255,255,255,255,255,255,127,63])
quantumAnomalyMap = bytearray([24,60,126,255,255,255,255,126,60,24,60,126,255,255,255,255,126,60,24,0])
rapidFireMap = bytearray([60,126,255,189,189,255,126,60])
speedBoostMap = bytearray([24,60,126,219,219,126,60,24])
invincibilityMap = bytearray([66,165,153,165,153,165,153,66])

# Game state variables
score = 0
high_score = 0
lives = 3
level = 1
bombs = 3
charge_level = 0
shield_active = False
shield_hits = 0
scroll_speed = 1
game_mode = "normal"
boss_active = False
boss_health = 10
boss_spawn_time = 20  # seconds
game_start_time = time.time()
mini_bosses_active = [False, False]
mini_boss_health = [5, 5]
ink_active = False
final_boss_active = False
final_boss_health = 20
cheat_active = False
cheat_timer = 0
bulletActive = False

# Initialize empty lists
starLayers = [[] for _ in range(STAR_LAYERS)]
explosions = [{'active': False, 'frame': 0, 'x': 0, 'y': 0, 'timer': 0} for _ in range(5)]
active_power_ups = []

# Create sprites
playerSprite = thumby.Sprite(13, 9, playerMap)
bulletSprite = thumby.Sprite(3, 3, bulletMap)
bossSprite = thumby.Sprite(16, 16, bossMap)
miniBossSprites = [thumby.Sprite(12, 12, miniBossMap) for _ in range(2)]
inkSprite = thumby.Sprite(8, 8, inkMap)
starSprite = thumby.Sprite(8, 8, starMap)
spaceJellySprite = thumby.Sprite(8, 8, spaceJellyMap)
cosmicRaySprite = thumby.Sprite(12, 3, cosmicRayMap)
quantumAnomalySprite = thumby.Sprite(10, 10, quantumAnomalyMap)
rapidFireSprite = thumby.Sprite(8, 8, rapidFireMap)
speedBoostSprite = thumby.Sprite(8, 8, speedBoostMap)
invincibilitySprite = thumby.Sprite(8, 8, invincibilityMap)

# Alien sprites
alienSprites = [thumby.Sprite(8, 8, alienMap) for _ in range(MAX_ALIENS)]

# Power-ups
power_ups = [
    {'sprite': rapidFireSprite, 'duration': 10, 'type': 'rapid_fire'},
    {'sprite': speedBoostSprite, 'duration': 15, 'type': 'speed_boost'},
    {'sprite': invincibilitySprite, 'duration': 5, 'type': 'invincibility'}
]

# Achievements
achievements = {
    "First Blood": {"description": "Destroy your first alien", "achieved": False},
    "Bomb Squad": {"description": "Use your first bomb", "achieved": False},
    "Boss Slayer": {"description": "Defeat your first boss", "achieved": False},
    "Power Up": {"description": "Collect your first power-up", "achieved": False},
    "Survivor": {"description": "Reach level 5", "achieved": False}
}

thumby.display.setFPS(60)

def create_stars():
    global starLayers, STAR_LAYERS
    starLayers = [[] for _ in range(STAR_LAYERS)]
    for layer in range(STAR_LAYERS):
        for _ in range(5 - layer):  # Fewer stars in closer layers
            starLayers[layer].append({
                'x': random.randint(0, 71),
                'y': random.randint(0, 39)
            })

def update_stars():
    global scroll_speed
    for layer in range(STAR_LAYERS):
        speed = (layer + 1) * scroll_speed
        for star in starLayers[layer]:
            star['x'] -= speed
            if star['x'] < 0:
                star['x'] = 71
                star['y'] = random.randint(0, 39)

def draw_stars():
    for layer in range(STAR_LAYERS):
        for star in starLayers[layer]:
            thumby.display.setPixel(int(star['x']), int(star['y']), 1)

def spawn_alien():
    for alien in alienSprites:
        if alien.x <= -10:
            alien.x, alien.y = 72, random.randint(5, 25)
            return

def check_collision(sprite1, sprite2):
    return (abs(sprite1.x - sprite2.x) < max(sprite1.width, sprite2.width) // 2 and
            abs(sprite1.y - sprite2.y) < max(sprite1.height, sprite2.height) // 2)

def start_explosion(x, y):
    for explosion in explosions:
        if not explosion['active']:
            explosion['active'], explosion['frame'] = True, 0
            explosion['x'], explosion['y'], explosion['timer'] = int(x), int(y), 0
            break

def update_explosions():
    for explosion in explosions:
        if explosion['active']:
            explosion['timer'] += 1
            if explosion['timer'] >= 5:
                explosion['frame'] += 1
                explosion['timer'] = 0
                if explosion['frame'] >= len(explosionMaps):
                    explosion['active'] = False

def draw_pulsating_shield():
    if shield_active:
        t = time.time() * 10  # Get current time in tenths of a second
        size = int(3 + math.sin(t) * 2)  # Pulsate between size 1 and 5
        center_x = int(playerSprite.x + playerSprite.width // 2)
        center_y = int(playerSprite.y + playerSprite.height // 2)
        for i in range(8):
            angle = i * math.pi / 4
            x = int(center_x + math.cos(angle) * size)
            y = int(center_y + math.sin(angle) * size)
            if 0 <= x < 72 and 0 <= y < 40:
                thumby.display.setPixel(x, y, 1)

def update_high_score(score):
    global high_score
    if score > high_score:
        high_score = score
        save_high_score(high_score)
        thumby.display.fill(0)
        thumby.display.drawText("New High", 10, 0, 1)
        thumby.display.drawText("Score!: " + str(high_score), 7, 10, 1)
        thumby.display.update()
        time.sleep(2)

def save_high_score(score):
    with open("/high_score.txt", "w") as f:
        f.write(str(score))

def load_high_score():
    try:
        with open("/high_score.txt", "r") as f:
            return int(f.read())
    except:
        return 0

high_score = load_high_score()

prev_button_a_state = False
def button_a_just_pressed():
    global prev_button_a_state
    current_state = thumby.buttonA.pressed()
    if current_state and not prev_button_a_state:
        prev_button_a_state = current_state
        return True
    prev_button_a_state = current_state
    return False

frame_count = 0
def update_frame_count():
    global frame_count
    frame_count += 1
    
def spawn_boss():
    global boss_active, boss_health
    bossSprite.x, bossSprite.y = 48, random.randint(0, 24)
    boss_active, boss_health = True, 10 + (level * 5)  # Boss health increases with level

def update_boss():
    global boss_active, boss_health, score, ink_active, bulletActive
    if boss_active:
        bossSprite.x += random.randint(-1, 1)
        bossSprite.y += random.randint(-1, 1)
        bossSprite.x = max(16, min(bossSprite.x, 56))
        bossSprite.y = max(0, min(bossSprite.y, 24))
        
        if random.randint(1, 60) == 1 and not ink_active:
            ink_active = True
            inkSprite.x, inkSprite.y = bossSprite.x, bossSprite.y + 8
        
        if bulletActive and check_collision(bossSprite, bulletSprite):
            boss_health -= bulletSprite.power
            score += 5 * bulletSprite.power
            play_hit_sound()
            if boss_health <= 0:
                boss_active = False
                spawn_mini_bosses()
                score += 100

def spawn_mini_bosses():
    global mini_bosses_active, mini_boss_health
    for i in range(2):
        miniBossSprites[i].x = random.randint(40, 60)
        miniBossSprites[i].y = random.randint(10, 30)
        mini_bosses_active[i], mini_boss_health[i] = True, 5
        
def update_mini_bosses():
    global mini_bosses_active, mini_boss_health, score, bulletActive
    for i in range(2):
        if mini_bosses_active[i]:
            miniBossSprites[i].x += random.randint(-1, 1)
            miniBossSprites[i].y += random.randint(-1, 1)
            miniBossSprites[i].x = max(0, min(miniBossSprites[i].x, 60))
            miniBossSprites[i].y = max(0, min(miniBossSprites[i].y, 28))
            
            if bulletActive and check_collision(miniBossSprites[i], bulletSprite):
                mini_boss_health[i] -= bulletSprite.power
                score += 10 * bulletSprite.power
                play_hit_sound()
                if mini_boss_health[i] <= 0:
                    mini_bosses_active[i] = False
                    score += 25
                    if not any(mini_bosses_active):
                        level_complete()

def level_complete():
    global level, scroll_speed, game_mode
    level += 1
    scroll_speed = min(scroll_speed + 0.5, 3)  # Increase scroll speed, max 3
    for _ in range(5):
        thumby.display.fill(0)
        thumby.display.drawText("LEVEL", random.randint(0, 4), random.randint(10, 14), 1)
        thumby.display.drawText(f"{level-1}", random.randint(0, 4), random.randint(20, 24), 1)
        thumby.display.drawText("COMPLETE!", random.randint(0, 4), random.randint(30, 34), 1)
        thumby.display.update()
        time.sleep(0.1)
    time.sleep(2)
    play_level_complete_sound()
    
    stories = [
        "As you venture\ndeeper into\nspace, strange\nanomalies\nappear ahead.\nPrepare for\nunknown dangers!",
        "The anomalies\nreveal a hidden\nwormhole. You're\npulled into a\nnew galaxy!\nWhat awaits?",
        "A distress call\nechoes through\nspace. A nearby\nplanet needs\nyour help!\nBattle awaits.",
        "The final\nfrontier looms.\nAn alien armada\napproaches.\nDefend Earth\nat all costs!",
        "Victory! Earth\nis safe, but\nnew adventures\nbeckons. Ready\nfor the next\nchallenge?",
        "Entering dense\nasteroid field.\nWatch out for\nspace rocks!",
        "A wormhole\nappears! Navigate\nthrough distorted\nspace-time.",
        "The alien\nmothership\napproaches. Get\nready for the\nfinal battle!"
    ]
    
    if level <= len(stories):
        show_scrolling_story(stories[level-1])
    
    game_modes = ["normal", "spread_shot", "laser", "homing_missile", "normal", "asteroid_field", "wormhole", "alien_mothership"]
    if level <= len(game_modes):
        game_mode = game_modes[level-1]
    
    generate_level(level)

def generate_level(level):
    global boss_spawn_time, MAX_ALIENS, game_start_time
    boss_spawn_time = 20 + (level * 10)  # Increase time before boss spawn
    MAX_ALIENS = 5 + level  # Increase number of aliens
    game_start_time = time.time()  # Reset the game start time for the new level

def spawn_final_boss():
    global final_boss_active, final_boss_health
    final_boss_active = True
    final_boss_health = 30 + (level * 10)
    bossSprite.x, bossSprite.y = 48, 20

def update_final_boss():
    global final_boss_active, final_boss_health, score, running, ink_active, bulletActive
    if final_boss_active:
        bossSprite.x += random.randint(-2, 2)
        bossSprite.y += random.randint(-2, 2)
        bossSprite.x = max(16, min(bossSprite.x, 56))
        bossSprite.y = max(0, min(bossSprite.y, 32))
        
        if random.randint(1, 30) == 1 and not ink_active:
            ink_active = True
            inkSprite.x, inkSprite.y = bossSprite.x, bossSprite.y + 8
        
        if bulletActive and check_collision(bossSprite, bulletSprite):
            final_boss_health -= bulletSprite.power
            score += 10 * bulletSprite.power
            play_hit_sound()
            if final_boss_health <= 0:
                final_boss_active = False
                for _ in range(10):  # Screen flash
                    thumby.display.fill(random.randint(0, 1))
                    thumby.display.update()
                    time.sleep(0.1)
                thumby.display.fill(0)
                thumby.display.drawText(f"LEVEL {level}", 10, 16, 1)
                thumby.display.drawText("COMPLETE!", 5, 24, 1)
                thumby.display.update()
                time.sleep(2)
                level_complete()

def shoot_bullet(power=1):
    global bulletActive, bulletSprite
    bulletActive = True
    bulletSprite.x = playerSprite.x + playerSprite.width // 2
    bulletSprite.y = playerSprite.y + playerSprite.height // 2
    bulletSprite.angle = 0
    bulletSprite.power = power  # Store the power level in the bullet sprite
    play_shoot_sound(power)

def shoot_spread():
    global bulletActive, bulletSprite
    angles = [-15, 0, 15]
    for angle in angles:
        bulletActive = True
        bulletSprite.x = playerSprite.x + playerSprite.width // 2
        bulletSprite.y = playerSprite.y + playerSprite.height // 2
        bulletSprite.angle = angle
        bulletSprite.power = 2  # Spread shots are more powerful
        play_shoot_sound(2)

def handle_player_hit():
    global lives, shield_active, shield_hits
    if shield_active:
        shield_hits += 1
        if shield_hits >= 3:
            shield_active = False
    else:
        lives -= 1
        play_hit_sound()

def activate_bomb():
    global bombs, score
    if bombs > 0:
        bombs -= 1
        for alien in alienSprites:
            if alien.x > -10:
                score += 10
                start_explosion(alien.x, alien.y)
                alien.x = -10
        if spaceJellySprite.x > -10:
            score += 15
            start_explosion(spaceJellySprite.x, spaceJellySprite.y)
            spaceJellySprite.x = -10
        if cosmicRaySprite.x > -12:
            score += 20
            start_explosion(cosmicRaySprite.x, cosmicRaySprite.y)
            cosmicRaySprite.x = -12
        if quantumAnomalySprite.x > -10:
            score += 25
            start_explosion(quantumAnomalySprite.x, quantumAnomalySprite.y)
            quantumAnomalySprite.x = -10
        play_explosion_sound()

def spawn_power_up():
    if random.randint(1, 500) == 1 and not any(pu['sprite'].x > -10 for pu in power_ups):
        power_up = random.choice(power_ups)
        power_up['sprite'].x = 72
        power_up['sprite'].y = random.randint(5, 35)

def update_power_ups():
    global active_power_ups
    for power_up in power_ups:
        if power_up['sprite'].x > -10:
            power_up['sprite'].x -= 1
            if check_collision(power_up['sprite'], playerSprite):
                active_power_ups.append({
                    'type': power_up['type'],
                    'duration': power_up['duration'] * 60  # Convert to frames
                })
                power_up['sprite'].x = -10
                play_powerup_sound()

    active_power_ups = [pu for pu in active_power_ups if pu['duration'] > 0]
    for power_up in active_power_ups:
        power_up['duration'] -= 1

def is_power_up_active(power_up_type):
    return any(pu['type'] == power_up_type for pu in active_power_ups)

def apply_power_ups():
    global playerSprite
    if is_power_up_active('speed_boost'):
        playerSprite.x += 1 if thumby.buttonR.pressed() else -1 if thumby.buttonL.pressed() else 0
        playerSprite.y += 1 if thumby.buttonD.pressed() else -1 if thumby.buttonU.pressed() else 0
    if is_power_up_active('invincibility'):
        # Make the player sprite blink
        if frame_count % 4 < 2:
            thumby.display.drawSprite(playerSprite)
            
def spawn_unique_monster():
    global spaceJellySprite, cosmicRaySprite, quantumAnomalySprite
    monster_type = random.choice(['jellyfish', 'cosmic_ray', 'quantum_anomaly'])
    if monster_type == 'jellyfish' and spaceJellySprite.x <= -10:
        spaceJellySprite.x, spaceJellySprite.y = 72, random.randint(5, 35)
    elif monster_type == 'cosmic_ray' and cosmicRaySprite.x <= -12:
        cosmicRaySprite.x, cosmicRaySprite.y = 72, random.randint(5, 37)
    elif monster_type == 'quantum_anomaly' and quantumAnomalySprite.x <= -10:
        quantumAnomalySprite.x, quantumAnomalySprite.y = 72, random.randint(5, 30)

def update_space_jellyfish():
    global spaceJellySprite, score, bulletActive
    if spaceJellySprite.x > -10:
        spaceJellySprite.x -= 1.5
        spaceJellySprite.y += math.sin(spaceJellySprite.x * 0.1) * 0.5
        if check_collision(spaceJellySprite, playerSprite):
            handle_player_hit()
            spaceJellySprite.x = -10
        elif bulletActive and check_collision(spaceJellySprite, bulletSprite):
            score += 15 * bulletSprite.power
            start_explosion(spaceJellySprite.x, spaceJellySprite.y)
            spaceJellySprite.x = -10
            bulletActive = False

def update_cosmic_ray():
    global cosmicRaySprite, score, bulletActive
    if cosmicRaySprite.x > -12:
        cosmicRaySprite.x -= 2
        if check_collision(cosmicRaySprite, playerSprite):
            handle_player_hit()
            cosmicRaySprite.x = -12
        elif bulletActive and check_collision(cosmicRaySprite, bulletSprite):
            score += 20 * bulletSprite.power
            start_explosion(cosmicRaySprite.x, cosmicRaySprite.y)
            cosmicRaySprite.x = -12
            bulletActive = False

def update_quantum_anomaly():
    global quantumAnomalySprite, score, bulletActive
    if quantumAnomalySprite.x > -10:
        quantumAnomalySprite.x -= 1
        quantumAnomalySprite.y += random.randint(-1, 1)
        quantumAnomalySprite.y = max(0, min(quantumAnomalySprite.y, 30))
        if check_collision(quantumAnomalySprite, playerSprite):
            handle_player_hit()
            quantumAnomalySprite.x = -10
        elif bulletActive and check_collision(quantumAnomalySprite, bulletSprite):
            score += 25 * bulletSprite.power
            start_explosion(quantumAnomalySprite.x, quantumAnomalySprite.y)
            quantumAnomalySprite.x = -10
            bulletActive = False

def check_achievements():
    global score, bombs, level
    
    if score >= 10 and not achievements["First Blood"]["achieved"]:
        unlock_achievement("First Blood")
    
    if bombs < 3 and not achievements["Bomb Squad"]["achieved"]:
        unlock_achievement("Bomb Squad")
    
    if level > 1 and not achievements["Boss Slayer"]["achieved"]:
        unlock_achievement("Boss Slayer")
    
    if any(pu['sprite'].x <= -10 for pu in power_ups) and not achievements["Power Up"]["achieved"]:
        unlock_achievement("Power Up")
    
    if level >= 5 and not achievements["Survivor"]["achieved"]:
        unlock_achievement("Survivor")

def unlock_achievement(achievement_name):
    achievements[achievement_name]["achieved"] = True
    display_achievement(achievement_name)

def display_achievement(achievement_name):
    thumby.display.fill(0)
    thumby.display.drawText("Achievement!", 0, 0, 1)
    thumby.display.drawText(achievement_name, 0, 10, 1)
    thumby.display.drawText(achievements[achievement_name]["description"], 0, 20, 1)
    thumby.display.update()
    play_achievement_sound()
    time.sleep(2)

def show_scrolling_story(story):
    lines = story.split('\n')
    y_pos = 40
    while y_pos > -len(lines) * 8:
        thumby.display.fill(0)
        for i, line in enumerate(lines):
            thumby.display.drawText(line, 0, y_pos + i * 8, 1)
        thumby.display.update()
        y_pos -= 1
        time.sleep(0.1)




def pause_menu():
    menu_items = ["Resume", "Restart", "Quit"]
    selected_item = 0
    
    while True:
        thumby.display.fill(0)
        thumby.display.drawText("PAUSED", 15, 0, 1)
        
        for i, item in enumerate(menu_items):
            if i == selected_item:
                thumby.display.drawText("> " + item, 5, 10 + i * 10, 1)
            else:
                thumby.display.drawText("  " + item, 5, 10 + i * 10, 1)
        
        thumby.display.update()
        
        if thumby.buttonU.justPressed():
            selected_item = (selected_item - 1) % len(menu_items)
        elif thumby.buttonD.justPressed():
            selected_item = (selected_item + 1) % len(menu_items)
        elif button_a_just_pressed():
            if selected_item == 0:  # Resume
                return "resume"
            elif selected_item == 1:  # Restart
                return "restart"
            else:  # Quit
                return "quit"
        
        time.sleep(0.1)

# Sound functions
def play_background_music():
    for note, duration in background_melody:
        thumby.audio.play(note, duration)
        time.sleep(duration / 1000)  # Convert milliseconds to seconds

def play_shoot_sound(power):
    frequency = 1000 + power * 200
    thumby.audio.play(frequency, 50)

def play_explosion_sound():
    for freq in range(500, 100, -100):
        thumby.audio.play(freq, 50)

def play_powerup_sound():
    for freq in range(1000, 2000, 200):
        thumby.audio.play(freq, 50)
        time.sleep(0.05)

def play_hit_sound():
    thumby.audio.play(200, 200)

def play_level_complete_sound():
    for _ in range(3):
        thumby.audio.play(800, 100)
        time.sleep(0.1)
        thumby.audio.play(1000, 100)
        time.sleep(0.1)

def play_achievement_sound():
    notes = [523, 659, 784]  # C5, E5, G5
    for note in notes:
        thumby.audio.play(note, 100)
        time.sleep(0.1)

def play_cheat_melody():
    notes = [523, 587, 659, 698, 784]  # C5, D5, E5, F5, G5
    for note in notes:
        thumby.audio.play(note, 100)
        time.sleep(0.1)
        
def reset_game():
    global score, lives, level, bombs, charge_level, shield_active, shield_hits
    global scroll_speed, game_mode, boss_active, boss_health, game_start_time
    global mini_bosses_active, mini_boss_health, ink_active, final_boss_active
    global final_boss_health, cheat_active, cheat_timer, bulletActive

    score = 0
    lives = 3
    level = 1
    bombs = 3
    charge_level = 0
    shield_active = False
    shield_hits = 0
    scroll_speed = 1
    game_mode = "normal"
    boss_active = False
    boss_health = 10
    game_start_time = time.time()
    mini_bosses_active = [False, False]
    mini_boss_health = [5, 5]
    ink_active = False
    final_boss_active = False
    final_boss_health = 20
    cheat_active = False
    cheat_timer = 0
    bulletActive = False

    playerSprite.x, playerSprite.y = 5, 30
    bulletSprite.x, bulletSprite.y = -10, -10

def show_title_screen():
    thumby.display.fill(0)
    thumby.display.drawText("Nova", 15, 8, 1)
    thumby.display.drawText("Naut", 16, 18, 1)
    thumby.display.drawText("Press A", 10, 30, 1)
    thumby.display.update()
    while not button_a_just_pressed():
        pass
    time.sleep(0.2)  # Debounce

def game_over():
    global score, high_score
    update_high_score(score)
    thumby.display.fill(0)
    thumby.display.drawText("GAME OVER", 5, 10, 1)
    thumby.display.drawText(f"Score: {score}", 5, 20, 1)
    thumby.display.drawText(f"High: {high_score}", 5, 30, 1)
    thumby.display.update()
    time.sleep(3)

def game_loop():
    global lives, charge_level, bulletActive, score, cheat_timer, frame_count

    while lives > 0:
        update_frame_count()
        thumby.display.fill(0)

        # Update and draw stars
        update_stars()
        draw_stars()

        # Cheat code activation
        if thumby.buttonL.pressed():
            cheat_timer += 1
            if cheat_timer >= 600 and not cheat_active:  # 10 seconds at 60 FPS
                cheat_active = True
                play_cheat_melody()
        else:
            cheat_timer = 0

        # Player movement
        if thumby.buttonU.pressed() and playerSprite.y > 0:
            playerSprite.y -= 1
        if thumby.buttonD.pressed() and playerSprite.y < 31:
            playerSprite.y += 1
        if thumby.buttonL.pressed() and playerSprite.x > 0:
            playerSprite.x -= 1
        if thumby.buttonR.pressed() and playerSprite.x < 59:
            playerSprite.x += 1

        # Shooting and bomb activation
        if thumby.buttonA.pressed():
            charge_level = min(charge_level + 1, MAX_CHARGE)
        elif charge_level > 0:  # Button released and we have some charge
            if charge_level >= MAX_CHARGE:  # Fully charged shot
                shoot_spread()
            elif charge_level > MAX_CHARGE // 2:  # Medium charge
                shoot_bullet(power=2)
            else:  # Low charge
                shoot_bullet(power=1)
            charge_level = 0  # Reset charge after shooting
        
        if thumby.buttonB.justPressed():
            activate_bomb()

        # Pause menu
        if thumby.buttonB.justPressed():
            pause_result = pause_menu()
            if pause_result == "restart":
                reset_game()
                return
            elif pause_result == "quit":
                return

        # Bullet movement
        if bulletActive:
            bulletSprite.x += 2 * bulletSprite.power
            bulletSprite.y -= 2 * math.sin(math.radians(bulletSprite.angle))
            if bulletSprite.x > 72 or bulletSprite.x < 0 or bulletSprite.y > 40 or bulletSprite.y < 0:
                bulletActive = False

        # Check if it's time to spawn the boss
        if not boss_active and not any(mini_bosses_active) and not final_boss_active and time.time() - game_start_time >= boss_spawn_time:
            if level == 8:
                spawn_final_boss()
            else:
                spawn_boss()

        # Update boss and mini-bosses
        if final_boss_active:
            update_final_boss()
        elif boss_active:
            update_boss()
        elif any(mini_bosses_active):
            update_mini_bosses()
        else:
            # Alien spawning and movement
            if random.randint(1, 60) == 1:
                spawn_alien()
            
            for alien in alienSprites:
                if alien.x > -10:
                    alien.x -= 1
                    if check_collision(alien, playerSprite):
                        handle_player_hit()
                        alien.x = -10
                    elif bulletActive and check_collision(alien, bulletSprite):
                        score += 10 * bulletSprite.power
                        start_explosion(alien.x, alien.y)
                        play_explosion_sound()
                        alien.x = -10
                        bulletActive = False

        # Update unique monsters
        if random.randint(1, 120) == 1:
            spawn_unique_monster()
        
        update_space_jellyfish()
        update_cosmic_ray()
        update_quantum_anomaly()

        # Update explosions
        update_explosions()

        # Spawn and update power-ups
        spawn_power_up()
        update_power_ups()
        apply_power_ups()

        # Check achievements
        check_achievements()

        # Draw sprites
        thumby.display.drawSprite(playerSprite)
        
        if bulletActive:
            thumby.display.drawSprite(bulletSprite)
        
        if final_boss_active or boss_active:
            thumby.display.drawSprite(bossSprite)
        elif any(mini_bosses_active):
            for i, active in enumerate(mini_bosses_active):
                if active:
                    thumby.display.drawSprite(miniBossSprites[i])
        else:
            for alien in alienSprites:
                if alien.x > -10:
                    thumby.display.drawSprite(alien)

        if ink_active:
            thumby.display.drawSprite(inkSprite)

        for power_up in power_ups:
            if power_up['sprite'].x > -10:
                thumby.display.drawSprite(power_up['sprite'])

        if spaceJellySprite.x > -10:
            thumby.display.drawSprite(spaceJellySprite)
        if cosmicRaySprite.x > -12:
            thumby.display.drawSprite(cosmicRaySprite)
        if quantumAnomalySprite.x > -10:
            thumby.display.drawSprite(quantumAnomalySprite)

        # Draw shield
        draw_pulsating_shield()

        # Draw explosions
        for explosion in explosions:
            if explosion['active']:
                thumby.display.blit(explosionMaps[explosion['frame']], 
                                    int(explosion['x']), int(explosion['y']), 
                                    8, 8, -1, 0, 0)

        # Draw charge bar
        charge_width = (charge_level * 72) // MAX_CHARGE
        thumby.display.drawLine(0, 39, charge_width, 39, 1)

        # Draw score, lives, level, and bombs
        thumby.display.drawText(f"S:{score} L:{lives} Lv:{level} B:{bombs}", 0, 0, 1)

        # Draw boss or mini-boss health
        if final_boss_active:
            thumby.display.drawText(f"FB:{final_boss_health}", 0, 8, 1)
        elif boss_active:
            thumby.display.drawText(f"B:{boss_health}", 0, 8, 1)
        elif any(mini_bosses_active):
            thumby.display.drawText(f"M1:{mini_boss_health[0]} M2:{mini_boss_health[1]}", 0, 8, 1)

        thumby.display.update()

        # Add a small delay to control the game speed
        time.sleep(0.016)  # Approximately 60 FPS

    game_over()

# Main game execution
while True:
    reset_game()
    show_title_screen()
    create_stars()
    
    game_loop()
    
    # Ask if the player wants to play again
    thumby.display.fill(0)
    thumby.display.drawText("Play Again?", 5, 15, 1)
    thumby.display.drawText("A: Yes B: No", 5, 25, 1)
    thumby.display.update()
    
    while True:
        if button_a_just_pressed():
            break
        elif thumby.buttonB.justPressed():
            # Exit to main menu or turn off the device
            thumby.reset()
        time.sleep(0.1)

# Clean up and exit
thumby.display.fill(1)
thumby.display.drawText("Thanks for", 0, 16, 0)
thumby.display.drawText("playing!", 0, 24, 0)
thumby.display.update()
time.sleep(2)
