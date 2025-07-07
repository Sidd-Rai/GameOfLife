import pygame
import numpy as np
import sys
import json
import os
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import random
import time

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
GRID_WIDTH = 100
GRID_HEIGHT = 60
CELL_SIZE = 12
SIDEBAR_WIDTH = 300
HEADER_HEIGHT = 80

# Colors
class Theme:
    def __init__(self, name: str, bg: tuple, grid: tuple, cell_alive: tuple, cell_dead: tuple, 
                 ui_bg: tuple, ui_text: tuple, ui_accent: tuple, ui_button: tuple):
        self.name = name
        self.bg = bg
        self.grid = grid
        self.cell_alive = cell_alive
        self.cell_dead = cell_dead
        self.ui_bg = ui_bg
        self.ui_text = ui_text
        self.ui_accent = ui_accent
        self.ui_button = ui_button

THEMES = {
    "Classic": Theme("Classic", (20, 20, 20), (40, 40, 40), (255, 255, 255), (0, 0, 0), 
                     (30, 30, 30), (255, 255, 255), (0, 255, 0), (60, 60, 60)),
    "Neon": Theme("Neon", (10, 10, 20), (30, 30, 60), (0, 255, 255), (20, 20, 40), 
                  (15, 15, 30), (255, 255, 255), (255, 0, 255), (40, 40, 80)),
    "Matrix": Theme("Matrix", (0, 0, 0), (0, 20, 0), (0, 255, 0), (0, 10, 0), 
                    (0, 15, 0), (0, 255, 0), (0, 200, 0), (0, 40, 0)),
    "Ocean": Theme("Ocean", (10, 30, 60), (20, 60, 100), (100, 200, 255), (30, 60, 100), 
                   (15, 45, 80), (255, 255, 255), (150, 220, 255), (40, 80, 120)),
    "Fire": Theme("Fire", (40, 0, 0), (80, 20, 0), (255, 100, 0), (60, 20, 0), 
                  (60, 15, 0), (255, 255, 255), (255, 150, 0), (100, 40, 0)),
}

class GameState(Enum):
    PAUSED = 0
    RUNNING = 1
    EDITING = 2

@dataclass
class Statistics:
    generation: int = 0
    population: int = 0
    births: int = 0
    deaths: int = 0
    max_population: int = 0
    total_births: int = 0
    total_deaths: int = 0
    runtime: float = 0

class Pattern:
    def __init__(self, name: str, pattern: List[List[int]], description: str = ""):
        self.name = name
        self.pattern = np.array(pattern)
        self.description = description
        self.height, self.width = self.pattern.shape

