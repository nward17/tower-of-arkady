import ConfigParser, pygame, time, random, pygame.locals as pg, sqlite3 as lite
from pygame import mixer

screen = pygame.display.set_mode((672, 512))
# Motion offsets for direction of movement
#     N  E  S   W
DX = [0, 1, 0, -1]
DY = [-1, 0, 1, 0]
map_level = 'INTRO'
map_tile = 'map'

#Items
keyincrement = 0
doorunlock = 0
touchingdoor = 0
fireextinguisher = 0
touchinglaser = 0
laserswitch = 0
floorfall = 0
touchingfire = 0
touchingbomb = 0
secondsitem = 1

#Death
deathfire = 0
deathlaser = 0
deathfall = 0
deathtime = 0
level = 1


# Dimensions of the map tiles
MAP_TILE_WIDTH, MAP_TILE_HEIGHT = 32, 32

ready = False
TIMER1_EVENT = pygame.USEREVENT + 1
seconds = 150

# checks if player has made it past the intro
isPastIntro = False

mixer.init()


class TileCache(object):
    #Loads tilesets into a global cache

    def __init__(self,  width=32, height=None):
        self.width = width
        self.height = height or width
        self.cache = {}

    def __getitem__(self, filename):
        #Returns a table of tiles

        key = (filename, self.width, self.height)
        try:
            return self.cache[key]
        except KeyError:
            tile_table = self._load_tile_table(filename, self.width,
                                               self.height)
            self.cache[key] = tile_table
            return tile_table

    def _load_tile_table(self, filename, width, height):
        #Splices an image into 

        image = pygame.image.load(filename).convert_alpha()
        image_width, image_height = image.get_size()
        tile_table = []
        for tile_x in range(0, image_width/width):
            line = []
            tile_table.append(line)
            for tile_y in range(0, image_height/height):
                rect = (tile_x*width, tile_y*height, width, height)
                line.append(image.subsurface(rect))
        return tile_table


class SortedUpdates(pygame.sprite.RenderUpdates):
    #Sort sprites by depth

    def sprites(self):
        #The list of sprites that will get sorted by depth
        return sorted(self.spritedict.keys(), key=lambda sprite: sprite.depth)


class Sprite(pygame.sprite.Sprite):
    #Animated sprites(items)
    #Base class for the player

    is_player = False

    def __init__(self, pos=(0, 0), frames=None):
        super(Sprite, self).__init__()
        if frames:
            self.frames = frames
        self.image = self.frames[0][0]
        self.rect = self.image.get_rect()
        self.animation = self.stand_animation()
        self.pos = pos

    def _get_pos(self):
        #Checks the current positon of sprites on the map

        return (self.rect.midbottom[0]-16)/32, (self.rect.midbottom[1]-32)/32

    def _set_pos(self, pos):
        #Sets sprite position and depth on the map

        self.rect.midbottom = pos[0]*32+16, pos[1]*32+32
        self.depth = self.rect.midbottom[1]

    pos = property(_get_pos, _set_pos)

    def move(self, dx, dy):
        #Changes sprite position

        self.rect.move_ip(dx, dy)
        self.depth = self.rect.midbottom[1]

    def stand_animation(self):
        #Default sprite animation

        while True:
            # Change to next frame every two ticks
            for frame in self.frames[0]:
                self.image = frame
                yield None
                yield None

    def update(self, *args):
        #Updates and runs current animation(Makes character sprite image change)
        self.animation.next()


class Player(Sprite):
    #Display the main character

    is_player = True

    def __init__(self, pos=(1, 1)):
        self.frames = SPRITE_CACHE["images/player.png"]
        Sprite.__init__(self, pos)
        self.direction = 0
        self.animation = None
        self.image = self.frames[self.direction][0]

    def walk_animation(self):
        #Player walking animation

        # This animation is hardcoded for 4 frames and 32x32 map tiles
        for frame in range(4):
            self.image = self.frames[self.direction][frame]
            yield None
            self.move(4*DX[self.direction], 4*DY[self.direction])
            yield None
            self.move(4*DX[self.direction], 4*DY[self.direction])

    def update(self, *args):
        #Runs the current animation or sets character to stand still if no input

        if self.animation is None:
            self.image = self.frames[self.direction][0]
        else:
            try:
                self.animation.next()
            except StopIteration:
                self.animation = None

