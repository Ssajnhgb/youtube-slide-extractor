import streamlit as st
import cv2
import os
import yt_dlp
from pptx import Presentation
from pptx.util import Inches
import imagehash
from PIL import Image

st.title("YouTube Video Slide Extractor")

url = st.text_input("Enter YouTube Video URL:")

if st.button("Process Video"):
    if url:
        try:
            # Step 1: Download video using yt-dlp
            st.write("Downloading video... this may take a minute.")
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': 'video.mp4',
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Step 2: Extract Slides
            st.write("Extracting slides...")
            cam = cv2.VideoCapture("video.mp4")
            prs = Presentation()
            last_hash = None
            
            count = 0
            while True:
                ret, frame = cam.read()
                if not ret:
                    break
                
                # Check every 30 frames (approx 1 second) to save speed
                if count % 30 == 0:
                    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    curr_hash = imagehash.phash(img)
                    
                    if last_hash is None or curr_hash - last_hash > 15:
                        # Slide changed! Add to PPT
                        cv2.imwrite("temp_slide.jpg", frame)
                        slide = prs.slides.add_slide(prs.slide_layouts[6])
                        slide.shapes.add_picture("temp_slide.jpg", 0, 0, width=prs.slide_width)
                        last_hash = curr_hash
                
                count += 1
            
            cam.release()
            prs.save("presentation.pptx")
            
            # Step 3: Provide Download
            with open("presentation.pptx", "rb") as f:
                st.download_button("Download PPTX", f, file_name="lecture_slides.pptx")
            
            # Cleanup
            os.remove("video.mp4")
            if os.path.exists("temp_slide.jpg"):
                os.remove("temp_slide.jpg")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a URL.")
