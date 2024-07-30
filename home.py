# Python In-built packages
from pathlib import Path
from pydoc import Helper
import PIL
import io
import sqlite3
from datetime import datetime
import pytz

# External packages
import streamlit as st
import cv2
import av
import numpy as np
import PIL.Image as Image
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration, VideoProcessorBase
from ultralytics import YOLO
import settings

# Initialize SQLite database
conn = sqlite3.connect('detection_tea.db', check_same_thread=False)
conn.execute('''CREATE TABLE IF NOT EXISTS detections
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp TEXT,
              image BLOB)''')
conn.commit()

# Function to check login credentials
def check_login(username, password):
    return username == "admin" and password == "123"

def save_detection(image):
    try:
        st.write("Starting to save detection")

        if not isinstance(image, PIL.Image.Image):
            raise ValueError("The provided image is not a valid PIL Image.")
          
        timezone = pytz.timezone('Asia/Jakarta')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.write("Timestamp created:", timestamp)

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        st.write("Image converted to byte array")

        conn.execute("INSERT INTO detections (timestamp, image) VALUES (?, ?)", (timestamp, img_byte_arr))
        conn.commit()
        st.success("Detection saved successfully.")
    except sqlite3.Error as e:
        st.error(f"Failed to save detection to the database: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")


def load_detection_history():
    try:
        st.write("Loading detection history...")
        c = conn.cursor()
        c.execute("SELECT id, timestamp, image FROM detections ORDER BY timestamp DESC")
        history = c.fetchall()
        st.write(f"Loaded {len(history)} records from the database.")
        return history
    except sqlite3.Error as e:
        st.error(f"Failed to load detection history: {e}")
        return []


# Function to delete all detection history
def delete_all_detections():
    c = conn.cursor()
    c.execute("DELETE FROM detections")
    conn.commit()

