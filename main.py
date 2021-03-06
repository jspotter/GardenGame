import pygame, numpy, random

WIDTH = 400
HEIGHT = 300
TRAY_WIDTH = 40
TRAY_SPEED = 1
NUM_TRAYS = 11
PERSON_SPEED = 3
PLANT_BUFFER = 5
PLANT_PLACEMENT_BUFFER = 5
BOTTOM_EDGE_BUFFER = 5
BACKGROUND = (255, 255, 255)

class Sprite(pygame.sprite.Sprite):
    '''
    Credit: https://docs.replit.com/tutorials/14-2d-platform-game
    '''

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def __init__(self, image, startx, starty):
        super().__init__()

        self.image = pygame.image.load(image)
        self.left_image = self.image
        self.right_image = self.image
        self.back_image = self.image
        self.front_image = self.image
        
        self.facing = Sprite.SOUTH

        self.rect = self.image.get_rect()

        self.rect.bottomleft = [startx, starty]

        self.subsprite = None
        self.holder = None
        self.immune_from_obstacles = True
        self.immune_from_semi_obstacles = True

        self.immune_permanently_from_obstacles = False
    
    def change_direction(self, direction):
        if direction == self.facing:
            return

        self.facing = direction
        if self.facing == Sprite.NORTH:
            self.image = self.back_image
        elif self.facing == Sprite.SOUTH:
            self.image = self.front_image
        elif self.facing == Sprite.EAST:
            self.image = self.right_image
        elif self.facing == Sprite.WEST:
            self.image = self.left_image

        if self.subsprite is not None:
            self.subsprite.change_direction(direction)
            self.move_subsprite_to_front()

    def move_subsprite_to_front(self):
        pass

    def get_bottom_edge(self):
        return pygame.Rect(self.rect.left,\
            self.get_rect().bottom - BOTTOM_EDGE_BUFFER,\
            self.get_rect().width, BOTTOM_EDGE_BUFFER)
    
    def get_rect(self):
        return self.rect
    
    def adjust_deltas(self, dx, dy, bounds=False, obstacles=None, semi_obstacles=None):
        '''
        If bounds is set to True, take the bounds
        of the universe into account.
        
        If obstacles is a sequence containing other
        sprites, do not collide with those sprites.

        If move_with contains an object, make sure both
        self and this object can move together without
        collision.

        Return the dx and dy actually moved (may
        be less than parameter values).
        '''
        if self.immune_from_obstacles and \
            not self.immune_permanently_from_obstacles and\
            obstacles is not None and \
            not self.check_collision(0, 0, obstacles):
            
            self.set_immune_from_obstacles(False)

        if obstacles is None or self.immune_from_obstacles:
            obstacles = []
        
        if semi_obstacles is None or self.immune_from_semi_obstacles:
            semi_obstacles = []
        
        if bounds:
            min_dx = max(-self.get_rect().left, dx)
            max_dx = min(WIDTH - self.get_rect().right, dx)
            
            min_dy = max(-self.get_rect().top, dy)
            max_dy = min(HEIGHT - self.get_rect().bottom, dy)

            # Check bounds before moving
            if dx < min_dx:
                dx = min_dx
            elif dx > max_dx:
                dx = max_dx
            
            if dy < min_dy:
                dy = min_dy
            elif dy > max_dy:
                dy = max_dy
    
        if len(obstacles) > 0:
            while self.check_collision(0, dy, obstacles) and dy != 0:
                dy -= numpy.sign(dy)
                
            while self.check_collision(dx, dy, obstacles):
                dx -= numpy.sign(dx)
        
        if len(semi_obstacles) > 0:
            while self.check_semi_collision(0, dy, semi_obstacles) and dy != 0:
                dy -= numpy.sign(dy)
            
            while self.check_semi_collision(dx, dy, semi_obstacles):
                dx -= numpy.sign(dx)

        return dx, dy
    
    def move(self, dx, dy, bounds=False, obstacles=None, semi_obstacles=None):
        '''
        Move this sprite by a certain x and y
        amount, taking into account bounds,
        obstacles, and subsprites.
        '''

        adx, ady = dx, dy
        current_sprite = self
        while True:
            adx, ady = current_sprite.adjust_deltas(adx, ady, bounds, obstacles, semi_obstacles)

            if current_sprite.subsprite is None:
                break
            
            current_sprite = current_sprite.subsprite

        current_sprite = self
        while True:
            current_sprite.move_unsafe(adx, ady)

            if current_sprite.subsprite is None:
                break
            
            current_sprite = current_sprite.subsprite
            
    def move_unsafe(self, dx, dy):
        self.rect.move_ip([dx, dy])

    def update(self):
        pass

    def draw(self, screen):
        screen.blit(self.image, self.rect)
    
    def check_collision(self, x, y, grounds):
        return len(self.get_collisions(x, y, grounds)) != 0
    
    def get_collisions(self, x, y, grounds):
        self.rect.move_ip([x, y])
        collisions = pygame.sprite.spritecollide(self, grounds, False)
        self.rect.move_ip([-x, -y])
        return collisions
    
    def check_semi_collision(self, x, y, grounds):
        self.rect.move_ip([x, y])
        retval = False
        for item in grounds:
            if self.get_bottom_edge().colliderect(item.get_bottom_edge()):
                retval = True
                break
        
        self.rect.move_ip([-x, -y])
        return retval
    
    def set_immune_from_obstacles(self, value):
        self.immune_from_obstacles = value
        # if self.subsprite is not None:
        #     self.subsprite.set_immune_from_obstacles(value)

