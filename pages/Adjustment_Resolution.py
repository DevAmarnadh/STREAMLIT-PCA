import streamlit as st
from io import BytesIO
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from scripts.pca_compression import PCACompressor
from scripts.utils import *

A4 = (210, 297)  # Width x Height in millimeters

def convert_to_pdf(image, initial_file_name, adjusted_width_input, adjusted_height_input):
    buffer_pdf = BytesIO()
    pdf_path = f"{initial_file_name}_pca_compressed_adjusted.pdf"

    # Create a PDF file with the adjusted compressed image
    pdf = canvas.Canvas(buffer_pdf, pagesize=A4)

    # Get the page size
    page_width, page_height = A4

    # Calculate scaling to fit the entire image within the PDF
    scale_x = page_width / adjusted_width_input
    scale_y = page_height / adjusted_height_input
    scale = min(scale_x, scale_y)

    # Calculate the position to center the image within the PDF
    offset_x = (page_width - adjusted_width_input * scale) / 2
    offset_y = (page_height - adjusted_height_input * scale) / 2

    # Draw the image on the PDF with the correct scaling and position
    pdf.drawInlineImage(image, offset_x, offset_y, adjusted_width_input * scale, adjusted_height_input * scale)

    pdf.save()

    st.download_button(
        "Download PDF",
        data=buffer_pdf.getvalue(),
        file_name=pdf_path,
        key="download_button_pdf"
    )

st.set_page_config(page_title="PCA", page_icon=":fire:")

st.markdown("# Adjust the Resolution")
st.sidebar.header("Instructions")
st.sidebar.markdown(
    """
    Please upload the image and enter the image quality. Then click the button to see the results!
    """
)

uploaded_image = st.file_uploader("Upload your image")

if uploaded_image is not None:
    st.markdown("<style>div.Widget.row-widget.stRadio { display: none; }</style>", unsafe_allow_html=True)

    quality_input = st.slider("Select Image Quality (1-95)", min_value=1, max_value=100, value=85)  # Default quality is set to 85

    if 'clicked' not in st.session_state:
        st.session_state.clicked = False

    original_size_kb = 0  # Initialize here
    compressed_size_kb = 0  # Initialize here

    def click_button():
        st.session_state.clicked = True

    st.button("Compress", on_click=click_button)

    if st.session_state.clicked and uploaded_image is not None:
        image_array = load_image_into_array(uploaded_image)
        if image_array is None:
            st.write("That is an invalid image file. Please try again.")
        else:
            compressor = PCACompressor(image_array)

            # Set a fixed number of principal components
            number = 5000  # Replace with your desired value

            compressed_array = compressor.compress(number)
            compressed_image = load_array_into_image(compressed_array)

            col1, col2, col3 = st.columns(3)

            # Displaying original image with information
            with col1:
                st.image(uploaded_image, caption="Original image")
                original_info = compressor.get_original_info()
                st.write(f"Original Height: {original_info['Height']} pixels")
                st.write(f"Original Width: {original_info['Width']} pixels")
                st.write(f"Original Resolution: {original_info['Resolution']} pixels")

            # Displaying information about Adjusted Compressed image in col2
            with col2:
                st.image(compressed_image, caption="Adjusted Compressed image")
                compressed_info = compressor.get_compressed_info()
                st.write(f"Compressed Height: {compressed_info['Height']} pixels")
                st.write(f"Compressed Width: {compressed_info['Width']} pixels")
                st.write(f"Compressed Resolution: {compressed_info['Resolution']} pixels")

            # Additional inputs for selecting resolution preset in col3
            with col3:
                resolution_presets = {
                    "144p": (256, 144),
                    "240p": (426, 240),
                    "360p": (640, 360),
                    "480p": (854, 480),
                    "720p": (1280, 720),
                    "1080p": (1920, 1080),
                    "2k": (2560, 1440),
                    "4k": (3840, 2160),
                }

                selected_resolution = st.selectbox("Select Resolution Preset", list(resolution_presets.keys()))

                # Get selected resolution dimensions
                adjusted_width_input, adjusted_height_input = resolution_presets[selected_resolution]

                # Adjusting height and width
                adjusted_resolution_input = adjusted_height_input * adjusted_width_input

                st.write(f"Adjusted Compressed Height: {adjusted_height_input:.2f} pixels")
                st.write(f"Adjusted Compressed Width: {adjusted_width_input:.2f} pixels")
                st.write(f"Adjusted Compressed Resolution: {adjusted_resolution_input:.2f} pixels")

                # Resize the compressed image with adjusted height and width
                compressed_image_resized = resize_image(compressed_image, (adjusted_width_input, adjusted_height_input))
                st.image(compressed_image_resized, caption="Adjusted Compressed image")

                compressed_info['Height'] = adjusted_height_input
                compressed_info['Width'] = adjusted_width_input
                compressed_info['Resolution'] = adjusted_resolution_input

                # Displaying sizes
                original_size_bytes = len(uploaded_image.read())
                original_size_kb = original_size_bytes / 1024  # Convert to KB

                buffer = BytesIO()

                # Convert quality to int
                quality = int(quality_input)

                quality = max(1, min(quality, 95))  # Ensure quality is within a valid range

                compressed_image_resized.save(buffer, format="JPEG", quality=quality)
                compressed_size_bytes = len(buffer.getvalue())
                compressed_size_kb = compressed_size_bytes / 1024  # Convert to KB

                st.write(f"Original Size: {original_size_kb:.2f} KB")
                st.write(f"Compressed Size: {compressed_size_kb:.2f} KB")

                initial_file_name = uploaded_image.name.split(".")[0]

                # Add logic for downloading adjusted compressed image
                download_button_label = f"Download adjusted compressed image ({compressed_info['Height']}x{adjusted_width_input})"
                st.download_button(
                    download_button_label,
                    data=buffer.getvalue(),
                    file_name=f"{initial_file_name}_pca_compressed_adjusted.jpg",
                    key="download_button_adjusted"
                )

                # Add logic for converting adjusted compressed image to PDF
                pdf_button_label = f"Convert adjusted compressed image to PDF"
                st.button(pdf_button_label, on_click=convert_to_pdf, args=(compressed_image_resized, initial_file_name, adjusted_width_input, adjusted_height_input))

    else:
        st.write("Please upload an image first.")