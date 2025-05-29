from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime
import subprocess
import threading
import tempfile
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File to store claims and counters
DATA_FILE = 'truth_tracker_data.json'

def load_data():
    """Load existing data from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"claims": []}

def save_data(data):
    """Save data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def run_twitter_automation(tweet_text):
    """Run the Twitter automation script with custom tweet text"""
    try:
        logger.info(f"Starting Twitter automation for tweet: {tweet_text[:50]}...")
        
        # Create a temporary file with the tweet text
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(tweet_text)
            temp_file_path = temp_file.name
        
        logger.info(f"Created temp file: {temp_file_path}")
        
        # Check if twitter_automation.py exists
        if not os.path.exists('twitter_automation.py'):
            logger.error("twitter_automation.py not found!")
            return False, "twitter_automation.py script not found"
        
        # Run the Twitter automation script with the tweet text file as argument
        cmd = ['python', 'twitter_automation.py', temp_file_path]
        logger.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              timeout=300,  # Increased timeout to 5 minutes
                              cwd=os.getcwd())
        
        # Clean up temp file
        try:
            os.unlink(temp_file_path)
            logger.info("Cleaned up temp file")
        except:
            logger.warning("Could not clean up temp file")
        
        logger.info(f"Subprocess return code: {result.returncode}")
        logger.info(f"Subprocess stdout: {result.stdout}")
        logger.info(f"Subprocess stderr: {result.stderr}")
        
        if result.returncode == 0:
            logger.info("✅ Twitter automation completed successfully")
            return True, result.stdout
        else:
            logger.error(f"❌ Twitter automation failed with return code {result.returncode}")
            return False, f"Error: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Twitter automation timed out after 5 minutes")
        return False, "Automation timed out after 5 minutes"
    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        return False, f"File not found: {e}"
    except Exception as e:
        logger.error(f"❌ Twitter automation error: {e}")
        return False, f"Unexpected error: {str(e)}"

@app.route('/')
def index():
    """Main dashboard page"""
    data = load_data()
    return render_template('index.html', claims=data['claims'])

@app.route('/add_claim', methods=['POST'])
def add_claim():
    """Add a new fake claim with counter-facts"""
    fake_claim = request.form.get('fake_claim')
    counter_facts = request.form.get('counter_facts')
    source_url = request.form.get('source_url', '')
    
    if not fake_claim or not counter_facts:
        return jsonify({"error": "Both fake claim and counter facts are required"}), 400
    
    data = load_data()
    
    new_claim = {
        "id": len(data['claims']) + 1,
        "fake_claim": fake_claim,
        "counter_facts": counter_facts,
        "source_url": source_url,
        "timestamp": datetime.now().isoformat(),
        "status": "active"
    }
    
    data['claims'].append(new_claim)
    save_data(data)
    
    return redirect(url_for('index'))

@app.route('/delete_claim/<int:claim_id>', methods=['POST'])
def delete_claim(claim_id):
    """Delete a claim"""
    data = load_data()
    data['claims'] = [claim for claim in data['claims'] if claim['id'] != claim_id]
    save_data(data)
    return redirect(url_for('index'))

@app.route('/twitter_form')
def twitter_form():
    """Show Twitter posting form"""
    return render_template('twitter_form.html')

@app.route('/post_tweet', methods=['POST'])
def post_tweet():
    """Post tweet with custom text"""
    tweet_text = request.form.get('tweet_text')
    
    if not tweet_text:
        return jsonify({"error": "Tweet text is required"}), 400
    
    tweet_text = tweet_text.strip()
    
    if len(tweet_text) > 280:
        return jsonify({"error": f"Tweet text too long ({len(tweet_text)} characters, max 280)"}), 400
    
    if len(tweet_text) == 0:
        return jsonify({"error": "Tweet text cannot be empty"}), 400
    
    logger.info(f"Received tweet request: {tweet_text[:50]}...")
    
    # Initialize status file
    status_file = 'last_tweet_status.txt'
    with open(status_file, 'w') as f:
        f.write("PROCESSING: Starting automation...")
    
    # Run automation in background thread
    def run_automation():
        try:
            logger.info("Starting background automation thread")
            
            # Update status
            with open(status_file, 'w') as f:
                f.write("PROCESSING: Running Twitter automation...")
            
            success, message = run_twitter_automation(tweet_text)
            
            # Store the result for status checking
            status = f"{'SUCCESS' if success else 'FAILED'}: {message}"
            with open(status_file, 'w') as f:
                f.write(status)
            
            logger.info(f"Automation completed with status: {status}")
            
        except Exception as e:
            logger.error(f"Error in automation thread: {e}")
            with open(status_file, 'w') as f:
                f.write(f"FAILED: Thread error - {str(e)}")
    
    thread = threading.Thread(target=run_automation)
    thread.daemon = True  # Make thread daemon so it doesn't prevent app shutdown
    thread.start()
    
    logger.info("Background thread started, redirecting to status page")
    
    return render_template('tweet_sent.html', tweet_text=tweet_text)

@app.route('/tweet_status')
def tweet_status():
    """Check last tweet status"""
    try:
        with open('last_tweet_status.txt', 'r') as f:
            status = f.read().strip()
        logger.info(f"Status check: {status}")
        return jsonify({"status": status})
    except FileNotFoundError:
        logger.warning("Status file not found")
        return jsonify({"status": "No recent tweets"})
    except Exception as e:
        logger.error(f"Error reading status: {e}")
        return jsonify({"status": f"Error reading status: {str(e)}"})

@app.route('/trigger_automation', methods=['POST'])
def trigger_automation():
    """Redirect to Twitter form instead of direct automation"""
    return jsonify({"redirect": "/twitter_form"})

@app.route('/api/claims')
def api_claims():
    """API endpoint to get all claims as JSON"""
    data = load_data()
    return jsonify(data['claims'])

@app.route('/debug')
def debug():
    """Debug endpoint to check system status"""
    debug_info = {
        "current_directory": os.getcwd(),
        "files_in_directory": os.listdir('.'),
        "twitter_script_exists": os.path.exists('twitter_automation.py'),
        "python_version": subprocess.run(['python', '--version'], capture_output=True, text=True).stdout,
        "chromedriver_check": subprocess.run(['chromedriver', '--version'], capture_output=True, text=True).stdout if os.system('which chromedriver') == 0 else "ChromeDriver not found"
    }
    return jsonify(debug_info)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)