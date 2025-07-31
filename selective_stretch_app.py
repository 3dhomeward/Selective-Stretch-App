import streamlit as st
import numpy as np
from stl import mesh
import tempfile
import os

st.title("Selective STL Stretch Tool")

st.write(
    "Stretch your STL model to a new size, keeping ends fixed in X, Y, and Z directions. "
    "Drag and drop your STL, set the new target sizes, and download the result!"
)

# --- User parameters ---
orig_x_total = 12.02
x_fixed_left = 3.75

orig_y_total = 209.45
y_fixed_ends = 2.01

orig_z_total = 9.6
z_fixed_ends = 4.02

uploaded_file = st.file_uploader("Drop STL file here", type=["stl"])

# Only show sizing controls if STL is uploaded
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tf:
        tf.write(uploaded_file.read())
        input_path = tf.name

    m = mesh.Mesh.from_file(input_path)
    all_vertices = m.vectors.reshape(-1, 3)

    # Find actual min/max (origin point of STL model)
    x_min = np.min(all_vertices[:, 0])
    x_max = np.max(all_vertices[:, 0])
    y_min = np.min(all_vertices[:, 1])
    y_max = np.max(all_vertices[:, 1])
    z_min = np.min(all_vertices[:, 2])
    z_max = np.max(all_vertices[:, 2])

    detected_x_total = x_max - x_min
    detected_y_total = y_max - y_min
    detected_z_total = z_max - z_min

    # Minimum stretch amounts = original dimension
    # Maximum = Let's set an arbitrary 10x the original size for each direction (customize as needed)
    x_min_val = detected_x_total
    x_max_val = detected_x_total * 10
    y_min_val = detected_y_total
    y_max_val = detected_y_total * 10
    z_min_val = detected_z_total
    z_max_val = detected_z_total * 10

    st.write(f"**Model detected:**")
    st.write(f"- X (width): {detected_x_total:.2f} mm")
    st.write(f"- Y (length): {detected_y_total:.2f} mm")
    st.write(f"- Z (height): {detected_z_total:.2f} mm")

    st.sidebar.header("Target Sizes (mm)")
    x_new = st.sidebar.text_input("X (Width)", value="")
    st.sidebar.markdown(
        f"<div style='color:gray;font-size:smaller'>Min: {x_min_val:.2f} mm &nbsp;&nbsp; Max: {x_max_val:.2f} mm</div>",
        unsafe_allow_html=True)
    y_new = st.sidebar.text_input("Y (Length)", value="")
    st.sidebar.markdown(
        f"<div style='color:gray;font-size:smaller'>Min: {y_min_val:.2f} mm &nbsp;&nbsp; Max: {y_max_val:.2f} mm</div>",
        unsafe_allow_html=True)
    z_new = st.sidebar.text_input("Z (Height)", value="")
    st.sidebar.markdown(
        f"<div style='color:gray;font-size:smaller'>Min: {z_min_val:.2f} mm &nbsp;&nbsp; Max: {z_max_val:.2f} mm</div>",
        unsafe_allow_html=True)

    # Only proceed if all boxes are filled and values are valid numbers in range
    if x_new and y_new and z_new:
        try:
            x_new = float(x_new)
            y_new = float(y_new)
            z_new = float(z_new)
        except ValueError:
            st.error("Please enter valid numeric values for all sizes.")
            st.stop()

        if not (x_min_val <= x_new <= x_max_val):
            st.error(f"X (Width) must be between {x_min_val:.2f} and {x_max_val:.2f} mm.")
            st.stop()
        if not (y_min_val <= y_new <= y_max_val):
            st.error(f"Y (Length) must be between {y_min_val:.2f} and {y_max_val:.2f} mm.")
            st.stop()
        if not (z_min_val <= z_new <= z_max_val):
            st.error(f"Z (Height) must be between {z_min_val:.2f} and {z_max_val:.2f} mm.")
            st.stop()

        # Prepare the transformation as before (reusing your last working code)
        x_fixed_left_pos = x_min + x_fixed_left
        y_fixed_start = y_min + y_fixed_ends
        y_fixed_end = y_max - y_fixed_ends
        z_fixed_start = z_min + z_fixed_ends
        z_fixed_end = z_max - z_fixed_ends

        x_stretch_factor = (x_new - x_fixed_left) / (x_max - x_fixed_left_pos) if (x_max - x_fixed_left_pos) > 0 else 1.0
        y_middle_orig = y_fixed_end - y_fixed_start
        y_stretch_factor = (y_new - 2 * y_fixed_ends) / y_middle_orig if y_middle_orig > 0 else 1.0
        z_middle_orig = z_fixed_end - z_fixed_start
        z_stretch_factor = (z_new - 2 * z_fixed_ends) / z_middle_orig if z_middle_orig > 0 else 1.0

        new_vectors = np.copy(m.vectors)
        for v in new_vectors.reshape(-1, 3):
            # X direction (fixed left)
            if v[0] > x_fixed_left_pos:
                v[0] = x_fixed_left_pos + (v[0] - x_fixed_left_pos) * x_stretch_factor

            # Y direction (fixed ends)
            if v[1] < y_fixed_start:
                pass
            elif v[1] > y_fixed_end:
                v[1] = y_fixed_end + (v[1] - y_fixed_end) + (y_new - detected_y_total)
            else:
                v[1] = y_fixed_start + (v[1] - y_fixed_start) * y_stretch_factor

            # Z direction (fixed ends)
            if v[2] < z_fixed_start:
                pass
            elif v[2] > z_fixed_end:
                v[2] = z_fixed_end + (v[2] - z_fixed_end) + (z_new - detected_z_total)
            else:
                v[2] = z_fixed_start + (v[2] - z_fixed_start) * z_stretch_factor

        m.vectors = new_vectors

        # Save mesh to a temp file, then read into memory
        with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as out_file:
            out_path = out_file.name
            m.save(out_path)

        with open(out_path, "rb") as f:
            st.download_button(
                label="Download Stretched STL",
                data=f.read(),
                file_name="stretched.stl",
                mime="application/sla"
            )

        os.remove(input_path)
        os.remove(out_path)
        st.success("Done! Download your stretched STL above.")
    else:
        st.info("Enter your desired X, Y, Z target sizes in the sidebar and press Enter.")

else:
    st.info("Upload an STL file to begin. The app will display the allowed min/max values for stretching based on your model.")
