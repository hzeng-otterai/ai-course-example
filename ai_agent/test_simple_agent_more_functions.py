import anthropic
import random
from datetime import datetime, timedelta

client = anthropic.Anthropic()

# ── Tool definitions ──────────────────────────────────────────────────────────

tools = [
    # Transportation
    {
        "name": "search_flights",
        "description": "Search for available flights between two cities on a given date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin":      {"type": "string", "description": "Departure city or airport code"},
                "destination": {"type": "string", "description": "Arrival city or airport code"},
                "date":        {"type": "string", "description": "Departure date in YYYY-MM-DD format"},
                "return_date": {"type": "string", "description": "Return date for round trips in YYYY-MM-DD format"},
                "passengers":  {"type": "integer", "description": "Number of passengers"}
            },
            "required": ["origin", "destination", "date", "passengers"]
        }
    },
    {
        "name": "book_flight",
        "description": "Book a specific flight by flight number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flight_number":   {"type": "string", "description": "Flight number e.g. AA123"},
                "origin":          {"type": "string", "description": "Departure city or airport code"},
                "destination":     {"type": "string", "description": "Arrival city or airport code"},
                "date":            {"type": "string", "description": "Departure date in YYYY-MM-DD format"},
                "passenger_name":  {"type": "string", "description": "Full name of the passenger"},
                "seat_class":      {"type": "string", "enum": ["economy", "business", "first"], "description": "Seat class"}
            },
            "required": ["flight_number", "origin", "destination", "date", "passenger_name", "seat_class"]
        }
    },
    {
        "name": "search_trains",
        "description": "Search for train routes and schedules between two cities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin":      {"type": "string", "description": "Departure city"},
                "destination": {"type": "string", "description": "Arrival city"},
                "date":        {"type": "string", "description": "Travel date in YYYY-MM-DD format"}
            },
            "required": ["origin", "destination", "date"]
        }
    },
    {
        "name": "book_train",
        "description": "Book a train ticket.",
        "input_schema": {
            "type": "object",
            "properties": {
                "train_number":   {"type": "string", "description": "Train number"},
                "origin":         {"type": "string", "description": "Departure city"},
                "destination":    {"type": "string", "description": "Arrival city"},
                "date":           {"type": "string", "description": "Travel date in YYYY-MM-DD format"},
                "passenger_name": {"type": "string", "description": "Full name of the passenger"}
            },
            "required": ["train_number", "origin", "destination", "date", "passenger_name"]
        }
    },
    {
        "name": "rent_car",
        "description": "Search and reserve a rental car at a location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location":    {"type": "string", "description": "Pick-up city or airport"},
                "pickup_date": {"type": "string", "description": "Pick-up date in YYYY-MM-DD format"},
                "return_date": {"type": "string", "description": "Return date in YYYY-MM-DD format"},
                "car_type":    {"type": "string", "enum": ["economy", "compact", "suv", "luxury"], "description": "Type of car"}
            },
            "required": ["location", "pickup_date", "return_date", "car_type"]
        }
    },
    # Accommodation
    {
        "name": "search_hotels",
        "description": "Search for available hotels in a location for given dates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location":         {"type": "string", "description": "City or area to search in"},
                "check_in":         {"type": "string", "description": "Check-in date in YYYY-MM-DD format"},
                "check_out":        {"type": "string", "description": "Check-out date in YYYY-MM-DD format"},
                "budget_per_night": {"type": "number",  "description": "Maximum budget per night in USD"},
                "guests":           {"type": "integer", "description": "Number of guests"}
            },
            "required": ["location", "check_in", "check_out", "guests"]
        }
    },
    {
        "name": "book_hotel",
        "description": "Book a hotel room.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hotel_name": {"type": "string", "description": "Name of the hotel"},
                "location":   {"type": "string", "description": "City where the hotel is located"},
                "check_in":   {"type": "string", "description": "Check-in date in YYYY-MM-DD format"},
                "check_out":  {"type": "string", "description": "Check-out date in YYYY-MM-DD format"},
                "room_type":  {"type": "string", "enum": ["standard", "deluxe", "suite"], "description": "Room type"},
                "guests":     {"type": "integer", "description": "Number of guests"}
            },
            "required": ["hotel_name", "location", "check_in", "check_out", "room_type", "guests"]
        }
    },
    {
        "name": "check_hotel_availability",
        "description": "Check room availability at a specific hotel for given dates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hotel_name": {"type": "string", "description": "Name of the hotel"},
                "location":   {"type": "string", "description": "City where the hotel is located"},
                "check_in":   {"type": "string", "description": "Check-in date in YYYY-MM-DD format"},
                "check_out":  {"type": "string", "description": "Check-out date in YYYY-MM-DD format"}
            },
            "required": ["hotel_name", "location", "check_in", "check_out"]
        }
    },
    # Dining
    {
        "name": "search_restaurants",
        "description": "Find restaurants by cuisine type, price range, and location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location":    {"type": "string", "description": "City or neighbourhood"},
                "cuisine":     {"type": "string", "description": "Cuisine type e.g. Italian, Japanese, local"},
                "price_range": {"type": "string", "enum": ["budget", "mid-range", "fine-dining"], "description": "Price range"}
            },
            "required": ["location", "cuisine", "price_range"]
        }
    },
    {
        "name": "make_restaurant_reservation",
        "description": "Reserve a table at a restaurant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "restaurant_name": {"type": "string",  "description": "Name of the restaurant"},
                "location":        {"type": "string",  "description": "City where the restaurant is located"},
                "date":            {"type": "string",  "description": "Reservation date in YYYY-MM-DD format"},
                "time":            {"type": "string",  "description": "Reservation time e.g. 19:30"},
                "party_size":      {"type": "integer", "description": "Number of people"}
            },
            "required": ["restaurant_name", "location", "date", "time", "party_size"]
        }
    },
    {
        "name": "get_food_recommendations",
        "description": "Get recommended local dishes and food experiences for a destination.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City or country"}
            },
            "required": ["location"]
        }
    },
    # Planning & Logistics
    {
        "name": "create_itinerary",
        "description": "Generate a day-by-day travel itinerary for a destination.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location":   {"type": "string", "description": "Destination city or country"},
                "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD format"},
                "end_date":   {"type": "string", "description": "End date in YYYY-MM-DD format"},
                "interests":  {"type": "array", "items": {"type": "string"}, "description": "List of interests e.g. ['history', 'food', 'outdoor']"}
            },
            "required": ["location", "start_date", "end_date", "interests"]
        }
    },
    {
        "name": "calculate_budget",
        "description": "Estimate the total cost for a trip based on destination, duration, and travel style.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination":   {"type": "string",  "description": "Destination city or country"},
                "duration_days": {"type": "integer", "description": "Number of days"},
                "travel_style":  {"type": "string",  "enum": ["budget", "mid-range", "luxury"], "description": "Travel style"}
            },
            "required": ["destination", "duration_days", "travel_style"]
        }
    },
    {
        "name": "get_packing_suggestions",
        "description": "Suggest what to pack based on destination, duration, and planned activities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination":   {"type": "string",  "description": "Destination city or country"},
                "duration_days": {"type": "integer", "description": "Number of days"},
                "activities":    {"type": "array", "items": {"type": "string"}, "description": "Planned activities e.g. ['hiking', 'beach', 'business meetings']"}
            },
            "required": ["destination", "duration_days", "activities"]
        }
    },
    {
        "name": "get_visa_requirements",
        "description": "Check visa requirements for a passport holder traveling to a destination country.",
        "input_schema": {
            "type": "object",
            "properties": {
                "passport_country":    {"type": "string", "description": "Passport holder's country e.g. United States"},
                "destination_country": {"type": "string", "description": "Destination country"}
            },
            "required": ["passport_country", "destination_country"]
        }
    },
    # On-the-Ground
    {
        "name": "convert_currency",
        "description": "Convert an amount from one currency to another using current rates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount":        {"type": "number", "description": "Amount to convert"},
                "from_currency": {"type": "string", "description": "Source currency code e.g. USD"},
                "to_currency":   {"type": "string", "description": "Target currency code e.g. EUR"}
            },
            "required": ["amount", "from_currency", "to_currency"]
        }
    },
    {
        "name": "translate_phrase",
        "description": "Translate a phrase into a target language.",
        "input_schema": {
            "type": "object",
            "properties": {
                "phrase":           {"type": "string", "description": "Phrase to translate"},
                "target_language":  {"type": "string", "description": "Target language e.g. French, Japanese, Spanish"}
            },
            "required": ["phrase", "target_language"]
        }
    },
    {
        "name": "get_local_customs",
        "description": "Get etiquette tips and cultural norms for a country.",
        "input_schema": {
            "type": "object",
            "properties": {
                "country": {"type": "string", "description": "Country to get customs for"}
            },
            "required": ["country"]
        }
    },
    {
        "name": "get_emergency_contacts",
        "description": "Get local emergency numbers and contact information for a country.",
        "input_schema": {
            "type": "object",
            "properties": {
                "country": {"type": "string", "description": "Country to get emergency contacts for"}
            },
            "required": ["country"]
        }
    },
    {
        "name": "find_nearby_pharmacy",
        "description": "Find the nearest pharmacies to a given location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City, neighbourhood, or address"}
            },
            "required": ["location"]
        }
    },
    # Events & Tours
    {
        "name": "search_events",
        "description": "Find local events, concerts, or festivals on a specific date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City to search in"},
                "date":     {"type": "string", "description": "Event date in YYYY-MM-DD format"},
                "category": {"type": "string", "description": "Optional event category e.g. music, sports, festival, art"}
            },
            "required": ["location", "date"]
        }
    },
    {
        "name": "search_tours",
        "description": "Find guided tours available at a destination.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location":  {"type": "string", "description": "City or destination"},
                "tour_type": {"type": "string", "description": "Type of tour e.g. city tour, food tour, day trip, adventure"}
            },
            "required": ["location", "tour_type"]
        }
    },
    {
        "name": "book_tour",
        "description": "Book a guided tour.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tour_name":    {"type": "string",  "description": "Name of the tour"},
                "location":     {"type": "string",  "description": "City where the tour takes place"},
                "date":         {"type": "string",  "description": "Tour date in YYYY-MM-DD format"},
                "participants": {"type": "integer", "description": "Number of participants"}
            },
            "required": ["tour_name", "location", "date", "participants"]
        }
    }
]

