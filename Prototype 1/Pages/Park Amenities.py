import os
import streamlit as st
import pandas as pd
import pydeck as pdk
from openai import OpenAI
from PIL import Image
from io import BytesIO

# ─── 1) Page config ───────────────────────────────────────────────────────────
st.set_page_config(page_title="Park Amenities", layout="centered")

# ─── 2) Load your amenities data ──────────────────────────────────────────────
amen_df = pd.read_csv("Park_amenities.csv")

# ─── 3) Simple lat/lon lookup for each park ────────────────────────────────────
park_coords = {
    "River Glen Park":       (37.3639, -121.9010),
    "Roosevelt Park":        (37.3500, -121.8934),
    "Watson Park":           (37.3668, -121.9245),
    "Almaden Lake Park":     (37.2143, -121.8233),
    "Happy Hollow Park":     (37.3040, -121.8605),
    "Emma Prusch Farm Park": (37.3252, -121.8206),
    "Overfelt Gardens":      (37.3640, -121.8773),
    "Municipal Rose Garden": (37.2735, -121.8866),
    "Willow Glen Park":      (37.3058, -121.8847),
    "Cataldi Park":          (37.2746, -121.9331),
}

# ─── 4) Amenity‐filter checkboxes ──────────────────────────────────────────────
st.header("📊 Filter Parks by Amenities & View on Map")

amen_cols = [
    "BBQ","Basketball Court","Playground","Restroom",
    "Tennis Courts","Volleyball","Skate Park",
    "Soccer Field","Pickleball"
]

filters = {}
cols = st.columns(3)
for i, amen in enumerate(amen_cols):
    with cols[i % 3]:
        filters[amen] = st.checkbox(f"Must have {amen}")

# apply filters
df = amen_df.copy()
for amen, req in filters.items():
    if req:
        df = df[df[amen]]

st.markdown(f"**{len(df)} park(s) match your criteria.**")
st.dataframe(df.reset_index(drop=True))

# ─── 5) Build map_df with tooltip data ────────────────────────────────────────
map_rows = []
for park in df["Park"]:
    coords = park_coords.get(park)
    if coords:
        map_rows.append({
            "Park": park,
            "lat": coords[0],
            "lon": coords[1]
        })

map_df = pd.DataFrame(map_rows)

# ─── 6) Render the map with hover tooltips ───────────────────────────────────
if not map_df.empty:
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[lon, lat]",
        get_fill_color=[124, 252, 0],
        get_radius=200,
        pickable=True
    )
    view = pdk.ViewState(latitude=37.33, longitude=-121.88, zoom=11)
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        tooltip={"text": "{Park}"}
    )
    st.pydeck_chart(deck)
else:
    st.info("No parks to display on the map.")

# ─── 7) AI‐powered image & description ────────────────────────────────────────
st.markdown("---")
st.subheader("🎨 Generate an Image & ✍️ Description")

choice = st.selectbox("Pick one park to explore:", df["Park"].tolist())

# initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 7a) DALL·E image
if st.button(f"🖼️ Generate image of {choice}"):
    prompt = (
        f"A cheerful, pastel-green UI illustration of {choice} Park in San Jose, "
        "showing trees, picnic tables, playground equipment, in a friendly cartoon style."
    )
    img_resp = client.images.generate(prompt=prompt, n=1, size="512x512")
    # decode base64 into an image
    img_bytes = BytesIO(img_resp.data[0].b64_json.decode("base64"))
    st.image(Image.open(img_bytes), caption=choice)

# 7b) GPT description
if st.button(f"✍️ Describe {choice}"):
    messages = [
        {"role": "system", "content": "You are an expert local guide."},
        {"role": "user",   "content": f"Write a friendly two-sentence description of {choice} Park in San Jose."}
    ]
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    st.write(resp.choices[0].message.content)
