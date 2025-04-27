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
    # Try H1 first
    title_tag = soup.find('h1')
    if title_tag:
        nombre = title_tag.get_text(strip=True)
        logger.info(f"Found asset name from H1: {nombre}")
    else:
        # Look for title in meta or other elements
        title_tag = soup.find('title')
        if title_tag:
            nombre = title_tag.get_text(strip=True).split('|')[0].strip()
            logger.info(f"Found asset name from title tag: {nombre}")
        else:
            nombre = "Name not found"
            logger.warning(f"Could not find asset name for {url}")
    
    # First approach: Look for paragraph containing compound annual return
    logger.info("Searching for metrics in paragraph text...")
    paragraphs = soup.find_all('p')
    logger.info(f"Found {len(paragraphs)} paragraphs to search")
    
    for p in paragraphs:
        text = p.get_text()
        logger.debug(f"Checking paragraph: {text[:100]}...")
        
        # Look for the standard pattern with compound annual return and std deviation
        if 'compound annual return' in text.lower() and 'standard deviation' in text.lower():
            logger.info(f"Found paragraph with metrics: {text}")
            
            # Extract the nominal return
            nominal_match = re.search(r'(\d+\.\d+)%\s+compound annual return', text)
            if nominal_match:
                retorno_30y_nominal = float(nominal_match.group(1))
                logger.info(f"Found nominal return: {retorno_30y_nominal}%")
            
            # Extract the standard deviation
            std_dev_match = re.search(r'with a\s+(\d+\.\d+)%\s+standard deviation', text)
            if std_dev_match:
                desvio_estandar = float(std_dev_match.group(1))
                logger.info(f"Found standard deviation: {desvio_estandar}%")
            
            # For real return, check for inflation adjusted or try to calculate
            if 'inflation adjusted' in text.lower():
                real_match = re.search(r'(\d+\.\d+)%\s+inflation adjusted', text)
                if real_match:
                    retorno_30y_real = float(real_match.group(1))
                    logger.info(f"Found real return: {retorno_30y_real}%")
            
            # If all is good, break
            if retorno_30y_nominal and desvio_estandar:
                break
    
    # Second approach: Look for metrics in the stats elements or other containers
    if not retorno_30y_nominal or not desvio_estandar:
        logger.info("Trying alternate method to find metrics...")
        
        # Look for metrics in specific containers that might hold them
        metric_containers = []
        metric_containers.extend(soup.find_all('div', class_=lambda c: c and any(x in str(c).lower() for x in ['metric', 'stat', 'result', 'data'])))
        metric_containers.extend(soup.find_all('div', id=lambda i: i and any(x in str(i).lower() for x in ['metric', 'stat', 'result', 'data'])))
        
        logger.info(f"Found {len(metric_containers)} potential metric containers")
        
        for container in metric_containers:
            text = container.get_text()
            logger.debug(f"Checking container: {text[:100]}...")
            
            # Look for return values with % sign
            if '%' in text and any(term in text.lower() for term in ['return', 'cagr', 'annual']):
                logger.info(f"Found container with possible metrics: {text[:200]}...")
                
                # Try to find nominal return
                if not retorno_30y_nominal:
                    # Pattern for "return" followed by percentage
                    nom_match = re.search(r'(?:annual|return|cagr)[^\d]*(\d+\.\d+)%', text.lower())
                    if nom_match:
                        retorno_30y_nominal = float(nom_match.group(1))
                        logger.info(f"Found nominal return: {retorno_30y_nominal}%")
                
                # Try to find standard deviation
                if not desvio_estandar:
                    # Pattern for standard deviation or volatility
                    std_match = re.search(r'(?:standard deviation|std|volatility)[^\d]*(\d+\.\d+)%', text.lower())
                    if std_match:
                        desvio_estandar = float(std_match.group(1))
                        logger.info(f"Found standard deviation: {desvio_estandar}%")
    
    # If we haven't found real return yet, estimate it as nominal - 3% (typical inflation)
    if retorno_30y_nominal and not retorno_30y_real:
        retorno_30y_real = retorno_30y_nominal - 3.0
        logger.warning(f"Real return not found, estimating as nominal - 3%: {retorno_30y_real}%")
        logger.warning("This is an estimation - actual inflation-adjusted returns may vary")
    
    # Check if we have the minimum required metrics to proceed
    missing_metrics = []
    if retorno_30y_nominal is None:
        missing_metrics.append("30Y nominal return")
    if desvio_estandar is None:
        missing_metrics.append("standard deviation")
    
    if missing_metrics:
        error_msg = f"Missing critical metrics for {url}: {', '.join(missing_metrics)}"
        logger.error(error_msg)
        
        # Debug info
        logger.debug(f"Page title: {soup.title.string if soup.title else 'No title'}")
        logger.debug(f"URL structure: {url.split('/')}")
        
        # For ETF pages, try to get ticker symbol
        if '/etf/' in url:
            ticker = url.split('/')[-2].split('-')[-1].upper()
            logger.info(f"ETF ticker symbol: {ticker}")
            alternative_msg = f"Consider using an alternative data source for ticker {ticker}"
            logger.info(alternative_msg)
        
        raise ValueError(error_msg)

    # Calculate Sharpe ratios
    cociente_nominal = retorno_30y_nominal / desvio_estandar if desvio_estandar != 0 else 0
    cociente_real = retorno_30y_real / desvio_estandar if desvio_estandar != 0 else 0
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
        'scrape_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'is_real_return_estimated': retorno_30y_real == retorno_30y_nominal - 3.0
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