class Level(object):
    global map_level, map_tile, image, level, ready
    #Load and store the map of the level

    def __init__(self, filename="level.map"):
        self.tileset = ''
        self.map = []
        self.items = {}
        self.key = {}
        self.width = 0
        self.height = 0
        self.load_file(filename)
        
    def load_file(self, filename="level.map"):
        #Load the level from the specified file

        parser = ConfigParser.ConfigParser()
        parser.read(filename)
        self.tileset = parser.get("TILESET", "tileset")
        self.map = parser.get(map_level, map_tile).split("\n")
        for section in parser.sections():
            if len(section) == 1:
                desc = dict(parser.items(section))
                self.key[section] = desc
        self.width = len(self.map[0])
        self.height = len(self.map)
        for y, line in enumerate(self.map):
            for x, c in enumerate(line):
                if not self.is_wall(x, y) and 'sprite' in self.key[c]:
                    self.items[(x, y)] = self.key[c]
                    
    def loadIntro(self, surface):
        # fonts
        titleFont = pygame.font.SysFont(None, 46, italic=True)
        pressAnyKeyFont = pygame.font.SysFont(None, 30, italic=True)

        # text
        title = titleFont.render('Tower of Arkady', True, (117, 109, 236))
        pressAnyKey = pressAnyKeyFont.render('Enter your name, then press Space to play', True, (255, 255, 255))

        # set location
        titleRect = title.get_rect()
        titleRect.centerx = surface.get_rect().centerx
        titleRect.centery = surface.get_rect().centery-200

        # set location
        pressAnyKeyRect = pressAnyKey.get_rect()
        pressAnyKeyRect.centerx = surface.get_rect().centerx
        pressAnyKeyRect.centery = surface.get_rect().centery

        # add to surface
        surface.blit(title, titleRect)
        surface.blit(pressAnyKey, pressAnyKeyRect)

        
    def tutorial(self, surface):
        # font
        font = pygame.font.SysFont('Courier New', 18, bold=True, italic=True)
        
        # text
        laser = font.render('Turn off the laser to proceed through the gate.', True, (0, 0, 0))
        controls = font.render('Controls: Arrow Keys or WASD', True, (0, 0, 0))
        fire = font.render('Grab the fire extinguisher to put out the fire.', True, (0, 0, 0))       
        holekey = font.render('Avoid the hole and grab the keycard.', True, (0, 0, 0))
        timer = font.render("The bomb's timer will start once you exit this room.", True, (0, 0, 0))
        space = font.render("Use SPACEBAR to open doors and defuse the bomb.", True, (0, 0, 0))
        
        # add to surface
        surface.blit(controls, (190, 450))
        surface.blit(fire, (100, 230))
        surface.blit(space, (90, 125))
        surface.blit(holekey, (175, 170))
        surface.blit(timer, (60, 405))
        surface.blit(laser, (100, 355))

    def render(self):
        global isPastIntro
        #Draws the level on the surface

        wall = self.is_wall
        tiles = MAP_CACHE[self.tileset]
        image = pygame.Surface((self.width*MAP_TILE_WIDTH, self.height*MAP_TILE_HEIGHT))
        
        overlays = {}
        
        if not isPastIntro:
            self.loadIntro(image)
            isPastIntro = True
        else:
            for map_y, line in enumerate(self.map):
                for map_x, c in enumerate(line):
                    try:
                            tile = self.key[c]['tile'].split(',')
                            tile = int(tile[0]), int(tile[1])
                    except (ValueError, KeyError):
                            # Default to ground tile
                            tile = 0, 3
                    tile_image = tiles[tile[0]][tile[1]]
                    image.blit(tile_image,
                               (map_x*MAP_TILE_WIDTH, map_y*MAP_TILE_HEIGHT))
                    
        if map_level == 'TUTORIAL':
            self.tutorial(image)

        return image, overlays

    def get_tile(self, x, y):
#########
        global seconds, secondsitem, keyincrement, touchingbomb, floorfall, doorunlock, map_level, map_tile, touchinglaser, laserswitch, touchingdoor, fireextinguisher, touchingfire, ready
        #Identifies what is on a specific tile on the map
        
        pickup = mixer.Sound("sounds/pickup.wav")
        extinguish = mixer.Sound("sounds/extinguish.wav")
        passingLaser = mixer.Sound("sounds/passingLaser.wav")
        
        if self.map[y][x] == 'F' and ready and fireextinguisher == 1:
            extinguish.play()
        if (self.map[y][x] == 'L' or self.map[y][x] == 'l') and ready and fireextinguisher == 1:
            passingLaser.play()
        
        if self.map[y][x] == 'K' and ready and doorunlock == 0:
            pickup.play()
            doorunlock = 1
#########
        if self.map[y][x] == 'S' and secondsitem == 1 and ready:
            tmp_list = list(self.map[y])
            tmp_list[x] = 'o'
            new_str = ''.join(tmp_list)
            self.map[y] = new_str
            s = random.randint(5,20)
            pickup.play()
            secondsitem = 1
            seconds += s
