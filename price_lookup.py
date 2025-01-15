import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
import re

logger = logging.getLogger(__name__)

def get_watchcount_prices(title_input, media_type="DVD"):
    """
    Look up prices on WatchCount.com for multiple titles
    Returns individual price info for each title
    """
    # Split by newlines and clean up
    titles = [t.strip().lstrip('- ') for t in title_input.splitlines() if t.strip()]
    
    results = []
    for title in titles:
        try:
            # Format the search URL with media type
            search_term = f"{title} {media_type}"
            encoded_title = urllib.parse.quote(search_term)
            url = f"https://www.watchcount.com/sold/{encoded_title}/-/all"
            logger.info(f"Original title: {search_term}")
            logger.info(f"Encoded title: {encoded_title}")
            logger.info(f"Full URL: {url}")
            
            # Fetch the page content
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            if response.text:
                soup = BeautifulSoup(response.text, 'html.parser')
                prices = parse_prices(str(soup))
                results.append({
                    "title": title,
                    "type": media_type,
                    "average": prices.get('average', 0),
                    "lowest": prices.get('lowest', 0),
                    "highest": prices.get('highest', 0),
                    "count": prices.get('count', 0)
                })
                
        except Exception as e:
            logger.error(f"Error looking up prices for {title}: {str(e)}")
            results.append({
                "title": title,
                "type": media_type,
                "average": 0,
                "lowest": 0,
                "highest": 0,
                "count": 0
            })
    
    return results

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
