import os
from PIL import Image, ImageOps
import math
import tkinter as tk
from tkinter import filedialog, ttk, messagebox,colorchooser
from enum import Enum, auto


# 定数定義
TARGET_RESOLUTIONS = {
    "1024:1024": [(1024, 1024)],
    "832/1216": [
        (1216, 832),   # 横長モード
        (832, 1216)    # 縦長モード
    ],
    "768/1344": [
        (1344, 768),   # 横長モード
        (768, 1344)    # 縦長モード
    ],
    "896/1152": [
        (1152, 896),   # 横長モード
        (896, 1152)    # 縦長モード
    ]
}

class AlignMode(Enum):
    TOP_LEFT = auto()
    TOP_CENTER = auto()
    TOP_RIGHT = auto()
    CENTER_LEFT = auto()
    CENTER = auto()
    CENTER_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_CENTER = auto()
    BOTTOM_RIGHT = auto()

class ProcessStatus:
    def __init__(self):
        self.is_running = False
        self.should_stop = False

class ImageProcessor:
    def __init__(self):
        self.process_status = ProcessStatus()
        self.setup_gui()

    def setup_gui(self):
        """GUIの設定"""
        self.root = tk.Tk() 
        self.root.title("Image Processor")
        self.root.geometry("600x500")  # ウィンドウサイズを少し大きくして新しい要素を収める

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # フォルダ選択部分
        ttk.Label(main_frame, text="処理するフォルダ:").grid(row=0, column=0, sticky=tk.W)
        self.folder_path = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.folder_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(main_frame, text="参照...", command=self.select_folder).grid(row=0, column=2)

        # リサイズモード選択
        ttk.Label(main_frame, text="リサイズモード:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.resize_mode = tk.StringVar(value="CROP")
        resize_frame = ttk.Frame(main_frame)
        resize_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W)
        
        ttk.Radiobutton(resize_frame, text="トリミング", value="CROP", 
                        variable=self.resize_mode).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(resize_frame, text="フィット", value="FIT", 
                        variable=self.resize_mode).grid(row=0, column=1, padx=5)

        # 背景色設定
        bg_frame = ttk.Frame(main_frame)
        bg_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(bg_frame, text="背景色:").grid(row=0, column=0, sticky=tk.W)
        self.bg_color = tk.StringVar(value="#FFFFFF")
        self.bg_color_entry = ttk.Entry(bg_frame, textvariable=self.bg_color, width=8)
        self.bg_color_entry.grid(row=0, column=1, padx=5)
        ttk.Button(bg_frame, text="色選択", command=self.choose_color).grid(row=0, column=2, padx=5)
        
        self.use_transparent = tk.BooleanVar(value=False)
        ttk.Checkbutton(bg_frame, text="透明背景を使用", 
                        variable=self.use_transparent).grid(row=0, column=3, padx=10)

        # アライメントモード選択
        ttk.Label(main_frame, text="リサイズ位置:").grid(row=3, column=0, sticky=tk.W, pady=10)
        self.align_mode = tk.StringVar(value="CENTER")
        align_frame = ttk.Frame(main_frame)
        align_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W)

        align_modes = [
            ("左上", "TOP_LEFT"), ("上", "TOP_CENTER"), ("右上", "TOP_RIGHT"),
            ("左", "CENTER_LEFT"), ("中央", "CENTER"), ("右", "CENTER_RIGHT"),
            ("左下", "BOTTOM_LEFT"), ("下", "BOTTOM_CENTER"), ("右下", "BOTTOM_RIGHT")
        ]

        for i, (text, value) in enumerate(align_modes):
            ttk.Radiobutton(align_frame, text=text, value=value, 
                        variable=self.align_mode).grid(row=i//3, column=i%3, padx=5, pady=2)

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        # リサイズボタン
        self.resize_button = ttk.Button(button_frame, text="リサイズ実行", 
                                    command=self.run_resize_processing)
        self.resize_button.grid(row=0, column=0, padx=10)
        
        # 反転ボタン
        self.flip_button = ttk.Button(button_frame, text="奇数番目の画像を左右反転", 
                                    command=self.run_flip_processing)
        self.flip_button.grid(row=0, column=1, padx=10)

        # 中止ボタン
        self.stop_button = ttk.Button(button_frame, text="処理中止", 
                                    command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=2, padx=10)

        # プログレスバーとステータス
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, length=300, mode='determinate', 
                                    variable=self.progress_var)
        self.progress.grid(row=5, column=0, columnspan=3, pady=10)
        
        self.status_var = tk.StringVar(value="待機中...")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=6, column=0, columnspan=3)

    def select_folder(self):
        """フォルダ選択ダイアログを表示"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
    
    def choose_color(self):
        """色選択ダイアログを表示"""
        color = colorchooser.askcolor(color=self.bg_color.get())[1]
        if color:
            self.bg_color.set(color)

    def find_best_resolution(self, width, height):
        """最適な解像度を見つける"""
        original_ratio = width / height
        best_score = float('inf')
        best_resolution = None

        for resolutions in TARGET_RESOLUTIONS.values():
            for target_width, target_height in resolutions:
                target_ratio = target_width / target_height
                score = abs(original_ratio - target_ratio)
                
                if score < best_score:
                    best_score = score
                    best_resolution = (target_width, target_height)

        return best_resolution

    def calculate_crop_box(self, img_size, target_size, align_mode):
        """アライメントモードに基づいて切り取り範囲を計算"""
        img_width, img_height = img_size
        target_width, target_height = target_size
        
        ratio = max(target_width / img_width, target_height / img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        if align_mode in [AlignMode.TOP_LEFT, AlignMode.TOP_CENTER, AlignMode.TOP_RIGHT]:
            y = 0
        elif align_mode in [AlignMode.CENTER_LEFT, AlignMode.CENTER, AlignMode.CENTER_RIGHT]:
            y = (new_height - target_height) // 2
        else:
            y = new_height - target_height

        if align_mode in [AlignMode.TOP_LEFT, AlignMode.CENTER_LEFT, AlignMode.BOTTOM_LEFT]:
            x = 0
        elif align_mode in [AlignMode.TOP_CENTER, AlignMode.CENTER, AlignMode.BOTTOM_CENTER]:
            x = (new_width - target_width) // 2
        else:
            x = new_width - target_width

        return (x, y, x + target_width, y + target_height), (new_width, new_height)

    def resize_image(self, input_path, output_path, align_mode_str):
        """画像のリサイズ処理"""
        try:
            align_mode = AlignMode[align_mode_str]
            with Image.open(input_path) as img:
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')

                best_resolution = self.find_best_resolution(*img.size)
                crop_box, resize_size = self.calculate_crop_box(img.size, best_resolution, align_mode)
                
                resized_img = img.resize(resize_size, Image.Resampling.LANCZOS)
                final_img = resized_img.crop(crop_box)
                
                final_img.save(output_path, format='PNG', optimize=True)
                return True
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            return False

    def flip_image(self, input_path, output_path):
        """画像の反転処理"""
        try:
            with Image.open(input_path) as img:
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                flipped_img = ImageOps.mirror(img)
                flipped_img.save(output_path, format='PNG', optimize=True)
                return True
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            return False

    def run_resize_processing(self):
        """リサイズ処理の実行"""
        if self.process_status.is_running:
            return

        input_folder = self.folder_path.get()
        if not self.validate_folder(input_folder):
            return

        self.process_status.is_running = True
        self.update_button_states()
        self.root.update()  # この行を追加
        self.process_status.should_stop = False

        try:
            # 出力フォルダの作成
            output_folder = os.path.join(input_folder, "resize")
            os.makedirs(output_folder, exist_ok=True)

            # 画像ファイルのリストを作成
            supported_formats = {'.jpg', '.jpeg', '.png', '.webp'}
            files_to_process = [f for f in os.listdir(input_folder) 
                              if os.path.splitext(f)[1].lower() in supported_formats]
            
            if not files_to_process:
                self.status_var.set("処理対象の画像がありません。")
                return

            total_files = len(files_to_process)
            processed_files = 0

            for filename in files_to_process:
                if self.process_status.should_stop:
                    break

                input_path = os.path.join(input_folder, filename)
                output_path = os.path.join(output_folder,
                                         os.path.splitext(filename)[0] + ".png")
                
                if self.resize_image(input_path, output_path, self.align_mode.get()):
                    processed_files += 1
                    progress = (processed_files / total_files) * 100
                    self.progress_var.set(progress)
                    self.status_var.set(f"処理中... {processed_files}/{total_files}")
                
                self.root.update()

            if self.process_status.should_stop:
                self.status_var.set("処理が中止されました。")
            else:
                self.status_var.set("リサイズ処理が完了しました。")

        except Exception as e:
            self.status_var.set(f"エラーが発生しました: {str(e)}")
        finally:
            self.process_status.is_running = False
            self.process_status.should_stop = False
            self.update_button_states()
            self.root.update()
            
    def resize_image(self, input_path, output_path, align_mode_str):
        """画像のリサイズ処理"""
        try:
            align_mode = AlignMode[align_mode_str]
            with Image.open(input_path) as img:
                # まず元画像を適切なモードに変換
                has_alpha = 'A' in img.getbands() or 'transparency' in img.info
                if self.use_transparent.get() and has_alpha:
                    # 透明背景を使用し、元画像に透過情報がある場合
                    img = img.convert('RGBA')
                elif self.use_transparent.get():
                    # 透明背景を使用するが、元画像に透過情報がない場合
                    img = img.convert('RGBA')
                else:
                    # 透明背景を使用しない場合
                    img = img.convert('RGB')

                best_resolution = self.find_best_resolution(*img.size)
                
                if self.resize_mode.get() == "CROP":
                    # 既存の切り取りモード
                    crop_box, resize_size = self.calculate_crop_box(img.size, best_resolution, align_mode)
                    resized_img = img.resize(resize_size, Image.Resampling.LANCZOS)
                    final_img = resized_img.crop(crop_box)
                else:
                    # フィットモード
                    ratio = min(best_resolution[0] / img.size[0], best_resolution[1] / img.size[1])
                    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                    resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    if self.use_transparent.get():
                        # 透明背景の場合
                        final_img = Image.new('RGBA', best_resolution, (0, 0, 0, 0))
                        # 中央に配置
                        paste_x = (best_resolution[0] - new_size[0]) // 2
                        paste_y = (best_resolution[1] - new_size[1]) // 2
                        final_img.paste(resized_img, (paste_x, paste_y))
                    else:
                        # 背景色を使用する場合
                        bg_color = tuple(int(self.bg_color.get()[i:i+2], 16) for i in (1, 3, 5))
                        final_img = Image.new('RGB', best_resolution, bg_color)
                        # 中央に配置
                        paste_x = (best_resolution[0] - new_size[0]) // 2
                        paste_y = (best_resolution[1] - new_size[1]) // 2
                        final_img.paste(resized_img, (paste_x, paste_y))
                
                # 保存
                if self.use_transparent.get():
                    final_img.save(output_path, format='PNG')
                else:
                    final_img.save(output_path, format='PNG', optimize=True)
                
                return True
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            return False
    
    def run_flip_processing(self):
        """反転処理の実行"""
        if self.process_status.is_running:
            return

        input_folder = self.folder_path.get()
        if not self.validate_folder(input_folder):
            return

        self.process_status.is_running = True
        self.update_button_states()
        self.root.update()
        self.process_status.should_stop = False

        try:
            # 出力フォルダの作成
            output_folder = os.path.join(input_folder, "flipped")
            os.makedirs(output_folder, exist_ok=True)

            # 画像ファイルのリストを作成（サポートされている形式のみ）
            supported_formats = {'.jpg', '.jpeg', '.png', '.webp'}
            files = sorted([f for f in os.listdir(input_folder) 
                        if os.path.splitext(f)[1].lower() in supported_formats])
            
            # 奇数番目（1から数えて）のファイルのみを抽出
            odd_numbered_files = files[::2]  # 0, 2, 4... のインデックスを取得（1枚目、3枚目、5枚目...に相当）
            
            if not odd_numbered_files:
                self.status_var.set("処理対象の画像がありません。")
                return

            total_files = len(odd_numbered_files)
            processed_files = 0

            for filename in odd_numbered_files:
                if self.process_status.should_stop:
                    break

                input_path = os.path.join(input_folder, filename)
                output_path = os.path.join(output_folder, filename)
                
                if self.flip_image(input_path, output_path):
                    processed_files += 1
                    progress = (processed_files / total_files) * 100
                    self.progress_var.set(progress)
                    self.status_var.set(f"処理中... {processed_files}/{total_files}")
                
                self.root.update()

            if self.process_status.should_stop:
                self.status_var.set("処理が中止されました。")
            else:
                self.status_var.set("反転処理が完了しました。")

        except Exception as e:
            self.status_var.set(f"エラーが発生しました: {str(e)}")
        finally:
            self.process_status.is_running = False
            self.process_status.should_stop = False
            self.update_button_states()
            self.root.update()

    def validate_folder(self, folder):
        """フォルダの検証"""
        if not folder:
            self.status_var.set("フォルダを選択してください。")
            return False
        
        if not os.path.exists(folder):
            self.status_var.set("指定されたフォルダが存在しません。")
            return False
        
        return True

    def update_button_states(self):
        """ボタンの状態を更新"""
        if self.process_status.is_running:
            self.resize_button.config(state=tk.DISABLED)
            self.flip_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.resize_button.config(state=tk.NORMAL)
            self.flip_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def stop_processing(self):
        """処理の中止"""
        if self.process_status.is_running:
            self.process_status.should_stop = True
            self.status_var.set("処理を中止しています...")

    def run(self):
        """アプリケーションの実行"""
        self.root.mainloop()

def main():
    processor = ImageProcessor()
    processor.run()

if __name__ == "__main__":
    main()