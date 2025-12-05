import os
import json
import streamlit as st
import numpy as np
import tensorflow as tf
from groq import Groq
from docx import Document
from docx.shared import Inches
import tempfile
from PIL import Image


def Home(lang_code):

    # ------------ TRANSLATIONS ------------
    translations = {
        "en": {
            "title": "🌱 Welcome to Tomato Detection System!",
            "subheader": "Your ultimate companion for tomato planting, care, and disease management.",
            "features": """  
                Use the Tomato System to:  
                - Detect and diagnose diseases in tomato plants.  
                - Get expert advice and treatment options with Planty AI.  
                - Shop for high-quality fertilizers, pesticides, and seeds.  
            """,
            "offer": "🌟 Special Offer for Tomato Lovers!",
            "buy_seeds": "Buy Premium Tomato Seeds Now!",
            "seed_benefits": """  
                - High yield and disease resistance.  
                - Suitable for all climates.  
                - Special 20% discount for a limited time!  
            """,
            "why_choose": """  
                🌟 Why choose our seeds?  
                - Tested and trusted by farmers worldwide.  
                - Supports sustainable and organic farming practices.  
                - Guaranteed freshness and germination rates.  
            """,
            "footer_text": "We are committed to helping farmers and gardeners maintain healthy tomato crops.\nIf you have any questions or need further assistance, feel free to reach out.\n**Happy farming! 🌱**",
            "shop": "👉 Visit Our Shop",
            "disease_diagnosis": "Tomato Disease Diagnosis",
            "upload_prompt": "📤 Upload an image of the tomato leaf",
            "invalid_image": "❌ Invalid Image",
            "low_quality": "### ⚠️ Low Image Quality",
            "upload_clear": "Please upload a clearer image for better diagnosis.",
            "upload_valid_image": "Please upload a valid image of a tomato leaf for diagnosis.",
            "disease_detected": "✅ Disease Detected:",
            "confidence": "Confidence:",
            "solution_info": "### Information and Solution:",
            "upload_image": "Uploaded Image",
            "generate_doc": "📄 Generate Word Report",
            "download_report": "📥 Download Diagnosis Report",
            "title_doc": "🍅 Tomato Disease Diagnosis Report",

            # class translations
            "Bacterial_spot": "Bacterial Spot",
            "Early_blight": "Early Blight",
            "Late_blight": "Late Blight",
            "Leaf_Mold": "Leaf Mold",
            "No_tomato_leaf": "No Tomato Leaf",
            "Septoria_leaf_spot": "Septoria Leaf Spot",
            "Spider_mites_Two-spotted_spider_mite": "Spider Mites (Two-Spotted)",
            "Target_Spot": "Target Spot",
            "Tomato_Yellow_Leaf_Curl_Virus": "Tomato Yellow Leaf Curl Virus",
            "Tomato_mosaic_virus": "Tomato Mosaic Virus",
            "Healthy": "Healthy",
            "powdery_mildew": "Powdery Mildew",

            "provide_info": "Provide detailed info, treatment solutions, and pesticide recommendations for {predicted_class}.",
            "footer_title": "🍃 Thank You for Using Our System!",
            "footer_description": """
            We help farmers maintain healthy tomato crops worldwide.  
            """,
            "footer_closing": "🌱 **Happy Farming!**",
        }
    }

    t = translations[lang_code]

    # ------------ HEADER UI ------------
    st.title(t["title"])
    st.subheader(t["subheader"])
    st.write(t["features"])

    st.markdown("---")

    # ------------ LOAD MODEL ------------
    model = tf.keras.models.load_model("tomato_disease_model.h5")

    # Class list (order MUST match training)
    classes = [
        "Bacterial_spot", "Early_blight", "Late_blight", "Leaf_Mold",
        "No_tomato_leaf", "Septoria_leaf_spot",
        "Spider_mites_Two-spotted_spider_mite", "Target_Spot",
        "Tomato_Yellow_Leaf_Curl_Virus", "Tomato_mosaic_virus",
        "Healthy", "powdery_mildew"
    ]

    # ------------ FIXED PREPROCESS FUNCTION ------------
    def preprocess_image(img):
        # Convert RGBA → RGB (this fixes your original crash)
        if img.mode != "RGB":
            img = img.convert("RGB")

        img = img.resize((128, 128))
        arr = np.array(img).astype("float32") / 255.0
        arr = np.expand_dims(arr, axis=0)
        return arr

    # ------------ UPLOAD UI ------------
    st.title(t["disease_diagnosis"])
    uploaded = st.file_uploader(t["upload_prompt"], type=["jpg", "jpeg", "png"])

    if uploaded:
        st.image(uploaded, caption=t["upload_image"], width=400)

        image = Image.open(uploaded)
        processed = preprocess_image(image)

        # ------------ PREDICTION ------------
        prediction = model.predict(processed)
        probs = prediction.flatten()

        idx = int(np.argmax(probs))
        predicted_class = classes[idx]
        confidence = float(probs[idx]) * 100.0

        # Debug info (super helpful)
        st.write("### DEBUG")
        st.write("Probabilities:", np.round(probs, 4).tolist())
        st.write("Predicted class:", predicted_class)
        st.write(f"Confidence: {confidence:.2f}%")

        # ------------ DECISION LOGIC ------------
        # Strong "no leaf" prediction
        if predicted_class == "No_tomato_leaf" and confidence >= 55:
            st.error(t["invalid_image"])
            st.write(t["upload_valid_image"])
            return

        # Uncertain model output
        if confidence < 40:
            st.warning(t["low_quality"])
            st.write(t["upload_clear"])
            return

        # VALID PREDICTION
        st.success(f"{t['disease_detected']} {t[predicted_class]}")
        st.write(f"{t['confidence']} {confidence:.2f}%")

        # ------------ GROQ API CALL ------------
        try:
            working_dir = os.path.dirname(os.path.abspath(__file__))
            config = json.load(open(f"{working_dir}/config.json"))
            os.environ["GROQ_API_KEY"] = config["GROQ_API_KEY"]

            client = Groq()

            msg = [
                {"role": "system", "content": "You are an expert tomato disease specialist."},
                {"role": "user", "content": t["provide_info"].format(predicted_class=predicted_class)},
            ]

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=msg
            )
            solution_info = response.choices[0].message.content.strip()

            st.write(t["solution_info"])
            st.write(solution_info)

        except Exception as e:
            st.error(f"Groq Error: {e}")

        # ------------ WORD REPORT BUTTON ------------
        if st.button(t["generate_doc"]):
            doc = Document()
            doc.add_heading(t["title_doc"], level=1)

            doc.add_paragraph(f"{t['disease_detected']} {predicted_class}")

            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
            image.save(temp_img)
            doc.add_picture(temp_img, width=Inches(4.5))

            doc.add_heading(t["solution_info"], level=2)
            doc.add_paragraph(solution_info)

            temp_doc = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
            doc.save(temp_doc)

            with open(temp_doc, "rb") as file:
                st.download_button(t["download_report"], file, "Diagnosis_Report.docx")

    else:
        st.write(t["upload_valid_image"])

    # ------------ FOOTER ------------
    st.markdown("---")
    st.header(t["offer"])

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(t["buy_seeds"])
        st.write(t["seed_benefits"])
        st.write(t["why_choose"])
        st.write(f"### {t['shop']}")

    with col2:
        st.image("./image/tomato_seeds.png", caption=t["buy_seeds"], width=250)

    st.markdown(f"## {t['footer_title']}")
    st.write(t["footer_description"])
    st.markdown(f"#### {t['footer_closing']}")
    st.markdown("---")
