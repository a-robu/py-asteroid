import sys
import math
import pygame
import random



warp_thresh = 1
def pip(pos, poly):
    pin = False
    for i in range(len(poly)):
        a = poly[i - 1][1] - pos[1]
        b = poly[i][1] - pos[1]
        if a * b < 0:
            if poly[i - 1][0] == poly[i][0]:
                if poly[i][0] > pos[0]:
                    pin = not pin
            else:
                slope = 1.0 * (poly[i][1] - poly[i - 1][1]) / (poly[i][0] - poly[i - 1][0])
                x = (pos[1] - poly[i][1]) / slope
                if x + poly[i][0] > pos[0]:
                    pin = not pin
    return pin

            

def angle(a, b):
    i = clockwise_angle(a, b)
    o = math.pi * 2 - i
    if i < o:
        return i
    else:
        return o
    
def clockwise_angle(a, b):
    diff = b - a
    if diff < 0:
        return diff + math.pi * 2
    else:
        return diff
    
def to_cart(rot, leng):
    return [math.cos(rot) * leng, math.sin(rot) * leng]

def warp(pos, game):
    if pos[0] < 0:
        pos[0] = game.width - warp_thresh
    elif pos[0] > game.width:
        pos[0] = warp_thresh

    if pos[1] < - warp_thresh:
        pos[1] = game.height
    elif pos[1] > game.height + warp_thresh:
        pos[1] = 0
    return pos

def instancing(pos, thresh, game):
    results = []

    sides = [False, False]

    if pos[0] < thresh:
        sides[1] = 'l'
    elif pos[0] > game.width - thresh:
        sides[1] = 'r'

    if pos[1] < thresh:
        sides[0] = 'u'
    elif pos[1] > game.height - thresh:
        sides[0] = 'd'

    if sides[1]:
        results.append([pos[0] + (1 if sides[1] == 'l' else -1) * game.width, pos[1]])
        if sides[0]:
            results.append([pos[0] + (1 if sides[1] == 'l' else -1) * game.width,
                            pos[1] + (1 if sides[0] == 'u' else -1) * game.height])
    if sides[0]:
        results.append([pos[0], pos[1] + (1 if sides[0] == 'u' else -1) * game.height])

    return results

class BulletEngine:
    def __init__(self, game):
        self.bullet_list = []
        self.game = game
        self.bullet_vel = 2

    def add_bullet(self, x, y, rot, ship):
        self.bullet_list.append([x, y, math.cos(rot) * 15, math.sin(rot) * 15, ship, 40])

    def render(self):
        for bullet in self.bullet_list:
            pygame.draw.line(self.game.surface, (255, 255, 255), (bullet[0] - bullet[2], bullet[1] - bullet[3]),
                             (bullet[0], bullet[1]), 3)

    def step(self):        
        for i in range(len(self.bullet_list) - 1, -1, -1):
            self.bullet_list[i][5] -= 1
            if self.bullet_list[i][5] < 0:
                del self.bullet_list[i]
            else:
                self.bullet_list[i][0] += self.bullet_list[i][2]
                self.bullet_list[i][1] += self.bullet_list[i][3]
                self.bullet_list[i][0],  self.bullet_list[i][1] = warp([self.bullet_list[i][0], self.bullet_list[i][1]], self.game)
                for ship in [x for x in self.game.ships.ship_list if x.player.team in self.bullet_list[i][4].player.team.can_hurt]:
                    if pip((self.bullet_list[i][0], self.bullet_list[i][1]), ship.get_poly()):
                        ship.hit(self.bullet_list[i][4])
                        self.game.add_event('hit', self.bullet_list[i][4], ship)
                        self.bullet_list[i][5] = 0
                        
class GUI:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 15)
        self.fps = 0
        self.score = 0
        self.lives = 0
        self.kill_log = [self.small_font.render('', True, (255, 255, 255))] * 4
        self.kill_log_fade_time = 0

    def add_kill(self, text):
        self.kill_log.append(self.small_font.render(text, True, (255, 255, 255)))
        self.kill_log[-1].convert_alpha()
        self.kill_log.pop(0)
        self.kill_log_fade_time = 255
        
    def render(self, window):
        for i in range(1, 5):
            self.kill_log[-i].set_alpha(255 - self.kill_log_fade_time)
            window.blit(self.kill_log[-i], (self.game.width - 200, 10 + i * 10))                                    
        window.blit(self.font.render('FPS '+str(self.fps), True, (255, 255, 255)), (self.game.width / 2, 15))     
        window.blit(self.font.render('Lives ' + str(self.lives), True, (255, 255, 255)), (20, 20))       
        window.blit(self.font.render('Score ' + str(self.score), True, (255, 255, 255)), (20, 40))       
        window.blit(self.font.render('Energy ' + '|' * (self.energy / 10), True, (255, 255, 255)), (20, 60))     
        
    def step(self):
        if self.kill_log_fade_time > 0:
            self.kill_log_fade_time -= 1
        
