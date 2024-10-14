import thumby
import random
import time
import math

# Constants
STAR_LAYERS = 3
MAX_ALIENS = 5
MAX_CHARGE = 60
BOSS_SPAWN_TIME = 10
POWER_UP_CHANCE = 1000
CHEAT_CODE = [thumby.buttonU, thumby.buttonU, thumby.buttonD, thumby.buttonD, thumby.buttonL, thumby.buttonR, thumby.buttonL, thumby.buttonR, thumby.buttonB, thumby.buttonA, thumby.buttonB, thumby.buttonA]
UPGRADE_COST = 100
MAX_UPGRADE_LEVEL = 3
ASTEROID_SPAWN_CHANCE = 100
POWER_DOWN_CHANCE = 500
FLASH_INTERVAL = 10  # Frames between flashes

# Musical notes
C4, D4, E4, F4, G4, A4, B4, C5 = 262, 294, 330, 349, 392, 440, 494, 523

# Bitmaps
playerMap = bytearray([16,8,4,60,194,74,66,74,194,60,4,8,16,0,0,0,0,1,0,0,0,1,0,0,0,0])
bulletMap = bytearray([5,7,5])
alienMap = bytearray([36,24,126,90,255,90,36,102])
fastAlienMap = bytearray([60,126,219,255,255,219,126,60])
shieldedAlienMap = bytearray([60,126,219,255,255,219,126,60])
explosionMaps = [
    bytearray([0,36,24,60,60,24,36,0]),
    bytearray([0,66,60,126,126,60,66,0]),
    bytearray([66,129,195,231,231,195,129,66]),
    bytearray([129,66,36,24,24,36,66,129])
]
bossMap = bytearray([0,0,60,126,255,255,255,255,255,255,255,255,126,60,0,0,0,60,255,255,255,255,255,255,255,255,255,255,255,255,60,0])
bossBulletMap = bytearray([60,126,126,60])
healthItemMap = bytearray([24,60,126,126,126,60,24,0])
asteroidMap = bytearray([60,126,255,255,255,255,126,60])

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
game_start_time = time.time()
cheat_active = False
cheat_index = 0
bulletActive = False
difficulty = 1
ship_speed_level = 0
ship_fire_rate_level = 0
ship_shield_level = 0
credits = 0
boss_phase = 1
asteroid_field_active = False
frame_count = 0

# Initialize empty lists
starLayers = [[] for _ in range(STAR_LAYERS)]
explosions = [{'active': False, 'frame': 0, 'x': 0, 'y': 0, 'timer': 0} for _ in range(5)]
active_power_ups = []
boss_bullets = []
health_items = []
bullets = []

# Create sprites
playerSprite = thumby.Sprite(13, 9, playerMap)
bulletSprite = thumby.Sprite(3, 3, bulletMap)
bossSprite = thumby.Sprite(16, 16, bossMap)
bossBulletSprite = thumby.Sprite(4, 4, bossBulletMap)
healthItemSprite = thumby.Sprite(8, 8, healthItemMap)
asteroidSprite = thumby.Sprite(8, 8, asteroidMap)

