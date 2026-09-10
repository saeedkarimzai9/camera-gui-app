import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
from PIL import Image, ImageTk
import threading
import time
import numpy as np
import json
import os
import pygame
from pydub import AudioSegment
from pydub.playback import play
import pyttsx3
from collections import defaultdict

try:
    import pyvirtualcam
    VIRTUAL_CAM_AVAILABLE = True
except ImportError:
    VIRTUAL_CAM_AVAILABLE = False

# Initialize audio
pygame.mixer.init()
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)

class SoundboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📷🎙️ Camera PRO + Soundboard - Ultimate Suite")
        self.root.geometry("1600x1000")
        self.root.configure(bg="#1a1a1a")
        
        # Audio variables
        self.sounds = {}
        self.current_playing = None
        self.hotkey_map = {}
        self.sound_files = {}
        self.sounds_file = "soundboard_presets.json"
        
        # Camera variables
        self.cap = None
        self.vcam = None
        self.running = False
        self.virtual_cam_active = False
        self.selected_camera = 0
        self.camera_name = "Camera 0"
        self.testing_camera = False
        
        self.VCAM_WIDTH = 640
        self.VCAM_HEIGHT = 480
        self.DISPLAY_WIDTH = 720
        self.DISPLAY_HEIGHT = 540
        
        # Effects settings
        self.effects = {
            "brightness": 0,
            "contrast": 1.0,
            "saturation": 1.0,
            "effect": "none",
            "opacity": 1.0,
            "effect_intensity": 1.0
        }
        
        self.presets = {
            "Gaming": {"brightness": 10, "contrast": 1.3, "saturation": 1.2, "effect": "none", "opacity": 1.0, "effect_intensity": 1.0},
            "Stream": {"brightness": 5, "contrast": 1.1, "saturation": 1.1, "effect": "blur", "opacity": 0.8, "effect_intensity": 0.5},
            "Professional": {"brightness": 0, "contrast": 1.0, "saturation": 0.9, "effect": "none", "opacity": 1.0, "effect_intensity": 1.0}
        }
        
        self.load_soundboard()
        
        # Bind hotkeys
        self.root.bind("<KeyPress>", self.on_key_press)
        
        # Title
        title_label = tk.Label(root, text="📷🎙️ Camera PRO + Soundboard - The Ultimate Suite", 
                              font=("Arial", 20, "bold"), bg="#1a1a1a", fg="#00ff00")
        title_label.pack(pady=10)
        
        # Status bar
        status_frame = tk.Frame(root, bg="#2a2a2a", height=40)
        status_frame.pack(fill=tk.X, padx=0, pady=0)
        
        self.vcam_status = tk.Label(status_frame, text="🔴 Virtual Cam: INACTIVE", 
                                   font=("Arial", 10, "bold"), bg="#2a2a2a", fg="red")
        self.vcam_status.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.now_playing_label = tk.Label(status_frame, text="🔊 Now Playing: None", 
                                         font=("Arial", 10, "bold"), bg="#2a2a2a", fg="#ffff00")
        self.now_playing_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Main container
        main_container = tk.Frame(root, bg="#1a1a1a")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # LEFT SIDE - CAMERA
        left_frame = tk.Frame(main_container, bg="#1a1a1a")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Camera selection
        camera_frame = tk.LabelFrame(left_frame, text="📷 Camera Control", font=("Arial", 11, "bold"), 
                                    bg="#2a2a2a", fg="#00ff00", padx=10, pady=10)
        camera_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(camera_frame, text="Camera:", font=("Arial", 10), bg="#2a2a2a", fg="#fff").pack(side=tk.LEFT, padx=5)
        
        self.available_cameras = self.find_cameras()
        self.manual_camera_var = tk.StringVar(value="Camera 0")
        manual_options = [f"Camera {i}" for i in range(10)]
        self.manual_dropdown = ttk.Combobox(camera_frame, textvariable=self.manual_camera_var, 
                                           values=manual_options, state="readonly", width=12)
        self.manual_dropdown.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = tk.Button(camera_frame, text="▶ Start", command=self.start_camera, 
                                   bg="#00aa00", fg="white", font=("Arial", 10, "bold"), width=8)
        self.start_btn.pack(side=tk.LEFT, padx=3)
        
        self.stop_btn = tk.Button(camera_frame, text="⏹ Stop", command=self.stop_camera, 
                                  bg="#aa0000", fg="white", font=("Arial", 10, "bold"), width=8, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=3)
        
        self.led_indicator = tk.Label(camera_frame, text="⚫", font=("Arial", 16), bg="#2a2a2a", fg="gray")
        self.led_indicator.pack(side=tk.LEFT, padx=10)
        
        # Video display
        video_label_text = tk.Label(left_frame, text="📺 Live Preview", font=("Arial", 12, "bold"), bg="#1a1a1a", fg="#00ff00")
        video_label_text.pack()
        
        self.video_label = tk.Label(left_frame, bg="black", width=self.DISPLAY_WIDTH, height=self.DISPLAY_HEIGHT, 
                                   relief=tk.SUNKEN, bd=2)
        self.video_label.pack(pady=10)
        
        self.camera_name_display = tk.Label(self.video_label, text="", font=("Arial", 12, "bold"), 
                                           bg="black", fg="lime", anchor="nw")
        self.camera_name_display.place(x=15, y=15)
        
        # Effects section
        effects_frame = tk.LabelFrame(left_frame, text="🎨 Effects & Display", font=("Arial", 11, "bold"), 
                                     bg="#2a2a2a", fg="#00ff00", padx=10, pady=10)
        effects_frame.pack(fill=tk.X, pady=5)
        
        # Presets
        tk.Label(effects_frame, text="Presets:", font=("Arial", 10), bg="#2a2a2a", fg="#fff").pack(anchor=tk.W)
        preset_btn_frame = tk.Frame(effects_frame, bg="#2a2a2a")
        preset_btn_frame.pack(fill=tk.X, pady=5)
        
        for preset_name in self.presets.keys():
            btn = tk.Button(preset_btn_frame, text=preset_name, command=lambda p=preset_name: self.load_preset(p),
                           bg="#6600cc", fg="white", font=("Arial", 9, "bold"), width=12)
            btn.pack(side=tk.LEFT, padx=3)
        
        # Brightness
        tk.Label(effects_frame, text="Brightness:", font=("Arial", 9), bg="#2a2a2a", fg="#fff").pack(anchor=tk.W)
        self.brightness_var = tk.IntVar(value=0)
        tk.Scale(effects_frame, from_=-100, to=100, orient=tk.HORIZONTAL, 
                variable=self.brightness_var, bg="#333", fg="#00ff00", command=self.update_effects).pack(fill=tk.X)
        
        # Virtual Camera button
        self.vcam_btn = tk.Button(effects_frame, text="🌐 Enable Virtual Camera", 
                                 command=self.toggle_virtual_camera, 
                                 bg="#9933ff", fg="white", font=("Arial", 10, "bold"), width=30, state=tk.DISABLED)
        self.vcam_btn.pack(pady=5)
        
        # RIGHT SIDE - SOUNDBOARD
        right_frame = tk.Frame(main_container, bg="#1a1a1a")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Soundboard controls
        soundboard_control_frame = tk.LabelFrame(right_frame, text="🎙️ Soundboard Controls", font=("Arial", 11, "bold"), 
                                                bg="#2a2a2a", fg="#00ff00", padx=10, pady=10)
        soundboard_control_frame.pack(fill=tk.X, pady=5)
        
        # Volume control
        tk.Label(soundboard_control_frame, text="Volume:", font=("Arial", 10), bg="#2a2a2a", fg="#fff").pack(anchor=tk.W)
        self.volume_var = tk.IntVar(value=80)
        volume_scale = tk.Scale(soundboard_control_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                               variable=self.volume_var, bg="#333", fg="#00ff00", command=self.set_volume)
        volume_scale.pack(fill=tk.X, pady=5)
        
        # Add sound buttons
        add_frame = tk.Frame(soundboard_control_frame, bg="#2a2a2a")
        add_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(add_frame, text="📁 Add Sound File", command=self.add_sound_file,
                 bg="#0099cc", fg="white", font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT, padx=3)
        
        tk.Button(add_frame, text="🎤 Text to Speech", command=self.add_tts_sound,
                 bg="#cc6600", fg="white", font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT, padx=3)
        
        # Clear all button
        tk.Button(soundboard_control_frame, text="🗑️ Clear All Sounds", command=self.clear_all_sounds,
                 bg="#ff3300", fg="white", font=("Arial", 10, "bold"), width=30).pack(pady=5)
        
        # Soundboard grid
        soundboard_frame = tk.LabelFrame(right_frame, text="🎵 Sound Library (Hotkeys: 1-9, A-Z)", 
                                        font=("Arial", 11, "bold"), bg="#2a2a2a", fg="#00ff00", padx=10, pady=10)
        soundboard_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollable sound buttons
        canvas_frame = tk.Frame(soundboard_frame, bg="#2a2a2a")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.sound_canvas = tk.Canvas(canvas_frame, bg="#2a2a2a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.sound_canvas.yview)
        self.sound_scrollable_frame = tk.Frame(self.sound_canvas, bg="#2a2a2a")
        
        self.sound_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.sound_canvas.configure(scrollregion=self.sound_canvas.bbox("all"))
        )
        
        self.sound_canvas.create_window((0, 0), window=self.sound_scrollable_frame, anchor="nw")
        self.sound_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.sound_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status_label = tk.Label(root, text="Status: Ready to rock! 🎉", font=("Arial", 10), bg="#2a2a2a", fg="#ffff00")
        self.status_label.pack(pady=5, fill=tk.X)
        
        self.refresh_sound_buttons()
    
    def find_cameras(self):
        """Find available cameras"""
        available = []
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, _ = cap.read()
                    cap.release()
                    if ret:
                        available.append(i)
            except:
                pass
        return available
    
    def start_camera(self):
        """Start camera"""
        if not self.running:
            camera_num = int(self.manual_camera_var.get().split()[-1])
            
            try:
                self.cap = cv2.VideoCapture(camera_num)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                ret, _ = self.cap.read()
                if not ret:
                    raise Exception("Camera failed")
                
                self.running = True
                self.selected_camera = camera_num
                self.camera_name = f"Camera {camera_num}"
                
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
                self.vcam_btn.config(state=tk.NORMAL)
                self.led_indicator.config(fg="lime")
                self.status_label.config(text=f"✓ Camera {camera_num} Running", fg="#00ff00")
                
                self.update_frame()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start camera:\n{str(e)}")
                self.running = False
    
    def stop_camera(self):
        """Stop camera"""
        self.running = False
        self.stop_virtual_camera()
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.vcam_btn.config(state=tk.DISABLED)
        self.led_indicator.config(fg="gray")
        self.video_label.config(image="")
        self.camera_name_display.config(text="")
        self.status_label.config(text="Camera Stopped", fg="#ff3300")
    
    def toggle_virtual_camera(self):
        """Toggle virtual camera"""
        if not VIRTUAL_CAM_AVAILABLE:
            messagebox.showerror("Error", "pyvirtualcam not installed!")
            return
        
        if self.virtual_cam_active:
            self.stop_virtual_camera()
        else:
            self.start_virtual_camera()
    
    def start_virtual_camera(self):
        """Start virtual camera"""
        try:
            import pyvirtualcam
            self.vcam = pyvirtualcam.Camera(width=self.VCAM_WIDTH, height=self.VCAM_HEIGHT, fps=30)
            self.virtual_cam_active = True
            self.vcam_btn.config(text="🌐 Disable Virtual Camera", bg="#00aa00")
            self.vcam_status.config(text="🟢 Virtual Cam: ACTIVE")
            self.status_label.config(text="Virtual Camera ACTIVE - Stream to OBS/Discord!", fg="#00ff00")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start virtual camera:\n{str(e)}")
    
    def stop_virtual_camera(self):
        """Stop virtual camera"""
        try:
            if self.vcam:
                self.vcam.close()
                self.vcam = None
            self.virtual_cam_active = False
            self.vcam_btn.config(text="🌐 Enable Virtual Camera", bg="#9933ff")
            self.vcam_status.config(text="🔴 Virtual Cam: INACTIVE")
        except:
            pass
    
    def update_effects(self, *args):
        """Update effects"""
        self.effects["brightness"] = self.brightness_var.get()
    
    def load_preset(self, preset_name):
        """Load preset"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            self.brightness_var.set(preset["brightness"])
            self.update_effects()
            self.status_label.config(text=f"Preset: {preset_name} ✓", fg="#00ff00")
    
    def apply_effects(self, frame):
        """Apply effects to frame"""
        brightness = self.effects["brightness"]
        if brightness != 0:
            frame = cv2.convertScaleAbs(frame, alpha=1.0, beta=brightness)
        return frame
    
    def resize_frame(self, frame, width, height):
        """Resize frame"""
        h, w = frame.shape[:2]
        aspect = w / h
        
        if aspect > (width / height):
            new_w = width
            new_h = int(width / aspect)
        else:
            new_h = height
            new_w = int(height * aspect)
        
        frame = cv2.resize(frame, (new_w, new_h))
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        y_offset = (height - new_h) // 2
        x_offset = (width - new_w) // 2
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = frame
        
        return canvas
    
    def update_frame(self):
        """Update frame loop"""
        if self.running and self.cap:
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    frame = self.apply_effects(frame)
                    
                    if self.virtual_cam_active and self.vcam:
                        try:
                            vcam_frame = self.resize_frame(frame, self.VCAM_WIDTH, self.VCAM_HEIGHT)
                            frame_rgb = cv2.cvtColor(vcam_frame, cv2.COLOR_BGR2RGB)
                            self.vcam.send(frame_rgb)
                        except:
                            pass
                    
                    display_frame = self.resize_frame(frame, self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)
                    cv2image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(cv2image)
                    imgtk = ImageTk.PhotoImage(image=img)
                    
                    self.video_label.imgtk = imgtk
                    self.video_label.config(image=imgtk)
                    
                    vcam_text = " 🌐" if self.virtual_cam_active else ""
                    self.camera_name_display.config(text=f"📷 {self.camera_name}{vcam_text}")
                else:
                    self.running = False
                    self.stop_camera()
                    return
            except Exception as e:
                print(f"Frame error: {e}")
                self.running = False
                self.stop_camera()
                return
            
            self.root.after(30, self.update_frame)
    
    def add_sound_file(self):
        """Add custom sound file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")]
        )
        
        if file_path:
            sound_name = os.path.basename(file_path).split('.')[0]
            self.sound_files[sound_name] = file_path
            self.sounds[sound_name] = file_path
            self.save_soundboard()
            self.refresh_sound_buttons()
            self.status_label.config(text=f"Added: {sound_name}", fg="#00ff00")
    
    def add_tts_sound(self):
        """Add text-to-speech sound"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Text to Speech")
        dialog.geometry("400x150")
        dialog.configure(bg="#2a2a2a")
        
        tk.Label(dialog, text="Sound Name:", bg="#2a2a2a", fg="#fff").pack(padx=10, pady=5)
        name_entry = tk.Entry(dialog, bg="#333", fg="#fff", font=("Arial", 10), width=40)
        name_entry.pack(padx=10, pady=5)
        
        tk.Label(dialog, text="Text to Speak:", bg="#2a2a2a", fg="#fff").pack(padx=10, pady=5)
        text_entry = tk.Entry(dialog, bg="#333", fg="#fff", font=("Arial", 10), width=40)
        text_entry.pack(padx=10, pady=5)
        
        def create_tts():
            sound_name = name_entry.get()
            text = text_entry.get()
            
            if not sound_name or not text:
                messagebox.showwarning("Error", "Enter name and text!")
                return
            
            try:
                output_file = f"tts_{sound_name}.wav"
                tts_engine.save_to_file(text, output_file)
                tts_engine.runAndWait()
                
                self.sound_files[sound_name] = output_file
                self.sounds[sound_name] = output_file
                self.save_soundboard()
                self.refresh_sound_buttons()
                dialog.destroy()
                self.status_label.config(text=f"Created: {sound_name}", fg="#00ff00")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create TTS:\n{str(e)}")
        
        tk.Button(dialog, text="Create Sound", command=create_tts, bg="#00aa00", fg="white", 
                 font=("Arial", 11, "bold"), width=30).pack(pady=10)
    
    def play_sound(self, sound_name):
        """Play a sound"""
        if sound_name not in self.sounds:
            return
        
        try:
            sound_path = self.sounds[sound_name]
            
            # Load and play with pygame
            if sound_path.endswith('.wav') or sound_path.endswith('.mp3'):
                sound = pygame.mixer.Sound(sound_path)
                sound.set_volume(self.volume_var.get() / 100.0)
                sound.play()
                
                self.current_playing = sound_name
                self.now_playing_label.config(text=f"🔊 Now Playing: {sound_name}")
                self.status_label.config(text=f"Playing: {sound_name} 🎵", fg="#ffff00")
                
                # Update after sound finishes
                duration = int(pygame.mixer.Sound(sound_path).get_length() * 1000)
                self.root.after(duration, self.sound_finished)
        except Exception as e:
            self.status_label.config(text=f"Error playing sound: {str(e)}", fg="#ff3300")
    
    def sound_finished(self):
        """Called when sound finishes"""
        self.current_playing = None
        self.now_playing_label.config(text="🔊 Now Playing: None")
    
    def set_volume(self, value):
        """Set volume"""
        pygame.mixer.music.set_volume(int(value) / 100.0)
    
    def refresh_sound_buttons(self):
        """Refresh sound button grid"""
        for widget in self.sound_scrollable_frame.winfo_children():
            widget.destroy()
        
        hotkeys = list("1234567890abcdefghijklmnopqrstuvwxyz")
        hotkey_idx = 0
        
        for i, (sound_name, sound_path) in enumerate(self.sounds.items()):
            hotkey = hotkeys[hotkey_idx] if hotkey_idx < len(hotkeys) else "?"
            self.hotkey_map[hotkey] = sound_name
            
            btn_frame = tk.Frame(self.sound_scrollable_frame, bg="#2a2a2a")
            btn_frame.pack(fill=tk.X, pady=3, padx=5)
            
            btn = tk.Button(btn_frame, text=f"[{hotkey.upper()}] {sound_name}", 
                           command=lambda s=sound_name: self.play_sound(s),
                           bg="#0066cc", fg="white", font=("Arial", 10, "bold"), width=35, anchor="w")
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
            
            delete_btn = tk.Button(btn_frame, text="❌", command=lambda s=sound_name: self.delete_sound(s),
                                  bg="#ff3300", fg="white", font=("Arial", 10, "bold"), width=3)
            delete_btn.pack(side=tk.LEFT, padx=3)
            
            hotkey_idx += 1
    
    def delete_sound(self, sound_name):
        """Delete a sound"""
        if sound_name in self.sounds:
            del self.sounds[sound_name]
            if sound_name in self.sound_files:
                del self.sound_files[sound_name]
            self.save_soundboard()
            self.refresh_sound_buttons()
            self.status_label.config(text=f"Deleted: {sound_name}", fg="#ffff00")
    
    def clear_all_sounds(self):
        """Clear all sounds"""
        if messagebox.askyesno("Confirm", "Delete all sounds?"):
            self.sounds.clear()
            self.sound_files.clear()
            self.save_soundboard()
            self.refresh_sound_buttons()
            self.status_label.config(text="All sounds cleared", fg="#ffff00")
    
    def on_key_press(self, event):
        """Handle keyboard hotkeys"""
        key = event.char.lower()
        
        if key in self.hotkey_map:
            sound_name = self.hotkey_map[key]
            self.play_sound(sound_name)
    
    def save_soundboard(self):
        """Save soundboard to file"""
        try:
            with open(self.sounds_file, 'w') as f:
                json.dump(self.sound_files, f)
        except:
            pass
    
    def load_soundboard(self):
        """Load soundboard from file"""
        if os.path.exists(self.sounds_file):
            try:
                with open(self.sounds_file, 'r') as f:
                    self.sound_files = json.load(f)
                    self.sounds = self.sound_files.copy()
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = SoundboardApp(root)
    root.mainloop()
