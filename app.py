import streamlit as st
from PIL import Image
from backend.stego_engine import hide_message, extract_message
from backend.explainability import (
    calculate_capacity,
    generate_difference_image,
    lsb_change_count,
    plot_rgb_histogram,
    plot_difference_heatmap,
    plot_lsb_visualization,
    plot_bit_plane,
    plot_pixel_value_scatter,
    plot_analysis_summary,
)

st.set_page_config(page_title="Explainable Steganography", layout="wide")

st.title("🔐 Explainable Image Steganography System")

tab1, tab2 = st.tabs(["Hide Message", "Extract Message"])

# ─── HIDE MESSAGE ────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Hide Secret Message")

    img_file = st.file_uploader("Upload PNG Image", type=["png"])
    secret = st.text_area("Enter Secret Text")

    if img_file:
        image = Image.open(img_file)
        st.image(image, caption="Original Image", use_column_width=True)

        capacity = calculate_capacity(image)
        st.info(f"📦 Image Capacity: {capacity} characters")

        if st.button("Hide Message"):

            if len(secret) == 0:
                st.warning("Please enter a secret message.")

            elif len(secret) > capacity:
                st.error("❌ Message too long for this image.")

            else:
                stego = hide_message(image, secret)

                st.image(stego, caption="Stego Image", use_column_width=True)

                # Save stego image
                stego.save("stego.png")
                with open("stego.png", "rb") as file:
                    st.download_button(
                        label="⬇ Download Stego Image",
                        data=file,
                        file_name="stego.png",
                        mime="image/png"
                    )

                # ── ANALYSIS SECTION ──────────────────────────────────────
                st.markdown("---")
                st.subheader("📊 Explainability & Analysis")

                changed = lsb_change_count(image, stego)
                total = image.size[0] * image.size[1] * 3
                st.metric("🔢 LSB Bits Modified", f"{changed:,} / {total:,}",
                          delta=f"{changed/total*100:.4f}% of all bits")

                # 1. RGB Histogram
                with st.expander("📈 RGB Histogram Comparison", expanded=True):
                    st.write("Compares pixel intensity distribution across R, G, B channels before and after hiding.")
                    hist_img = plot_rgb_histogram(image, stego)
                    st.image(hist_img, use_column_width=True)

                # 2. Difference Heatmap
                with st.expander("🔥 Pixel Difference Heatmap", expanded=True):
                    st.write("Shows *where* in the image pixels were modified. Brighter areas = more change.")
                    heatmap_img = plot_difference_heatmap(image, stego)
                    st.image(heatmap_img, use_column_width=True)

                # 3. LSB Visualization
                with st.expander("🧩 LSB Bit Plane Visualization", expanded=True):
                    st.write("Visualizes the least-significant bit layer of each image and highlights changes.")
                    lsb_img = plot_lsb_visualization(image, stego)
                    st.image(lsb_img, use_column_width=True)

                # 4. Bit Plane Analysis
                with st.expander("🔬 Bit Plane Analysis (Original)", expanded=False):
                    st.write("All 8 bit planes of the original image's Red channel.")
                    bp_orig = plot_bit_plane(image, title="Original")
                    st.image(bp_orig, use_column_width=True)

                with st.expander("🔬 Bit Plane Analysis (Stego)", expanded=False):
                    st.write("All 8 bit planes of the stego image's Red channel. The LSB plane (Bit 0) should show the hidden data pattern.")
                    bp_stego = plot_bit_plane(stego, title="Stego")
                    st.image(bp_stego, use_column_width=True)

                # 5. Scatter Plot
                with st.expander("🔵 Pixel Value Scatter Plot", expanded=False):
                    st.write("Each dot is a pixel. Red dots show pixels whose LSB was changed during encoding.")
                    scatter_img = plot_pixel_value_scatter(image, stego)
                    st.image(scatter_img, use_column_width=True)

                # 6. Summary
                with st.expander("📋 Analysis Summary", expanded=True):
                    st.write("Overall impact of steganographic encoding on the image.")
                    summary_img = plot_analysis_summary(image, stego)
                    st.image(summary_img, use_column_width=True)


# ─── EXTRACTION ──────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Extract Secret Message")

    stego_file = st.file_uploader("Upload Stego Image", type=["png"], key="extract")

    if stego_file is not None:
        stego_image = Image.open(stego_file)
        st.image(stego_image, caption="Uploaded Stego Image", use_column_width=True)

        if st.button("Extract Message"):
            message = extract_message(stego_image)

            st.success("Hidden Message Extracted:")
            st.code(message)

            # ── ANALYSIS ON EXTRACTED IMAGE ───────────────────────────────
            st.markdown("---")
            st.subheader("📊 Stego Image Analysis")

            with st.expander("🔬 LSB Bit Plane of Stego Image", expanded=True):
                st.write("The LSB plane (Bit 0) reveals where the hidden data was embedded.")
                bp = plot_bit_plane(stego_image, title="Stego")
                st.image(bp, use_column_width=True)