# ── Mock implementations ──────────────────────────────────────────────────────

def _search_flights(args):
    origin, destination, date = args["origin"], args["destination"], args["date"]
    passengers = args.get("passengers", 1)
    airlines = ["Air France", "Delta", "British Airways", "Lufthansa", "Emirates", "United", "KLM"]
    results = []
    for _ in range(3):
        airline = random.choice(airlines)
        fn = f"{airline[:2].upper()}{random.randint(100, 999)}"
        price = random.randint(200, 1200) * passengers
        hour, minute = random.randint(6, 21), random.choice([0, 15, 30, 45])
        duration = random.randint(1, 14)
        results.append(f"{fn} | {airline} | {date} {hour:02d}:{minute:02d} | {duration}h | ${price}")
    return f"Flights from {origin} to {destination} on {date}:\n" + "\n".join(results)


def _book_flight(args):
    prices = {"economy": 350, "business": 1200, "first": 2800}
    price = prices.get(args["seat_class"], 350)
    confirmation = f"FLT{random.randint(100000, 999999)}"
    seat = f"{random.randint(1, 40)}{random.choice('ABCDEF')}"
    return (f"Booking confirmed! Confirmation: {confirmation} | Flight: {args['flight_number']} | "
            f"{args['origin']} → {args['destination']} on {args['date']} | "
            f"Passenger: {args['passenger_name']} | Class: {args['seat_class']} | Seat: {seat} | Price: ${price}")