# Alien sprites
alienSprites = [thumby.Sprite(8, 8, alienMap) for _ in range(MAX_ALIENS)]
fastAlienSprites = [thumby.Sprite(8, 8, fastAlienMap) for _ in range(MAX_ALIENS // 2)]
shieldedAlienSprites = [thumby.Sprite(8, 8, shieldedAlienMap) for _ in range(MAX_ALIENS // 2)]

# Power-ups
power_ups = [
    {'sprite': thumby.Sprite(8, 8, bytearray([60,126,255,189,189,255,126,60])), 'duration': 10, 'type': 'rapid_fire'},
    {'sprite': thumby.Sprite(8, 8, bytearray([24,60,126,219,219,126,60,24])), 'duration': 15, 'type': 'speed_boost'},
    {'sprite': thumby.Sprite(8, 8, bytearray([66,165,153,165,153,165,153,66])), 'duration': 5, 'type': 'invincibility'}
]

# Storyline and mission objectives
story = [
    "Earth is under attack!",
    "Defend against aliens",
    "Destroy the mothership",
    "Save humanity!"
]

mission_objectives = [
    "Destroy 10 aliens",
    "Collect 3 power-ups",
    "Defeat the boss",
    "Survive for 2 minutes"
]

current_mission = 0
mission_progress = 0

thumby.display.setFPS(60)

def create_stars():
    global starLayers, STAR_LAYERS
    starLayers = [[] for _ in range(STAR_LAYERS)]
    for layer in range(STAR_LAYERS):
        for _ in range(5 - layer):
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

def spawn_fast_alien():
    for alien in fastAlienSprites:
        if alien.x <= -10:
            alien.x, alien.y = 72, random.randint(5, 25)
            return

def spawn_shielded_alien():
    for alien in shieldedAlienSprites:
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
        t = time.time() * 10
        size = int(3 + math.sin(t) * 2)
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

def spawn_boss():
    global boss_active, boss_health, boss_phase
    bossSprite.x, bossSprite.y = 48, random.randint(0, 24)
    boss_active, boss_health, boss_phase = True, 10 + (level * 5), 1

def update_boss():
    global boss_active, boss_health, score, bulletActive, boss_phase
    if boss_active:
        if boss_phase == 1:
            bossSprite.x += random.randint(-1, 1)
            bossSprite.y += random.randint(-1, 1)
        elif boss_phase == 2:
            bossSprite.x += math.sin(time.time() * 5) * 2
            bossSprite.y += math.cos(time.time() * 5) * 2
        elif boss_phase == 3:
            bossSprite.x += random.randint(-2, 2)
            bossSprite.y += random.randint(-2, 2)
        
        bossSprite.x = max(16, min(bossSprite.x, 56))
        bossSprite.y = max(0, min(bossSprite.y, 24))
        
        if random.randint(1, 60 // boss_phase) == 1:
            shoot_boss_bullet()
        
        for bullet in bullets:
            if check_collision(bossSprite, bullet['sprite']):
                boss_health -= bullet['power']
                score += 5 * bullet['power']
                play_hit_sound()
                bullet['active'] = False
                if boss_health <= 0:
                    if boss_phase < 3:
                        boss_phase += 1
                        boss_health = 10 + (level * 5) * boss_phase
                    else:
                        boss_defeated()

def boss_defeated():
    global boss_active, score
    boss_active = False
    score += 100
    for _ in range(10):
        thumby.display.fill(random.randint(0, 1))
        thumby.display.update()
        time.sleep(0.1)
    for _ in range(5):
        start_explosion(random.randint(0, 72), random.randint(0, 40))
    play_explosion_sound()

def shoot_boss_bullet():
    bullet = {'x': bossSprite.x, 'y': bossSprite.y + 8, 'active': True}
    boss_bullets.append(bullet)

def update_boss_bullets():
    global lives
    for bullet in boss_bullets:
        if bullet['active']:
            bullet['x'] -= 2
            if bullet['x'] < -4:
                bullet['active'] = False
            elif check_collision(playerSprite, bossBulletSprite):
                handle_player_hit()
                bullet['active'] = False

def shoot_bullet(power=1, spread=False):
    global bullets
    if spread:
        num_bullets = 10
        spread_angle = 30  # Total spread angle
        for i in range(num_bullets):
            angle = -spread_angle/2 + (spread_angle / (num_bullets-1)) * i
            bullet = {
                'sprite': thumby.Sprite(3, 3, bulletMap),
                'angle': angle,
                'power': power,
                'active': True
            }
            bullet['sprite'].x = playerSprite.x + playerSprite.width
            bullet['sprite'].y = playerSprite.y + playerSprite.height // 2
            bullets.append(bullet)
    else:
        bullet = {
            'sprite': thumby.Sprite(3, 3, bulletMap),
            'angle': 0,
            'power': power,
            'active': True
        }
        bullet['sprite'].x = playerSprite.x + playerSprite.width
        bullet['sprite'].y = playerSprite.y + playerSprite.height // 2
        bullets.append(bullet)
    
    play_shoot_sound(power)

def update_bullets():
    global bullets
    for bullet in bullets:
        if bullet['active']:
            bullet['sprite'].x += math.cos(math.radians(bullet['angle'])) * (2 * bullet['power'])
            bullet['sprite'].y += math.sin(math.radians(bullet['angle'])) * (2 * bullet['power'])
            if (bullet['sprite'].x > 72 or bullet['sprite'].x < 0 or 
                bullet['sprite'].y > 40 or bullet['sprite'].y < 0):
                bullet['active'] = False
    bullets = [b for b in bullets if b['active']]

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
        for alien in alienSprites + fastAlienSprites + shieldedAlienSprites:
            if alien.x > -10:
                score += 10
                start_explosion(alien.x, alien.y)
                alien.x = -10
        play_explosion_sound()

def spawn_power_up():
    if random.randint(1, POWER_UP_CHANCE) == 1 and not any(pu['sprite'].x > -10 for pu in power_ups):
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
                    'duration': power_up['duration'] * 60
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
        if frame_count % 4 < 2:
            thumby.display.drawSprite(playerSprite)

def spawn_health_item():
    if random.randint(1, 500) == 1 and len(health_items) < 3:
        health_items.append({'x': 72, 'y': random.randint(5, 35), 'active': True})

def update_health_items():
    global lives
    for item in health_items:
        if item['active']:
            item['x'] -= 1
            if item['x'] < -8:
                item['active'] = False
            elif check_collision(playerSprite, healthItemSprite):
                lives = min(lives + 1, 5)
                item['active'] = False
                play_health_pickup_sound()

def reset_game():
    global score, lives, level, bombs, charge_level, shield_active, shield_hits
    global scroll_speed, game_mode, boss_active, boss_health, game_start_time
    global cheat_active, cheat_index, bulletActive, difficulty, current_mission, mission_progress
    global ship_speed_level, ship_fire_rate_level, ship_shield_level, credits, boss_phase, asteroid_field_active
    global bullets, frame_count

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
    cheat_active = False
    cheat_index = 0
    bulletActive = False
    difficulty = 1
    current_mission = 0
    mission_progress = 0
    ship_speed_level = 0
    ship_fire_rate_level = 0
    ship_shield_level = 0
    credits = 0
    boss_phase = 1
    asteroid_field_active = False
    bullets = []
    frame_count = 0

    playerSprite.x, playerSprite.y = 5, 30
    bulletSprite.x, bulletSprite.y = -10, -10

    # Reset all enemy positions
    for alien in alienSprites + fastAlienSprites + shieldedAlienSprites:
        alien.x = -10

def upgrade_ship():
    global credits, ship_speed_level, ship_fire_rate_level, ship_shield_level

    thumby.display.fill(0)
    thumby.display.drawText("Upgrades:", 0, 0, 1)
    thumby.display.drawText(f"1.Speed: {ship_speed_level}", 0, 10, 1)
    thumby.display.drawText(f"2.Fire: {ship_fire_rate_level}", 0, 20, 1)
    thumby.display.drawText(f"3.Shield: {ship_shield_level}", 0, 30, 1)
    thumby.display.drawText(f"Credits: {credits}", 0, 40, 1)
    thumby.display.update()

    while True:
        if thumby.buttonU.justPressed():
            if credits >= UPGRADE_COST and ship_speed_level < MAX_UPGRADE_LEVEL:
                credits -= UPGRADE_COST
                ship_speed_level += 1
                break
        elif thumby.buttonL.justPressed():
            if credits >= UPGRADE_COST and ship_fire_rate_level < MAX_UPGRADE_LEVEL:
                credits -= UPGRADE_COST
                ship_fire_rate_level += 1
                break
        elif thumby.buttonD.justPressed():
            if credits >= UPGRADE_COST and ship_shield_level < MAX_UPGRADE_LEVEL:
                credits -= UPGRADE_COST
                ship_shield_level += 1
                break
        elif thumby.buttonB.justPressed():
            break

    time.sleep(0.2)

def spawn_asteroid():
    global asteroid_field_active
    if not asteroid_field_active and random.randint(1, ASTEROID_SPAWN_CHANCE) == 1:
        asteroid_field_active = True
        asteroidSprite.x = 72
        asteroidSprite.y = random.randint(0, 32)

def update_asteroid():
    global asteroid_field_active, lives
    if asteroid_field_active:
        asteroidSprite.x -= 1
        if asteroidSprite.x < -8:
            asteroid_field_active = False
        elif check_collision(asteroidSprite, playerSprite):
            handle_player_hit()
            asteroid_field_active = False

def apply_power_down():
    global ship_speed_level, ship_fire_rate_level, ship_shield_level
    if random.randint(1, POWER_DOWN_CHANCE) == 1:
        effect = random.choice(['speed', 'fire_rate', 'shield'])
        if effect == 'speed' and ship_speed_level > 0:
            ship_speed_level -= 1
        elif effect == 'fire_rate' and ship_fire_rate_level > 0:
            ship_fire_rate_level -= 1
        elif effect == 'shield' and ship_shield_level > 0:
            ship_shield_level -= 1
        play_power_down_sound()

def adjust_difficulty():
    global difficulty
    if score < 1000:
        difficulty = 1
    elif 1000 <= score < 3000:
        difficulty = 2
    elif 3000 <= score < 6000:
        difficulty = 3
    elif 6000 <= score < 10000:
        difficulty = 4
    else:
        difficulty = 5

def show_title_screen():
    thumby.display.fill(0)
    thumby.display.drawText("Nova", 15, 8, 1)
    thumby.display.drawText("Naut", 16, 18, 1)
    thumby.display.drawText("Press A", 10, 30, 1)
    thumby.display.update()
    while not thumby.buttonA.justPressed():
        pass
    time.sleep(0.2)

def show_story():
    for line in story:
        thumby.display.fill(0)
        thumby.display.drawText(line, 0, 16, 1)
        thumby.display.update()
        time.sleep(2)

def show_mission_objective():
    thumby.display.fill(0)
    thumby.display.drawText("Mission:", 0, 0, 1)
    thumby.display.drawText(mission_objectives[current_mission], 0, 10, 1)
    thumby.display.drawText(f"Progress: {mission_progress}", 0, 20, 1)
    thumby.display.update()
    time.sleep(2)

def update_mission_progress():
    global current_mission, mission_progress, level
    if current_mission == 0:  # Destroy 10 aliens
        mission_progress += 1
        if mission_progress >= 10:
            current_mission += 1
            mission_progress = 0
    elif current_mission == 1:  # Collect 3 power-ups
        mission_progress += 1
        if mission_progress >= 3:
            current_mission += 1
            mission_progress = 0
    elif current_mission == 2:  # Defeat the boss
        if not boss_active:
            current_mission += 1
            mission_progress = 0
    elif current_mission == 3:  # Survive for 2 minutes
        mission_progress += 1
        if mission_progress >= 7200:  # 2 minutes at 60 FPS
            current_mission = 0
            mission_progress = 0
            level += 1

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
    global lives, charge_level, bulletActive, score, cheat_index, difficulty, credits, frame_count

    game_start_time = time.time()
    show_story()
    show_mission_objective()

    while lives > 0:
        frame_count = (frame_count + 1) % 60  # Reset to 0 every 60 frames
        thumby.display.fill(0)

        # Update and draw stars
        update_stars()
        draw_stars()

        # Cheat code activation
        for i, button in enumerate(CHEAT_CODE):
            if button.pressed():
                if i == cheat_index:
                    cheat_index += 1
                    if cheat_index == len(CHEAT_CODE):
                        activate_cheat()
                        cheat_index = 0
                else:
                    cheat_index = 0
            break

        # Player movement
        if thumby.buttonU.pressed() and playerSprite.y > 0:
            playerSprite.y -= 1 + ship_speed_level
        if thumby.buttonD.pressed() and playerSprite.y < 31:
            playerSprite.y += 1 + ship_speed_level
        if thumby.buttonL.pressed() and playerSprite.x > 0:
            playerSprite.x -= 1 + ship_speed_level
        if thumby.buttonR.pressed() and playerSprite.x < 59:
            playerSprite.x += 1 + ship_speed_level

        # Shooting and bomb activation
        if thumby.buttonA.pressed():
            charge_level = min(charge_level + 1, MAX_CHARGE)
        elif charge_level > 0:  # Button released and we have some charge
            if charge_level >= MAX_CHARGE:  # Fully charged shot
                shoot_bullet(power=3, spread=True)
            elif charge_level > MAX_CHARGE // 2:  # Medium charge
                shoot_bullet(power=2)
            else:  # Low charge
                shoot_bullet(power=1)
            charge_level = 0  # Reset charge after shooting
        
        if thumby.buttonB.justPressed():
            activate_bomb()

        # Update bullets
        update_bullets()

        # Check if it's time to spawn the boss
        if not boss_active and time.time() - game_start_time >= BOSS_SPAWN_TIME:
            spawn_boss()

        # Update boss
        if boss_active:
            update_boss()
            update_boss_bullets()
        else:
            # Alien spawning and movement
            if random.randint(1, 60 // difficulty) == 1:
                spawn_alien()
            if random.randint(1, 90 // difficulty) == 1:
                spawn_fast_alien()
            if random.randint(1, 120 // difficulty) == 1:
                spawn_shielded_alien()
            
            for alien in alienSprites + fastAlienSprites + shieldedAlienSprites:
                if alien.x > -10:
                    alien.x -= 1 * (2 if alien in fastAlienSprites else 1)
                    if check_collision(alien, playerSprite):
                        handle_player_hit()
                        alien.x = -10
                    for bullet in bullets:
                        if bullet['active'] and check_collision(alien, bullet['sprite']):
                            if alien in shieldedAlienSprites and bullet['power'] < 2:
                                continue  # Shielded aliens require more powerful shots
                            score += 10 * bullet['power']
                            credits += 1
                            start_explosion(alien.x, alien.y)
                            play_explosion_sound()
                            alien.x = -10
                            bullet['active'] = False
                            update_mission_progress()

        # Update explosions
        update_explosions()

        # Spawn and update power-ups
        spawn_power_up()
        update_power_ups()
        apply_power_ups()

        # Spawn and update health items
        spawn_health_item()
        update_health_items()

        # New feature: upgradeable ship
        if thumby.buttonB.justPressed() and not boss_active:
            upgrade_ship()

        # New feature: environmental hazards (asteroids)
        spawn_asteroid()
        update_asteroid()

        # New feature: temporary power-downs
        apply_power_down()

        # New feature: dynamic difficulty adjustment
        adjust_difficulty()

        # Draw sprites
        thumby.display.drawSprite(playerSprite)
        
        for bullet in bullets:
            if bullet['active']:
                thumby.display.drawSprite(bullet['sprite'])
        
        if boss_active:
            thumby.display.drawSprite(bossSprite)
            for bullet in boss_bullets:
                if bullet['active']:
                    bossBulletSprite.x = bullet['x']
                    bossBulletSprite.y = bullet['y']
                    thumby.display.drawSprite(bossBulletSprite)
        else:
            for alien in alienSprites + fastAlienSprites + shieldedAlienSprites:
                if alien.x > -10:
                    thumby.display.drawSprite(alien)

        # Draw flashing collectibles
        for power_up in power_ups:
            if power_up['sprite'].x > -10 and frame_count % FLASH_INTERVAL < FLASH_INTERVAL // 2:
                thumby.display.drawSprite(power_up['sprite'])

        for item in health_items:
            if item['active'] and frame_count % FLASH_INTERVAL < FLASH_INTERVAL // 2:
                healthItemSprite.x = item['x']
                healthItemSprite.y = item['y']
                thumby.display.drawSprite(healthItemSprite)

        # Draw shield
        draw_pulsating_shield()

        # Draw explosions
        for explosion in explosions:
            if explosion['active']:
                thumby.display.blit(explosionMaps[explosion['frame']], 
                                    int(explosion['x']), int(explosion['y']), 
                                    8, 8, -1, 0, 0)

        # Draw asteroid
        if asteroid_field_active:
            thumby.display.drawSprite(asteroidSprite)

        # Draw charge bar
        charge_width = (charge_level * 72) // MAX_CHARGE
        thumby.display.drawLine(0, 39, charge_width, 39, 1)

        # Draw score, lives, level, and bombs
        thumby.display.drawText(f"S:{score} L:{lives} Lv:{level} B:{bombs}", 0, 0, 1)

        # Draw boss health
        if boss_active:
            thumby.display.drawText(f"Boss:{boss_health}", 0, 8, 1)

        # Draw credits
        thumby.display.drawText(f"C:{credits}", 60, 0, 1)

        thumby.display.update()

        # Add a small delay to control the game speed
        time.sleep(0.016)  # Approximately 60 FPS

    game_over()

def activate_cheat():
    global lives, bombs, shield_active
    lives = 5
    bombs = 5
    shield_active = True
    play_cheat_melody()

# Sound functions
def play_background_music():
    # Simple background melody
    melody = [
        (C4, 200), (E4, 200), (G4, 200), (C5, 200),
        (B4, 200), (G4, 200), (E4, 200), (C4, 200)
    ]
    for note, duration in melody:
        thumby.audio.play(note, duration)
        time.sleep(duration / 1000)

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

def play_health_pickup_sound():
    thumby.audio.play(1000, 100)
    time.sleep(0.1)
    thumby.audio.play(1500, 100)

def play_cheat_melody():
    notes = [523, 587, 659, 698, 784]  # C5, D5, E5, F5, G5
    for note in notes:
        thumby.audio.play(note, 100)
        time.sleep(0.1)

def play_power_down_sound():
    for freq in range(1000, 500, -100):
        thumby.audio.play(freq, 50)
        time.sleep(0.05)

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
        if thumby.buttonA.justPressed():
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
