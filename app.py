import streamlit as st
import google.generativeai as genai
import time
import re
import json
import pandas as pd
import base64
import html
import os
from functools import lru_cache
import logging
import matplotlib.pyplot as plt
import requests  # ADD this
from requests.adapters import HTTPAdapter  # ADD this
from urllib3.util.retry import Retry  # ADD this
from bs4 import BeautifulSoup

# Configure page
st.set_page_config(
    page_title="Sailpeak B2 Compliance Tool",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simple, clean CSS
st.markdown("""
<style>
    /* Clean, minimal styling */
    .stApp {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
        font-weight: 400;
    }
    
    /* Simple header */
    .header {
        padding: 2rem 0 1rem 0;
        border-bottom: 1px solid #e1e5e9;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .header h1 {
        color: #ffffff;
        margin: 0;
        font-weight: 600;
        font-size: 2.2rem;
    }
    
    .header p {
        color: #666;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    
    .header-content {
        flex: 1;
    }
    
    .logo {
        height: 50px;
        width: auto;
    }
    
    .sidebar-logo {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .sidebar-logo img {
        height: 40px;
        width: auto;
    }
    
    /* Simple URL list styling */
    .url-item {
        margin: 0.5rem 0;
        padding: 0.75rem;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        background: white;
        transition: all 0.2s ease;
    }
    
    .url-item:hover {
        background: #f8fafc;
        border-color: #EBD37F;
    }
    
    .url-item.selected {
        background: #EBD37F;
        border-color: #d4c46a;
        font-weight: 600;
    }
    
    .url-score {
        font-weight: 600;
        float: right;
        margin-left: 1rem;
    }
    
    .score-good { color: #059669; }
    .score-warning { color: #f59e0b; }
    .score-danger { color: #dc2626; }
    
    .url-title {
        font-size: 0.9rem;
        color: #1e293b;
        margin-bottom: 0.25rem;
    }
    
    .url-path {
        font-size: 0.75rem;
        color: #64748b;
        font-family: monospace;
    }
    
    /* Current URL display */
    .current-url {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #EBD37F;
    }
    
    .current-url h3 {
        margin: 0 0 0.5rem 0;
        color: #1e293b;
        font-size: 1.1rem;
    }
    
    .current-url .url-text {
        font-family: monospace;
        color: #059669;
        font-size: 0.9rem;
        word-break: break-all;
    }
    
    /* Score display */
    .score {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Simple sentence cards */
    .sentence {
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 3px solid #e5e7eb;
    }
    
    .sentence h4 {
        margin: 0 0 1rem 0;
        color: #ffffff !important;
        font-weight: 600;
    }
    
    .original {
        background: #fef3c7;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
        font-style: italic;
        border-left: 3px solid #f59e0b;
    }
    
    .improved {
        background: #d1fae5;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
        font-weight: 500;
        border-left: 3px solid #059669;
        color: #000000 !important;
    }
    
    /* Chat interface styling */
    .chat-message {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 3px solid #3b82f6;
        background: #f8fafc;
    }

    .chat-user {
        background: #eff6ff;
        border-left-color: #3b82f6;
    }

    .chat-assistant {
        background: #f0fdf4;
        border-left-color: #059669;
    }
            
    .analysis-scores {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
        border-left: 3px solid #EBD37F;
    }
    
    .score-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 1rem;
        margin-top: 0.5rem;
    }
    
    .score-item {
        text-align: center;
    }
    
    .score-label {
        font-size: 0.8rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .score-value {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1a1a1a;
    }
    
    .issues {
        margin: 1rem 0;
    }
    
    .sentence-accepted {
        background: #f0fdf4 !important;
        border-left: 3px solid #059669 !important;
    }
    
    .sentence-accepted h4 {
        color: #065f46 !important;
    }
    
    .issue-badge {
        display: inline-block;
        padding: 0.3rem 0.6rem;
        margin: 0.25rem 0.25rem 0.25rem 0;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        color: white;
    }
    
    .badge-jargon { background: #1f2937; }
    .badge-length { background: #dc2626; }
    .badge-passive { background: #7c3aed; }
    .badge-readability { background: #ea580c; }
    .badge-complexity { background: #374151; }
    .badge-grammar { background: #059669; }
    .badge-technical { background: #1f2937; }
    
    /* Simple buttons */
    .stButton > button {
        background: #EBD37F;
        color: #1a1a1a;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-family: inherit;
    }
    
    .stButton > button:hover {
        background: #d4c46a;
    }
    
    /* Clean info box */
    .info {
        padding: 1rem;
        border-left: 3px solid #EBD37F;
        margin: 1rem 0;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
<script>
function copyToClipboard(text, buttonId) {
    navigator.clipboard.writeText(text).then(function() {
        const button = document.getElementById(buttonId);
        const originalText = button.innerHTML;
        button.innerHTML = '✅ Copied!';
        button.style.background = '#059669';
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = '#EBD37F';
        }, 2000);
    });
}
</script>
""", unsafe_allow_html=True)

# Initialize session state
if 'analyzed_sentences' not in st.session_state:
    st.session_state.analyzed_sentences = []
if 'selected_url_score' not in st.session_state:
    st.session_state.selected_url_score = 0
if 'selected_url_info' not in st.session_state:
    st.session_state.selected_url_info = None
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = os.getenv('GEMINI_API_KEY', '')
if 'crelan_data' not in st.session_state:
    st.session_state.crelan_data = None
if 'current_page_score' not in st.session_state:
    st.session_state.current_page_score = 0
if 'accepted_improvements' not in st.session_state:
    st.session_state.accepted_improvements = set()
if 'estimated_score_gain' not in st.session_state:
    st.session_state.estimated_score_gain = 0
if 'chat_mode' not in st.session_state:
    st.session_state.chat_mode = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_left = image_to_base64("logos/crelan-logo.png")
logo_right = image_to_base64("logos/sailpeak.png")

@st.cache_data
def load_crelan_data():
    """Load Crelan URL data from Excel file"""
    try:
        df = pd.read_excel('data/crelan_b2_final_results.xlsx', sheet_name='Sheet1')
        return df
    except Exception as e:
        st.error(f"Could not load data file: {e}")
        return None

def extract_page_name_from_url(url):
    """Extract a readable page name from URL"""
    try:
        # Remove protocol and domain
        if 'crelan.be' in url:
            path = url.split('crelan.be')[-1]
        else:
            path = url
        
        # Remove leading slash
        if path.startswith('/'):
            path = path[1:]
        
        # Remove file extensions and parameters
        path = re.sub(r'\.(aspx|html).*$', '', path)
        path = path.rstrip('/')
        
        if not path or path == '':
            return "Home"
        
        # Split by slashes and take the last meaningful part
        parts = [p for p in path.split('/') if p]
        if parts:
            # Clean up the last part for display
            name = parts[-1].replace('-', ' ').replace('_', ' ')
            # Capitalize words
            name = ' '.join(word.capitalize() for word in name.split())
            return name
        
        return "Page"
    except:
        return "Unknown Page"

def render_simple_url_dropdown(data, show_all=False):
    """Render a simple dropdown for URL selection"""
    st.subheader("📄 Select a Page")
    
    filtered_data = data[data['Compliance Level'] < 70]
    
    if filtered_data.empty:
        if not show_all:
            st.info("No non-compliant pages found. Enable 'Show all pages' to see compliant pages too.")
        else:
            st.info("No pages found in the dataset.")
        return
    
    st.write(f"Found {len(filtered_data)} pages")
    
    # Sort by compliance score (worst first)
    sorted_data = filtered_data.sort_values('Compliance Level')
    
    # Create options for dropdown
    options = []
    option_data = {}
    
    # Add a default "None selected" option
    options.append("-- Select a page --")
    
    for idx, row in sorted_data.iterrows():
        score = row['Compliance Level']
        url = row['URL']
        page_type = row['Page Type']
        
        # Create clean URL display
        if 'crelan.be' in url:
            url_display = url.split('crelan.be')[-1]
            if not url_display or url_display == '/':
                url_display = '/home'
        else:
            url_display = url
        
        # Determine score icon
        if score >= 70:
            score_icon = "🟢"
        elif score >= 50:
            score_icon = "🟡"
        else:
            score_icon = "🔴"
        
        # Create dropdown option text with URL
        option_text = f"{score_icon} {url_display} ({score}%)"
        options.append(option_text)
        option_data[option_text] = row
    
    # Find current selection index
    current_index = 0
    if st.session_state.selected_url_info is not None:
        current_url = st.session_state.selected_url_info['URL']
        for i, (option_text, row_data) in enumerate(option_data.items(), 1):
            if row_data['URL'] == current_url:
                current_index = i
                break
    
    # Render dropdown
    selected_option = st.selectbox(
        "Choose a page to analyze:",
        options,
        index=current_index,
        key="page_selector"
    )
    
    # Handle selection
    if selected_option != "-- Select a page --" and selected_option in option_data:
        new_selection = option_data[selected_option]
        
        # Check if this is a different selection
        if (st.session_state.selected_url_info is None or 
            st.session_state.selected_url_info['URL'] != new_selection['URL']):
            
            st.session_state.selected_url_info = new_selection
            # Reset analysis when selecting new URL
            st.session_state.analyzed_sentences = []
            st.session_state.accepted_improvements = set()
            st.session_state.estimated_score_gain = 0
            st.rerun()
    elif selected_option == "-- Select a page --":
        if st.session_state.selected_url_info is not None:
            st.session_state.selected_url_info = None
            st.session_state.analyzed_sentences = []
            st.session_state.accepted_improvements = set()
            st.session_state.estimated_score_gain = 0
            st.rerun()

def extract_clean_text(url):
    """Extract text using requests + BeautifulSoup (cloud-friendly)"""
    try:
        # Set up session with retries and proper headers
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Make request with timeout
        st.write(f"Fetching content from: {url}")
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            if tag:
                tag.decompose()
        
        # Try to find main content areas first
        main_content = None
        content_selectors = [
            'main', 
            'article', 
            '[role="main"]',
            '.content', 
            '.main-content',
            '.page-content',
            '#content',
            '#main',
            '.container'
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                st.write(f"Found content using selector: {selector}")
                break
        
        # Extract text from main content or full page
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)
            st.write("Using full page content (no main content area found)")
        
        if text and len(text.strip()) > 100:
            cleaned_text = clean_bank_text(text)
            st.write(f"Extracted {len(cleaned_text)} characters of text")
            return cleaned_text[:15000]
        else:
            st.warning("Not enough text found on the page")
            return ""
            
    except requests.RequestException as e:
        st.error(f"Network error accessing {url}: {str(e)}")
        return ""
    except Exception as e:
        st.error(f"Error extracting text from {url}: {str(e)}")
        return ""

def clean_bank_text(raw_text):
    """Enhanced cleaning for banking website text"""
    if not raw_text or len(raw_text.strip()) < 20:
        return ""
    
    patterns_to_remove = [
        # Language switchers and navigation
        r'FR\s+NL\s+EN',
        r'Nederlands\s+Français\s+English',
        r'Taal\s*:\s*(Nederlands|Français|English)',
        r'Home.*?Contact.*?Login',
        r'Home\s*›\s*.*?›.*?›',
        r'Hoofdmenu\s+Sluiten',
        r'Menu\s+principal\s+Fermer',
        r'Menu\s+Sluiten',
        
        # Banking navigation menus
        r'Particulieren\s+Ondernemingen\s+Private\s+Banking',
        r'Particuliers\s+Entreprises\s+Private\s+Banking',
        r'Sparen\s+Beleggen\s+Lenen\s+Verzekeringen',
        r'Épargner\s+Investir\s+Emprunter\s+Assurances',
        r'Mijn\s+Crelan\s+.*?Online\s+Banking',
        r'Inloggen\s+Registreren',
        r'Se\s+connecter\s+S\'inscrire',
        
        # Cookie and privacy
        r'Cookie.*?Accept.*?Manage',
        r'Accept all cookies.*?Manage cookies',
        r'Deze website gebruikt cookies.*?Alles accepteren',
        r'Ce\s+site\s+web\s+utilise\s+des\s+cookies.*?Tout\s+accepter',
        r'This\s+website\s+uses\s+cookies.*?Accept\s+all',
        r'Cookiebeleid.*?Privacy.*?Algemene\s+voorwaarden',
        r'Politique\s+des\s+cookies.*?Confidentialité',
        
        # Social media and sharing
        r'Share on.*?Facebook',
        r'Tweet.*?Twitter',
        r'Deel\s+op\s+Facebook.*?Twitter.*?LinkedIn',
        r'Partager\s+sur\s+Facebook.*?Twitter',
        r'Volg\s+ons\s+op.*?(?:Facebook|Twitter|Instagram)',
        r'Suivez-nous\s+sur.*?(?:Facebook|Twitter)',
        r'Follow\s+us\s+on.*?(?:Facebook|Twitter)',
        
        # Call-to-action and promotional
        r'Lees meer\s*',
        r'Lire la suite\s*',
        r'Read more\s*',
        r'Meer\s+info\s*(?:rmatie)?\s*(?:aanvragen)?',
        r'Plus\s+d\'(?:info|information)s?\s*',
        r'More\s+info(?:rmation)?\s*',
        r'Aanvragen\s+online',
        r'Demander\s+en\s+ligne',
        r'Apply\s+online',
        r'Klik\s+hier',
        r'Cliquez\s+ici',
        r'Click\s+here',
        r'Bekijk\s+hier',
        r'Voir\s+ici',
        r'View\s+here',
        
        # Legal and footer
        r'©\s*\d{4}.*?Crelan.*?(?:Alle\s+rechten\s+voorbehouden|Tous\s+droits\s+réservés)',
        r'Copyright\s*©?\s*\d{4}.*?(?:Crelan|Bank)',
        r'Alle\s+rechten\s+voorbehouden.*?\d{4}',
        r'Tous\s+droits\s+réservés.*?\d{4}',
        r'Algemene\s+voorwaarden.*?Privacy.*?Cookiebeleid',
        r'Conditions\s+générales.*?Confidentialité.*?Cookies',
        r'Wettelijke\s+informatie.*?Klachten.*?Contact',
        r'Informations\s+légales.*?Réclamations',
        
        # Regulatory and banking codes
        r'FSMA.*?(?:Vergunning|Autorisation).*?\d+',
        r'BNB.*?(?:Toezicht|Supervision)',
        r'Depositogarantie.*?(?:Bescherming|Protection)',
        r'Garantie\s+des\s+dépôts.*?Protection',
        
        # Technical elements
        r'Vul\s+(?:dit|alle)\s+veld(?:en)?\s+in',
        r'Remplissez\s+ce(?:s)?\s+champ(?:s)?',
        r'Fill\s+(?:in\s+)?this\s+field',
        r'Verplicht\s+veld',
        r'Champ\s+obligatoire',
        r'Required\s+field',
        r'Er\s+is\s+een\s+fout\s+opgetreden',
        r'Une\s+erreur\s+s\'est\s+produite',
        r'An\s+error\s+occurred',
        
        # Search and form elements
        r'Zoeken\s+in\s+site',
        r'Rechercher\s+sur\s+le\s+site',
        r'Search\s+site',
    ]
    
    cleaned = raw_text
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove URLs
    cleaned = re.sub(r'https?://[^\s]+', '', cleaned)
    
    # Remove email addresses and phone numbers
    cleaned = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', cleaned)
    cleaned = re.sub(r'\b(?:\+32\s*)?[0-9\s\-\(\)]{8,}\b', '', cleaned)
    
    # Remove reference codes and standalone numbers
    cleaned = re.sub(r'\b[A-Z]{2,4}\d{2,6}\b', '', cleaned)
    cleaned = re.sub(r'\b\d{1,2}\s*(?:\.|:|\))\s*(?=\s|$)', '', cleaned)
    
    # Remove orphaned currency symbols
    cleaned = re.sub(r'[€$£]\s*(?=\s|$)', '', cleaned)
    
    # Clean up whitespace and punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\.{2,}', '.', cleaned)
    cleaned = re.sub(r'\,{2,}', ',', cleaned)
    
    # Remove very short fragments (less than 10 chars or just numbers/symbols)
    sentences = cleaned.split('.')
    meaningful_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if (len(sentence) > 10 and 
            not re.match(r'^[0-9\s\-\(\)\+€$£%.,;:]+$', sentence) and
            len(sentence.split()) >= 3):
            meaningful_sentences.append(sentence)
    
    cleaned = '. '.join(meaningful_sentences)
    
    # Final cleanup
    cleaned = re.sub(r'^\s+|\s+$', '', cleaned)
    if cleaned and not cleaned.endswith('.'):
        cleaned += '.'
    
    return cleaned.strip()

def detect_language_from_url(url):
    """Detect language from URL patterns"""
    url = url.lower()
    if '/nl/' in url or '/nederlands/' in url:
        return 'Dutch (NL)'
    elif '/fr/' in url or '/francais/' in url or '/fr-be/' in url:
        return 'French (FR)'
    elif '/en/' in url or '/english/' in url:
        return 'English (EN)'
    return 'Dutch (NL)'

def get_recommendations_with_gemini(text, url, page_score, page_type, api_key):
    """Get section-by-section recommendations with Sailpeak AI Lab"""
    if not api_key:
        st.error("Please provide your Gemini API key in the sidebar")
        return []
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        language = detect_language_from_url(url).split(' ')[0].lower()  # Extract 'nl', 'fr', or 'en'
        
        prompt = f"""
        **Context:** You are analyzing banking website content for CEFR B2 compliance improvements. The page has been pre-analyzed with a compliance score of {page_score}%. Your task is to identify specific problematic sentences and provide actionable recommendations.
        
        **Page Information:**
        - URL: {url}
        - Page type: {page_type}
        - Language: {language}
        - Current compliance score: {page_score}%
        - Industry: Banking (Crelan)
        - Target: General public including non-native speakers
        
        **CEFR B2 Evaluation Criteria:**
        
        **Vocabulary Complexity (0–10):**
        - 8-10 → Very simple, common words, basic banking terms, no unexplained jargon
        - 6-7 → Mostly common words, occasional technical terms that are explained or contextual
        - 4-5 → Mix of general and technical terms, some unnecessarily complex or rare words
        - 1-3 → Frequent use of complex, low-frequency words or jargon, often unexplained
        - 0 → Highly complex, dense language with rare or unexplained terms everywhere
        
        **Grammatical Structures (0–10):**
        - 8-10 → Simple sentences, clear structure, active voice, no complex clauses
        - 6-7 → Mostly simple, some moderate clauses, minor passive use
        - 4-5 → Mix of simple and complex sentences, occasional embedded or passive forms
        - 1-3 → Mostly long, embedded, or passive structures, hard to follow
        - 0 → Extremely complex grammar, frequent embedding, difficult to parse
        
        **Overall Clarity (0–10):**
        - 8-10 → Very clear, easy to understand, minimal effort required
        - 6-7 → Mostly clear, small moments of complexity
        - 4-5 → Mixed clarity, occasional confusion or ambiguity
        - 1-3 → Often unclear, requires effort to interpret
        - 0 → Very unclear, confusing, hard to follow
        
        **Coherence (0–10):**
        - 8-10 → Logical flow, clear organization, excellent connectors
        - 6-7 → Mostly logical, some jumps, minor missing links
        - 4-5 → Mixed coherence, weak transitions, partial disorganization
        - 1-3 → Often disorganized, unclear connections
        - 0 → No logical order, chaotic, fragmented
        
        **Compliance Threshold:** 70% (7/10) is the minimum for B2 compliance.
        
        **TEXT TO ANALYZE:**
        {text}
        
        **Task:** Identify sentences that are likely contributing to the score being below 70% and provide specific recommendations.
        
        For each problematic sentence, analyze:
        1. **Vocabulary issues** - banking jargon, complex terms, rare words
        2. **Grammar issues** - passive voice, complex clauses, sentence length
        3. **Clarity issues** - ambiguity, unclear references, confusing structure
        4. **Coherence issues** - poor transitions, illogical flow
        
        **Output Format:** Return a JSON array with this structure:
        [
            {{
                "sentence": "exact problematic sentence text",
                "issue_score": 45,
                "issues": ["Banking Jargon", "Sentence Length", "Passive Voice"],
                "vocabulary_score": 4,
                "grammar_score": 3,
                "clarity_score": 5,
                "coherence_score": 5,
                "recommendations": [
                    "Replace 'hypothecair krediet' with 'woonlening' or add simple explanation",
                    "Break this 35-word sentence into 2 shorter sentences",
                    "Change passive 'wordt berekend' to active 'wij berekenen'"
                ],
                "rewrite": "simplified version that maintains banking accuracy and achieves B2 compliance",
                "explanation": "This sentence scores low because it combines complex banking terminology ('hypothecair krediet', 'looptijd') with passive voice construction and exceeds 25 words, making it difficult for B2-level readers."
            }}
        ]
        
        **Important Guidelines:**
        - Only analyze sentences that actually need improvement (estimated score < 7/10 or 70%)
        - Focus on sentences most likely dragging down the overall page score
        - Provide specific, actionable recommendations
        - Maintain banking accuracy while simplifying language
        - Consider that some banking terms may be necessary but should be explained or simplified
        - Ensure rewrites achieve B2 compliance (≥70%) while preserving meaning
        """
        
        response = model.generate_content(prompt)
        
        # Parse JSON response
        try:
            # Clean the response to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            analyzed_sentences = json.loads(response_text)
            return analyzed_sentences
            
        except json.JSONDecodeError as e:
            st.error(f"Error parsing Gemini response: {e}")
            return []
            
    except Exception as e:
        st.error(f"Error with Gemini API: {str(e)}")
        return []

def calculate_score_improvement(sentence_data, current_score, total_sentences):
    """Calculate estimated score improvement from fixing a sentence"""
    issue_score = sentence_data.get('issue_score', 0)
    
    # Calculate what's needed to reach 70%
    target_score = 70
    gap_to_target = max(0, target_score - current_score)
    
    # Weight each sentence based on how problematic it is
    severity_factor = (70 - issue_score) / 70 if issue_score < 70 else 0.1
    
    # Distribute the gap across problematic sentences
    # Ensure that fixing all sentences will reach at least 70%
    base_improvement = gap_to_target / total_sentences
    weighted_improvement = base_improvement * (1 + severity_factor)
    
    # Add some buffer to ensure we exceed 70%
    final_improvement = weighted_improvement * 1.2
    
    return max(1, min(final_improvement, 25))  # Min 1%, max 25% per sentence

def render_sentence_recommendations(sentences):
   """Render section-by-section recommendations with score tracking"""
   if not sentences:
       st.info("No problematic sections identified yet. Click 'Get Recommendations' to analyze the page content.")
       return
   
   st.markdown("---")
   st.markdown("## Section-by-Section Recommendations")
   
   pending_count = len([s for i, s in enumerate(sentences, 1) if i not in st.session_state.accepted_improvements])
   accepted_count = len(st.session_state.accepted_improvements)
   
   st.write(f"**Progress:** {accepted_count} accepted, {pending_count} pending ({len(sentences)} total)")

   st.markdown("---")
   
   for i, sentence_data in enumerate(sentences, 1):
       score = sentence_data.get('issue_score', 0)
       issues = sentence_data.get('issues', [])
       is_accepted = i in st.session_state.accepted_improvements
       
       # Determine card style based on score and acceptance status
       if is_accepted:
           card_class = "sentence-accepted"
           border_color = "#059669"
       elif score >= 60:
           card_class = "sentence-warning"
           border_color = "#f59e0b"
       else:
           card_class = "sentence-critical"
           border_color = "#dc2626"
       
       # Calculate potential improvement for this sentence
       potential_improvement = calculate_score_improvement(sentence_data, st.session_state.selected_url_info['Compliance Level'], len(sentences))
       
       # Issue header at the top
       st.markdown(f"<h3 style='font-size: 1.5rem; font-weight: 700; color: #1e293b; margin: 1.5rem 0 0.5rem 0; border-bottom: 2px solid #EBD37F; padding-bottom: 0.3rem; display: inline-block;'>Issue #{i}</h3>", unsafe_allow_html=True)
       st.markdown(f"<p style='font-size: 1.1rem; font-weight: 600; color: #059669; margin: 0.5rem 0 1rem 0;'>Potential Improvement: <strong>+{potential_improvement:.1f}%</strong></p>", unsafe_allow_html=True)
       
       st.markdown(f"""
           <div style="background: #fef3c7; padding: 1rem; border-radius: 4px; border-left: 3px solid #f59e0b; margin: 1rem 0; {'opacity: 0.7;' if is_accepted else ''}">
               <strong style="color: #000000;">Original section:</strong><br>
               <span style="color: #000000; font-style: italic;">"{sentence_data.get('sentence', '')}"</span>
           </div>
       """, unsafe_allow_html=True)
       
       # Smart issue badge mapping (only show if not accepted)
       if issues and not is_accepted:
           issue_badges = ""
           for issue in issues:
               issue_clean = issue.lower().replace(' ', '').replace('banking', '').replace('complex', 'complexity')
               if 'jargon' in issue_clean or 'technical' in issue_clean:
                   badge_class = "badge-jargon"
               elif 'length' in issue_clean or 'long' in issue_clean:
                   badge_class = "badge-length"
               elif 'passive' in issue_clean:
                   badge_class = "badge-passive"
               elif 'readability' in issue_clean or 'clarity' in issue_clean:
                   badge_class = "badge-readability"
               elif 'grammar' in issue_clean:
                   badge_class = "badge-grammar"
               else:
                   badge_class = "badge-complexity"
               
               issue_badges += f'<span class="issue-badge {badge_class}">{issue}</span>'
           
           st.markdown(f"""
           <div class="issues">
               <strong>Issues Detected:</strong><br>
               {issue_badges}
           </div>
           """, unsafe_allow_html=True)
       
       if not is_accepted:
           # Show explanation
           explanation = sentence_data.get('explanation', '')
           if explanation:
               st.markdown(f"**Why this is problematic:** {explanation}")
           
           # Show recommendations
           recommendations = sentence_data.get('recommendations', [])
           if recommendations:
               st.markdown("**Specific Recommendations:**")
               for rec in recommendations:
                   st.markdown(f"• {rec}")
       
       # Show rewrite 
       rewrite = sentence_data.get('rewrite', '')
       if rewrite and rewrite != sentence_data.get('sentence', ''):
            if is_accepted:
                # Show accepted version with go back option
                st.markdown(f"""
                <div style="background: #f0fdf4; padding: 1rem; border-radius: 4px; margin: 1rem 0; border-left: 3px solid #059669;">
                    <strong>✅ Accepted Version:</strong>
                </div>
                """, unsafe_allow_html=True)
                
                # Use Streamlit's code block with built-in copy button
                st.code(rewrite, language=None)
                
                # Single go back button
                if st.button(f"↩️ Go Back", key=f"undo_{i}"):
                    st.session_state.accepted_improvements.discard(i)
                    st.session_state.estimated_score_gain -= potential_improvement
                    st.session_state.estimated_score_gain = max(0, st.session_state.estimated_score_gain)
                    st.warning(f"❌ Improvement undone. Score decreased by -{potential_improvement:.1f}%")
                    st.rerun()
            
            else:
                # Not accepted - show normal improved version
                st.markdown(f"""
                <div class="improved">
                    <strong>Improved Version:</strong>
                </div>
                """, unsafe_allow_html=True)
                
                # Use Streamlit's code block with built-in copy button
                st.code(rewrite, language=None)
                
                # Action buttons side by side
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"Accept (+{potential_improvement:.1f}%)", key=f"accept_{i}"):
                        st.session_state.accepted_improvements.add(i)
                        st.session_state.estimated_score_gain += potential_improvement
                        st.success(f"✅ Improvement accepted! Score increased by +{potential_improvement:.1f}%")
                        st.rerun()
                
                with col2:
                    if st.button(f"Edit/Regenerate", key=f"edit_{i}"):
                        chat_key = f"chat_mode_{i}"
                        if chat_key not in st.session_state.chat_mode:
                            st.session_state.chat_mode[chat_key] = False
                        st.session_state.chat_mode[chat_key] = not st.session_state.chat_mode[chat_key]
                        st.rerun()

                with col3:
                    # Empty column to maintain layout
                    pass

                # Chat interface for editing
                chat_key = f"chat_mode_{i}"
                if chat_key in st.session_state.chat_mode and st.session_state.chat_mode[chat_key]:
                    st.markdown("---")
                    st.markdown("### Edit this recommendation")
                    
                    # Display current sentence info
                    st.markdown(f"""
                    <div style="background: #f3f4f6; padding: 0.75rem; border-radius: 4px; margin: 0.5rem 0;">
                        <strong>Original:</strong> {sentence_data.get('sentence', '')}
                    </div>
                    <div style="background: #ecfdf5; padding: 0.75rem; border-radius: 4px; margin: 0.5rem 0;">
                        <strong>Current improved version:</strong> {rewrite}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Chat input
                    user_input = st.text_input(
                        "How would you like to improve this sentence?",
                        placeholder="e.g., 'Make it shorter', 'Replace technical terms', 'Use simpler words'",
                        key=f"chat_input_{i}"
                    )
                    
                    col_send, col_close = st.columns([1, 3])
                    
                    with col_send:
                        if st.button("Send", key=f"send_{i}") and user_input:
                            with st.spinner("Getting suggestion..."):
                                response = handle_sentence_edit_chat(
                                    i, 
                                    sentence_data.get('sentence', ''),
                                    rewrite,
                                    user_input,
                                    st.session_state.gemini_api_key
                                )
                                st.markdown(f"**Assistant:** {response}")
                                
                                # Check if response contains a new sentence version
                                if '"' in response and len(response) > 50:
                                    st.success("💡 The assistant provided a new version. You can copy it manually or ask for more changes.")
                    
                    with col_close:
                        if st.button("Close Editor", key=f"close_edit_{i}"):
                            st.session_state.chat_mode[chat_key] = False
                            st.rerun()
                    
                    st.markdown("---")

       # Add separator after each issue
       st.markdown("---")

def handle_sentence_edit_chat(sentence_index, original_sentence, current_rewrite, user_input, api_key):
    """Handle chat interaction for sentence editing"""
    if not api_key:
        return "Please provide your Gemini API key."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Simplified prompt for sentence-only output
        prompt = f"""
        **TASK:** Edit this sentence for CEFR B2 compliance based on the user's request. Return ONLY the improved sentence, nothing else.
        
        **ORIGINAL:** {original_sentence}
        **CURRENT VERSION:** {current_rewrite}
        **USER REQUEST:** {user_input}
        
        **RULES:**
        - Return ONLY the improved sentence
        - No explanations, no extra text
        - Maintain banking accuracy and meaning
        - Make it CEFR B2 compliant (simple, clear language)
        - If the request is not about sentence editing, respond: "I can only help edit this sentence."
        
        **IMPROVED SENTENCE:**
        """
        
        response = model.generate_content(prompt)
        
        # Clean the response to get just the sentence
        improved_sentence = response.text.strip()
        
        # Remove quotes if Gemini added them
        if improved_sentence.startswith('"') and improved_sentence.endswith('"'):
            improved_sentence = improved_sentence[1:-1]
        
        return improved_sentence
        
    except Exception as e:
        return f"Error: {str(e)}"
   
def main():
    # Load Crelan data
    if st.session_state.crelan_data is None:
        st.session_state.crelan_data = load_crelan_data()
    
    if st.session_state.crelan_data is None:
        st.error("Could not load Crelan data. Please ensure the Excel file is available.")
        return
    
    # Header with proper markdown rendering
    st.markdown(f"""
    <div style="background: #FFFFFF; padding: 1rem 1.5rem; border-radius: 16px; margin-bottom: 2rem; display: flex; align-items: center; justify-content: space-between;">
        <div style="padding: 0.75rem; border-radius: 12px; text-align: center;">
            <img src="data:image/png;base64,{logo_left}" width="120"/>
        </div>
        <div style="text-align: center; flex-grow: 1; padding: 0 2rem;">
            <h1 style="color: #212529; margin: 0; font-weight: 700; font-size: 2.2rem;">CEFR B2 Compliance Tool</h1>
        </div>
        <div style="padding: 0.75rem; border-radius: 12px; text-align: center;">
        </div>
    </div>
    """, unsafe_allow_html=True)
        
    # Sidebar for configuration
    with st.sidebar:
        try:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image("logos/sailpeak.png", width=150)
        except:
            st.markdown("**Sailpeak**")

        # Simple dropdown navigation (always show only non-compliant pages)
        render_simple_url_dropdown(st.session_state.crelan_data, show_all=False)
        
        # Show selected page info
        if st.session_state.selected_url_info is not None:
            st.subheader("Selected Page")
            score = st.session_state.selected_url_info['Compliance Level']
            page_type = st.session_state.selected_url_info['Page Type']
            
            # Score styling
            if score >= 70:
                score_class = "score-good"
                status = "✅ Compliant"
            elif score >= 50:
                score_class = "score-warning"
                status = "⚠️ Needs Improvement"
            else:
                score_class = "score-danger"
                status = "❌ Non-Compliant"
            
            st.markdown(f"""
            <div class="score {score_class}">
                {score}%<br>
                <small>{status}</small>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="info">
                <strong>Page Type:</strong> {page_type}
            </div>
            """, unsafe_allow_html=True)
            
            # Get recommendations button
            get_recommendations_btn = st.button("🔍 Get Recommendations", type="primary")
        else:
            st.info("👆 Select a page from the list above to get started")
            get_recommendations_btn = False
    
    # Main content area
    if st.session_state.selected_url_info is not None:
        # Show current URL being analyzed
        current_url = st.session_state.selected_url_info['URL']
        page_name = extract_page_name_from_url(current_url)
        
        st.markdown(f"""
        <div class="current-url">
            <h3>📄 Currently Analyzing:</h3>
            <div class="url-text">{current_url}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show current page summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            score = st.session_state.selected_url_info['Compliance Level']
            st.metric("Current Score", f"{score}%", delta=None)
        
        with col2:
            estimated_new_score = min(100, score + st.session_state.estimated_score_gain)
            st.metric("Estimated New Score", f"{estimated_new_score:.1f}%", 
                     delta=f"+{st.session_state.estimated_score_gain:.1f}%" if st.session_state.estimated_score_gain > 0 else None)
        
        with col3:
            compliance_status = "✅ Compliant" if estimated_new_score >= 70 else "❌ Non-Compliant"
            st.metric("Compliance Status", compliance_status)
        
        # Analysis results
        if get_recommendations_btn:
            if not st.session_state.gemini_api_key:
                st.error("Please provide your Gemini API key in the sidebar")
            else:
                selected_url = st.session_state.selected_url_info['URL']
                page_score = st.session_state.selected_url_info['Compliance Level']
                page_type = st.session_state.selected_url_info['Page Type']
                
                with st.spinner("Extracting content and analyzing with Sailpeak AI..."):
                    # Extract text from website
                    progress_bar = st.progress(0)
                    st.write("Extracting website content...")
                    progress_bar.progress(25)
                    
                    extracted_text = extract_clean_text(selected_url)
                    
                    if not extracted_text:
                        st.error("Could not extract text from the website. Please check the URL.")
                    else:
                        progress_bar.progress(50)
                        st.write("Getting sentence-by-sentence recommendations...")
                        
                        # Get recommendations with Gemini
                        recommendations = get_recommendations_with_gemini(
                            extracted_text, 
                            selected_url,
                            page_score,
                            page_type,
                            st.session_state.gemini_api_key
                        )
                        
                        progress_bar.progress(100)
                        
                        if recommendations:
                            st.session_state.analyzed_sentences = recommendations
                            # Reset improvements when new analysis is done
                            st.session_state.accepted_improvements = set()
                            st.session_state.estimated_score_gain = 0
                            st.success("Analysis complete!")
                        else:
                            st.warning("No specific problematic sentences found. The page might already be close to compliance!")
        
        # Render recommendations
        render_sentence_recommendations(st.session_state.analyzed_sentences)
    
    else:
        # Welcome screen when no page is selected
        st.markdown("""
        ## Welcome to the CEFR B2 Compliance Tool
        
        This tool helps you improve banking website content to meet CEFR B2 accessibility standards under the European Accessibility Act.
        
        ### How to get started:
        1. **Navigate** through the page list in the sidebar
        2. **Select** a page by clicking on it (pages show compliance scores with 🔴🟡🟢 indicators)
        3. **Analyze** the page content with AI-powered recommendations
        4. **Accept** improvements to boost compliance scores
        
        ### Features:
        - 🎯 **Section-level analysis** for precise improvements
        - 📊 **Real-time score tracking** with estimated improvements
        - 🌐 **Multi-language support** (Dutch, French, English)
        - 🏦 **Banking-specific** terminology and context awareness
        """)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>Sailpeak B2 Compliance Tool for Crelan</strong> - Powered by Sailpeak AI Lab</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
