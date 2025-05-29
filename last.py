from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def setup_driver():
    """Setup Chrome driver with options to bypass login"""
    options = Options()
    
    # Add arguments to make it look like a real browser
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    
    driver = webdriver.Chrome(options=options)
    
    # Execute script to hide webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def get_tweets_using_exact_structure(username="elonmusk"):
    """Get tweets using the exact CSS structure you provided"""
    driver = setup_driver()
    
    try:
        # Go directly to user profile
        url = f"https://twitter.com/{username}"
        print(f"Opening {url}")
        driver.get(url)
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(15)
        
        # Check current URL
        print(f"Current URL: {driver.current_url}")
        
        tweets = []
        
        # Method 1: Use the exact CSS structure you provided
        print("Searching using exact CSS structure...")
        
        # Find the outer divs with class "css-175oi2r r-1iusvr4 r-16y2uox r-1777fci r-kzbkwu"
        outer_divs = driver.find_elements(By.CSS_SELECTOR, 'div.css-175oi2r.r-1iusvr4.r-16y2uox.r-1777fci.r-kzbkwu')
        print(f"Found {len(outer_divs)} outer divs")
        
        for i, outer_div in enumerate(outer_divs[:5]):  # Check first 5 to get 3 tweets
            try:
                # Look for the inner div with class "css-175oi2r"
                inner_divs = outer_div.find_elements(By.CSS_SELECTOR, 'div.css-175oi2r')
                print(f"Outer div {i+1}: Found {len(inner_divs)} inner divs")
                
                for inner_div in inner_divs:
                    # Look for div with id starting with "id__"
                    id_divs = inner_div.find_elements(By.CSS_SELECTOR, 'div[id*="id__"]')
                    
                    if id_divs:
                        print(f"Found {len(id_divs)} divs with id starting with 'id__'")
                        
                        for id_div in id_divs:
                            # Finally, look for the span with the text classes
                            text_spans = id_div.find_elements(By.CSS_SELECTOR, 'span.css-1jxf684.r-bcqeeo.r-1ttztb7.r-qvutc0.r-poiln3')
                            
                            if text_spans:
                                print(f"Found {len(text_spans)} text spans")
                                
                                for span in text_spans:
                                    text = span.text.strip()
                                    if text and len(text) > 5:
                                        tweets.append(text)
                                        print(f"✓ Tweet {len(tweets)}: {text}")
                                        
                                        if len(tweets) >= 3:
                                            return tweets
                
            except Exception as e:
                print(f"Error processing outer div {i}: {e}")
        
        # Method 2: Try more flexible approach if exact structure doesn't work
        if not tweets:
            print("\nExact structure not found, trying flexible approach...")
            
            # Look for any spans with the text classes
            all_text_spans = driver.find_elements(By.CSS_SELECTOR, 'span.css-1jxf684.r-bcqeeo.r-1ttztb7.r-qvutc0.r-poiln3')
            print(f"Found {len(all_text_spans)} text spans anywhere on page")
            
            for span in all_text_spans[:10]:  # Check first 10 spans
                try:
                    text = span.text.strip()
                    if text and len(text) > 10:  # Filter out short text
                        tweets.append(text)
                        print(f"✓ Tweet {len(tweets)}: {text}")
                        
                        if len(tweets) >= 3:
                            break
                except:
                    pass
        
        # Method 3: Try alternative span classes
        if not tweets:
            print("\nTrying alternative span selectors...")
            
            # Try just the main classes
            alt_spans = driver.find_elements(By.CSS_SELECTOR, 'span.css-1jxf684')
            print(f"Found {len(alt_spans)} spans with css-1jxf684")
            
            for span in alt_spans[:15]:
                try:
                    text = span.text.strip()
                    if text and len(text) > 10 and not text.startswith('@'):
                        tweets.append(text)
                        print(f"✓ Tweet {len(tweets)}: {text}")
                        
                        if len(tweets) >= 3:
                            break
                except:
                    pass
        
        # Method 4: Debug - show what's actually on the page
        if not tweets:
            print("\nNo tweets found. Debugging page content...")
            
            # Check if we can find any of the expected classes
            check_classes = [
                'css-175oi2r',
                'r-1iusvr4',
                'css-1jxf684',
                'r-bcqeeo'
            ]
            
            for class_name in check_classes:
                elements = driver.find_elements(By.CSS_SELECTOR, f'.{class_name}')
                print(f"Found {len(elements)} elements with class '{class_name}'")
            
            # Check for any divs with id containing "id__"
            id_elements = driver.find_elements(By.CSS_SELECTOR, 'div[id*="id__"]')
            print(f"Found {len(id_elements)} divs with id containing 'id__'")
            
            # Show a sample of page content
            body = driver.find_element(By.TAG_NAME, "body")
            body_text = body.text[:500]
            print(f"\nPage content sample:\n{body_text}...")
        
        return tweets
        
    except Exception as e:
        print(f"Error: {e}")
        return []
        
    finally:
        print("Keeping browser open for 5 seconds...")
        time.sleep(5)
        driver.quit()

def main():
    username = input("Enter Twitter username (default: elonmusk): ").strip() or "elonmusk"
    
    print(f"\nGetting first 3 tweets from @{username} using exact CSS structure")
    print("="*60)
    
    tweets = get_tweets_using_exact_structure(username)
    
    # Display results
    print(f"\n{'='*50}")
    print("RESULTS:")
    print(f"{'='*50}")
    
    if tweets:
        for i, tweet in enumerate(tweets, 1):
            print(f"\nTweet {i}:")
            print(f"'{tweet}'")
    else:
        print("❌ No tweets found!")
        print("\nThe page structure might be different than expected.")
        print("Try running the script and check what it finds in the debugging output.")

if __name__ == "__main__":
    main()