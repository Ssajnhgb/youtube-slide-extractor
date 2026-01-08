import streamlit as st
import cv2
import os
from pptx import Presentation
import imagehash
from PIL import Image
import tempfile

st.set_page_config(page_title="Lecture Extractor", layout="wide")
st.title("📊 Unlimited Video-to-PPT Extractor")

# The UI will now accept files up to 2GB because of the config file
uploaded_file = st.file_uploader("Upload Lecture Video (Up to 2GB)", type=["mp4", "mkv", "avi"])

if uploaded_file is not None:
    # Save the uploaded video to a temporary file
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    video_path = tfile.name

    if st.button("🚀 Start Unlimited Extraction"):
        try:
            cap = cv2.VideoCapture(video_path)
            prs = Presentation()
            last_hash = None
            slides_found = 0
            count = 0
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            progress_bar = st.progress(0)
            status = st.empty()

            # "Unlimited" loop: runs until the very last frame of the video
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Check every 60 frames (approx. every 2 seconds) for speed
                if count % 60 == 0:
                    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    curr_hash = imagehash.phash(img)
                    
                    # If the visual content changed, it's a new slide
                    if last_hash is None or curr_hash - last_hash > 12:
                        temp_img = f"slide_{slides_found}.jpg"
                        cv2.imwrite(temp_img, frame)
                        
                        slide = prs.slides.add_slide(prs.slide_layouts[6])
                        slide.shapes.add_picture(temp_img, 0, 0, width=prs.slide_width)
                        
                        last_hash = curr_hash
                        slides_found += 1
                        os.remove(temp_img)
                
                # Update UI periodically
                if count % 300 == 0:
                    progress_bar.progress(min(count / total_frames, 1.0))
                    status.text(f"Processed {count} frames... Found {slides_found} slides.")
                
                count += 1

            cap.release()
            prs.save("lecture_slides.pptx")
            
            st.success(f"Done! Extracted {slides_found} slides.")
            with open("lecture_slides.pptx", "rb") as f:
                st.download_button("📥 Download PowerPoint", f, file_name="lecture.pptx")

        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            if os.path.exists(video_path):
                os.remove(video_path)
