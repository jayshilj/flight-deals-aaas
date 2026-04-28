import os
from langchain_core.tools import tool
from serpapi import GoogleSearch

@tool
def search_hotel_prices(query: str, check_in_date: str, check_out_date: str) -> str:
    """
    Search for hotel prices using Google Hotels.
    Args:
        query: Location or hotel name (e.g., 'Denver, CO' or 'Marriott Denver')
        check_in_date: Date in YYYY-MM-DD format
        check_out_date: Date in YYYY-MM-DD format
    """
    params = {
        "engine": "google_hotels",
        "q": query,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "currency": "USD",
        "hl": "en",
        "gl": "us",
        "api_key": os.getenv("SERPAPI_API_KEY")
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            return f"API Error: {results['error']}"

        properties = results.get("properties", [])
        
        if not properties:
            return f"No hotels found for {query} between {check_in_date} and {check_out_date}."

        output_lines = [f"🏨 Hotels for '{query}' ({check_in_date} to {check_out_date})\n"]

        for i, hotel in enumerate(properties[:5], 1):
            name = hotel.get("name", "Unknown Hotel")
            price = hotel.get("rate_per_night", {}).get("lowest", "N/A")
            total_price = hotel.get("total_rate", {}).get("lowest", "N/A")
            rating = hotel.get("overall_rating", "N/A")
            reviews = hotel.get("reviews", 0)
            class_rating = hotel.get("extracted_hotel_class", "N/A")
            amenities = hotel.get("amenities", [])
            
            amenity_str = ", ".join(amenities[:3]) if amenities else "No top amenities listed"
            
            output_lines.append(
                f"{'─'*40}\n"
                f"Option {i} | {name} ({class_rating} Stars)\n"
                f"💰 Price: ${price}/night (Total: ${total_price})\n"
                f"⭐ Rating: {rating}/5 ({reviews} reviews)\n"
                f"✨ Amenities: {amenity_str}"
            )

        return "\n".join(output_lines)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Unexpected error: {str(e)}"
