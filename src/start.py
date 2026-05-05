import pygame
from pygame import mixer
import random
import sys
import time
import main
import check
import warnings
import os
warnings.filterwarnings("ignore")

class AudioVisualizerLauncher():
    """启动主类"""

    def __init__(self) -> None:
        """初始化"""
        pygame.init()
        mixer.init()
        self.WIDTH, self.HEIGHT = 854, 480
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.NOFRAME)
        pygame.display.set_caption("Audio Visualization 1.1.0[313090505070001.2026]")
        self.BLACK = (0, 0, 0)
        self.DARK_GREEN = (0, 71, 0)
        self.GREEN = (0, 100, 0)
        self.LIGHT_GREEN = (100, 200, 100)
        self.WHITE = (255, 255, 255)
        self.GRAY = (100, 100, 100)
        self.LIGHT_GRAY = (200, 200, 200)
        self._load_fonts()
        self.background_layers = []
        self.layer_positions = [0, 0, 0]
        self._init_background()
        self.title_text = self.title_font.render("Audio Visualization", True, self.WHITE)
        self.title_shadow = self.title_font.render("Audio Visualization", True, self.GRAY)
        self.title_rect = self.title_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//3))
        self.version_text = self.version_font.render("1.1.0[313090505070001.2026]", True, self.LIGHT_GRAY)
        self.version_rect = self.version_text.get_rect(bottomright=(self.WIDTH-10, self.HEIGHT-10))
        self.progress_width = self.WIDTH - 100
        self.progress_height = 5
        self.progress_rect = pygame.Rect((self.WIDTH - self.progress_width) // 2, self.HEIGHT * 2 // 3, self.progress_width, self.progress_height)
        self.progress = 0
        self.loading_texts = [
            "启动Starting...",
            "检查网络...",
            "检查audio_capture...",
            "检查代码完整性...",
            "检查完成...",
            "启动完成",
        ]
        self.english_loading_texts = [
            "Starting...",
            "Checking network...",
            "Checking audio_capture...",
            "Checking source integrity...",
            "Checks complete...",
            "Startup complete",
        ]
        self.current_loading_text = "启动AudioVisualizer..."
        self.english_current_loading_text = "Starting AudioVisualizer..."
        self.running = True
        self.clock = pygame.time.Clock()
        self.start_time = time.time()

    def game_stop(self) -> None:
        """异常时停止游戏"""
        mixer.music.stop()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)

    def _load_fonts(self) -> None:
        """加载字体"""
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
            self.title_font = pygame.font.Font("./assets/LXGWWenKai.ttf", 72)
            self.version_font = pygame.font.Font("./assets/LXGWWenKai.ttf", 16)
            self.progress_font = pygame.font.Font("./assets/LXGWWenKai.ttf", 14)
        except:
            self.title_font = pygame.font.SysFont("arial", 72, bold=True)
            self.version_font = pygame.font.SysFont("arial", 16)
            self.progress_font = pygame.font.SysFont("arial", 14)
    
    def _init_background(self) -> None:
        """初始化背景"""
        for i in range(3):
            layer = pygame.Surface((self.WIDTH, self.HEIGHT))
            for _ in range(100):
                x = random.randint(0, self.WIDTH)
                y = random.randint(0, self.HEIGHT)
                size = random.randint(1, 3) * (i + 1)
                color = (random.randint(0, 50), random.randint(50, 100), random.randint(0, 50))
                pygame.draw.rect(layer, color, (x, y, size, size))
            self.background_layers.append(layer)
    
    def _handle_events(self) -> None:
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def _update_progress(self) -> None:
        """更新进度条"""
        if self.progress < 100:
            self.progress += random.uniform(0.05, 0.5)
            self.progress = min(self.progress, 100)
            self._update_loading_text()
    
    def _update_loading_text(self) -> None:
        """更新加载文本"""
        wifi_bool = check.Before_Start_Check.check_network
        shasum_bool = check.Shasum_Check.check_shasum
        shasum_error_file = check.Shasum_Check().error_files
        audiocapture_bool = check.Before_Start_Check.check_audio_library
        if self.progress < 5:
            self.current_loading_text = self.loading_texts[0]
            self.english_current_loading_text = self.english_loading_texts[0]
        elif 5 <= self.progress < 15:
            self.current_loading_text = self.loading_texts[1]
            self.english_current_loading_text = self.english_loading_texts[1]
        elif 15 <= self.progress < 40:
            if wifi_bool:
                self.current_loading_text = self.loading_texts[2]
                self.english_current_loading_text = self.english_loading_texts[2]
            else:
                self.current_loading_text = "网络异常，请检查网络并重启"
                self.english_current_loading_text = "Network anomaly , please check the network and restart"
                time.sleep(2)
                self.game_stop()
        elif 40 <= self.progress < 65:
            if audiocapture_bool:
                self.current_loading_text = self.loading_texts[3]
                self.english_current_loading_text = self.english_loading_texts[3]
            else:
                self.current_loading_text = "音频捕获库导入或编译错误"
                self.english_current_loading_text = "Audio capture library import or compilation error"
                time.sleep(2)
                self.game_stop()
        elif 65 <= self.progress < 85:
            if shasum_bool:
                self.current_loading_text = self.loading_texts[4]
                self.english_current_loading_text = self.english_loading_texts[4]
            else:
                self.current_loading_text = f"文件SHA256校验失败，错误的文件：{shasum_error_file}"
                self.english_current_loading_text = f"File SHA256 verification failed, incorrect file:{shasum_error_file}"
        elif 85 <= self.progress <= 100:
            self.current_loading_text = self.loading_texts[5]
            self.english_current_loading_text = self.english_loading_texts[5]
    
    def _update_background(self) -> None:
        """更新背景位置"""
        for i in range(3):
            self.layer_positions[i] += (i + 1) * 0.2
            if self.layer_positions[i] > self.WIDTH:
                self.layer_positions[i] = 0
    
    def _draw_background(self) -> None:
        """绘制背景"""
        for i, layer in enumerate(self.background_layers):
            self.screen.blit(layer, (self.layer_positions[i] - self.WIDTH, 0))
            self.screen.blit(layer, (self.layer_positions[i], 0))
    
    def _draw_title(self) -> None:
        """绘制标题"""
        self.screen.blit(self.title_shadow, (self.title_rect.x + 3, self.title_rect.y + 3))
        self.screen.blit(self.title_text, self.title_rect)
    
    def _draw_progress_bar(self) -> None:
        """绘制进度条"""
        pygame.draw.rect(self.screen, self.GRAY, self.progress_rect)
        filled_rect = pygame.Rect(self.progress_rect.x, self.progress_rect.y, self.progress_rect.width * (self.progress / 100), self.progress_rect.height)
        pygame.draw.rect(self.screen, self.GREEN, filled_rect)
        pygame.draw.rect(self.screen, self.LIGHT_GREEN, filled_rect, 1)
        loading_surface = self.progress_font.render(self.current_loading_text, True, self.LIGHT_GRAY)
        loading_rect = loading_surface.get_rect(midbottom=(self.WIDTH//2, self.progress_rect.y - 10))
        self.screen.blit(loading_surface, loading_rect)
        english_loading_surface = self.progress_font.render(self.english_current_loading_text, True, self.LIGHT_GRAY)
        english_loading_rect = english_loading_surface.get_rect(midbottom=(self.WIDTH//2, self.progress_rect.y - 25))
        self.screen.blit(english_loading_surface, english_loading_rect)
        if self.progress >= 100:
            continue_text = self.progress_font.render("加载完成，按下任意键启动 Loading Complete - Press any key", True, self.LIGHT_GREEN)
            continue_rect = continue_text.get_rect(midtop=(self.WIDTH//2, self.progress_rect.bottom + 20))
            self.screen.blit(continue_text, continue_rect)
    
    def _draw_version(self) -> None:
        """绘制版本信息"""
        self.screen.blit(self.version_text, self.version_rect)
    
    def _update(self) -> None:
        """更新状态"""
        self._update_background()
        self._update_progress()
    
    def _draw(self) -> None:
        """绘制"""
        self.screen.fill(self.DARK_GREEN)
        self._draw_background()
        self._draw_title()
        self._draw_progress_bar()
        self._draw_version()
        pygame.display.flip()
    
    def run_game(self) -> None:
        """运行主界面"""
        start = [1, 2, 3, 4, 5, 6]
        random.shuffle(start)
        stnum = random.choice(start)
        if stnum % 2 == 1:
            print("2")
            app = main.AudioVisualizer_start_2()
            app.run()
        else:
            print("1")
            app_1 = main.AudioVisualizer_start_1()
            app_1.run()

    def run(self) -> None:
        """运行主循环"""
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(60)
            if self.progress >= 100:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                        self.running = False
                        break
        self.run_game()
        pygame.quit()

if __name__ == "__main__":
    AudioVisualizerLauncher().run()