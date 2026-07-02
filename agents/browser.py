import webbrowser
import urllib.parse

class BrowserAgent:
    def __init__(self):
        pass

    def open_url(self, url):
        try:
            # Add prefix if missing
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            webbrowser.open(url)
            return f"Opening browser link: {url}"
        except Exception as e:
            return f"Failed to open URL: {str(e)}"

    def search_google(self, query):
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            webbrowser.open(url)
            return f"Searching Google for: '{query}'"
        except Exception as e:
            return f"Failed to perform search: {str(e)}"
