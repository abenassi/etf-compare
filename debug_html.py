import requests
import os
from bs4 import BeautifulSoup

def save_sample_html(url, output_file='sample_page.html'):
    """
    Save the HTML content of a URL to a file for debugging purposes.
    
    Args:
        url (str): URL to fetch
        output_file (str): Path to save the HTML content
    """
    print(f"Fetching HTML from: {url}")
    
    # Use a realistic user agent to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Save the raw HTML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"HTML saved to {output_file}")
        
        # Parse and print some basic information about the page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Print the title
        title = soup.title.string if soup.title else "No title found"
        print(f"Page title: {title}")
        
        # Look for different types of containers that might hold our metrics
        div_containers = {
            'et_pb_text_inner': soup.find_all('div', class_='et_pb_text_inner'),
            'table_containers': soup.find_all('table'),
            'data_divs': soup.find_all('div', class_=lambda c: c and 'data' in c.lower()),
            'metric_divs': soup.find_all('div', class_=lambda c: c and ('metric' in c.lower() or 'stat' in c.lower())),
            'all_divs_with_percent': []
        }
        
        # Look for text containing percentage values, which might be our metrics
        for div in soup.find_all('div'):
            text = div.get_text()
            if '%' in text and any(term in text.lower() for term in ['return', 'deviation', 'yield']):
                div_containers['all_divs_with_percent'].append(div)
        
        # Print summary of found elements
        for container_type, elements in div_containers.items():
            print(f"Found {len(elements)} elements of type '{container_type}'")
            
            # Print a sample of the first element if available
            if elements and container_type != 'all_divs_with_percent':
                sample = elements[0].get_text().strip()
                if len(sample) > 100:
                    sample = sample[:100] + "..."
                print(f"Sample content: {sample}")
        
        # If we found divs with percentage values, analyze them more closely
        if div_containers['all_divs_with_percent']:
            print("\nDetailed analysis of divs containing percentage values:")
            for i, div in enumerate(div_containers['all_divs_with_percent'][:5]):  # Show first 5 only
                text = div.get_text().strip()
                parent_class = div.parent.get('class', 'No class')
                print(f"{i+1}. Text: {text[:100]}... | Parent class: {parent_class}")
        
        return True
    
    except Exception as e:
        print(f"Error saving HTML: {e}")
        return False

if __name__ == "__main__":
    # Test with a few URLs
    urls_to_test = [
        "https://www.lazyportfolioetf.com/etf/spdr-sp-500-spy/",
        "https://www.lazyportfolioetf.com/allocation/all-weather-portfolio/"
    ]
    
    for i, url in enumerate(urls_to_test):
        output_file = f"sample_page_{i+1}.html"
        save_sample_html(url, output_file)
        print("\n" + "-" * 80 + "\n")