class Person(Sprite):
    '''
    Represent the game's primary actor.
    '''

    def __init__(self, startx, starty):
        '''
        Inspired by:
        https://docs.replit.com/tutorials/14-2d-platform-game
        '''
        super().__init__("assets/person3_front.png", startx, starty)

        self.immune_from_semi_obstacles = False

        self.front_image = self.image
        self.back_image = pygame.image.load("assets/person3_back.png")
        self.left_image = pygame.image.load("assets/person3_right.png")
        self.left_image = pygame.transform.flip(self.left_image, True, False)
        self.right_image = pygame.image.load("assets/person3_right.png")

        self.speed = PERSON_SPEED
        self.hands_free = True

    def update(self, plants, obstacles, watering_can):
        '''
        Listen for key presses and respond by:
            * moving
            * picking up / setting down plant
            * TODO: picking up / setting down water
        '''
        super().update()

        dx = 0
        dy = 0
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            dx = -self.speed
            self.change_direction(Sprite.WEST)
        elif key[pygame.K_RIGHT]:
            dx = self.speed
            self.change_direction(Sprite.EAST)
        elif key[pygame.K_UP]:
            dy = -self.speed
            self.change_direction(Sprite.NORTH)
        elif key[pygame.K_DOWN]:
            dy = self.speed
            self.change_direction(Sprite.SOUTH)

        if key[pygame.K_SPACE]:
            if self.hands_free:
                self.hands_free = False
                if self.subsprite is None:
                    self.pickup_nearby_object(plants + [watering_can])
                else:
                    self.place_object()
        else:
            self.hands_free = True
        
        if isinstance(self.subsprite, WateringCan):
            if key[pygame.K_RSHIFT] or key[pygame.K_LSHIFT]:
                self.subsprite.water()
            else:
                self.subsprite.stop_watering()
        
        semi_obstacles = [i for i in plants + [watering_can] if i != self.subsprite]
        self.move(dx, dy, True, obstacles, semi_obstacles)
    
    def get_one_step_deltas(self):
        if self.facing == Sprite.NORTH:
            return (0, -1)
        elif self.facing == Sprite.SOUTH:
            return (0, 1)
        elif self.facing == Sprite.EAST:
            return (1, 0)
        elif self.facing == Sprite.WEST:
            return (-1, 0)
    
    def pickup_nearby_object(self, objects):
        '''
        If we don't have an object and there is an object
        nearby, pick up one nearby object and move it
        to the front.
        '''
        if self.subsprite is not None:
            return

        dx, dy = self.get_one_step_deltas()
        nearby_objects = self.get_collisions(dx, dy, objects)

        if len(nearby_objects) > 0:
            self.subsprite = nearby_objects[0]
            if self.subsprite.holder is not None:
                self.subsprite.holder.subsprite = None
            self.subsprite.holder = self
            self.subsprite.change_direction(self.facing)
            self.move_subsprite_to_front()
    
    def get_plant_placement_buffer(self):
        extra_buffer = -PLANT_PLACEMENT_BUFFER
        if self.facing == Sprite.SOUTH:
            extra_buffer = -extra_buffer
        elif self.facing == Sprite.NORTH:
            extra_buffer *= 2
        
        return extra_buffer
    
    def place_object(self):
        '''
        If we have an object, place it down
        '''
        if self.subsprite is None:
            return

        extra_buffer = self.get_plant_placement_buffer()
        self.subsprite.move(0, self.get_rect().bottom - self.subsprite.get_rect().bottom + extra_buffer)
        self.subsprite.holder = None
        self.subsprite = None
        # TODO: allow placement back on conveyor belt?
            
    def move_subsprite_to_front(self):
        '''
        Move the object to the front of our body,
        depending on which direction we are facing.
        '''
        super().move_subsprite_to_front()

        if self.subsprite is None:
            return
        
        my_rect = self.get_rect()
        sub_rect = self.subsprite.get_rect()

        extra_buffer = self.get_plant_placement_buffer()
        if self.facing == Sprite.SOUTH:
            extra_buffer *= 0.5
        else:
            extra_buffer *= 1.5

        if self.facing == Sprite.NORTH:
            self.subsprite.move(\
                my_rect.centerx - sub_rect.centerx, \
                my_rect.bottom - sub_rect.bottom)
        elif self.facing == Sprite.EAST:
            self.subsprite.move(\
                my_rect.centerx - sub_rect.left, \
                my_rect.bottom - sub_rect.bottom)
        if self.facing == Sprite.SOUTH:
            self.subsprite.move(\
                my_rect.centerx - sub_rect.centerx, \
                my_rect.bottom - sub_rect.bottom)
        if self.facing == Sprite.WEST:
            self.subsprite.move(\
                my_rect.centerx - sub_rect.right, \
                my_rect.bottom - sub_rect.bottom)

        self.subsprite.move(0, extra_buffer)

