import trafilatura
import urllib.parse
import logging
import re

logger = logging.getLogger(__name__)

def get_watchcount_prices(title):
    """
    Look up DVD prices on WatchCount.com
    """
    try:
        # Format the search URL
        encoded_title = urllib.parse.quote(title)
        url = f"https://www.watchcount.com/sold.php?search={encoded_title}&bcat=617"
        
        # Fetch the page content
        downloaded = trafilatura.fetch_url(url)
        content = trafilatura.extract(downloaded)
        
        if not content:
            return {"error": "No results found"}

        # Parse prices from the content
        prices = parse_prices(content)
        
        return {
            "average_price": prices.get("average", 0),
            "lowest_price": prices.get("lowest", 0),
            "highest_price": prices.get("highest", 0),
            "num_results": prices.get("count", 0)
        }

    except Exception as e:
        logger.error(f"Error looking up prices: {str(e)}")
        return {"error": "Error fetching price information"}

def parse_prices(content):
    """
    Parse price information from WatchCount.com content
    """
    prices = []
    # Look for price patterns ($XX.XX)
    price_matches = re.findall(r'\$(\d+\.?\d*)', content)
    
    for match in price_matches:
        try:
            prices.append(float(match))
        except ValueError:
            continue

    if not prices:
        return {
            "average": 0,
            "lowest": 0,
            "highest": 0,
            "count": 0
        }

    return {
        "average": sum(prices) / len(prices),
        "lowest": min(prices),
        "highest": max(prices),
        "count": len(prices)
    }
