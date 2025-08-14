import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import json
import re
import os
import sys
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse

class UndetectedBPSMedanScraper:
    def __init__(self, output_file: str = "public/bps_undetected_index.json", headless: bool = False):
        self.base_url = "https://medankota.bps.go.id"
        self.output_file = output_file
        self.headless = headless
        self.driver = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('undetected_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create output directory
        os.makedirs(os.path.dirname(self.output_file) if os.path.dirname(self.output_file) else '.', exist_ok=True)
        
        self.all_links = set()
        self.scraped_data = []
        self.page_count = 0
        self.error_count = 0

    def setup_undetected_driver(self):
        """Setup undetected Chrome driver"""
        try:
            self.logger.info("Setting up undetected Chrome driver...")
            
            # Create Chrome options
            options = uc.ChromeOptions()
            
            if self.headless:
                options.add_argument("--headless=new")
            
            # Additional stealth options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")  # Speed up loading
            options.add_argument("--disable-javascript")  # Disable JS to avoid detection
            
            # Create undetected Chrome driver
            self.driver = uc.Chrome(
                options=options,
                version_main=None,  # Auto-detect Chrome version
                driver_executable_path=None,
                browser_executable_path=None,
                user_data_dir=None,
                headless=self.headless
            )
            
            # Set reasonable timeouts
            self.driver.implicitly_wait(15)
            self.driver.set_page_load_timeout(45)
            
            # Random user agent rotation
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            
            user_agent = random.choice(user_agents)
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
            
            self.logger.info("Undetected Chrome driver setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup undetected driver: {e}")
            return False

    def test_connection_advanced(self):
        """Advanced connection test with multiple strategies"""
        print("=== Undetected Chrome BPS Connection Test ===\n")
        
        if not self.setup_undetected_driver():
            print("❌ Failed to setup undetected Chrome driver")
            return False
        
        try:
            strategies = [
                ("Direct Homepage", self.base_url, 15),
                ("Subject Section", f"{self.base_url}/subject", 20),
                ("Publication Section", f"{self.base_url}/publication", 20),
                ("Statistics Table", f"{self.base_url}/staticTable", 25),
            ]
            
            successful_urls = []
            
            for strategy_name, test_url, wait_time in strategies:
                print(f"🔍 Testing {strategy_name}: {test_url}")
                try:
                    # Navigate with extended waiting
                    start_time = time.time()
                    self.driver.get(test_url)
                    
                    # Wait for page to load completely
                    print(f"  ⏳ Waiting {wait_time}s for page load...")
                    time.sleep(wait_time)
                    
                    load_time = time.time() - start_time
                    
                    # Get page information
                    page_title = self.driver.title
                    page_url = self.driver.current_url
                    page_source = self.driver.page_source
                    
                    print(f"  📄 Title: {page_title}")
                    print(f"  🔗 Final URL: {page_url}")
                    print(f"  ⏱️  Load time: {load_time:.2f}s")
                    print(f"  📊 Content length: {len(page_source)} characters")
                    
                    # Check for blocking indicators
                    page_lower = page_source.lower()
                    blocking_signs = [
                        'just a moment',
                        'checking your browser', 
                        'cloudflare',
                        'access denied',
                        'blocked',
                        'ray id:',
                        'error 403',
                        'please wait'
                    ]
                    
                    blocked = any(sign in page_lower for sign in blocking_signs)
                    
                    if blocked:
                        print(f"  ❌ BLOCKED - Anti-bot protection detected")
                        blocking_reason = next((sign for sign in blocking_signs if sign in page_lower), "unknown")
                        print(f"  🚫 Blocking reason: {blocking_reason}")
                    else:
                        print(f"  ✅ SUCCESS - Page loaded successfully!")
                        
                        # Check for BPS content
                        bps_indicators = [
                            'badan pusat statistik',
                            'bps kota medan',
                            'statistik',
                            'publikasi',
                            'data'
                        ]
                        
                        has_bps_content = any(indicator in page_lower for indicator in bps_indicators)
                        
                        if has_bps_content:
                            print(f"  📈 Contains BPS content")
                            successful_urls.append(test_url)
                            
                            # Try to find some links
                            try:
                                soup = BeautifulSoup(page_source, 'html.parser')
                                links = soup.find_all('a', href=True)
                                valid_links = [link for link in links if link.get('href') and 'medankota.bps.go.id' in link.get('href', '')]
                                print(f"  🔗 Found {len(links)} total links, {len(valid_links)} BPS links")
                                
                                if len(valid_links) > 0:
                                    print(f"  📝 Sample BPS links:")
                                    for i, link in enumerate(valid_links[:3]):
                                        href = link.get('href', '')
                                        text = link.get_text(strip=True)[:40]
                                        print(f"    {i+1}. {text} → {href}")
                                        
                            except Exception as link_error:
                                print(f"  ⚠️  Could not analyze links: {link_error}")
                        else:
                            print(f"  ⚠️  Page loaded but doesn't contain expected BPS content")
                    
                    print()
                    
                except TimeoutException:
                    print(f"  ❌ TIMEOUT - Page took too long to load")
                    print()
                except Exception as e:
                    print(f"  ❌ ERROR: {e}")
                    print()
                
                # Wait between tests to avoid triggering rate limits
                if strategy_name != strategies[-1][0]:  # Don't wait after last test
                    wait_between = random.randint(8, 15)
                    print(f"⏳ Waiting {wait_between}s before next test...\n")
                    time.sleep(wait_between)
            
            print("=== Test Summary ===")
            print(f"Successful URLs: {len(successful_urls)}")
            
            if successful_urls:
                print("✅ Working URLs:")
                for i, url in enumerate(successful_urls, 1):
                    print(f"  {i}. {url}")
                print(f"\n🎉 SUCCESS! The scraper should work!")
                print("🚀 You can now run: python undetected_scraper.py scrape")
            else:
                print("❌ No URLs accessible")
                print("\nPossible solutions:")
                print("  1. Try running from a different IP address")
                print("  2. Use a VPN")
                print("  3. Try at a different time")
                print("  4. The site may be temporarily blocking all automation")
            
            return len(successful_urls) > 0
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            print(f"❌ Connection test failed: {e}")
            return False
        finally:
            if self.driver:
                print("🔄 Closing browser...")
                self.driver.quit()

    def scrape_with_undetected_chrome(self, max_pages: int = 30, start_delay: int = 20):
        """Main scraping method using undetected Chrome"""
        self.logger.info("Starting undetected Chrome scraping...")
        start_time = datetime.now()
        
        if not self.setup_undetected_driver():
            return {"error": "Failed to setup undetected Chrome driver", "urls": []}
        
        try:
            # Initial long delay to let browser settle
            self.logger.info(f"Initial settling delay: {start_delay}s")
            time.sleep(start_delay)
            
            # Start with homepage
            self.logger.info("Loading homepage...")
            success = self._load_page_with_patience(self.base_url, patience=30)
            
            if not success:
                # Try alternative approach - go to a specific section first
                self.logger.info("Homepage failed, trying subject section...")
                success = self._load_page_with_patience(f"{self.base_url}/subject", patience=25)
            
            if not success:
                return {"error": "Could not access any page on the website", "urls": []}
            
            # Process the first successfully loaded page
            self._process_current_page_carefully(self.driver.current_url, depth=0)
            
            # Get links from the current page
            initial_links = self._extract_links_carefully()
            self.logger.info(f"Found {len(initial_links)} links on first page")
            
            # Visit additional pages
            pages_to_visit = initial_links[:max_pages-1]  # -1 because we already have homepage
            
            for i, url in enumerate(pages_to_visit):
                if len(self.scraped_data) >= max_pages:
                    break
                
                self.logger.info(f"Loading page {i+2}/{min(len(pages_to_visit)+1, max_pages)}: {url}")
                
                if self._load_page_with_patience(url, patience=15):
                    self._process_current_page_carefully(url, depth=1)
                    
                    # Add more links from successful pages (but limit growth)
                    if len(self.scraped_data) < max_pages // 2:
                        new_links = self._extract_links_carefully()
                        for new_link in new_links[:3]:  # Add max 3 new links per page
                            if new_link not in pages_to_visit and len(pages_to_visit) < max_pages:
                                pages_to_visit.append(new_link)
                
                # Progress update
                if (i + 1) % 5 == 0:
                    success_rate = len(self.scraped_data) / (i + 2) * 100
                    self.logger.info(f"Progress: {len(self.scraped_data)} pages scraped, {success_rate:.1f}% success rate")
                
                # Random delay between pages
                delay = random.randint(8, 15)
                self.logger.info(f"Waiting {delay}s before next page...")
                time.sleep(delay)
            
            # Prepare final data
            final_data = {
                "scraped_at": datetime.now().isoformat(),
                "total_urls": len(self.scraped_data),
                "base_url": self.base_url,
                "scraping_method": "undetected_chrome",
                "max_pages": max_pages,
                "error_count": self.error_count,
                "success_rate": f"{len(self.scraped_data)/(len(self.scraped_data)+self.error_count)*100:.1f}%" if (len(self.scraped_data)+self.error_count) > 0 else "0%",
                "urls": self.scraped_data
            }
            
            # Save results
            self._save_to_file(final_data)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(f"Undetected Chrome scraping completed!")
            self.logger.info(f"Scraped {len(self.scraped_data)} pages in {duration:.2f} seconds")
            self.logger.info(f"Success rate: {len(self.scraped_data)}/{len(self.scraped_data)+self.error_count}")
            
            return final_data
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e), "urls": self.scraped_data}
        
        finally:
            if self.driver:
                self.logger.info("Closing undetected Chrome driver")
                self.driver.quit()

    def _load_page_with_patience(self, url: str, patience: int = 20) -> bool:
        """Load page with extra patience for anti-bot systems"""
        try:
            self.logger.info(f"Loading with patience: {url}")
            
            # Navigate to page
            self.driver.get(url)
            
            # Wait patiently for the page to load
            self.logger.info(f"Waiting {patience}s for page to fully load...")
            time.sleep(patience)
            
            # Check page content
            page_source = self.driver.page_source
            page_title = self.driver.title
            
            # Check if we're still being blocked
            page_lower = page_source.lower()
            blocking_indicators = [
                'just a moment',
                'checking your browser',
                'please wait',
                'cloudflare'
            ]
            
            if any(indicator in page_lower for indicator in blocking_indicators):
                self.logger.warning(f"Still seeing blocking page, waiting longer...")
                time.sleep(15)  # Wait even more
                page_source = self.driver.page_source
                page_lower = page_source.lower()
                
                if any(indicator in page_lower for indicator in blocking_indicators):
                    self.logger.error(f"Page still blocked after extended wait: {url}")
                    self.error_count += 1
                    return False
            
            # Check for meaningful content
            if len(page_source) < 1000:
                self.logger.warning(f"Page content too short: {url}")
                self.error_count += 1
                return False
            
            # Check for BPS content
            bps_indicators = ['badan pusat statistik', 'bps', 'statistik']
            if not any(indicator in page_lower for indicator in bps_indicators):
                self.logger.warning(f"Page doesn't contain expected BPS content: {url}")
                # Don't count this as error, might still be useful
            
            self.logger.info(f"Successfully loaded page: {page_title}")
            return True
            
        except TimeoutException:
            self.logger.error(f"Timeout loading page: {url}")
            self.error_count += 1
            return False
        except Exception as e:
            self.logger.error(f"Error loading page {url}: {e}")
            self.error_count += 1
            return False

    def _process_current_page_carefully(self, url: str, depth: int = 0):
        """Carefully process the current page"""
        try:
            # Get page information
            page_title = self.driver.title
            page_url = self.driver.current_url
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract metadata carefully
            description = self._extract_description_safely(soup)
            keywords = self._extract_keywords_safely(soup)
            page_type = self._classify_page_type(page_url, page_title)
            
            # Store page data
            page_data = {
                "url": page_url,
                "original_url": url,
                "title": page_title,
                "description": description,
                "keywords": keywords,
                "type": page_type,
                "depth": depth,
                "scraped_at": datetime.now().isoformat(),
                "content_length": len(page_source),
                "redirected": url != page_url
            }
            
            self.scraped_data.append(page_data)
            self.page_count += 1
            
            self.logger.info(f"✅ Processed page {self.page_count}: {page_title[:60]}...")
            
        except Exception as e:
            self.logger.error(f"Error processing page {url}: {e}")
            self.error_count += 1

    def _extract_links_carefully(self) -> List[str]:
        """Carefully extract valid links from current page"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            links = []
            
            for link_element in soup.find_all('a', href=True):
                href = link_element.get('href')
                if href and self._is_valid_bps_url(href):
                    full_url = urljoin(self.base_url, href)
                    if full_url not in self.all_links:
                        links.append(full_url)
                        self.all_links.add(full_url)
            
            self.logger.debug(f"Extracted {len(links)} new valid links")
            return links[:15]  # Limit links per page
            
        except Exception as e:
            self.logger.error(f"Error extracting links: {e}")
            return []

    def _is_valid_bps_url(self, url: str) -> bool:
        """Check if URL is valid for scraping"""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Must contain BPS domain
        if 'medankota.bps.go.id' not in url_lower:
            return False
        
        # Skip unwanted file types and paths
        skip_patterns = [
            r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|jpg|jpeg|png|gif|css|js)(\?|$)',
            r'/(assets|static|media|images|css|js|fonts)/',
            r'/download/',
            r'mailto:',
            r'javascript:',
            r'#',
            r'\?print'
        ]
        
        return not any(re.search(pattern, url_lower) for pattern in skip_patterns)

    def _extract_description_safely(self, soup: BeautifulSoup) -> str:
        """Safely extract page description"""
        try:
            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                return meta_desc.get('content').strip()
            
            # First paragraph
            first_p = soup.find('p')
            if first_p:
                text = first_p.get_text(strip=True)
                return text[:200] + "..." if len(text) > 200 else text
            
            return "No description available"
        except:
            return "No description available"

    def _extract_keywords_safely(self, soup: BeautifulSoup) -> List[str]:
        """Safely extract keywords"""
        try:
            keywords = []
            
            # Meta keywords
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and meta_keywords.get('content'):
                keywords.extend([k.strip() for k in meta_keywords.get('content').split(',')][:5])
            
            # From headers
            for header in soup.find_all(['h1', 'h2', 'h3'])[:3]:
                text = header.get_text(strip=True).lower()
                words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
                keywords.extend(words[:2])
            
            return list(set(keywords))[:10]
        except:
            return []

    def _classify_page_type(self, url: str, title: str) -> str:
        """Classify page type"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        if '/subject/' in url_lower:
            return 'statistics_subject'
        elif '/publication' in url_lower:
            return 'publication'
        elif '/pressrelease' in url_lower or '/news' in url_lower:
            return 'news'
        elif '/statictable' in url_lower:
            return 'statistics_table'
        elif any(word in title_lower for word in ['tabel', 'data', 'statistik']):
            return 'statistics_data'
        elif any(word in title_lower for word in ['publikasi', 'laporan']):
            return 'publication'
        else:
            return 'general'

    def _save_to_file(self, data: Dict):
        """Save data to JSON file"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Data saved to {self.output_file}")
        except Exception as e:
            self.logger.error(f"Error saving to file: {e}")


def main():
    """Main function"""
    output_file = "public/bps_undetected_index.json"
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            print("🔧 Testing Undetected Chrome connection...")
            scraper = UndetectedBPSMedanScraper(output_file, headless=False)
            success = scraper.test_connection_advanced()
            
        elif command == "test-headless":
            print("🔧 Testing Undetected Chrome connection (headless)...")
            scraper = UndetectedBPSMedanScraper(output_file, headless=True)
            success = scraper.test_connection_advanced()
            
        elif command == "scrape":
            max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            print(f"🚀 Starting Undetected Chrome scraping (max {max_pages} pages)...")
            print("⚠️  This will take a while due to anti-bot protection...")
            
            scraper = UndetectedBPSMedanScraper(output_file, headless=True)
            result = scraper.scrape_with_undetected_chrome(max_pages=max_pages)
            
            print(f"\n{'='*60}")
            print(f"SCRAPING COMPLETED")
            print(f"{'='*60}")
            print(f"📊 Total pages scraped: {result.get('total_urls', 0)}")
            print(f"❌ Errors: {result.get('error_count', 0)}")
            print(f"📈 Success rate: {result.get('success_rate', 'N/A')}")
            print(f"💾 Output: {output_file}")
            
        else:
            print("Usage: python undetected_scraper.py [command]")
            print("Commands:")
            print("  test              - Test connection (visible browser)")
            print("  test-headless     - Test connection (headless)")
            print("  scrape [max_pages] - Scrape website (default: 20 pages)")
    else:
        print("🔧 Undetected Chrome BPS Scraper")
        print("=" * 40)
        
        scraper = UndetectedBPSMedanScraper(output_file, headless=False)
        
        if scraper.test_connection_advanced():
            print("\n✅ Connection test passed!")
            
            response = input("\nDo you want to start scraping? (y/n): ")
            if response.lower() in ['y', 'yes']:
                scraper_headless = UndetectedBPSMedanScraper(output_file, headless=True)
                result = scraper_headless.scrape_with_undetected_chrome(max_pages=15)
                print(f"\n✅ Scraping completed! Found {result.get('total_urls', 0)} pages")


if __name__ == "__main__":
    main()