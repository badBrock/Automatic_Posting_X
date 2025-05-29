from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

USERNAME = "docsharedocsharedoc@gmail.com"  # first login step
HANDLE = "@share_docu64137"       # for second prompt
PASSWORD = "your_password"
TWEET_TEXT = "Automated tweet from Selenium "

# Launch browser
driver = webdriver.Chrome()
driver.get("https://twitter.com/i/flow/login")

wait = WebDriverWait(driver, 20)

try:
    # Step 1: Email/Phone
    user_input = wait.until(EC.presence_of_element_located((By.NAME, "text")))
    user_input.send_keys(USERNAME)
    user_input.send_keys(Keys.ENTER)
    time.sleep(2)

    # Step 2: Handle confirmation (if prompted)
    try:
        handle_input = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        handle_input.send_keys(HANDLE)
        handle_input.send_keys(Keys.ENTER)
        time.sleep(2)
    except:
        pass  # not prompted

    # Step 3: Password
    password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.ENTER)
    time.sleep(5)

    # Compose a tweet
    tweet_compose_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//a[@data-testid='SideNav_NewTweet_Button']")))
    tweet_compose_btn.click()
    time.sleep(2)

    tweet_box = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']")))
    tweet_box.send_keys(TWEET_TEXT)
    time.sleep(1)

    tweet_button = driver.find_element(By.XPATH, "//div[@data-testid='tweetButton']")
    tweet_button.click()
    print("✅ Tweet posted!")

except Exception as e:
    print(f"❌ Error occurred: {e}")

finally:
    time.sleep(5)
    driver.quit()
