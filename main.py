import pygame

WIDTH = 400
HEIGHT = 300
TRAY_WIDTH = 40
TRAY_SPEED = 1
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
    
    def move(self, dx, dy):
        self.rect.move_ip([dx, dy])

    def update(self):
        pass

    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Person(Sprite):
    '''
    Represent the game's primary actor.
    '''

    def __init__(self, startx, starty):
        '''
        Inspired by:
        https://docs.replit.com/tutorials/14-2d-platform-game
        '''
        super().__init__("assets/person3.png", startx, starty)
        self.speed = 4

    def update(self):
        '''
        Listen for key presses and respond by
        moving.
        '''
        hsp = 0
        vsp = 0
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            hsp = -self.speed
        elif key[pygame.K_RIGHT]:
            hsp = self.speed
        elif key[pygame.K_UP]:
            vsp = -self.speed
        elif key[pygame.K_DOWN]:
            vsp = self.speed
        
        self.move(hsp, vsp)
    
    def move(self, dx, dy):
        '''
        Move within the bounds
        of the screen.
        '''
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

        self.rect.move_ip([dx, dy])

class Container(Sprite):
    def __init__(self, startx, starty):
        super().__init__("assets/bag1.png", startx, starty)

class Plant(Sprite):
    def __init__(self, startx, starty):
        super().__init__("assets/plant1.png", startx, starty)
        self.container = Container(startx, starty)

        self.rect.move_ip([
            self.rect.left - self.container.rect.left,
            self.container.rect.top - self.rect.bottom
        ])
    
    def draw(self, screen):
        super().draw(screen)
        self.container.draw(screen)
    
    def move(self, dx, dy):
        super().move(dx, dy)
        self.container.move(dx, dy)

class ConveyorBeltTray(Sprite):
    def __init__(self, startx, starty):
        super().__init__("assets/tray1.png", startx, starty)
    
    def update(self):
        self.move(-TRAY_SPEED, 0)

class ConveyorBelt:
    def __init__(self):
        self.trays = []
        for i in range(11):
            self.trays.append(ConveyorBeltTray(i * TRAY_WIDTH, HEIGHT))
    
    def update(self):
        [tray.update() for tray in self.trays]
        if self.trays[0].rect.right < 0:
            self.trays[0].rect.left = self.trays[-1].rect.right
            self.trays = self.trays[1:] + [self.trays[0]]

    def draw(self, screen):
        [tray.draw(screen) for tray in self.trays]

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
    
    cycle = 0

    while True:
        pygame.event.pump()
        person.update()
        if cycle % 5 == 0:
            belt.update()

        screen.fill(BACKGROUND)
        
        person.draw(screen)
        [plant.draw(screen) for plant in plants]
        belt.draw(screen)

        pygame.display.flip()

        clock.tick(60)
        cycle += 1

if __name__ == "__main__":
    main()