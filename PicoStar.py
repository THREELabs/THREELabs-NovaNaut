import thumby
import random
import time

# Player bitmap: width: 13, height: 9
playerMap = bytearray([
    239,247,251,195,61,181,189,181,61,195,251,247,239,
    255,255,255,255,254,255,255,255,254,255,255,255,255
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

# Boss (Octopus) bitmap: width: 24, height: 24 (black)
bossMap = bytearray([
    0,0,60,126,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,126,60,0,0,
    60,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,60,
    0,0,36,66,129,129,129,129,129,129,129,129,129,129,129,129,129,129,129,129,66,36,0,0
])

# Mini-boss (Small Octopus) bitmap: width: 16, height: 16 (black)
miniBossMap = bytearray([
    0,60,126,255,255,255,255,255,255,255,255,255,255,126,60,0,
    60,126,255,255,255,255,255,255,255,255,255,255,255,255,126,60
])

# Ink blob bitmap: width: 8, height: 8 (black)
inkMap = bytearray([24,60,126,255,255,126,60,24])

# Create sprites
playerSprite = thumby.Sprite(13, 9, playerMap)
bulletSprite = thumby.Sprite(3, 3, bulletMap)
bossSprite = thumby.Sprite(24, 24, bossMap)
miniBossSprites = [thumby.Sprite(16, 16, miniBossMap) for _ in range(2)]
inkSprite = thumby.Sprite(8, 8, inkMap)

# Alien sprites
MAX_ALIENS = 5
alienSprites = [thumby.Sprite(8, 8, alienMap) for _ in range(MAX_ALIENS)]

# Initial placements
playerSprite.x, playerSprite.y = 5, 30
bulletSprite.x, bulletSprite.y = -10, -10  # Off-screen initially

# Game state
playerSprite.yVel = 0
bulletActive = False
score = 0
lives = 3
explosions = [{'active': False, 'frame': 0, 'x': 0, 'y': 0, 'timer': 0} for _ in range(MAX_ALIENS)]

# Boss-related variables
boss_active = False
boss_health = 10
boss_spawn_time = 60  # seconds
game_start_time = time.time()
mini_bosses_active = [False, False]
mini_boss_health = [5, 5]
ink_active = False

thumby.display.setFPS(60)

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
    bossSprite.x, bossSprite.y = 48, random.randint(0, 16)
    boss_active, boss_health = True, 10

def update_boss():
    global boss_active, boss_health, score, ink_active
    if boss_active:
        bossSprite.x += random.randint(-1, 1)
        bossSprite.y += random.randint(-1, 1)
        bossSprite.x = max(24, min(bossSprite.x, 48))
        bossSprite.y = max(0, min(bossSprite.y, 16))
        
        if random.randint(1, 60) == 1 and not ink_active:
            ink_active = True
            inkSprite.x, inkSprite.y = bossSprite.x, bossSprite.y + 12
        
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
        miniBossSprites[i].x = bossSprite.x + random.randint(-10, 10)
        miniBossSprites[i].y = bossSprite.y + random.randint(-10, 10)
        mini_bosses_active[i], mini_boss_health[i] = True, 5

def update_mini_bosses():
    global mini_bosses_active, mini_boss_health, score
    for i in range(2):
        if mini_bosses_active[i]:
            miniBossSprites[i].x += random.randint(-1, 1)
            miniBossSprites[i].y += random.randint(-1, 1)
            miniBossSprites[i].x = max(0, min(miniBossSprites[i].x, 56))
            miniBossSprites[i].y = max(0, min(miniBossSprites[i].y, 24))
            
            if bulletActive and check_collision(miniBossSprites[i], bulletSprite):
                mini_boss_health[i] -= 1
                score += 10
                thumby.audio.play(600, 100)
                if mini_boss_health[i] <= 0:
                    mini_bosses_active[i] = False
                    score += 25
                    if not any(mini_bosses_active):
                        level_complete()

def level_complete():
    for _ in range(5):
        thumby.display.fill(0)
        thumby.display.drawText("LEVEL", random.randint(0, 4), random.randint(10, 14), 1)
        thumby.display.drawText("COMPLETE!", random.randint(0, 4), random.randint(20, 24), 1)
        thumby.display.update()
        time.sleep(0.1)
    time.sleep(2)

def game_over():
    thumby.display.fill(1)
    thumby.display.drawText("GAME OVER", 0, 16, 0)
    thumby.display.drawText(f"Score: {score}", 0, 24, 0)
    thumby.display.update()
    time.sleep(2)
    return False

# Main game loop
running = True
while running:
    thumby.display.fill(1)

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
    if thumby.buttonA.pressed() and not bulletActive:
        bulletActive = True
        bulletSprite.x = playerSprite.x + playerSprite.width // 2
        bulletSprite.y = playerSprite.y + playerSprite.height // 2
        thumby.audio.play(1000, 50)

    # Bullet movement
    if bulletActive:
        bulletSprite.x += 2
        if bulletSprite.x > 72:
            bulletActive = False
            bulletSprite.x = -10

    # Check if it's time to spawn the boss
    if not boss_active and not any(mini_bosses_active) and time.time() - game_start_time >= boss_spawn_time:
        spawn_boss()

    # Update boss and mini-bosses
    if boss_active:
        update_boss()
    else:
        update_mini_bosses()

    # Ink movement
    if ink_active:
        inkSprite.x -= 2
        if inkSprite.x < 0:
            ink_active = False
        elif check_collision(inkSprite, playerSprite):
            lives -= 1
            ink_active = False

    # ... (continued in the next section)
# Alien spawning and movement (only when boss is not active)
    if not boss_active and not any(mini_bosses_active):
        if random.randint(1, 60) == 1:
            spawn_alien()
        
        for alien in alienSprites:
            if alien.x > -10:
                alien.x -= 1
                if check_collision(alien, playerSprite):
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

    # Draw sprites
    thumby.display.drawSprite(playerSprite)
    
    if bulletActive:
        thumby.display.drawSprite(bulletSprite)
    
    if boss_active:
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

    # Draw explosions
    for explosion in explosions:
        if explosion['active']:
            thumby.display.blit(explosionMaps[explosion['frame']], 
                                int(explosion['x']), int(explosion['y']), 
                                8, 8, -1, 0, 0)

    # Draw score and lives
    thumby.display.drawText(f"S:{score} L:{lives}", 0, 0, 0)

    # Draw boss or mini-boss health
    if boss_active:
        thumby.display.drawText(f"B:{boss_health}", 0, 8, 0)
    elif any(mini_bosses_active):
        thumby.display.drawText(f"M1:{mini_boss_health[0]} M2:{mini_boss_health[1]}", 0, 8, 0)

    thumby.display.update()

    # Add a small delay to control the game speed
    time.sleep(0.016)  # Approximately 60 FPS

# Clean up and exit
thumby.display.fill(1)
thumby.display.drawText("Thanks for", 0, 16, 0)
thumby.display.drawText("playing!", 0, 24, 0)
thumby.display.update()
time.sleep(2)
