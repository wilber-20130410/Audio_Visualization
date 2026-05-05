import pygame
import numpy as np
import os
import sys
import pyaudio
import random
import math
import warnings
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
    import audio_capture
    capture = audio_capture.AudioCapture()
    if capture.initialize():
        print("音频捕获初始化成功")
        print(f"采样率: {capture.get_sample_rate()}")
        capture.stop_capture()
    else:
        print("音频捕获初始化失败")
except ImportError as e:
    print("✗ 无法导入C++音频捕获库，请复制以下错误信息，并在GitHub上提交issue以获取帮助")
    print(f"错误详情: {e}")
    sys.exit()
except Exception as e:
    print("✗ 检查音频库时出错，请复制以下错误信息，并在GitHub上提交issue以获取帮助")
    print(f"错误详情: {e}")
    sys.exit()
import audio_capture
warnings.filterwarnings("ignore")

class AudioVisualizer_output():
    '''输出音频可视化类'''
    def __init__(self) -> None:
        """初始化"""
        pygame.mixer.music.stop()
        self.WIDTH, self.HEIGHT = 1280, 720
        self.BAR_COUNT = 80
        self._init_pygame()
        self.data_hold_time = 2.0
        self.smoothing_factor = 0.3
        self.history_length = int(60 * self.data_hold_time)
        self.band_history = [[] for _ in range(self.BAR_COUNT)]
        self.current_bands = np.zeros(self.BAR_COUNT)
        self.smoothed_bands = np.zeros(self.BAR_COUNT)
        self.peak_values = np.zeros(self.BAR_COUNT)
        self.peak_decay_rate = 0.995
        self.peak_hold_time = 1.5
        self.waveform_history = []
        self.max_waveform_points = 500
        try:
            lib_path = os.path.join(os.path.dirname(__file__))
            if lib_path not in sys.path:
                sys.path.append(lib_path)
            self.audio_capture = audio_capture
            self.capture = audio_capture.AudioCapture()
            if not self.capture.initialize():
                print("初始化音频捕获失败")
                self.capture = None
            else:
                print("C++音频捕获库初始化成功")
                self.sample_rate = self.capture.get_sample_rate()
                print(f"采样率: {self.sample_rate}")
        except ImportError as e:
            print(f"无法导入C++音频捕获库: {e}")
            self.capture = None
        except Exception as e:
            print(f"初始化C++音频捕获库时出错: {e}")
            self.capture = None
        self.audio_buffer = []
        self.buffer_size = 4096
        self.max_buffer_size = 16384
        self.running = True
        self.fps = 50
        self.frame_count = 0
        self.visualization_mode = 0
        self.show_peaks = True
        self.show_waveform = True
        if self.capture is False:
            print("使用回退的音频捕获实现")
            self._init_fallback_audio()
        else:
            self._start_cpp_capture()
    
    def _init_pygame(self) -> None:
        """初始化Pygame"""
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Audio Visualization - Output Mode (Enhanced)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font('./assets/LXGWWenKai.ttf', 18)
        self.large_font = pygame.font.Font('./assets/LXGWWenKai.ttf', 24)
    
    def _init_fallback_audio(self) -> None:
        """回退的音频初始化"""
        try:
            self.p = pyaudio.PyAudio()
            self.CHUNK = 2048
            self.FORMAT = pyaudio.paInt16
            self.CHANNELS = 2
            self.RATE = 44100
            self.sample_rate = self.RATE
            self.output_device_index = None
            info = self.p.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount')
            for i in range(num_devices):
                device = self.p.get_device_info_by_host_api_device_index(0, i)
                if device['maxOutputChannels'] > 0:
                    self.output_device_index = i
                    break
            if self.output_device_index is None:
                self.output_device_index = self.p.get_default_output_device_info()['index']
            self.stream = self.p.open( format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, input=True, input_device_index=self.output_device_index, frames_per_buffer=self.CHUNK)
            self.use_fallback = True
        except Exception as e:
            print(f"回退音频初始化也失败: {e}")
            self.stream = None
            self.use_fallback = False
    
    def _start_cpp_capture(self) -> None:
        """启动C++音频捕获"""
        def audio_callback(audio_data):
            self.audio_buffer.extend(audio_data)
            if len(self.audio_buffer) > self.max_buffer_size:
                self.audio_buffer = self.audio_buffer[-self.buffer_size:]
        self.capture.set_audio_callback(audio_callback)
        if not self.capture.start_capture():
            print("启动音频捕获失败，使用回退方案")
            self._init_fallback_audio()
        else:
            print("C++音频捕获已启动")
            self.use_fallback = False
    
    def _get_audio_data_cpp(self) -> np.ndarray | None:
        if len(self.audio_buffer) < self.buffer_size:
            return None
        data = np.array(self.audio_buffer[:self.buffer_size])
        self.audio_buffer = self.audio_buffer[self.buffer_size:]
        return data
    
    def _get_audio_data_fallback(self):
        if not self.stream:
            return None
        try:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            if self.CHANNELS == 2:
                left = audio_data[0::2]
                right = audio_data[1::2]
                audio_data = (left + right) / 2
            audio_data = audio_data.astype(np.float32) / 32768.0
            return audio_data
        except Exception as e:
            print(f"获取音频数据错误: {e}")
            return None
    
    def _get_audio_data(self) -> np.ndarray | None:
        if self.use_fallback:
            return self._get_audio_data_fallback()
        else:
            return self._get_audio_data_cpp()
    
    def _apply_fft(self, audio_data: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:
        if audio_data is None or len(audio_data) == 0:
            return np.zeros(self.BAR_COUNT), np.zeros(self.BAR_COUNT)
        window = np.hanning(len(audio_data))
        windowed_data = audio_data * window
        fft = np.abs(np.fft.rfft(windowed_data))
        freqs = np.fft.rfftfreq(len(audio_data), 1.0/self.sample_rate)
        return fft, freqs
    
    def _group_frequencies(self, fft: np.ndarray, freqs: np.ndarray) -> np.ndarray:
        if len(fft) == 0 or len(freqs) == 0:
            return np.zeros(self.BAR_COUNT)
        bands = np.logspace(np.log10(20), np.log10(20000), num=self.BAR_COUNT + 1)
        band_values = []
        for i in range(len(bands)-1):
            mask = (freqs >= bands[i]) & (freqs < bands[i+1])
            if np.any(mask):
                value = np.mean(fft[mask])
                band_values.append(value)
            else:
                band_values.append(0)
        if len(band_values) > 0:
            max_value = np.max(band_values) if np.max(band_values) > 0 else 1
            band_values = [min(value / max_value, 1.0) for value in band_values]
        return band_values
    
    def _update_band_history(self, band_values: list[float]) -> None:
        """更新频带历史数据"""
        for i, value in enumerate(band_values):
            self.band_history[i].append(value)
            if len(self.band_history[i]) > self.history_length:
                self.band_history[i].pop(0)
    
    def _smooth_bands(self, band_values: list[float]) -> None:
        """平滑频带数据"""
        for i, value in enumerate(band_values):
            self.smoothed_bands[i] = (self.smoothing_factor * value + (1 - self.smoothing_factor) * self.smoothed_bands[i])
            if value > self.peak_values[i]:
                self.peak_values[i] = value
            else:
                self.peak_values[i] *= self.peak_decay_rate
    
    def _update_waveform_history(self, audio_data: np.ndarray | None) -> None:
        """更新波形历史"""
        if audio_data is not None and len(audio_data) > 0:
            step = max(1, len(audio_data) // 100)
            waveform_points = audio_data[::step]
            self.waveform_history.extend(waveform_points)
            if len(self.waveform_history) > self.max_waveform_points:
                self.waveform_history = self.waveform_history[-self.max_waveform_points:]
    
    def _draw_spectrum_bars(self, band_values: list[float]) -> None:
        """绘制频谱条"""
        bar_width = self.WIDTH / self.BAR_COUNT
        for i, value in enumerate(band_values):
            height = min(self.smoothed_bands[i] * self.HEIGHT * 0.7, self.HEIGHT * 0.7)
            hue = i / self.BAR_COUNT
            color_value = int(value * 255)
            r = int(min(255, 100 + color_value * 1.5))
            g = int(min(255, 50 + color_value * 0.8))
            b = int(min(255, 150 + color_value))
            color = (r, g, b)
            pygame.draw.rect(self.screen, color, (i * bar_width, self.HEIGHT - height, bar_width - 1, height))
            if self.show_peaks and self.peak_values[i] > 0.1:
                peak_height = min(self.peak_values[i] * self.HEIGHT * 0.7, self.HEIGHT * 0.7)
                pygame.draw.rect(self.screen, (255, 255, 255), (i * bar_width, self.HEIGHT - peak_height - 2, bar_width - 1, 2))
            if len(self.band_history[i]) > 1:
                for j in range(1, min(10, len(self.band_history[i]))):
                    hist_value = self.band_history[i][-j]
                    hist_height = min(hist_value * self.HEIGHT * 0.7, self.HEIGHT * 0.7)
                    alpha = 255 - j * 25
                    if alpha > 0:
                        trail_color = (r, g, b, alpha)
                        trail_surface = pygame.Surface((bar_width - 1, 2), pygame.SRCALPHA)
                        trail_surface.fill(trail_color)
                        self.screen.blit(trail_surface, 
                                       (i * bar_width, self.HEIGHT - hist_height))
    
    def _draw_waveform(self) -> None:
        """绘制波形"""
        if len(self.waveform_history) < 2:
            return None
        points = []
        for i, value in enumerate(self.waveform_history):
            x = int(i * self.WIDTH / len(self.waveform_history))
            y = int(self.HEIGHT / 2 - value * self.HEIGHT * 0.3)
            points.append((x, y))
        if len(points) > 1:
            pygame.draw.lines(self.screen, (0, 255, 255), False, points, 2)
    
    def _draw_circular_spectrum(self, band_values: list[float]) -> None:
        """绘制圆形频谱"""
        center_x, center_y = self.WIDTH // 2, self.HEIGHT // 2
        max_radius = min(self.WIDTH, self.HEIGHT) * 0.4
        for i, value in enumerate(band_values):
            angle = 2 * math.pi * i / self.BAR_COUNT
            radius = max_radius * (0.3 + 0.7 * self.smoothed_bands[i])
            end_x = center_x + radius * math.cos(angle)
            end_y = center_y + radius * math.sin(angle)
            hue = i / self.BAR_COUNT
            color = self._hsv_to_rgb(hue, 1.0, 1.0)
            pygame.draw.line(self.screen, color, (center_x, center_y), (end_x, end_y), 3)
    
    def _draw_particle_effect(self, band_values: list[float]) -> None:
        """绘制粒子效果"""
        if not hasattr(self, 'particles'):
            self.particles = []
            for _ in range(200):
                self.particles.append({
                    'x': random.uniform(0, self.WIDTH),
                    'y': random.uniform(0, self.HEIGHT),
                    'vx': random.uniform(-1, 1),
                    'vy': random.uniform(-1, 1),
                    'life': random.uniform(0, 1),
                    'max_life': random.uniform(1, 3),
                    'size': random.uniform(1, 4)
                })
        overall_energy = np.mean(band_values)
        for particle in self.particles:
            particle['x'] += particle['vx'] * (0.5 + overall_energy)
            particle['y'] += particle['vy'] * (0.5 + overall_energy)
            particle['life'] += 0.02
            if (particle['x'] < 0 or particle['x'] > self.WIDTH or 
                particle['y'] < 0 or particle['y'] > self.HEIGHT or
                particle['life'] > particle['max_life']):
                particle['x'] = random.uniform(0, self.WIDTH)
                particle['y'] = random.uniform(0, self.HEIGHT)
                particle['life'] = 0
                particle['vx'] = random.uniform(-1, 1)
                particle['vy'] = random.uniform(-1, 1)
            alpha = int(255 * (1 - particle['life'] / particle['max_life']))
            color = (100, 200, 255, alpha)
            size = particle['size'] * (1 + overall_energy)
            particle_surface = pygame.Surface((int(size*2), int(size*2)), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color, (int(size), int(size)), int(size))
            self.screen.blit(particle_surface, (int(particle['x'] - size), int(particle['y'] - size)))
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> tuple[int, int, int]:
        """HSV转RGB"""
        if s == 0.0:
            return (int(v*255), int(v*255), int(v*255))
        i = int(h*6)
        f = (h*6) - i
        p = v*(1-s)
        q = v*(1-s*f)
        t = v*(1-s*(1-f))
        i = i%6
        if i == 0: return (int(v*255), int(t*255), int(p*255))
        if i == 1: return (int(q*255), int(v*255), int(p*255))
        if i == 2: return (int(p*255), int(v*255), int(t*255))
        if i == 3: return (int(p*255), int(q*255), int(v*255))
        if i == 4: return (int(t*255), int(p*255), int(v*255))
        if i == 5: return (int(v*255), int(p*255), int(q*255))
    
    def _draw_visualization(self, band_values: list[float], audio_data: np.ndarray | None) -> None:
        """绘制可视化效果"""
        self.screen.fill((0, 0, 0))
        if self.visualization_mode == 0:
            self._draw_spectrum_bars(band_values)
        elif self.visualization_mode == 1:
            self._draw_waveform()
            self._draw_spectrum_bars(band_values)
        elif self.visualization_mode == 2:
            self._draw_circular_spectrum(band_values)
        elif self.visualization_mode == 3:
            self._draw_particle_effect(band_values)
        mode_names = ["频谱条", "波形+频谱", "圆形频谱", "粒子效果"]
        mode_text = f"模式: {mode_names[self.visualization_mode]} | "
        mode_text += "C++库" if not self.use_fallback else "回退模式"
        fps_text = self.font.render(f"FPS: {int(self.clock.get_fps())} - 50", True, (255, 255, 255))
        mode_surface = self.font.render(mode_text, True, (255, 255, 255))
        info_text = self.font.render("ESC:退出  SPACE:切换模式  P:切换峰值  W:切换波形", True, (255, 255, 255))
        self.screen.blit(fps_text, (10, 10))
        self.screen.blit(mode_surface, (10, 35))
        self.screen.blit(info_text, (10, 60))
        hold_text = self.font.render(f"数据保持: {self.data_hold_time}s", True, (200, 200, 200))
        self.screen.blit(hold_text, (self.WIDTH - 150, 10))
    
    def _handle_events(self) -> None:
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.visualization_mode = (self.visualization_mode + 1) % 4
                elif event.key == pygame.K_p:
                    self.show_peaks = not self.show_peaks
                elif event.key == pygame.K_w:
                    self.show_waveform = not self.show_waveform
                elif event.key == pygame.K_UP:
                    self.data_hold_time = min(5.0, self.data_hold_time + 0.5)
                    self.history_length = int(60 * self.data_hold_time)
                elif event.key == pygame.K_DOWN:
                    self.data_hold_time = max(0.5, self.data_hold_time - 0.5)
                    self.history_length = int(60 * self.data_hold_time)
    
    def run(self) -> None:
        """主循环"""
        try:
            while self.running:
                self._handle_events()
                self.frame_count += 1
                audio_data = self._get_audio_data()
                fft, freqs = self._apply_fft(audio_data)
                band_values = self._group_frequencies(fft, freqs)
                self._update_band_history(band_values)
                self._smooth_bands(band_values)
                self._update_waveform_history(audio_data)
                self._draw_visualization(band_values, audio_data)
                pygame.display.flip()
                self.clock.tick(self.fps)
        except Exception as e:
            print(f"输出可视化运行错误: {e}")
        finally:
            self._cleanup()
    
    def _cleanup(self) -> None:
        """清理资源"""
        try:
        #    if hasattr(self, 'capture') and self.capture:
        #        self.capture.stop_capture()
            if hasattr(self, 'stream') and self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if hasattr(self, 'p') and self.p:
                self.p.terminate()
        except Exception as e:
            print(f"清理资源错误: {e}")
        pygame.quit()