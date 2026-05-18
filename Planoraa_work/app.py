from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from groq import Groq
import json
import re
import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="gamchi23",
    database="Planora"
)

cursor = db.cursor()

app = Flask(__name__)
CORS(app)

client = Groq(api_key="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")

DESTINATIONS = [
    "Mumbai",
    "Delhi",
    "Bengaluru",
    "Chennai",
    "Kolkata",
    "Hyderabad",
    "Pune",
    "Ahmedabad",
    "Jaipur",
    "Chandigarh",
    "Lucknow",
    "Kochi",
    "Bhopal",
    "Nagpur",
    "Surat",
    "Goa",
    "Manali",
    "Kerala",
    "Udaipur",
    "Rishikesh",
    "Shimla",
    "Leh Ladakh",
    "Paris, France",
    "London, UK",
    "New York, USA",
    "Dubai, UAE",
    "Singapore",
    "Bangkok, Thailand",
    "Tokyo, Japan",
    "Bali, Indonesia",
    "Rome, Italy",
    "Sydney, Australia"
]
# =======================
# HELPER
# =======================

def extract_json(raw, array=True):
    """Strip markdown fences and extract the first JSON array or object."""
    raw = re.sub(r"```json", "", raw)
    raw = re.sub(r"```", "", raw)
    raw = raw.strip()

    if array:
        start = raw.find("[")
        end = raw.rfind("]") + 1
    else:
        start = raw.find("{")
        end = raw.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("No JSON found in response")

    return json.loads(raw[start:end])


def groq_chat(system_prompt):
    """Call Groq and return the text response."""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.4,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": "Generate now."}
        ]
    )
    return response.choices[0].message.content


# =======================
# PAGE ROUTES
# =======================

@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/index")
def index_page():
    return render_template("index.html")

@app.route("/result")
def result_page():
    return render_template("result.html")


# =======================
# CORE LOGIC
# =======================

def generate_itinerary(destination, days, budget):
    if budget < 5000:
        travel_type = "Budget Trip"
        budget_guidance = "Use cheap local transport, budget guesthouses, street food and free attractions."
    elif budget < 10000:
        travel_type = "Standard Trip"
        budget_guidance = "Use mid-range hotels, occasional cabs, sit-down restaurants and paid attractions."
    else:
        travel_type = "Luxury Trip"
        budget_guidance = "Use premium hotels, private cabs, fine dining and exclusive experiences."

    system_prompt = f"""
You are an expert Indian travel planner. Create a detailed {days}-day itinerary for {destination}.

Trip type: {travel_type}
Total budget: Rs{budget}
Budget guidance: {budget_guidance}

Rules:
- Each day must have 3-4 activities: morning, afternoon, evening, and optionally night.
- Each activity must include: a real place name, a short description, and an estimated cost in Rs.
- Activities must be realistic and specific to {destination} — no generic suggestions.
- Keep the total estimated cost across all days within Rs{budget}.
- Return ONLY a valid JSON array, no explanation, no markdown, no extra text.

Format:
[
  {{
    "day": 1,
    "plan": [
      {{ "time": "Morning",   "activity": "Visit Rohtang Pass", "description": "Scenic snow-covered mountain pass with panoramic views.", "cost": 500 }},
      {{ "time": "Afternoon", "activity": "Solang Valley",      "description": "Adventure sports like skiing and zorbing.",              "cost": 800 }},
      {{ "time": "Evening",   "activity": "Mall Road stroll",   "description": "Browse local shops and try Himachali street food.",      "cost": 300 }}
    ]
  }}
]
"""

    try:
        raw = groq_chat(system_prompt)
        print("Raw Groq itinerary response:\n", raw[:300])
        itinerary = extract_json(raw, array=True)

    except Exception as e:
        print("Itinerary error:", e)
        itinerary = [
            {
                "day": i + 1,
                "plan": [
                    {"time": "Morning",   "activity": f"Explore {destination}", "description": "Local sightseeing",    "cost": 0},
                    {"time": "Afternoon", "activity": "Local Cuisine",          "description": "Try regional food",    "cost": 0},
                    {"time": "Evening",   "activity": "Leisure",                "description": "Explore nearby areas", "cost": 0}
                ]
            }
            for i in range(days)
        ]

    return {
        "destination": destination,
        "days": days,
        "budget": budget,
        "type": travel_type,
        "itinerary": itinerary
    }


