"""
Amazon Shoes Scraper - SeleniumBase
Robust price extraction with multiple fallbacks
Output: CSV only
"""

import time
import re
import random
from datetime import datetime
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd

#CONFIGURATION
SEARCH_TERM = "shoes"
TARGET_PRODUCTS = 50
MAX_PAGES = 10
CSV_FILENAME = f"amazon_shoes_50.csv"

# Amazon base URL (change if using a different locale)
BASE_URL = "https://www.amazon.com"

#HELPERS
def random_delay(min_sec=1.5, max_sec=3.5):
    time.sleep(random.uniform(min_sec, max_sec))

def safe_text(element):
    return element.text.strip() if element else "N/A"

def move_mouse_randomly(driver):
    try:
        driver.execute_script("""
            var event = new MouseEvent('mousemove', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: Math.random() * window.innerWidth,
                clientY: Math.random() * window.innerHeight
            });
            document.dispatchEvent(event);
        """)
    except:
        pass

def clean_price(text):
    """Extract numeric price from text with various formats."""
    if not text or text == "N/A":
        return "N/A"
    
    # Common patterns: $123.45, PKR 1,234.56, ₹1,234.56, 1,234.56
    patterns = [
        r'([\d,]+\.\d{2})',           # 1,234.56
        r'([\d,]+)',                   # 1,234 (whole number)
        r'[\$\€\£\¥\₹PKR]+\s*([\d,]+\.\d{2})',  # $123.45, PKR 1,234.56
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return text  # return as-is if no pattern matches

#  URL COLLECTION
def get_product_urls_from_search(driver, search_term, target_count):
    # Go to Amazon homepage first
    driver.get(BASE_URL)
    random_delay(2, 4)
    move_mouse_randomly(driver)

    # Accept cookies if present
    try:
        driver.find_element(By.CSS_SELECTOR, "input#sp-cc-accept").click()
        random_delay(1, 2)
    except:
        pass

    # Search
    search_url = f"{BASE_URL}/s?k={search_term.replace(' ', '+')}"
    driver.get(search_url)
    random_delay(3, 5)

    # Handle CAPTCHA/block
    if "Sorry" in driver.title or "something went wrong" in driver.page_source.lower():
        print("⚠️ Blocked! Solve CAPTCHA manually, then press ENTER...")
        input("▶️ Press ENTER after solving CAPTCHA...")

    product_urls = set()
    page = 1

    while len(product_urls) < target_count and page <= MAX_PAGES:
        # Scroll to load more
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        random_delay(2, 4)
        move_mouse_randomly(driver)

        # Find product links
        selectors = [
            'a[href*="/dp/"]',
            'a[href*="/gp/product/"]',
            'div[data-asin] a.a-link-normal'
        ]
        for sel in selectors:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                href = el.get_attribute("href")
                if href and ("/dp/" in href or "/gp/product/" in href):
                    clean = href.split("?")[0].split("#")[0]
                    product_urls.add(clean)

        print(f"  📦 Found {len(product_urls)} unique product URLs so far...")

        if len(product_urls) >= target_count:
            break

        # Click next page
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "a.s-pagination-next")
            if "disabled" in next_btn.get_attribute("class"):
                break
            driver.execute_script("arguments[0].click();", next_btn)
            random_delay(3, 5)
            page += 1
        except:
            break

    return list(product_urls)[:target_count]

