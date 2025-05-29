from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re

def scroll_and_load(driver, max_scrolls=5):
    """Scroll down the page to load more content"""
    print("Starting scroll sequence...")
    
    for i in range(max_scrolls):
        # Get current page height
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"Scroll {i+1}/{max_scrolls} - Scrolled to bottom")
        
        # Wait for new content to load
        time.sleep(3)
        
        # Check if page height changed (new content loaded)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            print("No new content loaded, stopping scroll")
            break
        else:
            print(f"New content loaded (height: {last_height} -> {new_height})")
    
    # Scroll back to top to ensure we can see the latest tweets
    print("Scrolling back to top...")
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    # Do a few small scrolls to trigger any remaining lazy loading
    print("Performing small scrolls to trigger lazy loading...")
    for i in range(3):
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(1)
    
    print("Scroll sequence completed")

def setup_driver():
    """Setup Chrome driver with options to bypass detection"""
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

def get_tweets_with_bs4(username="johncena"):
    """Get tweets using Selenium for automation and BeautifulSoup for parsing"""
    driver = setup_driver()
    
    try:
        # Go directly to user profile
        url = f"https://x.com/{username}"
        print(f"Opening {url}")
        driver.get(url)
        
        # Wait for initial page load
        print("Waiting for initial page load...")
        time.sleep(10)
        
        # Check current URL
        print(f"Current URL: {driver.current_url}")
        
        # Scroll down to load tweets and trigger lazy loading
        print("Scrolling to load content...")
        scroll_and_load(driver)
        
        # Additional wait after scrolling for content to stabilize
        print("Waiting for content to stabilize after scrolling...")
        time.sleep(5)
        
        # Get page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        tweets = []
        
        # Method 1: Use the new CSS classes you provided
        print("Searching using new CSS classes with BeautifulSoup...")
        
        # Look directly for spans with the new classes
        text_spans = soup.find_all('span', class_='css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-bnwqim')
        print(f"Found {len(text_spans)} spans with new CSS classes")
        
        for i, span in enumerate(text_spans):
            try:
                text = span.get_text().strip()
                if is_valid_tweet(text) and not is_duplicate(text, tweets):
                    tweets.append(text)
                    print(f"✓ Tweet {len(tweets)}: {text}")
                    
                    if len(tweets) >= 3:
                        return tweets
                        
            except Exception as e:
                print(f"Error processing span {i}: {e}")
        
        # Also try finding the outer container structure for context
        if not tweets:
            print("Trying with container structure...")
            outer_divs = soup.find_all('div', class_='css-175oi2r r-1iusvr4 r-16y2uox r-1777fci r-kzbkwu')
            print(f"Found {len(outer_divs)} outer container divs")
            
            for i, outer_div in enumerate(outer_divs[:10]):
                try:
                    # Look for the new span classes within containers
                    container_spans = outer_div.find_all('span', class_='css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-bnwqim')
                    
                    for span in container_spans:
                        text = span.get_text().strip()
                        if is_valid_tweet(text) and not is_duplicate(text, tweets):
                            tweets.append(text)
                            print(f"✓ Tweet {len(tweets)}: {text}")
                            
                            if len(tweets) >= 3:
                                return tweets
                                
                except Exception as e:
                    print(f"Error processing container {i}: {e}")
        
        # Method 2: Try partial matching with the new primary class
        if not tweets:
            print("\nTrying partial matching with css-146c3p1...")
            
            # Look for spans with just the main class
            partial_spans = soup.find_all('span', class_=re.compile(r'css-146c3p1'))
            print(f"Found {len(partial_spans)} spans with css-146c3p1")
            
            for span in partial_spans[:15]:
                try:
                    text = span.get_text().strip()
                    if is_valid_tweet(text) and not is_duplicate(text, tweets):
                        tweets.append(text)
                        print(f"✓ Tweet {len(tweets)}: {text}")
                        
                        if len(tweets) >= 3:
                            break
                except Exception as e:
                    print(f"Error processing span: {e}")
        
        # Method 3: Try the old css-1jxf684 class as fallback
        if not tweets:
            print("\nTrying old css-1jxf684 as fallback...")
            
            # Look for any spans with the old text classes
            old_text_spans = soup.find_all('span', class_='css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3')
            print(f"Found {len(old_text_spans)} old text spans")
            
            for span in old_text_spans[:15]:
                try:
                    text = span.get_text().strip()
                    if is_valid_tweet(text) and not is_duplicate(text, tweets):
                        tweets.append(text)
                        print(f"✓ Tweet {len(tweets)}: {text}")
                        
                        if len(tweets) >= 3:
                            break
                except Exception as e:
                    print(f"Error processing span: {e}")
        
        # Method 4: Try generic span matching within tweet containers
        if not tweets:
            print("\nTrying generic span matching...")
            
            # Try just the main class patterns
            generic_spans = soup.find_all('span', class_=re.compile(r'css-1jxf684|css-146c3p1'))
            print(f"Found {len(generic_spans)} spans with main CSS patterns")
            
            for span in generic_spans[:20]:
                try:
                    text = span.get_text().strip()
                    if is_valid_tweet(text) and not is_duplicate(text, tweets):
                        tweets.append(text)
                        print(f"✓ Tweet {len(tweets)}: {text}")
                        
                        if len(tweets) >= 3:
                            break
                except Exception as e:
                    print(f"Error processing span: {e}")
        
        # Method 4: Look for tweet-like content in articles or data-testid
        if not tweets:
            print("\nTrying to find tweets by data attributes...")
            
            # Look for articles (tweets are often in article tags)
            articles = soup.find_all('article')
            print(f"Found {len(articles)} article elements")
            
            for article in articles[:10]:
                try:
                    # Look for spans with either new or old classes within articles
                    spans = article.find_all('span', class_=re.compile(r'css-146c3p1|css-1jxf684'))
                    for span in spans:
                        text = span.get_text().strip()
                        if is_valid_tweet(text) and not is_duplicate(text, tweets):
                            tweets.append(text)
                            print(f"✓ Tweet {len(tweets)}: {text}")
                            
                            if len(tweets) >= 3:
                                return tweets
                except Exception as e:
                    print(f"Error processing article: {e}")
        
        # Method 5: Debug - show what classes are actually available
        if not tweets:
            print("\nNo tweets found. Debugging page content...")
            
            # Check for common Twitter classes including the new one
            check_patterns = [
                'css-175oi2r',
                'css-146c3p1',  # New class you provided
                'css-1jxf684',  # Old class
                'r-bcqeeo',
                'tweet',
                'TweetTextSize'
            ]
            
            for pattern in check_patterns:
                elements = soup.find_all(class_=re.compile(pattern))
                print(f"Found {len(elements)} elements with class pattern '{pattern}'")
            
            # Show all unique classes on the page (first 20)
            all_elements = soup.find_all(class_=True)
            all_classes = set()
            for el in all_elements:
                if isinstance(el.get('class'), list):
                    all_classes.update(el.get('class'))
            
            print(f"\nFirst 20 unique classes found on page:")
            for i, cls in enumerate(sorted(list(all_classes))[:20]):
                print(f"  {cls}")
        
        return tweets
        
    except Exception as e:
        print(f"Error: {e}")
        return []
        
    finally:
        print("Keeping browser open for 10 seconds for inspection...")
        time.sleep(10)
        driver.quit()