class Container(Sprite):
    def __init__(self, startx, starty):
        super().__init__("assets/pot.png", startx, starty)

class Plant(Sprite):
    '''
    Composite object with a plant and a container.
    '''
    def __init__(self, startx, starty):
        super().__init__("assets/plant1.png", startx, starty)
        self.subsprite = Container(startx, starty)
        self.font = pygame.font.SysFont('Courier', 10)
        
        self.alive = True
        self.underwatered = False
        self.overwatered = False

        self.cycles_without_water = 0
        self.max_cycles_without_water = 1500
        
        self.max_water_level = float(random.randint(10, 20))
        self.water_level = self.max_water_level
        self.water_decay = random.randint(4, 8) / 1000

        self.overwater_amount = 0.0
        self.overwater_limit = self.max_water_level * 0.5

        self.rect.move_ip([
            self.rect.left - self.subsprite.rect.left,
            self.subsprite.rect.top - self.rect.bottom
        ])
    
    def get_rect(self):
        new_left = min(self.rect.left, self.subsprite.rect.left)
        new_right = max(self.rect.right, self.subsprite.rect.right)
        new_top = min(self.rect.top, self.subsprite.rect.top)
        new_bottom = max(self.rect.bottom, self.subsprite.rect.bottom)

        return pygame.Rect(new_left, new_top, new_right - new_left,\
            new_bottom - new_top)

    def get_bottom_edge(self):
        return self.subsprite.get_bottom_edge()
    
    def update(self, cycle, water_spray):
        super().update()

        if water_spray is not None and\
            self.get_rect().colliderect(water_spray.get_rect()):
            self.water_level += 0.05

        self.water_level = max(\
            0.0, self.water_level - self.water_decay)

        if self.water_level >\
            self.max_water_level:
            
            self.overwater_amount += self.water_decay
        
        elif self.overwater_amount > 0.0:
            self.overwater_amount -= min(self.water_decay * 0.25, self.overwater_amount)

        if self.overwater_amount +\
            (self.water_level - self.max_water_level) >\
            self.overwater_limit:
            
            self.alive = False
            self.overwatered = True
        
        if self.water_level < 0.01:
            self.cycles_without_water += 1
            if self.cycles_without_water >=\
                self.max_cycles_without_water:
                
                self.alive = False
                self.underwatered = True
    
    def draw(self, screen):
        super().draw(screen)
        if self.subsprite is not None:
            self.subsprite.draw(screen)
        
        color = (0, 0, 0)
        if self.water_level < 0.1 or self.water_level > self.max_water_level:
            color = (255, 0, 0)

        water_text = self.font.render('water: {}'.format(int(self.water_level)), True, color)
        screen.blit(water_text, (self.rect.x, self.rect.y - water_text.get_rect().height))