class ParticleEngine:
    def __init__(self, game):
        self.particles = []
        self.game = game
        self.types = {'smoke': {'lifespan': 70,
                                'dir_rand': 0.2,
                                'speed_rand': 0.4},
                      'small_smoke': {'lifespan': 30,
                                      'dir_rand': 0.1,
                                      'speed_rand': 1},
                      'debries': {'lifespan': 100,
                                  'dir_rand': math.pi * 2,
                                  'speed_rand': 3},
                      'spawn': {'lifespan': 50,
                                  'dir_rand': math.pi * 2,
                                  'speed_rand': 3},}                               
                                    
    def add_particle(self, p_type, pos, direction, speed, color):
        self.particles.append([p_type,
                               list(pos),
                               to_cart(direction + (random.random() - 0.5) * self.types[p_type]['dir_rand'] * direction,
                                       speed + (random.random() - 0.5) * self.types[p_type]['speed_rand'] * speed),
                               self.types[p_type]['lifespan'],
                               color])

    def step(self):
        for i in range(len(self.particles) -1, -1, -1):
            if self.particles[i][0] in ['smoke', 'small_smoke']:
                self.particles[i][2][0] *= 0.99
                self.particles[i][2][1] *= 0.99
            self.particles[i][1][0] += self.particles[i][2][0]
            self.particles[i][1][1] += self.particles[i][2][1]
            self.particles[i][3] -= 1
            if self.particles[i][3] < 0:
                del self.particles[i]
            else:
                warp(self.particles[i][1], self.game)

    def render(self): 
        for p in self.particles:
            if p[0] in ['smoke', 'small_smoke']:
                pygame.draw.circle(self.game.surface, p[4], map(int, p[1]), int((10 + p[3]) * 0.06 + 1))
            if p[0] in ['debries', 'spawn']:
                pygame.draw.circle(self.game.surface, p[4], map(int, p[1]), int((25 + p[3]) * 0.06 + 1))


class ShipEngine:
    def __init__(self, game):
        self.ship_list = []
        self.game = game

    def make_ship(self, player):
        ship = Ship()
        ship.game = self.game
        ship.x = random.randint(200, self.game.width - 201)
        ship.y = random.randint(200, self.game.height - 201)
        for i in range(30):
            self.game.particles.add_particle('spawn', (ship.x, ship.y), 1, 1, (255, 255, 255))
        ship.rot = math.pi * 2 * random.random()
        ship.player = player
        self.ship_list.append(ship)
        return ship

    def destroy(self, ship):
        self.ship_list.remove(ship)
    
    def step(self):
        for ship in self.ship_list:
            ship.step()
            
    def render(self):
        for ship in self.ship_list:
            instances = [[ship.x, ship.y]] + instancing([ship.x, ship.y], ship.instance_thresh, self.game)
            for pair in instances:
                poly = []
                for point in ship.model:
                    a = point[0] + ship.rot
                    b = point[1] * ship.scale
                    aa = math.cos(a) * b + pair[0]
                    bb = math.sin(a) * b + pair[1]
                    poly.append((aa, bb))
                pygame.draw.polygon(self.game.surface, (0,0,0), poly, 0)
                pygame.draw.polygon(self.game.surface, ship.color, poly, int(1 + 1 * ship.scale))

