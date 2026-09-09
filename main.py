import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import threading

class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera GUI - Easy Mode")
        self.root.geometry("900x800")
        self.root.configure(bg="#f0f0f0")
        
        # Camera variables
        self.cap = None
        self.running = False
        self.current_effect = "none"
        self.selected_camera = 0
        self.camera_name = "Camera 0"
        
        # Title
        title_label = tk.Label(root, text="📷 Camera Application", font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)
        
        # Camera Selection Frame
        camera_frame = tk.LabelFrame(root, text="Select Camera", font=("Arial", 12, "bold"), bg="#f0f0f0", padx=10, pady=10)
        camera_frame.pack(pady=10, fill=tk.BOTH, padx=20)
        
        # Find available cameras
        self.available_cameras = self.find_cameras()
        
        if self.available_cameras:
            camera_options = [f"Camera {i}" for i in self.available_cameras]
            self.camera_var = tk.StringVar(value=camera_options[0])
            self.camera_dropdown = ttk.Combobox(camera_frame, textvariable=self.camera_var, 
                                               values=camera_options, state="readonly", width=20, font=("Arial", 11))
            self.camera_dropdown.pack(side=tk.LEFT, padx=5)
            
            # Start Camera Button (moved next to dropdown)
            self.start_btn = tk.Button(camera_frame, text="▶ Start Camera", command=self.start_camera, 
                                       bg="#4CAF50", fg="white", font=("Arial", 11), width=15)
            self.start_btn.pack(side=tk.LEFT, padx=5)
            
            # Stop Camera Button
            self.stop_btn = tk.Button(camera_frame, text="⏹ Stop", command=self.stop_camera, 
                                      bg="#f44336", fg="white", font=("Arial", 11), width=10, state=tk.DISABLED)
            self.stop_btn.pack(side=tk.LEFT, padx=5)
            
            self.camera_info_label = tk.Label(camera_frame, text=f"Found {len(self.available_cameras)} camera(s)", 
                                              font=("Arial", 10), bg="#f0f0f0", fg="green")
            self.camera_info_label.pack(side=tk.LEFT, padx=10)
            
            # Camera LED Indicator
            self.led_indicator = tk.Label(camera_frame, text="⚫", font=("Arial", 20), bg="#f0f0f0", fg="gray")
            self.led_indicator.pack(side=tk.LEFT, padx=10)
            self.led_label = tk.Label(camera_frame, text="LED OFF", font=("Arial", 10), bg="#f0f0f0", fg="gray")
            self.led_label.pack(side=tk.LEFT, padx=5)
        else:
            self.camera_info_label = tk.Label(camera_frame, text="❌ No cameras detected!", 
                                              font=("Arial", 10), bg="#f0f0f0", fg="red")
            self.camera_info_label.pack(side=tk.LEFT, padx=10)
        
        # Video frame
        self.video_label = tk.Label(root, bg="black", width=700, height=400)
        self.video_label.pack(pady=10)
        
        # Camera Name Display (on top of video)
        self.camera_name_display = tk.Label(self.video_label, text="", font=("Arial", 16, "bold"), 
                                           bg="black", fg="lime", anchor="nw")
        self.camera_name_display.place(x=10, y=10)
        
        # Control frame
        control_frame = tk.Frame(root, bg="#f0f0f0")
        control_frame.pack(pady=10)
        
        # Snapshot button
        self.snapshot_btn = tk.Button(control_frame, text="📸 Take Snapshot", command=self.take_snapshot, 
                                      bg="#2196F3", fg="white", font=("Arial", 12), width=15, state=tk.DISABLED)
        self.snapshot_btn.pack(side=tk.LEFT, padx=5)
        
        # Effects frame
        effects_frame = tk.LabelFrame(root, text="Effects", font=("Arial", 12, "bold"), bg="#f0f0f0", padx=10, pady=10)
        effects_frame.pack(pady=10, fill=tk.BOTH, padx=20)
        
        # Effect buttons
        effects = [
            ("Normal", "none"),
            ("Grayscale", "gray"),
            ("Blur", "blur"),
            ("Edge Detection", "edge"),
            ("Flip H", "flip_h"),
            ("Flip V", "flip_v")
        ]
        
        self.effect_buttons = {}
        for i, (name, effect_id) in enumerate(effects):
            btn = tk.Button(effects_frame, text=name, command=lambda e=effect_id: self.set_effect(e),
                           bg="#9C27B0", fg="white", font=("Arial", 10), width=12)
            btn.grid(row=i//3, column=i%3, padx=5, pady=5)
            self.effect_buttons[effect_id] = btn
        
        # Status label
        self.status_label = tk.Label(root, text="Status: Ready", font=("Arial", 10), bg="#f0f0f0")
        self.status_label.pack(pady=5)
    
    def find_cameras(self):
        """Detect available cameras on the system"""
        available = []
        for i in range(10):  # Check first 10 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available
    
    def update_led_indicator(self, camera_index=None):
        """Update the LED indicator based on camera status"""
        if self.running and camera_index is not None:
            # LED ON - Green
            self.led_indicator.config(fg="lime")
            self.led_label.config(text="🔴 LED ON", fg="red")
        else:
            # LED OFF - Gray
            self.led_indicator.config(fg="gray")
            self.led_label.config(text="⚫ LED OFF", fg="gray")
    
    def start_camera(self):
        if not self.running:
            # Get selected camera index
            if self.available_cameras:
                camera_index = self.available_cameras[0]  # Default to first available
                if hasattr(self, 'camera_dropdown'):
                    selected_text = self.camera_var.get()
                    camera_num = int(selected_text.split()[-1])
                    if camera_num in self.available_cameras:
                        camera_index = camera_num
            else:
                self.status_label.config(text="Status: No cameras available!", fg="red")
                return
            
            self.cap = cv2.VideoCapture(camera_index)
            self.running = True
            self.selected_camera = camera_index
            self.camera_name = f"Camera {camera_index}"
            
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.snapshot_btn.config(state=tk.NORMAL)
            
            # Update LED indicator
            self.update_led_indicator(camera_index)
            
            self.status_label.config(text=f"Status: Camera {camera_index} Running ✓", fg="green")
            self.update_frame()
    
    def stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.snapshot_btn.config(state=tk.DISABLED)
        self.video_label.config(image="")
        self.camera_name_display.config(text="")
        
        # Update LED indicator
        self.update_led_indicator()
        
        self.status_label.config(text="Status: Camera Stopped", fg="red")
    
    def set_effect(self, effect):
        self.current_effect = effect
    
    def apply_effect(self, frame):
        if self.current_effect == "gray":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif self.current_effect == "blur":
            frame = cv2.blur(frame, (15, 15))
        elif self.current_effect == "edge":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.Canny(gray, 100, 200)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif self.current_effect == "flip_h":
            frame = cv2.flip(frame, 1)
        elif self.current_effect == "flip_v":
            frame = cv2.flip(frame, 0)
        
        return frame
    
    def update_frame(self):
        if self.running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, (700, 400))
                frame = self.apply_effect(frame)
                
                # Convert to PIL format
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)
                
                # Update camera name display on video
                self.camera_name_display.config(text=f"📷 {self.camera_name}")
            
            self.root.after(30, self.update_frame)
    
    def take_snapshot(self):
        if self.running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                frame = self.apply_effect(frame)
                cv2.imwrite("snapshot.jpg", frame)
                self.status_label.config(text="Status: Snapshot saved as 'snapshot.jpg' ✓", fg="blue")
                self.root.after(3000, lambda: self.status_label.config(text=f"Status: Camera {self.selected_camera} Running ✓", fg="green"))

if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root)
    root.mainloop()