class WaterSpray(Sprite):
    '''
    Water coming out of watering can when
    watering can is being used
    '''
    def __init__(self, startx, starty):
        super().__init__('assets/water_down.png', startx, starty)

        self.front_image = self.image
        self.back_image = pygame.image.load('assets/water_up.png')
        self.left_image = pygame.image.load('assets/water_left.png')
        self.right_image = pygame.transform.flip(self.left_image, True, False)

        self.immune_permanently_from_obstacles = True

class WateringCan(Sprite):
    '''
    Watering can sprite used to water plants.
    '''
    def __init__(self, startx, starty):
        super().__init__("assets/watering_can.png", startx, starty)

        self.left_image = self.image
        self.right_image = pygame.transform.flip(self.left_image, True, False)
        self.back_image = pygame.image.load('assets/watering_can_back.png')
        self.front_image = pygame.image.load('assets/watering_can_front.png')
    
    def move_subsprite_to_front(self):
        super().move_subsprite_to_front()
        
        if self.subsprite is None:
            return
        
        my_rect = self.get_rect()
        sub_rect = self.subsprite.get_rect()

        if self.facing == Sprite.NORTH:
            self.subsprite.move(\
                my_rect.centerx - sub_rect.centerx, \
                my_rect.top - sub_rect.bottom)
        elif self.facing == Sprite.EAST:
            self.subsprite.move(\
                my_rect.right - sub_rect.left, \
                my_rect.centery - sub_rect.centery)
        if self.facing == Sprite.SOUTH:
            self.subsprite.move(\
                my_rect.centerx - sub_rect.centerx, \
                my_rect.bottom - sub_rect.top)
        if self.facing == Sprite.WEST:
            self.subsprite.move(\
                my_rect.left - sub_rect.right, \
                my_rect.centery - sub_rect.centery)
    
    def water(self):
        self.subsprite = WaterSpray(0, 0)
        self.subsprite.change_direction(self.facing)
        self.move_subsprite_to_front()

    def stop_watering(self):
        self.subsprite = None
    
    def draw(self, screen):
        super().draw(screen)
        if self.subsprite is not None:
            self.subsprite.draw(screen)

class ConveyorBeltTray(Sprite):
    '''
    Single tray on a conveyor belt that carries
    plants
    '''
    def __init__(self, startx, starty):
        super().__init__("assets/tray1.png", startx, starty)
    
    def update(self):
        '''
        Move to the left. Move our plant
        if we have one.
        '''
        super().update()
        self.move(-TRAY_SPEED, 0)

class ConveyorBelt:
    '''
    Constantly moving conveyor belt that can contain
    plants
    '''
    def __init__(self):
        self.trays = []
        for i in range(NUM_TRAYS):
            self.trays.append(ConveyorBeltTray(i * TRAY_WIDTH, HEIGHT))
    
    def update(self):
        '''
        Update each tray in belt
        '''
        [tray.update() for tray in self.trays]
        if self.trays[0].rect.right < 0:
            self.trays[0].move(self.trays[-1].rect.right - self.trays[0].rect.left, 0)
            self.trays = self.trays[1:] + [self.trays[0]]

    def draw(self, screen):
        '''
        Draw each tray in belt
        '''
        [tray.draw(screen) for tray in self.trays]
    
    def add_plant(self):
        '''
        If the last tray is empty, add a plant to it
        '''
        last_tray = self.trays[-1]
        
        # cannot add a new plant if the last
        # tray is already full
        if last_tray.subsprite is not None:
            return None

        new_plant = Plant(last_tray.rect.left + PLANT_BUFFER, last_tray.rect.bottom - PLANT_BUFFER)
        last_tray.subsprite = new_plant
        new_plant.holder = last_tray

        return new_plant
    
    def get_trays(self):
        return self.trays

def get_cause(plant):
    if plant.overwatered:
        return 'You overwatered one of your plants.'
    elif plant.underwatered:
        return 'You underwatered one of your plants.'
    
    return ''

