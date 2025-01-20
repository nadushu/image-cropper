import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
from tkinterdnd2 import DND_FILES, TkinterDnD
import math

class ImageCropper:
    """画像切り抜きツール"""  
#--------------------------------------
#
#初期化
#
#--------------------------------------
    def __init__(self, root):
        self.root = root
        self.root.title("Image Cropper")
        self._init_variables()
        self._setup_ui()
        self._setup_bindings()
        
    def _init_variables(self):
        """変数の初期化"""
        # 基本設定
        self.scale = 1.0
        self.rotation_angle = 0
        self.fixed_size_mode = False
        self.resize_save_mode = False  # リサイズして保存モード

        # 以下の変数を追加
        self.is_resizing = False
        self.resize_edge = None
        self.start_coords = None
        # 画像関連
        self.image = None
        self.pil_image = None
        self.photo = None
        self.current_file_path = None
        self.image_bounds = None
        
        # フリー回転用の変数を追加
        self.is_rotating = False
        self.rotation_start_x = None
        self.rotation_start_y = None
        self.free_rotation_angle = 0  # フリー回転用の角度
        self.rotation_timer = None  # 回転処理用のタイマーを追加
        self.rotation_start_angle = 0 # 回転開始時の角度を追加



        # 左右反転用の変数
        self.is_flipped = False
        
        # 保存先のデフォルトパス用変数を追加
        self.save_directory = None
        
        # 矩形選択関連
        self.rect_id = None
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.is_moving = False
        self.rect_size = 0

        self.is_right_dragging = False  # 右クリックドラッグ状態の管理
        self.last_drag_y = None        # 前回のドラッグY座標
        self.last_drag_x = None  # X座標用の変数を追加


        
        # クロップモード設定
        self.crop_modes = {
            "1:1": (1, 1),
            "1216:832": (1216, 832),
            "832:1216": (832, 1216)
        }
        self.current_mode = "1:1"

    def _setup_ui(self):
        """UIコンポーネントの設定"""
        self._create_main_frame()
        self._create_button_frame()
        self._create_canvas_container()
        self._create_buttons()

    def _create_main_frame(self):
        """メインフレームの作成"""
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def _create_button_frame(self):
        """ボタンフレームの作成"""
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(side=tk.TOP, fill=tk.X)

    def _create_canvas_container(self):
        """キャンバスコンテナの作成"""
        # サイズ表示用フレームとラベル
        self.size_frame = tk.Frame(self.main_frame)
        self.size_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.image_size_label = tk.Label(self.size_frame, text="Image Size: -")
        self.image_size_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        #キャンバスコンテナ
        self.rect_size_label = tk.Label(self.size_frame, text="Selection Size: -")
        self.rect_size_label.pack(side=tk.RIGHT, padx=5, pady=2)
        
        self.canvas_container = tk.Frame(self.main_frame)
        self.canvas_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # キャンバスとスクロールバーを作成
        self.canvas = tk.Canvas(self.canvas_container, bg='#f0f0f0')
        self.scrollbar_y = tk.Scrollbar(self.canvas_container, orient=tk.VERTICAL)
        self.scrollbar_x = tk.Scrollbar(self.canvas_container, orient=tk.HORIZONTAL)

        # スクロールバーとキャンバスを配置
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # スクロールバーとキャンバスを連動
        self.canvas.configure(xscrollcommand=self.scrollbar_x.set,
                            yscrollcommand=self.scrollbar_y.set)
        self.scrollbar_x.configure(command=self.canvas.xview)
        self.scrollbar_y.configure(command=self.canvas.yview)

        # ドラッグ&ドロップの設定
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind('<<Drop>>', self.on_drop)

    def _create_buttons(self):
        """ボタンの作成"""
        # 基本操作ボタン
        self.open_button = tk.Button(self.button_frame, text="Open", command=self.load_image)
        self.open_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.save_button = tk.Button(self.button_frame, text="Save", command=self.save_crop)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # リサイズ保存トグルボタン
        self.resize_save_var = tk.BooleanVar()
        self.resize_save_button = tk.Checkbutton(
            self.button_frame, 
            text="Resize and Save",
            variable=self.resize_save_var,
            command=lambda: setattr(self, 'resize_save_mode', self.resize_save_var.get())
        )
        self.resize_save_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 保存先指定ボタン
        self.save_dir_button = tk.Button(self.button_frame, text="Save Directory", command=self.set_save_directory)
        self.save_dir_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 回転ボタン
        self.rotate_button = tk.Button(self.button_frame, text="Rotate", command=self.rotate_image)
        self.rotate_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 回転リセットボタン
        self.reset_rotation_button = tk.Button(
            self.button_frame, 
            text="回転リセット", 
            command=self.reset_rotation
        )
        self.reset_rotation_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 左右反転ボタン
        self.flip_button = tk.Button(
            self.button_frame, 
            text="左右反転", 
            command=self.flip_horizontal
        )
        self.flip_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Fixed Sizeトグルボタン
        self.fixed_size_var = tk.BooleanVar()
        self.fixed_size_button = tk.Checkbutton(
            self.button_frame, 
            text="Fixed Size",
            variable=self.fixed_size_var,
            command=self.toggle_fixed_size
        )
        self.fixed_size_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # モードボタン（順番を指定）
        mode_order = ["1:1", "1216:832", "832:1216"]
        self.mode_buttons = {}
        for mode in mode_order:
            btn = tk.Button(
                self.button_frame,
                text=mode,
                command=lambda m=mode: self.change_mode(m)
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)
            self.mode_buttons[mode] = btn
        
        # 初期状態のボタンスタイルを設定
        self._update_mode_display()

        # 初期ウィンドウサイズを記録
        self.last_width = self.root.winfo_width()
        self.last_height = self.root.winfo_height()

    def _setup_bindings(self):
        """イベントバインディングの設定"""
        # キャンバスイベント
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # 右クリックイベント
        self.canvas.bind("<ButtonPress-3>", self.on_right_press)     # 右クリック押下
        self.canvas.bind("<B3-Motion>", self.on_right_drag)         # 右クリックドラッグ
        self.canvas.bind("<ButtonRelease-3>", self.on_right_release) # 右クリック解放
        
        # ダブルクリックイベントを追加
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        
        # ルートウィンドウイベント
        self.root.bind("<MouseWheel>", self.zoom_with_mousewheel)
        self.root.bind("<Control-MouseWheel>", self.scroll_vertical)
        self.root.bind("<Shift-MouseWheel>", self.scroll_horizontal)
        self.root.bind("z", lambda e: self.zoom_with_key(1.1))
        self.root.bind("x", lambda e: self.zoom_with_key(0.9))
        self.root.bind('s', lambda e: self.save_crop())
        self.root.bind('a', lambda e: self.load_image())
        self.root.bind('r', lambda e: self.rotate_image())
        self.root.bind('<Alt-s>', lambda e: self.save_crop(force_resize=True))
        self.root.bind("<Configure>", self.on_window_resize)
        
         # 回転リセット用のキーバインド
        self.root.bind('0', lambda e: self.reset_rotation())
        
        # 左右反転用のキーバインド
        self.root.bind('f', lambda e: self.flip_horizontal())
        
        # フリー回転用のバインド
        self.canvas.bind('<Shift-Button-1>', self.start_free_rotation)
        self.canvas.bind('<Shift-B1-Motion>', self.do_free_rotation)
        self.canvas.bind('<Shift-ButtonRelease-1>', self.end_free_rotation)
        
        # 矩形の移動用キーバインド
        self.root.bind('<Left>', lambda e: self.move_rect('left'))
        self.root.bind('<Right>', lambda e: self.move_rect('right'))
        self.root.bind('<Up>', lambda e: self.move_rect('up'))
        self.root.bind('<Down>', lambda e: self.move_rect('down'))

        # ウィンドウサイズを記録
        self.last_width = self.root.winfo_width()
        self.last_height = self.root.winfo_height()
#--------------------------------------
#
#画像表示関連のメソッド
#
#--------------------------------------

    #画像表示
    def display_image(self):
        """画像の表示処理"""
        if self.pil_image is None:
            return

        # 矩形情報を相対位置で保存
        rect_info = self._save_rect_info()
        
        scaled_size = self._calculate_scaled_size()
        scaled_image = self._create_scaled_image(scaled_size)
        
        self.canvas.delete("all")
        self._update_canvas_settings(scaled_size)
        self._draw_image(scaled_size)
        
        # 矩形を中央基準で復元
        self._restore_rect_from_info(rect_info)
        self._update_size_labels()

    def _calculate_scaled_size(self):
        """スケールされたサイズを計算"""
        scaled_width = int(self.pil_image.size[0] * self.scale)
        scaled_height = int(self.pil_image.size[1] * self.scale)
        return (scaled_width, scaled_height)

    def _create_scaled_image(self, scaled_size):
        """スケールされた画像を作成"""
        scaled_image = self.pil_image.resize(scaled_size, Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(scaled_image)
        return scaled_image

    def _update_canvas_settings(self, scaled_size):
        """キャンバスの設定を更新"""
        # 現在のビューポートサイズを取得
        viewport_width = self.canvas.winfo_width()
        viewport_height = self.canvas.winfo_height()
        
        if self.is_rotating:
            # 回転時はビューポートサイズを超えないように設定
            scroll_width = viewport_width
            scroll_height = viewport_height
        else:
            # 通常時は既存の動作を維持
            scaled_width, scaled_height = scaled_size
            scroll_width = max(viewport_width, scaled_width + 40)
            scroll_height = max(viewport_height, scaled_height + 40)
        
        # スクロール領域の設定
        self.canvas.configure(scrollregion=(
            -20, -20,
            scroll_width, scroll_height
        ))

    def _draw_image(self, scaled_size):
        """画像をキャンバスに描画"""
        scaled_width, scaled_height = scaled_size
        
        # キャンバスの中央位置を計算
        viewport_width = self.canvas.winfo_width()
        viewport_height = self.canvas.winfo_height()
        
        # 必ず中央に配置
        x_position = (viewport_width - scaled_width) // 2
        y_position = (viewport_height - scaled_height) // 2
        
        # 画像の背景を描画
        self.canvas.create_rectangle(
            x_position, y_position,
            x_position + scaled_width,
            y_position + scaled_height,
            fill="white",
            outline=""
        )

        # 画像を中央に描画
        self.canvas.create_image(
            viewport_width // 2,
            viewport_height // 2,
            image=self.photo,
            anchor="center"
        )

        # 画像の境界を保存
        self.image_bounds = {
            'x1': x_position,
            'y1': y_position,
            'x2': x_position + scaled_width,
            'y2': y_position + scaled_height,
            'center_x': viewport_width // 2,
            'center_y': viewport_height // 2
        }

    def _restore_selection(self):
        """選択範囲の復元"""
        if self.fixed_size_mode:
            self.create_fixed_rect()
        elif self.rect_id and hasattr(self, 'current_rect_coords'):
            x1, y1 = self.current_rect_coords[:2]
            self.rect_id = self.canvas.create_rectangle(
                x1, y1,
                x1 + self.rect_width,
                y1 + self.rect_height,
                outline="red"
            )
    
    def reset_rotation(self):
        """回転をリセット"""
        if not self.pil_image:
            return

        # 矩形情報を相対位置で保存
        rect_info = self._save_rect_info()
        
        # 回転角度をリセット
        self.rotation_angle = 0
        self.free_rotation_angle = 0
        self.is_rotating = False
        self.is_flipped = False
        
        # 表示用の元画像もリセット
        if hasattr(self, 'original_display_image'):
            del self.original_display_image
        
        # 現在の回転を打ち消す回転を適用
        self.pil_image = Image.open(self.current_file_path)
        if self.pil_image.mode != 'RGBA':
            self.pil_image = self.pil_image.convert('RGBA')
        
        self.display_image()
        
        # 矩形を復元
        if rect_info:
            self._restore_rect_from_info(rect_info)
                
    def flip_horizontal(self):
        """画像を水平方向に反転"""
        if not self.pil_image:
            return

        # 矩形情報を相対位置で保存
        rect_info = self._save_rect_info()
        
        # 画像を水平方向に反転
        self.pil_image = self.pil_image.transpose(Image.FLIP_LEFT_RIGHT)
        self.is_flipped = not self.is_flipped
        
        self.display_image()
        
        # 矩形を復元
        if rect_info:
            self._restore_rect_from_info(rect_info)
            
    def start_free_rotation(self, event):
        """フリー回転の開始"""
        self.is_rotating = True
        self.rotation_start_x = event.x
        # 開始時の累積角度を保存
        self.rotation_start_angle = self.free_rotation_angle
        
        # 表示用の画像をクリーンな状態で作成
        if not hasattr(self, 'original_display_image'):
            # 初回のみ表示用の元画像を保存
            self.original_display_image = self.pil_image.copy()
        
        # 現在の表示用画像をバックアップ
        self.rotation_backup_image = self.original_display_image.copy()

    def do_free_rotation(self, event):
        """フリー回転の実行"""
        if not self.is_rotating or not self.pil_image:
            return

        if self.rotation_timer:
            self.root.after_cancel(self.rotation_timer)
            self.rotation_timer = None
        
        dx = event.x - self.rotation_start_x
        delta_angle = dx * 0.3
        
        # 開始時の角度を基準に新しい角度を計算
        new_angle = (self.rotation_start_angle + delta_angle) % 360
        print(f"開始角度: {self.rotation_start_angle}, 変化量: {delta_angle}, 新角度: {new_angle}")
        
        self.rotation_timer = self.root.after(5, lambda: self._apply_rotation(new_angle))

    def _apply_rotation(self, angle):
        """回転を適用する（表示用）"""
        if not self.is_rotating:
            return

        # 絶対角度として保存（この角度は後で保存時に使用）
        self.free_rotation_angle = angle
        
        # 矩形情報を保存
        rect_info = self._save_rect_info()
        
        # バックアップ画像から新しい角度で回転（表示用）
        if hasattr(self, 'pil_image'):
            del self.pil_image
        self.pil_image = self.rotation_backup_image.rotate(
            angle,
            expand=True,
            resample=Image.BILINEAR,
            fillcolor='white'
        )
        
        self.display_image()
        
        if rect_info:
            self._restore_rect_from_info(rect_info)
        
        self.rotation_timer = None

    def end_free_rotation(self, event):
        """フリー回転の終了"""
        if self.rotation_timer:
            self.root.after_cancel(self.rotation_timer)
            self.rotation_timer = None
        
        self.is_rotating = False
        
        # 回転操作終了時にバックアップを解放
        if hasattr(self, 'rotation_backup_image'):
            del self.rotation_backup_image
        
        print(f"回転終了時の累積角度: {self.free_rotation_angle}")
            
    def move_rect(self, direction):
        """矩形を1ピクセル移動"""
        if not self.rect_id:
            return
        
        coords = self.canvas.coords(self.rect_id)
        x1, y1, x2, y2 = coords
        
        # 移動量を設定
        dx = dy = 0
        if direction == 'left':
            dx = -1
        elif direction == 'right':
            dx = 1
        elif direction == 'up':
            dy = -1
        elif direction == 'down':
            dy = 1
        
        # スケールを考慮した移動量
        scaled_dx = dx / self.scale
        scaled_dy = dy / self.scale
        
        # 画像の境界をチェック
        new_x1 = x1 + dx
        new_y1 = y1 + dy
        new_x2 = x2 + dx
        new_y2 = y2 + dy
        
        # 境界チェック
        if (new_x1 >= self.image_bounds['x1'] and 
            new_x2 <= self.image_bounds['x2'] and 
            new_y1 >= self.image_bounds['y1'] and 
            new_y2 <= self.image_bounds['y2']):
            
            # 矩形を移動
            self.canvas.coords(self.rect_id, new_x1, new_y1, new_x2, new_y2)
            self.current_rect_coords = [new_x1, new_y1]
                       
    # 矩形選択関連のメソッド
    def on_drag(self, event):
        """マウスドラッグ時の処理"""
        if not self.image_bounds:
            return

        if self.is_resizing:
            self._handle_rect_resize(event)
        elif self.is_moving and self.rect_id:
            self._handle_rect_movement(event)
        elif not self.fixed_size_mode:  # not self.is_moving条件を削除
            self._handle_rect_creation(event)
    
    def on_double_click(self, event):
        """ダブルクリックで矩形を削除"""
        if self.rect_id and self.is_inside_rect(event.x, event.y):
            self.canvas.delete(self.rect_id)
            self.rect_id = None
            
    def on_right_press(self, event):
        """右クリック押下時の処理"""
        if not self.rect_id:
            return
        self.is_right_dragging = True
        self.last_drag_y = event.y
        self.last_drag_x = event.x  # X座標も保存
        # 現在の矩形の座標を保存
        self.start_coords = self.canvas.coords(self.rect_id)

    def on_right_drag(self, event):
        """右クリックドラッグ時の処理（矩形のリサイズ）"""
        if not (self.is_right_dragging and self.last_drag_y is not None and self.rect_id):
            return

        # Y座標とX座標の移動量から拡大縮小率を決定
        delta_y = self.last_drag_y - event.y
        delta_x = event.x - self.last_drag_x  # X方向の移動量（右が正）
        if delta_y != 0 or delta_x != 0:
            ratio_w, ratio_h = self.crop_modes[self.current_mode]
            coords = self.canvas.coords(self.rect_id)
            center_x = (coords[0] + coords[2]) / 2
            center_y = (coords[1] + coords[3]) / 2

            # 現在のサイズを取得
            current_width = coords[2] - coords[0]
            
            # 上下と左右の移動量を組み合わせて倍率を計算
            scale_factor = 1.0
            if abs(delta_y) > abs(delta_x):
                # 上下の移動が大きい場合
                scale_factor *= (1.0 + (delta_y / 200.0))
            else:
                # 左右の移動が大きい場合
                scale_factor *= (1.0 + (delta_x / 200.0))

            # 新しいサイズを計算
            new_width = current_width * scale_factor
            if ratio_w == ratio_h:
                new_height = new_width
            else:
                new_height = (new_width * ratio_h) / ratio_w

            # 中心点から新しい座標を計算
            x1 = center_x - new_width / 2
            y1 = center_y - new_height / 2
            x2 = center_x + new_width / 2
            y2 = center_y + new_height / 2

            # 画像の範囲内に制限
            x1 = max(self.image_bounds['x1'], min(x1, self.image_bounds['x2']))
            y1 = max(self.image_bounds['y1'], min(y1, self.image_bounds['y2']))
            x2 = max(self.image_bounds['x1'], min(x2, self.image_bounds['x2']))
            y2 = max(self.image_bounds['y1'], min(y2, self.image_bounds['y2']))

            # 矩形を更新
            self.canvas.coords(self.rect_id, x1, y1, x2, y2)
            self.current_rect_coords = [x1, y1]
            self.rect_width = x2 - x1
            self.rect_height = y2 - y1

        self.last_drag_y = event.y
        self.last_drag_x = event.x  # X座標も更新

    def on_right_release(self, event):
        """右クリック解放時の処理"""
        self.is_right_dragging = False
        self.last_drag_y = None

    def _handle_rect_movement(self, event):
        """矩形の移動処理"""
        coords = self.canvas.coords(self.rect_id)
        width = coords[2] - coords[0]
        height = coords[3] - coords[1]
        
        new_position = self._calculate_new_position(event, width, height)
        self._update_rect_position(new_position, width, height)

    def _handle_rect_resize(self, event):
        """矩形のリサイズ処理"""
        if not self.rect_id or not self.start_coords:
            return

        x1, y1, x2, y2 = self.start_coords
        ratio_w, ratio_h = self.crop_modes[self.current_mode]
        
        if self.resize_edge == 'right':
            new_width = max(10, event.x - x1)  # 最小幅を10pxに設定
            if ratio_w == ratio_h:  # 1:1の場合
                new_height = new_width
                y2 = y1 + new_height
            else:
                new_height = (new_width * ratio_h) / ratio_w
                y2 = y1 + new_height
            x2 = x1 + new_width
        elif self.resize_edge == 'left':
            new_width = max(10, x2 - event.x)
            if ratio_w == ratio_h:
                new_height = new_width
                y2 = y1 + new_height
            else:
                new_height = (new_width * ratio_h) / ratio_w
                y2 = y1 + new_height
            x1 = x2 - new_width
        elif self.resize_edge == 'bottom':
            new_height = max(10, event.y - y1)
            if ratio_w == ratio_h:
                new_width = new_height
                x2 = x1 + new_width
            else:
                new_width = (new_height * ratio_w) / ratio_h
                x2 = x1 + new_width
            y2 = y1 + new_height
        elif self.resize_edge == 'top':
            new_height = max(10, y2 - event.y)
            if ratio_w == ratio_h:
                new_width = new_height
                x2 = x1 + new_width
            else:
                new_width = (new_height * ratio_w) / ratio_h
                x2 = x1 + new_width
            y1 = y2 - new_height

        # 画像の範囲内に制限
        x1 = max(self.image_bounds['x1'], min(x1, self.image_bounds['x2']))
        y1 = max(self.image_bounds['y1'], min(y1, self.image_bounds['y2']))
        x2 = max(self.image_bounds['x1'], min(x2, self.image_bounds['x2']))
        y2 = max(self.image_bounds['y1'], min(y2, self.image_bounds['y2']))

        # 矩形を更新
        self.canvas.coords(self.rect_id, x1, y1, x2, y2)
        self.current_rect_coords = [x1, y1]
        self.rect_width = x2 - x1
        self.rect_height = y2 - y1

    def _update_rect_position(self, position, width, height):
        """矩形の位置を更新"""
        new_x, new_y = position
        self.canvas.coords(
            self.rect_id,
            new_x, new_y,
            new_x + width,
            new_y + height
        )
        self.current_rect_coords = [new_x, new_y]

    def _handle_rect_creation(self, event):
        """矩形の新規作成処理"""
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        constrained_pos = self._constrain_to_image(event)
        rect_dims = self._calculate_rect_dimensions(constrained_pos)
        self._create_new_rect(rect_dims)

    def _calculate_new_position(self, event, width, height):
        """移動後の位置を計算"""
        new_x = event.x - self.drag_offset_x
        new_y = event.y - self.drag_offset_y
        
        # 画像の範囲内に制限
        new_x = max(self.image_bounds['x1'], 
                min(new_x, self.image_bounds['x2'] - width))
        new_y = max(self.image_bounds['y1'], 
                min(new_y, self.image_bounds['y2'] - height))
        
        return (new_x, new_y)

    def _constrain_to_image(self, event):
        """イベント位置を画像の範囲内に制限"""
        x = max(self.image_bounds['x1'], 
                min(event.x, self.image_bounds['x2']))
        y = max(self.image_bounds['y1'], 
                min(event.y, self.image_bounds['y2']))
        return (x, y)

    def _calculate_rect_dimensions(self, pos):
        """矩形のサイズと位置を計算"""
        ratio_w, ratio_h = self.crop_modes[self.current_mode]
        event_x, event_y = pos
        
        if ratio_w == ratio_h:
            # 1:1の場合
            width = height = min(abs(event_x - self.start_x),
                            abs(event_y - self.start_y))
        else:
            # その他の比率の場合
            width = abs(event_x - self.start_x)
            height = (width * ratio_h) / ratio_w
        
        x1 = self.start_x
        y1 = self.start_y
        
        if event_x < self.start_x:
            x1 = self.start_x - width
        if event_y < self.start_y:
            y1 = self.start_y - height
        
        # 画像内に収める
        x1 = max(self.image_bounds['x1'], min(x1, self.image_bounds['x2'] - width))
        y1 = max(self.image_bounds['y1'], min(y1, self.image_bounds['y2'] - height))
        
        return (x1, y1, width, height)

    def _create_new_rect(self, dimensions):
        """新しい矩形を作成"""
        x1, y1, width, height = dimensions
        self._create_rect(x1, y1, x1 + width, y1 + height)

    # ファイル操作関連のメソッド
    def load_image(self):
        """画像ファイルを読み込む"""
        file_path = self._show_file_dialog()
        if file_path:
            self.load_image_from_path(file_path)

    def load_image_from_path(self, file_path):
        try:
            # まず元画像を読み込み
            original_image = Image.open(file_path)
            if original_image.mode != 'RGBA':
                original_image = original_image.convert('RGBA')

            # 表示用の最大サイズを設定
            MAX_DISPLAY_SIZE = 2000  # この値は調整可能

            # 画像が大きすぎる場合は縮小
            width, height = original_image.size
            if width > MAX_DISPLAY_SIZE or height > MAX_DISPLAY_SIZE:
                # アスペクト比を維持しながら縮小
                ratio = min(MAX_DISPLAY_SIZE / width, MAX_DISPLAY_SIZE / height)
                new_size = (int(width * ratio), int(height * ratio))
                self.pil_image = original_image.resize(new_size, Image.Resampling.LANCZOS)
            else:
                self.pil_image = original_image

            # 元のファイルパスは保持（保存時に使用）
            self.current_file_path = file_path
            self._init_image_settings()
            self.display_image()
            self._update_size_labels()

        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def _show_file_dialog(self):
        """ファイル選択ダイアログを表示"""
        file_types = [
            ("All supported formats", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.gif;*.tiff"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg;*.jpeg"),
            ("WebP files", "*.webp"),
            ("BMP files", "*.bmp"),
            ("GIF files", "*.gif"),
            ("TIFF files", "*.tiff"),
            ("All files", "*.*")
        ]
        return filedialog.askopenfilename(filetypes=file_types)

    def _init_image_settings(self):
        """画像読み込み時の初期設定"""
        self.rotation_angle = 0
        
        if self.pil_image.mode != 'RGBA':
            self.pil_image = self.pil_image.convert('RGBA')
        
        # ウィンドウサイズに基づいたスケール計算
        viewport_width = self.canvas.winfo_width()
        viewport_height = self.canvas.winfo_height()
        
        # 余白を考慮（ボタンやラベルのスペース）
        margin = 50  # ボタンやラベル用の余白
        available_height = viewport_height - margin
        available_width = viewport_width - margin
        
        # 画像の元サイズ
        img_width, img_height = self.pil_image.size
        
        # アスペクト比を維持しながら、ウィンドウに収まるようにスケール計算
        width_scale = available_width / img_width
        height_scale = available_height / img_height
        self.scale = min(width_scale, height_scale)  # 小さい方のスケールを採用
        
        # 既存の選択をクリア
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    def save_crop(self, force_resize=False):
        """選択範囲を保存"""
        if not self._can_save():
            return

        cropped_image = self._get_cropped_image()
        if cropped_image and (self.resize_save_mode or force_resize):
            # モードに応じたサイズを取得
            ratio_w, ratio_h = self.crop_modes[self.current_mode]
            if self.current_mode == "1:1":
                target_width = target_height = 1024
            else:
                if ratio_w > ratio_h:  # 横長
                    target_width = 1216
                    target_height = 832
                else:  # 縦長
                    target_width = 832
                    target_height = 1216

            # 現在のサイズを確認
            current_width, current_height = cropped_image.size
            # サイズが既に目標と同じ場合はリサイズしない
            if current_width != target_width or current_height != target_height:
                cropped_image = cropped_image.resize(
                    (target_width, target_height),
                    Image.Resampling.LANCZOS
                )

        if cropped_image:
            self._save_image(cropped_image)

    def _can_save(self):
        """保存可能か確認"""
        return (self.rect_id is not None and 
                self.pil_image is not None and 
                len(self.canvas.coords(self.rect_id)) == 4)

    def _get_cropped_image(self):
        """選択範囲の画像を取得（保存用）"""
        if not self.rect_id:
            return None
        
        # 元画像を読み込んで回転を適用
        original_image = Image.open(self.current_file_path)
        if original_image.mode != 'RGBA':
            original_image = original_image.convert('RGBA')

        if self.is_flipped:
            original_image = original_image.transpose(Image.FLIP_LEFT_RIGHT)

        # 自由回転を適用
        if self.free_rotation_angle != 0:
            import cv2
            import numpy as np
            
            img_array = np.array(original_image)
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
            
            print(f"保存時の回転角度: {self.free_rotation_angle}")
            height, width = img_array.shape[:2]
            center = (width/2, height/2)
            
            # 累積された最終角度で回転を適用
            rotation_matrix = cv2.getRotationMatrix2D(center, self.free_rotation_angle, 1.0)
            
            abs_cos = abs(rotation_matrix[0,0])
            abs_sin = abs(rotation_matrix[0,1])
            new_width = int(height * abs_sin + width * abs_cos)
            new_height = int(height * abs_cos + width * abs_sin)
            
            rotation_matrix[0, 2] += new_width/2 - center[0]
            rotation_matrix[1, 2] += new_height/2 - center[1]
            
            rotated = cv2.warpAffine(
                img_array,
                rotation_matrix,
                (new_width, new_height),
                flags=cv2.INTER_LANCZOS4,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(255, 255, 255, 255)
            )
            
            rotated = cv2.cvtColor(rotated, cv2.COLOR_BGRA2RGBA)
            original_image = Image.fromarray(rotated)

        # 90度回転を適用
        if self.rotation_angle != 0:
            original_image = original_image.rotate(
                -self.rotation_angle,
                expand=True,
                fillcolor='white'
            )

        # スケール計算と座標変換
        scale_factor = original_image.size[0] / self.pil_image.size[0]
        coords = self.canvas.coords(self.rect_id)
        
        x1 = (coords[0] - self.image_bounds['x1']) / self.scale * scale_factor
        y1 = (coords[1] - self.image_bounds['y1']) / self.scale * scale_factor
        x2 = (coords[2] - self.image_bounds['x1']) / self.scale * scale_factor
        y2 = (coords[3] - self.image_bounds['y1']) / self.scale * scale_factor
        
        x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
        
        return original_image.crop((x1, y1, x2, y2))

    def _convert_coords_to_image_space(self, coords):
        """キャンバス座標を画像座標に変換"""
        x1, y1, x2, y2 = coords
        # 整数に変換する前の正確な座標を計算
        x1 = (x1 - self.image_bounds['x1']) / self.scale
        y1 = (y1 - self.image_bounds['y1']) / self.scale
        x2 = (x2 - self.image_bounds['x1']) / self.scale
        y2 = (y2 - self.image_bounds['y1']) / self.scale
        
        # 切り捨てと切り上げを適切に使用
        return (
            int(x1),  # 左端は切り捨て
            int(y1),  # 上端は切り捨て
            int(x2 + 0.5),  # 右端は四捨五入
            int(y2 + 0.5)   # 下端は四捨五入
        )

    def _save_image(self, image):
        """画像を保存"""
        file_path = self._get_save_path()
        if file_path:
            image.save(file_path, "PNG")
            
    def set_save_directory(self):
        """保存先ディレクトリを設定"""
        # 現在の保存先かファイルのディレクトリをデフォルトとして表示
        initial_dir = self.save_directory or (
            os.path.dirname(self.current_file_path) if self.current_file_path 
            else os.getcwd()
        )
        
        directory = filedialog.askdirectory(
            initialdir=initial_dir,
            title="Select Save Directory"
        )
        
        if directory:
            self.save_directory = directory


    def _get_save_path(self):
        """保存先のパスを取得"""
        # 保存先ディレクトリの決定
        save_dir = self.save_directory or (
            os.path.dirname(self.current_file_path) if self.current_file_path 
            else None
        )
        
        base_name = self._generate_base_filename()
        file_path = self._generate_unique_filepath(save_dir, base_name)
        
        # ファイル保存ダイアログを表示（デフォルトディレクトリを指定）
        return filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
            initialdir=save_dir,
            initialfile=os.path.basename(file_path)
        )

    def _generate_base_filename(self):
        """基本ファイル名を生成"""
        if self.current_file_path:
            return os.path.splitext(os.path.basename(self.current_file_path))[0]
        return "cropped"

    def _generate_unique_filepath(self, directory, base_name):
        """重複しないファイルパスを生成"""
        if not directory:
            return f"{base_name}.png"
            
        base_path = os.path.join(directory, f"{base_name}_cropped.png")
        counter = 1
        file_path = base_path
        
        while os.path.exists(file_path):
            file_path = os.path.join(directory, f"{base_name}_cropped_{counter:03d}.png")
            counter += 1
        
        return file_path

    # 画像回転関連のメソッド
    def rotate_image(self):
        """画像を90度時計回りに回転"""
        if not self.pil_image:
            return

        # 矩形情報を相対位置で保存
        rect_info = self._save_rect_info()
    
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.pil_image = self.pil_image.rotate(-90, expand=True)
        
        self.display_image()
        
        # 矩形を中央基準で復元
        if rect_info:
            self._restore_rect_from_info(rect_info)
            self._update_size_labels()
    
    def _reset_selection(self):
        """選択範囲をリセット"""
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    # ズーム関連のメソッド
    def zoom_with_mousewheel(self, event):
        """マウスホイールでのズーム処理"""
        if not self.pil_image:
            return
        
        old_scale = self.scale
        self._update_zoom_scale(event)
        
        if old_scale != self.scale:
            self.display_image()

    def zoom_with_key(self, factor):
        """キーボードでのズーム処理"""
        if not self.pil_image:
            return
        
        old_scale = self.scale
        self.scale *= factor
        
        if old_scale != self.scale:
            self.display_image()

    def _update_zoom_scale(self, event):
        """ズームスケールを更新"""
        if event.delta > 0:
            self.scale *= 1.1
        else:
            self.scale *= 0.9

    # スクロール関連のメソッド
    def scroll_vertical(self, event):
        """垂直スクロール処理"""
        if not self.pil_image:
            return
        
        self._scroll_canvas(event, "vertical")

    def scroll_horizontal(self, event):
        """水平スクロール処理"""
        if not self.pil_image:
            return
        
        self._scroll_canvas(event, "horizontal")

    def _scroll_canvas(self, event, direction):
        """キャンバスのスクロール処理"""
        # スクロール量を計算（event.deltaの正負を反転）
        scroll_amount = -1 * (event.delta / 120)  # 120は1回のスクロール単位
        
        if direction == "vertical":
            self.canvas.yview_scroll(int(scroll_amount), "units")
        else:
            self.canvas.xview_scroll(int(scroll_amount), "units")

    # 固定サイズ矩形関連のメソッド
    def create_fixed_rect(self, x=None, y=None):
        """固定サイズの矩形を作成"""
        if not self._can_create_fixed_rect():
            return

        # 画像のサイズを取得
        img_width = self.pil_image.size[0]
        img_height = self.pil_image.size[1]

        # 目標サイズを取得
        target_size = self._calculate_fixed_rect_dimensions()
        rect_width = target_size['width']   # 1024 or 1216/832
        rect_height = target_size['height'] # 1024 or 832/1216

        # 画像サイズと目標サイズの差分を計算
        width_diff = img_width - rect_width
        height_diff = img_height - rect_height

        # クリック位置が指定されていない場合は中央に配置
        if x is None or y is None:
            # 中央配置のための開始位置を計算（整数の除算）
            image_x1 = width_diff // 2
            image_y1 = height_diff // 2
        else:
            # クリック位置を画像座標に変換
            click_x = int((x - self.image_bounds['x1']) / self.scale)
            click_y = int((y - self.image_bounds['y1']) / self.scale)
            
            # クリック位置を中心とした開始位置を計算
            image_x1 = click_x - (rect_width // 2)
            image_y1 = click_y - (rect_height // 2)

            # 画像の範囲内に収める
            image_x1 = max(0, min(image_x1, width_diff))
            image_y1 = max(0, min(image_y1, height_diff))

        # サイズの補正（1024/832/1216で割り切れるようにする）
        if self.current_mode == "1:1":
            # 1024で割り切れるように調整
            image_x1 = (image_x1 // 1024) * 1024
            image_y1 = (image_y1 // 1024) * 1024
        else:
            ratio_w, ratio_h = self.crop_modes[self.current_mode]
            if ratio_w > ratio_h:  # 横長
                image_x1 = (image_x1 // 1216) * 1216
                image_y1 = (image_y1 // 832) * 832
            else:  # 縦長
                image_x1 = (image_x1 // 832) * 832
                image_y1 = (image_y1 // 1216) * 1216

        # キャンバス座標に変換
        canvas_x1 = self.image_bounds['x1'] + (image_x1 * self.scale)
        canvas_y1 = self.image_bounds['y1'] + (image_y1 * self.scale)
        canvas_x2 = canvas_x1 + (rect_width * self.scale)
        canvas_y2 = canvas_y1 + (rect_height * self.scale)

        # 矩形を作成
        self._create_rect(canvas_x1, canvas_y1, canvas_x2, canvas_y2)

    def _can_create_fixed_rect(self):
        """固定サイズ矩形が作成可能か確認"""
        return (self.pil_image and 
                self.fixed_size_mode and 
                self.image_bounds)

    def _calculate_rect_center(self, x=None, y=None):
        """矩形の中心位置を計算"""
        if x is None or y is None:
            return {
                'x': (self.image_bounds['x1'] + self.image_bounds['x2']) / 2,
                'y': (self.image_bounds['y1'] + self.image_bounds['y2']) / 2
            }
        return {'x': x, 'y': y}

    def _calculate_fixed_rect_dimensions(self):
        """固定サイズ矩形の寸法を計算"""
        if self.current_mode == "1:1":
            self.target_width = self.target_height = 1024
        else:
            if self.crop_modes[self.current_mode][0] > self.crop_modes[self.current_mode][1]:  # 横長
                self.target_width = 1216
                self.target_height = 832
            else:  # 縦長
                self.target_width = 832
                self.target_height = 1216
        
        # 固定サイズを直接返す
        return {
            'width': self.target_width,
            'height': self.target_height
        }

    def _adjust_rect_position(self, center, dimensions):
        """矩形の位置を画像内に収める"""
        x1 = center['x'] - dimensions['width'] / 2
        y1 = center['y'] - dimensions['height'] / 2
        
        # 画像の範囲内に制限
        x1 = max(self.image_bounds['x1'], 
                min(x1, self.image_bounds['x2'] - dimensions['width']))
        y1 = max(self.image_bounds['y1'], 
                min(y1, self.image_bounds['y2'] - dimensions['height']))
        
        return {'x1': x1, 'y1': y1}

    def _create_rect_at_position(self, position, dimensions):
        """指定位置に矩形を作成"""
        x1 = position['x1']
        y1 = position['y1']
        x2 = x1 + dimensions['width']
        y2 = y1 + dimensions['height']
        self._create_rect(x1, y1, x2, y2)

    # モード切替関連のメソッド
    def change_mode(self, mode):
        """クロップモードを変更"""
        self.current_mode = mode
        self._update_mode_display()
        self._handle_mode_change()

    def _update_mode_display(self):
        """モードの表示を更新"""
        for mode, button in self.mode_buttons.items():
            if mode == self.current_mode:
                # 選択中のモード
                button.config(
                    text=mode,
                    bg='green',  # 背景色を緑に
                    fg='white',  # 文字色を白に
                    font=('TkDefaultFont', 9, 'bold')  # フォントを太字に
                )
            else:
                # 非選択のモード
                button.config(
                    text=mode,
                    bg='SystemButtonFace',  # デフォルトの背景色
                    fg='black',  # デフォルトの文字色
                    font=('TkDefaultFont', 9, 'normal')  # 通常のフォント
                )
    
    def _handle_mode_change(self):
        """モード変更時の処理"""
        if self.fixed_size_mode:
            self.create_fixed_rect()
        else:
            self._reset_selection()

    def toggle_fixed_size(self):
        """Fixed Sizeモードの切り替え"""
        self.fixed_size_mode = self.fixed_size_var.get()
        if self.fixed_size_mode:
            self.create_fixed_rect()
        else:
            self._reset_selection()

    # ユーティリティメソッド
    def is_inside_rect(self, x, y):
        """点が矩形の内側にあるか判定"""
        if not self.rect_id:
            return False
            
        coords = self.canvas.coords(self.rect_id)
        if not coords:
            return False
            
        x1, y1, x2, y2 = coords
        return x1 <= x <= x2 and y1 <= y <= y2


    def on_window_resize(self, event):
        """ウィンドウリサイズ時の処理"""
        if not self._is_root_window_event(event) or not self._has_image():
            return
        
        # 現在のウィンドウ状態を取得
        current_width = self.canvas.winfo_width()
        current_height = self.canvas.winfo_height()
        
        if current_width != self.last_width or current_height != self.last_height:
            self.last_width = current_width
            self.last_height = current_height
            
            # スクロール位置をリセット
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            
            # 矩形情報を保存
            rect_info = self._save_rect_info()
            
            # キャンバスをクリアして再描画
            self.canvas.delete("all")
            self.canvas.update()
            
            # 画像とキャンバスの設定を更新
            scaled_size = self._calculate_scaled_size()
            self._update_canvas_settings(scaled_size)
            self._draw_image(scaled_size)
            
            # 矩形を復元
            if rect_info:
                self._restore_rect_from_info(rect_info)
    
    # マウスイベント関連のメソッド
    def on_press(self, event):
        """マウスボタンが押された時の処理"""
        self._store_initial_position(event)
        
        if self.rect_id:
            if self.is_inside_rect(event.x, event.y):
                self._start_rect_movement(event)
            else:
                self._move_rect_to_center(event)
        else:
            self._handle_new_rect(event)
                
    def _move_rect_to_center(self, event):
        """クリックした位置に矩形の中心を移動"""
        if not self.rect_id:
            return
            
        # 現在の矩形の幅と高さを取得
        coords = self.canvas.coords(self.rect_id)
        width = coords[2] - coords[0]
        height = coords[3] - coords[1]
        
        # クリックした位置を中心とした新しい座標を計算
        new_x = event.x - width / 2
        new_y = event.y - height / 2
        
        # 画像の範囲内に収まるように制限
        new_x = max(self.image_bounds['x1'], 
                min(new_x, self.image_bounds['x2'] - width))
        new_y = max(self.image_bounds['y1'], 
                min(new_y, self.image_bounds['y2'] - height))
        
        # 矩形を移動
        self.canvas.coords(
            self.rect_id,
            new_x, new_y,
            new_x + width,
            new_y + height
        )
        self.current_rect_coords = [new_x, new_y]
        self.rect_width = width
        self.rect_height = height
        
        # 移動モードに設定し、ドラッグのためのオフセットを設定
        self.is_moving = True
        self.drag_offset_x = event.x - new_x
        self.drag_offset_y = event.y - new_y

    def _store_initial_position(self, event):
        """開始位置を保存"""
        self.start_x = event.x
        self.start_y = event.y

    def _handle_existing_rect(self, event):
        """既存の矩形がある場合の処理"""
        if self.is_inside_rect(event.x, event.y):
            self._start_rect_movement(event)
        else:
            self._clear_and_create_new_rect(event)

    def _start_rect_movement(self, event):
        """矩形の移動を開始"""
        self.is_moving = True
        coords = self.canvas.coords(self.rect_id)
        self.current_rect_coords = coords
        self.drag_offset_x = event.x - coords[0]
        self.drag_offset_y = event.y - coords[1]

    def _clear_and_create_new_rect(self, event):
        """既存の矩形を削除して新しい矩形を作成"""
        self.is_moving = False
        self.canvas.delete(self.rect_id)
        self.rect_id = None
        
        if self.fixed_size_mode:
            self.create_fixed_rect(event.x, event.y)

    def _handle_new_rect(self, event):
        """新しい矩形の作成処理"""
        self.is_moving = False
        if self.fixed_size_mode:
            self.create_fixed_rect(event.x, event.y)

    def on_release(self, event):
        """マウスボタンが離された時の処理"""
        self.is_moving = False
        self.is_resizing = False
        self.resize_edge = None
        self.start_coords = None
        self.click_time = None

    # ドラッグ&ドロップ関連のメソッド
    def on_drop(self, event):
        """ファイルのドロップ処理"""
        file_path = self._get_dropped_file_path(event)
        if self._is_valid_file_path(file_path):
            self.load_image_from_path(file_path)
        else:
            self._show_unsupported_format_error()

    def _get_dropped_file_path(self, event):
        """ドロップされたファイルのパスを取得"""
        file_path = event.data
        
        # Windowsの場合、パスが{}で囲まれている可能性があるため除去
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        
        return file_path

    def _is_valid_file_path(self, file_path):
        """ファイルパスが有効な画像形式か確認"""
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff')
        return file_path.lower().endswith(valid_extensions)

    def _show_unsupported_format_error(self):
        """サポートされていない形式のエラーを表示"""
        messagebox.showerror("Error", "Unsupported file format")

    def _is_root_window_event(self, event):
        """イベントがルートウィンドウからのものか確認"""
        return event.widget == self.root and hasattr(self, 'last_width')

    def _has_image(self):
        """画像が読み込まれているか確認"""
        return self.pil_image is not None
    
    # 共通の矩形操作メソッド
    def _create_rect(self, x1, y1, x2, y2):
        """共通の矩形作成処理"""
        # 中央からの相対位置を計算
        center_x = self.image_bounds['center_x']
        center_y = self.image_bounds['center_y']
        
        # 現在の位置から中央からの相対位置を計算
        rel_x1 = x1 - center_x
        rel_y1 = y1 - center_y
        rel_x2 = x2 - center_x
        rel_y2 = y2 - center_y
        
        # 相対位置を保存
        self.rect_relative_pos = {
            'x1': rel_x1 / self.scale,
            'y1': rel_y1 / self.scale,
            'x2': rel_x2 / self.scale,
            'y2': rel_y2 / self.scale
        }
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="red",
            width=2
        )
        self.current_rect_coords = [x1, y1]
        self.rect_width = x2 - x1
        self.rect_height = y2 - y1
        
        # サイズ表示を更新
        self._update_size_labels()

    def _save_rect_info(self):
        """矩形情報の保存（中央からの相対位置で保存）"""
        if not self.rect_id:
            return None
        
        coords = self.canvas.coords(self.rect_id)
        center_x = self.image_bounds['center_x']
        center_y = self.image_bounds['center_y']
        
        # 中央からの相対位置を計算して保存
        return {
            'relative_pos': {
                'x1': (coords[0] - center_x) / self.scale,
                'y1': (coords[1] - center_y) / self.scale,
                'x2': (coords[2] - center_x) / self.scale,
                'y2': (coords[3] - center_y) / self.scale
            },
            'width': self.rect_width,
            'height': self.rect_height
        }

    def _restore_rect_from_info(self, rect_info):
        """矩形情報からの復元（中央からの相対位置を基に復元）"""
        if not rect_info:
            return

        center_x = self.image_bounds['center_x']
        center_y = self.image_bounds['center_y']
        rel_pos = rect_info['relative_pos']
        
        # 現在の中央位置と保存された相対位置から実際の座標を計算
        x1 = center_x + (rel_pos['x1'] * self.scale)
        y1 = center_y + (rel_pos['y1'] * self.scale)
        x2 = center_x + (rel_pos['x2'] * self.scale)
        y2 = center_y + (rel_pos['y2'] * self.scale)
        
        self._create_rect(x1, y1, x2, y2)
        
    def _update_size_labels(self):
        """サイズ表示の更新"""
        if self.pil_image:
            width, height = self.pil_image.size
            self.image_size_label.config(text=f"Image Size: {width} x {height}")
        
        if self.rect_id:
            # 矩形の実際のサイズを計算（スケールを考慮）
            rect_width = int(self.rect_width / self.scale)
            rect_height = int(self.rect_height / self.scale)
            self.rect_size_label.config(text=f"Selection Size: {rect_width} x {rect_height}")
        else:
            self.rect_size_label.config(text="Selection Size: -")
    
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    root.geometry("1050x1050")  # デフォルトサイズを1050x1050に
    root.minsize(1050, 1050)    # 最小サイズも1050x1050に
    app = ImageCropper(root)
    root.mainloop()