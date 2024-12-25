import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import cv2
from PIL import Image, ImageTk
import os
import subprocess
import threading
import re
import time

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox('insert')
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f'+{x}+{y}')

        label = ttk.Label(self.tooltip, text=self.text, 
                         justify=tk.LEFT,
                         background='#ffffe0', 
                         relief='solid', 
                         borderwidth=1)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class VideoConverter(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        
        # Initialize TkinterDnD
        try:
            self.TkdndVersion = self.tk.call('package', 'require', 'tkdnd')
        except:
            messagebox.showerror("Error", "TkinterDnD2 not properly installed. Drag and drop will not work.")

        self.title("Video Format Converter")
        self.geometry("600x600")
        
        # Define common presets
        self.presets = {
            'ultrafast': 'Fastest encoding, largest file size',
            'superfast': 'Very fast encoding, larger file size',
            'veryfast': 'Fast encoding, good file size',
            'faster': 'Fast encoding, better compression',
            'fast': 'Good balance of speed and compression',
            'medium': 'Default preset, good balance',
            'slow': 'Better compression, slower encoding',
            'slower': 'Very good compression, slower encoding',
            'veryslow': 'Best compression, slowest encoding'
        }

        # Define resolution presets
        self.resolution_presets = [
            'Original',
            '4K (3840x2160)',
            '2K (2560x1440)',
            'Full HD (1920x1080)',
            'HD (1280x720)',
            'SD (854x480)',
            'Low (640x360)'
        ]

        self.formats = {
            'MP4': {
                'extension': '.mp4',
                'presets': {
                    'Maximum Quality': {
                        'crf': 18,
                        'preset': 'slow',
                        'codec': 'libx264'
                    },
                    'High Quality': {
                        'crf': 23,
                        'preset': 'medium',
                        'codec': 'libx264'
                    },
                    'Balanced': {
                        'crf': 28,
                        'preset': 'fast',
                        'codec': 'libx264'
                    },
                    'Small Size': {
                        'crf': 32,
                        'preset': 'veryfast',
                        'codec': 'libx264'
                    }
                }
            },
            'MOV': {
                'extension': '.mov',
                'presets': {
                    'ProRes HQ': {
                        'codec': 'prores_ks',
                        'profile': 3
                    },
                    'ProRes Normal': {
                        'codec': 'prores_ks',
                        'profile': 2
                    },
                    'ProRes LT': {
                        'codec': 'prores_ks',
                        'profile': 1
                    },
                    'ProRes Proxy': {
                        'codec': 'prores_ks',
                        'profile': 0
                    }
                }
            },
            'MKV': {
                'extension': '.mkv',
                'presets': {
                    'Maximum Quality': {
                        'crf': 18,
                        'preset': 'slow',
                        'codec': 'libx264'
                    },
                    'High Quality': {
                        'crf': 23,
                        'preset': 'medium',
                        'codec': 'libx264'
                    },
                    'Balanced': {
                        'crf': 28,
                        'preset': 'fast',
                        'codec': 'libx264'
                    },
                    'Small Size': {
                        'crf': 32,
                        'preset': 'veryfast',
                        'codec': 'libx264'
                    }
                }
            },
            'WEBM': {
                'extension': '.webm',
                'presets': {
                    'Maximum Quality': {
                        'crf': 18,
                        'speed': 0,
                        'codec': 'libvpx-vp9'
                    },
                    'High Quality': {
                        'crf': 30,
                        'speed': 1,
                        'codec': 'libvpx-vp9'
                    },
                    'Balanced': {
                        'crf': 35,
                        'speed': 2,
                        'codec': 'libvpx-vp9'
                    },
                    'Small Size': {
                        'crf': 40,
                        'speed': 4,
                        'codec': 'libvpx-vp9'
                    }
                }
            }
        }

        self.current_video = None
        self.setup_ui()
        self.setup_drop_target()

    def setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        center_container = ttk.Frame(main_frame)
        center_container.pack(expand=True, fill=tk.BOTH)
        
        ttk.Frame(center_container).pack(expand=True)

        controls_frame = ttk.Frame(center_container)
        controls_frame.pack(fill=tk.X, pady=(0, 20))

        # Format selection
        format_frame = ttk.LabelFrame(controls_frame, text="Output Format")
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.format_var = tk.StringVar()
        self.format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, 
                                       values=list(self.formats.keys()), state='readonly')
        self.format_combo.pack(padx=10, pady=5, fill=tk.X)
        self.format_combo.bind('<<ComboboxSelected>>', self.update_quality_options)
        ToolTip(self.format_combo, "Select the output video format")

        # Quality Preset selection
        preset_frame = ttk.LabelFrame(controls_frame, text="Quality Preset")
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.quality_preset_var = tk.StringVar()
        self.quality_preset_combo = ttk.Combobox(preset_frame, textvariable=self.quality_preset_var, state='readonly')
        self.quality_preset_combo.pack(padx=10, pady=5, fill=tk.X)
        self.quality_preset_combo.bind('<<ComboboxSelected>>', self.update_advanced_options)
        ToolTip(self.quality_preset_combo, "Select a predefined quality preset")

        # Advanced Options
        advanced_frame = ttk.LabelFrame(controls_frame, text="Advanced Options")
        advanced_frame.pack(fill=tk.X, pady=(0, 10))

        # Resolution
        resolution_frame = ttk.Frame(advanced_frame)
        resolution_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(resolution_frame, text="Resolution:").pack(side=tk.LEFT)
        self.resolution_var = tk.StringVar(value='Original')
        self.resolution_combo = ttk.Combobox(resolution_frame, textvariable=self.resolution_var,
                                           values=self.resolution_presets, state='readonly')
        self.resolution_combo.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        ToolTip(self.resolution_combo, "Select output resolution. Original maintains source resolution")

        # CRF (for formats that support it)
        crf_frame = ttk.Frame(advanced_frame)
        crf_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(crf_frame, text="CRF Value:").pack(side=tk.LEFT)
        self.crf_var = tk.StringVar(value='23')
        self.crf_spinbox = ttk.Spinbox(crf_frame, from_=0, to=51, textvariable=self.crf_var, width=5)
        self.crf_spinbox.pack(side=tk.LEFT, padx=(10, 0))
        ToolTip(self.crf_spinbox, "Constant Rate Factor (0-51). Lower values mean better quality but larger files")

        # Encoding Preset
        encode_preset_frame = ttk.Frame(advanced_frame)
        encode_preset_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(encode_preset_frame, text="Encoding Preset:").pack(side=tk.LEFT)
        self.encode_preset_var = tk.StringVar(value='medium')
        self.encode_preset_combo = ttk.Combobox(encode_preset_frame, textvariable=self.encode_preset_var,
                                              values=list(self.presets.keys()), state='readonly')
        self.encode_preset_combo.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        ToolTip(self.encode_preset_combo, "Encoding preset affects compression speed vs quality")

        # Convert button
        self.convert_btn = ttk.Button(controls_frame, text="Convert", command=self.convert_video)
        self.convert_btn.pack(fill=tk.X, pady=(0, 10))

        # Progress bar and label
        self.progress = ttk.Progressbar(controls_frame, mode='determinate', maximum=100)
        self.progress.pack(fill=tk.X)
        self.progress_label = ttk.Label(controls_frame, text="")
        self.progress_label.pack(fill=tk.X, pady=(5, 0))

        # Preview frame
        preview_container = ttk.Frame(center_container)
        preview_container.pack(fill=tk.X, pady=(0, 20))
        
        self.filename_label = ttk.Label(preview_container, text="Drop video file here or click to select")
        self.filename_label.pack(anchor=tk.CENTER, pady=(0, 10))
        
        self.preview_frame = ttk.Frame(preview_container, style='Preview.TFrame', height=180)
        self.preview_frame.pack(fill=tk.X)
        self.preview_frame.pack_propagate(False)
        
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        self.preview_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.preview_label.bind('<Button-1>', lambda e: self.select_file())

        # Set initial format
        self.format_combo.set('MP4')
        self.update_quality_options()

    def update_quality_options(self, event=None):
        selected_format = self.format_var.get()
        quality_presets = list(self.formats[selected_format]['presets'].keys())
        self.quality_preset_combo['values'] = quality_presets
        self.quality_preset_combo.set(quality_presets[0])
        self.update_advanced_options()

    def update_advanced_options(self, event=None):
        selected_format = self.format_var.get()
        selected_preset = self.quality_preset_var.get()
        
        preset_options = self.formats[selected_format]['presets'][selected_preset]
        
        # Update CRF if applicable
        if 'crf' in preset_options:
            self.crf_var.set(str(preset_options['crf']))
            self.crf_spinbox.state(['!disabled'])
        else:
            self.crf_spinbox.state(['disabled'])
        
        # Update encoding preset if applicable
        if 'preset' in preset_options:
            self.encode_preset_var.set(preset_options['preset'])
            self.encode_preset_combo.state(['!disabled'])
        else:
            self.encode_preset_combo.state(['disabled'])

    def get_conversion_parameters(self):
        selected_format = self.format_var.get()
        selected_preset = self.quality_preset_var.get()
        preset_options = self.formats[selected_format]['presets'][selected_preset]
        
        params = []
        
        # Add codec
        if 'codec' in preset_options:
            params.extend(['-c:v', preset_options['codec']])
        
        # Add resolution if not original
        if self.resolution_var.get() != 'Original':
            resolution = self.resolution_var.get()
            width = resolution.split('(')[1].split('x')[0]
            params.extend(['-vf', f'scale={width}:-2'])
        
        # Add format-specific parameters
        if selected_format in ['MP4', 'MKV']:
            if not self.crf_spinbox.instate(['disabled']):
                params.extend(['-crf', self.crf_var.get()])
            if not self.encode_preset_combo.instate(['disabled']):
                params.extend(['-preset', self.encode_preset_var.get()])
        elif selected_format == 'MOV':
            if 'profile' in preset_options:
                params.extend(['-profile:v', str(preset_options['profile'])])
        elif selected_format == 'WEBM':
            if 'speed' in preset_options:
                params.extend(['-speed', str(preset_options['speed'])])
            if 'crf' in preset_options:
                params.extend(['-crf', str(preset_options['crf']), '-b:v', '0'])
        
        # Always copy audio codec
        params.extend(['-c:a', 'copy'])
        
        return params

    def convert_video(self):
        if not self.current_video:
            messagebox.showerror("Error", "No video selected")
            return

        output_file = filedialog.asksaveasfilename(
            defaultextension=self.formats[self.format_var.get()]['extension'],
            filetypes=[(f"{self.format_var.get()} file", 
                       f"*{self.formats[self.format_var.get()]['extension']}")]
        )
        
        if not output_file:
            return

        # Get video duration
        duration = self.get_video_duration(self.current_video)
        if duration == 0:
            messagebox.showerror("Error", "Could not determine video duration")
            return

        # Reset progress
        self.progress['value'] = 0
        self.progress_label.config(text="Starting conversion...")

        # Get conversion parameters
        conversion_params = self.get_conversion_parameters()

        # Prepare FFMPEG command
        command = [
            'ffmpeg', 
            '-i', self.current_video,
            *conversion_params,
            '-y',  # Overwrite output file if it exists
            output_file
        ]

        # Start conversion in a separate thread
        self.convert_btn.state(['disabled'])
        threading.Thread(target=self.run_conversion, 
                        args=(command, output_file, duration)).start()

    def run_conversion(self, command, output_file, duration):
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                errors='replace'
            )

            # Pattern to match time progress in FFmpeg output
            time_pattern = re.compile(r'time=(\d{2}):(\d{2}):(\d{2})\.\d+')
            
            while True:
                line = process.stderr.readline()
                
                if not line and process.poll() is not None:
                    break
                    
                time_match = time_pattern.search(line)
                if time_match:
                    hours, minutes, seconds = map(int, time_match.groups())
                    current_time = hours * 3600 + minutes * 60 + seconds
                    self.after(0, self.update_progress, current_time, duration)

            return_code = process.poll()
            self.after(0, self.conversion_complete, return_code, output_file)
            
        except Exception as e:
            self.after(0, self.conversion_error, str(e))
            
        finally:
            try:
                process.stderr.close()
                process.stdout.close()
            except:
                pass

    def conversion_complete(self, return_code, output_file):
        self.progress['value'] = 100
        self.progress_label.config(text="Conversion complete!")
        self.convert_btn.state(['!disabled'])
        
        if return_code == 0:
            messagebox.showinfo("Success", 
                              f"Video converted successfully!\nSaved to: {output_file}")
        else:
            messagebox.showerror("Error", 
                               "Conversion failed. Please check if FFMPEG is installed.")

    def conversion_error(self, error_message):
        self.progress['value'] = 0
        self.progress_label.config(text="Conversion failed!")
        self.convert_btn.state(['!disabled'])
        messagebox.showerror("Error", f"Conversion failed: {error_message}")

    def setup_drop_target(self):
        """Setup drag and drop functionality for the preview frame."""
        self.preview_frame.drop_target_register(DND_FILES)
        self.preview_frame.dnd_bind('<<Drop>>', self.handle_drop)
        self.preview_label.drop_target_register(DND_FILES)
        self.preview_label.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        """Handle dropped files."""
        file_path = event.data
        # Handle multiple path formats
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        if file_path.startswith('"') and file_path.endswith('"'):
            file_path = file_path[1:-1]
        # Check file extension
        if any(file_path.lower().endswith(ext) for ext in 
               ('.mp4', '.mov', '.avi', '.mkv', '.webm')):
            self.load_video(file_path)
        else:
            messagebox.showerror("Error", "Unsupported file format")

    def select_file(self):
        """Open file dialog to select a video file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Video files", 
                       "*.mp4 *.mov *.avi *.mkv *.webm")]
        )
        if file_path:
            self.load_video(file_path)

    def load_video(self, file_path):
        """Load a video file and update the UI."""
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "File does not exist")
            return

        self.current_video = file_path
        # Update filename label with just the filename, not the full path
        self.filename_label.config(text=os.path.basename(file_path))
        self.update_thumbnail()

    def update_thumbnail(self):
        """Generate and display a thumbnail from the video."""
        cap = cv2.VideoCapture(self.current_video)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open video file")
            cap.release()
            return

        # Read the first frame
        ret, frame = cap.read()
        cap.release()

        if not ret:
            messagebox.showerror("Error", "Could not read video frame")
            return

        # Get preview frame dimensions
        frame_width = self.preview_frame.winfo_width()
        frame_height = self.preview_frame.winfo_height()

        # Calculate resize dimensions while maintaining aspect ratio
        aspect_ratio = frame.shape[1] / frame.shape[0]
        preview_height = 180  # Fixed preview height
        target_width = int(preview_height * aspect_ratio)

        # Resize and convert frame
        frame = cv2.resize(frame, (target_width, preview_height))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create and display thumbnail
        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=image)
        
        self.preview_label.configure(image=photo)
        self.preview_label.image = photo  # Keep a reference to prevent garbage collection

    def update_progress(self, current_time, duration):
        """Update progress bar and label."""
        if duration > 0:
            progress = (current_time / duration) * 100
            self.progress['value'] = progress
            time_remaining = duration - current_time
            
            current_formatted = time.strftime('%H:%M:%S', time.gmtime(current_time))
            total_formatted = time.strftime('%H:%M:%S', time.gmtime(duration))
            remaining_formatted = time.strftime('%H:%M:%S', time.gmtime(time_remaining))
            
            self.progress_label.config(
                text=f"{current_formatted} / {total_formatted} (ETA: {remaining_formatted})"
            )

    def get_video_duration(self, filename):
        """Get video duration using ffmpeg."""
        cmd = ['ffmpeg', '-i', filename]
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            
            duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", output)
            if duration_match:
                hours, minutes, seconds, centis = map(int, duration_match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds + centis / 100
                return total_seconds
        except subprocess.CalledProcessError as e:
            output = e.output
            duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", output)
            if duration_match:
                hours, minutes, seconds, centis = map(int, duration_match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds + centis / 100
                return total_seconds
        return 0

if __name__ == "__main__":
    app = VideoConverter()
    app.mainloop()