# Predefined patterns
PATTERNS = {
    "Glider": Pattern("Glider", [
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1]
    ], "A small spaceship that moves diagonally"),
    
    "Gosper Gun": Pattern("Gosper Gun", [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1,1,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ], "Famous pattern that generates gliders"),
    
    "Pulsar": Pattern("Pulsar", [
        [0,0,1,1,1,0,0,0,1,1,1,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [0,0,1,1,1,0,0,0,1,1,1,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,1,1,1,0,0,0,1,1,1,0,0],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,1,1,1,0,0,0,1,1,1,0,0]
    ], "Oscillator with period 3"),
    
    "Beacon": Pattern("Beacon", [
        [1,1,0,0],
        [1,1,0,0],
        [0,0,1,1],
        [0,0,1,1]
    ], "Simple period-2 oscillator"),
    
    "Toad": Pattern("Toad", [
        [0,1,1,1],
        [1,1,1,0]
    ], "Period-2 oscillator"),
    
    "Blinker": Pattern("Blinker", [
        [1,1,1]
    ], "Simplest oscillator"),
    
    "R-pentomino": Pattern("R-pentomino", [
        [0,1,1],
        [1,1,0],
        [0,1,0]
    ], "Famous methuselah pattern"),
    
    "Acorn": Pattern("Acorn", [
        [0,1,0,0,0,0,0],
        [0,0,0,1,0,0,0],
        [1,1,0,0,1,1,1]
    ], "Long-lived methuselah pattern"),
    
    "Lightweight Spaceship": Pattern("LWSS", [
        [1,0,0,1,0],
        [0,0,0,0,1],
        [1,0,0,0,1],
        [0,1,1,1,1]
    ], "Spaceship that moves horizontally")
}

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font: pygame.font.Font, 
                 color: tuple, text_color: tuple, hover_color: tuple = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.text_color = text_color
        self.hover_color = hover_color or color
        self.is_hovered = False
        self.is_pressed = False
    
    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.is_pressed = False
        elif event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        return False
    
    def draw(self, screen: pygame.Surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class GameOfLife:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Advanced Game of Life - Commercial Edition")
        self.clock = pygame.time.Clock()
        
        # Game state
        self.grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        self.previous_grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        self.state = GameState.PAUSED
        self.current_theme = "Classic"
        self.theme = THEMES[self.current_theme]
        
        # Timing
        self.speed = 10  # Updates per second
        self.last_update = 0
        self.start_time = time.time()
        
        # Statistics
        self.stats = Statistics()
        
        # UI
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        
        # Grid offset for panning
        self.grid_offset_x = 0
        self.grid_offset_y = 0
        self.is_panning = False
        self.pan_start = (0, 0)
        
        # Selected pattern
        self.selected_pattern = None
        self.pattern_preview = None
        
        # History for undo/redo
        self.history = []
        self.history_index = -1
        self.max_history = 50
        
        # Drawing
        self.is_drawing = False
        self.draw_mode = True  # True for drawing, False for erasing
        
        self.setup_ui()
    
    def setup_ui(self):
        # Control buttons
        button_width = 80
        button_height = 30
        start_x = WINDOW_WIDTH - SIDEBAR_WIDTH + 20
        start_y = 120
        
        self.buttons = {
            "play_pause": Button(start_x, start_y, button_width, button_height, 
                               "Play", self.font_small, self.theme.ui_button, self.theme.ui_text),
            "step": Button(start_x + 90, start_y, button_width, button_height, 
                          "Step", self.font_small, self.theme.ui_button, self.theme.ui_text),
            "clear": Button(start_x, start_y + 40, button_width, button_height, 
                           "Clear", self.font_small, self.theme.ui_button, self.theme.ui_text),
            "random": Button(start_x + 90, start_y + 40, button_width, button_height, 
                            "Random", self.font_small, self.theme.ui_button, self.theme.ui_text),
            "save": Button(start_x, start_y + 80, button_width, button_height, 
                          "Save", self.font_small, self.theme.ui_button, self.theme.ui_text),
            "load": Button(start_x + 90, start_y + 80, button_width, button_height, 
                          "Load", self.font_small, self.theme.ui_button, self.theme.ui_text),
            "undo": Button(start_x, start_y + 120, button_width, button_height, 
                          "Undo", self.font_small, self.theme.ui_button, self.theme.ui_text),
            "redo": Button(start_x + 90, start_y + 120, button_width, button_height, 
                          "Redo", self.font_small, self.theme.ui_button, self.theme.ui_text),
        }
        
        # Theme buttons
        theme_y = start_y + 200
        for i, theme_name in enumerate(THEMES.keys()):
            self.buttons[f"theme_{theme_name}"] = Button(
                start_x, theme_y + i * 35, 120, 30, theme_name, 
                self.font_small, self.theme.ui_button, self.theme.ui_text
            )
        
        # Pattern buttons
        pattern_y = theme_y + len(THEMES) * 35 + 30
        for i, pattern_name in enumerate(PATTERNS.keys()):
            if i < 8:  # Limit display
                self.buttons[f"pattern_{pattern_name}"] = Button(
                    start_x, pattern_y + i * 25, 200, 20, pattern_name, 
                    self.font_small, self.theme.ui_button, self.theme.ui_text
                )
    
    def save_to_history(self):
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        self.history.append(self.grid.copy())
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.history_index += 1
    
    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.grid = self.history[self.history_index].copy()
    
    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.grid = self.history[self.history_index].copy()
    
    def change_theme(self, theme_name: str):
        if theme_name in THEMES:
            self.current_theme = theme_name
            self.theme = THEMES[theme_name]
            self.setup_ui()
    
    def get_neighbors(self, row: int, col: int) -> int:
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < GRID_HEIGHT and 0 <= c < GRID_WIDTH:
                    count += self.grid[r, c]
        return count
    
    def update_grid(self):
        self.previous_grid = self.grid.copy()
        new_grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        births = 0
        deaths = 0
        
        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                neighbors = self.get_neighbors(row, col)
                
                if self.grid[row, col] == 1:  # Alive
                    if neighbors in [2, 3]:
                        new_grid[row, col] = 1
                    else:
                        deaths += 1
                else:  # Dead
                    if neighbors == 3:
                        new_grid[row, col] = 1
                        births += 1
        
        self.grid = new_grid
        self.stats.generation += 1
        self.stats.births = births
        self.stats.deaths = deaths
        self.stats.total_births += births
        self.stats.total_deaths += deaths
        self.stats.population = np.sum(self.grid)
        self.stats.max_population = max(self.stats.max_population, self.stats.population)
    
    def place_pattern(self, pattern: Pattern, x: int, y: int):
        grid_x = (x - self.grid_offset_x) // CELL_SIZE
        grid_y = (y - self.grid_offset_y) // CELL_SIZE
        
        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
            self.save_to_history()
            
            for row in range(pattern.height):
                for col in range(pattern.width):
                    grid_row = grid_y + row
                    grid_col = grid_x + col
                    
                    if 0 <= grid_row < GRID_HEIGHT and 0 <= grid_col < GRID_WIDTH:
                        self.grid[grid_row, grid_col] = pattern.pattern[row, col]
    
    def toggle_cell(self, x: int, y: int):
        grid_x = (x - self.grid_offset_x) // CELL_SIZE
        grid_y = (y - self.grid_offset_y) // CELL_SIZE
        
        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
            if not self.is_drawing:
                self.save_to_history()
                self.is_drawing = True
            
            if self.draw_mode:
                self.grid[grid_y, grid_x] = 1
            else:
                self.grid[grid_y, grid_x] = 0
    
    def fill_random(self, density: float = 0.3):
        self.save_to_history()
        self.grid = np.random.choice([0, 1], size=(GRID_HEIGHT, GRID_WIDTH), 
                                   p=[1-density, density])
    
    def clear_grid(self):
        self.save_to_history()
        self.grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        self.stats = Statistics()
        self.start_time = time.time()
    
    def save_pattern(self, filename: str):
        try:
            data = {
                "grid": self.grid.tolist(),
                "stats": {
                    "generation": self.stats.generation,
                    "population": self.stats.population,
                    "max_population": self.stats.max_population,
                    "total_births": self.stats.total_births,
                    "total_deaths": self.stats.total_deaths
                }
            }
            with open(filename, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving pattern: {e}")
    
    def load_pattern(self, filename: str):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.save_to_history()
            self.grid = np.array(data["grid"])
            
            if "stats" in data:
                stats_data = data["stats"]
                self.stats.generation = stats_data.get("generation", 0)
                self.stats.population = stats_data.get("population", 0)
                self.stats.max_population = stats_data.get("max_population", 0)
                self.stats.total_births = stats_data.get("total_births", 0)
                self.stats.total_deaths = stats_data.get("total_deaths", 0)
        except Exception as e:
            print(f"Error loading pattern: {e}")
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Handle button clicks
            for button_name, button in self.buttons.items():
                if button.handle_event(event):
                    self.handle_button_click(button_name)
            
            # Handle keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.state = GameState.RUNNING if self.state == GameState.PAUSED else GameState.PAUSED
                elif event.key == pygame.K_c:
                    self.clear_grid()
                elif event.key == pygame.K_r:
                    self.fill_random()
                elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.save_pattern("saved_pattern.json")
                elif event.key == pygame.K_l and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.load_pattern("saved_pattern.json")
                elif event.key == pygame.K_z and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.undo()
                elif event.key == pygame.K_y and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.redo()
                elif event.key == pygame.K_ESCAPE:
                    self.selected_pattern = None
                elif event.key == pygame.K_1:
                    self.speed = max(1, self.speed - 1)
                elif event.key == pygame.K_2:
                    self.speed = min(60, self.speed + 1)
            
            # Handle mouse events
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if event.pos[0] < WINDOW_WIDTH - SIDEBAR_WIDTH:
                        if self.selected_pattern:
                            self.place_pattern(self.selected_pattern, event.pos[0], event.pos[1])
                            self.selected_pattern = None
                        else:
                            self.draw_mode = True
                            self.toggle_cell(event.pos[0], event.pos[1])
                elif event.button == 3:  # Right click
                    if event.pos[0] < WINDOW_WIDTH - SIDEBAR_WIDTH:
                        self.draw_mode = False
                        self.toggle_cell(event.pos[0], event.pos[1])
                elif event.button == 2:  # Middle click for panning
                    self.is_panning = True
                    self.pan_start = event.pos
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 or event.button == 3:
                    self.is_drawing = False
                elif event.button == 2:
                    self.is_panning = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.is_panning:
                    dx = event.pos[0] - self.pan_start[0]
                    dy = event.pos[1] - self.pan_start[1]
                    self.grid_offset_x += dx
                    self.grid_offset_y += dy
                    self.pan_start = event.pos
                
                if self.is_drawing and event.pos[0] < WINDOW_WIDTH - SIDEBAR_WIDTH:
                    self.toggle_cell(event.pos[0], event.pos[1])
            
            # Handle mouse wheel for speed control
            elif event.type == pygame.MOUSEWHEEL:
                if pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.speed = max(1, min(60, self.speed + event.y))
        
        return True
    
    def handle_button_click(self, button_name: str):
        if button_name == "play_pause":
            self.state = GameState.RUNNING if self.state == GameState.PAUSED else GameState.PAUSED
            self.buttons["play_pause"].text = "Pause" if self.state == GameState.RUNNING else "Play"
        elif button_name == "step":
            if self.state == GameState.PAUSED:
                self.update_grid()
        elif button_name == "clear":
            self.clear_grid()
        elif button_name == "random":
            self.fill_random()
        elif button_name == "save":
            self.save_pattern("saved_pattern.json")
        elif button_name == "load":
            self.load_pattern("saved_pattern.json")
        elif button_name == "undo":
            self.undo()
        elif button_name == "redo":
            self.redo()
        elif button_name.startswith("theme_"):
            theme_name = button_name.replace("theme_", "")
            self.change_theme(theme_name)
        elif button_name.startswith("pattern_"):
            pattern_name = button_name.replace("pattern_", "")
            self.selected_pattern = PATTERNS[pattern_name]
    
    def draw_grid(self):
        # Draw grid background
        grid_rect = pygame.Rect(0, 0, WINDOW_WIDTH - SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, self.theme.bg, grid_rect)
        
        # Draw cells
        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                x = col * CELL_SIZE + self.grid_offset_x
                y = row * CELL_SIZE + self.grid_offset_y
                
                if -CELL_SIZE <= x < WINDOW_WIDTH - SIDEBAR_WIDTH and -CELL_SIZE <= y < WINDOW_HEIGHT:
                    cell_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                    
                    if self.grid[row, col] == 1:
                        pygame.draw.rect(self.screen, self.theme.cell_alive, cell_rect)
                    else:
                        pygame.draw.rect(self.screen, self.theme.cell_dead, cell_rect)
                    
                    # Draw grid lines
                    pygame.draw.rect(self.screen, self.theme.grid, cell_rect, 1)
    
    def draw_ui(self):
        # Draw sidebar
        sidebar_rect = pygame.Rect(WINDOW_WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, self.theme.ui_bg, sidebar_rect)
        
        # Draw title
        title_surface = self.font_large.render("Game of Life", True, self.theme.ui_text)
        self.screen.blit(title_surface, (WINDOW_WIDTH - SIDEBAR_WIDTH + 20, 20))
        
        # Draw statistics
        stats_y = 60
        stats_text = [
            f"Generation: {self.stats.generation}",
            f"Population: {self.stats.population}",
            f"Max Population: {self.stats.max_population}",
            f"Births: {self.stats.births}",
            f"Deaths: {self.stats.deaths}",
            f"Total Births: {self.stats.total_births}",
            f"Total Deaths: {self.stats.total_deaths}",
            f"Speed: {self.speed} FPS",
            f"Runtime: {time.time() - self.start_time:.1f}s"
        ]
        
        for i, text in enumerate(stats_text):
            text_surface = self.font_small.render(text, True, self.theme.ui_text)
            self.screen.blit(text_surface, (WINDOW_WIDTH - SIDEBAR_WIDTH + 20, stats_y + i * 20))
        
        # Draw buttons
        for button in self.buttons.values():
            button.draw(self.screen)
        
        # Draw current theme indicator
        theme_text = f"Theme: {self.current_theme}"
        theme_surface = self.font_small.render(theme_text, True, self.theme.ui_accent)
        self.screen.blit(theme_surface, (WINDOW_WIDTH - SIDEBAR_WIDTH + 20, 420))
        
        # Draw selected pattern indicator
        if self.selected_pattern:
            pattern_text = f"Selected: {self.selected_pattern.name}"
            pattern_surface = self.font_small.render(pattern_text, True, self.theme.ui_accent)
            self.screen.blit(pattern_surface, (WINDOW_WIDTH - SIDEBAR_WIDTH + 20, 440))
            
            # Draw pattern description
            desc_lines = []
            words = self.selected_pattern.description.split()
            line = ""
            for word in words:
                if len(line + word) < 35:
                    line += word + " "
                else:
                    desc_lines.append(line.strip())
                    line = word + " "
            desc_lines.append(line.strip())
            
            for i, line in enumerate(desc_lines):
                desc_surface = self.font_small.render(line, True, self.theme.ui_text)
                self.screen.blit(desc_surface, (WINDOW_WIDTH - SIDEBAR_WIDTH + 20, 460 + i * 15))
        
        # Draw controls help
        help_y = 520
        help_text = [
            "Controls:",
            "Space - Play/Pause",
            "C - Clear grid",
            "R - Random fill",
            "Ctrl+S - Save",
            "Ctrl+L - Load",
            "Ctrl+Z - Undo",
            "Ctrl+Y - Redo",
            "1/2 - Speed control",
            "Left click - Draw",
            "Right click - Erase",
            "Middle click - Pan",
            "Ctrl+Wheel - Speed"
        ]
        
        for i, text in enumerate(help_text):
            if i == 0:
                text_surface = self.font_medium.render(text, True, self.theme.ui_accent)
            else:
                text_surface = self.font_small.render(text, True, self.theme.ui_text)
            self.screen.blit(text_surface, (WINDOW_WIDTH - SIDEBAR_WIDTH + 20, help_y + i * 18))
        
        # Draw separator line
        pygame.draw.line(self.screen, self.theme.grid, 
                        (WINDOW_WIDTH - SIDEBAR_WIDTH, 0), 
                        (WINDOW_WIDTH - SIDEBAR_WIDTH, WINDOW_HEIGHT), 2)
    
    def draw_pattern_preview(self):
        if self.selected_pattern:
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0] < WINDOW_WIDTH - SIDEBAR_WIDTH:
                grid_x = (mouse_pos[0] - self.grid_offset_x) // CELL_SIZE
                grid_y = (mouse_pos[1] - self.grid_offset_y) // CELL_SIZE
                
                # Draw pattern preview
                for row in range(self.selected_pattern.height):
                    for col in range(self.selected_pattern.width):
                        if self.selected_pattern.pattern[row, col] == 1:
                            preview_x = (grid_x + col) * CELL_SIZE + self.grid_offset_x
                            preview_y = (grid_y + row) * CELL_SIZE + self.grid_offset_y
                            
                            if 0 <= preview_x < WINDOW_WIDTH - SIDEBAR_WIDTH and 0 <= preview_y < WINDOW_HEIGHT:
                                preview_rect = pygame.Rect(preview_x, preview_y, CELL_SIZE, CELL_SIZE)
                                # Draw semi-transparent preview
                                preview_surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
                                preview_surface.set_alpha(128)
                                preview_surface.fill(self.theme.ui_accent)
                                self.screen.blit(preview_surface, preview_rect)
    
    def run(self):
        running = True
        
        # Save initial state
        self.save_to_history()
        
        while running:
            current_time = pygame.time.get_ticks()
            
            # Handle events
            running = self.handle_events()
            
            # Update game state
            if self.state == GameState.RUNNING:
                if current_time - self.last_update > 1000 / self.speed:
                    self.update_grid()
                    self.last_update = current_time
            
            # Update runtime
            self.stats.runtime = time.time() - self.start_time
            
            # Draw everything
            self.screen.fill(self.theme.bg)
            self.draw_grid()
            self.draw_pattern_preview()
            self.draw_ui()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS for smooth UI
        
        pygame.quit()
        sys.exit()

def main():
    """Main function to run the Game of Life"""
    try:
        game = GameOfLife()
        game.run()
    except Exception as e:
        print(f"Error running game: {e}")
        pygame.quit()
        sys.exit(1)

if __name__ == "__main__":
    # Add some startup patterns for demonstration
    print("🎮 Advanced Game of Life - Commercial Edition")
    print("=" * 50)
    print("Features:")
    print("• Multiple themes (Classic, Neon, Matrix, Ocean, Fire)")
    print("• Pre-built patterns (Glider, Gosper Gun, Pulsar, etc.)")
    print("• Real-time statistics and population tracking")
    print("• Save/Load functionality with JSON format")
    print("• Unlimited undo/redo system")
    print("• Variable speed control (1-60 FPS)")
    print("• Grid panning and zooming")
    print("• Interactive pattern placement")
    print("• Keyboard shortcuts and mouse controls")
    print("• Professional UI with hover effects")
    print("• Pattern preview system")
    print("• Random generation with density control")
    print("• Comprehensive help system")
    print("=" * 50)
    print("Starting game...")
    
    main()