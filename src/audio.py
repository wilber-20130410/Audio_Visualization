import pygame
import pyaudio
import numpy as np
import os
from tkinter import Tk, filedialog
import warnings
import sys
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

class AudioVisualizer_Audio():
    """音频文件可视化类（适配audio_capture库）"""
    def __init__(self) -> None:
        """初始化"""
        pygame.mixer.music.stop()
        self.WIDTH, self.HEIGHT = 1280, 720
        self.BAR_COUNT = 100
        self.CHUNK = 2048
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.smoothing_factor = 0.2
        self.peak_decay = 0.98
        self.peak_hold = 1.0
        self._init_pygame()
        self.audio_file = self._select_audio_file()
        self.capture = None
        self.use_audio_capture = False
        self.audio_data = None
        self.playback_pos = 0
        self.peak_values = np.zeros(self.BAR_COUNT)
        self.running = True
        self._init_audio_capture()
        if not self.use_audio_capture:
            self._init_fallback_audio()

    def _init_pygame(self) -> None:
        """初始化Pygame"""
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Audio Visualization - Audio File Mode")
        self.clock = pygame.time.Clock()
        try:
            self.font = pygame.font.Font("./assets/LXGWWenKai.ttf", 16)
        except:
            self.font = pygame.font.SysFont("Arial", 16)

    def _select_audio_file(self) -> str | None:
        """选择音频文件"""
        root = Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="选择音频文件",
            filetypes=[
                ("Audio Files", "*.wav *.mp3 *.ogg *.flac *.aac"),
                ("All Files", "*.*")
            ]
        )
        root.destroy()
        return file_path if file_path else None

    def _init_audio_capture(self) -> None:
        """初始化audio_capture库"""
        try:
            import audio_capture
            self.capture = audio_capture.AudioCapture()
            if self.capture.initialize():
                self.use_audio_capture = True
                self.sample_rate = self.capture.get_sample_rate()
                print("成功初始化audio_capture库")
            else:
                print("audio_capture初始化失败，使用回退方案")
        except (ImportError, Exception) as e:
            print(f"加载audio_capture失败: {e}，使用回退方案")

    def _init_fallback_audio(self) -> None:
        """回退初始化：使用pyaudio+pygame mixer"""
        try:
            self.p = pyaudio.PyAudio()
            if self.audio_file:
                pygame.mixer.music.load(self.audio_file)
                self._load_audio_file_raw()
            print("已初始化回退音频方案")
        except Exception as e:
            print(f"回退音频初始化失败: {e}")
            self.audio_data = None

    def _load_audio_file_raw(self) -> None:
        """加载音频文件原始数据（用于FFT分析）"""
        try:
            if self.audio_file.endswith(".wav"):
                import wave
                with wave.open(self.audio_file, 'rb') as wf:
                    self.CHANNELS = wf.getnchannels()
                    self.RATE = wf.getframerate()
                    self.FORMAT = self.p.get_format_from_width(wf.getsampwidth())
                    frames = wf.readframes(wf.getnframes())
                    self.audio_data = np.frombuffer(frames, dtype=np.int16)
            else:
                import soundfile as sf
                data, self.RATE = sf.read(self.audio_file)
                if len(data.shape) > 1:
                    data = np.mean(data, axis=1)
                self.audio_data = (data * 32767).astype(np.int16)
            self.CHUNK = min(self.CHUNK, len(self.audio_data) // 100)
            print(f"成功加载音频文件: {self.audio_file}")
        except Exception as e:
            print(f"加载音频文件原始数据失败: {e}")
            self.audio_data = None

    def _get_audio_chunk(self) -> np.ndarray:
        """获取音频块数据（适配两种方案）"""
        if not self.audio_file:
            return np.zeros(self.CHUNK)
        if self.use_audio_capture and self.capture:
            audio_chunk = self.capture.get_audio_chunk(self.CHUNK)
            if audio_chunk is not None and len(audio_chunk) > 0:
                return audio_chunk
            return np.zeros(self.CHUNK)
        if self.audio_data is None:
            return np.zeros(self.CHUNK)
        end_pos = self.playback_pos + self.CHUNK * self.CHANNELS
        if end_pos > len(self.audio_data):
            end_pos = len(self.audio_data)
            self.playback_pos = 0
        chunk = self.audio_data[self.playback_pos:end_pos]
        self.playback_pos = end_pos
        if len(chunk) < self.CHUNK * self.CHANNELS:
            chunk = np.pad(chunk, (0, self.CHUNK * self.CHANNELS - len(chunk)), mode='constant')
        return chunk

    def _process_fft(self, audio_chunk: np.ndarray) -> np.ndarray:
        """处理FFT，生成频谱数据"""
        if len(audio_chunk) == 0:
            return np.zeros(self.BAR_COUNT)
        if self.CHANNELS > 1:
            audio_chunk = audio_chunk[::self.CHANNELS]
        window = np.hanning(len(audio_chunk))
        normalized_data = audio_chunk.astype(np.float32) / 32768.0
        windowed_data = normalized_data * window
        fft_data = np.abs(np.fft.rfft(windowed_data))
        fft_data = fft_data[:len(fft_data) // 2]
        freq_bins = np.logspace(np.log10(20), np.log10(self.RATE//2), self.BAR_COUNT + 1)
        fft_freqs = np.fft.rfftfreq(len(windowed_data), 1/self.RATE)[:len(fft_data)]
        spectrum = np.zeros(self.BAR_COUNT)
        for i in range(self.BAR_COUNT):
            mask = (fft_freqs >= freq_bins[i]) & (fft_freqs < freq_bins[i+1])
            if np.any(mask):
                spectrum[i] = np.mean(fft_data[mask])
        spectrum = self.smoothing_factor * spectrum + (1 - self.smoothing_factor) * np.roll(spectrum, 1)
        spectrum = np.nan_to_num(spectrum)
        self.peak_values = np.maximum(self.peak_values * self.peak_decay, spectrum)
        return spectrum

    def _draw_visualization(self, spectrum: np.ndarray) -> None:
        """绘制音频可视化界面"""
        self.screen.fill((10, 10, 20))
        bar_width = self.WIDTH / self.BAR_COUNT
        bar_spacing = 1
        draw_width = bar_width - bar_spacing
        for i in range(self.BAR_COUNT):
            norm_height = min(spectrum[i] / 1000, 1.0)
            bar_height = norm_height * self.HEIGHT * 0.8
            hue = i / self.BAR_COUNT
            color = (int(255 * (1 - hue)), int(255 * hue * (1 - hue) * 4), int(255 * hue))
            x = i * bar_width
            y = self.HEIGHT - bar_height - 40
            pygame.draw.rect(self.screen, color, (x, y, draw_width, bar_height))
            if self.show_peaks and self.peak_values[i] > 0:
                peak_height = min(self.peak_values[i] / 1000, 1.0) * self.HEIGHT * 0.8
                peak_y = self.HEIGHT - peak_height - 40
                pygame.draw.line(self.screen, (255, 255, 255), (x, peak_y), (x + draw_width, peak_y), 2)
        if self.audio_file:
            file_name = os.path.basename(self.audio_file)
            text = self.font.render(f"播放中: {file_name}", True, (200, 200, 200))
            self.screen.blit(text, (10, 10))
        hint = self.font.render("按ESC退出 | 空格暂停/继续", True, (150, 150, 150))
        self.screen.blit(hint, (self.WIDTH - hint.get_width() - 10, 10))

    def _handle_events(self) -> None:
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    if self.audio_file and not self.use_audio_capture:
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.pause()
                        else:
                            pygame.mixer.music.unpause()

    def run(self) -> None:
        """运行主循环"""
        if not self.audio_file:
            print("未选择音频文件，退出")
            return
        if not self.use_audio_capture:
            try:
                pygame.mixer.music.play(-1 if self.audio_data is not None else 0)
            except Exception as e:
                print(f"播放音频失败: {e}")
        self.show_peaks = True
        while self.running:
            self._handle_events()
            audio_chunk = self._get_audio_chunk()
            spectrum = self._process_fft(audio_chunk)
            self._draw_visualization(spectrum)
            pygame.display.flip()
            self.clock.tick(60)
        self._cleanup()

    def _cleanup(self) -> None:
        """清理资源"""
        if self.use_audio_capture and self.capture:
            self.capture.stop_capture()
        else:
            if hasattr(self, 'p'):
                self.p.terminate()
            pygame.mixer.music.stop()
        pygame.quit()