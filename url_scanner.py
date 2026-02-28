"""
URL Scanner Module for PRISM
Deep scanning of URLs for threat intelligence
"""

import re
import requests
from urllib.parse import urlparse
from datetime import datetime
import socket
import ssl

def extract_domain_info(url):
    """Extract domain information from URL"""
    try:
        parsed = urlparse(url if url.startswith('http') else f'http://{url}')
        domain = parsed.netloc or parsed.path.split('/')[0]
        return {
            'domain': domain,
            'scheme': parsed.scheme,
            'path': parsed.path,
            'full_url': url
        }
    except Exception as e:
        return {'error': str(e)}


def check_url_patterns(url):
    """Check for suspicious URL patterns"""
    suspicious_indicators = []
    risk_score = 0
    
    # Convert to lowercase for checking
    url_lower = url.lower()
    
    # Check for IP address instead of domain
    if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
        suspicious_indicators.append('Uses IP address instead of domain name')
        risk_score += 30
    
    # Check for suspicious TLDs
    suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work', '.click']
    for tld in suspicious_tlds:
        if url_lower.endswith(tld):
            suspicious_indicators.append(f'Uses suspicious TLD: {tld}')
            risk_score += 20
            break
    
    # Check for excessive subdomains
    domain_info = extract_domain_info(url)
    if 'domain' in domain_info:
        subdomain_count = domain_info['domain'].count('.')
        if subdomain_count > 3:
            suspicious_indicators.append(f'Excessive subdomains ({subdomain_count})')
            risk_score += 15
    
    # Check for URL encoding/obfuscation
    if '%' in url and url.count('%') > 3:
        suspicious_indicators.append('Contains excessive URL encoding')
        risk_score += 15
    
    # Check for suspicious keywords in URL
    suspicious_keywords = ['login', 'verify', 'secure', 'account', 'update', 'confirm', 
                          'banking', 'alert', 'suspended', 'locked', 'credential']
    found_keywords = [kw for kw in suspicious_keywords if kw in url_lower]
    if found_keywords:
        suspicious_indicators.append(f'Contains suspicious keywords: {", ".join(found_keywords[:3])}')
        risk_score += 10 * min(len(found_keywords), 3)
    
    # Check for very long URLs (often used in phishing)
    if len(url) > 150:
        suspicious_indicators.append(f'Unusually long URL ({len(url)} characters)')
        risk_score += 10
    
    # Check for @ symbol (can be used to trick users)
    if '@' in url:
        suspicious_indicators.append('Contains @ symbol (potential spoofing)')
        risk_score += 25
    
    # Check for shortener services
    shortener_domains = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly', 'is.gd', 'cutt.ly']
    for shortener in shortener_domains:
        if shortener in url_lower:
            suspicious_indicators.append(f'URL shortener detected: {shortener}')
            risk_score += 5
            break
    
    return {
        'indicators': suspicious_indicators,
        'risk_score': min(risk_score, 100),
        'pattern_check_passed': risk_score < 30
    }


