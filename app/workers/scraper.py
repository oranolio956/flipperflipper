import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from urllib.parse import urlparse

from celery import Task
from app.core.celery_app import celery_app
from app.core.database import db_manager

logger = logging.getLogger(__name__)


class ScraperTask(Task):
    """Base task class for Scraper worker"""
    autoretry_for = (aiohttp.ClientError, asyncio.TimeoutError)
    retry_kwargs = {'max_retries': 5}
    retry_backoff = True
    retry_backoff_max = 1200
    retry_jitter = True
    rate_limit = '100/m'  # 100 requests per minute


@celery_app.task(base=ScraperTask, bind=True, queue='scraper')
def scrape_url(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Scrape a single URL"""
    try:
        logger.info(f"Scraping URL: {url}")
        
        async def _scrape():
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    content = await response.text()
                    return {
                        'url': url,
                        'status_code': response.status,
                        'content_length': len(content),
                        'headers': dict(response.headers),
                        'content': content[:1000],  # First 1000 chars
                        'scraped_at': datetime.utcnow().isoformat()
                    }
        
        # Run async scraper
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_scrape())
            logger.info(f"Successfully scraped: {url}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        raise self.retry(exc=e)


@celery_app.task(base=ScraperTask, bind=True, queue='scraper')
def batch_scrape(self, urls: List[str], options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Scrape multiple URLs concurrently"""
    try:
        logger.info(f"Batch scraping {len(urls)} URLs")
        
        async def _batch_scrape():
            results = []
            errors = []
            
            # Limit concurrent requests
            semaphore = asyncio.Semaphore(10)
            
            async def scrape_with_limit(session, url):
                async with semaphore:
                    try:
                        async with session.get(url) as response:
                            content = await response.text()
                            return {
                                'url': url,
                                'status_code': response.status,
                                'success': True,
                                'content_length': len(content)
                            }
                    except Exception as e:
                        return {
                            'url': url,
                            'success': False,
                            'error': str(e)
                        }
            
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                tasks = [scrape_with_limit(session, url) for url in urls]
                results = await asyncio.gather(*tasks)
            
            successful = [r for r in results if r.get('success')]
            failed = [r for r in results if not r.get('success')]
            
            return {
                'total_urls': len(urls),
                'successful': len(successful),
                'failed': len(failed),
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Run async batch scraper
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_batch_scrape())
            logger.info(f"Batch scrape completed: {result['successful']} successful, {result['failed']} failed")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in batch scraping: {e}")
        raise self.retry(exc=e)


@celery_app.task(base=ScraperTask, bind=True, queue='scraper')
def scrape_api(self, endpoint: str, params: Dict[str, Any] = None, 
               headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Scrape API endpoint"""
    try:
        logger.info(f"Scraping API endpoint: {endpoint}")
        
        async def _scrape_api():
            timeout = aiohttp.ClientTimeout(total=60)
            
            # Default headers for API requests
            api_headers = {
                'Accept': 'application/json',
                'User-Agent': 'ProxyScanner/1.0'
            }
            if headers:
                api_headers.update(headers)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(endpoint, params=params, headers=api_headers) as response:
                    # Handle different content types
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'application/json' in content_type:
                        data = await response.json()
                    else:
                        data = await response.text()
                    
                    return {
                        'endpoint': endpoint,
                        'status_code': response.status,
                        'content_type': content_type,
                        'data': data,
                        'scraped_at': datetime.utcnow().isoformat()
                    }
        
        # Run async API scraper
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_scrape_api())
            logger.info(f"Successfully scraped API: {endpoint}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error scraping API {endpoint}: {e}")
        raise self.retry(exc=e)


@celery_app.task(base=ScraperTask, bind=True, queue='scraper')
def extract_proxies(self, source_url: str, pattern: str = None) -> Dict[str, Any]:
    """Extract proxy addresses from a source"""
    try:
        logger.info(f"Extracting proxies from: {source_url}")
        
        # First scrape the URL
        scrape_result = scrape_url.apply(args=[source_url]).get()
        
        if scrape_result['status_code'] != 200:
            raise Exception(f"Failed to fetch source: {scrape_result['status_code']}")
        
        content = scrape_result.get('content', '')
        
        # Extract proxies based on pattern
        import re
        
        # Default proxy pattern (IP:PORT)
        if not pattern:
            pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}\b'
        
        proxies = re.findall(pattern, content)
        
        # Validate extracted proxies
        valid_proxies = []
        for proxy in proxies:
            parts = proxy.split(':')
            if len(parts) == 2:
                ip, port = parts
                try:
                    # Validate IP
                    octets = ip.split('.')
                    if len(octets) == 4 and all(0 <= int(o) <= 255 for o in octets):
                        # Validate port
                        if 1 <= int(port) <= 65535:
                            valid_proxies.append(proxy)
                except ValueError:
                    continue
        
        return {
            'source_url': source_url,
            'total_found': len(proxies),
            'valid_proxies': len(valid_proxies),
            'proxies': valid_proxies[:100],  # Limit to first 100
            'extracted_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error extracting proxies from {source_url}: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True, queue='scraper')
def health_check(self) -> Dict[str, str]:
    """Health check task for scraper worker"""
    return {
        'worker': 'scraper',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }