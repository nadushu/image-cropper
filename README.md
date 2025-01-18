# Image Cropper

画像を読み込んで任意の箇所をLora学習に適したサイズで切り取ることができるPythonアプリケーションです。

## Changelog
- v1.1.0 (2025-01-16)
  - 画像の自由回転を追加 (shift + 左クリック)
  - 画像の回転をリセット機能を追加
  - 画像を左右反転させる機能の追加
  - 指定した矩形枠のキーボードによる移動

- v1.0.0 (2025-01-16)
  - 初回リリース
  - 基本的な画像切り取り機能
  - ドラッグ&ドロップ対応

## 特徴

- ドラッグ&ドロップでの画像読み込み対応
- 対応しているサイズ（1:1(1024:1024), 1216:832, 832:1216）
- リサイズして保存機能(Lanczos3)*1
- マウスホイールでのズーム操作
- 画像の90度回転

*1 画像を拡大する際はリサイズせず、別途アップスケーラーを利用した拡大を推奨

## 必要要件

- Python 3.x
- tkinter
- PIL (Pillow)
- tkinterdnd2

## インストール方法

1. 必要なライブラリをインストール:
```bash
pip install pillow tkinterdnd2
```

2. プログラムを実行:
```bash
python image_cropper.py
```

## 使用方法

### 基本操作

1. 画像の読み込み:
   - 「Open」ボタンをクリック
   - または画像ファイルをウィンドウにドラッグ&ドロップ

2. 切り取り範囲の指定:
   - マウスでドラッグして範囲を指定
   - 既存の範囲をドラッグして移動可能
   - 右クリックドラッグで範囲のサイズを変更可能

3. 画像の保存:
   - 「Save」ボタンをクリック
   - または'S'キーを押下

### 特殊機能

#### 切り取りモード
- 「1:1」「1216:832」「832:1216」の3つのアスペクト比から選択可能
- 「Fixed Size」をオンにすると指定したモードの固定サイズでの切り取りが可能

#### ズーム操作
- マウスホイール: ズームイン/アウト
- Ctrl + マウスホイール: 垂直スクロール
- Shift + マウスホイール: 水平スクロール
- 'Z'キー: ズームイン
- 'X'キー: ズームアウト

#### その他の操作
- 'R'キー: 画像を90度回転
- 'A'キー: 画像を開く
- Alt + 'S': リサイズして保存

### 保存オプション
- 「Resize and Save」: 切り取った画像を選択中のモードに合わせたサイズで保存（
- 「Save Directory」: 保存先ディレクトリの指定

## ショートカットキー一覧

| キー | 機能 |
|------|------|
| S | 保存 |
| A | 画像を開く |
| F | 画像の左右反転 |
| R | 90度回転 |
| Z | ズームイン |
| X | ズームアウト |
| Alt + S | リサイズして保存 |


## 対応画像フォーマット

- PNG
- JPEG
- WebP
- BMP
- GIF
- TIFF