def get_transport_options(destination):
    system_prompt = f"""
You are an Indian travel expert. List transport options to reach {destination} from the nearest major Indian city.

Always include exactly these 3 modes in this order: Bus, Train, Flight.

Rules:
- Give realistic 2025 Indian market prices in Rs (Bus: 300-1500, Train: 500-2500, Flight: 2000-12000 depending on distance).
- Give accurate travel time for each mode.
- If a mode does NOT exist for this destination (no railway station, no airport, no road), set "available": false, "price": null, "time": null.
- If it IS available, set "available": true with a real price and time.
- Return ONLY a valid JSON array. No explanation, no markdown, no extra text.

Format:
[
  {{"type": "Bus",    "available": true,  "price": 800,  "time": "8 hrs"}},
  {{"type": "Train",  "available": false, "price": null, "time": null}},
  {{"type": "Flight", "available": true,  "price": 4500, "time": "1.5 hrs"}}
]
"""
    try:
        raw = groq_chat(system_prompt)
        print("Raw Groq transport response:\n", raw[:200])
        transport = extract_json(raw, array=True)

    except Exception as e:
        print("Transport error:", e)
        transport = [
            {"type": "Bus",    "available": True,  "price": 600,  "time": "6 hrs"},
            {"type": "Train",  "available": True,  "price": 900,  "time": "4 hrs"},
            {"type": "Flight", "available": True,  "price": 3500, "time": "1 hr"}
        ]
    return transport


# =======================
# API ROUTES
# =======================

@app.route("/plan", methods=["POST"])
def plan_trip():
    data = request.json
    destination = data.get("destination")
    days = int(data.get("days"))
    budget = int(data.get("budget"))

    email = data.get("email", "")

    return jsonify({
        "trip": generate_itinerary(destination, days, budget),
        "transport": get_transport_options(destination)
    })


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name     = data.get("name")
    email    = data.get("email")
    phone    = data.get("phone")
    password = data.get("password")

    query = "INSERT INTO Users (Name, Email, PhoneNumber, Password) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (name, email, phone, password))
    db.commit()

    return jsonify({"message": "User added successfully"})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email    = data.get("email")
    password = data.get("password")

    query = "SELECT * FROM Users WHERE Email=%s AND Password=%s"
    cursor.execute(query, (email, password))
    user = cursor.fetchone()

    if user:
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"message": "Invalid credentials"})

@app.route("/profile")
def profile_page():
    return render_template("profile.html")
 
 
# 3.  Return current user's profile data (uses session email stored client-side):
 
@app.route("/get_profile", methods=["GET"])
def get_profile():
    email = request.args.get("email", "")
    if not email:
        return jsonify({})
 
    cursor.execute("SELECT Name, Email, PhoneNumber, Location, Avatar FROM Users WHERE Email=%s", (email,))
    row = cursor.fetchone()
    if row:
        return jsonify({"name": row[0], "email": row[1], "phone": row[2], "location": row[3] or "","avatar": row[4] or "" })
    return jsonify({})
 
 
# 4.  Save updated name + location:
 
@app.route("/update_profile", methods=["POST"])
def update_profile():
    data = request.json

    email    = data.get("email")
    name     = data.get("name")
    location = data.get("location")
    avatar   = data.get("avatar")

    if not email:
        return jsonify({"message": "No email"}), 400

    cursor.execute(
        "UPDATE Users SET Name=%s, Location=%s, Avatar=%s WHERE Email=%s",
        (name, location, avatar, email)
    )
    db.commit()

    return jsonify({"message": "Profile updated"})

# ── ADD THIS ROUTE (page) ──
@app.route("/hotel")
def hotel_page():
    return render_template("hotel.html")


# ── ADD THIS ROUTE (API) ──
@app.route("/hotels", methods=["POST"])
def search_hotels():
    data        = request.json
    destination = data.get("destination")
    checkin     = data.get("checkin")
    checkout    = data.get("checkout")
    nights      = data.get("nights", 1)
    guests      = data.get("guests", 1)
    budget      = data.get("budget", "any budget")

    system_prompt = f"""
You are an expert hotel recommendation engine for India and international destinations.

Recommend exactly 6 real hotels in {destination} for {guests} guest(s).
Check-in: {checkin}, Check-out: {checkout} ({nights} night(s)).
Budget per night: {budget}.

Rules:
- All hotels must be real, existing properties in {destination}.
- Price per night must realistically fit within the budget range given.
- Return ONLY a valid JSON array. No explanation, no markdown, no backticks.
- Each hotel object must have exactly these keys:
  name, location (area/neighbourhood in {destination}), price_per_night (integer, INR),
  rating (string like "4.7"), amenities (array of 3 short strings),
  type (e.g. "Luxury Resort", "Budget Hostel", "Boutique Hotel"),
  highlight (one sentence about why it is great).
  Each hotel MUST include:
- name
- location
- price_per_night
- rating
- amenities
- type
- highlight
- image_url (realistic image of hotel in that city)

Example format:
[
  {{
    "name": "Hotel Sunshine",
    "location": "Calangute Beach, Goa",
    "price_per_night": 4500,
    "rating": "4.6",
    "amenities": ["Pool", "Free WiFi", "Breakfast"],
    "type": "Beach Resort",
    "highlight": "Steps from the beach with stunning sea views.",
    "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945"
  }}
]
"""

    try:
        raw    = groq_chat(system_prompt)
        hotels = extract_json(raw, array=True)
        return jsonify({"hotels": hotels})
    except Exception as e:
        print("Hotel search error:", e)
        return jsonify({"hotels": []}), 500

