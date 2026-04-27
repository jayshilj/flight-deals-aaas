import os
from langchain_core.tools import tool
from serpapi import GoogleSearch

@tool
def search_flight_prices(origin: str, destination: str, departure_date: str,
                          return_date: str = "", trip_type: str = "one_way") -> str:
    """
    Search for real flight prices between two airports using Google Flights.
    Args:
        origin: Departure airport IATA code (e.g. 'AUS' for Austin)
        destination: Arrival airport IATA code (e.g. 'LAX' for Los Angeles)
        departure_date: Date in YYYY-MM-DD format (e.g. '2026-04-10')
        return_date: Return date in YYYY-MM-DD (only for round trips)
        trip_type: 'one_way' or 'round_trip'
    """
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": departure_date,
        "currency": "USD",
        "hl": "en",
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "type": "2" if trip_type == "one_way" else "1",
        "sort_by": "2"  # sort by price
    }

    if return_date and trip_type == "round_trip":
        params["return_date"] = return_date

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        # Catch API-level errors
        if "error" in results:
            return f"API Error: {results['error']}"

        # SerpApi puts results in best_flights OR other_flights [web:114]
        best_flights = results.get("best_flights", [])
        other_flights = results.get("other_flights", [])
        all_flights = (best_flights + other_flights)[:5]

        # Fallback check for missing flights array in search
        if not all_flights:
            return f"No flights found from {origin} to {destination} on {departure_date}. The airline schedules might not be published yet, or the route may not exist. Please advise the user to try a different date or nearby airport."

        output_lines = [f"✈ Flights from {origin} → {destination} on {departure_date}\n"]

        for i, flight in enumerate(all_flights, 1):
            price = flight.get("price", "N/A")
            total_duration = flight.get("total_duration", 0)
            hours = total_duration // 60
            mins = total_duration % 60

            legs = flight.get("flights", [])
            if not legs:
                continue

            first_leg = legs[0]
            last_leg = legs[-1]
            airline = first_leg.get("airline", "Unknown Airline")
            airline_logo = first_leg.get("airline_logo", "")
            flight_number = first_leg.get("flight_number", "N/A")
            dep_time = first_leg.get("departure_airport", {}).get("time", "N/A")
            dep_airport = first_leg.get("departure_airport", {}).get("name", origin)
            arr_time = last_leg.get("arrival_airport", {}).get("time", "N/A")
            arr_airport = last_leg.get("arrival_airport", {}).get("name", destination)
            stops = len(legs) - 1
            stop_label = "🟢 Nonstop" if stops == 0 else f"🔴 {stops} stop(s)"
            tag = "⭐ BEST DEAL" if i == 1 and best_flights else f"Option {i}"

            # Carbon emissions
            carbon = flight.get("carbon_emissions", {})
            carbon_diff = carbon.get("difference_percent", None)
            carbon_note = ""
            if carbon_diff is not None:
                carbon_note = f"🌿 {abs(carbon_diff)}% {'less' if carbon_diff < 0 else 'more'} emissions than typical"

            output_lines.append(
                f"{'─'*40}\n"
                f"{tag} | {airline} ({flight_number})\n"
                f"💰 Price: ${price} USD\n"
                f"🕐 {dep_time} ({dep_airport}) → {arr_time} ({arr_airport})\n"
                f"⏱ Duration: {hours}h {mins}m | {stop_label}\n"
                f"{carbon_note}"
            )

        # Price insights
        price_insights = results.get("price_insights", {})
        typical_range = price_insights.get("typical_price_range", [])
        price_level = price_insights.get("price_level", "")
        if typical_range:
            output_lines.append(f"\n{'─'*40}\n📊 Typical range: ${typical_range[0]}–${typical_range[1]} | Price level: {price_level}")

        return "\n".join(output_lines)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Unexpected error: {str(e)}"