#########
        if self.map[y][x] == 'F' and ready:
            tmp_list = list(self.map[y])
            tmp_list[x] = 'o'
            new_str = ''.join(tmp_list)
            self.map[y] = new_str
            touchingfire = 1
        if (self.map[y][x] == 'L' or self.map[y][x] == 'l') and ready:
            if laserswitch == 1:
                passingLaser.play()
            tmp_list = list(self.map[y])
            tmp_list[x] = 'o'
            new_str = ''.join(tmp_list)
            self.map[y] = new_str
            touchinglaser = 1
        if self.map[y][x] == 'y' and ready:
            floorfall = 1
        if self.map[y][x] == ')' and ready:
            touchingbomb = 1
            
        if self.map[y][x] == '*' and ready:
            if laserswitch == 0:
                switch = mixer.Sound("sounds/switch.wav")
                switch.play()
                lasergoodv = pygame.image.load('images/lasergoodv.png')
                lasergoodv.convert_alpha()
                lasergood = pygame.image.load('images/lasergood.png')
                lasergood.convert_alpha()
                if map_tile == 'ma1':
                    screen.blit(lasergood, (320, 320))
                if map_tile == 'ma4':
                    screen.blit(lasergoodv, (384, 160))
                    screen.blit(lasergoodv, (224, 288))
                    screen.blit(lasergoodv, (288, 288))
                    screen.blit(lasergoodv, (352, 288))
                    screen.blit(lasergoodv, (416, 288))
                    laserswitch = 1
                if map_tile == 'm44':
                    screen.blit(lasergoodv, (256, 256))
                    screen.blit(lasergood, (480, 160))
                    screen.blit(lasergood, (544, 288))
                if map_tile == '444':
                    screen.blit(lasergoodv, (192, 224))
                    screen.blit(lasergoodv, (320, 224))
                    screen.blit(lasergoodv, (448, 224))
                    screen.blit(lasergood, (352, 160))
                    screen.blit(lasergood, (544, 352))
                    screen.blit(lasergood, (608, 352))
                    laserswitch = 1
                if map_tile == 'ma5':
                    screen.blit(lasergood, (608, 160))
                    screen.blit(lasergood, (320, 160))
                    screen.blit(lasergoodv, (288, 288))
                    screen.blit(lasergoodv, (352, 288))
                    laserswitch = 1
                if map_tile == 'm55':
                    screen.blit(lasergood, (224, 160))
                    screen.blit(lasergood, (320, 160))
                    screen.blit(lasergood, (160, 352))
                    laserswitch = 1
                if map_tile == '555':
                    screen.blit(lasergood, (224, 416))
                    screen.blit(lasergood, (128, 352))
                    screen.blit(lasergood, (320, 192))
                    screen.blit(lasergoodv, (544, 192))
                    laserswitch = 1
                if map_tile == 'ma6':
                    screen.blit(lasergood, (96, 128))
                    screen.blit(lasergood, (320, 128))
                    screen.blit(lasergood, (544, 128))
                    laserswitch = 1
                laserswitch = 1
        if self.map[y][x] == 'f' and ready and fireextinguisher == 0:
            pickup.play()
            fireextinguisher = 1
        if self.map[y][x] == 'd' and ready:
            touchingdoor = 1
        elif self.map[y][x] == 'w' and ready:
            touchingdoor = 0
        elif self.map[y][x] == 'o' and ready:
            touchingdoor = 0
            
        try:
            char = self.map[y][x]
        except IndexError:
            return {}
        try:
            return self.key[char]
        except KeyError:
            return {}

    def get_bool(self, x, y, name):
        #Is flag set for specified position

        value = self.get_tile(x, y).get(name)
        return value in (True, 1, 'true', 'yes', 'True', 'Yes', '1', 'on', 'On')

    def is_wall(self, x, y):
        #Check for wall

        return self.get_bool(x, y, 'wall')

    def is_blocking(self, x, y):
        #Does area block movement?

        if not 0 <= x < self.width or not 0 <= y < self.height:
            return True
        return self.get_bool(x, y, 'block')


        
