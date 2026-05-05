import pygame
import random
import math
from noise import pnoise2
import warnings
import os
import sys
warnings.filterwarnings("ignore")

class AudioVisualizer_start_1():
    """音频可视化主类"""
    
    class Particle():
        """粒子系统类"""
        def __init__(self, width: int, height: int) -> None:
            """初始化"""
            self.x = random.randint(0, width)
            self.y = random.randint(0, height)
            self.size = random.uniform(1, 3)
            self.speed = random.uniform(0.2, 1.5)
            self.color = (random.randint(70, 100), random.randint(120, 180), random.randint(200, 255), random.randint(150, 220))
            self.direction = random.uniform(0, 2 * math.pi)
            self.width = width
            self.height = height
            
        def update(self) -> None:
            """更新粒子位置"""
            self.x += math.cos(self.direction) * self.speed
            self.y += math.sin(self.direction) * self.speed
            if self.x < 0 or self.x > self.width or self.y < 0 or self.y > self.height:
                self.reset()
                
        def reset(self) -> None:
            """重置粒子位置"""
            self.x = random.randint(0, self.width)
            self.y = random.randint(0, self.height)
            self.direction = random.uniform(0, 2 * math.pi)
        
        def draw(self, surface: pygame.Surface) -> None:
            """绘制粒子"""
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))
    
    class MindustryButton:
        """Mindustry风格按钮类"""
        def __init__(self, x: int, y: int, width: int, height: int, text: str, fonts: dict , colors: dict) -> None:
            """初始化"""
            self.rect = pygame.Rect(x, y, width, height)
            self.text = text
            self.state = 'normal'  # normal, hover, pressed
            self.animation = 0
            self.fonts = fonts
            self.colors = colors
            
        def update(self, mouse_pos: bool, mouse_clicked: bool) -> None:
            """更新按钮状态"""
            if self.rect.collidepoint(mouse_pos):
                if mouse_clicked:
                    self.state = 'pressed'
                else:
                    self.state = 'hover'
            else:
                self.state = 'normal'  
            if self.state == 'hover' and self.animation < 10:
                self.animation += 1
            elif self.state == 'pressed' and self.animation > -5:
                self.animation -= 1
            elif self.state == 'normal' and self.animation > 0:
                self.animation -= 1
                
        def draw(self, surface: pygame.Surface) -> None:
            """绘制按钮"""
            if self.state == 'pressed':
                color = self.colors['button_pressed']
            elif self.state == 'hover':
                color = self.colors['button_hover']
            else:
                color = self.colors['button']
            pygame.draw.rect(surface, color, self.rect, border_radius=3)
            highlight = pygame.Surface((self.rect.width, max(2, self.rect.height // 4)), pygame.SRCALPHA)
            highlight.fill((255, 255, 255, 30))
            surface.blit(highlight, (self.rect.x, self.rect.y))
            text_color = self.colors['text'] if self.state != 'pressed' else (200, 200, 200)
            text_surf = self.fonts['medium'].render(self.text, True, text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            if self.state == 'pressed':
                text_rect.y += 1   
            surface.blit(text_surf, text_rect)
            border_color = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40))
            pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=3)
    
    def __init__(self) -> None:
        """初始化"""
        pygame.init()
        self.WIDTH, self.HEIGHT = 1280, 720
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Audio Visualization 1.1.0[313090505070001.2026]")
        self.colors = {
            'background': (29, 33, 45),
            'panel': (40, 46, 52),
            'accent': (84, 186, 255),
            'text': (220, 220, 220),
            'button': (60, 68, 80),
            'button_hover': (84, 186, 255),
            'button_pressed': (50, 120, 180)
        }
        self.fonts = self._init_fonts()
        self.particles = [self.Particle(self.WIDTH, self.HEIGHT) for _ in range(150)]
        self.buttons = self._init_buttons()
        self.noise_offset = 0
        self.cell_size = 20
        self.panel_width, self.panel_height = 800, 500
        self.running = True
        self.clock = pygame.time.Clock()

    def _init_fonts(self) -> dict:
        """初始化字体"""
        fonts = {}
        try:
            possible_paths = [
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')),
                os.path.join(os.path.dirname(__file__), "/lib"),
                os.path.dirname(__file__),
                os.getcwd(),
            ]
            for path in possible_paths:
                if path not in sys.path and os.path.exists(path):
                    sys.path.append(path)
            fonts['large'] = pygame.font.Font("./assets/LXGWWenKai.ttf", 48)
            fonts['medium'] = pygame.font.Font("./assets/LXGWWenKai.ttf", 32)
            fonts['small'] = pygame.font.Font("./assets/LXGWWenKai.ttf", 18)
        except:
            fonts['large'] = pygame.font.SysFont('courier', 48, bold=True)
            fonts['medium'] = pygame.font.SysFont('courier', 32, bold=True)
            fonts['small'] = pygame.font.SysFont('courier', 18, bold=True)
        return fonts
    
    def _init_buttons(self) -> list:
        """初始化按钮"""
        buttons = [
            self.MindustryButton(self.WIDTH//2 - 150, 250, 300, 50, "Real-time mode", self.fonts, self.colors),
            self.MindustryButton(self.WIDTH//2 - 150, 320, 300, 50, "Audio mode", self.fonts, self.colors),
            self.MindustryButton(self.WIDTH//2 - 150, 390, 300, 50, "Output mode", self.fonts, self.colors),
            self.MindustryButton(self.WIDTH//2 - 150, 460, 300, 50, "Exit", self.fonts, self.colors)
        ]
        return buttons

    def _draw_background(self) -> None:
        """绘制背景和噪声网格"""
        self.screen.fill(self.colors['background'])
        for y in range(0, self.HEIGHT, self.cell_size):
            for x in range(0, self.WIDTH, self.cell_size):
                n = pnoise2(x * 0.01, y * 0.01 + self.noise_offset, octaves=1)
                alpha = max(0, min(20, int((n + 0.5) * 30)))
                if alpha > 5:
                    s = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                    s.fill((84, 186, 255, alpha))
                    self.screen.blit(s, (x, y))
    
    def _draw_particles(self) -> None:
        """绘制所有粒子"""
        for particle in self.particles:
            particle.draw(self.screen)
    
    def _draw_main_panel(self) -> None:
        """绘制主面板"""
        panel = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        panel.fill((*self.colors['panel'], 220))
        pygame.draw.rect(panel, self.colors['accent'], (0, 0, self.panel_width, self.panel_height), 2)
        pygame.draw.rect(panel, (100, 170, 220), (2, 2, self.panel_width-4, self.panel_height-4), 1)
        self.screen.blit(panel, (self.WIDTH//2 - self.panel_width//2, self.HEIGHT//2 - self.panel_height//2))
    
    def _draw_title(self) -> None:
        """绘制标题"""
        title = self.fonts['large'].render("Audio Visualization", True, self.colors['accent'])
        shadow = self.fonts['large'].render("Audio Visualization", True, (20, 40, 60))
        self.screen.blit(shadow, (self.WIDTH//2 - title.get_width()//2 + 3, 100 + 3))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 100))
        version = self.fonts['small'].render("v1.1.0[313090505070001.2026]", True, (150, 150, 150))
        self.screen.blit(version, (self.WIDTH//2 - version.get_width()//2, 160))
    
    def _draw_buttons(self) -> None:
        """绘制所有按钮"""
        for button in self.buttons:
            button.draw(self.screen)
    
    def _draw_footer(self) -> None:
        """绘制页脚信息"""
        copyright = self.fonts['small'].render("© 2025~2026 Wilber-20130410", True, (100, 100, 120))
        self.screen.blit(copyright, (self.WIDTH//2 - copyright.get_width()//2, self.HEIGHT - 40))
    
    def _handle_events(self) -> None:
        """处理事件"""
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_clicked = True
        for button in self.buttons:
            button.update(mouse_pos, mouse_clicked)
            if mouse_clicked and button.state == 'pressed':
                if button.text == "Exit":
                    self.running = False
                elif button.text == "Real-time mode":
                    import realtime
                    visualizer = realtime.AudioVisualizer_realtime()
                    visualizer.run()
                elif button.text == "Audio mode":
                    import audio
                    audio_visualizer = audio.AudioVisualizer_Audio()
                    audio_visualizer.run()
                elif button.text == "Output mode":
                    import output
                    output_visualizer = output.AudioVisualizer_output()
                    output_visualizer.run()
    
    def _update_particles(self) -> None:
        """更新所有粒子"""
        for particle in self.particles:
            particle.update()
    
    def _update_noise(self) -> None:
        """更新噪声偏移"""
        self.noise_offset += 0.01
    
    def run(self) -> None:
        """运行主循环"""
        while self.running:
            self._handle_events()
            self._update_particles()
            self._update_noise()
            self._draw_background()
            self._draw_particles()
            self._draw_main_panel()
            self._draw_title()
            self._draw_buttons()
            self._draw_footer()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

class AudioVisualizer_start_2():
    """像素工厂风格UI"""

    class AnimatedPixelButton():
        """带有动画效果的像素风格按钮"""
        def __init__(self, x: int, y: int, width: int, height: int, text: str, color: dict, hover_color: dict) -> None:
            """初始化"""
            self.rect = pygame.Rect(x, y, width, height)
            self.text = text
            self.color = color
            self.hover_color = hover_color
            self.is_hovered = False
            self.animation_progress = 0
            self.max_animation = 10
        
        def check_hover(self, pos:  tuple) -> bool:
            """按钮上鼠标悬停检查"""
            self.is_hovered = self.rect.collidepoint(pos)
            return self.is_hovered
        
        def is_clicked(self, pos: tuple, event: pygame.event.Event) -> bool:
            """鼠标点击检查"""
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return self.rect.collidepoint(pos)
            return False
        
        def draw(self, surface: pygame.Surface) -> None:
            """按钮绘制"""
            if self.is_hovered and self.animation_progress < self.max_animation:
                self.animation_progress += 1
            elif not self.is_hovered and self.animation_progress > 0:
                self.animation_progress -= 1
            offset = self.animation_progress * 0.5
            pulse = abs(self.animation_progress - self.max_animation//2) * 2
            color = self.hover_color if self.is_hovered else self.color
            rect = self.rect.copy()
            rect.inflate_ip(offset, offset)
            pygame.draw.rect(surface, color, rect)
            border_color = (min(255, color[0] + 50 + pulse), min(255, color[1] + 50 + pulse), min(255, color[2] + 50 + pulse))
            pygame.draw.rect(surface, border_color, rect, 2)
            inner_rect = rect.inflate(-4, -4)
            pygame.draw.rect(surface, (0, 0, 0), inner_rect, 1)
            font = pygame.font.SysFont('Arial', 16)
            text_surf = font.render(self.text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            surface.blit(text_surf, text_rect)
    
    def __init__(self) -> None:
        """初始化"""
        pygame.init()
        self.WIDTH, self.HEIGHT = 1280, 720
        self.PIXEL_SIZE = 4
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Audio Visualization 1.1.0[313090505070001.2026]")
        self.COLORS = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'purple': (128, 0, 128),
            'dark_bg': (10, 10, 20),
            'yellow': (255, 228, 0)
        }
        self.load_resources()
        self.setup_ui()
        
    def load_resources(self) -> None:
        """加载字体、音效等资源"""
        try:
            possible_paths = [
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets')),
                os.path.join(os.path.dirname(__file__), "/assets"),
                os.path.dirname(__file__),
                os.getcwd(),
            ]
            for path in possible_paths:
                if path not in sys.path and os.path.exists(path):
                    sys.path.append(path)
            self.font_large = pygame.font.Font("./assets/LXGWWenKai.ttf", 48)
            self.font_medium = pygame.font.Font("./assets/LXGWWenKai.ttf", 24)
            self.font_small = pygame.font.Font("./assets/LXGWWenKai.ttf", 16)
            self.button_sound = None
        except:
            self.font_large = pygame.font.SysFont('Arial', 48)
            self.font_medium = pygame.font.SysFont('Arial', 24)
            self.font_small = pygame.font.SysFont('Arial', 16)
            self.button_sound = None

    def setup_ui(self) -> None:
        """设置UI元素"""
        self.buttons = [
            self.AnimatedPixelButton(self.WIDTH//2 - 100, 250, 200, 50, "Real-time mode", self.COLORS['green'], (100, 255, 100)),
            self.AnimatedPixelButton(self.WIDTH//2 - 100, 320, 200, 50, "Audio mode", self.COLORS['blue'], (100, 100, 255)),
            self.AnimatedPixelButton(self.WIDTH//2 - 100, 390, 200, 50, "Output mode", self.COLORS['yellow'], (240, 233, 170)),
            self.AnimatedPixelButton(self.WIDTH//2 - 100, 460, 200, 50, "Exit", self.COLORS['red'], (255, 100, 100))
        ]
        self.particles = []
        for _ in range(150):
            self.particles.append({
                'x': random.randint(0, self.WIDTH),
                'y': random.randint(0, self.HEIGHT),
                'speed': random.uniform(0.5, 2.5),
                'size': random.randint(1, 3),
                'color': (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            })

    def run(self) -> None:
        """运行主循环"""
        clock = pygame.time.Clock()
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_clicked = True
            for button in self.buttons:
                button.check_hover(mouse_pos)
                if mouse_clicked and button.is_hovered:
                    if self.button_sound != None:
                        self.button_sound.play()
                    if button.text == "Exit":
                        running = False
                    elif button.text == "Real-time mode":
                        import realtime
                        visualizer = realtime.AudioVisualizer_realtime()
                        visualizer.run() 
                    elif button.text == "Audio mode":
                        import audio
                        audio_visualizer = audio.AudioVisualizer_Audio()
                        audio_visualizer.run()
                    elif button.text == "Output mode":
                        import output
                        output_visualizer = output.AudioVisualizer_output()
                        output_visualizer.run()    
            self.update_particles()
            self.draw_background()
            self.draw_particles()
            self.draw_ui_overlay()
            self.draw_title()
            self.draw_buttons()
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()
    
    def update_particles(self) -> None:
        """更新粒子位置"""
        for p in self.particles:
            p['y'] += p['speed']
            if p['y'] > self.HEIGHT:
                p['y'] = 0
                p['x'] = random.randint(0, self.WIDTH)
    
    def draw_background(self) -> None:
        """绘制像素风格背景"""
        for y in range(self.HEIGHT):
            color_val = max(10, min(50, y // 15))
            pygame.draw.line(
                self.screen, 
                (color_val, color_val, color_val + 10),
                (0, y), (self.WIDTH, y)
            )
    
    def draw_particles(self) -> None:
        """绘制粒子"""
        for p in self.particles:
            pygame.draw.circle(
                self.screen, 
                p['color'], 
                (int(p['x']), int(p['y'])), 
                p['size']
            )
    
    def draw_ui_overlay(self) -> None:
        """绘制UI覆盖层"""
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 50, 180))
        self.screen.blit(overlay, (0, 0))
    
    def draw_title(self) -> None:
        """绘制标题"""
        title = self.font_large.render("Audio Visualization", True, self.COLORS['white'])
        shadow = self.font_large.render("Audio Visualization", True, (100, 100, 150))
        self.screen.blit(shadow, (self.WIDTH//2 - title.get_width()//2 + 3, 83))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 80))
        subtitle = self.font_medium.render("v1.1.0[313090505070001.2026]", True, (200, 200, 255))
        self.screen.blit(subtitle, (self.WIDTH//2 - subtitle.get_width()//2, 140))
        copyright = self.font_small.render("© 2025~2026 Wilber-20130410", True, (100, 100, 120))
        self.screen.blit(copyright, (self.WIDTH//2 - copyright.get_width()//2, self.HEIGHT - 40))
    
    def draw_buttons(self) -> None:
        """绘制所有按钮"""
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)
            button.draw(self.screen)