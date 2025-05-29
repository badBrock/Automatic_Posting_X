from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import random
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime, timedelta
import re

def setup_driver(headless=True):
    """Setup Chrome driver with optimal settings for Twitter scraping"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless')
    
    # Essential arguments for stability
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    
    # Enhanced anti-detection measures
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Disable logging
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--log-level=3')
    
    # Add language and timezone settings
    chrome_options.add_argument('--lang=en-US')
    chrome_options.add_argument('--accept-lang=en-US,en;q=0.9')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to hide webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome driver initialized successfully")
        return driver
        
    except Exception as e:
        print(f"❌ Failed to initialize Chrome driver: {e}")
        return None

def login_to_twitter(driver, username=None, password=None):
    """Login to Twitter for better access to recent content"""
    if not username or not password:
        print("⚠️ No login credentials provided - continuing without login")
        return False
    
    try:
        print("🔐 Attempting to log in to Twitter...")
        driver.get('https://x.com/i/flow/login')
        time.sleep(5)
        
        # Enter username
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
        )
        username_input.send_keys(username)
        
        # Click Next
        next_button = driver.find_element(By.XPATH, "//span[text()='Next']")
        next_button.click()
        time.sleep(3)
        
        # Enter password
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
        )
        password_input.send_keys(password)
        
        # Click Log in
        login_button = driver.find_element(By.XPATH, "//span[text()='Log in']")
        login_button.click()
        time.sleep(5)
        
        # Check if login was successful
        if "home" in driver.current_url.lower():
            print("✅ Successfully logged in to Twitter")
            return True
        else:
            print("❌ Login failed")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def access_following_timeline(driver):
    """Access the Following timeline which shows chronological tweets"""
    try:
        print("🔄 Accessing Following timeline for chronological order...")
        
        # Go to home first
        driver.get('https://x.com/home')
        time.sleep(3)
        
        # Look for Following tab - multiple strategies
        following_selectors = [
            "//span[text()='Following']",
            "//div[@role='tab']//span[text()='Following']",
            "//a[contains(@href, 'following')]",
            "[data-testid='ScrollSnap-NextButtonLink']",
            "//div[contains(text(), 'Following')]"
        ]
        
        for selector in following_selectors:
            try:
                if selector.startswith("//"):
                    element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                ActionChains(driver).move_to_element(element).click().perform()
                print("✅ Successfully clicked Following tab")
                time.sleep(3)
                return True
                
            except:
                continue
        
        print("⚠️ Could not find Following tab, using default timeline")
        return False
        
    except Exception as e:
        print(f"❌ Error accessing Following timeline: {e}")
        return False

def navigate_to_user_with_following_context(driver, username):
    """Navigate to user profile after establishing Following timeline context"""
    try:
        # First establish Following timeline context
        access_following_timeline(driver)
        
        # Now navigate to the specific user
        print(f"🔍 Navigating to @{username}'s profile...")
        profile_url = f'https://x.com/{username}'
        driver.get(profile_url)
        time.sleep(5)
        
        # Try to click "Latest" if available on profile
        try:
            latest_selectors = [
                "//span[contains(text(), 'Posts')]",  # Sometimes it's just "Posts"
                "//div[contains(@aria-label, 'Timeline')]",
                "//div[@role='tablist']//div[contains(text(), 'Posts')]"
            ]
            
            for selector in latest_selectors:
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    element.click()
                    print("✅ Clicked on Posts/Timeline tab")
                    time.sleep(2)
                    break
                except:
                    continue
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error navigating to user profile: {e}")
        return False

def try_search_approach(driver, username, query_type="latest"):
    """Use Twitter search to get latest tweets from user"""
    try:
        print(f"🔍 Trying search approach for latest tweets from @{username}...")
        
        # Construct search query for latest tweets
        if query_type == "latest":
            search_query = f"from:{username}"
        elif query_type == "recent":
            search_query = f"from:{username} since:2025-05-28"  # Adjust date as needed
        else:
            search_query = f"from:{username}"
        
        # Go to search with the query
        search_url = f"https://x.com/search?q={search_query}&src=typed_query&f=live"
        driver.get(search_url)
        time.sleep(5)
        
        # Look for "Latest" tab in search results
        try:
            latest_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Latest']"))
            )
            latest_tab.click()
            print("✅ Clicked Latest tab in search results")
            time.sleep(3)
        except:
            print("⚠️ Latest tab not found in search, continuing...")
        
        return True
        
    except Exception as e:
        print(f"❌ Search approach failed: {e}")
        return False

def extract_tweet_timestamp_improved(article_element):
    """Improved timestamp extraction"""
    try:
        # Multiple strategies for timestamp extraction
        time_selectors = [
            'time[datetime]',
            'a[href*="/status/"] time',
            'time',
            '[datetime]',
            '.css-4rbku5.css-18t94o4 time'
        ]
        
        for selector in time_selectors:
            try:
                time_element = article_element.find_element(By.CSS_SELECTOR, selector)
                datetime_attr = time_element.get_attribute('datetime')
                if datetime_attr:
                    return datetime_attr
                
                # Try to get text content and parse it
                time_text = time_element.text.strip()
                if time_text:
                    # Handle relative time formats like "2h", "1m", "now"
                    if time_text == "now":
                        return datetime.now().isoformat() + "Z"
                    elif re.match(r'\d+[smh]$', time_text):
                        # Parse relative time
                        number = int(re.findall(r'\d+', time_text)[0])
                        unit = time_text[-1]
                        
                        if unit == 's':
                            delta = timedelta(seconds=number)
                        elif unit == 'm':
                            delta = timedelta(minutes=number)
                        elif unit == 'h':
                            delta = timedelta(hours=number)
                        else:
                            continue
                        
                        timestamp = datetime.now() - delta
                        return timestamp.isoformat() + "Z"
                        
            except:
                continue
        
        return "Unknown"
        
    except:
        return "Unknown"

def extract_tweet_with_enhanced_priority(article_element):
    """Enhanced tweet extraction with better text and timestamp handling"""
    try:
        # Strategy 1: Multiple approaches for tweet text
        text_selectors = [
            '[data-testid="tweetText"]',
            '[data-testid="tweetText"] span',
            '.css-901oao.css-16my406',
            '.css-1dbjc4n .css-901oao',
            '[lang] span',
            'div[lang]'
        ]
        
        tweet_text = ""
        for selector in text_selectors:
            try:
                elements = article_element.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    text_parts = []
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 1 and not text.startswith('@'):
                            text_parts.append(text)
                    
                    if text_parts:
                        tweet_text = ' '.join(text_parts)
                        # Clean up the text
                        tweet_text = re.sub(r'\s+', ' ', tweet_text).strip()
                        
                        if len(tweet_text) > 5:  # Valid tweet text
                            break
            except:
                continue
        
        # Enhanced timestamp extraction
        timestamp = extract_tweet_timestamp_improved(article_element)
        
        # Extract engagement metrics
        metrics = {}
        try:
            # Likes
            like_elements = article_element.find_elements(By.CSS_SELECTOR, '[data-testid="like"]')
            for elem in like_elements:
                aria_label = elem.get_attribute('aria-label') or ""
                if 'like' in aria_label.lower():
                    metrics['likes'] = aria_label
                    break
            
            # Retweets
            retweet_elements = article_element.find_elements(By.CSS_SELECTOR, '[data-testid="retweet"]')
            for elem in retweet_elements:
                aria_label = elem.get_attribute('aria-label') or ""
                if 'repost' in aria_label.lower() or 'retweet' in aria_label.lower():
                    metrics['retweets'] = aria_label
                    break
                    
        except:
            pass
        
        return {
            'text': tweet_text,
            'timestamp': timestamp,
            'metrics': metrics
        }
        
    except Exception as e:
        return {'text': '', 'timestamp': 'Unknown', 'metrics': {}}

def is_very_recent_tweet(timestamp_str, hours_threshold=24):
    """Check if tweet is very recent (within specified hours)"""
    try:
        if timestamp_str == "Unknown":
            return False
        
        # Parse the timestamp
        tweet_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        current_time = datetime.now(tweet_time.tzinfo)
        
        # Check if within threshold
        time_diff = current_time - tweet_time
        return time_diff.total_seconds() <= (hours_threshold * 3600)
        
    except Exception as e:
        return False

def scrape_latest_tweets_enhanced(username, max_tweets=10, headless=True, login_username=None, login_password=None):
    """
    Enhanced latest tweets scraper with multiple strategies
    """
    driver = setup_driver(headless=headless)
    if not driver:
        return []
    
    tweets = []
    seen_tweet_ids = set()
    
    try:
        # Strategy 1: Login for better access
        logged_in = False
        if login_username and login_password:
            logged_in = login_to_twitter(driver, login_username, login_password)
            time.sleep(3)
        
        strategies = [
            ("search_latest", lambda: try_search_approach(driver, username, "latest")),
            ("search_recent", lambda: try_search_approach(driver, username, "recent")),
            ("profile_following_context", lambda: navigate_to_user_with_following_context(driver, username)),
            ("direct_profile", lambda: driver.get(f'https://x.com/{username}'))
        ]
        
        best_tweets = []
        
        for strategy_name, strategy_func in strategies:
            if len(best_tweets) >= max_tweets:
                break
                
            print(f"\n🔄 Trying strategy: {strategy_name}")
            
            try:
                success = strategy_func()
                if not success and strategy_name != "direct_profile":
                    continue
                
                time.sleep(5)
                
                # Collect tweets with this strategy
                strategy_tweets = []
                scroll_attempts = 0
                max_scrolls = 10
                
                while len(strategy_tweets) < max_tweets and scroll_attempts < max_scrolls:
                    # Find articles
                    articles = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"], article[role="article"], article')
                    
                    if not articles:
                        print(f"No articles found with {strategy_name}")
                        break
                    
                    new_tweets_this_scroll = 0
                    
                    for article in articles:
                        if len(strategy_tweets) >= max_tweets:
                            break
                        
                        try:
                            tweet_data = extract_tweet_with_enhanced_priority(article)
                            tweet_text = tweet_data.get('text', '').strip()
                            timestamp = tweet_data.get('timestamp', 'Unknown')
                            
                            # Skip invalid tweets
                            if (not tweet_text or len(tweet_text) < 10 or 
                                tweet_text.startswith('@') or 
                                'Show this thread' in tweet_text or
                                'Likes. Like' in tweet_text):
                                continue
                            
                            # Generate ID for deduplication
                            tweet_id = hashlib.md5(f"{tweet_text[:50]}_{timestamp}".encode()).hexdigest()[:12]
                            
                            if tweet_id in seen_tweet_ids:
                                continue
                            
                            tweet_obj = {
                                'id': tweet_id,
                                'text': tweet_text,
                                'timestamp': timestamp,
                                'metrics': tweet_data.get('metrics', {}),
                                'strategy': strategy_name,
                                'is_very_recent': is_very_recent_tweet(timestamp, 24),
                                'is_recent': is_very_recent_tweet(timestamp, 168)  # 7 days
                            }
                            
                            strategy_tweets.append(tweet_obj)
                            seen_tweet_ids.add(tweet_id)
                            new_tweets_this_scroll += 1
                            
                            print(f"✅ Found tweet with {strategy_name}: {tweet_text[:60]}... ({timestamp})")
                            
                        except Exception as e:
                            continue
                    
                    # Scroll if we need more tweets
                    if len(strategy_tweets) < max_tweets and new_tweets_this_scroll > 0:
                        driver.execute_script("window.scrollBy(0, 800);")
                        time.sleep(2)
                        scroll_attempts += 1
                    else:
                        break
                
                # Add strategy tweets to best collection
                if strategy_tweets:
                    print(f"✅ Strategy {strategy_name} found {len(strategy_tweets)} tweets")
                    best_tweets.extend(strategy_tweets)
                    
                    # If we found very recent tweets, prioritize this strategy
                    very_recent_count = sum(1 for t in strategy_tweets if t.get('is_very_recent', False))
                    if very_recent_count > 0:
                        print(f"🔥 Found {very_recent_count} very recent tweets with {strategy_name}")
                        break
                
            except Exception as e:
                print(f"❌ Strategy {strategy_name} failed: {e}")
                continue
        
        # Remove duplicates and sort by timestamp
        tweets_dict = {tweet['id']: tweet for tweet in best_tweets}
        tweets = list(tweets_dict.values())
        
        # Sort by timestamp (most recent first)
        try:
            tweets.sort(key=lambda x: x['timestamp'] if x['timestamp'] != 'Unknown' else '1970-01-01', reverse=True)
        except:
            pass
        
        # Limit to requested number
        tweets = tweets[:max_tweets]
        
        very_recent_count = sum(1 for t in tweets if t.get('is_very_recent', False))
        recent_count = sum(1 for t in tweets if t.get('is_recent', False))
        
        print(f"\n🎉 Collected {len(tweets)} total tweets!")
        print(f"🔥 Very recent (24h): {very_recent_count}")
        print(f"📅 Recent (7 days): {recent_count}")
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        
    finally:
        driver.quit()
        print("🔒 Browser closed")
    
    return tweets

def display_tweets_enhanced(tweets, username):
    """Enhanced display with recency indicators"""
    if not tweets:
        print(f"❌ No tweets collected for @{username}")
        return
    
    print(f"\n🐦 Latest {len(tweets)} tweets from @{username}:")
    print("=" * 80)
    
    very_recent = sum(1 for t in tweets if t.get('is_very_recent', False))
    recent = sum(1 for t in tweets if t.get('is_recent', False))
    
    print(f"🔥 Very recent (24h): {very_recent}")
    print(f"📅 Recent (7 days): {recent}")
    print(f"🔧 Strategies used: {', '.join(set(t.get('strategy', 'unknown') for t in tweets))}")
    print("=" * 80)
    
    for i, tweet in enumerate(tweets, 1):
        if tweet.get('is_very_recent'):
            time_indicator = "🔥 HOT"
        elif tweet.get('is_recent'):
            time_indicator = "📅 Recent"
        else:
            time_indicator = "📚 Older"
        
        print(f"\n{i}. {time_indicator} | {tweet['timestamp']}")
        print(f"   Strategy: {tweet.get('strategy', 'unknown')}")
        print(f"   Text: {tweet['text']}")
        
        if tweet.get('metrics'):
            metrics_str = ", ".join([f"{k}: {v}" for k, v in tweet['metrics'].items() if v])
            if metrics_str:
                print(f"   Engagement: {metrics_str}")
        
        print("-" * 60)

def save_tweets_enhanced(tweets, username, filename=None):
    """Save tweets with enhanced metadata"""
    if not filename:
        timestamp = int(time.time())
        filename = f"{username}_latest_tweets_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'username': username,
                'collected_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_tweets': len(tweets),
                'very_recent_count': sum(1 for t in tweets if t.get('is_very_recent', False)),
                'recent_count': sum(1 for t in tweets if t.get('is_recent', False)),
                'strategies_used': list(set(t.get('strategy', 'unknown') for t in tweets)),
                'tweets': tweets
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Tweets saved to {filename}")
        
    except Exception as e:
        print(f"❌ Could not save tweets: {e}")

# === MAIN EXECUTION ===
def main():
    print("🚀 Enhanced Latest Tweets Scraper - Multi-Strategy Approach")
    print("=" * 70)
    
    # Configuration
    username = "johncena"  # Change this to target username
    max_tweets = 5
    headless_mode = False  # Set to False to see what's happening
    save_to_file = True
    
    # Optional login credentials for better access
    # Uncomment and fill these if you have Twitter credentials
    # login_username = "your_twitter_username"
    # login_password = "your_twitter_password"
    login_username = None
    login_password = None
    
    print(f"Target: @{username}")
    print(f"Max tweets: {max_tweets}")
    print(f"Headless mode: {headless_mode}")
    print(f"Login: {'Yes' if login_username else 'No'}")
    print("-" * 70)
    
    # Scrape tweets with enhanced method
    tweets = scrape_latest_tweets_enhanced(username, max_tweets, headless_mode, 
                                         login_username, login_password)
    
    # Display results
    display_tweets_enhanced(tweets, username)
    
    # Save to file if requested
    if save_to_file and tweets:
        save_tweets_enhanced(tweets, username)
    
    print(f"\n✨ Enhanced scraping completed! Found {len(tweets)} tweets.")
    
    if not tweets:
        print("\n💡 Troubleshooting tips:")
        print("1. Try with login credentials for better access")
        print("2. Run with headless_mode = False to see what's happening") 
        print("3. Check if the profile exists and is public")
        print("4. Try a different username with more recent activity")
        print("5. Consider rate limiting - wait between runs")

if __name__ == "__main__":
    main()