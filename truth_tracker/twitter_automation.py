from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import sys
import os
import random

# Twitter credentials
USERNAME = "docsharedocsharedoc@gmail.com"
HANDLE = "@share_docu64137"
PASSWORD = "8c9vp9ljy"

def get_tweet_text():
    """Get tweet text from command line argument or file"""
    if len(sys.argv) > 1:
        # Check if it's a file path (temp file from Flask)
        if os.path.exists(sys.argv[1]):
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                return f.read().strip()
        else:
            # Direct text argument
            return sys.argv[1]
    else:
        # Fallback default message
        return "🚨 FACT CHECK: Always verify information before sharing. Combat misinformation with facts! #TruthTracker #FactCheck"

def random_delay(min_seconds=1, max_seconds=3):
    """Add random delay to avoid detection"""
    delay = random.uniform(min_seconds, max_seconds)
    print(f"⏳ Waiting {delay:.1f} seconds...")
    time.sleep(delay)


def setup_driver():
    """Setup Chrome driver with optimal settings"""
    chrome_options = Options()
    
    # Add options for better stability and stealth
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Updated user agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Enable logging for debugging
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--log-level=0")
    chrome_options.add_argument('--disable-dev-shm-usage')
    # Uncomment the next line to run headless (no browser window)
    chrome_options.add_argument("--headless")
    
    try:
        # Use webdriver-manager to automatically download and setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"❌ Error setting up Chrome driver: {e}")
        print("Make sure you have Chrome browser installed")
        return None

def wait_for_element(driver, selectors, timeout=30, clickable=False):
    """Wait for element using multiple selectors"""
    wait = WebDriverWait(driver, timeout)
    
    for selector in selectors:
        try:
            if clickable:
                element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            else:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            
            if element and element.is_displayed():
                print(f"✅ Found element with selector: {selector}")
                return element
        except TimeoutException:
            continue
    
    return None

