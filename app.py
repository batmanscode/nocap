import streamlit as st

import os
from zipfile import ZipFile
import io

st.set_page_config(page_title="nocap", page_icon="📝", initial_sidebar_state="auto")

st.title(":blue[nocap]")
st.write("### :blue[Making it a little easier to fine tune image models, no cap 🙂]")

st.write(
    """
    Write captions for your images and download a zip file you can fine tune Flux models with

    Fine tuning guide: [replicate.com/blog/fine-tune-flux-with-faces](https://replicate.com/blog/fine-tune-flux-with-faces)
    """
)
st.write("---")

# user uploads their folder here
uploaded_file = st.sidebar.file_uploader("Upload a folder of images", type="zip")

# Initialize session state variables if not already set
if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None
if st.sidebar.button("RESET CAPTIONS", use_container_width=True):
    st.session_state.clear()

# Reset session state if a new file is uploaded
if uploaded_file and uploaded_file != st.session_state.get('last_uploaded_file'):
    st.session_state.current_index = 0
    st.session_state.captions = {}
    st.session_state.last_uploaded_file = uploaded_file
    st.session_state.early_end = False  # Reset early end flag for new upload

# present user a form with the image and a text area for the user to fill in
# after user has filled in, they should press a button "done"
# and the next image will be shown for them to write a caption for
# all the image+caption pairs will be saved so that the user can download them as a folder
# the each caption will be in a txt file with the same name as it's image
# the folder the user downloads will have both the image + txt files all in the same dir

if uploaded_file:
    # Open the uploaded zip file
    with ZipFile(uploaded_file) as z:
        # Get a list of image files in the zip
        image_files = [f for f in z.namelist() if f.endswith(('png', 'jpg', 'jpeg'))]
        st.sidebar.info(f"Detected {len(image_files)} images")

        # Read all image data into memory
        image_data_dict = {image_file: z.read(image_file) for image_file in image_files}

    # Initialize session state variables for current index and captions
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'captions' not in st.session_state:
        st.session_state.captions = {}

    current_index = st.session_state.current_index
    captions = st.session_state.captions

    # Check if there are more images to caption
    # And check if user opts to end early
    if current_index < len(image_files) and not st.session_state.get("early_end", False):

        image_file = image_files[current_index]
        image_data = image_data_dict[image_file]

        col1, col2 = st.columns(2)
        with col1:
            # Display the current image
            st.image(image_data, caption=image_file)

        with col2:
            # Text area for the user to input the caption
            caption = st.text_area("Caption", height=300, key="caption", label_visibility="collapsed",
                                  placeholder="use Ctrl/cmd + enter for a new line and remember to use a trigger word")
            save_caption = st.button("Save", type="primary", use_container_width=True)

            # Add an "End/Save Now" button to allow ending the session early
            end_now = st.button("End/Save Now", type="secondary", use_container_width=True)
            if end_now:
                st.session_state.early_end = True  # Set flag to indicate early ending of captioning
                st.rerun()  # Rerun to switch to the download interface

        progress_bar_text = f"Captioning image {current_index + 1} of {len(image_files)}"
        my_bar = st.progress(0, text=progress_bar_text)
        progress = st.session_state.current_index / len(image_files)
        my_bar.progress(progress, text=progress_bar_text)

        # Button to save the caption and move to the next image
        if save_caption:
            # Save the caption and move to the next image
            captions[image_file] = caption
            st.session_state.current_index += 1
            st.session_state.captions = captions
            # Rerun the script to update the interface with the next image
            st.rerun()

    else:
        # All images have been captioned
        st.success("Nice work. All images have been captioned.")
        st.balloons()
        # Button to download the images and captions as a zip file
        with io.BytesIO() as buffer:
            with ZipFile(buffer, 'w') as zip_file:
                for image_file, caption in captions.items():
                    # Add the image file to the zip
                    zip_file.writestr(os.path.basename(image_file), image_data_dict[image_file])
                    # Add the caption file to the zip
                    caption_file = os.path.splitext(os.path.basename(image_file))[0] + ".txt"
                    zip_file.writestr(caption_file, caption)
            buffer.seek(0)

            st.download_button(
                "Download",
                data=buffer,
                # remove the .zip extension from the uploaded file name
                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_captions.zip",
                type="primary",
                use_container_width=True
                )
