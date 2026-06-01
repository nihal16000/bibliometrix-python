import requests
import time

class OpenAlexRetriever:
    """
    Extract Phase: OpenAlex API Retriever.
    
    This class is responsible for connecting to the OpenAlex REST API, bypassing the 
    need for manual CSV downloads. It automates the data extraction process by 
    handling HTTP requests, pagination, and rate-limiting (retries) dynamically.
    """
    BASE_URL = "https://api.openalex.org/works"
    
    def __init__(self, email: str = "example@example.com"):
        """
        Initializes the retriever and sets up the polite pool.
        
        Args:
            email (str): An email address used to access OpenAlex's polite pool 
                         for faster response times and better rate limits.
        """
        self.email = email
        self.session = requests.Session()
        
        # Adding email to the User-Agent registers the request with the polite pool
        self.session.headers.update({"User-Agent": f"mailto:{self.email}"})

    def fetch(self, query: str, max_results: int = 100) -> list:
        """
        Fetches metadata from OpenAlex for a given textual query.
        
        This method fully automates extraction by looping through paginated results
        until the desired max_results limit is reached.
        
        Args:
            query (str): The search term (e.g., "machine learning").
            max_results (int): The maximum number of documents to retrieve.
            
        Returns:
            list: A list of dictionaries, where each dictionary is a raw OpenAlex document.
        """
        results = []
        # OpenAlex allows a maximum of 200 per page, but we use 50 to ensure stable loads
        per_page = min(50, max_results)
        page = 1
        
        while len(results) < max_results:
            params = {
                "search": query,
                "per-page": per_page,
                "page": page
            }
            
            # Rate limit and network error handling
            retries = 3
            for attempt in range(retries):
                response = self.session.get(self.BASE_URL, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    works = data.get("results", [])
                    
                    if not works:
                        return results # No more results available in the database
                        
                    results.extend(works)
                    break # Success, break out of retry loop
                    
                elif response.status_code == 429:
                    print(f"[Warning] Rate limited by OpenAlex. Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                else:
                    print(f"[Error] API Error {response.status_code}: {response.text}")
                    break # Stop retrying on permanent errors
            
            page += 1
            # Rate limit handling: Sleep slightly to respect polite pool limits
            time.sleep(0.1)
            
            # Truncate if we fetched slightly more than max_results due to page sizes
            if len(results) >= max_results:
                results = results[:max_results]
                break

        return results