class Game(object):
    #Main game

    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.pressed_key = None
        self.game_over = False
        self.sprites = SortedUpdates()
        self.overlays = pygame.sprite.RenderUpdates()
        self.use_level(Level())
        self.victorious = False
        

    def use_level(self, level):
        global sprite, itemcheck
        #sets current level
        self.sprites = SortedUpdates()
        self.overlays = pygame.sprite.RenderUpdates()
        self.level = level
        # Populate the game with the level's objects
        x = 0
        for pos, tile in level.items.iteritems():
            if tile.get("player") in ('true', '1', 'yes', 'on'):
                sprite = Player(pos)
                self.player = sprite
                self.sprites.add(sprite)
            else:
                itemcheck = Sprite(pos, SPRITE_CACHE[tile["sprite"]])
                self.sprites.add(itemcheck)

        # Render the level map
        self.background, overlays = self.level.render()
        # Add the overlays for the level map
        for (x, y), image in overlays.iteritems():
            overlay = pygame.sprite.Sprite(self.overlays)
            overlay.image = image
            overlay.rect = image.get_rect().move(x*32, y*32-32)

    def gameover(self):
        global deathfire, deathlaser, deathfall, deathtime, fireextinguisher
        fireextinguisher = 0
        
        # set game state
        self.game_over = True
        
        gameoverfire = pygame.image.load("images/deathfire.png")
        gameoverfire.convert()
        gameoverlaser = pygame.image.load("images/laserdeath.png")
        gameoverlaser.convert()
        gameoverfall = pygame.image.load("images/gameoverfall.png")
        gameoverfall.convert()
        gameovertime = pygame.image.load("images/deathtimer.png")
        gameovertime.convert()
        
        if deathfire == 1:
            screen.blit(gameoverfire, (0, 0))
            pygame.display.flip()
        if deathlaser == 1:
            screen.blit(gameoverlaser, (0, 0))
            pygame.display.flip()
        if deathfall == 1:
            screen.blit(gameoverfall, (0, 0))
            pygame.display.flip()
        if deathtime == 1:
            screen.blit(gameovertime, (0, 0))
            pygame.display.flip()
            
        self.sprites.remove(sprite)

        # play game over sound
        gameOver = mixer.Sound("sounds/gameOver.wav")
        gameOver.play()
    def movementchecks(self):
        global deathfire, deathlaser, deathfall, deathtime, touchingbomb, touchingfire, fireextinguisher, laserswitch, touchinglaser, floorfall
        if fireextinguisher == 0 and touchingfire == 1:
            deathfire = 1
 
        if laserswitch == 0 and touchinglaser == 1:
            deathlaser = 1

        if floorfall == 1:
            deathfall = 1


    def control(self):
        global seconds, secondsitem, deathfire, level, deathlaser, deathfall, touchingbomb, deathtime, map_level, map_tile, Items, screen, doorunlock, touchinglaser, floorfall, laserswitch, ready, fireextinguisher, touchingfire

        #controls for the game
        keys = pygame.key.get_pressed()

                    
        def pressed(key):
            #Check for what key is pressed
            return self.pressed_key == key or keys[key]
        
        def walk(d):
            global screen, sprite, fire, itemcheck, level
            #Walk in certain direction
            x, y = self.player.pos
            self.player.direction = d
            if not self.level.is_blocking(x+DX[d], y+DY[d]):
                self.player.animation = self.player.walk_animation()

        if pressed(pg.K_UP) or pressed(pg.K_w):
            ready = True
            if deathfall == 1:
                self.gameover()
            if deathfire == 1:
                self.gameover()
            if deathlaser == 1:
                self.gameover()
            walk(0)
        elif pressed(pg.K_DOWN) or pressed(pg.K_s):
            if deathfall == 1:
                self.gameover()
            if deathfire == 1:
                self.gameover()
            if deathlaser == 1:
                self.gameover()
            walk(2)
        elif pressed(pg.K_LEFT) or pressed(pg.K_a):
            if deathfall == 1:
                self.gameover()
            if deathfire == 1:
                self.gameover()
            if deathlaser == 1:
                self.gameover()
            walk(3)
        elif pressed(pg.K_RIGHT) or pressed(pg.K_d):
            if deathfall == 1:
                self.gameover()
            if deathfire == 1:
                self.gameover()
            if deathlaser == 1:
                self.gameover()
            walk(1)
        #elif pressed(pg.K_SEMICOLON):
           #self.victorious = True
        elif pressed(pg.K_SPACE):
            if touchingbomb == 1 and self.player.direction == 0:
                self.victorious = True
            if doorunlock == 1 and touchingdoor == 1 and self.player.direction ==0:
                ready = False
                if level == 1 and doorunlock == 1 and touchingdoor == 1 and self.player.direction == 0:
                    self.start_timer1()
                    x = random.randint(1,3)
                    #Checks to see if room will generate a time bonus
                    secondsitem = random.randint(1,3)
                    if x == 1:
                        map_tile = 'ma2'
                        map_level = 'LEVEL1'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        screen.blit(keycard, (256, 128))
                        screen.blit(fireextinguisher, (32,128))
                        screen.blit(fire, (32, 256))
                        screen.blit(fire, (32, 352))
                        screen.blit(fire, (32, 388))
                        screen.blit(fire, (32, 416))
                        screen.blit(fire, (224, 288))
                        screen.blit(fire, (576, 192))
                        #Generate time bonus in room if seconds value is 1
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (320, 256))
                        level = 2
                
                    elif x == 2:
                        map_tile = 'm22'
                        map_level = 'LEVEL1'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        screen.blit(keycard, (32, 128))
                        screen.blit(fireextinguisher, (32,192))
                        screen.blit(fire, (64, 256))
                        screen.blit(fire, (352, 288))
                        screen.blit(fire, (288, 448))
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (480, 192))
                        level = 2
                        
                    else:
                        map_tile = '222'
                        map_level = 'LEVEL1'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        screen.blit(keycard, (96, 128))
                        screen.blit(fireextinguisher, (512,224))
                        screen.blit(fire, (160, 320))
                        screen.blit(fire, (512, 256))
                        screen.blit(fire, (320, 160))
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (544, 128))
                        level = 2
                    doorunlock = 0
                    touchingfire = 0
                    fireextinguisher = 0
                    touchinglaser = 0
                    floorfall = 0
                    laserswitch = 0
                    pygame.display.flip()
                    ready = False
                    
                        
                elif level == 2 and doorunlock == 1 and touchingdoor == 1 and self.player.direction == 0:
                    x = random.randint(1,3)
                    secondsitem = random.randint(1,3)
                    if x == 1:
                        map_tile = 'ma3'
                        map_level = 'LEVEL2'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        crack = pygame.image.load('images/crack.png')
                        crack.convert_alpha()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        screen.blit(crack, (32, 256))
                        screen.blit(crack, (32, 384))
                        screen.blit(crack, (64, 320))
                        screen.blit(crack, (64, 192))
                        screen.blit(crack, (288, 256))
                        screen.blit(crack, (320, 320))
                        screen.blit(crack, (352, 224))
                        screen.blit(crack, (576, 192))
                        screen.blit(crack, (576, 256))
                        screen.blit(keycard, (544, 256))
                        screen.blit(fireextinguisher, (128,160))
                        screen.blit(fire, (128, 256))
                        screen.blit(fire, (352, 384))
                        screen.blit(fire, (352, 128))
                        screen.blit(fire, (608, 192))
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (128, 224))
                        level = 3
                    if x == 2:
                        map_tile = 'm33'
                        map_level = 'LEVEL2'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        crack = pygame.image.load('images/crack.png')
                        crack.convert_alpha()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        screen.blit(crack, (320, 384))
                        screen.blit(crack, (256, 384))
                        screen.blit(crack, (384, 320))
                        screen.blit(crack, (416, 448))
                        screen.blit(crack, (32, 160))
                        screen.blit(crack, (32, 288))
                        screen.blit(keycard, (320, 320))
                        screen.blit(fireextinguisher, (32,128))
                        screen.blit(fire, (384, 256))
                        screen.blit(fire, (256, 224))
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (608, 128))
                        level = 3
                    if x == 3:
                        map_tile = '333'
                        map_level = 'LEVEL2'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        crack = pygame.image.load('images/crack.png')
                        crack.convert_alpha()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        screen.blit(crack, (32, 192))
                        screen.blit(crack, (448, 192))
                        screen.blit(crack, (352, 352))
                        screen.blit(crack, (64, 128))
                        screen.blit(crack, (512, 448))
                        screen.blit(crack, (512, 288))
                        screen.blit(keycard, (608, 448))
                        screen.blit(fireextinguisher, (32,128))
                        screen.blit(fire, (160, 256))
                        screen.blit(fire, (192, 320))
                        screen.blit(fire, (256, 224))
                        screen.blit(fire, (384, 256))
                        screen.blit(fire, (480, 224))
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (608, 288))
                        level = 3
                        
                    doorunlock = 0
                    touchingfire = 0
                    fireextinguisher = 0
                    touchinglaser = 0
                    floorfall = 0
                    laserswitch = 0
                    pygame.display.flip()
                    ready = False
                        
                elif level == 3 and doorunlock == 1 and touchingdoor == 1 and self.player.direction == 0:
                    x = random.randint(1,3)
                    secondsitem = random.randint(1,3)
                    if x == 1:
                        map_tile = 'ma4'
                        map_level = 'LEVEL3'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        laserv = pygame.image.load('images/laserv.png')
                        laserv.convert_alpha()
                        switch = pygame.image.load('images/switch.png')
                        switch.convert_alpha()
                        screen.blit(laserv, (384, 160))
                        screen.blit(laserv, (224, 288))
                        screen.blit(laserv, (288, 288))
                        screen.blit(laserv, (352, 288))
                        screen.blit(laserv, (416, 288))
                        screen.blit(switch, (128, 256))
                        screen.blit(keycard, (416, 128))
                        screen.blit(fireextinguisher, (512, 256))
                        screen.blit(fire, (416, 160))
                        screen.blit(fire, (192, 320))
                        screen.blit(fire, (352, 352))
                        screen.blit(fire, (544, 288))
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (320, 384))
                        level = 4
                    if x == 2:
                        map_tile = 'm44'
                        map_level = 'LEVEL3'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        laserv = pygame.image.load('images/laserv.png')
                        laserv.convert_alpha()
                        laser = pygame.image.load('images/laser.png')
                        laser.convert_alpha()
                        switch = pygame.image.load('images/switch.png')
                        switch.convert_alpha()
                        screen.blit(laserv, (256, 256))
                        screen.blit(laser, (480, 160))
                        screen.blit(laser, (544, 288))
                        screen.blit(switch, (480, 320))
                        screen.blit(keycard, (608, 128))
                        screen.blit(fireextinguisher, (32, 128))
                        screen.blit(fire, (288, 320))
                        screen.blit(fire, (608, 352))
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (64, 448))
                        level = 4
                    if x == 3:
                        map_tile = '444'
                        map_level = 'LEVEL3'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        laserv = pygame.image.load('images/laserv.png')
                        laserv.convert_alpha()
                        laser = pygame.image.load('images/laser.png')
                        laser.convert_alpha()
                        switch = pygame.image.load('images/switch.png')
                        switch.convert_alpha()
                        screen.blit(laserv, (192, 224))
                        screen.blit(laserv, (320, 224))
                        screen.blit(laserv, (448, 224))
                        screen.blit(laser, (352, 160))
                        screen.blit(laser, (544, 352))
                        screen.blit(laser, (608, 352))
                        screen.blit(switch, (608, 160))
                        screen.blit(keycard, (544, 448))
                        screen.blit(fireextinguisher, (32, 128))
                        screen.blit(fire, (288, 160))
                        screen.blit(fire, (256, 320))
                        screen.blit(fire, (384, 320))
                        screen.blit(fire, (32, 352))
                        screen.blit(fire, (96, 352))
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (96, 448))
                        level = 4

                    doorunlock = 0
                    touchingfire = 0
                    fireextinguisher = 0
                    touchinglaser = 0
                    floorfall = 0
                    laserswitch = 0
                    pygame.display.flip()
                    ready = False

                elif level == 4 and doorunlock == 1 and touchingdoor == 1 and self.player.direction == 0:
                    x = random.randint(1,3)
                    secondsitem = random.randint(1,3)
                    if x == 1:
                        map_tile = 'ma5'
                        map_level = 'LEVEL4'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        laserv = pygame.image.load('images/laserv.png')
                        laserv.convert_alpha()
                        laser = pygame.image.load('images/laser.png')
                        laser.convert_alpha()
                        switch = pygame.image.load('images/switch.png')
                        switch.convert_alpha()
                        crack = pygame.image.load('images/crack.png')
                        crack.convert_alpha()
                        screen.blit(crack, (96, 192))
                        screen.blit(crack, (128, 256))
                        screen.blit(crack, (416, 256))
                        screen.blit(crack, (608, 384))
                        screen.blit(laser, (608, 160))
                        screen.blit(laser, (320, 160))
                        screen.blit(laserv, (288, 288))
                        screen.blit(laserv, (352, 288))
                        screen.blit(switch, (192, 256))
                        screen.blit(keycard, (608, 128))
                        screen.blit(fireextinguisher, (256, 448))
                        screen.blit(fire, (288, 448))
                        screen.blit(fire, (288, 352))
                        screen.blit(fire, (192, 288))
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (608, 448))
                        level = 5
                    if x == 2:
                        map_tile = 'm55'
                        map_level = 'LEVEL4'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        laserv = pygame.image.load('images/laserv.png')
                        laserv.convert_alpha()
                        laser = pygame.image.load('images/laser.png')
                        laser.convert_alpha()
                        switch = pygame.image.load('images/switch.png')
                        switch.convert_alpha()
                        crack = pygame.image.load('images/crack.png')
                        crack.convert_alpha()
                        screen.blit(crack, (608, 128))
                        screen.blit(crack, (544, 160))
                        screen.blit(crack, (192, 192))
                        screen.blit(laser, (224, 160))
                        screen.blit(laser, (320, 160))
                        screen.blit(laser, (160, 352))
                        screen.blit(switch, (160, 448))
                        screen.blit(keycard, (384, 416))
                        screen.blit(fireextinguisher, (416, 128))
                        screen.blit(fire, (320, 224))
                        screen.blit(fire, (544, 256))
                        screen.blit(fire, (192, 384))
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (64, 160))
                        level = 5
                    if x == 3:
                        map_tile = '555'
                        map_level = 'LEVEL4'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        keycard = pygame.image.load("images/key.png")
                        keycard.convert_alpha()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        laserv = pygame.image.load('images/laserv.png')
                        laserv.convert_alpha()
                        laser = pygame.image.load('images/laser.png')
                        laser.convert_alpha()
                        switch = pygame.image.load('images/switch.png')
                        switch.convert_alpha()
                        crack = pygame.image.load('images/crack.png')
                        crack.convert_alpha()
                        screen.blit(crack, (224, 160))
                        screen.blit(crack, (384, 192))
                        screen.blit(crack, (576, 288))
                        screen.blit(laser, (224, 416))
                        screen.blit(laser, (128, 352))
                        screen.blit(laser, (320, 192))
                        screen.blit(laserv, (544, 192))
                        screen.blit(switch, (192, 256))
                        screen.blit(keycard, (256, 448))
                        screen.blit(fireextinguisher, (480, 352))
                        screen.blit(fire, (384, 160))
                        screen.blit(fire, (256, 192))
                        if secondsitem == 1:
                            timeforward = pygame.image.load("images/timeplus.png")
                            timeforward.convert_alpha()
                            screen.blit(timeforward, (448, 128))
                        level = 5

                    doorunlock = 0
                    touchingfire = 0
                    fireextinguisher = 0
                    touchinglaser = 0
                    floorfall = 0
                    laserswitch = 0
                    pygame.display.flip()
                    ready = False
                elif level == 5 and doorunlock == 1 and touchingdoor == 1 and self.player.direction == 0:
                    x = 1
                    if x == 1:
                        map_tile = 'ma6'
                        map_level = 'LEVEL5'
                        self.use_level(Level())
                        self.screen.blit(self.background, (0, 0))
                        self.overlays.draw(self.screen)
                        pygame.display.flip()
                        fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                        fireextinguisher.convert_alpha()
                        fire = pygame.image.load("images/fire1.png")
                        fire.convert_alpha()
                        laserv = pygame.image.load('images/laserv.png')
                        laserv.convert_alpha()
                        laser = pygame.image.load('images/laser.png')
                        laser.convert_alpha()
                        switch = pygame.image.load('images/switch.png')
                        switch.convert_alpha()
                        crack = pygame.image.load('images/crack.png')
                        crack.convert_alpha()
                        timerbomb = pygame.image.load('images/timerbomb.png')
                        timerbomb.convert_alpha()
                        screen.blit(timerbomb, (320, 224))
                        screen.blit(crack, (352, 352))
                        screen.blit(crack, (544, 224))
                        screen.blit(laser, (96, 128))
                        screen.blit(laser, (320, 128))
                        screen.blit(laser, (544, 128))
                        screen.blit(switch, (320, 320))
                        screen.blit(fireextinguisher, (544, 160))
                        screen.blit(fire, (192, 160))
                        screen.blit(fire, (160, 160))
                        screen.blit(fire, (320, 160))
                        level = 5

                    doorunlock = 0
                    touchingfire = 0
                    fireextinguisher = 0
                    touchinglaser = 0
                    floorfall = 0
                    laserswitch = 0
                    pygame.display.flip()
                    ready = False

        self.pressed_key = None

    def start_timer1(self):
        global seconds, TIMER1_EVENT
        
        pygame.time.set_timer(TIMER1_EVENT, 1000)

    def on_timer1(self):
        global seconds,TIMER1_EVENT, deathtime
        
        if not self.victorious and not self.game_over and map_level != 'TUTORIAL' and map_level != 'INTRO':
            seconds -= 1
        if seconds <= 0:
            deathtime = 1
        
    def main(self):
        global map_level, map_tile, touchingfire, Items, deathtime, deathlaser, secondsitem, seconds, secondsitem, deathfire, level, deathlaser, deathfall, touchingbomb, deathtime, map_level, map_tile, Items, screen, doorunlock, touchinglaser, floorfall, laserswitch, ready
        #Main loop
        clock = pygame.time.Clock()
        # Draw the whole screen initially
        self.screen.blit(self.background, (0, 0))
        self.overlays.draw(self.screen)
        pygame.display.flip()
        introscreen = pygame.image.load("images/toa.png")
        introscreen.convert()
        screen.blit(introscreen, (0, 0))
        pygame.display.flip()
        # The main game loop
        while not self.game_over:
            if deathtime == 1:
                self.gameover()
            
            # Don't clear shadows and overlays, only sprites.
            self.sprites.clear(self.screen, self.background)
            self.sprites.update()
            # Check for touching an item (Death Check)
            self.movementchecks()
            
            # If the player's animation is finished, check for keypresses
            if map_level == 'INTRO':
                keys = pygame.key.get_pressed()

                if self.pressed_key == pg.K_SPACE or keys[pg.K_SPACE]:
                    map_tile = 'ma1'
                    map_level = 'TUTORIAL'
                    self.use_level(Level())
                    
                    # Draw the whole screen initially
                    self.screen.blit(self.background, (0, 0))
                    self.overlays.draw(self.screen)
                    pygame.display.flip()
                    keycard = pygame.image.load("images/key.png")
                    keycard.convert_alpha()
                    fireextinguisher = pygame.image.load("images/fireextinguisher.png")
                    fireextinguisher.convert_alpha()
                    fire = pygame.image.load('images/fire1.png')
                    fire.convert_alpha()
                    laser = pygame.image.load('images/laser.png')
                    laser.convert_alpha()
                    switch = pygame.image.load('images/switch.png')
                    switch.convert_alpha()
                    crack = pygame.image.load('images/crack.png')
                    crack.convert_alpha()
                    screen.blit(crack, (64, 160))
                    screen.blit(keycard, (32, 160))
                    screen.blit(fireextinguisher, (32, 224))
                    screen.blit(fire, (320, 192))
                    screen.blit(laser, (320, 320))
                    screen.blit(switch, (32, 320)) 
                    pygame.display.flip()
                    


            else:
                if self.player.animation is None:
                    self.control()
                    self.player.update()
            # Don't add shadows to dirty rectangles, as they already fit inside
            # sprite rectangles.
            dirty = self.sprites.draw(self.screen)            
            self.overlays.draw(self.screen)
            # Update the dirty areas of the screen
            pygame.display.update(dirty)
            # Wait for one tick of the game clock
            clock.tick(40)
            
            if map_level != "INTRO":
                #Bomb Timer Display
                font = pygame.font.SysFont(None, 25, italic=True)
                blackBox = pygame.image.load("images/bombborder.png")
                blackBox.convert_alpha()
                #Timer Formatting
                mm = seconds / 60
                mm = str(mm).zfill(2)
                ss = seconds % 60
                ss = str(ss).zfill(2)
                text = font.render(mm+':'+ss, True, (255, 255, 255))
                self.screen.blit(blackBox, (0,0))
                self.screen.blit(text, (312,20))
                pygame.display.flip()
            
            # Process pygame events
            for event in pygame.event.get():
                if event.type == pg.QUIT:
                    self.game_over = True
                    pygame.quit()
                    exit()
                elif event.type == pg.KEYDOWN:
                    self.pressed_key = event.key
                elif event.type == TIMER1_EVENT:
                    self.on_timer1()
                    
            if self.victorious:
                name = getplayername(screen)
                enternewscore(name, seconds)
                #Here is where a Victory splash screen should go. It should probably show high scores also.
                #Right now it'll just end the game
                font = pygame.font.SysFont('Courier New', 20, italic=True)
                k=0
                Top3 = gethighscores()
                for i in range(3):
                    scoredisplay = font.render(displayhighscores(Top3[k]), True, (255,255,255))
                    screen.blit(scoredisplay, (40,(270+(30*i))))
                    k+=1
                pygame.display.flip()
                self.game_over = True
        self.gameover()
        while self.game_over:
            time.sleep(4)
            seconds = 150
            map_level = 'INTRO'
            map_tile = 'map'
            self.use_level(Level())
            SPRITE_CACHE = TileCache()
            MAP_CACHE = TileCache(MAP_TILE_WIDTH, MAP_TILE_HEIGHT)
            TILE_CACHE = TileCache(32, 32)
            keyincrement = 0
            doorunlock = 0
            touchingdoor = 0
            touchinglaser = 0
            laserswitch = 0
            floorfall = 0
            touchingfire = 0
            touchingbomb = 0
            secondsitem = 1
            deathfire = 0
            deathlaser = 0
            deathfall = 0
            deathtime = 0
            level = 1
            ready = False
            screen #Possibly does nothing?
            Game().main()
            self.game_over = False

