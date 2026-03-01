# Test videos for EngageIQ Flight Deck

Use yawning or drowsy face videos to test the PerceptionAgent.

## Video format

- **Formats:** MP4, AVI, MOV, WebM, MKV
- **Recommended:** MP4 (H.264) — best compatibility
- **Max size:** 100MB
- **Content:** Face visible, preferably front-facing. Yawning or drowsy footage triggers fatigue detection.

## Where to get test videos

1. **NTHU Drowsy Driver Detection Dataset** — publicly available, contains drowsy face clips  
   - https://drive.google.com/file/d/1_Cq-MG3HYKpomDXNyHHnmCFzZ6FN3YJf/view  
   - Or search for "NTHU Drowsy Driver dataset"

2. **UTA Real-Life Drowsiness Dataset** — real-world drowsiness videos  
   - Search for "UTA drowsiness dataset"

3. **Record yourself** — use your webcam to record a short clip with yawns or closed eyes

4. **Stock footage** — search "drowsy driver" or "yawning face" on stock video sites (check licenses)

## How to use

1. Start the backend and frontend
2. Open the **Simulator** panel (right side)
3. Click **Upload video** and select your MP4/AVI/MOV file
4. The PerceptionAgent will read frames from the video instead of the camera (loops when finished)
5. Click **Clear** to switch back to live camera