def _search_trains(args):
    origin, destination, date = args["origin"], args["destination"], args["date"]
    operators = ["Eurostar", "TGV", "ICE", "Thalys", "Intercity"]
    results = []
    for _ in range(3):
        op = random.choice(operators)
        tn = f"{op[:3].upper()}{random.randint(100, 9999)}"
        price = random.randint(30, 300)
        hour, minute = random.randint(6, 20), random.choice([0, 15, 30, 45])
        duration = random.randint(1, 8)
        results.append(f"{tn} | {op} | {date} {hour:02d}:{minute:02d} | {duration}h | ${price}")
    return f"Trains from {origin} to {destination} on {date}:\n" + "\n".join(results)


def _book_train(args):
    price = random.randint(30, 300)
    confirmation = f"TRN{random.randint(100000, 999999)}"
    seat = f"Car {random.randint(1, 10)}, Seat {random.randint(1, 80)}"
    return (f"Train booked! Confirmation: {confirmation} | Train: {args['train_number']} | "
            f"{args['origin']} → {args['destination']} on {args['date']} | "
            f"Passenger: {args['passenger_name']} | {seat} | Price: ${price}")


def _rent_car(args):
    companies = ["Hertz", "Avis", "Enterprise", "Budget", "Sixt"]
    prices_per_day = {"economy": 35, "compact": 50, "suv": 80, "luxury": 150}
    price_per_day = prices_per_day.get(args["car_type"], 50)
    try:
        days = (datetime.strptime(args["return_date"], "%Y-%m-%d") - datetime.strptime(args["pickup_date"], "%Y-%m-%d")).days
    except ValueError:
        days = 1
    confirmation = f"CAR{random.randint(100000, 999999)}"
    return (f"Car reserved! Confirmation: {confirmation} | {random.choice(companies)} | "
            f"{args['car_type'].capitalize()} | {args['location']} | "
            f"{args['pickup_date']} → {args['return_date']} ({days} days) | "
            f"${price_per_day}/day | Total: ${price_per_day * days}")


