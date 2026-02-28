"""
PRISM - Enhanced Flask Web Application
Advanced scam detection with OCR, URL scanning, and real-time dashboard
"""

from flask import Flask, render_template, request, jsonify
import sys
import os
import requests

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.inference import PrismInference
from src.ocr_scanner import extract_text_from_image, is_valid_image, get_image_info
from src.url_scanner import analyze_url
from src.database import add_scam_report, add_url_report, get_statistics, get_recent_reports, \
    get_language_distribution, get_risk_level_distribution, get_trending_patterns, get_daily_distribution

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year static file caching

@app.after_request
def add_header(response):
    """Add caching headers for static files for optimization"""
    if 'Cache-Control' not in response.headers:
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        else:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

# Load model once at startup
print("🔄 Loading PRISM model...")
try:
    model = PrismInference()
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Serve the dashboard page"""
    return render_template('dashboard.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze message endpoint"""
    if model is None:
        return jsonify({
            'error': 'Model not loaded. Please train the model first.',
            'instructions': 'Run: python src/prepare_dataset.py && python train_simple.py'
        }), 500
    
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Please provide a message to analyze'}), 400
        
        # Get prediction
        result = model.predict(message)
        explanation = model.get_explanation(result)
        
        # Add explanation to result
        result['explanation'] = explanation
        result['source'] = 'text'
        
        # Calculate statistics
        result['stats'] = {
            'characters': len(message),
            'words': len(message.split()),
            'urls': len(result['urls_found']),
            'phones': len(result['phone_numbers_found'])
        }
        
        # Scan URLs if present
        if result['urls_found']:
            url_scans = []
            for url in result['urls_found'][:3]:  # Limit to first 3 URLs
                try:
                    url_analysis = analyze_url(url)
                    url_scans.append(url_analysis)
                    # Store URL report in database
                    add_url_report(url, url_analysis)
                except Exception as e:
                    print(f"Error scanning URL {url}: {e}")
            
            result['url_scans'] = url_scans
        
        # Store report in database
        add_scam_report(result)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    """Analyze image/screenshot endpoint"""
    if model is None:
        return jsonify({
            'error': 'Model not loaded. Please train the model first.'
        }), 500
    
    try:
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file data
        file_data = file.read()
        
        # Validate image
        if not is_valid_image(file_data):
            return jsonify({'error': 'Invalid image file'}), 400
        
        # Get image info
        image_info = get_image_info(file_data)
        
        # Extract text using OCR
        ocr_result = extract_text_from_image(file_data)
        
        if not ocr_result['success']:
            return jsonify({
                'error': ocr_result.get('error', 'OCR failed'),
                'installation_guide': ocr_result.get('installation_guide')
            }), 500
        
        extracted_text = ocr_result['text']
        
        if not extracted_text or len(extracted_text.strip()) < 5:
            return jsonify({
                'error': 'No text detected in image. Please ensure the image contains readable text.',
                'ocr_metadata': ocr_result.get('metadata')
            }), 400
        
        # Analyze the extracted text
        result = model.predict(extracted_text)
        explanation = model.get_explanation(result)
        
        # Add OCR-specific data
        result['explanation'] = explanation
        result['source'] = 'image'
        result['ocr_metadata'] = ocr_result.get('metadata')
        result['image_info'] = image_info
        result['extracted_text'] = extracted_text
        
        # Calculate statistics
        result['stats'] = {
            'characters': len(extracted_text),
            'words': len(extracted_text.split()),
            'urls': len(result['urls_found']),
            'phones': len(result['phone_numbers_found'])
        }
        
        # Scan URLs if present
        if result['urls_found']:
            url_scans = []
            for url in result['urls_found'][:3]:
                try:
                    url_analysis = analyze_url(url)
                    url_scans.append(url_analysis)
                    add_url_report(url, url_analysis)
                except Exception as e:
                    print(f"Error scanning URL {url}: {e}")
            
            result['url_scans'] = url_scans
        
        # Store report in database
        add_scam_report(result)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'Image analysis failed: {str(e)}'}), 500


@app.route('/scan-url', methods=['POST'])
def scan_url():
    """Scan URL endpoint"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'Please provide a URL to scan'}), 400
        
        # Analyze URL
        result = analyze_url(url)
        
        # Store URL report
        add_url_report(url, result)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'URL scan failed: {str(e)}'}), 500


@app.route('/api/statistics')
def api_statistics():
    """Get overall statistics"""
    try:
        stats = get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recent-reports')
def api_recent_reports():
    """Get recent reports"""
    try:
        limit = request.args.get('limit', 50, type=int)
        reports = get_recent_reports(limit)
        return jsonify(reports)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/language-distribution')
def api_language_distribution():
    """Get language distribution"""
    try:
        distribution = get_language_distribution()
        return jsonify(distribution)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/risk-distribution')
def api_risk_distribution():
    """Get risk level distribution"""
    try:
        distribution = get_risk_level_distribution()
        return jsonify(distribution)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trending-patterns')
def api_trending_patterns():
    """Get trending scam patterns"""
    try:
        patterns = get_trending_patterns()
        return jsonify(patterns if patterns else {})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/daily-distribution')
def api_daily_distribution():
    """Get daily scam reports distribution"""
    try:
        days = request.args.get('days', 7, type=int)
        distribution = get_daily_distribution(days)
        return jsonify(distribution)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/global-risk')
def api_global_risk():
    """Get real global cyber risk status from an external authority (SANS ISC)"""
    try:
        # Fetch SANS ISC InfoCon status (green, yellow, orange, red)
        resp = requests.get('https://isc.sans.edu/api/infocon?json', timeout=3)
        if resp.ok:
            data = resp.json()
            status = data.get('status', 'green').lower()
            
            # Map status to a 0-100 scale:
            if status == 'red':
                risk_score = 95
                threat_level = 'SEVERE'
            elif status == 'orange':
                risk_score = 75
                threat_level = 'HIGH'
            elif status == 'yellow':
                risk_score = 45
                threat_level = 'MODERATE'
            else: # green
                risk_score = 15
                threat_level = 'LOW'
                
            return jsonify({
                'source': 'SANS Internet Storm Center',
                'infocon': status,
                'risk_score': risk_score,
                'threat_level': threat_level
            })
    except Exception as e:
        print(f"Global risk API error: {e}")
        
    # Fallback if API fails
    return jsonify({
        'source': 'Fallback',
        'infocon': 'green',
        'risk_score': 20, 
        'threat_level': 'LOW'
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'features': {
            'text_analysis': True,
            'image_ocr': True,
            'url_scanning': True,
            'dashboard': True
        }
    })


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🛡️  PRISM - Advanced Scam Detection System")
    print("="*80)
    print("\n✨ Features Enabled:")
    print("   📝 Text Message Analysis")
    print("   📸 Screenshot OCR Analysis")
    print("   🔗 URL Deep Scanning")
    print("   📊 Real-Time Dashboard")
    print("\n🌐 Starting server...")
    print("📍 Main App: http://localhost:5000")
    print("📊 Dashboard: http://localhost:5000/dashboard")
    print("\n💡 Press Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