@app.route("/payment")
def payment_page():
    return render_template("payment.html")


@app.route("/confirm_payment", methods=["POST"])
def confirm_payment():

    try:

        data = request.json

        email  = data.get("email", "")
        title  = data.get("title", "")
        amount = data.get("amount", 0)
        btype  = data.get("type", "")
        extra  = data.get("extra", {})

        if not email:
            return jsonify({
                "message": "Email missing"
            }), 400

        clean_amount = int(
            str(amount)
            .replace("₹", "")
            .replace(",", "")
            .strip() or 0
        )

        # DESTINATION LABEL

        if btype == "transport":

            destination_label = (
                f"{extra.get('source')} → "
                f"{extra.get('destination')} "
                f"({extra.get('transport_type')})"
            )

        elif btype == "hotel":

            destination_label = (
                f"Hotel: "
                f"{extra.get('hotel')} "
                f"({extra.get('location')})"
            )

        else:

            destination_label = title

        # CHECK DUPLICATE

        cursor.execute("""

            SELECT COUNT(*)
            FROM TripHistory

            WHERE Email=%s
            AND Destination=%s
            AND Budget=%s
            AND TravelDate=%s

        """, (

            email,
            destination_label,
            clean_amount,
            extra.get("travel_date", "")

        ))

        exists = cursor.fetchone()[0]

        if exists > 0:

            return jsonify({
                "message": "Booking already exists"
            })

        # INSERT BOOKING

        cursor.execute("""

            INSERT INTO TripHistory

            (
                Email,
                Destination,
                Days,
                Budget,
                TravelDate
            )

            VALUES (%s,%s,%s,%s,%s)

        """, (

            email,
            destination_label,
            1,
            clean_amount,
            extra.get("travel_date", "")

        ))

        db.commit()

        return jsonify({
            "message": "Payment recorded"
        })

    except Exception as e:

        print("CONFIRM_PAYMENT ERROR:", e)

        return jsonify({
            "message": "error"
        }), 500

@app.route("/chatbot")
def chatbot_page():
    return render_template("chatbot.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        messages = data.get("messages", [])

        groq_messages = [
            {
                "role": "system",
                "content": (
                    "You are Planora Assistant, an expert AI travel agent. "
                    "You help users plan trips, suggest destinations, recommend hotels, "
                    "explain visa requirements, estimate budgets, suggest itineraries, "
                    "give packing tips, and answer any travel-related questions. "
                    "You specialise in both Indian domestic travel and international destinations. "
                    "Be friendly, concise, and practical. Use bullet points and short paragraphs "
                    "for readability. Always tailor advice to the user's budget and preferences when mentioned. "
                    "If asked about something unrelated to travel, politely redirect the conversation back to travel."
                )
            }
        ] + messages

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            temperature=0.6,
            max_tokens=800,
            messages=groq_messages
        )

        reply = response.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"reply": "Sorry, I'm having trouble connecting right now. Please try again!"}), 500


@app.route("/transport_booking")
def transport_booking():

    return render_template(

        "transport_booking.html",

        destinations=DESTINATIONS
    )

@app.route("/search_transport", methods=["POST"])
def search_transport():

    try:

        data = request.json

        source = data.get("source")
        destination = data.get("destination")
        date = data.get("date")
        passengers = data.get("passengers")
        transport_type = data.get("transport_type")

        source_lower = source.lower()
        dest_lower = destination.lower()

        international_routes = [
            "tokyo",
            "paris",
            "london",
            "new york",
            "dubai",
            "singapore"
        ]

        # VALIDATION

        if transport_type in ["Bus", "Train"]:

            if dest_lower in international_routes:
                return jsonify({
                    "success": False,
                    "message":
                    f"{transport_type} not available for international routes"
                })

        # AI PROMPT

        prompt = f"""
Generate realistic {transport_type} booking options.

Source: {source}
Destination: {destination}
Travel Date: {date}
Passengers: {passengers}

Return ONLY valid JSON array.

Each object must contain:
- operator
- departure
- arrival
- duration
- price
- class

Generate exactly 5 options.

Example:
[
 {{
   "operator":"IndiGo",
   "departure":"08:30",
   "arrival":"12:15",
   "duration":"3h 45m",
   "price":5499,
   "class":"Economy"
 }}
]
"""

        completion = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.7
        )

        response_text = (
            completion.choices[0]
            .message
            .content
        )

        import json
        import re

        json_match = re.search(
            r'\[.*\]',
            response_text,
            re.DOTALL
        )

        if json_match:

            routes = json.loads(
                json_match.group()
            )

            return jsonify({
                "success": True,
                "routes": routes
            })

        return jsonify({
            "success": False,
            "message": "AI parsing failed"
        })

    except Exception as e:

        print("TRANSPORT ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        })
    
if __name__ == "__main__":
    app.run(debug=True)