def _search_hotels(args):
    location = args["location"]
    budget = args.get("budget_per_night", 500)
    hotels_by_city = {
        "paris":    ["Hotel Le Marais", "Hôtel de Ville", "Le Petit Boutique", "Grand Paris Hotel"],
        "new york": ["The Manhattan Inn", "Brooklyn Boutique Hotel", "Midtown Suites", "Central Park View Hotel"],
        "tokyo":    ["Shinjuku Garden Hotel", "Asakusa Traditional Inn", "Tokyo Bay Hotel", "Shibuya Cross Hotel"],
    }
    city = location.lower().split(',')[0].strip()
    names = hotels_by_city.get(city, [f"{location} Grand Hotel", f"{location} City Inn", f"The {location} Suites"])
    results = []
    for name in names[:3]:
        price = random.randint(80, min(int(budget), 450))
        stars = random.randint(3, 5)
        rating = round(random.uniform(7.5, 9.8), 1)
        results.append(f"{'★' * stars} {name} | ${price}/night | Rating: {rating}/10")
    return (f"Hotels in {location} ({args['check_in']} → {args['check_out']}, {args['guests']} guests):\n"
            + "\n".join(results))


def _book_hotel(args):
    prices = {"standard": 120, "deluxe": 200, "suite": 400}
    price_per_night = prices.get(args["room_type"], 120)
    try:
        days = (datetime.strptime(args["check_out"], "%Y-%m-%d") - datetime.strptime(args["check_in"], "%Y-%m-%d")).days
    except ValueError:
        days = 1
    confirmation = f"HTL{random.randint(100000, 999999)}"
    return (f"Hotel booked! Confirmation: {confirmation} | {args['hotel_name']}, {args['location']} | "
            f"{args['room_type'].capitalize()} room | {args['check_in']} → {args['check_out']} ({days} nights) | "
            f"{args['guests']} guests | ${price_per_night}/night | Total: ${price_per_night * days}")


def _check_hotel_availability(args):
    available = random.choices([True, False], weights=[3, 1])[0]
    if available:
        room_types = random.sample(["standard", "deluxe", "suite"], random.randint(1, 3))
        prices = {"standard": random.randint(100, 150), "deluxe": random.randint(180, 250), "suite": random.randint(350, 500)}
        room_info = ", ".join([f"{r} (${prices[r]}/night)" for r in room_types])
        return (f"{args['hotel_name']} in {args['location']}: Available for "
                f"{args['check_in']} → {args['check_out']} | Rooms: {room_info}")
    return (f"{args['hotel_name']} in {args['location']}: No availability for "
            f"{args['check_in']} → {args['check_out']}. Consider nearby dates or alternative hotels.")


def _search_restaurants(args):
    price_symbols = {"budget": "$", "mid-range": "$$", "fine-dining": "$$$"}
    symbol = price_symbols.get(args["price_range"], "$$")
    adjectives = ["Le Petit", "The Golden", "Casa", "La Bella", "The Rustic", "Urban", "Classic"]
    nouns = ["Bistro", "Kitchen", "Eatery", "Table", "Garden", "Corner", "House"]
    results = []
    for _ in range(4):
        name = f"{random.choice(adjectives)} {random.choice(nouns)}"
        rating = round(random.uniform(3.5, 5.0), 1)
        results.append(f"{name} | {args['cuisine']} | {symbol} | Rating: {rating}/5")
    return f"{args['cuisine']} restaurants in {args['location']} ({args['price_range']}):\n" + "\n".join(results)


