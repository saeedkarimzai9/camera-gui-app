import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import threading

class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera GUI - Easy Mode")
        self.root.geometry("800x700")
        self.root.configure(bg="#f0f0f0")
        
        # Camera variables
        self.cap = None
        self.running = False
        self.current_effect = "none"
        
        # Title
        title_label = tk.Label(root, text="📷 Camera Application", font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=10)
        
        # Video frame
        self.video_label = tk.Label(root, bg="black", width=600, height=400)
        self.video_label.pack(pady=10)
        
        # Control frame
        control_frame = tk.Frame(root, bg="#f0f0f0")
        control_frame.pack(pady=10)
        
        # Start/Stop buttons
        self.start_btn = tk.Button(control_frame, text="▶ Start Camera", command=self.start_camera, 
                                   bg="#4CAF50", fg="white", font=("Arial", 12), width=15)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = tk.Button(control_frame, text="⏹ Stop Camera", command=self.stop_camera, 
                                  bg="#f44336", fg="white", font=("Arial", 12), width=15, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        # Snapshot button
        self.snapshot_btn = tk.Button(control_frame, text="📸 Take Snapshot", command=self.take_snapshot, 
                                      bg="#2196F3", fg="white", font=("Arial", 12), width=15, state=tk.DISABLED)
        self.snapshot_btn.grid(row=0, column=2, padx=5)
        
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
        
    def start_camera(self):
        if not self.running:
            self.cap = cv2.VideoCapture(0)
            self.running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.snapshot_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Camera Running ✓", fg="green")
            self.update_frame()
    
    def stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.snapshot_btn.config(state=tk.DISABLED)
        self.video_label.config(image="")
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
                frame = cv2.resize(frame, (600, 400))
                frame = self.apply_effect(frame)
                
                # Convert to PIL format
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)
            
            self.root.after(30, self.update_frame)
    
    def take_snapshot(self):
        if self.running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                frame = self.apply_effect(frame)
                cv2.imwrite("snapshot.jpg", frame)
                self.status_label.config(text="Status: Snapshot saved as 'snapshot.jpg' ✓", fg="blue")
                self.root.after(3000, lambda: self.status_label.config(text="Status: Camera Running ✓", fg="green"))

if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root)
    root.mainloop()
