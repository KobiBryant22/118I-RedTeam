import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI

# Set Page - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="City Connect", layout="centered")

# Custom CSS for cartoonish pastel green theme
# 2) inject just enough CSS for the green background
st.markdown(
    """
    <style>
      /* entire app background */
      .stApp {
        background-color: #D7E9A9;
      }
      /* panel/container backgrounds */
      .block-container, section[data-testid="stSidebar"] {
        background-color: #E8F5E9;
        border-radius: 16px;
        padding: 2rem;
      }
      /* round inputs and buttons */
      input, textarea,
      button,
      .stSelectbox>div,
      .stDateInput>div {
        border-radius: 12px !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3) your content
st.title("🌳 City Connect")
st.write("Welcome to your fresh green-themed Streamlit page!") 

# Load Data
schedule_df = pd.read_csv("Park_schedule.csv")
amenities_df = pd.read_csv("Park_amenities.csv")
log_df = pd.read_csv("reservations_log.csv")

# Remove stray header rows if duplicated
schedule_df = schedule_df[schedule_df["date"] != "date"]

# Convert date column to datetime format
schedule_df["date"] = pd.to_datetime(schedule_df["date"], errors='coerce')

# Page header with tree icon
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <div style="font-size: 48px; margin-right: 15px;">🌳</div>
    <div>
        <h1 style="margin: 0; padding: 0;">City Connect</h1>
        <p style="margin: 0; padding: 0; font-style: italic; color: #558B2F;">Your gateway to San Jose's parks and recreation</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Main content container
st.markdown("""
<div style="background-color: #E8F5E9; border-radius: 20px; border: 2px solid #5C8D3B; padding: 20px; box-shadow: 0 6px 0 #96BE5A;">
""", unsafe_allow_html=True)

# ------------------- Contact Info -------------------
st.subheader("👤 Your Contact Information")
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Full Name")
    email = st.text_input("Email Address")
with col2:
    phone = st.text_input("Phone Number")

# ------------------- Reservation -------------------
st.markdown("""
<hr style="height:2px; margin: 20px 0; background-color:#AED581; border:none;">
""", unsafe_allow_html=True)
st.subheader("📅 Reservation Details")
parks = schedule_df["park_name"].unique()
selected_park = st.selectbox("Choose a park:", parks)

# Show park amenities
if selected_park:
    park_amenities = amenities_df[amenities_df["Park"] == selected_park].iloc[0].to_dict()
    st.markdown("""
    <div style="background-color: #F1F8E9; border-radius: 15px; padding: 15px; border: 2px solid #8BC34A; margin: 10px 0;">
        <h5 style="margin-top: 0;">Available Amenities:</h5>
    """, unsafe_allow_html=True)
    
    amenity_icons = {
        "BBQ": "🔥",
        "Basketball Court": "🏀",
        "Playground": "🧒",
        "Restroom": "🚻",
        "Tennis Courts": "🎾",
        "Volleyball": "🏐",
        "Skate Park": "🛹",
        "Soccer Field": "⚽",
        "Pickleball": "🏓"
    }
    
    amenity_html = '<div style="display: flex; flex-wrap: wrap;">'
    amenity_index = 0
    for amenity, has_amenity in park_amenities.items():
        if amenity != "Park" and has_amenity == True:
            icon = amenity_icons.get(amenity, "✓")
            amenity_html += f"""<div style="margin-right: 20px; margin-bottom: 10px;">
                <span style="background-color: #DCEDC8; padding: 5px 10px; border-radius: 15px; border: 1px solid #8BC34A;">
                    {icon} {amenity}
                </span>
            </div>"""
    amenity_html += '</div>'
    st.markdown(amenity_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

available_dates = schedule_df[(schedule_df["park_name"] == selected_park) & (schedule_df["status"] == "available")]["date"].dt.date.unique()
selected_date = st.date_input("Choose a date:", min_value=datetime.now().date())

available_slots = schedule_df[(schedule_df["park_name"] == selected_park) & 
                            (schedule_df["date"].dt.date == selected_date) & 
                            (schedule_df["status"] == "available")]["time_slot"].unique()
selected_slot = st.selectbox("Choose a time slot:", available_slots if len(available_slots) > 0 else ["No options available"])

# Booking form
st.markdown("""
<hr style="height:2px; margin: 20px 0; background-color:#AED581; border:none;">
""", unsafe_allow_html=True)
col1, col2, col3 = st.columns([2,1,2])
with col2:
    book_button = st.button("✅ Book Now", use_container_width=True)

if book_button and selected_slot != "No options available":
    if not name or not email or not phone:
        st.error("Please fill out all contact information before booking.")
    else:
        new_booking = {
            "name": name,
            "email": email,
            "phone": phone,
            "park_name": selected_park,
            "date": selected_date.strftime("%Y-%m-%d"),
            "time_slot": selected_slot
        }
        log_df = pd.concat([log_df, pd.DataFrame([new_booking])], ignore_index=True)
        log_df.to_csv("reservations_log.csv", index=False)

        # Update schedule
        schedule_df.loc[(schedule_df["park_name"] == selected_park) &
                        (schedule_df["date"].dt.date == selected_date) &
                        (schedule_df["time_slot"] == selected_slot), "status"] = "booked"
        schedule_df.to_csv("Park_schedule.csv", index=False)

        st.success(f"Reservation confirmed for {selected_park} on {selected_date} at {selected_slot}!")
        st.info("You will receive a confirmation email shortly.")

# ------------------- View Reservations -------------------
st.markdown("""
<hr style="height:2px; margin: 20px 0; background-color:#AED581; border:none;">
""", unsafe_allow_html=True)

with st.expander("📒 View All Bookings"):
    st.dataframe(schedule_df)

# ------------------- Park Issue Reporting -------------------
st.markdown("""
<hr style="height:2px; margin: 20px 0; background-color:#AED581; border:none;">
""", unsafe_allow_html=True)
st.subheader("🔔 Park Issue Reporting")
col1, col2 = st.columns(2)
with col1:
    issue_park = st.selectbox("Which park?", parks)
    issue_type = st.selectbox("Issue type:", ["Litter", "Damaged Equipment", "Graffiti", "Safety Concern", "Other"])
with col2:
    issue_description = st.text_area("Describe the issue you're experiencing:", height=124)

col1, col2, col3 = st.columns([2,1,2])
with col2:
    report_button = st.button("📝 Submit Report", use_container_width=True)

if report_button:
    if not issue_description:
        st.error("Please provide a description of the issue.")
    else:
        st.success("Your issue has been submitted. Thank you for helping improve our parks!")

# ------------------- Chatbot Assistant -------------------
st.markdown("""
<hr style="height:2px; margin: 20px 0; background-color:#AED581; border:none;">
""", unsafe_allow_html=True)
st.subheader("💬 Park Assistant")
st.markdown("*Ask a question about park rules, hours, or reservations*")

# Chat UI
user_input = st.chat_input("Type your question here...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        try:
            client = OpenAI(api_key="OPENAI_API_KEY")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful San Jose park assistant. Keep your responses friendly, informative, and brief."},
                    {"role": "user", "content": user_input}
                ]
            )
            st.write(response.choices[0].message.content)
        except Exception as e:
            st.write("I'm sorry, I couldn't connect to the assistant right now. Please try again later.")

st.markdown("</div>", unsafe_allow_html=True)  # Close the main content container

# Add footer
st.markdown("""
<div style="text-align: center; color: #558B2F; font-size: 14px; margin-top: 30px; background-color: #E8F5E9; border-radius: 20px; padding: 10px; border: 2px solid #5C8D3B;">
    © 2025 City Connect | San Jose Parks & Recreation
</div>
""", unsafe_allow_html=True)