def _make_restaurant_reservation(args):
    confirmation = f"RST{random.randint(10000, 99999)}"
    return (f"Reservation confirmed! Confirmation: {confirmation} | {args['restaurant_name']}, {args['location']} | "
            f"{args['date']} at {args['time']} | Party of {args['party_size']}")


def _get_food_recommendations(args):
    location = args["location"]
    food_by_city = {
        "paris":    "Croissants, Coq au Vin, French Onion Soup, Crème Brûlée, Escargot. Must-try: steak frites at a brasserie.",
        "tokyo":    "Ramen, Sushi, Tempura, Yakitori, Takoyaki, Matcha desserts. Must-try: omakase at a local sushi counter.",
        "new york": "NY-style pizza, bagels with lox, pastrami on rye, hot dogs, cheesecake. Must-try: a deli sandwich in Midtown.",
        "rome":     "Cacio e Pepe, Carbonara, Supplì, Gelato, Maritozzi. Must-try: pizza al taglio from a local bakery.",
        "bangkok":  "Pad Thai, Tom Yum, Mango Sticky Rice, Som Tum, Khao Man Gai. Must-try: street food at Yaowarat Road.",
    }
    city = location.lower().split(',')[0].strip()
    tips = food_by_city.get(city, f"Explore local street food markets and ask residents for neighbourhood favourites in {location}.")
    return f"Food recommendations for {location}: {tips}"


def _create_itinerary(args):
    location, start_date, end_date = args["location"], args["start_date"], args["end_date"]
    interests = args.get("interests", ["sightseeing"])
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        days = (datetime.strptime(end_date, "%Y-%m-%d") - start).days + 1
    except ValueError:
        start, days = datetime.today(), 3

    activity_pool = {
        "history":     ["Visit the old town", "Tour a local museum", "Explore ancient ruins", "Historical walking tour"],
        "food":        ["Morning food market visit", "Cooking class", "Street food tour", "Fine dining dinner"],
        "outdoor":     ["Hike a local trail", "Cycling tour", "Visit a national park", "Sunrise viewpoint"],
        "art":         ["Contemporary art museum", "Gallery hopping", "Street art walk", "Artisan workshop"],
        "sightseeing": ["Iconic landmark visit", "Panoramic viewpoint", "Neighbourhood stroll", "Sunset cruise"],
    }

    lines = [f"Itinerary for {location} ({start_date} → {end_date}), interests: {', '.join(interests)}"]
    for day in range(min(days, 7)):
        date_str = (start + timedelta(days=day)).strftime("%Y-%m-%d")
        activities = [random.choice(activity_pool.get(i, activity_pool["sightseeing"])) for i in interests[:2]]
        lines.append(f"Day {day + 1} ({date_str}): {' | '.join(activities)}")
    return "\n".join(lines)


def _calculate_budget(args):
    daily_costs = {
        "budget":    {"accommodation": 40,  "food": 25,  "transport": 10, "activities": 15},
        "mid-range": {"accommodation": 120, "food": 60,  "transport": 20, "activities": 40},
        "luxury":    {"accommodation": 400, "food": 200, "transport": 80, "activities": 150},
    }
    costs = daily_costs.get(args["travel_style"], daily_costs["mid-range"])
    per_day = sum(costs.values())
    total = per_day * args["duration_days"]
    breakdown = " | ".join([f"{k}: ${v}/day" for k, v in costs.items()])
    return (f"Budget estimate for {args['duration_days']} days in {args['destination']} "
            f"({args['travel_style']}): {breakdown} | Daily: ${per_day} | Trip total: ~${total}")


