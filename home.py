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
    # Translations Dictionary
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
            "generate_pdf": "📄 Generate PDF Report",
            "download_report": "📥 Download Diagnosis Report",
            "upload_image": "Uploaded Image",
            "Bacterial_spot": "Bacterial Spot",
            "Early_blight": "Early Blight",
            "Late_blight": "Late Blight",
            "Leaf_Mold": "Leaf Mold",
            "No_tomato_leaf": "No Tomato Leaf",
            "Septoria_leaf_spot": "Septoria Leaf Spot",
            "Spider_mites_Two-spotted_spider_mite": "Spider Mites (Two-Spotted Spider Mite)",
            "Target_Spot": "Target Spot",
            "Tomato_Yellow_Leaf_Curl_Virus": "Tomato Yellow Leaf Curl Virus",
            "Tomato_mosaic_virus": "Tomato Mosaic Virus",
            "Healthy": "Healthy",
            "powdery_mildew": "Powdery Mildew",
            "disease_info": "**Information:**",
            "treatment_solutions": "**Treatment Solutions:**",
            "pesticide_recommendations": "**Pesticide Recommendations:**",
            "provide_info": "Provide information, treatment solutions, and pesticide recommendations for {predicted_class} in tomatoes.",
            "footer_title": "🍃 Thank You for Using Our System!",
            "footer_description": """
            We are dedicated to helping farmers and gardeners maintain **healthy tomato crops**.  
            If you have any questions or need assistance, feel free to reach out.  
            """,
            "footer_closing": "🌱 **Happy Farming!**",
            "generate_doc": "📄 Generate Word Report",
            "download_report1": "📥 Download Diagnosis Report (Word)",
            "title_doc": "🍅 Tomato Disease Diagnosis Report",
        }
    }

    t = translations[lang_code]

    # Header
    st.title(t["title"])
    st.subheader(t["subheader"])
    st.write(t["features"])

    st.markdown("---")

    model = tf.keras.models.load_model('tomato_disease_model.h5')

    # Classes for diseases
    classes = [
        'Bacterial_spot', 'Early_blight', 'Late_blight', 'Leaf_Mold',
        'No_tomato_leaf', 'Septoria_leaf_spot',
        'Spider_mites_Two-spotted_spider_mite', 'Target_Spot',
        'Tomato_Yellow_Leaf_Curl_Virus', 'Tomato_mosaic_virus',
        'Healthy', 'powdery_mildew'
    ]

    # ---------------------------------------------
    # FIXED PREPROCESS FUNCTION (THE CAUSE OF ERROR)
    # ---------------------------------------------
    def preprocess_image(img):
        # Convert RGBA or anything weird → RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        img = img.resize((128, 128))

        img_array = np.array(img).astype("float32") / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        return img_array

    # Tomato Disease Diagnosis Section
    st.title(t["disease_diagnosis"])
    uploaded_file = st.file_uploader(t["upload_prompt"], type=["jpg", "jpeg", "png"])

    if uploaded_file:
        st.image(uploaded_file, caption=t['upload_image'], width=400)

        image = Image.open(uploaded_file)

        processed_image = preprocess_image(image)

        prediction = model.predict(processed_image)

        predicted_class_index = np.argmax(prediction, axis=1)[0]
        predicted_class = classes[predicted_class_index]
        confidence = np.max(prediction) * 100

        try:
            working_dir = os.path.dirname(os.path.abspath(__file__))
            config_data = json.load(open(f"{working_dir}/config.json"))
            GROQ_API_KEY = config_data["GROQ_API_KEY"]
            os.environ["GROQ_API_KEY"] = GROQ_API_KEY

            client = Groq()

            messages = [
                {"role": "system", "content": "You are an expert in tomato diseases and treatment solutions."},
                {"role": "user", "content": t['provide_info'].format(predicted_class=predicted_class)},
            ]

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages
            )
            solution_info = response.choices[0].message.content.strip()

            if predicted_class == "No_tomato_leaf":
                st.write(f"### {t['invalid_image']}")
                st.write(t["upload_valid_image"])

            elif 40 <= confidence <= 85:
                st.write(f"### {t['invalid_image']}")
                st.write(t["upload_valid_image"])

            elif confidence < 40:
                st.write(t["low_quality"])
                st.write(t["upload_clear"])

            else:
                st.write(f"### {t['disease_detected']} {t[predicted_class]}")
                st.write(f"{t['confidence']} {confidence:.2f}%")
                st.write(t["solution_info"])
                st.write(solution_info)

                # Generate DOCX Report
                if st.button(t["generate_doc"]):
                    doc = Document()
                    doc.add_heading(t["title_doc"], level=1)

                    doc.add_paragraph(f"**{t['disease_detected']}** {predicted_class}")

                    if image:
                        temp_image_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                        image.save(temp_image_path)
                        doc.add_picture(temp_image_path, width=Inches(4.5))

                    doc.add_heading(t["solution_info"], level=2)
                    doc.add_paragraph(solution_info)

                    temp_doc_path = tempfile.NamedTemporaryFile(delete=False, suffix=".docx").name
                    doc.save(temp_doc_path)

                    with open(temp_doc_path, "rb") as doc_file:
                        st.download_button(t["download_report"], doc_file, "Diagnosis_Report.docx")

        except Exception as e:
            st.error(f"Error: {e}")

    else:
        st.write(t["upload_valid_image"])

    st.markdown("---")
    st.header(t["offer"])
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(t["buy_seeds"])
        st.write(t["seed_benefits"])
        st.write(t["why_choose"])
        st.write(f"### {t['shop']}")

    with col2:
        ad_image = "./image/tomato_seeds.png"
        st.image(ad_image, caption=t["buy_seeds"], use_container_width=True)

    st.markdown(f"## {t['footer_title']}")
    st.write(t["footer_description"])
    st.markdown(f"#### {t['footer_closing']}")
    st.markdown("---")
