"""
PRISM - Privacy-First Multilingual AI System
Streamlit Web Application for Real-Time Scam Detection
"""

import streamlit as st
import sys
import os
import plotly.graph_objects as go
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.inference import PrismInference


# Page configuration
st.set_page_config(
    page_title="PRISM - AI Scam Detector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide sidebar
)


# Custom CSS for beautiful UI
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Better solid background */
    .stApp {
        background: #5b68db;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Better header with shadow */
    .main-header {
        background: rgba(255, 255, 255, 0.2);
        padding: 2.5rem 2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .main-header h1 {
        color: white;
        font-size: 3.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.01em;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.95);
        font-size: 1.15rem;
        margin-top: 0.75rem;
        font-weight: 400;
    }
    
    /* Card styling with glassmorphism */
    .card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 1.5rem;
    }
    
    /* Better text area */
    .stTextArea textarea {
        border-radius: 10px !important;
        border: 2px solid rgba(255, 255, 255, 0.4) !important;
        background: rgba(255, 255, 255, 0.25) !important;
        color: white !important;
        font-size: 1rem !important;
        padding: 1.2rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stTextArea textarea::placeholder {
        color: rgba(255, 255, 255, 0.65) !important;
    }
    
    .stTextArea textarea:focus {
        border-color: rgba(255, 255, 255, 0.7) !important;
        background: rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* Label styling */
    .stTextArea label {
        color: white !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }
    
    /* Risk indicator */
    .risk-safe {
        color: #10b981;
        font-weight: 700;
        font-size: 2rem;
    }
    
    .risk-suspicious {
        color: #f59e0b;
        font-weight: 700;
        font-size: 2rem;
    }
    
    .risk-scam {
        color: #ef4444;
        font-weight: 700;
        font-size: 2rem;
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        margin: 0.25rem;
        font-size: 0.9rem;
    }
    
    .badge-keyword {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    
    .badge-indicator {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Privacy notice */
    .privacy-notice {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 2rem;
        text-align: center;
        font-weight: 600;
    }
    
    /* Sidebar styling - completely hidden */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Make main content full width */
    .main .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* Better button */
    .stButton>button {
        background: #4c51ce !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.85rem 2.5rem !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    .stButton>button:hover {
        background: #3d42b5 !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    
    .stButton>button:active {
        transform: translateY(-1px) !important;
    }
    
    .stButton>button:active {
        transform: translateY(-1px) !important;
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: white !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model():
    """Load the PRISM model (cached)"""
    try:
        model = PrismInference()
        return model
    except Exception as e:
        st.error(f"❌ Error loading model: {e}")
        st.info("ℹ️ Please train the model first using: `python src/train_model.py`")
        return None


def create_risk_gauge(risk_score):
    """Create an animated risk gauge using Plotly"""
    
    # Determine color based on risk
    if risk_score >= 70:
        color = "#ef4444"
    elif risk_score >= 40:
        color = "#f59e0b"
    else:
        color = "#10b981"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = risk_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Risk Score", 'font': {'size': 24, 'color': '#1f2937'}},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#1f2937"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e5e7eb",
            'steps': [
                {'range': [0, 40], 'color': '#d1fae5'},
                {'range': [40, 70], 'color': '#fef3c7'},
                {'range': [70, 100], 'color': '#fee2e2'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter'}
    )
    
    return fig


def main():
    """Main application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🛡️ PRISM</h1>
        <p>Privacy-First Multilingual AI System for Real-Time Scam Detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar removed - info moved to bottom
    
    # Load model
    model = load_model()
    
    if model is None:
        st.warning("⚠️ Model not loaded. Please train the model first.")
        st.code("python src/prepare_dataset.py")
        st.code("python src/train_model.py")
        return
    
    # Main content with centered, smaller text box
    # Center the text area with max-width
    col_left, col_center, col_right = st.columns([1, 3, 1])
    
    with col_center:
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0 1rem 0;">
            <h2 style="color: white; font-size: 2rem; font-weight: 600; margin: 0;">
                📝 Enter Message to Analyze
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Text input - smaller and centered
        user_message = st.text_area(
            "Paste your SMS, email, or WhatsApp message here:",
            height=120,
            placeholder="Example: URGENT! Your bank account will be suspended. Click here to verify immediately.",
            label_visibility="collapsed"
        )
    
        # Analyze button
        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Analyze Message", use_container_width=True)
    
    # Analysis results
    if analyze_button and user_message.strip():
        with st.spinner("🔄 Analyzing message..."):
            # Get prediction
            result = model.predict(user_message)
            explanation = model.get_explanation(result)
        
        # Display results
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")
        
        # Risk level and score
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Risk level with colored styling - no box
            risk_class = f"risk-{result['prediction'].lower()}"
            st.markdown(f'<p class="{risk_class}">🎯 {result["prediction"].upper()}</p>', unsafe_allow_html=True)
            
            st.markdown(f"<p style='color: white; font-size: 1.1rem; margin-top: 1rem;'><strong>Detected Language:</strong> {result['language']}</p>", unsafe_allow_html=True)
            
            # Confidence scores
            st.markdown("<p style='color: white; font-weight: 600; margin-top: 1.5rem;'>Confidence Scores:</p>", unsafe_allow_html=True)
            st.progress(result['confidence']['scam'] / 100)
            st.markdown(f"<p style='color: white;'>Scam: <strong>{result['confidence']['scam']}%</strong></p>", unsafe_allow_html=True)
            
            st.progress(result['confidence']['safe'] / 100)
            st.markdown(f"<p style='color: white;'>Safe: <strong>{result['confidence']['safe']}%</strong></p>", unsafe_allow_html=True)
        
        with col2:
            # Risk gauge
            st.plotly_chart(create_risk_gauge(result['risk_score']), use_container_width=True)
        
        # Message Statistics - NEW FEATURE
        st.markdown("<h3 style='color: white; font-size: 1.6rem; margin-top: 2rem;'>📊 Message Statistics</h3>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            char_count = len(user_message)
            st.metric("Characters", f"{char_count}")
        
        with col2:
            word_count = len(user_message.split())
            st.metric("Words", f"{word_count}")
        
        with col3:
            url_count = len(result['urls_found'])
            st.metric("URLs Found", f"{url_count}")
        
        with col4:
            phone_count = len(result['phone_numbers_found'])
            st.metric("Phone Numbers", f"{phone_count}")
        
        # Explanation - no box
        st.markdown("<h3 style='color: white; font-size: 1.6rem; margin-top: 2rem;'>💡 Explanation</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: rgba(255, 255, 255, 0.95); line-height: 1.7; font-size: 1.05rem;'>{explanation}</p>", unsafe_allow_html=True)
        
        # Detailed indicators - no box
        if result['suspicious_keywords'] or result['urls_found'] or result['phone_numbers_found']:
            st.markdown("<h3 style='color: white; font-size: 1.6rem; margin-top: 2rem;'>🔍 Detected Indicators</h3>", unsafe_allow_html=True)
            
            # Suspicious keywords
            if result['suspicious_keywords']:
                st.markdown("<p style='color: white; font-weight: 600; margin-top: 1rem;'>Suspicious Keywords:</p>", unsafe_allow_html=True)
                keywords_html = " ".join([f'<span class="badge badge-keyword">{kw}</span>' 
                                         for kw in result['suspicious_keywords'][:10]])
                st.markdown(keywords_html, unsafe_allow_html=True)
            
            # URLs
            if result['urls_found']:
                st.markdown("**Suspicious Links:**")
                for url in result['urls_found']:
                    st.markdown(f"- `{url}`")
            
            # Phone numbers
            if result['phone_numbers_found']:
                st.markdown("**Phone Numbers:**")
                for phone in result['phone_numbers_found']:
                    st.markdown(f"- `{phone}`")
            
        
        # Risk indicators summary - no box
        st.markdown("<h3 style='color: white; font-size: 1.6rem; margin-top: 2rem;'>📈 Risk Indicators Summary</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        indicators = result['indicators']
        
        with col1:
            st.metric("Urgency Tactics", "Yes" if indicators['has_urgency'] else "No")
            st.metric("Financial Terms", "Yes" if indicators['has_financial_terms'] else "No")
        
        with col2:
            st.metric("Action Required", "Yes" if indicators['has_action_required'] else "No")
            st.metric("Threats", "Yes" if indicators['has_threats'] else "No")
        
        with col3:
            st.metric("Personal Info Request", "Yes" if indicators['requests_personal_info'] else "No")
            st.metric("Contains Links", "Yes" if indicators['contains_urls'] else "No")
        
    
    elif analyze_button:
        st.warning("⚠️ Please enter a message to analyze.")
    
    # Privacy notice at bottom
    st.markdown("""
    <div class="privacy-notice">
        🔒 Your privacy is protected: Messages are analyzed in real-time and never stored or logged.
    </div>
    """, unsafe_allow_html=True)
    
    # Information section at bottom - with dividers
    st.markdown("<div style='margin: 4rem 0 2rem 0;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; border-right: 2px solid rgba(255, 255, 255, 0.3);">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">ℹ️</div>
            <h3 style="color: white; font-size: 1.3rem; margin-bottom: 1rem; font-weight: 600;">About PRISM</h3>
            <p style="color: rgba(255, 255, 255, 0.85); line-height: 1.6; font-size: 0.95rem;">
                Advanced AI for real-time scam detection
            </p>
            <div style="margin-top: 1rem; text-align: left;">
                <p style="color: rgba(255, 255, 255, 0.9); font-size: 0.9rem; line-height: 1.8;">
                    🌐 22+ Indian Languages<br>
                    🔒 100% Private<br>
                    ⚡ Instant Detection<br>
                    🎯 AI Explained
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; border-right: 2px solid rgba(255, 255, 255, 0.3);">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">📊</div>
            <h3 style="color: white; font-size: 1.3rem; margin-bottom: 1rem; font-weight: 600;">Model Info</h3>
            <p style="color: rgba(255, 255, 255, 0.9); font-size: 0.95rem; line-height: 1.8;">
                <strong>DistilBERT</strong> Multilingual<br>
                Hindi • Tamil • Telugu • Bengali<br>
                Marathi • Gujarati • Kannada + more<br>
                <strong style="font-size: 1.3rem; color: #10b981;">95%+</strong> Accuracy
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🔐</div>
            <h3 style="color: white; font-size: 1.3rem; margin-bottom: 1rem; font-weight: 600;">Privacy First</h3>
            <p style="color: rgba(255, 255, 255, 0.9); font-size: 0.9rem; line-height: 1.8;">
                ✅ In-Memory Only<br>
                ✅ Zero Storage<br>
                ✅ No Logging<br>
                ✅ Fully Secure
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Add spacer to push text to bottom
    st.markdown("<div style='margin-top: 10rem;'></div>", unsafe_allow_html=True)
    
    # Simple text at very bottom
    st.markdown("""
    <div style='text-align: center; color: white; padding-bottom: 2rem;'>
        <p style='font-size: 0.95rem; opacity: 0.85; margin-bottom: 0.3rem;'>
            Built with ❤️ for AI + Cybersecurity & Privacy Hackathon
        </p>
        <p style='font-size: 0.85rem; opacity: 0.7;'>
            Power by <strong>DistilBERT Multilingual</strong> • <strong>HuggingFace Transformers</strong> • <strong>Streamlit</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