def _get_packing_suggestions(args):
    essentials = ["passport/ID", "travel insurance documents", "phone charger", "power adapter", "medication"]
    clothing = [f"{min(args['duration_days'] + 1, 7)} days of clothes", "comfortable walking shoes"]
    activity_items = {
        "hiking":            ["hiking boots", "trekking poles", "moisture-wicking layers", "first aid kit"],
        "beach":             ["swimsuit", "sunscreen SPF 50+", "flip flops", "beach towel"],
        "business meetings": ["formal attire", "business cards", "laptop", "smart shoes"],
        "skiing":            ["thermal base layers", "ski gloves", "goggles", "lip balm"],
        "cycling":           ["padded shorts", "helmet", "gloves", "repair kit"],
    }
    packing = essentials + clothing
    for activity in args.get("activities", []):
        packing += activity_items.get(activity.lower(), [])
    activities_str = ', '.join(args.get('activities', [])) or 'general'
    return (f"Packing list for {args['duration_days']} days in {args['destination']} "
            f"(activities: {activities_str}): {', '.join(packing)}")


def _get_visa_requirements(args):
    passport, destination = args["passport_country"], args["destination_country"]
    visa_free_pairs = {
        ("United States", "France"), ("United States", "Japan"), ("United States", "United Kingdom"),
        ("United Kingdom", "France"), ("United Kingdom", "Germany"), ("Australia", "United Kingdom"),
        ("Canada", "France"), ("Germany", "Japan"), ("United States", "Germany"),
    }
    if (passport, destination) in visa_free_pairs or (destination, passport) in visa_free_pairs:
        return (f"Visa-free: {passport} passport holders can enter {destination} for up to 90 days. "
                f"Ensure your passport is valid for at least 6 months beyond your travel dates.")
    return (f"Visa required: {passport} passport holders need a visa for {destination}. "
            f"Apply at least 4–6 weeks in advance at the {destination} embassy or consulate.")


def _convert_currency(args):
    rates_to_usd = {
        "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "AUD": 1.53,
        "CAD": 1.36, "CHF": 0.89, "CNY": 7.24, "HKD": 7.82, "SGD": 1.34,
        "THB": 35.1, "MXN": 17.2, "BRL": 4.97, "INR": 83.1, "KRW": 1325.0,
    }
    src, dst = args["from_currency"].upper(), args["to_currency"].upper()
    if src not in rates_to_usd or dst not in rates_to_usd:
        return f"Unsupported currency. Supported: {', '.join(rates_to_usd)}"
    converted = args["amount"] / rates_to_usd[src] * rates_to_usd[dst]
    rate = rates_to_usd[dst] / rates_to_usd[src]
    return f"{args['amount']} {src} = {converted:.2f} {dst} (rate: 1 {src} = {rate:.4f} {dst})"


def _translate_phrase(args):
    phrase, lang = args["phrase"], args["target_language"].lower()
    dictionary = {
        "hello":                  {"french": "Bonjour", "spanish": "Hola", "japanese": "こんにちは (Konnichiwa)", "german": "Hallo", "italian": "Ciao", "mandarin": "你好 (Nǐ hǎo)"},
        "thank you":              {"french": "Merci", "spanish": "Gracias", "japanese": "ありがとう (Arigatō)", "german": "Danke", "italian": "Grazie", "mandarin": "谢谢 (Xièxiè)"},
        "where is the bathroom":  {"french": "Où sont les toilettes?", "spanish": "¿Dónde está el baño?", "japanese": "トイレはどこですか？", "german": "Wo ist die Toilette?", "italian": "Dov'è il bagno?"},
        "how much does this cost": {"french": "Combien ça coûte?", "spanish": "¿Cuánto cuesta?", "japanese": "これはいくらですか？", "german": "Was kostet das?", "italian": "Quanto costa?"},
        "i need help":            {"french": "J'ai besoin d'aide", "spanish": "Necesito ayuda", "japanese": "助けてください (Tasukete kudasai)", "german": "Ich brauche Hilfe", "italian": "Ho bisogno di aiuto"},
        "excuse me":              {"french": "Excusez-moi", "spanish": "Perdón", "japanese": "すみません (Sumimasen)", "german": "Entschuldigung", "italian": "Scusi"},
    }
    translation = dictionary.get(phrase.lower(), {}).get(lang)
    if translation:
        return f'"{phrase}" in {lang.capitalize()}: {translation}'
    return f'"{phrase}" in {lang.capitalize()}: [Translation unavailable in mock — would call a translation API in production]'


