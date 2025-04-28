import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI

# --- Set Page Settings ---
st.set_page_config(page_title="City Connect", layout="centered")

# --- Title ---
st.markdown("# 🌟 City Connect")

# --- Custom CSS Styling ---
st.markdown(
    """
    <style>
    /* Nature Harmony Theme */
    body, .stApp {
      background-color: #f8f5f2;
      color: #2e7d32;
      font-family: 'Poppins', sans-serif;
    }

    /* Center the main titles */
    .stApp h1, .stApp h2 {
      text-align: center;
    }

    .stButton>button {
      background-color: #81c784;
      color: white;
      border-radius: 12px;
      padding: 12px 24px;
      font-size: 16px;
    }
    .stButton>button:hover {
      background-color: #66bb6a;
    }
    .stTextInput>div>div>input,
    .stDateInput>div>div>div>input,
    .stSelectbox > div > div > div,
    .stSelectbox > div > div > div > div,
    .stSelectbox select,
    .stSelectbox div[role="combobox"],
    .stSelectbox div[role="option"] {
        color: #2e7d32 !important;
        background-color: #e8f5e9 !important;
    }
    .stTextArea>div>div>textarea {
      background-color: #e8f5e9;
      color: #2e7d32;
      border-radius: 10px;
      padding: 10px;
      font-size: 16px;
    }
    .stSelectbox>div>div>div {
      display: flex;
      align-items: center;
    }
    .css-1wy0on6::after {
      color: #2e7d32;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Load Data ---
schedule_df = pd.read_csv("Park_schedule.csv")
amenities_df = pd.read_csv("Park_amenities.csv")
log_df = pd.read_csv("reservations_log.csv")

# Remove stray header rows if duplicated
schedule_df = schedule_df[schedule_df["date"] != "date"]

# Convert date column to datetime format
schedule_df["date"] = pd.to_datetime(schedule_df["date"], errors='coerce')

# --- Sidebar Navigation ---
st.sidebar.title("📋 Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["Chatbot Assistant", "Reservation", "Park Data Insights", "Report an Issue"]
)

# --- Pages ---
if page == "Chatbot Assistant":
    st.header("💬 Chatbot Assistant")

    from datetime import datetime
    import pydeck as pdk

    # OpenAI API client
    client = OpenAI(api_key="OPENAI_API_KEY")

    # --- Initialize Session State ---
    if 'reservation_data' not in st.session_state:
        st.session_state.reservation_data = {
            "name": "",
            "email": "",
            "phone": "",
            "park": "",
            "date": "",
            "time_slot": ""
        }
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'booking_progress' not in st.session_state:
        st.session_state.booking_progress = None

    # --- Load Data ---
    amenities_df = pd.read_csv("Park_amenities.csv")
    locations_df = pd.read_csv("Park_location.csv")
    schedule_df = pd.read_csv("Park_schedule.csv")
    schedule_df["date"] = pd.to_datetime(schedule_df["date"], errors="coerce")

    # --- Display conversation history ---
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                if "text" in msg:
                    st.write(msg["text"])
                if "map_df" in msg:
                    map_layer = pdk.Layer(
                        "ScatterplotLayer",
                        data=msg["map_df"],
                        get_position='[lon, lat]',
                        get_color='[255, 0, 0, 160]',
                        get_radius=100,
                        pickable=True,
                    )
                    view_state = pdk.ViewState(
                        latitude=msg["map_df"]["lat"].mean(),
                        longitude=msg["map_df"]["lon"].mean(),
                        zoom=11,
                        pitch=0,
                    )
                    tooltip = {
                        "html": "<b>🏞️ Park:</b> {park_name}",
                        "style": {
                            "backgroundColor": "white",
                            "color": "black",
                            "fontSize": "14px"
                        }
                    }
                    st.pydeck_chart(pdk.Deck(
                        map_style="mapbox://styles/mapbox/light-v9",
                        initial_view_state=view_state,
                        layers=[map_layer],
                        tooltip=tooltip
                    ))

    # --- Chat Input ---
    user_input = st.chat_input("Ask me about parks, amenities, or start your reservation!")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        user_trigger_words = ["reservation", "book", "schedule", "reserve"]

        if any(word in user_input.lower() for word in user_trigger_words) and st.session_state.booking_progress is None:
            st.session_state.booking_progress = "name"
            st.session_state.messages.append({"role": "assistant", "text": "Sure! Let's make a reservation. What's your full name?"})
            st.rerun()

        elif st.session_state.booking_progress == "name":
            st.session_state.reservation_data["name"] = user_input
            st.session_state.booking_progress = "email"
            st.session_state.messages.append({"role": "assistant", "text": "Great! Now, what's your email address?"})
            st.rerun()

        elif st.session_state.booking_progress == "email":
            st.session_state.reservation_data["email"] = user_input
            st.session_state.booking_progress = "phone"
            st.session_state.messages.append({"role": "assistant", "text": "Thanks! Could you also provide your phone number?"})
            st.rerun()

        elif st.session_state.booking_progress == "phone":
            st.session_state.reservation_data["phone"] = user_input
            st.session_state.booking_progress = "park"
            st.session_state.messages.append({"role": "assistant", "text": "Which park would you like to reserve?"})
            st.rerun()

        elif st.session_state.booking_progress == "park":
            st.session_state.reservation_data["park"] = user_input
            st.session_state.booking_progress = "date"
            st.session_state.messages.append({"role": "assistant", "text": "What date would you like to book? (Format: YYYY-MM-DD)"})
            st.rerun()

        elif st.session_state.booking_progress == "date":
            if "available" in user_input.lower():
                # Show available dates
                available_dates = schedule_df[
                    (schedule_df["park_name"].str.lower() == st.session_state.reservation_data["park"].lower()) &
                    (schedule_df["status"] == "available")
                ]["date"].dt.date.unique()

                if len(available_dates) > 0:
                    available_dates_text = ", ".join([str(d) for d in available_dates])
                    st.session_state.messages.append({"role": "assistant", "text": f"📅 Available dates for {st.session_state.reservation_data['park']} are: {available_dates_text}.\n\nPlease pick one."})
                else:
                    st.session_state.messages.append({"role": "assistant", "text": "😢 Sorry, no available dates for that park."})
                st.rerun()

            else:
                # Save the provided date
                st.session_state.reservation_data["date"] = user_input
                st.session_state.booking_progress = "time_slot"
                st.session_state.messages.append({"role": "assistant", "text": "Lastly, what time slot would you like?"})
                st.rerun()

        elif st.session_state.booking_progress == "time_slot":
            if "available" in user_input.lower():
                # Show available time slots
                selected_date = st.session_state.reservation_data["date"]
                available_slots = schedule_df[
                    (schedule_df["park_name"].str.lower() == st.session_state.reservation_data["park"].lower()) &
                    (schedule_df["date"].dt.date == datetime.strptime(selected_date, "%Y-%m-%d").date()) &
                    (schedule_df["status"] == "available")
                ]["time_slot"].unique()

                if len(available_slots) > 0:
                    slots_text = ", ".join(available_slots)
                    st.session_state.messages.append({"role": "assistant", "text": f"⏰ Available time slots for {st.session_state.reservation_data['park']} on {selected_date}: {slots_text}.\n\nPlease pick one."})
                else:
                    st.session_state.messages.append({"role": "assistant", "text": "😢 No available time slots for that date."})
                st.rerun()

            else:
                st.session_state.reservation_data["time_slot"] = user_input
                st.session_state.booking_progress = None

                # Save reservation
                new_booking = {
                    "name": st.session_state.reservation_data['name'],
                    "email": st.session_state.reservation_data['email'],
                    "phone": st.session_state.reservation_data['phone'],
                    "park_name": st.session_state.reservation_data['park'],
                    "date": st.session_state.reservation_data['date'],
                    "time_slot": st.session_state.reservation_data['time_slot']
                }
                log_df = pd.read_csv("reservations_log.csv")
                log_df = pd.concat([log_df, pd.DataFrame([new_booking])], ignore_index=True)
                log_df.to_csv("reservations_log.csv", index=False)

                st.session_state.messages.append({"role": "assistant", "text": f"✅ Your reservation for {st.session_state.reservation_data['park']} on {st.session_state.reservation_data['date']} at {st.session_state.reservation_data['time_slot']} has been recorded! You will be receiving a confirmation email shortly."})

                # Clear
                st.session_state.reservation_data = {key: "" for key in st.session_state.reservation_data}
                st.rerun()

        else:
            # --- Amenities Search ---
            amenities_keywords = {
                "BBQ": ["bbq", "barbecue"],
                "Basketball Court": ["basketball"],
                "Playground": ["playground"],
                "Restroom": ["restroom", "bathroom", "toilet"],
                "Tennis Courts": ["tennis"],
                "Volleyball": ["volleyball"],
                "Skate Park": ["skate park", "skating"],
                "Soccer Field": ["soccer"],
                "Pickleball": ["pickleball"]
            }

            selected_amenities = []
            user_message_lower = user_input.lower()

            for amenity, keywords in amenities_keywords.items():
                if any(keyword in user_message_lower for keyword in keywords):
                    selected_amenities.append(amenity)

            if selected_amenities:
                filtered_df = amenities_df.copy()
                for amenity in selected_amenities:
                    if amenity in filtered_df.columns:
                        filtered_df = filtered_df[filtered_df[amenity] == True]

                if not filtered_df.empty:
                    merged_df = pd.merge(
                        filtered_df,
                        locations_df,
                        left_on="Park",
                        right_on="Park Name",
                        how="inner"
                    )
                    map_df = merged_df[["Latitude", "Longitude", "Park"]].copy()
                    map_df.columns = ["lat", "lon", "park_name"]

                    park_list = merged_df["Park"].tolist()
                    park_names_text = ", ".join(park_list)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "text": (
                            f"🏡 Here’s a map of the parks that match your request! 📍\n\n"
                            f"🗺️ Parks: {park_names_text}\n\n"
                            f"Feel free to ask if you'd like help booking one!"
                        ),
                        "map_df": map_df
                    })
                    st.rerun()

            # Otherwise normal AI conversation
            chat_history = [
                {"role": m["role"], "content": m.get("content", m.get("text", ""))}
                for m in st.session_state.messages if m["role"] in ["user", "assistant"]
            ]

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=chat_history
            )
            assistant_response = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "text": assistant_response})
            st.rerun()

elif page == "Reservation":
    st.header("👨‍💼 Your Contact Information")
    name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    phone = st.text_input("Phone Number")

    st.header("📍 Reservation Details")
    parks = schedule_df["park_name"].unique()
    selected_park = st.selectbox("Choose a park:", parks)

    available_dates = schedule_df[
        (schedule_df["park_name"] == selected_park) & (schedule_df["status"] == "available")
    ]["date"].dt.date.unique()

    selected_date = st.date_input("Choose a date:", min_value=datetime.now().date())

    available_slots = schedule_df[
        (schedule_df["park_name"] == selected_park) &
        (schedule_df["date"].dt.date == selected_date) &
        (schedule_df["status"] == "available")
    ]["time_slot"].unique()

    selected_slot = st.selectbox("Choose a time slot:", available_slots if len(available_slots) > 0 else ["No options available"])

    if st.button("✅ Book Now") and selected_slot != "No options available":
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
        schedule_df.loc[
            (schedule_df["park_name"] == selected_park) &
            (schedule_df["date"].dt.date == selected_date) &
            (schedule_df["time_slot"] == selected_slot),
            "status"
        ] = "booked"
        schedule_df.to_csv("Park_schedule.csv", index=False)

        st.success(f"Reservation confirmed for {selected_park} on {selected_date} at {selected_slot}!")
        st.info("You will receive a confirmation email shortly (mock only).")

elif page == "Park Data Insights":
    st.header("📊 Park Data Insights & Filter")
    st.subheader("🔍 Filter Parks by Amenities")

    # Load the amenities info
    amenities_df = pd.read_csv("Park_amenities.csv")

    # Load the park location info
    locations_df = pd.read_csv("Park_location.csv")  # Should have Park, lat, lon columns

    # Checkbox filters
    filter_options = {
        "BBQ": st.checkbox("Must have BBQ"),
        "Basketball Court": st.checkbox("Must have Basketball Court"),
        "Playground": st.checkbox("Must have Playground"),
        "Restroom": st.checkbox("Must have Restroom"),
        "Tennis Courts": st.checkbox("Must have Tennis Courts"),
        "Volleyball": st.checkbox("Must have Volleyball"),
        "Skate Park": st.checkbox("Must have Skate Park"),
        "Soccer Field": st.checkbox("Must have Soccer Field"),
        "Pickleball": st.checkbox("Must have Pickleball")
    }

    # Filter amenities based on selected options
    filtered_df = amenities_df.copy()
    for amenity, required in filter_options.items():
        if required and amenity in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[amenity] == True]


    # --- Map section ---
    st.subheader('🗺️ Maps', divider='grey')

    # Merge filtered amenities with locations
    merged_df = pd.merge(
    filtered_df,
    locations_df,
    left_on="Park",
    right_on="Park Name",
    how="inner"
)

    # Check if there are parks to display
    if not merged_df.empty:
        map_df = merged_df[["Latitude", "Longitude"]]
        map_df.columns = ["lat", "lon"]


        import pydeck as pdk

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position='[lon, lat]',
            get_color='[255, 0, 0, 160]',  # Red color
            get_radius=100,
            pickable=True,
        )

        view_state = pdk.ViewState(
            latitude=map_df["lat"].mean(),
            longitude=map_df["lon"].mean(),
            zoom=11,
            pitch=0,
        )

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[layer],
        ))
    else:
        st.warning("No parks match the selected filters.")


elif page == "Report an Issue":
    st.header("🛠️ Park Issue Reporting")
    issue_description = st.text_area("Describe the issue you're experiencing:")
    issue_type = st.selectbox("Issue type:", ["Litter", "Damaged Equipment", "Graffiti", "Other"])
    parks = schedule_df["park_name"].unique()
    issue_park = st.selectbox("Which park?", parks)

    if st.button("🛠️ Submit Report"):
        st.success("Your issue has been submitted. Thank you for helping improve our parks!")