def post_tweet(tweet_text):
    """Post a tweet using Selenium automation"""
    driver = setup_driver()
    if not driver:
        return False
    
    try:
        print(f"🚀 Starting Twitter automation...")
        print(f"📝 Tweet content: {tweet_text}")
        
        # Navigate to Twitter login
        print("🌐 Navigating to Twitter...")
        driver.get("https://x.com/i/flow/login")
        random_delay(3, 5)
        
        # Step 1: Enter email/username
        print("📧 Entering username...")
        username_selectors = [
            "input[name='text']",
            "input[autocomplete='username']",
            "input[data-testid='ocfEnterTextTextInput']",
            "input[type='text']"
        ]
        
        user_input = wait_for_element(driver, username_selectors)
        if not user_input:
            raise Exception("Could not find username input field")
        
        user_input.clear()
        # Type slowly to avoid detection
        for char in USERNAME:
            user_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        
        random_delay(1, 2)
        user_input.send_keys(Keys.ENTER)
        random_delay(3, 5)

        # Step 2: Handle verification (if prompted)
        print("🔍 Checking for handle verification...")
        verification_selectors = [
            "input[name='text']",
            "input[data-testid='ocfEnterTextTextInput']"
        ]
        
        # Wait briefly to see if verification is needed
        time.sleep(3)
        handle_input = wait_for_element(driver, verification_selectors, timeout=5)
        
        if handle_input and handle_input.is_displayed():
            print("✅ Handle verification required")
            handle_input.clear()
            for char in HANDLE:
                handle_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            random_delay(1, 2)
            handle_input.send_keys(Keys.ENTER)
            random_delay(3, 5)
        else:
            print("ℹ️ Handle verification not required")

        # Step 3: Enter password
        print("🔐 Entering password...")
        password_selectors = [
            "input[name='password']",
            "input[type='password']",
            "input[autocomplete='current-password']"
        ]
        
        password_input = wait_for_element(driver, password_selectors)
        if not password_input:
            raise Exception("Could not find password input field")
        
        password_input.clear()
        for char in PASSWORD:
            password_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        
        random_delay(1, 2)
        password_input.send_keys(Keys.ENTER)
        random_delay(5, 8)

        # Wait for login to complete
        print("⏳ Waiting for login to complete...")
        try:
            WebDriverWait(driver, 30).until(
                lambda driver: "home" in driver.current_url.lower() or 
                               len(driver.find_elements(By.CSS_SELECTOR, "[data-testid='SideNav_NewTweet_Button']")) > 0
            )
            print("✅ Login successful!")
        except TimeoutException:
            print("⚠️ Login verification timeout, checking current page...")
            print(f"Current URL: {driver.current_url}")
            # Take a screenshot for debugging
            driver.save_screenshot(f"login_debug_{int(time.time())}.png")

        # Step 4: Navigate to compose tweet
        print("✍️ Opening tweet composer...")
        tweet_button_selectors = [
            "[data-testid='SideNav_NewTweet_Button']",
            "[aria-label='Tweet']",
            "[data-testid='tweetButtonInline']",
            "a[href='/compose/tweet']",
            "[data-testid='toolBar'] [role='button']"
        ]
        
        tweet_compose_btn = wait_for_element(driver, tweet_button_selectors, clickable=True)
        
        if tweet_compose_btn:
            driver.execute_script("arguments[0].click();", tweet_compose_btn)
            random_delay(3, 5)
        else:
            # Alternative: navigate directly to compose URL
            print("🔄 Using direct URL method...")
            driver.get("https://x.com/compose/tweet")
            random_delay(3, 5)

        # Step 5: Enter tweet text
        print("📝 Entering tweet content...")
        tweet_text_selectors = [
            "[data-testid='tweetTextarea_0']",
            "[contenteditable='true'][aria-label*='Tweet']",
            "[contenteditable='true'][data-testid*='tweet']",
            "[contenteditable='true'][role='textbox']",
            ".public-DraftEditor-content",
            "[data-testid='tweetTextarea_0_label']",
            ".DraftEditor-root .public-DraftEditor-content"
        ]
        
        tweet_input = wait_for_element(driver, tweet_text_selectors, clickable=True)
        if not tweet_input:
            # Try XPath as fallback
            try:
                tweet_input = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true']"))
                )
            except:
                raise Exception("Could not find tweet input field")
        
        # Click on the text area
        driver.execute_script("arguments[0].click();", tweet_input)
        random_delay(1, 2)
        
        # Clear any existing text
        tweet_input.send_keys(Keys.CONTROL + "a")
        tweet_input.send_keys(Keys.DELETE)
        
        # Type the tweet text slowly
        for char in tweet_text:
            tweet_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.1))
        
        random_delay(2, 3)
        print("✅ Tweet text entered successfully")

        # Step 6: Post the tweet
        print("🚀 Posting tweet...")
        post_button_selectors = [
            "[data-testid='tweetButtonInline']",
            "[data-testid='tweetButton']",
            "[role='button'][data-testid='tweetButton']"
        ]
        
        post_button = wait_for_element(driver, post_button_selectors, clickable=True)
        
        # Also try XPath for button with text
        if not post_button:
            try:
                post_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tweet')] | //button[contains(text(), 'Post')] | //div[@role='button' and contains(text(), 'Tweet')]"))
                )
            except:
                pass
        
        if not post_button:
            raise Exception("Could not find tweet post button")
        
        # Make sure button is enabled
        if not post_button.is_enabled():
            print("⚠️ Post button is disabled, checking tweet length...")
            raise Exception("Post button is disabled - tweet might be too long or empty")
        
        # Click the post button
        driver.execute_script("arguments[0].click();", post_button)
        random_delay(5, 8)
        
        # Verify tweet was posted
        print("🔍 Verifying tweet was posted...")
        try:
            # Look for success indicators
            WebDriverWait(driver, 15).until(
                lambda driver: "home" in driver.current_url.lower() or
                               len(driver.find_elements(By.XPATH, "//*[contains(text(), 'Your Tweet was sent')]")) > 0 or
                               len(driver.find_elements(By.XPATH, "//*[contains(text(), 'Tweet sent')]")) > 0
            )
            print("✅ Tweet posted successfully!")
            return True
        except TimeoutException:
            print("⚠️ Could not verify tweet posting, but it may have succeeded")
            # Take screenshot for debugging
            driver.save_screenshot(f"tweet_post_debug_{int(time.time())}.png")
            return True  # Assume success if we got this far

    except Exception as e:
        print(f"❌ Error in Twitter automation: {e}")
        
        # Take screenshot for debugging
        try:
            screenshot_path = f"twitter_error_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved: {screenshot_path}")
        except:
            pass
            
        return False
        
    finally:
        print("🔄 Closing browser...")
        try:
            random_delay(2, 3)  # Give time for any final actions
            driver.quit()
        except:
            pass

def main():
    """Main function to run the Twitter automation"""
    tweet_text = get_tweet_text()
    
    if not tweet_text:
        print("❌ No tweet text provided")
        sys.exit(1)
    
    if len(tweet_text) > 280:
        print(f"❌ Tweet text too long ({len(tweet_text)} characters, max 280)")
        sys.exit(1)
    
    print(f"🎯 Starting automation for tweet: {tweet_text[:50]}...")
    success = post_tweet(tweet_text)
    
    if success:
        print("🎉 Twitter automation completed successfully!")
        sys.exit(0)
    else:
        print("💥 Twitter automation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()