def _get_local_customs(args):
    customs = {
        "japan":          "Remove shoes before entering homes. Bow as a greeting. Tipping is considered rude. Use two hands when giving/receiving cards or gifts.",
        "france":         "Say 'Bonjour' before any interaction. La bise (cheek kiss) is a common greeting. Dress modestly at churches. Tipping is appreciated but not mandatory.",
        "india":          "Remove footwear before entering temples. Use your right hand for eating and exchanging items. Dress modestly at religious sites.",
        "thailand":       "Never touch someone's head. Point feet away from people and sacred objects. Dress modestly at temples. Remove shoes at sacred spaces.",
        "united states":  "Tipping 15–20% is expected at restaurants. Personal space is valued. Greet with a handshake.",
        "germany":        "Punctuality is important. Firm handshake greeting. Separate recycling carefully. Tipping 5–10% is appreciated.",
        "italy":          "Dress modestly at churches (cover shoulders and knees). Greet with a kiss on each cheek. Avoid cappuccino after meals — it's a morning drink.",
        "united kingdom": "Queue patiently and never jump the line. 'Please' and 'thank you' are used frequently. Tipping 10–15% at restaurants is customary.",
    }
    country = args["country"].lower()
    tips = customs.get(country, f"For {args['country']}: dress modestly at religious sites, learn a few local phrases, and observe how locals behave in public.")
    return f"Local customs for {args['country']}: {tips}"


def _get_emergency_contacts(args):
    contacts = {
        "france":         {"Police": "17", "Ambulance": "15", "Fire": "18", "General emergency": "112"},
        "japan":          {"Police": "110", "Ambulance & Fire": "119"},
        "united states":  {"Police / Ambulance / Fire": "911"},
        "united kingdom": {"Police / Ambulance / Fire": "999", "Non-emergency police": "101"},
        "australia":      {"Police / Ambulance / Fire": "000"},
        "germany":        {"Police": "110", "Ambulance & Fire": "112"},
        "thailand":       {"Police": "191", "Ambulance": "1669", "Tourist Police": "1155"},
        "italy":          {"Police": "113", "Ambulance": "118", "Fire": "115", "General emergency": "112"},
    }
    country = args["country"].lower()
    if country in contacts:
        nums = " | ".join([f"{k}: {v}" for k, v in contacts[country].items()])
        return f"Emergency contacts for {args['country']}: {nums}"
    return f"Emergency contacts for {args['country']}: General international emergency: 112. Contact your embassy for country-specific numbers."


def _find_nearby_pharmacy(args):
    names = ["MedPlus Pharmacy", "City Pharmacy", "Green Cross Chemist", "HealthCare Plus", "Pharmazone", "Wellness Pharmacy"]
    results = []
    for _ in range(3):
        distance = round(random.uniform(0.1, 1.5), 1)
        is_24h = random.choice([True, False])
        hours = "Open 24 hours" if is_24h else f"Open {random.randint(7, 9)}:00–{random.randint(20, 22)}:00"
        results.append(f"{random.choice(names)} | {distance}km away | {hours}")
    return f"Nearby pharmacies in {args['location']}:\n" + "\n".join(results)


def _search_events(args):
    location, date = args["location"], args["date"]
    category = args.get("category", "all")
    event_pool = {
        "music":    ["Jazz Night at Blue Note", "Classical Concert at City Hall", "Rock Festival at Riverside Park", "Open Mic Night"],
        "sports":   ["City Marathon", "Football Match", "Tennis Open", "Cycling Race"],
        "festival": ["Street Food Festival", "Cultural Heritage Fair", "Night Market", "Lantern Festival"],
        "art":      ["Gallery Opening", "Street Art Tour", "Film Screening", "Photography Exhibition"],
        "all":      ["Jazz Night", "City Marathon", "Street Food Festival", "Gallery Opening", "Local Craft Fair"],
    }
    events = event_pool.get(category.lower() if category else "all", event_pool["all"])
    results = []
    for event in random.sample(events, min(3, len(events))):
        time = f"{random.randint(10, 20)}:00"
        price = random.choice(["Free", f"${random.randint(10, 80)}"])
        results.append(f"{event} | {date} {time} | {price}")
    return f"Events in {location} on {date} (category: {category or 'all'}):\n" + "\n".join(results)


