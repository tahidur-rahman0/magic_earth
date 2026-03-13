import cv2
import mediapipe as mp
import numpy as np
import time
import random
import os
import urllib.request
import math

# Download the model if it doesn't exist
MODEL_PATH = 'hand_landmarker.task'
if not os.path.exists(MODEL_PATH):
    print("Downloading MediaPipe Hand Landmarker model...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        MODEL_PATH
    )
    print("Download complete!")

# Initialize MediaPipe Tasks API
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)

landmarker = HandLandmarker.create_from_options(options)

# Particle class for complex magic effect
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # White and bright silver/cyan colors (BGR)
        shade = random.randint(200, 255)
        self.color = (255, shade, shade) 
        self.radius = random.uniform(2, 6)
        self.life = 1.0
        # Give them some swirling velocity
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 12)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.decay = random.uniform(0.02, 0.08)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        # Add slight gravity or drift
        self.vy -= 0.2
        self.radius -= 0.1
        self.life -= self.decay

    def draw(self, img):
        if self.life > 0 and self.radius > 0:
            overlay = img.copy()
            r = int(self.radius)
            # Core
            cv2.circle(overlay, (int(self.x), int(self.y)), r, (255, 255, 255), -1)
            # Outer glow
            cv2.circle(overlay, (int(self.x), int(self.y)), r + 4, self.color, 1)
            
            alpha = max(0, self.life)
            x1, y1 = max(0, int(self.x - r - 5)), max(0, int(self.y - r - 5))
            x2, y2 = min(img.shape[1], int(self.x + r + 5)), min(img.shape[0], int(self.y + r + 5))
            if x1 < x2 and y1 < y2:
                img[y1:y2, x1:x2] = cv2.addWeighted(overlay[y1:y2, x1:x2], alpha, img[y1:y2, x1:x2], 1 - alpha, 0)

particles = []
# Store previous core positions for trails
trail_history = [] 

print("Initializing camera. Press 'q' to exit.")

cap = cv2.VideoCapture(0)
frame_timestamp_ms = 0
frame_count = 0

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    image = cv2.flip(image, 1)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

    frame_timestamp_ms = int(time.time() * 1000)
    result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)

    h, w, c = image.shape
    frame_count += 1
    
    current_cores = []

    if result.hand_landmarks:
        for hand_landmarks in result.hand_landmarks:
            palm = hand_landmarks[9] # MIDDLE_FINGER_MCP
            px, py = int(palm.x * w), int(palm.y * h)
            current_cores.append((px, py))
            
            # Extract all fingertips
            tips = [4, 8, 12, 16, 20]
            tip_points = [(int(hand_landmarks[idx].x * w), int(hand_landmarks[idx].y * h)) for idx in tips]
            
            # 1. Draw mystical geometric rings around palm
            base_radius = 40
            pulsing = int(math.sin(frame_count * 0.2) * 10)
            
            # Inner bright core
            cv2.circle(image, (px, py), 15, (255, 255, 255), -1)
            # Spinning inner triangle
            pts = []
            for i in range(3):
                angle = frame_count * 0.1 + (i * 2 * math.pi / 3)
                tx = int(px + (base_radius - 10) * math.cos(angle))
                ty = int(py + (base_radius - 10) * math.sin(angle))
                pts.append([tx, ty])
            cv2.polylines(image, [np.array(pts, np.int32)], True, (255, 255, 255), 2)
            
            # Pulsing outer ring
            cv2.circle(image, (px, py), base_radius + pulsing, (200, 255, 255), 2)
            # Second dashed-like complex ring
            cv2.circle(image, (px, py), base_radius + 20 - pulsing, (255, 240, 240), 1)

            # 2. Draw white energy lines connecting all fingertips to the palm
            for tx, ty in tip_points:
                cv2.line(image, (px, py), (tx, ty), (255, 255, 255), 1)
                # Spawn particles at fingertips randomly
                if random.random() > 0.3:
                    for _ in range(3):
                        particles.append(Particle(tx, ty))
                # Highlight fingertip
                cv2.circle(image, (tx, ty), 6, (255, 255, 255), -1)
                
            # 3. Draw a magical web between the fingertips (constellation effect)
            for i in range(len(tip_points)-1):
                cv2.line(image, tip_points[i], tip_points[i+1], (200, 255, 255), 2)

            # Spawn palm particles
            for _ in range(5):
                particles.append(Particle(px, py))
                
    # Handle core trails
    trail_history.append(current_cores)
    if len(trail_history) > 15:
        trail_history.pop(0)
        
    # Draw trails for core energy
    for i in range(1, len(trail_history)):
        opacity = i / len(trail_history)
        thickness = max(1, int(opacity * 10))
        older_cores = trail_history[i-1]
        newer_cores = trail_history[i]
        
        # Connect identical hand indices if possible
        for j in range(min(len(older_cores), len(newer_cores))):
            pt1 = older_cores[j]
            pt2 = newer_cores[j]
            cv2.line(image, pt1, pt2, (255, 255, 255), thickness)

    # Update and render particles
    for p in reversed(particles):
        p.update()
        p.draw(image)
        if p.life <= 0 or p.radius <= 0:
            particles.remove(p)

    cv2.imshow('Magic Power Hands (Press "q" to exit)', image)
    
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
landmarker.close()
