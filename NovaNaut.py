import thumby
import random
import time
import math

# Player bitmap: width: 13, height: 9 (updated to white)
playerMap = bytearray([
    16,8,4,60,194,74,66,74,194,60,4,8,16,
    0,0,0,0,1,0,0,0,1,0,0,0,0
])

# Bullet bitmap: width: 3, height: 3 (plus shape)
bulletMap = bytearray([5,7,5])

# Alien bitmap: width: 8, height: 8 (black)
alienMap = bytearray([36,24,126,90,255,90,36,102])

# Explosion bitmaps: width: 8, height: 8 (black)
explosionMaps = [
    bytearray([0,36,24,60,60,24,36,0]),
    bytearray([0,66,60,126,126,60,66,0]),
    bytearray([66,129,195,231,231,195,129,66]),
    bytearray([129,66,36,24,24,36,66,129])
]

# Boss (Dark Circle) bitmap: width: 16, height: 16 (black)
bossMap = bytearray([
    0,0,60,126,255,255,255,255,255,255,255,255,126,60,0,0,
    0,60,255,255,255,255,255,255,255,255,255,255,255,255,60,0
])

# Mini-boss (Smaller Dark Circle) bitmap: width: 12, height: 12 (black)
miniBossMap = bytearray([
    0,60,126,255,255,255,255,255,255,126,60,0,
    60,255,255,255,255,255,255,255,255,255,255,60
])

# Ink blob bitmap: width: 8, height: 8 (black)
inkMap = bytearray([24,60,126,255,255,126,60,24])

# Star (power-up) bitmap: width: 8, height: 8
starMap = bytearray([0,0,20,42,127,42,20,0])

# Create sprites
playerSprite = thumby.Sprite(13, 9, playerMap)
bulletSprite = thumby.Sprite(3, 3, bulletMap)
bossSprite = thumby.Sprite(16, 16, bossMap)
miniBossSprites = [thumby.Sprite(12, 12, miniBossMap) for _ in range(2)]
inkSprite = thumby.Sprite(8, 8, inkMap)
starSprite = thumby.Sprite(8, 8, starMap)

# Alien sprites
MAX_ALIENS = 5
alienSprites = [thumby.Sprite(8, 8, alienMap) for _ in range(MAX_ALIENS)]

# Star layers for parallax effect
STAR_LAYERS = 3
starLayers = [[] for _ in range(STAR_LAYERS)]

# Initial placements
playerSprite.x, playerSprite.y = 5, 30
bulletSprite.x, bulletSprite.y = -10, -10  # Off-screen initially
starSprite.x, starSprite.y = -10, -10  # Off-screen initially

# Game state
playerSprite.yVel = 0
bulletActive = False
score = 0
lives = 3
level = 1
explosions = [{'active': False, 'frame': 0, 'x': 0, 'y': 0, 'timer': 0} for _ in range(MAX_ALIENS)]

# Boss-related variables
boss_active = False
boss_health = 10
boss_spawn_time = 20  # seconds
game_start_time = time.time()
mini_bosses_active = [False, False]
mini_boss_health = [5, 5]
ink_active = False

# Cheat code variables
cheat_active = False
cheat_timer = 0
machine_gun_cooldown = 0

# Shield variables
shield_active = False
shield_hits = 0

# Scroll speed
scroll_speed = 1

# Game mode variables
game_mode = "normal"
spread_shot_active = False
laser_active = False
homing_missile_active = False
homing_missile_x, homing_missile_y = -10, -10

thumby.display.setFPS(60)

# END OF SECTION 1

def create_stars():
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

def spawn_boss():
    global boss_active, boss_health
    bossSprite.x, bossSprite.y = 48, random.randint(0, 24)
    boss_active, boss_health = True, 10 + (level * 5)  # Boss health increases with level

def update_boss():
    global boss_active, boss_health, score, ink_active
    if boss_active:
        bossSprite.x += random.randint(-1, 1)
        bossSprite.y += random.randint(-1, 1)
        bossSprite.x = max(16, min(bossSprite.x, 56))
        bossSprite.y = max(0, min(bossSprite.y, 24))
        
        if random.randint(1, 60) == 1 and not ink_active:
            ink_active = True
            inkSprite.x, inkSprite.y = bossSprite.x, bossSprite.y + 8
        
        if bulletActive and check_collision(bossSprite, bulletSprite):
            boss_health -= 1
            score += 5
            thumby.audio.play(800, 100)
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
    global mini_bosses_active, mini_boss_health, score
    for i in range(2):
        if mini_bosses_active[i]:
            miniBossSprites[i].x += random.randint(-1, 1)
            miniBossSprites[i].y += random.randint(-1, 1)
            miniBossSprites[i].x = max(0, min(miniBossSprites[i].x, 60))
            miniBossSprites[i].y = max(0, min(miniBossSprites[i].y, 28))
            
            if bulletActive and check_collision(miniBossSprites[i], bulletSprite):
                mini_boss_health[i] -= 1
                score += 10
                thumby.audio.play(600, 100)
                if mini_boss_health[i] <= 0:
                    mini_bosses_active[i] = False
                    score += 25
                    if not any(mini_bosses_active):
                        level_complete()

