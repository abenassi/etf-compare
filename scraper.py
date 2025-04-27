import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime

def scrape_lazyportfolio_30y_metrics(url):
    """
    Scrape financial metrics from a lazyportfolioetf.com URL.
    
    Args:
        url (str): URL of the page to scrape
        
    Returns:
        dict: Dictionary with scraped metrics
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    retorno_30y_nominal = None
    retorno_30y_real = None
    desvio_estandar = None
    nombre = None
    
    # Buscar el título de la página (nombre del asset)
    title_tag = soup.find('h1')
    if title_tag:
        nombre = title_tag.get_text(strip=True)
    else:
        nombre = "Name not found"
    
    text_blocks = soup.find_all('div', class_='et_pb_text_inner')
    
    for block in text_blocks:
        text = block.get_text()
        
        match = re.search(r'30Y Return\s*([\d\.]+)%', text)
        if match and retorno_30y_nominal is None:
            retorno_30y_nominal = float(match.group(1))
        
        match = re.search(r'30Y Inflation Adjusted Return\s*([\d\.]+)%', text)
        if match and retorno_30y_real is None:
            retorno_30y_real = float(match.group(1))
        
        match = re.search(r'Std Deviation\s*([\d\.]+)%', text)
        if match and desvio_estandar is None:
            desvio_estandar = float(match.group(1))
        
        if retorno_30y_nominal and retorno_30y_real and desvio_estandar:
            break

    if None in (retorno_30y_nominal, retorno_30y_real, desvio_estandar):
        raise ValueError(f"Could not find all metrics on the page: {url}")

    cociente_nominal = retorno_30y_nominal / desvio_estandar
    cociente_real = retorno_30y_real / desvio_estandar

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
        pd.DataFrame: DataFrame with scraped metrics
    """
    datos = []
    errors = []
    
    for url in urls:
        try:
            metricas = scrape_lazyportfolio_30y_metrics(url)
            datos.append(metricas)
        except Exception as e:
            errors.append({"url": url, "error": str(e)})
    
    df = pd.DataFrame(datos)
    return df, errors