def _search_tours(args):
    location, tour_type = args["location"], args["tour_type"]
    tour_pool = {
        "city tour": ["Historic City Walking Tour (3h, $25)", "Hop-On Hop-Off Bus Tour (full day, $40)", "Evening City Lights Tour (2h, $35)"],
        "food tour":  ["Street Food Night Tour (3h, $55)", "Local Market & Cooking Tour (4h, $75)", "Wine & Cheese Tasting (2h, $65)"],
        "day trip":   [f"Day Trip to nearby countryside ($80)", f"Full-Day Historical Excursion ($95)", f"Scenic Drive & Hike ($70)"],
        "adventure":  ["Kayaking & Snorkelling (5h, $90)", "Rock Climbing Half Day ($85)", "Paragliding Experience ($120)"],
    }
    tours = tour_pool.get(tour_type.lower(), [f"{tour_type.capitalize()} Tour in {location} (3h, $45)", f"Premium {tour_type.capitalize()} Experience (5h, $85)"])
    return f"{tour_type.capitalize()} tours in {location}:\n" + "\n".join(tours)


def _book_tour(args):
    price_per_person = random.randint(30, 150)
    confirmation = f"TUR{random.randint(100000, 999999)}"
    meeting_point = random.choice(["Main city square", "Hotel lobby pickup", "Central train station", "Tourist information centre"])
    total = price_per_person * args["participants"]
    return (f"Tour booked! Confirmation: {confirmation} | {args['tour_name']} | {args['location']} | "
            f"{args['date']} | {args['participants']} participant(s) | Meeting: {meeting_point} | "
            f"${price_per_person}/person | Total: ${total}")


# ── Dispatcher ────────────────────────────────────────────────────────────────

_HANDLERS = {
    "search_flights":             _search_flights,
    "book_flight":                _book_flight,
    "search_trains":              _search_trains,
    "book_train":                 _book_train,
    "rent_car":                   _rent_car,
    "search_hotels":              _search_hotels,
    "book_hotel":                 _book_hotel,
    "check_hotel_availability":   _check_hotel_availability,
    "search_restaurants":         _search_restaurants,
    "make_restaurant_reservation":_make_restaurant_reservation,
    "get_food_recommendations":   _get_food_recommendations,
    "create_itinerary":           _create_itinerary,
    "calculate_budget":           _calculate_budget,
    "get_packing_suggestions":    _get_packing_suggestions,
    "get_visa_requirements":      _get_visa_requirements,
    "convert_currency":           _convert_currency,
    "translate_phrase":           _translate_phrase,
    "get_local_customs":          _get_local_customs,
    "get_emergency_contacts":     _get_emergency_contacts,
    "find_nearby_pharmacy":       _find_nearby_pharmacy,
    "search_events":              _search_events,
    "search_tours":               _search_tours,
    "book_tour":                  _book_tour,
}

def execute_function_call(tool_call):
    handler = _HANDLERS.get(tool_call.name)
    if handler:
        return handler(tool_call.input)
    return f"Function '{tool_call.name}' not implemented"


# ── Agent ─────────────────────────────────────────────────────────────────────

def trip_planner_single_round(user_message):
    system = "You are a comprehensive travel planning assistant. Help users plan trips by using the available tools for flights, trains, hotels, restaurants, tours, events, budgeting, packing, visas, currency, translation, local customs, and emergency info. Be thorough and proactive in using multiple tools to give complete advice."
    messages = [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=messages,
        tools=tools
    )

    text_blocks = [b for b in response.content if b.type == "text"]
    tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

    if text_blocks:
        print("Assistant:", text_blocks[0].text)

    if tool_use_blocks:
        print("\nExecuting functions...")
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tool_call in tool_use_blocks:
            print(f"  Calling: {tool_call.name}")
            result = execute_function_call(tool_call)
            print(f"  Result: {result}\n")
            tool_results.append({"type": "tool_result", "tool_use_id": tool_call.id, "content": result})

        messages.append({"role": "user", "content": tool_results})

        final_response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=tools
        )
        final_text = [b for b in final_response.content if b.type == "text"]
        if final_text:
            print("\nFinal response:")
            print("Assistant:", final_text[0].text)


if __name__ == "__main__":
    test_queries = [
        "I'm planning a 5-day trip to Tokyo in mid-June. I have a US passport. Can you check visa requirements, estimate the budget for a mid-range trip, suggest what to pack, and find a food tour?",
        "I need to get from Paris to Rome next Friday. What are my transport options, and can you find me a mid-range Italian restaurant in Rome for dinner on arrival?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"TEST QUERY {i}: {query}")
        print('=' * 60)
        trip_planner_single_round(query)
