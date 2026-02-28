"""
Database Module for PRISM
Store and track scam reports for real-time dashboard
"""

import sqlite3
import json
from datetime import datetime
import os

DB_PATH = 'data/scam_reports.db'


def init_database():
    """Initialize the database with required tables"""
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create scam reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scam_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            language TEXT,
            language_code TEXT,
            has_urls BOOLEAN,
            has_phones BOOLEAN,
            has_urgency BOOLEAN,
            has_financial BOOLEAN,
            has_threats BOOLEAN,
            keyword_count INTEGER,
            message_length INTEGER,
            source TEXT DEFAULT 'web',
            date_created TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create URL reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS url_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            domain TEXT,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            is_safe BOOLEAN,
            threat_type TEXT,
            timestamp TEXT NOT NULL,
            date_created TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create statistics cache table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics_cache (
            id INTEGER PRIMARY KEY,
            total_scans INTEGER DEFAULT 0,
            total_scams_detected INTEGER DEFAULT 0,
            total_urls_scanned INTEGER DEFAULT 0,
            total_images_processed INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Initialize statistics if not exists
    cursor.execute('SELECT COUNT(*) FROM statistics_cache')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO statistics_cache (id, total_scans, total_scams_detected, 
                                         total_urls_scanned, total_images_processed)
            VALUES (1, 0, 0, 0, 0)
        ''')
    
    conn.commit()
    conn.close()


def add_scam_report(result_data):
    """
    Add a scam analysis report to database
    
    Args:
        result_data: Analysis result dictionary
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Extract data
        indicators = result_data.get('indicators', {})
        
        cursor.execute('''
            INSERT INTO scam_reports (
                timestamp, risk_level, risk_score, language, language_code,
                has_urls, has_phones, has_urgency, has_financial, has_threats,
                keyword_count, message_length, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            result_data.get('prediction', 'Unknown'),
            result_data.get('risk_score', 0),
            result_data.get('language', 'Unknown'),
            result_data.get('language_code', 'unknown'),
            indicators.get('contains_urls', False),
            indicators.get('contains_phone', False),
            indicators.get('has_urgency', False),
            indicators.get('has_financial_terms', False),
            indicators.get('has_threats', False),
            len(result_data.get('suspicious_keywords', [])),
            len(result_data.get('text', '')),
            result_data.get('source', 'web')
        ))
        
        # Update statistics
        cursor.execute('''
            UPDATE statistics_cache 
            SET total_scans = total_scans + 1,
                total_scams_detected = total_scams_detected + ?,
                last_updated = ?
            WHERE id = 1
        ''', (
            1 if result_data.get('prediction') in ['Scam', 'Suspicious'] else 0,
            datetime.now().isoformat()
        ))
        
        # Update image count if from OCR
        if result_data.get('source') == 'image':
            cursor.execute('''
                UPDATE statistics_cache 
                SET total_images_processed = total_images_processed + 1
                WHERE id = 1
            ''')
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"Error adding scam report: {e}")
        return False
    
    finally:
        conn.close()


def add_url_report(url, analysis_result):
    """
    Add a URL scan report to database
    
    Args:
        url: URL scanned
        analysis_result: URL analysis result dictionary
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        domain_info = analysis_result.get('domain_info', {})
        
        cursor.execute('''
            INSERT INTO url_reports (
                url, domain, risk_score, risk_level, is_safe, threat_type, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            url,
            domain_info.get('domain', 'unknown'),
            analysis_result.get('risk_score', 0),
            analysis_result.get('risk_level', 'UNKNOWN'),
            analysis_result.get('is_safe', True),
            analysis_result.get('safe_browsing', {}).get('threat_type'),
            datetime.now().isoformat()
        ))
        
        # Update statistics
        cursor.execute('''
            UPDATE statistics_cache 
            SET total_urls_scanned = total_urls_scanned + 1,
                last_updated = ?
            WHERE id = 1
        ''', (datetime.now().isoformat(),))
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"Error adding URL report: {e}")
        return False
    
    finally:
        conn.close()


def get_statistics():
    """Get overall statistics from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get cached statistics
        cursor.execute('SELECT * FROM statistics_cache WHERE id = 1')
        stats = cursor.fetchone()
        
        if not stats:
            return {
                'total_scans': 0,
                'total_scams_detected': 0,
                'total_urls_scanned': 0,
                'total_images_processed': 0
            }
        
        return {
            'total_scans': stats[1],
            'total_scams_detected': stats[2],
            'total_urls_scanned': stats[3],
            'total_images_processed': stats[4],
            'last_updated': stats[5]
        }
    
    finally:
        conn.close()


