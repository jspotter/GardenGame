import pygame, numpy

WIDTH = 400
HEIGHT = 300
TRAY_WIDTH = 40
TRAY_SPEED = 1
NUM_TRAYS = 11
PLANT_BUFFER = 5
BACKGROUND = (255, 255, 255)

class Sprite(pygame.sprite.Sprite):
    '''
    Credit: https://docs.replit.com/tutorials/14-2d-platform-game
    '''
    def __init__(self, image, startx, starty):
        super().__init__()

        self.image = pygame.image.load(image)
        self.rect = self.image.get_rect()

        self.rect.bottomleft = [startx, starty]

        self.subsprite = None
        self.holder = None
        self.immune_from_obstacles = True
    
    def adjust_deltas(self, dx, dy, bounds=False, obstacles=None):
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
        if obstacles is None or self.immune_from_obstacles:
            obstacles = []
        
        if bounds:
            min_dx = max(-self.rect.left, dx)
            max_dx = min(WIDTH - self.rect.right, dx)
            
            min_dy = max(-self.rect.top, dy)
            max_dy = min(HEIGHT - self.rect.bottom, dy)

            # Check bounds before moving
            if dx < min_dx:
                dx = min_dx
            elif dx > max_dx:
                dx = max_dx
            
            if dy < min_dy:
                dy = min_dy
            elif dy > max_dy:
                dy = max_dy
    
        while self.check_collision(0, dy, obstacles):
            dy -= numpy.sign(dy)

        while self.check_collision(dx, dy, obstacles):
            dx -= numpy.sign(dx)
        
        return dx, dy
    
    def move(self, dx, dy, bounds=False, obstacles=None):
        '''
        Move this sprite by a certain x and y
        amount, taking into account bounds,
        obstacles, and subsprites.
        '''

        adx, ady = dx, dy
        current_sprite = self
        while True:
            adx, ady = current_sprite.adjust_deltas(adx, ady, bounds, obstacles)

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
        self.rect.move_ip([x, y])
        collide = pygame.sprite.spritecollideany(self, grounds)
        self.rect.move_ip([-x, -y])
        return collide
    
    def set_immune_from_obstacles(self, value):
        self.immune_from_obstacles = value
        if self.subsprite is not None:
            self.subsprite.set_immune_from_obstacles(value)

class Person(Sprite):
    '''
    Represent the game's primary actor.
    '''

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def __init__(self, startx, starty):
        '''
        Inspired by:
        https://docs.replit.com/tutorials/14-2d-platform-game
        '''
        super().__init__("assets/person3.png", startx, starty)
        self.speed = 4
        self.facing = Person.NORTH
        self.hands_free = True

    def update(self, plants, obstacles):
        '''
        Listen for key presses and respond by:
            * moving
            * picking up / setting down plant
            * TODO: picking up / setting down water
        '''
        dx = 0
        dy = 0
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            dx = -self.speed
            self.change_direction(Person.WEST)
        elif key[pygame.K_RIGHT]:
            dx = self.speed
            self.change_direction(Person.EAST)
        elif key[pygame.K_UP]:
            dy = -self.speed
            self.change_direction(Person.NORTH)
        elif key[pygame.K_DOWN]:
            dy = self.speed
            self.change_direction(Person.SOUTH)

        if key[pygame.K_SPACE]:
            if self.hands_free:
                self.hands_free = False
                if self.subsprite is None:
                    self.pickup_nearby_plant(plants)
                else:
                    self.subsprite.person = None
                    self.subsprite = None
                    # TODO: allow placement back on conveyor belt?
        else:
            self.hands_free = True
        
        self.move(dx, dy, True, obstacles)

    def change_direction(self, direction):
        self.facing = direction
        self.move_plant_to_front()
    
    def pickup_nearby_plant(self, plants):
        '''
        If we don't have a plant and there is a plant
        nearby, pick up one nearby plant and move it
        to the front.
        '''
        if self.subsprite is not None:
            return

        nearby_plants = pygame.sprite.spritecollide(self, plants, False)

        if len(nearby_plants) > 0:
            self.subsprite = nearby_plants[0]
            if self.subsprite.holder is not None:
                self.subsprite.holder.subsprite = None
            self.subsprite.holder = self
            self.move_plant_to_front()
            
    def move_plant_to_front(self):
        '''
        Move the plant to the front of our body,
        depending on which direction we are facing.
        '''
        if self.subsprite is None or self.subsprite.subsprite is None:
            return
        
        if self.facing == Person.NORTH:
            self.subsprite.move(\
                self.rect.centerx - self.subsprite.subsprite.rect.centerx, \
                self.rect.top - self.subsprite.subsprite.rect.top)
        elif self.facing == Person.EAST:
            self.subsprite.move(\
                self.rect.centerx - self.subsprite.subsprite.rect.left, \
                self.rect.centery - self.subsprite.subsprite.rect.centery)
        if self.facing == Person.SOUTH:
            self.subsprite.move(\
                self.rect.centerx - self.subsprite.subsprite.rect.centerx, \
                self.rect.bottom - self.subsprite.subsprite.rect.bottom)
        if self.facing == Person.WEST:
            self.subsprite.move(\
                self.rect.centerx - self.subsprite.subsprite.rect.right, \
                self.rect.centery - self.subsprite.subsprite.rect.centery)

class Container(Sprite):
    def __init__(self, startx, starty):
        super().__init__("assets/bag1.png", startx, starty)

class Plant(Sprite):
    '''
    Composite object with a plant and a container.
    '''
    def __init__(self, startx, starty):
        super().__init__("assets/plant1.png", startx, starty)
        self.subsprite = Container(startx, starty)

        self.rect.move_ip([
            self.rect.left - self.subsprite.rect.left,
            self.subsprite.rect.top - self.rect.bottom
        ])
    
    def draw(self, screen):
        super().draw(screen)
        self.subsprite.draw(screen)
    
    def move(self, dx, dy, bounds=False, obstacles=None):
        super().move(dx, dy, bounds, obstacles)
        if self.immune_from_obstacles and \
            obstacles is not None and \
            not self.check_collision(0, 0, obstacles):
            self.set_immune_from_obstacles(False)

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
            self.trays[0].rect.left = self.trays[-1].rect.right
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
    plants = []
    belt = ConveyorBelt()
    obstacles = belt.get_trays()
    
    cycle = 0

    while True:
        pygame.event.pump()
        person.update(plants, obstacles)
        if cycle % 2 == 0:
            belt.update()
        if cycle % 1000 == 0:
            new_plant = belt.add_plant()
            if new_plant is not None:
                plants.append(new_plant)

        screen.fill(BACKGROUND)
        
        person.draw(screen)
        [plant.draw(screen) for plant in plants]
        belt.draw(screen)

        pygame.display.flip()

        clock.tick(60)
        cycle += 1

if __name__ == "__main__":
    main()