#PRICE EXTRACTION (ROBUST)
def extract_selling_price(driver):
    """Extract selling price using multiple strategies."""
    
    # Strategy 1: Wait for price to load and try common selectors
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.a-price-whole, span.a-offscreen, div.a-column.a-span12"))
        )
    except:
        pass
    
    # Try multiple selector patterns
    selectors = [
        # Standard Amazon price
        "span.a-price-whole",  # Whole part of price
        "span.a-price .a-offscreen",  # Full price text
        "span.a-offscreen",  # Fallback
        # Your specified selector
        "div.a-column.a-span12",
        # Other common patterns
        "span.a-price",
        "div.a-price",
        "span.price",
        ".a-price .a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        ".a-price-whole"
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                text = el.text.strip()
                if text and re.search(r'[\d,]+', text):
                    # Check if it's a list price (contains "List" or "Was")
                    if "List" not in text and "Was" not in text and "MRP" not in text:
                        # Try to get fraction part if it's a whole+frac split
                        if selector == "span.a-price-whole":
                            try:
                                frac = driver.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text.strip()
                                if frac:
                                    return f"{text}.{frac}"
                            except:
                                pass
                        return clean_price(text)
        except:
            continue
    
    # Strategy 2: Regex on page source
    page_source = driver.page_source
    
    # Look for price patterns in the page source
    price_patterns = [
        r'PKR\s*([\d,]+\.\d{2})',
        r'PKR\s*([\d,]+)',
        r'\$\s*([\d,]+\.\d{2})',
        r'\$\s*([\d,]+)',
        r'₹\s*([\d,]+\.\d{2})',
        r'₹\s*([\d,]+)',
        r'([\d,]+\.\d{2})',
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, page_source)
        for match in matches:
            # Skip if it's a list price
            context_start = max(0, page_source.find(match) - 50)
            context_end = min(len(page_source), page_source.find(match) + 50)
            context = page_source[context_start:context_end]
            if "List" not in context and "Was" not in context and "MRP" not in context:
                return match
    
    return "N/A"

def extract_original_price(driver):
    """Extract original (list) price using multiple strategies."""
    
    # Try multiple selector patterns
    selectors = [
        # Standard Amazon list price
        "span.a-price.a-text-price .a-offscreen",
        "span.a-price.a-text-price",
        'a[aria-describedly="price-link"]',
        # Your specified selector
        'a[aria-describedly="price-link"] span',
        # Other common patterns
        ".a-price .a-offscreen",
        "span.a-offscreen",
        "#priceblock_listprice",
        ".a-text-price .a-offscreen"
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                text = el.text.strip()
                if text and re.search(r'[\d,]+', text):
                    # Check if it contains list price indicators
                    if "List" in text or "Was" in text or "MRP" in text or "list" in text.lower():
                        return clean_price(text)
                    # If it's a different price from selling price, treat as list price
                    return clean_price(text)
        except:
            continue
    
    # Strategy 2: Look for "List:" or "Was:" in page source
    page_source = driver.page_source
    
    # Look for "List:" or "Was:" or "MRP:" followed by price
    list_patterns = [
        r'List[:]?\s*[^0-9]*([\d,]+\.\d{2})',
        r'List[:]?\s*[^0-9]*([\d,]+)',
        r'Was[:]?\s*[^0-9]*([\d,]+\.\d{2})',
        r'Was[:]?\s*[^0-9]*([\d,]+)',
        r'MRP[:]?\s*[^0-9]*([\d,]+\.\d{2})',
        r'MRP[:]?\s*[^0-9]*([\d,]+)',
    ]
    
    for pattern in list_patterns:
        match = re.search(pattern, page_source, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # Strategy 3: Find any price that's higher than selling price
    # (This is a heuristic - not always accurate)
    try:
        selling = extract_selling_price(driver)
        if selling != "N/A":
            # Look for any price in the page source
            all_prices = re.findall(r'([\d,]+\.\d{2})', page_source)
            for price in all_prices:
                if price != selling:
                    # Check if this price appears near "List" or "Was"
                    context_start = max(0, page_source.find(price) - 50)
                    context = page_source[context_start:context_start + 100]
                    if "List" in context or "Was" in context or "MRP" in context:
                        return price
    except:
        pass
    
    return "N/A"

#  PRODUCT PARSING 
def parse_product_page(driver, url):
    driver.get(url)
    random_delay(2, 4)
    move_mouse_randomly(driver)

    if "Sorry" in driver.title or "something went wrong" in driver.page_source.lower():
        print("  ⚠️ Blocked – skipping.")
        return None

    #  Product Name: span#productTitle 
    try:
        name_el = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span#productTitle"))
        )
        name = safe_text(name_el)
    except:
        name = "N/A"

    #Prices using robust extraction
    selling_price = extract_selling_price(driver)
    original_price = extract_original_price(driver)
    
    # If original price is same as selling, try to find a different price
    if original_price == selling_price and selling_price != "N/A":
        # Look for a different price
        page_source = driver.page_source
        all_prices = re.findall(r'([\d,]+\.\d{2})', page_source)
        for price in all_prices:
            if price != selling_price:
                original_price = price
                break

    # Rating: span.a-size-small.a-color-base
    rating = "N/A"
    try:
        rating_el = driver.find_element(By.CSS_SELECTOR, "span.a-size-small.a-color-base")
        rating = safe_text(rating_el)
    except:
        pass

    #  Reviews: span#acrCustomerReviewText 
    reviews = "N/A"
    try:
        reviews_el = driver.find_element(By.CSS_SELECTOR, "span#acrCustomerReviewText")
        reviews = safe_text(reviews_el)
    except:
        pass

    #  Purchasing History: span#social-proofing-faceout-title-tk_bought 
    purchase_history = "N/A"
    try:
        purch_el = driver.find_element(By.CSS_SELECTOR, "span#social-proofing-faceout-title-tk_bought")
        purchase_history = safe_text(purch_el)
    except:
        pass

    #  Add to Cart: button[aria-label="Add to cart"] 
    add_to_cart = "No"
    try:
        atc_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Add to cart"]')
        if atc_btn.is_displayed():
            add_to_cart = "Yes"
    except:
        pass

    # Debug logging for missing prices
    if selling_price == "N/A" or original_price == "N/A":
        print(f"  ⚠️ Price missing - Selling: '{selling_price}', Original: '{original_price}'")
        print(f"     URL: {url[:60]}...")

    return {
        "product_url": url,
        "product_name": name,
        "selling_price": selling_price,
        "original_price": original_price,
        "rating": rating,
        "reviews": reviews,
        "purchase_history": purchase_history,
        "add_to_cart": add_to_cart,
        "scraped_at": datetime.now().isoformat()
    }

#SAVE CSV 
def save_to_csv(products, filename):
    df = pd.DataFrame(products)
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"✅ CSV saved: {filename} ({len(products)} products)")

#MAIN 
def main():
    print("👟 Amazon Shoes Scraper (Robust Price Extraction)")
    print("=" * 50)

    driver = Driver(uc=True, headless=False)
    driver.maximize_window()

    try:
        print(f"🔍 Searching for '{SEARCH_TERM}'...")
        product_urls = get_product_urls_from_search(driver, SEARCH_TERM, TARGET_PRODUCTS)
        print(f"✅ Found {len(product_urls)} product URLs")

        products = []
        for i, url in enumerate(product_urls, 1):
            print(f"  [{i}/{len(product_urls)}] Scraping: {url[:60]}...")
            data = parse_product_page(driver, url)
            if data:
                products.append(data)
            random_delay(1.5, 3)

        if products:
            save_to_csv(products, CSV_FILENAME)
            print(f"\n🎉 Done! Scraped {len(products)} products.")
        else:
            print("⚠️ No products scraped.")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        input("Press ENTER to close browser...")
        driver.quit()

if __name__ == "__main__":
    main()