class Ship:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.xvel = 0
        self.yvel = 0
        self.rot = 0
        self.accel = 0.3
        self.model = [(math.radians(0), 20),
                      (math.radians(140), 20),
                      (math.radians(180), 10),
                      (math.radians(220), 20)]
        self.scale = 1
        self.instance_thresh = sorted([x[1] for x in self.model])[-1] * self.scale #This is furthest point from the ship,
                                                                #used for duplicate rendering
        self.angular_vel = 0
        self.angular_acc = 0.006
        self.angular_acc = 0.01
        self.color = (255, 255, 255)
        self.hit_points = 1
        self.player = None
        self.energy = 100
        self.shooting_penalty = 2
        self.ai_target = None
        self.spawn_inv = 300

    def hit(self, source_ship):
        if self.spawn_inv <= 0:
            self.hit_points -= 1
            if self.hit_points <= 0:
                self.game.ships.destroy(self)
                self.game.add_event('destroy', source_ship, self)

    def get_poly(self):
        poly = []
        for point in self.model:
            poly.append(self.ship_to_world_coord(point))
        return poly            
            
    def step(self):
        if self.spawn_inv >= 1:
            if (self.spawn_inv / 15 + 1) % 2:
                self.color = (self.player.color[0] / 3, self.player.color[1] / 3, self.player.color[2] / 3)
            else:
                self.color = self.player.color
            self.spawn_inv -= 1
        else:
            self.color = self.player.color
            
        self.keys = {'linear_stabil':False,
                     'thrust':False,
                     'turn_left':False,
                     'turn_right':False,
                     'rot_stabil':False,
                     'shoot': False}
        if self.player.ai:
            self.ai()
        else:
            self.human()
        if self.keys['turn_left']:
            self.angular_vel -= self.angular_acc
            for i in [-1, 1]:
                self.game.particles.add_particle('small_smoke',                                                 
                           self.ship_to_world_coord(self.model[0 if i == -1 else 3]),
                            self.rot - i * math.pi / 2, 2, self.color) 
            
        if self.keys['turn_right']:
            self.angular_vel += self.angular_acc
            for i in [-1, 1]:                    
                self.game.particles.add_particle('small_smoke',
                           self.ship_to_world_coord(self.model[int(0.5 + i / 2.0)]),
                            self.rot + i * math.pi / 2, 2, self.color)         
            
        if self.keys['thrust']:
            self.xvel += self.accel * math.cos(self.rot)
            self.yvel += self.accel * math.sin(self.rot)

        if self.keys['linear_stabil']:
            self.xvel *= 0.94
            self.yvel *= 0.94

        if self.keys['rot_stabil']:
            self.angular_vel*= 0.94

        if self.keys['shoot']:
            self.spawn_inv = 0
            if self.energy >= 10 and self.shooting_penalty == 0:
                pos  = self.ship_to_world_coord(self.model[2])
                self.game.bullets.add_bullet(pos[0], pos[1], self.rot, self)
                self.energy -= 10
                self.shooting_penalty = 2
        
        if self.energy <= 100:
            self.energy += 1

        if self.shooting_penalty > 0:
            self.shooting_penalty -= 1
        
        self.x += self.xvel
        self.y += self.yvel
        self.rot += self.angular_vel

        self.rot = self.rot % (math.pi * 2)

        self.x, self.y = warp([self.x, self.y], self.game)

        if self.keys['thrust']:
            for i in range(3):
                self.game.particles.add_particle('smoke',
                                       self.ship_to_world_coord(self.model[2]),
                                       self.rot + math.pi, 2, self.color)
                
    def ship_to_world_coord(self, (rot, leng)):
        a = rot + self.rot
        b = leng * self.scale
        aa = math.cos(a) * b + self.x
        bb = math.sin(a) * b + self.y
        return aa, bb
        

    def ai(self):
        if not (self.ai_target and isinstance(self.ai_target, Ship) and self.ai_target.hit_points > 0): 
            try:
                self.ai_target = random.choice([x for x in self.game.ships.ship_list if x.player.team in self.player.team.can_hurt])
            except IndexError:
                class dummy:
                    x = self.game.width/2
                    y = self.game.height/2
                self.ai_target = dummy
            
        closest_coord = []
        closest_length = 100000000
        for i in range(-1, 2):
            for o in range(-1, 2):
                dist = math.sqrt((self.ai_target.x + i * self.game.width - self.x) ** 2 +
                                 (self.ai_target.y + o * self.game.height - self.y) ** 2)
                if dist < closest_length:
                    closest_coord = (self.ai_target.x + i * self.game.width,
                                     self.ai_target.y + o * self.game.height)
                    closest_length = dist

        target_angle = math.atan2(closest_coord[1] - self.y - self.yvel * 10,
                                  closest_coord[0] - self.x - self.xvel * 10)
        if target_angle <= 0:
            target_angle += math.pi * 2
        target_angle = (target_angle - self.rot) % (math.pi * 2)
        
        vel_dir = math.atan2(self.yvel, self.xvel)
        if vel_dir <= 0:
            vel_dir += math.pi * 2

        rand = random.random() * abs(self.angular_vel)

        stabilise = ''
        if rand > 0.05:
            stabilise = 'ON'
            if self.angular_vel > 0:
                self.keys['turn_left'] = True
            else:
                self.keys['turn_right'] = True
        else:       
            if target_angle + 0.1 < math.pi:
                self.keys['turn_right'] = True
            elif target_angle - 0.1 > math.pi:
                self.keys['turn_left'] = True

        if not self.spawn_inv:
            self.keys['shoot'] = True
        dist = math.sqrt((closest_coord[0] - self.x) ** 2 + (closest_coord[1] - self.y) ** 2)
        speed = math.sqrt(self.xvel**2 + self.yvel**2) ** 2 * 10
        if math.pi * 0.2 < target_angle or target_angle > math.pi * 1.8:
            if speed < dist or angle(vel_dir, self.rot) > math.pi * 0.75:
                self.keys['thrust'] = True
    
    def human(self):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_UP]:
            self.keys['thrust'] = True

        if keys[pygame.K_LEFT]:
            self.keys['turn_left']= True

        if keys[pygame.K_RIGHT]:
            self.keys['turn_right'] = True
            
        if keys[pygame.K_z]:
            self.keys['shoot'] = True

        mods = pygame.key.get_mods()
        
        if mods & pygame.KMOD_LCTRL:
            self.keys['linear_stabil'] = True

        if mods & pygame.KMOD_LSHIFT:
            self.keys['rot_stabil'] = True                          

