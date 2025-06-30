import streamlit as st
import google.generativeai as genai
import time
import re
import json
import pandas as pd
import base64
import html
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
    
    /* Score display */
    .score {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .score-good { color: #059669; }
    .score-warning { color: #d97706; }
    .score-danger { color: #dc2626; }
    
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
""", unsafe_allow_html=True)

# Initialize session state
if 'analyzed_sentences' not in st.session_state:
    st.session_state.analyzed_sentences = []
if 'selected_url_score' not in st.session_state:
    st.session_state.selected_url_score = 0
if 'selected_url_info' not in st.session_state:
    st.session_state.selected_url_info = None
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
if 'belfius_data' not in st.session_state:
    st.session_state.belfius_data = None
if 'current_page_score' not in st.session_state:
    st.session_state.current_page_score = 0
if 'accepted_improvements' not in st.session_state:
    st.session_state.accepted_improvements = set()
if 'estimated_score_gain' not in st.session_state:
    st.session_state.estimated_score_gain = 0

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_left = image_to_base64("logos/belfius-logo.png")
logo_right = image_to_base64("logos/sailpeak.png")

@st.cache_data
def load_belfius_data():
    """Load Belfius URL data from Excel file"""
    try:
        df = pd.read_excel('data/belfius_b2_accessibility_final.xlsx', sheet_name='Sheet1')
        return df
    except Exception as e:
        st.error(f"Could not load data file: {e}")
        return None

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
    """Clean banking website text"""
    if not raw_text or len(raw_text.strip()) < 20:
        return ""
    
    patterns_to_remove = [
        r'FR\s+NL\s+EN',
        r'Nederlands\s+Français\s+English',
        r'Home.*?Contact.*?Login',
        r'Menu\s+Sluiten',
        r'Cookie.*?Accept.*?Manage',
        r'Accept all cookies.*?Manage cookies',
        r'Deze website gebruikt cookies.*?Alles accepteren',
        r'Share on.*?Facebook',
        r'Tweet.*?Twitter',
        r'Home\s*›.*?›',
        r'Lees meer\s*',
        r'Lire la suite\s*',
        r'Read more\s*',
    ]
    
    cleaned = raw_text
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\.{2,}', '.', cleaned)
    
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

def extract_url_hierarchy(url):
    """Extract clean URL path for display"""
    try:
        path = url.split('belfius.be')[-1]
        if path.startswith('/'):
            path = path[1:]
        
        path = path.replace('.aspx', '').replace('.html', '')
        path = path.replace('/index', '')
        
        if path.endswith('/'):
            path = path[:-1]
            
        return path if path else 'home'
    except:
        return url

def create_hierarchical_filter(data):
    """Create hierarchical filters for language -> page type -> URL"""
    data['Language'] = data['URL'].apply(detect_language_from_url)
    data['URL_Path'] = data['URL'].apply(extract_url_hierarchy)
    return data

def get_recommendations_with_gemini(text, url, page_score, page_type, api_key):
    """Get sentence-by-sentence recommendations using Gemini API"""
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
        - Industry: Banking (Belfius)
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

def render_url_info(url_info):
    """Render URL information from the database"""
    if url_info is None or url_info.empty:
        return
    
    score = url_info['Compliance Level']
    page_type = url_info['Page Type']
    
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

def calculate_score_improvement(sentence_data, current_score):
    """Calculate estimated score improvement from fixing a sentence"""
    issue_score = sentence_data.get('issue_score', 0)
    
    # Simple heuristic: improvement proportional to how bad the sentence was
    # and how much of the page it represents (assuming ~10-20 sentences per page)
    sentence_weight = 1 / 15  # Assume 15 sentences average per page
    current_gap = 100 - current_score
    improvement_factor = (70 - issue_score) / 70  # How much improvement this sentence needs
    
    # Estimated improvement: sentence weight * improvement factor * remaining gap
    estimated_improvement = sentence_weight * improvement_factor * current_gap * 0.3
    
    return max(0, min(estimated_improvement, 15))  # Cap at 15% improvement per sentence

def render_sentence_recommendations(sentences):
    """Render sentence-by-sentence recommendations with score tracking"""
    if not sentences:
        st.info("No problematic sentences identified yet. Click 'Get Recommendations' to analyze the page content.")
        return
    
    st.markdown("---")
    st.subheader("Sentence-by-Sentence Recommendations")
    
    pending_count = len([s for i, s in enumerate(sentences, 1) if i not in st.session_state.accepted_improvements])
    accepted_count = len(st.session_state.accepted_improvements)
    
    st.write(f"**Progress:** {accepted_count} accepted, {pending_count} pending ({len(sentences)} total)")
    
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
        potential_improvement = calculate_score_improvement(sentence_data, st.session_state.selected_url_info['Compliance Level'])
        
        accepted_badge = '✅ ACCEPTED' if is_accepted else ''
        
        # Issue header at the top
        st.markdown(f"**Issue #{i} - Score: {score}%**")
        st.markdown(f"Potential Improvement: **+{potential_improvement:.1f}%**")
        
        st.markdown(f"""
            <div style="background: #fef3c7; padding: 1rem; border-radius: 4px; border-left: 3px solid #f59e0b; margin: 1rem 0; {'opacity: 0.7;' if is_accepted else ''}">
                <strong style="color: #000000;">Original sentence:</strong><br>
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
            improved_title = "✅ Accepted Version:" if is_accepted else "Improved Version:"
            st.markdown(f"""
            <div class="improved">
                <strong>{improved_title}</strong><br>
                "{rewrite}"
            </div>
            """, unsafe_allow_html=True)
            
            if not is_accepted:
                # Action buttons (no columns, just regular buttons)
                if st.button(f"Accept Improvement (+{potential_improvement:.1f}%)", key=f"accept_{i}"):
                    st.session_state.accepted_improvements.add(i)
                    st.session_state.estimated_score_gain += potential_improvement
                    st.success(f"✅ Improvement accepted! Score increased by +{potential_improvement:.1f}%")
                    st.rerun()
                
                if st.button(f"Edit Recommendation", key=f"edit_{i}"):
                    st.info("Opening content editor...")
                    
                if st.button(f"Regenerate Recommendation", key=f"regen_{i}"):
                    st.info("Generating new recommendations...")
            else:
                # Show undo option for accepted recommendations
                if st.button(f"Undo Acceptance", key=f"undo_{i}"):
                    st.session_state.accepted_improvements.discard(i)
                    st.session_state.estimated_score_gain -= potential_improvement
                    st.session_state.estimated_score_gain = max(0, st.session_state.estimated_score_gain)
                    st.warning(f"❌ Improvement undone. Score decreased by -{potential_improvement:.1f}%")
                    st.rerun()
                    
                st.markdown(f"<div style='color: #059669; font-weight: 500; padding: 0.5rem 0;'>✅ This recommendation has been accepted</div>", unsafe_allow_html=True)
        
        # Add separator
        st.markdown("---")

def main():
    # Load Belfius data
    if st.session_state.belfius_data is None:
        st.session_state.belfius_data = load_belfius_data()
    
    if st.session_state.belfius_data is None:
        st.error("Could not load Belfius data. Please ensure the Excel file is available.")
        return
    
    # Header with proper markdown rendering
    st.markdown(f"""
    <div style="background: #F7E194; padding: 1rem 1.5rem; border-radius: 16px; margin-bottom: 2rem; display: flex; align-items: center; justify-content: space-between;">
        <div style="padding: 0.75rem; border-radius: 12px; text-align: center;">
            <img src="data:image/png;base64,{logo_left}" width="120"/>
        </div>
        <div style="text-align: center; flex-grow: 1; padding: 0 2rem;">
            <h1 style="color: #212529; margin: 0; font-weight: 700; font-size: 2.2rem;">CEFR B2 Compliance Analysis</h1>
            <p style="color: #495057; margin: 0.5rem 0 0 0; font-size: 1rem;">Sentence-by-sentence recommendations for banking content</p>
        </div>
        <div style="padding: 0.75rem; border-radius: 12px; text-align: center;">
            <img src="data:image/png;base64,{logo_right}" width="120"/>
        </div>
    </div>
    """, unsafe_allow_html=True)
        
    # Sidebar for configuration
    with st.sidebar:
        try:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image("logos/sailpeak-logo.png", width=150)
        except:
            st.markdown("**Sailpeak**")
        
        st.header("Configuration")
        
        # URL Search
        st.subheader("URL Search")
        search_url = st.text_input("Enter URL to search:", placeholder="e.g., belfius.be/nl/particulieren")
        
        # Add language and path data
        enhanced_data = create_hierarchical_filter(st.session_state.belfius_data)
        
        if search_url:
            # Filter data based on search
            search_filtered = enhanced_data[enhanced_data['URL'].str.contains(search_url, case=False, na=False)]
            if len(search_filtered) > 0:
                st.success(f"Found {len(search_filtered)} matching URLs")
                enhanced_data = search_filtered
            else:
                st.warning("No matching URLs found")
        
        # Language filter
        languages = ['All Languages'] + sorted(enhanced_data['Language'].unique().tolist())
        selected_language = st.selectbox("Language:", languages)
        
        # Filter by language
        filtered_data = enhanced_data.copy()
        if selected_language != 'All Languages':
            filtered_data = filtered_data[filtered_data['Language'] == selected_language]
        
        # Page type filter
        page_types = ['All Types'] + sorted(filtered_data['Page Type'].unique().tolist())
        selected_page_type = st.selectbox("Page Type:", page_types)
        
        # Filter by page type
        if selected_page_type != 'All Types':
            filtered_data = filtered_data[filtered_data['Page Type'] == selected_page_type]
        
        # Add compliance filter
        show_all = st.checkbox("Show all pages (including compliant)")
        
        # Filter by compliance threshold
        if not show_all:
            filtered_data = filtered_data[filtered_data['Compliance Level'] < 70]
        
        # URL selection with clean paths
        if len(filtered_data) > 0:
            # Create display names with clean paths and scores
            url_options = []
            url_data_map = {}
            
            for idx, row in filtered_data.iterrows():
                clean_path = row['URL_Path']
                score = row['Compliance Level']
                
                # Create display string
                display_name = f"{clean_path} (Score: {score}%)"
                url_options.append(display_name)
                url_data_map[display_name] = row
            
            # Sort URLs alphabetically
            url_options = sorted(url_options)
            
            selected_url_display = st.selectbox("Select URL:", url_options)
            selected_url_data = url_data_map[selected_url_display]
            
            st.session_state.selected_url_info = selected_url_data
            
            # Show URL hierarchy
            st.markdown(f"""
            <div class="info">
                <strong>URL Path:</strong> {selected_url_data['URL_Path']}<br>
                <strong>Language:</strong> {selected_url_data['Language']}<br>
                <strong>Type:</strong> {selected_url_data['Page Type']}<br>
                <strong>Score:</strong> {selected_url_data['Compliance Level']}%
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.warning("No pages match the current filters")
            st.session_state.selected_url_info = None
        
        # Get recommendations button
        get_recommendations_btn = st.button("Get Recommendations", type="primary")
            
    # Analysis results
    if get_recommendations_btn:
        if not st.session_state.gemini_api_key:
            st.error("Please provide your Gemini API key in the sidebar")
        elif st.session_state.selected_url_info is None:
            st.error("Please select a URL from the sidebar")
        else:
            selected_url = st.session_state.selected_url_info['URL']
            page_score = st.session_state.selected_url_info['Compliance Level']
            page_type = st.session_state.selected_url_info['Page Type']
            
            with st.spinner("Extracting content and analyzing with Gemini AI..."):
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
                        st.success("Analysis complete!")
                    else:
                        st.warning("No specific problematic sentences found. The page might already be close to compliance!")
    
    # Render recommendations
    render_sentence_recommendations(st.session_state.analyzed_sentences)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>Sailpeak B2 Compliance Tool for Belfius</strong> - Powered by Gemini API</p>
        <p>Sentence-level recommendations for CEFR B2 compliance under the European Accessibility Act</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
