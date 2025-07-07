# -*- coding: utf-8 -*-
"""
Conway's Game of Life: Studio Edition
Author: Gemini
Date: July 8, 2025
Version: 2.1

A feature-rich, high-performance implementation of Conway's Game of Life
built with Python, Pygame, NumPy, and SciPy.

Features:
- High-performance simulation using vectorized operations.
- Interactive controls: Play/Pause, Speed Control, Step, Reset, Clear.
- Live drawing and erasing of cells with the mouse.
- Zoom and Pan functionality for navigating large grids.
- A library of classic patterns to "stamp" onto the grid.
- Pattern rotation and flipping before placement.
- Multiple, switchable color themes with cell glow and fade effects.
- Real-time display of generation, population, and other stats.
- Save/Load functionality for grid states.
"""

import pygame
import numpy as np
from scipy.signal import convolve2d
import sys
import json

# --- Constants and Settings ---
# Screen dimensions
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

# UI Panel dimensions
PANEL_WIDTH = 320

# Colors
COLOR_BG = (10, 15, 20)
COLOR_GRID = (30, 40, 50)
COLOR_PANEL = (20, 25, 35)
COLOR_TEXT = (220, 220, 220)
COLOR_TEXT_HOVER = (255, 255, 255)
COLOR_ACCENT = (0, 150, 255)
COLOR_ACCENT_HOVER = (100, 200, 255)
COLOR_DANGER = (255, 80, 80)
COLOR_DANGER_HOVER = (255, 120, 120)

# Themes: (cell_color, glow_color, dying_color)
THEMES = {
    "Neon": ((0, 255, 170), (0, 100, 80), (100, 100, 0)),
    "Bio-Lab": ((100, 255, 100), (50, 120, 50), (150, 100, 50)),
    "Classic": ((255, 255, 255), (100, 100, 100), (128, 128, 128)),
    "Fire": ((255, 190, 0), (180, 50, 0), (100, 100, 100)),
}

# --- Predefined Patterns ---
PATTERNS = {
    'Glider': np.array([[0, 1, 0], [0, 0, 1], [1, 1, 1]]),
    'LWSS': np.array([[0,1,0,0,1],[1,0,0,0,0],[1,0,0,0,1],[1,1,1,1,0]]),
    'Pulsar': np.array([
        [0,0,1,1,1,0,0,0,1,1,1,0,0], [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,0,0,0,0,1,0,1,0,0,0,0,1], [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1], [0,0,1,1,1,0,0,0,1,1,1,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0], [0,0,1,1,1,0,0,0,1,1,1,0,0],
        [1,0,0,0,0,1,0,1,0,0,0,0,1], [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1], [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,1,1,1,0,0,0,1,1,1,0,0]]),
    'Gosper Glider Gun': np.array([
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1,1,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]])
}

