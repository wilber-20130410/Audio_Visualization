import os
import sys
import hashlib
from pathlib import Path

class Shasum_Check():
    """检查文件哈希值"""
    def __init__(self) -> None:
        """初始化"""
        self.files = []
        self.shasum = {"main.py" : "aeb18a6c80aa25e52274ecd17f873f1decdf4b7af4a03d4639d58a7517d15e47",
                       "realtime.py" :"218613010025055fecbbff6fed85269b8fdc550f30d80869fbf6c2269f9ca759",
                       "start.py" : "8082227231759ee60767c95b34cac54aee4d8b68f17385e76387e74f7fb1239d",
                       "audio.py" : "9d3b7fca9d1ab448bfb0f6c3f9383dd7ca8d94b2b393ac5f775df6bf3adfcbc5",
                       "output.py" : "53c845e65c6bb3f5f87c520127ba1e59407fded7588fcfcc5381f8cf2f1274d0",
                       }
        self.error_files = []

    def calculate_sha256(self, file_path: str) -> str | None:
        """计算文件的SHA256哈希值"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except (IOError, OSError) as e:
            print(f"错误: {e}")
            return None
    
    def get_all_files_recursive(self, directory: str) -> list:
        """递归获取目录下所有文件"""
        files = []
        for item in Path(directory).rglob('*.py'):
            if item.is_file():
                files.append(item)
        print(files)
        return files
    
    def check_shasum(self) -> bool:
        """"检查文件哈希值"""
        current_dir = Path(__file__).parent.absolute()
        files = self.get_all_files_recursive(current_dir)
        if not files:
            return False
        for file_path in sorted(files):
            relative_path = file_path.relative_to(current_dir)
            sha256_value = self.calculate_sha256(file_path)
            if str(relative_path) != "check.py":
                shasum_now = self.shasum[str(relative_path)]
                if sha256_value == shasum_now:
                    pass
                else:
                    self.error_files.append(str(relative_path))
            else:
                pass
        if self.error_files == []:
            return True
        else:
            return False

class Before_Start_Check():
    def __init__(self) -> None:
        """初始化"""
        self.network = self.check_network()
        self.audio_library = self.check_audio_library()

    def check_network(self) -> bool:
        """检查网络连接"""
        import requests
        try:
            requests.get('https://www.baidu.com', timeout=3)
            return True
        except:
            return False


    def check_audio_library(self) -> bool:
        """检查C++音频捕获库是否可用"""
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
            print("✓ C++音频捕获库导入成功")
            return True
        except ImportError as e:
            print("✗ 无法导入C++音频捕获库，请复制以下错误信息，并在GitHub上提交issue以获取帮助")
            print(f"错误详情: {e}")
            return False
        except Exception as e:
            print("✗ 检查音频库时出错，请复制以下错误信息，并在GitHub上提交issue以获取帮助")
            print(f"错误详情: {e}")
            return False