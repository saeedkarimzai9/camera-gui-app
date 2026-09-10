import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time
import numpy as np
import json
import os

try:
    import pyvirtualcam
    VIRTUAL_CAM_AVAILABLE = True
except ImportError:
    VIRTUAL_CAM_AVAILABLE = False
    print("WARNING: pyvirtualcam not installed. Install with: pip install pyvirtualcam")

class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera GUI PRO - Complete Customization Suite")
        self.root.geometry("1400x1200")
        self.root.configure(bg="#f0f0f0")
        
        # Camera variables
        self.cap = None
        self.vcam = None
        self.running = False
        self.virtual_cam_active = False
        self.selected_camera = 0
        self.camera_name = "Camera 0"
        self.testing_camera = False
        self.manual_camera_num = 0
        
        # Standard resolutions
        self.VCAM_WIDTH = 640
        self.VCAM_HEIGHT = 480
        self.DISPLAY_WIDTH = 720
        self.DISPLAY_HEIGHT = 540
        
        # Settings storage
        self.settings_file = "camera_presets.json"
        self.current_preset = "Custom"
        
        # Effect settings
        self.effects = {
            "brightness": 0,
            "contrast": 1.0,
            "saturation": 1.0,
            "effect": "none",
            "opacity": 1.0,
            "effect_intensity": 1.0,
            "resolution": "720x540"
        }
        
        # Presets
        self.presets = {
            "Gaming": {
                "brightness": 10,
                "contrast": 1.3,
                "saturation": 1.2,
                "effect": "none",
                "opacity": 1.0,
                "effect_intensity": 1.0
            },
            "Stream": {
                "brightness": 5,
                "contrast": 1.1,
                "saturation": 1.1,
                "effect": "blur",
                "opacity": 0.8,
                "effect_intensity": 0.5
            },
            "Professional": {
                "brightness": 0,
                "contrast": 1.0,
                "saturation": 0.9,
                "effect": "none",
                "opacity": 1.0,
                "effect_intensity": 1.0
            }
        }
        
        self.load_presets()
        
        # Title
        title_label = tk.Label(root, text="📷 Camera PRO - Complete Customization Suite", 
                              font=("Arial", 22, "bold"), bg="#f0f0f0", fg="#333")
        title_label.pack(pady=10)
        
        # Virtual Camera Status
        vcam_status_frame = tk.Frame(root, bg="#f0f0f0")
        vcam_status_frame.pack(pady=5)
        
        vcam_label = tk.Label(vcam_status_frame, text="Virtual Camera:", 
                             font=("Arial", 11, "bold"), bg="#f0f0f0", fg="#333")
        vcam_label.pack(side=tk.LEFT, padx=5)
        
        if VIRTUAL_CAM_AVAILABLE:
            self.vcam_status = tk.Label(vcam_status_frame, text="🔴 INACTIVE", 
                                       font=("Arial", 11, "bold"), bg="#f0f0f0", fg="red")
        else:
            self.vcam_status = tk.Label(vcam_status_frame, text="❌ NOT INSTALLED", 
                                       font=("Arial", 11, "bold"), bg="#f0f0f0", fg="red")
        self.vcam_status.pack(side=tk.LEFT, padx=5)
        
        # Camera Selection Frame
        camera_frame = tk.LabelFrame(root, text="📷 Select Camera", font=("Arial", 12, "bold"), 
                                    bg="#f0f0f0", padx=10, pady=10)
        camera_frame.pack(pady=10, fill=tk.BOTH, padx=20)
        
        self.available_cameras = self.find_cameras()
        
        # Auto-detected cameras
        tk.Label(camera_frame, text="Auto-Detected:", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        if self.available_cameras:
            camera_options = [f"Camera {i}" for i in self.available_cameras]
            self.camera_var = tk.StringVar(value=camera_options[0])
            self.camera_dropdown = ttk.Combobox(camera_frame, textvariable=self.camera_var, 
                                               values=camera_options, state="readonly", width=12, font=("Arial", 11))
            self.camera_dropdown.pack(side=tk.LEFT, padx=5)
        else:
            self.camera_dropdown = ttk.Combobox(camera_frame, values=[], state="readonly", width=12, font=("Arial", 11))
            self.camera_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Manual camera selection
        tk.Label(camera_frame, text="Or Manual:", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        self.manual_camera_var = tk.StringVar(value="Camera 0")
        manual_options = [f"Camera {i}" for i in range(10)]
        self.manual_dropdown = ttk.Combobox(camera_frame, textvariable=self.manual_camera_var, 
                                           values=manual_options, state="readonly", width=12, font=("Arial", 11))
        self.manual_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        self.test_btn = tk.Button(camera_frame, text="🧪 Test", command=self.test_camera, 
                                  bg="#FF9800", fg="white", font=("Arial", 11, "bold"), width=8, padx=5)
        self.test_btn.pack(side=tk.LEFT, padx=3)
        
        self.start_btn = tk.Button(camera_frame, text="▶ Start", command=self.start_camera, 
                                   bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), width=8, padx=5)
        self.start_btn.pack(side=tk.LEFT, padx=3)
        
        self.stop_btn = tk.Button(camera_frame, text="⏹ Stop", command=self.stop_camera, 
                                  bg="#f44336", fg="white", font=("Arial", 11, "bold"), width=8, padx=5, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=3)
        
        self.led_indicator = tk.Label(camera_frame, text="⚫", font=("Arial", 18), bg="#f0f0f0", fg="gray")
        self.led_indicator.pack(side=tk.LEFT, padx=10)
        
        # Main content frame
        main_frame = tk.Frame(root, bg="#f0f0f0")
        main_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        
        # Left side - Video preview
        left_frame = tk.Frame(main_frame, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        video_label_text = tk.Label(left_frame, text="📺 Live Preview", font=("Arial", 12, "bold"), bg="#f0f0f0")
        video_label_text.pack()
        
        self.video_label = tk.Label(left_frame, bg="black", width=self.DISPLAY_WIDTH, height=self.DISPLAY_HEIGHT, 
                                   relief=tk.SUNKEN, bd=2)
        self.video_label.pack(pady=10)
        
        self.camera_name_display = tk.Label(self.video_label, text="", font=("Arial", 14, "bold"), 
                                           bg="black", fg="lime", anchor="nw")
        self.camera_name_display.place(x=15, y=15)
        
        # Right side - Controls
        right_frame = tk.Frame(main_frame, bg="#f0f0f0")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Presets
        preset_frame = tk.LabelFrame(right_frame, text="🎭 Presets", font=("Arial", 11, "bold"), bg="#f0f0f0", padx=10, pady=10)
        preset_frame.pack(fill=tk.X, pady=5)
        
        for preset_name in self.presets.keys():
            btn = tk.Button(preset_frame, text=preset_name, command=lambda p=preset_name: self.load_preset(p),
                           bg="#673AB7", fg="white", font=("Arial", 10, "bold"), width=12)
            btn.pack(side=tk.LEFT, padx=3)
        
        # Display Settings
        display_frame = tk.LabelFrame(right_frame, text="🎨 Display Settings", font=("Arial", 11, "bold"), bg="#f0f0f0", padx=10, pady=10)
        display_frame.pack(fill=tk.X, pady=5)
        
        # Brightness
        tk.Label(display_frame, text="Brightness:", font=("Arial", 10), bg="#f0f0f0").pack(anchor=tk.W)
        self.brightness_var = tk.IntVar(value=0)
        brightness_scale = tk.Scale(display_frame, from_=-100, to=100, orient=tk.HORIZONTAL, 
                                    variable=self.brightness_var, bg="#fff", fg="#333", command=self.update_effects)
        brightness_scale.pack(fill=tk.X, pady=5)
        self.brightness_label = tk.Label(display_frame, text="0", font=("Arial", 9), bg="#f0f0f0")
        self.brightness_label.pack(anchor=tk.E)
        
        # Contrast
        tk.Label(display_frame, text="Contrast:", font=("Arial", 10), bg="#f0f0f0").pack(anchor=tk.W)
        self.contrast_var = tk.DoubleVar(value=1.0)
        contrast_scale = tk.Scale(display_frame, from_=0.5, to=2.0, orient=tk.HORIZONTAL, resolution=0.1,
                                  variable=self.contrast_var, bg="#fff", fg="#333", command=self.update_effects)
        contrast_scale.pack(fill=tk.X, pady=5)
        self.contrast_label = tk.Label(display_frame, text="1.0", font=("Arial", 9), bg="#f0f0f0")
        self.contrast_label.pack(anchor=tk.E)
        
        # Saturation
        tk.Label(display_frame, text="Saturation:", font=("Arial", 10), bg="#f0f0f0").pack(anchor=tk.W)
        self.saturation_var = tk.DoubleVar(value=1.0)
        saturation_scale = tk.Scale(display_frame, from_=0.0, to=2.0, orient=tk.HORIZONTAL, resolution=0.1,
                                    variable=self.saturation_var, bg="#fff", fg="#333", command=self.update_effects)
        saturation_scale.pack(fill=tk.X, pady=5)
        self.saturation_label = tk.Label(display_frame, text="1.0", font=("Arial", 9), bg="#f0f0f0")
        self.saturation_label.pack(anchor=tk.E)
        
        # Effects
        effects_frame = tk.LabelFrame(right_frame, text="✨ Effects", font=("Arial", 11, "bold"), bg="#f0f0f0", padx=10, pady=10)
        effects_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(effects_frame, text="Select Effect:", font=("Arial", 10), bg="#f0f0f0").pack(anchor=tk.W)
        
        self.effect_var = tk.StringVar(value="none")
        effect_options = ["none", "gray", "blur", "edge", "sepia", "vintage", "pixelate", "sharpen", "red_filter", "blue_filter", "green_filter", "flip_h", "flip_v"]
        effect_menu = ttk.Combobox(effects_frame, textvariable=self.effect_var, values=effect_options, state="readonly", font=("Arial", 10))
        effect_menu.pack(fill=tk.X, pady=5)
        effect_menu.bind("<<ComboboxSelected>>", lambda e: self.update_effects())
        
        # Effect Intensity
        tk.Label(effects_frame, text="Effect Intensity:", font=("Arial", 10), bg="#f0f0f0").pack(anchor=tk.W)
        self.effect_intensity_var = tk.DoubleVar(value=1.0)
        intensity_scale = tk.Scale(effects_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, resolution=0.1,
                                   variable=self.effect_intensity_var, bg="#fff", fg="#333", command=self.update_effects)
        intensity_scale.pack(fill=tk.X, pady=5)
        self.intensity_label = tk.Label(effects_frame, text="1.0", font=("Arial", 9), bg="#f0f0f0")
        self.intensity_label.pack(anchor=tk.E)
        
        # Opacity
        tk.Label(effects_frame, text="Opacity:", font=("Arial", 10), bg="#f0f0f0").pack(anchor=tk.W)
        self.opacity_var = tk.DoubleVar(value=1.0)
        opacity_scale = tk.Scale(effects_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, resolution=0.1,
                                variable=self.opacity_var, bg="#fff", fg="#333", command=self.update_effects)
        opacity_scale.pack(fill=tk.X, pady=5)
        self.opacity_label = tk.Label(effects_frame, text="1.0", font=("Arial", 9), bg="#f0f0f0")
        self.opacity_label.pack(anchor=tk.E)
        
        # Quick Effects Buttons
        quick_effects = [
            ("Grayscale", "gray"),
            ("Sepia", "sepia"),
            ("Blur", "blur")
        ]
        
        quick_frame = tk.Frame(effects_frame, bg="#f0f0f0")
        quick_frame.pack(fill=tk.X, pady=5)
        
        for name, effect_id in quick_effects:
            btn = tk.Button(quick_frame, text=name, command=lambda e=effect_id: self.set_effect_quick(e),
                           bg="#9C27B0", fg="white", font=("Arial", 9, "bold"), width=8)
            btn.pack(side=tk.LEFT, padx=3)
        
        # Virtual Camera and Snapshot
        action_frame = tk.Frame(right_frame, bg="#f0f0f0")
        action_frame.pack(fill=tk.X, pady=5)
        
        self.snapshot_btn = tk.Button(action_frame, text="📸 Snapshot", command=self.take_snapshot, 
                                      bg="#2196F3", fg="white", font=("Arial", 11, "bold"), width=15, state=tk.DISABLED)
        self.snapshot_btn.pack(side=tk.LEFT, padx=3)
        
        self.vcam_btn = tk.Button(action_frame, text="🌐 Virtual Camera", 
                                 command=self.toggle_virtual_camera, 
                                 bg="#9C27B0", fg="white", font=("Arial", 11, "bold"), width=15, state=tk.DISABLED)
        self.vcam_btn.pack(side=tk.LEFT, padx=3)
        
        # Reset button
        reset_btn = tk.Button(right_frame, text="🔄 Reset All", command=self.reset_settings,
                             bg="#FF6F00", fg="white", font=("Arial", 11, "bold"), width=30)
        reset_btn.pack(pady=5)
        
        # Status label
        self.status_label = tk.Label(root, text="Status: Ready", font=("Arial", 10, "bold"), bg="#f0f0f0", fg="#333")
        self.status_label.pack(pady=5)
    
    def find_cameras(self):
        """Detect available cameras"""
        available = []
        print("🔍 Scanning for cameras...")
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    success = False
                    for attempt in range(3):
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            success = True
                            print(f"✅ Found Camera {i}")
                            break
                        time.sleep(0.1)
                    cap.release()
                    if success:
                        available.append(i)
            except Exception as e:
                print(f"Error checking camera {i}: {e}")
                continue
        return available
    
    def get_selected_camera(self):
        """Get camera number"""
        if self.available_cameras and self.camera_dropdown.get():
            auto_text = self.camera_var.get()
            return int(auto_text.split()[-1])
        manual_text = self.manual_camera_var.get()
        return int(manual_text.split()[-1])
    
    def test_camera(self):
        """Test selected camera"""
        if self.testing_camera:
            messagebox.showwarning("Testing", "Already testing!")
            return
        
        camera_num = self.get_selected_camera()
        self.manual_camera_num = camera_num
        
        self.testing_camera = True
        self.test_btn.config(state=tk.DISABLED)
        self.status_label.config(text=f"Testing Camera {camera_num}...", fg="orange")
        self.root.update()
        
        test_thread = threading.Thread(target=self._test_camera_thread, args=(camera_num,))
        test_thread.daemon = True
        test_thread.start()
    
    def _test_camera_thread(self, camera_num):
        """Test camera in background"""
        try:
            cap = cv2.VideoCapture(camera_num)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            success = False
            for attempt in range(5):
                ret, frame = cap.read()
                if ret and frame is not None:
                    success = True
                    break
                time.sleep(0.2)
            
            cap.release()
            self.root.after(0, self._test_camera_result, camera_num, success)
        except Exception as e:
            print(f"Error testing camera {camera_num}: {e}")
            self.root.after(0, self._test_camera_result, camera_num, False)
    
    def _test_camera_result(self, camera_num, success):
        """Show test results"""
        self.testing_camera = False
        self.test_btn.config(state=tk.NORMAL)
        
        if success:
            messagebox.showinfo("Test Successful", f"✅ Camera {camera_num} works!")
            self.status_label.config(text=f"Camera {camera_num} OK ✓", fg="green")
        else:
            messagebox.showerror("Test Failed", f"❌ Camera {camera_num} not responding!")
            self.status_label.config(text=f"Camera {camera_num} FAILED", fg="red")
    
    def start_camera(self):
        """Start camera"""
        if not self.running:
            camera_index = self.get_selected_camera()
            self.manual_camera_num = camera_index
            
            try:
                self.cap = cv2.VideoCapture(camera_index)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                ret, _ = self.cap.read()
                if not ret:
                    raise Exception("Camera failed to open")
                
                self.running = True
                self.selected_camera = camera_index
                self.camera_name = f"Camera {camera_index}"
                
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
                self.snapshot_btn.config(state=tk.NORMAL)
                self.vcam_btn.config(state=tk.NORMAL)
                self.test_btn.config(state=tk.DISABLED)
                self.manual_dropdown.config(state=tk.DISABLED)
                
                self.led_indicator.config(fg="lime")
                self.status_label.config(text=f"Camera {camera_index} Running ✓", fg="green")
                self.update_frame()
            except Exception as e:
                self.cap = None
                self.running = False
                messagebox.showerror("Camera Error", f"Failed to open camera {camera_index}:\n{str(e)}")
    
    def stop_camera(self):
        """Stop camera"""
        self.running = False
        self.stop_virtual_camera()
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.snapshot_btn.config(state=tk.DISABLED)
        self.vcam_btn.config(state=tk.DISABLED)
        self.test_btn.config(state=tk.NORMAL)
        self.manual_dropdown.config(state="readonly")
        self.video_label.config(image="")
        self.camera_name_display.config(text="")
        self.led_indicator.config(fg="gray")
        self.status_label.config(text="Camera Stopped", fg="red")
    
    def update_effects(self, *args):
        """Update effect values"""
        self.effects["brightness"] = self.brightness_var.get()
        self.effects["contrast"] = self.contrast_var.get()
        self.effects["saturation"] = self.saturation_var.get()
        self.effects["effect"] = self.effect_var.get()
        self.effects["effect_intensity"] = self.effect_intensity_var.get()
        self.effects["opacity"] = self.opacity_var.get()
        
        # Update labels
        self.brightness_label.config(text=str(self.brightness_var.get()))
        self.contrast_label.config(text=f"{self.contrast_var.get():.1f}")
        self.saturation_label.config(text=f"{self.saturation_var.get():.1f}")
        self.intensity_label.config(text=f"{self.effect_intensity_var.get():.1f}")
        self.opacity_label.config(text=f"{self.opacity_var.get():.1f}")
    
    def set_effect_quick(self, effect):
        """Quick set effect"""
        self.effect_var.set(effect)
        self.update_effects()
    
    def load_preset(self, preset_name):
        """Load preset"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            self.brightness_var.set(preset["brightness"])
            self.contrast_var.set(preset["contrast"])
            self.saturation_var.set(preset["saturation"])
            self.effect_var.set(preset["effect"])
            self.opacity_var.set(preset["opacity"])
            self.effect_intensity_var.set(preset["effect_intensity"])
            self.update_effects()
            self.current_preset = preset_name
            self.status_label.config(text=f"Preset: {preset_name} ✓", fg="blue")
    
    def reset_settings(self):
        """Reset all settings"""
        self.brightness_var.set(0)
        self.contrast_var.set(1.0)
        self.saturation_var.set(1.0)
        self.effect_var.set("none")
        self.opacity_var.set(1.0)
        self.effect_intensity_var.set(1.0)
        self.update_effects()
        self.status_label.config(text="Settings Reset ✓", fg="green")
    
    def apply_effects(self, frame):
        """Apply all effects to frame"""
        # Brightness
        brightness = self.effects["brightness"]
        if brightness != 0:
            frame = cv2.convertScaleAbs(frame, alpha=1.0, beta=brightness)
        
        # Contrast
        contrast = self.effects["contrast"]
        frame = cv2.convertScaleAbs(frame, alpha=contrast, beta=0)
        
        # Saturation
        saturation = self.effects["saturation"]
        if saturation != 1.0:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = hsv[:, :, 1] * saturation
            hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
            frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        # Apply effect
        effect = self.effects["effect"]
        intensity = self.effects["effect_intensity"]
        
        if effect == "gray":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif effect == "blur":
            blur_amount = int(5 + (intensity * 10))
            if blur_amount % 2 == 0:
                blur_amount += 1
            frame = cv2.blur(frame, (blur_amount, blur_amount))
        elif effect == "edge":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            frame = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        elif effect == "sepia":
            sepia_filter = np.array([[0.272, 0.534, 0.131],
                                    [0.349, 0.686, 0.168],
                                    [0.393, 0.769, 0.189]])
            frame = cv2.transform(frame, sepia_filter)
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        elif effect == "vintage":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.addWeighted(frame, 0.8, np.ones_like(frame) * 40, 0.2, 0)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        elif effect == "pixelate":
            pixel_size = int(5 + (intensity * 10))
            h, w = frame.shape[:2]
            temp = cv2.resize(frame, (w // pixel_size, h // pixel_size))
            frame = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
        elif effect == "sharpen":
            kernel = np.array([[-1, -1, -1],
                              [-1, 9 + int(intensity * 5), -1],
                              [-1, -1, -1]]) / 1.0
            frame = cv2.filter2D(frame, -1, kernel)
        elif effect == "red_filter":
            frame[:, :, 1] = frame[:, :, 1] * (1 - intensity * 0.7)
            frame[:, :, 0] = frame[:, :, 0] * (1 - intensity * 0.7)
        elif effect == "blue_filter":
            frame[:, :, 1] = frame[:, :, 1] * (1 - intensity * 0.7)
            frame[:, :, 2] = frame[:, :, 2] * (1 - intensity * 0.7)
        elif effect == "green_filter":
            frame[:, :, 0] = frame[:, :, 0] * (1 - intensity * 0.7)
            frame[:, :, 2] = frame[:, :, 2] * (1 - intensity * 0.7)
        elif effect == "flip_h":
            frame = cv2.flip(frame, 1)
        elif effect == "flip_v":
            frame = cv2.flip(frame, 0)
        
        # Opacity
        opacity = self.effects["opacity"]
        if opacity < 1.0:
            frame = (frame.astype(np.float32) * opacity).astype(np.uint8)
        
        return frame
    
    def resize_frame(self, frame, width, height):
        """Resize frame maintaining aspect ratio"""
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
            if not VIRTUAL_CAM_AVAILABLE:
                raise Exception("pyvirtualcam not installed")
            
            self.vcam = pyvirtualcam.Camera(width=self.VCAM_WIDTH, height=self.VCAM_HEIGHT, fps=30)
            self.virtual_cam_active = True
            self.vcam_btn.config(text="🌐 Disable Virtual", bg="#4CAF50")
            self.vcam_status.config(text="🟢 ACTIVE", fg="green")
            self.status_label.config(text="Virtual Camera ACTIVE ✓", fg="green")
            messagebox.showinfo("Success", "✅ Virtual Camera Active!\n\nUse in OBS/Discord/Websites")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start virtual camera:\n{str(e)}")
    
    def stop_virtual_camera(self):
        """Stop virtual camera"""
        try:
            if self.vcam:
                self.vcam.close()
                self.vcam = None
            self.virtual_cam_active = False
            self.vcam_btn.config(text="🌐 Virtual Camera", bg="#9C27B0")
            self.vcam_status.config(text="🔴 INACTIVE", fg="red")
        except Exception as e:
            print(f"Error stopping virtual camera: {e}")
    
    def update_frame(self):
        """Update frame loop"""
        if self.running and self.cap:
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    # Apply effects
                    frame = self.apply_effects(frame)
                    
                    # Virtual camera
                    if self.virtual_cam_active and self.vcam:
                        try:
                            vcam_frame = self.resize_frame(frame, self.VCAM_WIDTH, self.VCAM_HEIGHT)
                            frame_rgb = cv2.cvtColor(vcam_frame, cv2.COLOR_BGR2RGB)
                            self.vcam.send(frame_rgb)
                        except Exception as e:
                            print(f"Virtual camera error: {e}")
                    
                    # Display
                    display_frame = self.resize_frame(frame, self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)
                    cv2image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(cv2image)
                    imgtk = ImageTk.PhotoImage(image=img)
                    
                    self.video_label.imgtk = imgtk
                    self.video_label.config(image=imgtk)
                    
                    vcam_text = " 🌐 STREAMING" if self.virtual_cam_active else ""
                    self.camera_name_display.config(text=f"📷 {self.camera_name}{vcam_text}")
                else:
                    self.running = False
                    self.stop_camera()
                    messagebox.showerror("Camera Error", "Camera disconnected!")
                    return
            except Exception as e:
                print(f"Frame update error: {e}")
                self.running = False
                self.stop_camera()
                return
            
            self.root.after(30, self.update_frame)
    
    def take_snapshot(self):
        """Take snapshot"""
        if self.running and self.cap:
            try:
                ret, frame = self.cap.read()
                if ret:
                    frame = self.apply_effects(frame)
                    cv2.imwrite("snapshot.jpg", frame)
                    self.status_label.config(text="Snapshot saved ✓", fg="blue")
                    self.root.after(3000, lambda: self.status_label.config(text="Ready", fg="#333"))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save snapshot:\n{str(e)}")
    
    def load_presets(self):
        """Load presets from file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    self.presets.update(loaded)
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root)
    root.mainloop()
