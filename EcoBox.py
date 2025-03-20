import random
import pygame

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Ecosystem Simulation")
pygame.display.set_icon(pygame.image.load("EcoBox.ico"))

# const variables
RES = WIDTH, HEIGHT = 1400, 700
TILE = 20
W, H = WIDTH // TILE, HEIGHT // TILE
FPS = 20
CID = 0

screen = pygame.display.set_mode((1400, 700))
clock = pygame.time.Clock()
running = True
play = False

class Pixel():
    def __init__(self, x, y, color, energy = 20, eaten = False, id = None):
        self.x = x
        self.y = y
        self.color = color
        self.energy = energy
        self.eaten = eaten
        self.consumed = False
        self.target = None
        self.hunt_time = 0
        global CID
        self.id = CID
        CID += 1

    def __repr__(self):
        return f"Pixel(x={self.x}, y={self.y}, color={self.color}, food={self.energy})"
    
    def get_pos(self):
        return (self.x, self.y)
    
    def find_close(self, foods):
        # Finds a close food within a increasing distances, until a hard max
        # Algorithm attempts
        # 1. Checked for distances within 5 tiles
        # 2. Finds a close food within a 5 by 5 square (in tiles), with the pixel at the center

        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = self.x + dx * TILE, self.y + dy * TILE
                for food in foods:
                    if food.x == nx and food.y == ny and food.id != self.id:
                        self.target = food
                        return food
        # If no food is found in the 5 by 5 square, pick a random food
        if len(foods) > 0:
            self.target = random.choice(foods)
        return None
    
    def count_adjacent_color(self, pixels, color):
        # Counts how many adjacent pixels have the same color
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        count = 0
        for dx, dy in directions:
            nx, ny = self.x + dx, self.y + dy
            for pixel in pixels:
                if pixel.x == nx and pixel.y == ny and pixel.color == color:
                    count += 1
        return count

    def check_adj_target(self, food):
        # Check for adjacent food
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dx, dy in directions:
            nx, ny = self.x + dx, self.y + dy
            for f in food:
                if f.x == nx and f.y == ny:
                    self.target = f
                    return f
        return None
    
    def find_target(self, foods):
        if self.target == None:
            self.find_close(foods)
        self.check_adj_target(foods)
        return None

    def movement(self, food, live):
        # Change x/y to move towards target
        self.hunt_time += 1

        if self.hunt_time > 3:
            self.target = None
            self.hunt_time = 0
        if self.color == "green":
            self.find_target(food) 
        elif self.color == "red":
            self.find_target([pixel for pixel in live if pixel.color == "green"])
        # Ensure target is set

        if self.target is not None:
            if self.x < self.target.x:
                dx = 1
            elif self.x > self.target.x:
                dx = -1
            else:
                dx = 0

            if self.y < self.target.y:
                dy = 1
            elif self.y > self.target.y:
                dy = -1
            else:
                dy = 0
            
            # Move towards the target
            new_x = self.x + dx
            new_y = self.y + dy

            # Check if the pixel is occupying the same space as another pixel
            if not any(pixel.x == new_x and pixel.y == new_y and pixel.color == self.color for pixel in live):
                # Move towards the target if the new position is not occupied
                self.x = new_x
                self.y = new_y
        else: 
            new_x = self.x + random.randint(-1, 1)
            new_y = self.y + random.randint(-1, 1)
            
            if not any(pixel.x == new_x and pixel.y == new_y for pixel in live):
                # Move towards the target if the new position is not occupied
                self.x = new_x
                self.y = new_y

        if self.count_adjacent_color(live, self.color) > 3:
            self.energy = 0
            return (self.x, self.y)

        # Ensure the pixel stays within bounds
        self.x = max(0, min(self.x, 1399))  # Width is 1400
        self.y = max(0, min(self.y, 699))  # Height is 700

        # Consume Energy
        self.energy -= 1
        if self.color == "red":
            self.eat_animal(live)
        elif self.color == "green":
            self.eat(food)

        return (self.x, self.y)
    
    def change_color(self, new_color):
        if random.randint(1, 20) == 20:
            self.color = new_color
        return self.color
    
    def eat(self, foods):
        for food in foods:
            if self.get_pos() == food.get_pos() and food.color == "white":
                self.energy += 10
                foods.remove(food)
                self.eaten = True
                if self.target is not None:
                    self.target.energy = 0
                self.target = None
                return True
        return False
    
    def eat_animal(self, lives):
        for l in lives:
            if self.get_pos() == l.get_pos():
                if self.id != l.id and l.color != "white":
                    self.energy += 6
                    self.eaten = True
                    if l == self.target:
                        self.target = None
                    l.consumed = True
                    l.energy = 0
                    print(f"Pixel {self.id} at ({self.x},{self.y}) ate Pixel {l.id} at ({l.x},{l.y})")
                    return True
        return False
    
    def is_alive(self):
        if self.energy > 0:
            return True
        return False
    
    def reproduce(self, cells):
        if self.energy > 6 and self.eaten == True:
            if self.color == "green" and random.randint(1, 6) == 6:
                cells.append(Pixel(self.x + random.randint(-1, 1), self.y + random.randint(-1, 1), self.color, self.energy // 2))
                self.energy //= 2
                self.eaten = False
            elif self.color == "red" and random.randint(1, 15) == 15:
                cells.append(Pixel(self.x + random.randint(-1, 1), self.y + random.randint(-1, 1), self.color, self.energy // 2))
                self.energy //= 2
                self.eaten = False
            if random.randint(1, 20) == 20:
                self.change_color(random.choice(["red", "blue", "green"]))
        return cells
    
    def produce_food(self, foods, food_positions, live_positions):
        # Produce food from blue pixels
        l = []
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                l.append((self.x + dx, self.y + dy))
        
        for _ in range(len(l)):
            j = random.choice(l)
            if j not in food_positions and j not in live_positions and j[0] >= 0 and j[0] < 1400 and j[1] >= 0 and j[1] < 700:
                foods.append(Pixel(j[0], j[1], "white"))
                if random.randint(1, 5) == 5:
                    self.energy -= 1
                break
            else:
                l.remove(j)

        return foods
    
    
    
def get_tile_at_pos(pos):
    x, y = pos
    return (x//TILE)*TILE, (y//TILE)*TILE

def draw_pixels(px, screen):
    for p in px:
        pygame.draw.rect(screen, p.color, pygame.Rect(p.x * TILE, p.y * TILE, TILE, TILE))

def set_game():
    live = [
        Pixel(random.randint(0, 1399) // TILE, random.randint(0, 699) // TILE, "blue") for _ in range(10)
    ]

    # for _ in range(10):
    #     live.append(Pixel(random.randint(0, 1399) // TILE, random.randint(0, 699) // TILE, "green"))

    foods = [
        Pixel(random.randint(0, 1399) // TILE, random.randint(0, 699) // TILE, "white") for _ in range(40)
    ]

    draw_pixels(live, screen)
    draw_pixels(foods, screen)
    pygame.display.flip()

    return (live, foods)

def remove_pixel_at_pos(pos, live, foods):
    tile = get_tile_at_pos(pos)
    for pixel in live[:]:
        if pixel.get_pos() == (tile[0] // TILE, tile[1] // TILE):
            live.remove(pixel)
            return
    for food in foods[:]:
        if food.get_pos() == (tile[0] // TILE, tile[1] // TILE):
            foods.remove(food)
            return

def run(live, foods):
    colors = ["red", "blue", "green", "white"]
    i = 0
    global running, play, screen, FPS

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[2]:  # Right-click to remove pixel
                    pos = pygame.mouse.get_pos()
                    remove_pixel_at_pos(pos, live, foods)
                else:
                    pos = pygame.mouse.get_pos()
                    tile = get_tile_at_pos(pos)
                    tile_rect = Pixel(tile[0] // TILE, tile[1] // TILE, colors[i])
                    if tile_rect.color != "white":
                        if tile_rect in live:
                            live.remove(tile_rect)
                        elif tile_rect in foods:
                            foods.remove(tile_rect)
                            live.append(tile_rect)
                        else:
                            live.append(tile_rect)
                    else:
                        if tile_rect in foods:
                            foods.remove(tile_rect)
                        elif tile_rect in live:
                            live.remove(tile_rect)
                            foods.append(tile_rect)
                        else:
                            foods.append(tile_rect)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    play = not play
                elif event.key == pygame.K_c:
                    i = (i + 1) % len(colors)
                elif event.key == pygame.K_DOWN:
                    FPS = max(FPS - 1, 1)
                elif event.key == pygame.K_UP:
                    FPS = min(FPS + 1, 60)
        
        live_positions = [(cell.x, cell.y) for cell in live]
        food_positions = [(food.x, food.y) for food in foods]

        if play:
            for cell in live[:]:  # Iterate over a copy of the list
                if not cell.is_alive():
                    if not cell.consumed:
                        foods.append(Pixel(cell.x, cell.y, "white")) # Add food to the environment
                        live.remove(cell) # Remove dead cells
                    else:
                        live.remove(cell)
                    continue
                if cell.color == "green":
                    cell.movement(foods, live) # Move towards food
                elif cell.color == "blue":
                    cell.produce_food(foods, food_positions, live_positions) # Produce food
                elif cell.color == "red":
                    cell.movement(foods, live) # Move towards other cells
                # cell.eat(foods)
                if cell.color != "blue" and cell.color != "white":
                    cell.reproduce(live)
            
            for food in foods[:]:
                if random.randint(1, 5000) == 5000:
                    live.append(Pixel(food.x, food.y, "blue"))
                    foods.remove(food)
                    
            if random.randint(1, 400) == 400:
                live.append(Pixel(random.randint(0, 1399) // TILE, random.randint(0, 699) // TILE, random.choice(["blue", "green"])))
        
        print(live, "\n" + "hi" + "\n")
        screen.fill((0, 0, 0))  # Clear screen before drawing
        draw_pixels(live, screen)
        draw_pixels(foods, screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


live, foods = set_game()
print(Pixel(0, 0, "white"))
run(live, foods)