def get_recent_reports(limit=50):
    """Get recent scam reports"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get scam reports
        cursor.execute('''
            SELECT risk_level, risk_score, language, timestamp, has_urls, has_phones, source, language_code
            FROM scam_reports
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))
        scam_rows = cursor.fetchall()

        # Get URL reports
        cursor.execute('''
            SELECT risk_level, risk_score, url, timestamp
            FROM url_reports
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))
        url_rows = cursor.fetchall()
        
        all_reports = []
        
        # Process scam reports
        for row in scam_rows:
            all_reports.append({
                'risk_level': row[0],
                'risk_score': row[1],
                'language': row[2],
                'timestamp': row[3],
                'has_urls': bool(row[4]),
                'has_phones': bool(row[5]),
                'source': row[6] if len(row) > 6 else 'web',
                'language_code': row[7] if len(row) > 7 else 'unknown'
            })
            
        # Process URL reports
        for row in url_rows:
            all_reports.append({
                'risk_level': row[0],
                'risk_score': row[1],
                'language': 'URL Scan',
                'timestamp': row[3],
                'has_urls': True,
                'has_phones': False,
                'source': 'url',
                'details': row[2]
            })
            
        # Sort by timestamp descending
        all_reports.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return all_reports[:limit]
    
    finally:
        conn.close()


def get_language_distribution():
    """Get distribution of languages in reports"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT language, COUNT(*) as count
            FROM scam_reports
            WHERE language IS NOT NULL AND language != 'Unknown'
            GROUP BY language
            ORDER BY count DESC
            LIMIT 10
        ''')
        
        rows = cursor.fetchall()
        
        lang_map_full = {
            'en': 'English', 'hi': 'Hindi', 'mr': 'Marathi', 'ta': 'Tamil', 'te': 'Telugu',
            'bn': 'Bengali', 'gu': 'Gujarati', 'kn': 'Kannada', 'ml': 'Malayalam', 'pa': 'Punjabi',
            'es': 'Spanish', 'fr': 'French', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
            'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ru': 'Russian', 'ar': 'Arabic',
            'id': 'Indonesian', 'vi': 'Vietnamese', 'th': 'Thai', 'so': 'Somali', 'uk': 'Ukrainian',
            'pl': 'Polish', 'tr': 'Turkish', 'nl': 'Dutch', 'sv': 'Swedish'
        }
        
        result = {}
        for row in rows:
            lang_name = row[0]
            count = row[1]
            lower_name = lang_name.lower()
            
            # Map if it's a known short code
            mapped_name = lang_map_full.get(lower_name, lang_name)
            
            result[mapped_name] = result.get(mapped_name, 0) + count
            
        # Return top 10 sorted by count
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True)[:10])
    
    finally:
        conn.close()


def get_risk_level_distribution():
    """Get distribution of risk levels"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT risk_level, COUNT(*) as count
            FROM scam_reports
            GROUP BY risk_level
            ORDER BY count DESC
        ''')
        
        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}
    
    finally:
        conn.close()


def get_trending_patterns():
    """Get trending scam patterns from last 24 hours"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(risk_score) as avg_risk,
                SUM(CASE WHEN has_urls THEN 1 ELSE 0 END) as urls_count,
                SUM(CASE WHEN has_phones THEN 1 ELSE 0 END) as phones_count,
                SUM(CASE WHEN has_urgency THEN 1 ELSE 0 END) as urgency_count,
                SUM(CASE WHEN has_financial THEN 1 ELSE 0 END) as financial_count,
                SUM(CASE WHEN has_threats THEN 1 ELSE 0 END) as threats_count
            FROM scam_reports
            WHERE datetime(timestamp) > datetime('now', '-1 day')
        ''')
        
        row = cursor.fetchone()
        
        if not row or row[0] == 0:
            return None
        
        return {
            'total_last_24h': row[0],
            'average_risk_score': round(row[1], 2) if row[1] else 0,
            'urls_detected': row[2] or 0,
            'phones_detected': row[3] or 0,
            'urgency_tactics': row[4] or 0,
            'financial_terms': row[5] or 0,
            'threats_detected': row[6] or 0
        }
    
    finally:
        conn.close()


def get_hourly_distribution():
    """Get reports distribution by hour (last 24 hours)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                strftime('%H', timestamp) as hour,
                COUNT(*) as count
            FROM scam_reports
            WHERE datetime(timestamp) > datetime('now', '-1 day')
            GROUP BY hour
            ORDER BY hour
        ''')
        
        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}
    
    finally:
        conn.close()


def get_daily_distribution(days=7):
    """Get reports distribution by day (last N days)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                date(timestamp) as day_date,
                COUNT(*) as count
            FROM scam_reports
            WHERE date(timestamp) >= date('now', ?)
            GROUP BY day_date
            ORDER BY day_date ASC
        ''', (f'-{days} days',))
        
        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}
    
    finally:
        conn.close()


# Initialize database on import
init_database()


# Test function
if __name__ == "__main__":
    print("\n📊 Database Module Test\n")
    
    # Test data
    test_report = {
        'prediction': 'Scam',
        'risk_score': 85,
        'language': 'English',
        'language_code': 'en',
        'text': 'Test scam message',
        'suspicious_keywords': ['urgent', 'verify'],
        'indicators': {
            'contains_urls': True,
            'contains_phone': True,
            'has_urgency': True,
            'has_financial_terms': True,
            'has_threats': False
        },
        'source': 'web'
    }
    
    print("Adding test report...")
    add_scam_report(test_report)
    
    stats = get_statistics()
    print(f"\nStatistics:")
    print(f"Total scans: {stats['total_scans']}")
    print(f"Total scams detected: {stats['total_scams_detected']}")
    
    print("\n✅ Database test completed!")
