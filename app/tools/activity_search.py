import os
from langchain_core.tools import tool
from serpapi import GoogleSearch

@tool
def search_local_activities(query: str) -> str:
    """
    Search for local activities, itineraries, or restaurants using Google Search.
    Args:
        query: What to search for (e.g., 'Top things to do in Denver', '3 day itinerary for Paris')
    """
    params = {
        "engine": "google",
        "q": query,
        "api_key": os.getenv("SERPAPI_API_KEY")
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            return f"API Error: {results['error']}"

        organic_results = results.get("organic_results", [])
        local_results = results.get("local_results", [])
        
        if not organic_results and not local_results:
            return f"No activities or itineraries found for '{query}'."

        output_lines = [f"📍 Activity Search Results for '{query}'\n"]

        # If there are local places, list them first
        if local_results:
            if isinstance(local_results, list):
                output_lines.append("Top Local Places:")
                for i, place in enumerate(local_results[:3], 1):
                    name = place.get("title", "Unknown")
                    rating = place.get("rating", "N/A")
                    output_lines.append(f"- {name} (⭐ {rating})")
            output_lines.append("\n")

        # List organic web results
        output_lines.append("Helpful Guides & Itineraries:")
        for i, result in enumerate(organic_results[:3], 1):
            title = result.get("title", "Unknown Title")
            snippet = result.get("snippet", "No description available.")
            link = result.get("link", "#")
            
            output_lines.append(
                f"{'─'*40}\n"
                f"{i}. {title}\n"
                f"📝 {snippet}\n"
                f"🔗 {link}"
            )

        return "\n".join(output_lines)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Unexpected error: {str(e)}"