class Player:
    def __init__(self, game, ai = False):
        self.ai = ai
        self.lives = 5
        self.score = 0
        self.game = game
        self.team = None
        self.ship = None        
        self.name = None

    def set_team(self, team):
        self.team = team
        self.color = team.color
        if self.ship:
            self.ship.color = team.color

    def request_ship(self):
        self.ship = self.game.ships.make_ship(player = self)
        if self.team:
            self.ship.color = self.team.color
        
class Team:
    def __init__(self):
        self.color = (255, 100, 255)
        self.name = 'default'
        self.can_hurt = []

class Endurance:
    def __init__(self):
        self.surface = None
        self.particles = None
        self.bullets = None
        self.ships = None
        self.width = 1366
        self.height = 768
        self.events = []

    def add_event(self, event_type, *data):
        self.events.append([event_type, data])

    def play(self):
        red_team = Team()
        red_team.color = (255, 100, 100)
        blue_team = Team()
        blue_team.color = (100, 100, 255)
        green_team = Team()
        green_team.color = (100, 255, 100)
        
        blue_team.can_hurt.append(red_team)
        blue_team.can_hurt.append(green_team)  
        green_team.can_hurt.append(red_team)
        green_team.can_hurt.append(blue_team)        
        red_team.can_hurt.append(blue_team)
        red_team.can_hurt.append(green_team)

        human = Player(game = self)
        human.request_ship()
        human.name = 'Andrei'
        human.lives = 20
        ai1 = Player(game = self, ai = True)
        ai1.request_ship()
        ai1.name = 'Bob'
        ai2 = Player(game = self, ai = True)
        ai2.request_ship()
        ai2.name = 'Smith'

        human.set_team(red_team)
        ai1.set_team(blue_team)
        ai2.set_team(green_team)

        game_over = False

        while not game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:                
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.size
                    pygame.display.set_mode((self.width, self.height),  pygame.RESIZABLE)
                    self.surface = pygame.Surface((self.width, self.height))
                        
            self.ships.step()
            while self.events:
                event = self.events.pop()
                if event[0] == 'destroy':
                    self.gui.add_kill(random.choice(['{} obliterated {}',
                                                    '{} destroyed {}',
                                                    '{} mutilated {}',
                                                    '{} maimed {}',
                                                    '{} decapitated {}',
                                                    '{} humiliated {}',
                                                    '{} desintegrated {}',
                                                    '{} killed {}',
                                                    '{} left {} in tears',
                                                    '{} disposed of {}',
                                                    "{} decided {}'s days are over"]).format(event[1][0].player.name,
                                                             event[1][1].player.name))
                    event[1][0].player.score += 1
                    event[1][1].player.lives -= 1
                    if event[1][1].player.team in [blue_team, green_team]:
                        event[1][1].player.request_ship()
                    if event[1][1].player is human:
                        if human.lives > 0:
                            event[1][1].player.request_ship()
                        else:
                            game_over = True
                    
                    
            self.gui.step()
            self.bullets.step()
            self.particles.step()
            self.particles.render()
            self.bullets.render()
            self.ships.render()
            self.gui.score = human.score
            self.gui.lives = human.lives
            self.gui.energy = human.ship.energy
            self.gui.render(self.surface)
            self.gui.step()
            window.blit(self.surface, (0,0))
            pygame.display.update()
            clock.tick(60)
            self.gui.fps = clock.get_fps()
            
            self.surface.fill((0,0,0))

pygame.init()
clock = pygame.time.Clock()

window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    
while True:
    game = Endurance()
    game.width, game.height = window.get_size()

    game.surface = pygame.Surface(window.get_size())
    pygame.display.set_caption('AsterDriods')
    game.gui = GUI(game)
    game.particles = ParticleEngine(game)
    game.bullets = BulletEngine(game)
    game.ships = ShipEngine(game)

    game.play()