def getplayername(display):
    name = ""
    font = pygame.font.SysFont('Courier New', 20, bold=True, italic=True)
    while True:
        #Keyboard name entry routine
        for evt in pygame.event.get():
            if evt.type == pygame.KEYDOWN:
                #limits name to letters
                if evt.unicode.isalpha():
                    #limits name to 12 digits
                    if len(name) < 12:
                        name += evt.unicode
                elif evt.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif evt.key == pygame.K_RETURN and name != "": #Prevents blank entries
                    return name
            elif evt.type == pygame.QUIT:
                return

        highscore = pygame.image.load("images/highscore.png")
        highscore.convert()
        screen.blit(highscore, (0, 0))
        nameprompt = font.render("", True, (255,255,255))
        namedisplay = font.render(name, True, (255,255,255))
        rect2 = namedisplay.get_rect()
        rect2.center = display.get_rect().center
        display.blit(nameprompt, (0,0))
        display.blit(namedisplay, rect2)
        pygame.display.flip()








def displayhighscores(Top3):
    highscores = ""
    highscores = Top3[0].ljust(13)
    highscores += str(Top3[1]).rjust(3) + "s"

    return highscores


def gethighscores():
    con = lite.connect('highscores.db')
    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS HighScores(Name TEXT, TimeRemaining INT)")
        #Enters sample data. High Scores table should have at least three entries at all times
        #Fewer may behave unpredictably.
        cur.executescript("""
            INSERT INTO HighScores VALUES('Chris', 4);
            INSERT INTO HIGHSCORES VALUES('Curtis', 3);
            """)
        #Sorts the scores in descending order
        cur.execute("SELECT * FROM HighScores ORDER BY TimeRemaining DESC")
        #Collects them into a list
        rows = cur.fetchmany(3) #Takes the top 3
        Top3 = []   #List of lists
        for row in rows:
            Top3.append([row[0],row[1]])

    return Top3

def enternewscore(playername, score):
    con = lite.connect('highscores.db')
    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS HighScores(Name TEXT, TimeRemaining INT)")
        cur.execute("INSERT INTO HighScores VALUES(?, ?)", (playername, score))
        print "Added " + playername + " to the database of scores, with time remaining of", (score / 60), "minutes and", \
            (score % 60), "seconds."



if __name__ == "__main__":
    SPRITE_CACHE = TileCache()
    MAP_CACHE = TileCache(MAP_TILE_WIDTH, MAP_TILE_HEIGHT)
    TILE_CACHE = TileCache(32, 32)
    pygame.init()
    screen #Possibly does nothing?
    Game().main()
