import streamlit as st
import cv2
import os
import yt_dlp
from pptx import Presentation
from pptx.util import Inches
import imagehash
from PIL import Image

st.title("YouTube Video Slide Extractor")

# Options for the user
option = st.radio("Choose source:", ("YouTube URL", "Upload Video File (.mp4)"))

video_path = "video.mp4"
ready_to_process = False

if option == "YouTube URL":
    url = st.text_input("Enter YouTube Video URL:")
    if st.button("Download & Process"):
        if url:
            try:
                st.write("Downloading video... (Trying to bypass YouTube block)")
                # Added browser headers to bypass 403 Forbidden errors
                ydl_opts = {
                    'format': 'best[ext=mp4]',
                    'outtmpl': video_path,
                    'quiet': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'referer': 'https://www.google.com/',
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                ready_to_process = True
            except Exception as e:
                st.error(f"YouTube Blocked the download: {e}. Please use the 'Upload' option instead.")
        else:
            st.warning("Please enter a URL.")

else:
    uploaded_file = st.file_uploader("Upload your lecture video", type=["mp4"])
    if uploaded_file is not None:
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        ready_to_process = True
        if st.button("Process Uploaded Video"):
            pass # Button triggers the logic below

if ready_to_process:
    try:
        st.write("Extracting slides... this may take a few minutes.")
        cam = cv2.VideoCapture(video_path)
        prs = Presentation()
        last_hash = None
        count = 0
        
        # Progress bar for the user
        progress_bar = st.progress(0)
        total_frames = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))

        while True:
            ret, frame = cam.read()
            if not ret:
                break
            
            # Check every 60 frames (approx 2 seconds) to avoid duplicate slides
            if count % 60 == 0:
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                curr_hash = imagehash.phash(img)
                
                # If the image hash changed significantly, it's a new slide
                if last_hash is None or curr_hash - last_hash > 15:
                    cv2.imwrite("temp_slide.jpg", frame)
                    slide = prs.slides.add_slide(prs.slide_layouts[6])
                    slide.shapes.add_picture("temp_slide.jpg", 0, 0, width=prs.slide_width)
                    last_hash = curr_hash
                
                # Update progress
                if total_frames > 0:
                    progress_bar.progress(min(count / total_frames, 1.0))
            
            count += 1
        
        cam.release()
        prs.save("presentation.pptx")
        
        st.success("Extraction Complete!")
        with open("presentation.pptx", "rb") as f:
            st.download_button("Download PPTX", f, file_name="lecture_slides.pptx")
        
        # Cleanup files to keep the server clean
        if os.path.exists(video_path): os.remove(video_path)
        if os.path.exists("temp_slide.jpg"): os.remove("temp_slide.jpg")
            
    except Exception as e:
        st.error(f"Processing Error: {e}")
