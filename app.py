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
    
    /* Hierarchical navigation styles */
    .nav-item {
        margin: 0.25rem 0;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
        border-left: 3px solid transparent;
        font-size: 0.9rem;
    }
    
    .nav-item:hover {
        background: #f1f5f9;
        border-left-color: #EBD37F;
    }
    
    .nav-item.active {
        background: #EBD37F;
        border-left-color: #d4c46a;
        font-weight: 600;
    }
    
    .nav-item.has-children {
        font-weight: 500;
    }
    
    .nav-item.leaf {
        color: #059669;
        font-size: 0.85rem;
    }
    
    .nav-item.leaf.selected {
        background: #d1fae5;
        border-left-color: #059669;
        font-weight: 600;
    }
    
    .nav-children {
        margin-left: 1rem;
        padding-left: 0.5rem;
        border-left: 1px solid #e2e8f0;
    }
    
    .breadcrumb {
        background: #f8fafc;
        padding: 0.75rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-size: 0.85rem;
        color: #64748b;
    }
    
    .breadcrumb .current {
        font-weight: 600;
        color: #1e293b;
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
if 'navigation_path' not in st.session_state:
    st.session_state.navigation_path = []
if 'expanded_nodes' not in st.session_state:
    st.session_state.expanded_nodes = set()

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

def build_url_hierarchy(data):
    """Build hierarchical structure from URLs"""
    hierarchy = {}
    
    for idx, row in data.iterrows():
        url = row['URL']
        
        # Clean up URL and extract path
        if 'belfius.be' in url:
            path_part = url.split('belfius.be')[-1]
            if path_part.startswith('/'):
                path_part = path_part[1:]
            
            # Remove file extensions and query parameters
            path_part = re.sub(r'\.(aspx|html).*$', '', path_part)
            path_part = path_part.rstrip('/')
            
            if not path_part:
                path_part = 'home'
            
            # Split path into components
            path_components = path_part.split('/')
            
            # Build hierarchy
            current_level = hierarchy
            full_path = []
            
            for component in path_components:
                full_path.append(component)
                path_key = '/'.join(full_path)
                
                if component not in current_level:
                    current_level[component] = {
                        '_children': {},
                        '_data': None,
                        '_path': path_key
                    }
                
                # If this is the last component, store the data
                if component == path_components[-1]:
                    current_level[component]['_data'] = row
                
                current_level = current_level[component]['_children']
    
    return hierarchy

def render_navigation_node(node_name, node_data, level=0, parent_path="", show_all=False, is_last=True, prefix=""):
    """Render a single navigation node in repository-style format with proper tree structure"""
    current_path = f"{parent_path}/{node_name}" if parent_path else node_name
    has_children = len(node_data['_children']) > 0
    has_data = node_data['_data'] is not None
    
    # Check if this node or its children have non-compliant pages
    def has_non_compliant_pages(node):
        if node['_data'] is not None:
            return node['_data']['Compliance Level'] < 70
        for child in node['_children'].values():
            if has_non_compliant_pages(child):
                return True
        return False
    
    # Skip this node if it has no non-compliant pages and show_all is False
    if not show_all and not has_non_compliant_pages(node_data):
        return
    
    # Create unique key for this node
    node_key = f"nav_{current_path}_{level}"
    
    # Tree structure symbols
    if level == 0:
        tree_symbol = ""
        new_prefix = ""
    else:
        tree_symbol = "└── " if is_last else "├── "
        new_prefix = prefix + ("    " if is_last else "│   ")
    
    # Determine node styling
    if has_data and not has_children:
        # Leaf node (file) - use document icon
        score = node_data['_data']['Compliance Level']
        
        # Skip compliant pages unless show_all is True
        if not show_all and score >= 70:
            return
        
        # File icon with status
        if score < 50:
            file_icon = "📄"
            status_color = "#dc2626"  # Red
        elif score < 70:
            file_icon = "📄"
            status_color = "#f59e0b"  # Yellow
        else:
            file_icon = "📄"
            status_color = "#059669"  # Green
        
        display_text = f"{prefix}{tree_symbol}{file_icon} {node_name}"
        score_text = f"({score}%)"
        
        # Custom styling for repository look with proper selection highlighting
        is_selected = (st.session_state.selected_url_info is not None and 
                      node_data['_data']['URL'] == st.session_state.selected_url_info['URL'])
        
        st.markdown(f"""
        <div style="font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; 
                    font-size: 0.8rem; 
                    padding: 0.2rem 0.5rem; 
                    margin: 0.05rem 0;
                    background: {'#e3f2fd' if is_selected else 'transparent'};
                    border-radius: 3px;
                    border-left: 3px solid {'#1976d2' if is_selected else 'transparent'};
                    white-space: pre;">
            <span style="color: #666;">{display_text}</span>
            <span style="color: {status_color}; font-weight: 600; margin-left: 8px;">{score_text}</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Select", key=node_key, help=f"Score: {score}%"):
            st.session_state.selected_url_info = node_data['_data']
            st.session_state.navigation_path = current_path.split('/')
            st.rerun()
            
    elif has_children:
        # Parent node (folder) - use folder icon
        is_expanded = current_path in st.session_state.expanded_nodes
        
        # Folder icon with expand/collapse state
        if level == 0:
            folder_icon = "🏠" if node_name == "home" else "📂"
            display_text = f"{folder_icon} {node_name}/"
        else:
            folder_icon = "📂" if is_expanded else "📁"
            display_text = f"{prefix}{tree_symbol}{folder_icon} {node_name}/"
        
        # Repository-style folder display
        st.markdown(f"""
        <div style="font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; 
                    font-size: 0.8rem; 
                    padding: 0.2rem 0.5rem; 
                    margin: 0.05rem 0;
                    font-weight: 600;
                    color: #1976d2;
                    white-space: pre;">
            {display_text}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Toggle", key=node_key):
            if is_expanded:
                st.session_state.expanded_nodes.discard(current_path)
            else:
                st.session_state.expanded_nodes.add(current_path)
            st.rerun()
        
        # Show children if expanded
        if is_expanded:
            # Sort children: folders first, then files
            folders = [(name, data) for name, data in node_data['_children'].items() if len(data['_children']) > 0]
            files = [(name, data) for name, data in node_data['_children'].items() if len(data['_children']) == 0]
            all_children = sorted(folders) + sorted(files)
            
            # Filter children based on show_all setting
            visible_children = []
            for child_name, child_data in all_children:
                def has_non_compliant_pages_recursive(node):
                    if node['_data'] is not None:
                        return node['_data']['Compliance Level'] < 70
                    for child in node['_children'].values():
                        if has_non_compliant_pages_recursive(child):
                            return True
                    return False
                
                if show_all or has_non_compliant_pages_recursive(child_data):
                    visible_children.append((child_name, child_data))
            
            for idx, (child_name, child_data) in enumerate(visible_children):
                is_last_child = (idx == len(visible_children) - 1)
                render_navigation_node(child_name, child_data, level + 1, current_path, show_all, is_last_child, new_prefix)

def render_breadcrumb():
    """Render breadcrumb navigation"""
    if st.session_state.navigation_path:
        breadcrumb_items = []
        for i, item in enumerate(st.session_state.navigation_path):
            if i == len(st.session_state.navigation_path) - 1:
                breadcrumb_items.append(f'<span class="current">{item}</span>')
            else:
                breadcrumb_items.append(item)
        
        breadcrumb_text = " → ".join(breadcrumb_items)
        st.markdown(f"""
        <div class="breadcrumb">
            <strong>Current Path:</strong> belfius.be → {breadcrumb_text}
        </div>
        """, unsafe_allow_html=True)

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
        potential_improvement = calculate_score_improvement(sentence_data, st.session_state.selected_url_info['Compliance Level'], len(sentences))
        
        accepted_badge = '✅ ACCEPTED' if is_accepted else ''
        
        # Issue header at the top
        st.markdown(f"**Issue #{i}**")
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
                st.image("logos/sailpeak.png", width=150)
        except:
            st.markdown("**Sailpeak**")
        
        st.header("Navigation")
        
        # Show all pages checkbox
        show_all_pages = st.checkbox("Show all pages (including compliant)", value=False)
        
        st.markdown("---")
        
        # Build hierarchical navigation
        hierarchy = build_url_hierarchy(st.session_state.belfius_data)
        
        # Show breadcrumb if a page is selected
        render_breadcrumb()
        
        # Start with root level navigation
        st.subheader("🏠 belfius.be")
        st.markdown("""
        <div style="font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; 
                    font-size: 0.75rem; 
                    color: #666; 
                    margin-bottom: 1rem;
                    padding: 0.5rem;
                    background: #f8f9fa;
                    border-radius: 4px;">
        📁 = Folder (click Toggle to expand)<br>
        📄 = Page file<br>
        <span style="color: #dc2626;">Red scores = &lt;50%</span><br>
        <span style="color: #f59e0b;">Yellow scores = 50-69%</span><br>
        <span style="color: #059669;">Green scores = ≥70%</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Render navigation tree
        for idx, (node_name, node_data) in enumerate(sorted(hierarchy.items())):
            is_last_root = (idx == len(hierarchy) - 1)
            render_navigation_node(node_name, node_data, show_all=show_all_pages, is_last=is_last_root)
        
        st.markdown("---")
        
        # Show selected page info
        if st.session_state.selected_url_info is not None:
            st.subheader("Selected Page")
            render_url_info(st.session_state.selected_url_info)
            
            # Get recommendations button
            get_recommendations_btn = st.button("🔍 Get Recommendations", type="primary")
        else:
            st.info("👆 Select a page from the navigation above to get started")
            get_recommendations_btn = False
    
    # Main content area
    if st.session_state.selected_url_info is not None:
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
        1. **Navigate** through the Belfius website structure in the sidebar
        2. **Select** a page by clicking on it (pages show compliance scores with 🔴🟡🟢 indicators)
        3. **Analyze** the page content with AI-powered recommendations
        4. **Accept** improvements to boost compliance scores
        
        ### Features:
        - 🎯 **Sentence-level analysis** for precise improvements
        - 📊 **Real-time score tracking** with estimated improvements
        - 🌐 **Multi-language support** (Dutch, French, English)
        - 🏦 **Banking-specific** terminology and context awareness
        """)

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
