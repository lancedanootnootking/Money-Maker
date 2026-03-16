#!/usr/bin/env python3
"""
Google Maps Scraper - Finds businesses without websites

This script scrapes Google Maps for businesses that don't have websites
and exports their names and phone numbers to a text file.

Required packages:
- selenium
- webdriver-manager

Installation:
pip install selenium webdriver-manager
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class GoogleMapsScraper:
    def __init__(self):
        """Initialize the scraper with Chrome browser"""
        self.driver = None
        self.wait = None
        self.businesses_without_website = []
        
    def setup_browser(self):
        """Set up Chrome browser with Selenium"""
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Try to use webdriver-manager first
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("Chrome driver installed successfully")
        except Exception as e:
            print(f"Error with webdriver-manager: {e}")
            print("Trying to find Chrome driver in system PATH...")
            try:
                self.driver = webdriver.Chrome(options=options)
                print("Using system Chrome driver")
            except Exception as e2:
                print(f"Failed to start Chrome: {e2}")
                print("Please install Chrome or ensure chromedriver is in PATH")
                raise
                
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)  # Increased wait time
        
    def get_user_input(self):
        """Get business type and city from user"""
        print("Google Maps Business Scraper")
        print("=" * 40)
        
        business_type = input("Enter business type (e.g., plumber, dentist, restaurant): ").strip()
        city = input("Enter city (e.g., Nashville, Austin, Miami): ").strip()
        
        if not business_type or not city:
            print("Both business type and city are required!")
            return None, None
            
        return business_type, city
        
    def search_google_maps(self, business_type, city):
        """Search for businesses on Google Maps"""
        search_query = f"{business_type}s in {city}"
        
        # Go to Google Maps
        self.driver.get("https://www.google.com/maps")
        time.sleep(3)
        
        # Find search box and enter query - try multiple selectors
        search_selectors = [
            "input[name='q']",
            "#searchboxinput", 
            "input[placeholder*='Search']",
            "input[aria-label*='Search']",
            "input[type='text']"
        ]
        
        search_box = None
        for selector in search_selectors:
            try:
                search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                if search_box.is_displayed():
                    break
            except:
                continue
                
        if not search_box:
            print("Could not find search box on Google Maps")
            return False
            
        try:
            search_box.clear()
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(4)
            return True
        except Exception as e:
            print(f"Error entering search query: {e}")
            return False
            
    def scroll_to_load_results(self, scroll_count=5):
        """Scroll through results to load more businesses"""
        print("Loading more business results...")
        
        # Find the results panel
        try:
            results_panel = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='feed']"))
            )
            
            for i in range(scroll_count):
                # Scroll down
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", results_panel)
                time.sleep(2)
                print(f"Scroll {i+1}/{scroll_count} completed")
                
        except TimeoutException:
            print("Could not find results panel for scrolling")
            
    def extract_business_data(self):
        """Extract business information from search results"""
        print("Extracting business data...")
        
        # Find all business listings
        business_links = []
        try:
            # Get all business result elements
            business_elements = self.driver.find_elements(
                By.XPATH, 
                "//div[@role='feed']//a[contains(@href, '/maps/place/')]"
            )
            
            for element in business_elements:
                href = element.get_attribute('href')
                if href and href not in business_links:
                    business_links.append(href)
                    
        except Exception as e:
            print(f"Error finding business links: {e}")
            
        print(f"Found {len(business_links)} businesses to check")
        
        # Visit each business and check for website
        for i, link in enumerate(business_links):
            try:
                print(f"Checking business {i+1}/{len(business_links)}")
                self.check_business_for_website(link)
                time.sleep(1)  # Small delay between requests
            except Exception as e:
                print(f"Error checking business {i+1}: {e}")
                continue
                
    def check_business_for_website(self, business_url):
        """Visit a business page and check if it has a website"""
        try:
            self.driver.get(business_url)
            time.sleep(3)
            
            # Get business name - try multiple selectors
            business_name = "Unknown Business"
            name_selectors = [
                "h1[data-attrid*='title']",
                "h1",
                "[data-attrid='title']",
                ".x3AX1-LfntMc-header-title-title",
                ".l5Lhkf",
                "[data-attrid='title'] span"
            ]
            
            for selector in name_selectors:
                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if name_element.text.strip():
                        business_name = name_element.text.strip()
                        break
                except:
                    continue
                
            print(f"Checking: {business_name}")
                
            # Check for website - try multiple selectors and text patterns
            has_website = False
            website_selectors = [
                "a[data-attrid*='website']",
                "a[href*='http'][data-attrid]",
                "a[data-attrid='//google.com/place']",
                ".Io6YTe",
                "a[data-item-id*='website']",
                "a[href*='website']"
            ]
            
            # Also check for common website text patterns
            website_text_patterns = ['website', 'web site', 'site', 'www.', '.com']
            
            for selector in website_selectors:
                try:
                    website_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in website_elements:
                        element_text = element.text.lower()
                        element_href = element.get_attribute('href') or ''
                        
                        # Check if this is actually a website link
                        if (any(pattern in element_text for pattern in website_text_patterns) or
                            'http' in element_href and 'google.com' not in element_href):
                            has_website = True
                            print(f"  Found website: {element_text}")
                            break
                    if has_website:
                        break
                except:
                    continue
                
            # If no website, get phone number
            if not has_website:
                print(f"  No website found, checking phone...")
                phone_number = self.extract_phone_number()
                
                if phone_number:
                    business_info = f"{business_name} - {phone_number}"
                    self.businesses_without_website.append(business_info)
                    print(f"✓ Found business without website: {business_name} - {phone_number}")
                else:
                    print(f"✗ Skipping {business_name} (no phone number)")
            else:
                print(f"✗ Skipping {business_name} (has website)")
                    
        except Exception as e:
            print(f"Error visiting business page: {e}")
            
    def extract_phone_number(self):
        """Extract phone number from business page"""
        try:
            # Look for phone number in various possible locations
            phone_selectors = [
                "span[data-attrid*='phone']",
                "[data-attrid='phone'] span",
                ".LrzXr",
                ".LrzXr.zdqRlf.kno-fv-",
                "a[href*='tel:']",
                "[data-dtype='d3ph']",
                "span[data-tooltip*='Phone']",
                "[data-attrid='phone']"
            ]
            
            for selector in phone_selectors:
                try:
                    phone_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in phone_elements:
                        phone_text = element.text.strip()
                        # Validate phone number format
                        if phone_text and re.match(r'[\(\)\d\-\s\+]{10,}', phone_text):
                            print(f"    Found phone: {phone_text}")
                            return phone_text
                except Exception:
                    continue
                    
            # Also try to find phone numbers in page text
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            phone_matches = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', page_text)
            if phone_matches:
                print(f"    Found phone in text: {phone_matches[0]}")
                return phone_matches[0]
                    
        except Exception as e:
            print(f"    Error extracting phone: {e}")
            
        return None
        
    def save_results(self, business_type, city):
        """Save results to a text file"""
        if not self.businesses_without_website:
            print("No businesses without websites found!")
            return
            
        filename = f"{business_type}_without_website_{city.replace(' ', '_')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Businesses without websites - {business_type}s in {city}\n")
                f.write("=" * 50 + "\n\n")
                
                for business in self.businesses_without_website:
                    f.write(business + "\n")
                    
            print(f"\nResults saved to: {filename}")
            print(f"Total businesses found: {len(self.businesses_without_website)}")
            
        except Exception as e:
            print(f"Error saving results: {e}")
            
    def run(self):
        """Main method to run the scraper"""
        try:
            # Get user input
            business_type, city = self.get_user_input()
            if not business_type or not city:
                return
                
            # Set up browser
            print("Setting up browser...")
            self.setup_browser()
            
            # Search Google Maps
            print(f"Searching for {business_type}s in {city}...")
            if not self.search_google_maps(business_type, city):
                return
                
            # Scroll to load more results
            self.scroll_to_load_results()
            
            # Extract business data
            self.extract_business_data()
            
            # Save results
            self.save_results(business_type, city)
            
        except KeyboardInterrupt:
            print("\nScraper stopped by user")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Clean up
            if self.driver:
                self.driver.quit()
                print("Browser closed")


def main():
    """Main function to run the scraper"""
    scraper = GoogleMapsScraper()
    scraper.run()


if __name__ == "__main__":
    main()