# Model class for object detection
class VideoTransformer(VideoProcessorBase):
    def __init__(self):
        self.model = YOLO(settings.DETECTION_MODEL)
        self.confidence = 0.3

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        
        # Perform object detection
        results = self.model(img)
        
        # Draw bounding boxes on the frame
        for r in results:
            boxes = r.boxes
            for box in boxes:
                b = box.xyxy[0].cpu().numpy()  # get box coordinates in (top, left, bottom, right) format
                c = box.cls
                conf = box.conf.item()
                if conf >= self.confidence:
                    x1, y1, x2, y2 = map(int, b)
                    label = f"{self.model.names[int(c)]} {conf:.2f}"
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(img, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# Login interface
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Login Website Deteksi Kematangan Kelapa Sawit")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if check_login(username, password):
            st.session_state.logged_in = True
            st.success("Login successful")
        else:
            st.error("Invalid username or password")
else:
    # Setting page layout
    st.set_page_config(
        page_title="Object Detection using YOLOv8",
        page_icon="🍃",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar menu
    st.sidebar.image('images/icon.png', width=200)
    st.sidebar.header("Navigation")
    menu = st.sidebar.selectbox("Select a page:", ["Home", "Detection", "Detection History"])

    if menu == "Home":
        # Main page heading
        st.title("Selamat datang di Aplikasi Deteksi Kematangan Tandan Buah Kelapa Sawit!")
        col1, col2 = st.columns(2)

        with col1:
            st.image("images/klpsawit.jpg", use_column_width=True)
        
        with col2:
            st.image("images/sawit.jpg", use_column_width=True)

        st.write("""
            Aplikasi ini memungkinkan Anda untuk melakukan deteksi kematangan kelapa sawit menggunakan model YOLOv8. Mendeteksi kematangan kelapa sawit sulit karena beberapa faktor.
            Pertama, variasi warna buah seringkali tidak konsisten, sehingga warna tidak selalu menjadi indikator yang jelas dari kematangan. 
            Kedua, perubahan fisik antara buah yang belum matang dan matang seringkali sangat halus dan sulit dilihat dengan mata telanjang. 
            Ketiga, faktor lingkungan seperti cuaca dan kondisi tanah mempengaruhi kematangan buah secara tidak merata, membuat penilaian menjadi lebih kompleks. 
            Selain itu, teknologi deteksi canggih seperti pencitraan spektral yang dapat membantu dalam identifikasi kematangan memerlukan biaya tinggi dan keahlian khusus.
            Akhirnya, menentukan waktu yang tepat untuk panen sangat penting untuk kualitas minyak, tetapi ini memerlukan pengalaman dan pengetahuan mendalam. 
            Solusi untuk tantangan ini termasuk penggunaan teknologi yang lebih baik, pelatihan petani, dan penelitian lebih lanjut.
        """)
        st.title("Tingkat Kematangan Tandan Kelapa Sawit")
        st.write(""" 
        Kelapa sawit, tanaman tropis yang dikenal karena minyaknya yang bernilai tinggi, 
        mengalami tahap kematangan yang berbeda yang secara signifikan memengaruhi kualitas dan kuantitas minyak yang dihasilkan. 
        Memahami tingkat kematangan mentah, setengah matang, 
        dan matang sangat penting dalam memilih tandan buah segar yang tepat untuk berbagai proses pengolahan minyak sawit.
        """)
        # Using columns layout for images and descriptions
        col3, col4 = st.columns([1, 2])
        
        with col3:
            st.image("images/kurangmasak.jpg", caption="kelapa sawit kurang masak", use_column_width=True)
        with col4:
            st.write("""
            ### Kurang Masak
            Pada tahap ini, tandan buah kelapa sawit masih berwarna ungu gelap dan buahnya keras, 
            dengan kandungan minyak yang sangat rendah sehingga belum optimal untuk diproses.
            Umur tandan ini biasanya berkisar antara 5-15 minggu setelah penyerbukan, dan beratnya sekitar 2-5 kg per tandan.
            Buah kurang masak belum menghasilkan minyak dengan jumlah dan kualitas yang optimal.
            """)
        
        col5, col6 = st.columns([1, 2])
        
        with col5:
            st.image("images/sawitmatang.jpg", caption="kelapa sawit masak", use_column_width=True)
        with col6:
            st.write("""
            ### Masak
            Tandan buah kelapa sawit yang masak berwarna oranye kemerahan, mudah lepas dari tandan, dan memiliki kandungan minyak optimal. 
            Umurnya berkisar antara 21-24 minggu setelah penyerbukan, dengan berat sekitar 20-30 kg per tandan.
            Buah masak ini ideal untuk diproses menjadi minyak sawit dan produk turunannya karena menghasilkan 
            minyak berkualitas tinggi dalam jumlah maksimal.
            """)

        col7, col8 = st.columns([1, 2])
        
        with col7:
            st.image("images/sawitterlalu.jpg", caption="kelapa sawit terlalu masak", use_column_width=True)
        with col8:
            st.write("""
            ### Terlalu Masak
            Pada tahap terlalu masak, tandan buah kelapa sawit mulai menurun kualitasnya, buahnya mungkin berjatuhan dan warnanya lebih gelap,  
            dengan kandungan minyak yang menurun. Umurnya lebih dari 24 minggu setelah penyerbukan, dan beratnya sekitar 20-30 kg per tandan.
            Buah ini sebaiknya segera dipanen dan diproses untuk mencegah penurunan kualitas minyak.
            """)

    elif menu == "Detection":
        # Main page heading
        st.title("Deteksi Kematangan Tandan Kelapa Sawit")
        st.sidebar.header("ML Model Config")

        confidence = float(st.sidebar.slider("Select Model Confidence (%)", 25, 100, 40)) / 100
        model_path = Path(settings.DETECTION_MODEL)

        # Load Pre-trained ML Model
        try:
            model = YOLO(model_path)
        except Exception as ex:
            st.error(f"Unable to load model. Check the specified path: {model_path}")
            st.error(ex)

        st.sidebar.header("Image/Webcam Config")
        source_radio = st.sidebar.radio("Select Source", settings.SOURCES_LIST)

        source_img = None
        # If image is selected
        if source_radio == settings.IMAGE:
            source_img = st.sidebar.file_uploader(
                "Choose an image...", type=("jpg", "jpeg", "png", 'bmp', 'webp'))

            col1, col2 = st.columns(2)

            with col1:
                try:
                    if source_img is None:
                        default_image_path = str(settings.DEFAULT_IMAGE)
                        default_image = PIL.Image.open(default_image_path)
                        st.image(default_image_path, caption="Default Image", use_column_width=True)
                    else:
                        uploaded_image = PIL.Image.open(source_img)
                        st.image(source_img, caption="Uploaded Image", use_column_width=True)
                except Exception as ex:
                    st.error("Error occurred while opening the image.")
                    st.error(ex)

            with col2:
                if source_img is None:
                    default_detected_image_path = str(settings.DEFAULT_DETECT_IMAGE)
                    default_detected_image = PIL.Image.open(default_detected_image_path)
                    st.image(default_detected_image_path, caption='Detected Image', use_column_width=True)
                else:
                    if st.sidebar.button('Detect Objects', key='detect_button'):
                        res = model.predict(uploaded_image, conf=confidence)
                        boxes = res[0].boxes
                        res_plotted = res[0].plot()[:, :, ::-1]
                        detected_image = Image.fromarray(res_plotted)
                        st.image(detected_image, caption='Detected Image', use_column_width=True)
                        
                        # Save detection result to database
                        try:
                            st.write("Saving detection result to database...")
                            save_detection(detected_image)
                            st.write("Detection result saved.")
                        except Exception as ex:
                            st.error("Failed to save detection result.")
                            st.error(ex)

                        try:
                            with st.expander("Detection Results"):
                                for box in boxes:
                                    st.write(box.data)
                        except Exception as ex:
                            st.write("No image is uploaded yet!")

        elif source_radio == settings.VIDEO:
            Helper.play_stored_video(confidence, model)

        elif source_radio == settings.WEBCAM:
            st.header("WebRTC Object Detection")
            
            # Define the VideoTransformer class
            class VideoTransformer(VideoProcessorBase):
                def __init__(self):
                    self.model = YOLO(settings.DETECTION_MODEL)
                    self.confidence = 0.3
                
                def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
                    img = frame.to_ndarray(format="bgr24")
            
                    # Perform object detection
                    results = self.model(img)
                    st.write("Results obtained")  # Debugging line
                    
                    # Draw bounding boxes on the frame
                    for r in results:
                        boxes = r.boxes
                        for box in boxes:
                            b = box.xyxy[0].cpu().numpy()  # get box coordinates in (top, left, bottom, right) format
                            c = box.cls
                            conf = box.conf.item()
                            if conf >= self.confidence:
                                x1, y1, x2, y2 = map(int, b)
                                label = f"{self.model.names[int(c)]} {conf:.2f}"
                                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.putText(img, label, (x1, y1 - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
                    return av.VideoFrame.from_ndarray(img, format="bgr24")

            webrtc_ctx = webrtc_streamer(
                key="object-detection",
                mode=WebRtcMode.SENDRECV,
                rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
                video_processor_factory=VideoTransformer,
                async_processing=True,
            )

            if webrtc_ctx.video_processor:
                webrtc_ctx.video_processor.confidence = confidence
            else:
                st.error("Please select a valid source type!")

    elif menu == "Detection History":
        # Main page heading
        st.title("Detection History")

        # Displaying history
        history = load_detection_history()
        for id, timestamp, image in history:
            image = Image.open(io.BytesIO(image))
            with st.expander(f"ID: {id}, Time: {timestamp}"):
                st.image(image, caption="Detected Image", use_column_width=False, width=500)

        # Delete all history
        if st.button('Delete All History'):
            delete_all_detections()
            st.success("All detection history has been deleted.")
            # Update the history display
            st.experimental_rerun()

    # Logout button in sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()
