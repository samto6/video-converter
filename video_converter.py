import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import cv2
from PIL import Image, ImageTk
import os
import subprocess
import threading
from pathlib import Path
import tempfile
import re
import time

class VideoConverter(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title("Video Format Converter")
        self.geometry("500x400")
        
        self.formats = {
            'MP4': {
                'extension': '.mp4',
                'quality_options': {
                    'High (H.264)': '-c:v libx264 -crf 18',
                    'Medium (H.264)': '-c:v libx264 -crf 23',
                    'Low (H.264)': '-c:v libx264 -crf 28',
                    'High (H.265)': '-c:v libx265 -crf 18',
                    'Medium (H.265)': '-c:v libx265 -crf 23',
                    'Low (H.265)': '-c:v libx265 -crf 28'
                }
            },
            'MOV': {
                'extension': '.mov',
                'quality_options': {
                    'High (ProRes)': '-c:v prores_ks -profile:v 3',
                    'Medium (ProRes)': '-c:v prores_ks -profile:v 2',
                    'Low (ProRes)': '-c:v prores_ks -profile:v 0'
                }
            },
            'AVI': {
                'extension': '.avi',
                'quality_options': {
                    'High': '-c:v mpeg4 -q:v 2',
                    'Medium': '-c:v mpeg4 -q:v 5',
                    'Low': '-c:v mpeg4 -q:v 8'
                }
            },
            'MKV': {
                'extension': '.mkv',
                'quality_options': {
                    'High (H.264)': '-c:v libx264 -crf 18',
                    'Medium (H.264)': '-c:v libx264 -crf 23',
                    'Low (H.264)': '-c:v libx264 -crf 28'
                }
            },
            'WEBM': {
                'extension': '.webm',
                'quality_options': {
                    'High': '-c:v libvpx-vp9 -crf 18 -b:v 0',
                    'Medium': '-c:v libvpx-vp9 -crf 30 -b:v 0',
                    'Low': '-c:v libvpx-vp9 -crf 40 -b:v 0'
                }
            }
        }

        self.current_video = None
        
        self.setup_ui()
        self.setup_drop_target()

    def get_video_duration(self, filename):
        """Get video duration using ffmpeg."""
        cmd = ['ffmpeg', '-i', filename]
        try:
            # FFmpeg writes to stderr for duration info
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            
            # Find duration in output
            duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", output)
            if duration_match:
                hours, minutes, seconds, centis = map(int, duration_match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds + centis / 100
                return total_seconds
        except subprocess.CalledProcessError as e:
            # FFmpeg returns 1 when getting info, which raises this error, but we still get the output
            output = e.output
            duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", output)
            if duration_match:
                hours, minutes, seconds, centis = map(int, duration_match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds + centis / 100
                return total_seconds
        return 0

    def parse_time(self, time_str):
        """Convert FFmpeg time string to seconds."""
        time_parts = time_str.split(':')
        if len(time_parts) == 3:
            hours, minutes, seconds = time_parts
            seconds = float(seconds)
            return int(hours) * 3600 + int(minutes) * 60 + seconds
        return 0

    def update_progress(self, current_time, duration):
        """Update progress bar and label."""
        if duration > 0:
            progress = (current_time / duration) * 100
            self.progress['value'] = progress
            time_remaining = duration - current_time
            
            # Format times as HH:MM:SS
            current_formatted = time.strftime('%H:%M:%S', time.gmtime(current_time))
            total_formatted = time.strftime('%H:%M:%S', time.gmtime(duration))
            remaining_formatted = time.strftime('%H:%M:%S', time.gmtime(time_remaining))
            
            self.progress_label.config(
                text=f"{current_formatted} / {total_formatted} (ETA: {remaining_formatted})"
            )

    def setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Center container for all content
        center_container = ttk.Frame(main_frame)
        center_container.pack(expand=True, fill=tk.BOTH)
        
        # Push content down with empty frame
        ttk.Frame(center_container).pack(expand=True)

        controls_frame = ttk.Frame(center_container)
        controls_frame.pack(fill=tk.X, pady=(0, 20))

        # Format selection
        format_frame = ttk.Frame(controls_frame)
        format_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar()
        self.format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, 
                                       values=list(self.formats.keys()), state='readonly')
        self.format_combo.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        self.format_combo.bind('<<ComboboxSelected>>', self.update_quality_options)

        # Quality selection
        quality_frame = ttk.Frame(controls_frame)
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(quality_frame, text="Quality:").pack(side=tk.LEFT)
        self.quality_var = tk.StringVar()
        self.quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var, state='readonly')
        self.quality_combo.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)

        # Convert button
        self.convert_btn = ttk.Button(controls_frame, text="Convert", command=self.convert_video)
        self.convert_btn.pack(fill=tk.X, pady=(0, 10))

        # Progress bar and label
        self.progress = ttk.Progressbar(controls_frame, mode='determinate', maximum=100)
        self.progress.pack(fill=tk.X)
        self.progress_label = ttk.Label(controls_frame, text="")
        self.progress_label.pack(fill=tk.X, pady=(5, 0))

        # Preview frame at the bottom
        preview_container = ttk.Frame(center_container)
        preview_container.pack(fill=tk.X, pady=(0, 20))
        
        self.filename_label = ttk.Label(preview_container, text="Drop video file here or click to select")
        self.filename_label.pack(anchor=tk.CENTER, pady=(0, 10))
        
        self.preview_frame = ttk.Frame(preview_container, style='Preview.TFrame', height=180)
        self.preview_frame.pack(fill=tk.X)
        self.preview_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        self.preview_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.preview_label.bind('<Button-1>', lambda e: self.select_file())
        
        # Push content up with empty frame
        ttk.Frame(center_container).pack(expand=True)

        # Set initial format
        self.format_combo.set('MP4')
        self.update_quality_options()

    def setup_drop_target(self):
        self.preview_frame.drop_target_register(DND_FILES)
        self.preview_frame.dnd_bind('<<Drop>>', self.handle_drop)
        self.preview_label.drop_target_register(DND_FILES)
        self.preview_label.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
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
        file_path = filedialog.askopenfilename(
            filetypes=[("Video files", 
                       "*.mp4 *.mov *.avi *.mkv *.webm")]
        )
        if file_path:
            self.load_video(file_path)

    def load_video(self, file_path):
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "File does not exist")
            return

        self.current_video = file_path
        # Update filename label with just the filename, not the full path
        self.filename_label.config(text=os.path.basename(file_path))
        self.update_thumbnail()

    def update_thumbnail(self):
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

    def update_quality_options(self, event=None):
        selected_format = self.format_var.get()
        quality_options = list(self.formats[selected_format]['quality_options'].keys())
        self.quality_combo['values'] = quality_options
        self.quality_combo.set(quality_options[0])

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

        # Get FFMPEG parameters
        format_settings = self.formats[self.format_var.get()]
        quality_settings = format_settings['quality_options'][self.quality_var.get()]

        # Reset progress
        self.progress['value'] = 0
        self.progress_label.config(text="Starting conversion...")

        # Prepare FFMPEG command
        command = [
            'ffmpeg', 
            '-i', self.current_video,
            *quality_settings.split(),
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
                # Read from stderr as FFmpeg outputs progress there
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

if __name__ == "__main__":
    app = VideoConverter()
    app.mainloop()