class GameOfLife:
    """ Main class for the Game of Life simulation and GUI """
    def __init__(self, width, height, cell_size=10):
        pygame.init()
        pygame.display.set_caption("Game of Life Studio")
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()

        # Grid and simulation state
        self.cell_size = cell_size
        self.grid_width = (width - PANEL_WIDTH) // self.cell_size
        self.grid_height = height // self.cell_size
        self.grid = np.zeros((self.grid_height, self.grid_width), dtype=np.uint8)
        self.prev_grid = self.grid.copy()
        self.is_running = False
        self.generation = 0
        
        # Performance and update timing
        self.updates_per_second = 10
        self.time_since_last_update = 0

        # Camera/View controls
        self.zoom = self.cell_size
        self.offset_x, self.offset_y = 0, 0
        self.is_panning = False
        self.pan_start_pos = (0, 0)

        # Drawing and pattern state
        self.is_drawing = False
        self.draw_mode = 0 # 0 for draw, 1 for erase
        self.active_pattern_name = None
        self.active_pattern = None

        # UI Elements
        self.font_small = pygame.font.SysFont("Arial", 16)
        self.font_medium = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 28, bold=True)
        self.theme = "Neon"
        self.setup_ui()

    def setup_ui(self):
        """ Initialize UI elements """
        self.buttons = {}
        self.sliders = {}
        
        # Playback Controls
        self.buttons['play_pause'] = Button(SCREEN_WIDTH - PANEL_WIDTH + 20, 50, 130, 40, "Play", self.toggle_running)
        self.buttons['step'] = Button(SCREEN_WIDTH - PANEL_WIDTH + 170, 50, 130, 40, "Step", self.step)
        
        # Speed Slider
        self.sliders['speed'] = Slider(SCREEN_WIDTH - PANEL_WIDTH + 20, 120, 280, 1, 60, self.updates_per_second, "Speed")
        
        # Grid Controls
        self.buttons['reset'] = Button(SCREEN_WIDTH - PANEL_WIDTH + 20, 180, 130, 40, "Random", self.reset_grid, color=COLOR_ACCENT)
        self.buttons['clear'] = Button(SCREEN_WIDTH - PANEL_WIDTH + 170, 180, 130, 40, "Clear", self.clear_grid, color=COLOR_DANGER)

        # File Operations
        self.buttons['save'] = Button(SCREEN_WIDTH - PANEL_WIDTH + 20, 240, 130, 40, "Save", self.save_grid)
        self.buttons['load'] = Button(SCREEN_WIDTH - PANEL_WIDTH + 170, 240, 130, 40, "Load", self.load_grid)

        # Pattern Buttons
        y_pos = 350
        for name in PATTERNS.keys():
            self.buttons[f"pattern_{name}"] = Button(SCREEN_WIDTH - PANEL_WIDTH + 20, y_pos, 280, 30, name, lambda n=name: self.select_pattern(n))
            y_pos += 40
        
        # Theme Buttons
        y_pos = SCREEN_HEIGHT - 150
        for name in THEMES.keys():
            self.buttons[f"theme_{name}"] = Button(SCREEN_WIDTH - PANEL_WIDTH + 20, y_pos, 130, 30, name, lambda n=name: self.set_theme(n))
            y_pos += 40

    def run(self):
        """ Main game loop """
        while True:
            delta_time = self.clock.tick(60) / 1000.0
            self.handle_events()
            if self.is_running:
                self.update(delta_time)
            self.draw()
            pygame.display.flip()

    def handle_events(self):
        """ Process all user input """
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # --- UI Events ---
            for button in self.buttons.values():
                button.handle_event(event)
            for slider in self.sliders.values():
                slider.handle_event(event)

            # --- Mouse Grid Interaction ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                if mouse_pos[0] < SCREEN_WIDTH - PANEL_WIDTH:
                    if event.button == 1: # Left click
                        if self.active_pattern is not None:
                            self.place_pattern(mouse_pos)
                            self.active_pattern = None # Place once
                            self.active_pattern_name = None
                        else:
                            self.is_drawing = True
                            self.draw_mode = 0
                    elif event.button == 3: # Right click
                        self.is_drawing = True
                        self.draw_mode = 1
                    elif event.button == 2: # Middle click
                        self.is_panning = True
                        self.pan_start_pos = mouse_pos
                    elif event.button == 4: # Scroll up
                        self.zoom_at(mouse_pos, 1.1)
                    elif event.button == 5: # Scroll down
                        self.zoom_at(mouse_pos, 1 / 1.1)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button in [1, 3]: self.is_drawing = False
                if event.button == 2: self.is_panning = False

            if event.type == pygame.MOUSEMOTION:
                if self.is_drawing:
                    self.draw_on_grid(mouse_pos)
                if self.is_panning:
                    dx = mouse_pos[0] - self.pan_start_pos[0]
                    dy = mouse_pos[1] - self.pan_start_pos[1]
                    self.offset_x += dx
                    self.offset_y += dy
                    self.pan_start_pos = mouse_pos

            # --- Keyboard Events ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: self.toggle_running()
                if event.key == pygame.K_c: self.clear_grid()
                if event.key == pygame.K_r and self.active_pattern is not None:
                    self.active_pattern = np.rot90(self.active_pattern)
                if event.key == pygame.K_f and self.active_pattern is not None:
                    self.active_pattern = np.fliplr(self.active_pattern)

        if self.is_drawing:
            self.draw_on_grid(mouse_pos)

    def world_to_screen(self, x, y):
        """ Convert grid coordinates to screen coordinates """
        screen_x = (x * self.zoom) + self.offset_x
        screen_y = (y * self.zoom) + self.offset_y
        return int(screen_x), int(screen_y)

    def screen_to_world(self, sx, sy):
        """ Convert screen coordinates to grid coordinates """
        world_x = (sx - self.offset_x) / self.zoom
        world_y = (sy - self.offset_y) / self.zoom
        return int(world_x), int(world_y)

    def zoom_at(self, mouse_pos, scale):
        """ Zoom in/out centered on the mouse cursor """
        world_x, world_y = self.screen_to_world(*mouse_pos)
        new_zoom = self.zoom * scale
        
        # Clamp zoom level
        if not (2 < new_zoom < 100):
            return
        self.zoom = new_zoom

        self.offset_x = mouse_pos[0] - world_x * self.zoom
        self.offset_y = mouse_pos[1] - world_y * self.zoom

    def update(self, delta_time):
        """ Update the simulation state """
        self.time_since_last_update += delta_time
        update_interval = 1.0 / self.sliders['speed'].value
        if self.time_since_last_update >= update_interval:
            self.time_since_last_update -= update_interval
            self.step()

    def step(self):
        """ Advance the simulation by one generation """
        self.prev_grid = self.grid.copy()
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        
        # Count neighbors using convolution with wrap-around boundaries
        neighbor_count = convolve2d(self.grid, kernel, mode='same', boundary='wrap')
        
        # Apply Conway's rules
        born = (self.grid == 0) & (neighbor_count == 3)
        survives = (self.grid == 1) & ((neighbor_count == 2) | (neighbor_count == 3))
        
        self.grid = (born | survives).astype(np.uint8)
        self.generation += 1

    def draw(self):
        """ Draw everything to the screen """
        self.screen.fill(COLOR_BG)
        self.draw_grid()
        self.draw_ui()
        if self.active_pattern is not None:
            self.draw_pattern_preview(pygame.mouse.get_pos())

    def draw_grid(self):
        """ Draw the Game of Life grid """
        cell_color, glow_color, dying_color = THEMES[self.theme]
        
        # Determine visible grid area
        start_col, start_row = self.screen_to_world(0, 0)
        end_col, end_row = self.screen_to_world(SCREEN_WIDTH - PANEL_WIDTH, SCREEN_HEIGHT)
        
        start_col = max(0, start_col)
        start_row = max(0, start_row)
        end_col = min(self.grid_width, end_col + 2)
        end_row = min(self.grid_height, end_row + 2)

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                screen_x, screen_y = self.world_to_screen(x, y)
                rect = pygame.Rect(screen_x, screen_y, self.zoom, self.zoom)
                
                # Draw grid lines for high zoom levels
                if self.zoom > 5:
                    pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)

                # Draw cells with effects
                if self.grid[y, x] == 1:
                    if self.prev_grid[y, x] == 0: # Newly born
                        # Fade-in effect (simplified)
                        color = tuple(int(c * 0.7) for c in cell_color)
                    else:
                        color = cell_color
                    
                    if self.zoom > 4: # Draw glow effect
                        glow_rect = rect.inflate(self.zoom * 0.8, self.zoom * 0.8)
                        glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (*glow_color, 60), glow_surf.get_rect().center, glow_rect.width / 2)
                        self.screen.blit(glow_surf, glow_rect)
                    
                    pygame.draw.rect(self.screen, color, rect)

                elif self.prev_grid[y, x] == 1: # Just died
                    pygame.draw.rect(self.screen, dying_color, rect)

    def draw_ui(self):
        """ Draw the UI panel """
        panel_rect = pygame.Rect(SCREEN_WIDTH - PANEL_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_PANEL, panel_rect)
        
        # Title
        title_text = self.font_large.render("GOL Studio", True, COLOR_TEXT)
        self.screen.blit(title_text, (SCREEN_WIDTH - PANEL_WIDTH + 20, 10))

        # Buttons and Sliders
        for button in self.buttons.values():
            button.draw(self.screen, self.font_small)
        for slider in self.sliders.values():
            slider.draw(self.screen, self.font_small)

        # Stats
        self.draw_text(f"Generation: {self.generation}", 20, SCREEN_HEIGHT - 60)
        self.draw_text(f"Population: {np.sum(self.grid)}", 20, SCREEN_HEIGHT - 40)
        
        # Pattern section title
        self.draw_text("Pattern Library", SCREEN_WIDTH - PANEL_WIDTH + 20, 320, self.font_medium)
        
        # Theme section title
        self.draw_text("Themes", SCREEN_WIDTH - PANEL_WIDTH + 20, SCREEN_HEIGHT - 180, self.font_medium)
        
        # Active pattern info
        if self.active_pattern_name:
            info = f"Placing: {self.active_pattern_name}. R to rotate, F to flip."
            self.draw_text(info, SCREEN_WIDTH - PANEL_WIDTH + 20, SCREEN_HEIGHT - 30)

    def draw_text(self, text, x, y, font=None, color=COLOR_TEXT):
        if font is None: font = self.font_small
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def draw_on_grid(self, mouse_pos):
        """ Set cell state based on mouse position """
        if mouse_pos[0] >= SCREEN_WIDTH - PANEL_WIDTH: return
        
        grid_x, grid_y = self.screen_to_world(*mouse_pos)
        
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            self.grid[grid_y, grid_x] = 1 - self.draw_mode
            self.prev_grid[grid_y, grid_x] = self.grid[grid_y, grid_x] # Update prev to avoid fade effect

    def place_pattern(self, mouse_pos):
        """ Place the active pattern on the grid """
        if self.active_pattern is None: return
        
        grid_x, grid_y = self.screen_to_world(*mouse_pos)
        h, w = self.active_pattern.shape
        
        # Center pattern on cursor
        grid_x -= w // 2
        grid_y -= h // 2
        
        # Place pattern, handling boundaries
        y_min = max(0, grid_y)
        y_max = min(self.grid_height, grid_y + h)
        x_min = max(0, grid_x)
        x_max = min(self.grid_width, grid_x + w)

        pat_y_min = max(0, -grid_y)
        pat_y_max = h - max(0, (grid_y + h) - self.grid_height)
        pat_x_min = max(0, -grid_x)
        pat_x_max = w - max(0, (grid_x + w) - self.grid_width)

        if y_max > y_min and x_max > x_min:
            self.grid[y_min:y_max, x_min:x_max] = self.active_pattern[pat_y_min:pat_y_max, pat_x_min:pat_x_max]

    def draw_pattern_preview(self, mouse_pos):
        """ Draw a preview of the pattern at the mouse cursor """
        if mouse_pos[0] >= SCREEN_WIDTH - PANEL_WIDTH: return
        
        h, w = self.active_pattern.shape
        cell_color, _, _ = THEMES[self.theme]
        preview_color = (*cell_color, 150) # Semi-transparent
        
        start_gx, start_gy = self.screen_to_world(*mouse_pos)
        start_gx -= w // 2
        start_gy -= h // 2

        for y_off, row in enumerate(self.active_pattern):
            for x_off, cell in enumerate(row):
                if cell:
                    sx, sy = self.world_to_screen(start_gx + x_off, start_gy + y_off)
                    rect = pygame.Rect(sx, sy, self.zoom, self.zoom)
                    
                    # Create a temporary surface for transparency
                    temp_surf = pygame.Surface((self.zoom, self.zoom), pygame.SRCALPHA)
                    pygame.draw.rect(temp_surf, preview_color, (0, 0, self.zoom, self.zoom))
                    self.screen.blit(temp_surf, rect.topleft)

    # --- UI Callbacks ---
    def toggle_running(self):
        self.is_running = not self.is_running
        self.buttons['play_pause'].text = "Pause" if self.is_running else "Play"

    def reset_grid(self):
        self.grid = np.random.choice([0, 1], size=(self.grid_height, self.grid_width), p=[0.8, 0.2])
        self.generation = 0

    def clear_grid(self):
        self.grid.fill(0)
        self.generation = 0
        self.is_running = False
        self.buttons['play_pause'].text = "Play"

    def select_pattern(self, name):
        self.active_pattern_name = name
        self.active_pattern = PATTERNS[name].copy()

    def set_theme(self, name):
        self.theme = name
    
    def save_grid(self):
        """ Save the current grid state to a file """
        try:
            # Using a simple JSON format to be human-readable
            data = {
                'grid': self.grid.tolist(),
                'generation': self.generation
            }
            with open("gol_save.json", "w") as f:
                json.dump(data, f)
            print("Grid saved to gol_save.json")
        except Exception as e:
            print(f"Error saving grid: {e}")

    def load_grid(self):
        """ Load a grid state from a file """
        try:
            with open("gol_save.json", "r") as f:
                data = json.load(f)
            loaded_grid = np.array(data['grid'])
            
            # Resize grid if loaded dimensions are different
            if loaded_grid.shape != (self.grid_height, self.grid_width):
                new_grid = np.zeros_like(self.grid)
                h, w = min(loaded_grid.shape[0], self.grid_height), min(loaded_grid.shape[1], self.grid_width)
                new_grid[:h, :w] = loaded_grid[:h, :w]
                self.grid = new_grid
            else:
                self.grid = loaded_grid
                
            self.generation = data.get('generation', 0)
            self.prev_grid = self.grid.copy()
            print("Grid loaded from gol_save.json")
        except FileNotFoundError:
            print("No save file found.")
        except Exception as e:
            print(f"Error loading grid: {e}")

