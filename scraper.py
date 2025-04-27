import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scraper')

def scrape_lazyportfolio_30y_metrics(url):
    """
    Scrape financial metrics from a lazyportfolioetf.com URL.
    
    Args:
        url (str): URL of the page to scrape
        
    Returns:
        dict: Dictionary with scraped metrics
    """
    logger.info(f"Scraping URL: {url}")
    
    # Get the webpage content
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        logger.info(f"Sending request to: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info(f"Received response: Status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching URL {url}: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialize variables
    retorno_30y_nominal = None
    retorno_30y_real = None
    desvio_estandar = None
    nombre = None
    
    # Find the title of the page (asset name)
    title_tag = soup.find('h1')
    if title_tag:
        nombre = title_tag.get_text(strip=True)
        logger.info(f"Found asset name: {nombre}")
    else:
        nombre = "Name not found"
        logger.warning(f"Could not find asset name for {url}")
    
    # Find the text blocks that might contain the metrics
    text_blocks = soup.find_all('div', class_='et_pb_text_inner')
    logger.info(f"Found {len(text_blocks)} text blocks to search for metrics")
    
    # Search for metrics in each block
    for i, block in enumerate(text_blocks):
        text = block.get_text()
        
        # Search for nominal return
        match = re.search(r'30Y Return\s*([\d\.]+)%', text)
        if match and retorno_30y_nominal is None:
            retorno_30y_nominal = float(match.group(1))
            logger.info(f"Found 30Y nominal return: {retorno_30y_nominal}%")
        
        # Search for real (inflation-adjusted) return
        match = re.search(r'30Y Inflation Adjusted Return\s*([\d\.]+)%', text)
        if match and retorno_30y_real is None:
            retorno_30y_real = float(match.group(1))
            logger.info(f"Found 30Y real return: {retorno_30y_real}%")
        
        # Search for standard deviation
        match = re.search(r'Std Deviation\s*([\d\.]+)%', text)
        if match and desvio_estandar is None:
            desvio_estandar = float(match.group(1))
            logger.info(f"Found standard deviation: {desvio_estandar}%")
        
        # If we found all metrics, we can stop searching
        if retorno_30y_nominal and retorno_30y_real and desvio_estandar:
            logger.info("Found all required metrics")
            break

    # Check if all metrics were found
    missing_metrics = []
    if retorno_30y_nominal is None:
        missing_metrics.append("30Y nominal return")
    if retorno_30y_real is None:
        missing_metrics.append("30Y real return")
    if desvio_estandar is None:
        missing_metrics.append("standard deviation")
    
    if missing_metrics:
        error_msg = f"Missing metrics for {url}: {', '.join(missing_metrics)}"
        logger.error(error_msg)
        
        # Debug info - show a sample of the page content
        logger.debug(f"Page title: {soup.title.string if soup.title else 'No title'}")
        logger.debug(f"Sample HTML structure: {soup.prettify()[:500]}...")
        
        raise ValueError(error_msg)

    # Calculate Sharpe ratios
    cociente_nominal = retorno_30y_nominal / desvio_estandar
    cociente_real = retorno_30y_real / desvio_estandar
    logger.info(f"Calculated Sharpe ratios - Nominal: {cociente_nominal:.2f}, Real: {cociente_real:.2f}")

    # Return the metrics as a dictionary
    return {
        'name': nombre,
        'url': url,
        'nominal_30y_return': retorno_30y_nominal,
        'real_30y_return': retorno_30y_real,
        'std_deviation': desvio_estandar,
        'nominal_sharpe': cociente_nominal,
        'real_sharpe': cociente_real,
        'scrape_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def scrape_multiple_lazyportfolio_30y_metrics(urls):
    """
    Scrape financial metrics from multiple lazyportfolioetf.com URLs.
    
    Args:
        urls (list): List of URLs to scrape
        
    Returns:
        tuple: (DataFrame with scraped metrics, List of errors)
    """
    logger.info(f"Starting to scrape {len(urls)} URLs")
    datos = []
    errors = []
    
    for i, url in enumerate(urls):
        logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")
        try:
            metricas = scrape_lazyportfolio_30y_metrics(url)
            datos.append(metricas)
            logger.info(f"Successfully scraped data for: {metricas['name']}")
        except Exception as e:
            error_detail = {"url": url, "error": str(e)}
            errors.append(error_detail)
            logger.error(f"Error scraping {url}: {str(e)}")
    
    logger.info(f"Scraping complete. Processed {len(urls)} URLs with {len(errors)} errors")
    
    if not datos:
        logger.warning("No data was successfully scraped from any URL")
        return pd.DataFrame(), errors
    
    df = pd.DataFrame(datos)
    logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
    return df, errors