def show_game_start(screen):
    '''
    Instructional screen at beginning
    '''
    game_start_font = pygame.font.SysFont('Courier', 30)
    info_font = pygame.font.SysFont('Courier', 12)

    x = 10
    next_y = 10

    game_start_text = game_start_font.render('Botanical Bonanza', True,\
        (0, 0, 0), (255, 255, 255))
    screen.blit(game_start_text, (x, next_y))
    next_y += game_start_text.get_rect().height

    move_text = info_font.render('  arrow keys:  move',\
        True, (0, 0, 0), (255, 255, 255))
    screen.blit(move_text, (x, next_y))
    next_y += move_text.get_rect().height

    object_text = info_font.render('       space:  pick up or put down object',\
        True, (0, 0, 0), (255, 255, 255))
    screen.blit(object_text, (x, next_y))
    next_y += object_text.get_rect().height

    water_text = info_font.render('       shift:  water plant',\
        True, (0, 0, 0), (255, 255, 255))
    screen.blit(water_text, (x, next_y))
    next_y += water_text.get_rect().height

    enter_text = info_font.render('Press ENTER to play!',\
        True, (0, 0, 0), (255, 255, 255))
    screen.blit(enter_text, (x, next_y))

def show_game_over(plant, score, screen):
    '''
    Shows screen when game ends, along with
    reason for game ending
    '''
    red_x = Sprite("assets/x.png", plant.get_rect().left, plant.get_rect().bottom)
    red_x.draw(screen)

    x = 10
    next_y = 10

    game_over_font = pygame.font.SysFont('Courier', 50)
    info_font = pygame.font.SysFont('Courier', 12)

    game_over_text = game_over_font.render('GAME OVER', True,\
        (0, 0, 0), (255, 255, 255))
    screen.blit(game_over_text, (x, next_y))
    next_y += game_over_text.get_rect().height

    cause_text = info_font.render(get_cause(plant),\
        True, (0, 0, 0), (255, 255, 255))
    screen.blit(cause_text, (x, next_y))
    next_y += cause_text.get_rect().height

    score_text = info_font.render(\
        'Score (plants in play): {}'.format(score),\
        True, (0, 0, 0), (255, 255, 255))
    screen.blit(score_text, (x, next_y))
    next_y += score_text.get_rect().height

    enter_text = info_font.render('Press ENTER to exit.',\
        True, (0, 0, 0), (255, 255, 255))
    screen.blit(enter_text, (x, next_y))

def main():
    '''
    Main game driver.

    Inspired by:
    https://docs.replit.com/tutorials/14-2d-platform-game
    '''
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    person = Person(100, 200)
    watering_can = WateringCan(300, 200)
    plants = []
    belt = ConveyorBelt()
    obstacles = belt.get_trays()
    score = 0
    faulting_plant = None
    
    cycle = 0
    game_start = True
    game_over = False

    while True:
        pygame.event.pump()

        if not game_over:
            screen.fill(BACKGROUND)
            
        if game_start:
            person.draw(screen)
            belt.draw(screen)
            watering_can.draw(screen)
            show_game_start(screen)

        if game_start or game_over:
            key = pygame.key.get_pressed()
            if key[pygame.K_RETURN]:
                if game_start:
                    game_start = False
                else:
                    break
        else:
            person.update(plants, obstacles, watering_can)
            [p.update(cycle, watering_can.subsprite) for p in plants]

            belt.update()

            if cycle % 1000 == 0:
                new_plant = belt.add_plant()
                if new_plant is not None:
                    plants.append(new_plant)
            
            floating_items = plants + [watering_can]
            
            front_items = []
            back_items = []
            for item in floating_items:
                if item == person.subsprite:
                    if person.facing == Sprite.SOUTH:
                        front_items = [item] + front_items
                    else:
                        back_items.append(item)
                elif item.get_rect().bottom < person.get_rect().bottom:
                    back_items.append(item)
                else:
                    front_items.append(item)

            [item.draw(screen) for item in back_items]
            person.draw(screen)
            [item.draw(screen) for item in front_items]

            belt.draw(screen)

            for p in plants:
                if not p.alive:
                    score = len([p for p in plants if not isinstance(p.holder, ConveyorBeltTray)])
                    show_game_over(p, score, screen)
                    game_over = True
                    break
            
            cycle += 1

        pygame.display.flip()

        clock.tick(60)

if __name__ == "__main__":
    main()