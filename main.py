import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time
import numpy as np

try:
    import pyvirtualcam
    VIRTUAL_CAM_AVAILABLE = True
except ImportError:
    VIRTUAL_CAM_AVAILABLE = False
    print("WARNING: pyvirtualcam not installed. Install with: pip install pyvirtualcam")

class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera GUI - Virtual Camera Edition")
        self.root.geometry("1000x950")
        self.root.configure(bg="#f0f0f0")
        
        # Camera variables
        self.cap = None
        self.vcam = None
        self.running = False
        self.virtual_cam_active = False
        self.current_effect = "none"
        self.selected_camera = 0
        self.camera_name = "Camera 0"
        self.testing_camera = False
        self.manual_camera_num = 0
        
        # Standard resolutions for virtual camera and display
        self.VCAM_WIDTH = 640
        self.VCAM_HEIGHT = 480
        self.DISPLAY_WIDTH = 720
        self.DISPLAY_HEIGHT = 540
        
        # Title
        title_label = tk.Label(root, text="📷 Camera Application - Virtual Camera", 
                              font=("Arial", 20, "bold"), bg="#f0f0f0", fg="#333")
        title_label.pack(pady=10)
        
        # Virtual Camera Status
        vcam_status_frame = tk.Frame(root, bg="#f0f0f0")
        vcam_status_frame.pack(pady=5)
        
        vcam_label = tk.Label(vcam_status_frame, text="Virtual Camera Status:", 
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
        camera_frame = tk.LabelFrame(root, text="Select Camera", font=("Arial", 12, "bold"), 
                                    bg="#f0f0f0", padx=10, pady=10)
        camera_frame.pack(pady=10, fill=tk.BOTH, padx=20)
        
        # Find available cameras
        self.available_cameras = self.find_cameras()
        
        # Create two options: Auto-detect and Manual
        camera_options_frame = tk.Frame(camera_frame, bg="#f0f0f0")
        camera_options_frame.pack(side=tk.LEFT, padx=5)
        
        # Auto-detected cameras
        tk.Label(camera_options_frame, text="Auto-Detected:", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        if self.available_cameras:
            camera_options = [f"Camera {i}" for i in self.available_cameras]
            self.camera_var = tk.StringVar(value=camera_options[0])
            self.camera_dropdown = ttk.Combobox(camera_options_frame, textvariable=self.camera_var, 
                                               values=camera_options, state="readonly", width=12, font=("Arial", 11))
            self.camera_dropdown.pack(side=tk.LEFT, padx=5)
            
            self.camera_info_label = tk.Label(camera_options_frame, text=f"({len(self.available_cameras)} found)", 
                                              font=("Arial", 9), bg="#f0f0f0", fg="green")
            self.camera_info_label.pack(side=tk.LEFT, padx=5)
        else:
            self.camera_dropdown = ttk.Combobox(camera_options_frame, values=[], state="readonly", width=12, font=("Arial", 11))
            self.camera_dropdown.pack(side=tk.LEFT, padx=5)
            
            self.camera_info_label = tk.Label(camera_options_frame, text="(0 found)", 
                                              font=("Arial", 9), bg="#f0f0f0", fg="red")
            self.camera_info_label.pack(side=tk.LEFT, padx=5)
        
        # Manual camera selection
        manual_frame = tk.Frame(camera_frame, bg="#f0f0f0")
        manual_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(manual_frame, text="Or Use:", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        # Dropdown for manual camera numbers (0-9)
        self.manual_camera_var = tk.StringVar(value="Camera 0")
        manual_options = [f"Camera {i}" for i in range(10)]
        self.manual_dropdown = ttk.Combobox(manual_frame, textvariable=self.manual_camera_var, 
                                           values=manual_options, state="readonly", width=12, font=("Arial", 11))
        self.manual_dropdown.pack(side=tk.LEFT, padx=5)
        
        tk.Label(manual_frame, text="(Manual)", font=("Arial", 9), bg="#f0f0f0", fg="blue").pack(side=tk.LEFT, padx=5)
        
        # Test Camera Button
        self.test_btn = tk.Button(camera_frame, text="🧪 Test Camera", command=self.test_camera, 
                                  bg="#FF9800", fg="white", font=("Arial", 11), width=12, padx=10)
        self.test_btn.pack(side=tk.LEFT, padx=5)
        
        # Start Camera Button
        self.start_btn = tk.Button(camera_frame, text="▶ Start Camera", command=self.start_camera, 
                                   bg="#4CAF50", fg="white", font=("Arial", 11), width=15, padx=10)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        # Stop Camera Button
        self.stop_btn = tk.Button(camera_frame, text="⏹ Stop", command=self.stop_camera, 
                                  bg="#f44336", fg="white", font=("Arial", 11), width=10, padx=10, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Camera LED Indicator
        self.led_indicator = tk.Label(camera_frame, text="⚫", font=("Arial", 20), bg="#f0f0f0", fg="gray")
        self.led_indicator.pack(side=tk.LEFT, padx=10)
        self.led_label = tk.Label(camera_frame, text="LED OFF", font=("Arial", 10), bg="#f0f0f0", fg="gray")
        self.led_label.pack(side=tk.LEFT, padx=5)
        
        # Video frame with better styling
        self.video_label = tk.Label(root, bg="black", width=self.DISPLAY_WIDTH, height=self.DISPLAY_HEIGHT, 
                                   relief=tk.SUNKEN, bd=2)
        self.video_label.pack(pady=15)
        
        # Camera Name Display (on top of video)
        self.camera_name_display = tk.Label(self.video_label, text="", font=("Arial", 14, "bold"), 
                                           bg="black", fg="lime", anchor="nw")
        self.camera_name_display.place(x=15, y=15)
        
        # Control frame
        control_frame = tk.Frame(root, bg="#f0f0f0")
        control_frame.pack(pady=10)
        
        # Snapshot button
        self.snapshot_btn = tk.Button(control_frame, text="📸 Take Snapshot", command=self.take_snapshot, 
                                      bg="#2196F3", fg="white", font=("Arial", 12, "bold"), width=16, padx=10, state=tk.DISABLED)
        self.snapshot_btn.pack(side=tk.LEFT, padx=5)
        
        # Virtual Camera Toggle
        self.vcam_btn = tk.Button(control_frame, text="🌐 Enable Virtual Camera", 
                                 command=self.toggle_virtual_camera, 
                                 bg="#9C27B0", fg="white", font=("Arial", 12, "bold"), width=22, padx=10, state=tk.DISABLED)
        self.vcam_btn.pack(side=tk.LEFT, padx=5)
        
        # Effects frame
        effects_frame = tk.LabelFrame(root, text="Effects - Apply to All (GUI + Virtual Camera)", 
                                     font=("Arial", 12, "bold"), bg="#f0f0f0", padx=10, pady=10)
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
                           bg="#9C27B0", fg="white", font=("Arial", 10, "bold"), width=14, padx=8)
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="ew")
            self.effect_buttons[effect_id] = btn
        
        # Make columns equal width
        for i in range(3):
            effects_frame.columnconfigure(i, weight=1)
        
        # Status label
        self.status_label = tk.Label(root, text="Status: Ready - Select Camera 0 or use Manual selector", 
                                     font=("Arial", 10, "bold"), bg="#f0f0f0", fg="#333")
        self.status_label.pack(pady=5)
        
        # Instructions
        instructions_text = "📝 TIP: If Camera 0 doesn't show in Auto-Detected, use the Manual selector on the right!"
        if not VIRTUAL_CAM_AVAILABLE:
            instructions_text += "\n⚠️ To enable virtual camera: pip install pyvirtualcam"
        
        instructions = tk.Label(root, text=instructions_text, 
                               font=("Arial", 9), bg="#e3f2fd", fg="#1976d2", padx=10, pady=5)
        instructions.pack(pady=5, fill=tk.X, padx=20)
    
    def find_cameras(self):
        """Detect available cameras on the system with improved detection"""
        available = []
        print("🔍 Scanning for cameras...")
        for i in range(10):  # Check first 10 camera indices
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Try multiple times to read
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
        
        if not available:
            print("⚠️ No cameras auto-detected - use Manual selector!")
        
        return available
    
    def get_selected_camera(self):
        """Get camera number from either auto-detect or manual selection"""
        # Try to use manual camera first if set
        manual_text = self.manual_camera_var.get()
        manual_num = int(manual_text.split()[-1])
        
        # If auto-detect has options, prefer it
        if self.available_cameras and self.camera_dropdown.get():
            auto_text = self.camera_var.get()
            auto_num = int(auto_text.split()[-1])
            return auto_num
        
        # Otherwise use manual
        return manual_num
    
    def test_camera(self):
        """Test selected camera safely before starting"""
        if self.testing_camera:
            messagebox.showwarning("Testing", "Already testing a camera!")
            return
        
        camera_num = self.get_selected_camera()
        self.manual_camera_num = camera_num
        
        self.testing_camera = True
        self.test_btn.config(state=tk.DISABLED)
        self.status_label.config(text=f"Testing Camera {camera_num}...", fg="orange")
        self.root.update()
        
        # Run test in a separate thread to prevent freezing
        test_thread = threading.Thread(target=self._test_camera_thread, args=(camera_num,))
        test_thread.daemon = True
        test_thread.start()
    
    def _test_camera_thread(self, camera_num):
        """Test camera in background thread"""
        try:
            cap = cv2.VideoCapture(camera_num)
            
            # Set timeout for opening
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Try to read frames
            success = False
            for attempt in range(5):
                ret, frame = cap.read()
                if ret and frame is not None:
                    success = True
                    break
                time.sleep(0.2)
            
            cap.release()
            
            # Update UI from main thread
            self.root.after(0, self._test_camera_result, camera_num, success)
        except Exception as e:
            print(f"Error testing camera {camera_num}: {e}")
            self.root.after(0, self._test_camera_result, camera_num, False)
    
    def _test_camera_result(self, camera_num, success):
        """Show test results"""
        self.testing_camera = False
        self.test_btn.config(state=tk.NORMAL)
        
        if success:
            messagebox.showinfo("Test Successful", f"✅ Camera {camera_num} is working!\n\nYou can safely use this camera.")
            self.status_label.config(text=f"Status: Camera {camera_num} Test OK ✓", fg="green")
        else:
            messagebox.showerror("Test Failed", f"❌ Camera {camera_num} is not responding!\n\nTry another camera number or check the connection.")
            self.status_label.config(text=f"Status: Camera {camera_num} Test FAILED", fg="red")
            self.root.after(3000, lambda: self.status_label.config(text="Status: Ready", fg="#333"))
    
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
            camera_index = self.get_selected_camera()
            self.manual_camera_num = camera_index
            
            # Start camera with timeout protection
            try:
                self.cap = cv2.VideoCapture(camera_index)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # Test if camera opens
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
                self.camera_dropdown.config(state=tk.DISABLED)
                self.manual_dropdown.config(state=tk.DISABLED)
                
                # Update LED indicator
                self.update_led_indicator(camera_index)
                
                self.status_label.config(text=f"Status: Camera {camera_index} Running ✓", fg="green")
                self.update_frame()
            except Exception as e:
                self.cap = None
                self.running = False
                messagebox.showerror("Camera Error", f"Failed to open camera {camera_index}:\n{str(e)}\n\nTry testing the camera first!")
                self.status_label.config(text="Status: Camera Failed", fg="red")
    
    def stop_camera(self):
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
        self.camera_dropdown.config(state="readonly")
        self.manual_dropdown.config(state="readonly")
        self.video_label.config(image="")
        self.camera_name_display.config(text="")
        
        # Update LED indicator
        self.update_led_indicator()
        
        self.status_label.config(text="Status: Camera Stopped", fg="red")
    
    def toggle_virtual_camera(self):
        """Toggle virtual camera on/off"""
        if not VIRTUAL_CAM_AVAILABLE:
            messagebox.showerror("Error", "pyvirtualcam is not installed!\n\nRun: pip install pyvirtualcam")
            return
        
        if self.virtual_cam_active:
            self.stop_virtual_camera()
        else:
            self.start_virtual_camera()
    
    def start_virtual_camera(self):
        """Start streaming to virtual camera"""
        try:
            if not VIRTUAL_CAM_AVAILABLE:
                raise Exception("pyvirtualcam not installed")
            
            # Create virtual camera with standard resolution
            self.vcam = pyvirtualcam.Camera(width=self.VCAM_WIDTH, height=self.VCAM_HEIGHT, fps=30)
            self.virtual_cam_active = True
            self.vcam_btn.config(text="🌐 Disable Virtual Camera", bg="#4CAF50")
            self.vcam_status.config(text="🟢 ACTIVE", fg="green")
            self.status_label.config(text="Virtual Camera ACTIVE - Stream to OBS/Discord/Websites", fg="green")
            messagebox.showinfo("Success", "✅ Virtual Camera is now ACTIVE!\n\nYou can now use this camera in:\n• OBS Studio\n• Discord\n• Websites\n• Any app that uses camera\n\nAll effects are applied!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start virtual camera:\n{str(e)}\n\nMake sure pyvirtualcam is installed:\npip install pyvirtualcam")
            self.virtual_cam_active = False
    
    def stop_virtual_camera(self):
        """Stop virtual camera stream"""
        try:
            if self.vcam:
                self.vcam.close()
                self.vcam = None
            self.virtual_cam_active = False
            self.vcam_btn.config(text="🌐 Enable Virtual Camera", bg="#9C27B0")
            self.vcam_status.config(text="🔴 INACTIVE", fg="red")
            self.status_label.config(text="Status: Virtual Camera Stopped", fg="orange")
        except Exception as e:
            print(f"Error stopping virtual camera: {e}")
    
    def set_effect(self, effect):
        self.current_effect = effect
    
    def apply_effect(self, frame):
        """Apply selected effect to frame"""
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
    
    def resize_frame(self, frame, width, height):
        """Resize frame while maintaining aspect ratio"""
        h, w = frame.shape[:2]
        aspect = w / h
        
        # Calculate new dimensions
        if aspect > (width / height):
            new_w = width
            new_h = int(width / aspect)
        else:
            new_h = height
            new_w = int(height * aspect)
        
        # Resize frame
        frame = cv2.resize(frame, (new_w, new_h))
        
        # Create canvas with padding
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        y_offset = (height - new_h) // 2
        x_offset = (width - new_w) // 2
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = frame
        
        return canvas
    
    def update_frame(self):
        if self.running and self.cap:
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    # Apply effects
                    frame = self.apply_effect(frame)
                    
                    # Prepare frame for virtual camera (640x480)
                    vcam_frame = self.resize_frame(frame, self.VCAM_WIDTH, self.VCAM_HEIGHT)
                    
                    # Send to virtual camera if active
                    if self.virtual_cam_active and self.vcam:
                        try:
                            # Convert BGR to RGB for virtual camera
                            frame_rgb = cv2.cvtColor(vcam_frame, cv2.COLOR_BGR2RGB)
                            self.vcam.send(frame_rgb)
                        except Exception as e:
                            print(f"Error sending frame to virtual camera: {e}")
                    
                    # Prepare frame for display (720x540)
                    display_frame = self.resize_frame(frame, self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)
                    
                    # Convert to PIL format for display
                    cv2image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(cv2image)
                    imgtk = ImageTk.PhotoImage(image=img)
                    
                    self.video_label.imgtk = imgtk
                    self.video_label.config(image=imgtk)
                    
                    # Update camera name display on video
                    vcam_text = " 🌐 STREAMING" if self.virtual_cam_active else ""
                    self.camera_name_display.config(text=f"📷 {self.camera_name}{vcam_text}")
                else:
                    # Camera disconnected
                    self.running = False
                    self.status_label.config(text="Status: Camera Disconnected!", fg="red")
                    self.stop_camera()
                    messagebox.showerror("Camera Error", "Camera was disconnected!")
                    return
            except Exception as e:
                print(f"Frame update error: {e}")
                self.running = False
                self.stop_camera()
                return
            
            self.root.after(30, self.update_frame)
    
    def take_snapshot(self):
        if self.running and self.cap:
            try:
                ret, frame = self.cap.read()
                if ret:
                    frame = self.apply_effect(frame)
                    cv2.imwrite("snapshot.jpg", frame)
                    self.status_label.config(text="Status: Snapshot saved as 'snapshot.jpg' ✓", fg="blue")
                    self.root.after(3000, lambda: self.status_label.config(text=f"Status: Camera {self.selected_camera} Running ✓", fg="green"))
            except Exception as e:
                messagebox.showerror("Snapshot Error", f"Failed to save snapshot:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root)
    root.mainloop()
