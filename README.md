# Video Format Converter

A simple, user-friendly desktop application for converting video files between different formats. Built with Python and Tkinter.

![video_converter](https://github.com/user-attachments/assets/ad61dbbe-18a7-4ae4-9086-4e3f64467376)

## Features

- Drag-and-drop interface for easy file selection
- Support for popular video formats:
  - MP4
  - MOV (with ProRes support)
  - MKV
  - AVI
  - WEBM
- Multiple quality presets for each format
- Advanced options for fine-tuning:
  - Resolution selection
  - CRF (Constant Rate Factor) adjustment
  - Encoding speed presets
- Real-time conversion progress tracking
- Video thumbnail preview
- Tooltips for better understanding of options

## Installation

### Pre-built Executables

See the [Releases](../../releases) page to download the latest version.

### Requirements for Running from Source

If you prefer to run from source, you'll need:
- Python 3.7+
- FFmpeg (must be installed and accessible in system PATH)
- Required Python packages:
  ```bash
  pip install tkinterdnd2 pillow
  ```

### Running from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/video-format-converter.git
   cd video-format-converter
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python video_converter.py
   ```

## Usage

1. Launch the application
2. Either drag and drop a video file onto the window or click to select a file
3. Choose your desired output format
4. Select a quality preset
5. Adjust advanced options if needed
6. Click "Convert" and choose where to save the output file
7. Wait for the conversion to complete

## Quality Presets

### MP4/MKV/AVI
- Maximum Quality: Best quality, larger file size
- High Quality: Good quality, balanced file size
- Balanced: Decent quality, smaller file size
- Small Size: Reduced quality, minimal file size

### MOV (ProRes)
- ProRes HQ: High-quality professional codec
- ProRes Normal: Standard professional quality
- ProRes LT: Lightweight professional quality
- ProRes Proxy: Preview quality

### WEBM
- Maximum Quality: Best VP9 encoding
- High Quality: Good quality web video
- Balanced: Standard web video quality
- Small Size: Compressed web video

## Building from Source

### Windows
```bash
pyinstaller --windowed --onefile video_converter.py
```

### macOS
```bash
pyinstaller --windowed --onefile --icon=icon.icns video_converter.py
```

### Linux
```bash
pyinstaller --windowed --onefile video_converter.py
```

## Dependencies

- tkinter/tkinterdnd2: GUI framework
- PIL (Pillow): Image processing
- FFmpeg: Video processing (external dependency)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