# --- UI Helper Classes ---
class Button:
    def __init__(self, x, y, width, height, text, callback, color=COLOR_ACCENT):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = tuple(min(255, c + 40) for c in color)
        self.is_hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        text_surf = font.render(self.text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.callback()

class Slider:
    def __init__(self, x, y, width, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, width, 20)
        self.min_val, self.max_val = min_val, max_val
        self.value = initial_val
        self.label = label
        self.is_dragging = False

    def draw(self, screen, font):
        # Draw label
        label_surf = font.render(f"{self.label}: {self.value:.0f}", True, COLOR_TEXT)
        screen.blit(label_surf, (self.rect.x, self.rect.y - 20))
        
        # Draw slider bar and handle
        pygame.draw.rect(screen, COLOR_GRID, self.rect, border_radius=5)
        handle_x = self.rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        pygame.draw.circle(screen, COLOR_ACCENT, (handle_x, self.rect.centery), 12)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mouse_pos):
                self.is_dragging = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
        if self.is_dragging and event.type == pygame.MOUSEMOTION:
            self.value = self.min_val + (mouse_pos[0] - self.rect.x) / self.rect.width * (self.max_val - self.min_val)
            self.value = max(self.min_val, min(self.max_val, self.value))

if __name__ == '__main__':
    game = GameOfLife(SCREEN_WIDTH, SCREEN_HEIGHT)
    game.run()