def is_valid_tweet(text):
    """Check if text looks like a valid tweet"""
    if not text or len(text) < 10:
        return False
    
    # Filter out common non-tweet text
    skip_patterns = [
        r'^@\w+$',  # Just mentions
        r'^\d+h$',  # Time stamps like "2h"
        r'^Follow$',
        r'^Following$',
        r'^Retweet$',
        r'^Like$',
        r'^Reply$',
        r'^Share$',
        r'^\d+$',  # Just numbers
        r'^Show this thread$',
        r'^Translate$'
    ]
    
    for pattern in skip_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return False
    
    return True

def is_duplicate(text, existing_tweets):
    """Check if tweet text is already in the list"""
    for existing in existing_tweets:
        if text.lower() == existing.lower():
            return True
    return False

def main():
    username = input("Enter Twitter username (default: elonmusk): ").strip() or "elonmusk"
    
    print(f"\nGetting first 3 tweets from @{username} using Selenium + BeautifulSoup")
    print("="*70)
    
    tweets = get_tweets_with_bs4(username)
    
    # Display results
    print(f"\n{'='*50}")
    print("RESULTS:")
    print(f"{'='*50}")
    
    if tweets:
        for i, tweet in enumerate(tweets, 1):
            print(f"\nTweet {i}:")
            print(f"'{tweet}'")
            print("-" * 40)
    else:
        print("❌ No tweets found!")
        print("\nPossible reasons:")
        print("1. Twitter's structure has changed")
        print("2. Account is private or doesn't exist")
        print("3. Rate limiting or blocking")
        print("4. Need to adjust CSS selectors")

if __name__ == "__main__":
    main()