def check_ssl_certificate(domain):
    """Check SSL certificate validity"""
    try:
        # Remove http:// or https://
        domain_clean = domain.replace('http://', '').replace('https://', '').split('/')[0]
        
        context = ssl.create_default_context()
        with socket.create_connection((domain_clean, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain_clean) as ssock:
                cert = ssock.getpeercert()
                
                # Check expiry
                not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_until_expiry = (not_after - datetime.now()).days
                
                return {
                    'has_ssl': True,
                    'valid': True,
                    'issuer': dict(x[0] for x in cert['issuer']),
                    'expires_in_days': days_until_expiry,
                    'subject': dict(x[0] for x in cert['subject'])
                }
    except ssl.SSLError:
        return {'has_ssl': True, 'valid': False, 'error': 'Invalid SSL certificate'}
    except socket.timeout:
        return {'has_ssl': False, 'error': 'Connection timeout'}
    except Exception as e:
        return {'has_ssl': False, 'error': str(e)}


def check_domain_age(domain):
    """Check domain age using WHOIS (basic check)"""
    try:
        import whois
        domain_clean = domain.replace('http://', '').replace('https://', '').split('/')[0]
        w = whois.whois(domain_clean)
        
        if w.creation_date:
            creation_date = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
            age_days = (datetime.now() - creation_date).days
            
            return {
                'age_days': age_days,
                'age_years': age_days / 365,
                'creation_date': str(creation_date),
                'is_new': age_days < 180,  # Less than 6 months
                'registrar': w.registrar
            }
    except Exception as e:
        return {'error': str(e), 'age_days': None}
    
    return {'error': 'Unable to determine', 'age_days': None}


def check_google_safe_browsing(url):
    """
    Check URL against Google Safe Browsing API
    Note: Requires API key. Returns simulated result for demo.
    To use real API: Get key from https://developers.google.com/safe-browsing/v4/get-started
    """
    # For demo purposes, we'll do basic checks
    # In production, uncomment below and add your API key
    
    # API_KEY = "YOUR_GOOGLE_SAFE_BROWSING_API_KEY"
    # api_url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    # payload = {
    #     "client": {"clientId": "prism", "clientVersion": "1.0.0"},
    #     "threatInfo": {
    #         "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
    #         "platformTypes": ["ANY_PLATFORM"],
    #         "threatEntryTypes": ["URL"],
    #         "threatEntries": [{"url": url}]
    #     }
    # }
    # response = requests.post(f"{api_url}?key={API_KEY}", json=payload)
    
    # For now, return a simulated check based on patterns
    pattern_check = check_url_patterns(url)
    
    if pattern_check['risk_score'] > 60:
        return {
            'is_safe': False,
            'threat_type': 'Potentially malicious',
            'confidence': 'MEDIUM'
        }
    elif pattern_check['risk_score'] > 30:
        return {
            'is_safe': False,
            'threat_type': 'Suspicious patterns detected',
            'confidence': 'LOW'
        }
    else:
        return {
            'is_safe': True,
            'threat_type': None,
            'confidence': 'HIGH'
        }


def analyze_url(url):
    """
    Comprehensive URL analysis
    
    Args:
        url: URL to analyze
        
    Returns:
        Dictionary with analysis results
    """
    results = {
        'url': url,
        'risk_score': 0,
        'is_safe': True,
        'warnings': []
    }
    
    # Extract domain info
    domain_info = extract_domain_info(url)
    results['domain_info'] = domain_info
    
    if 'error' in domain_info:
        results['warnings'].append('Invalid URL format')
        results['risk_score'] = 100
        results['is_safe'] = False
        return results
    
    # Check URL patterns
    pattern_check = check_url_patterns(url)
    results['pattern_analysis'] = pattern_check
    results['risk_score'] += pattern_check['risk_score']
    results['warnings'].extend(pattern_check['indicators'])
    
    # Check SSL certificate
    ssl_check = check_ssl_certificate(url)
    results['ssl_check'] = ssl_check
    
    if not ssl_check.get('has_ssl', False):
        results['warnings'].append('No SSL certificate (not using HTTPS)')
        results['risk_score'] += 20
    elif not ssl_check.get('valid', False):
        results['warnings'].append('Invalid or expired SSL certificate')
        results['risk_score'] += 30
    
    # Check domain age
    domain_age = check_domain_age(url)
    results['domain_age'] = domain_age
    
    if domain_age.get('is_new', False):
        results['warnings'].append(f'Domain is very new (less than 6 months old)')
        results['risk_score'] += 25
    
    # Google Safe Browsing check
    safe_browsing = check_google_safe_browsing(url)
    results['safe_browsing'] = safe_browsing
    
    if not safe_browsing['is_safe']:
        results['warnings'].append(f"Threat detected: {safe_browsing['threat_type']}")
        results['risk_score'] += 40
    
    # Final risk assessment
    results['risk_score'] = min(results['risk_score'], 100)
    results['is_safe'] = results['risk_score'] < 40
    results['risk_level'] = 'LOW' if results['risk_score'] < 30 else 'MEDIUM' if results['risk_score'] < 70 else 'HIGH'
    
    return results


# Test function
if __name__ == "__main__":
    test_urls = [
        "https://google.com",
        "http://192.168.1.1/login.php",
        "https://secure-bank-verify-account-now.tk/update",
        "https://bit.ly/3xyz123"
    ]
    
    print("\n🔍 URL Scanner Test\n")
    for url in test_urls:
        print(f"\nAnalyzing: {url}")
        result = analyze_url(url)
        print(f"Risk Score: {result['risk_score']}/100")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Safe: {result['is_safe']}")
        if result['warnings']:
            print(f"Warnings: {', '.join(result['warnings'][:3])}")
        print("-" * 80)