def draw_shield():
    if shield_active:
        center_x = int(playerSprite.x + playerSprite.width // 2)
        center_y = int(playerSprite.y + playerSprite.height // 2)
        radius = 10
        for x in range(center_x - radius, center_x + radius + 1):
            for y in range(center_y - radius, center_y + radius + 1):
                if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                    if 0 <= x < 72 and 0 <= y < 40:  # Check if within screen bounds
                        thumby.display.setPixel(x, y, 1)

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

def show_artwork(artwork):
    thumby.display.fill(0)
    for y, row in enumerate(artwork):
        for x, pixel in enumerate(row):
            if pixel == '1':
                thumby.display.setPixel(x, y, 1)
    thumby.display.update()
    time.sleep(3)

# END OF SECTION 2


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
    
    stories = [
        "As you venture\ndeeper into\nspace, strange\nanomalies\nappear ahead.\nPrepare for\nunknown dangers!",
        "The anomalies\nreveal a hidden\nwormhole. You're\npulled into a\nnew galaxy!\nWhat awaits?",
        "A distress call\nechoes through\nspace. A nearby\nplanet needs\nyour help!\nBattle awaits.",
        "The final\nfrontier looms.\nAn alien armada\napproaches.\nDefend Earth\nat all costs!",
        "Victory! Earth\nis safe, but\nnew adventures\nbeckons. Ready\nfor the next\nchallenge?"
    ]
    
    artworks = [
        ['00111100',
         '01111110',
         '11111111',
         '11111111',
         '01111110',
         '00111100'],
        ['00011000',
         '00111100',
         '01111110',
         '11111111',
         '01111110',
         '00111100',
         '00011000'],
        ['11000011',
         '01100110',
         '00111100',
         '00011000',
         '00111100',
         '01100110',
         '11000011'],
        ['10000001',
         '01000010',
         '00100100',
         '00011000',
         '00011000',
         '00100100',
         '01000010',
         '10000001'],
        ['11111111',
         '10000001',
         '10111101',
         '10100101',
         '10100101',
         '10111101',
         '10000001',
         '11111111']
    ]
    
    if level <= len(stories):
        show_scrolling_story(stories[level-1])
        show_artwork(artworks[level-1])
    
    game_modes = ["normal", "spread_shot", "laser", "homing_missile", "normal"]
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
    global final_boss_active, final_boss_health, score, running
    if final_boss_active:
        bossSprite.x += random.randint(-2, 2)
        bossSprite.y += random.randint(-2, 2)
        bossSprite.x = max(16, min(bossSprite.x, 56))
        bossSprite.y = max(0, min(bossSprite.y, 32))
        
        if random.randint(1, 30) == 1 and not ink_active:
            ink_active = True
            inkSprite.x, inkSprite.y = bossSprite.x, bossSprite.y + 8
        
        if bulletActive and check_collision(bossSprite, bulletSprite):
            final_boss_health -= 1
            score += 10
            thumby.audio.play(800, 100)
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

def game_over():
    thumby.display.fill(1)
    thumby.display.drawText("GAME OVER", 0, 16, 0)
    thumby.display.drawText(f"Score: {score}", 0, 24, 0)
    thumby.display.update()
    time.sleep(2)
    return False

def play_cheat_melody():
    notes = [523, 587, 659, 698, 784]  # C5, D5, E5, F5, G5
    for note in notes:
        thumby.audio.play(note, 100)
        time.sleep(0.1)

def spawn_power_up():
    global starSprite
    if random.randint(1, 1000) == 1 and starSprite.x <= -10:
        starSprite.x = 72
        starSprite.y = random.randint(5, 35)

def update_power_up():
    global starSprite, shield_active, shield_hits
    if starSprite.x > -10:
        starSprite.x -= 1
        if check_collision(starSprite, playerSprite):
            shield_active = True
            shield_hits = 0
            starSprite.x = -10
            thumby.audio.play(1000, 200)  # Play a sound when shield is activated

def shoot_bullet():
    global bulletActive, bulletSprite
    bulletActive = True
    bulletSprite.x = playerSprite.x + playerSprite.width // 2
    bulletSprite.y = playerSprite.y + playerSprite.height // 2
    bulletSprite.angle = 0
    thumby.audio.play(1000, 50)

def shoot_spread():
    global bulletActive, bulletSprite
    angles = [-15, 0, 15]
    for angle in angles:
        bulletActive = True
        bulletSprite.x = playerSprite.x + playerSprite.width // 2
        bulletSprite.y = playerSprite.y + playerSprite.height // 2
        bulletSprite.angle = angle
        thumby.audio.play(1000, 50)

def shoot_laser():
    global laser_active
    laser_active = True
    thumby.audio.play(1500, 100)

def shoot_homing_missile():
    global homing_missile_active, homing_missile_x, homing_missile_y
    homing_missile_active = True
    homing_missile_x = playerSprite.x + playerSprite.width // 2
    homing_missile_y = playerSprite.y + playerSprite.height // 2
    thumby.audio.play(800, 100)

# Main game loop
create_stars()
running = True
final_boss_active = False
final_boss_health = 20

while running:
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

    # Shooting
    if thumby.buttonA.pressed():
        if cheat_active and machine_gun_cooldown == 0:
            for i in range(5):
                shoot_bullet()
                time.sleep(0.05)
            machine_gun_cooldown = 10
        elif not bulletActive:
            if game_mode == "normal":
                shoot_bullet()
            elif game_mode == "spread_shot":
                shoot_spread()
            elif game_mode == "laser":
                shoot_laser()
            elif game_mode == "homing_missile":
                shoot_homing_missile()

    # Bullet movement
    if bulletActive:
        bulletSprite.x += 2 * math.cos(math.radians(bulletSprite.angle))
        bulletSprite.y -= 2 * math.sin(math.radians(bulletSprite.angle))
        if bulletSprite.x > 72 or bulletSprite.x < 0 or bulletSprite.y > 40 or bulletSprite.y < 0:
            bulletActive = False

    # Laser update
    if laser_active:
        for alien in alienSprites:
            if alien.x > -10 and alien.x < 72 and abs(alien.y - playerSprite.y) < 5:
                score += 10
                start_explosion(alien.x, alien.y)
                alien.x = -10
        laser_active = False

    # Homing missile update
    if homing_missile_active:
        target = min((alien for alien in alienSprites if alien.x > -10), key=lambda a: (a.x - homing_missile_x)**2 + (a.y - homing_missile_y)**2, default=None)
        if target:
            angle = math.atan2(target.y - homing_missile_y, target.x - homing_missile_x)
            homing_missile_x += 2 * math.cos(angle)
            homing_missile_y += 2 * math.sin(angle)
            if abs(homing_missile_x - target.x) < 5 and abs(homing_missile_y - target.y) < 5:
                score += 20
                start_explosion(target.x, target.y)
                target.x = -10
                homing_missile_active = False
        else:
            homing_missile_active = False

    # Update machine gun cooldown
    if machine_gun_cooldown > 0:
        machine_gun_cooldown -= 1

    # Check if it's time to spawn the boss
    if not boss_active and not any(mini_bosses_active) and not final_boss_active and time.time() - game_start_time >= boss_spawn_time:
        if level == 5:
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
                    if shield_active:
                        shield_hits += 1
                        if shield_hits >= 3:
                            shield_active = False
                    else:
                        lives -= 1
                        thumby.audio.play(200, 200)
                    alien.x = -10
                    if lives <= 0:
                        running = game_over()
                elif bulletActive and check_collision(alien, bulletSprite):
                    score += 10
                    start_explosion(alien.x, alien.y)
                    thumby.audio.play(500, 100)
                    alien.x = -10
                    bulletActive = False
                    bulletSprite.x = -10

    # Update explosions
    update_explosions()

    # Spawn and update power-up
    spawn_power_up()
    update_power_up()

    # Draw sprites
    thumby.display.drawSprite(playerSprite)
    
    if bulletActive:
        thumby.display.drawSprite(bulletSprite)
    
    if laser_active:
        thumby.display.drawLine(playerSprite.x + playerSprite.width // 2, playerSprite.y, 72, playerSprite.y, 1)
    
    if homing_missile_active:
        thumby.display.setPixel(int(homing_missile_x), int(homing_missile_y), 1)
    
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

    if starSprite.x > -10:
        thumby.display.drawSprite(starSprite)

    # Draw shield
    if shield_active:
        draw_shield()

    # Draw explosions
    for explosion in explosions:
        if explosion['active']:
            thumby.display.blit(explosionMaps[explosion['frame']], 
                                int(explosion['x']), int(explosion['y']), 
                                8, 8, -1, 0, 0)

    # Draw score, lives, and level
    thumby.display.drawText(f"S:{score} L:{lives} Lv:{level}", 0, 0, 1)

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

# Clean up and exit
thumby.display.fill(1)
thumby.display.drawText("Thanks for", 0, 16, 0)
thumby.display.drawText("playing!", 0, 24, 0)
thumby.display.update()
time.sleep(2)
