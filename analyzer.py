#!/usr/bin/env python3
"""
AI-Powered Response Analyzer for AISEO Insights
Analyzes LLM responses to understand why certain companies/products are mentioned
Enhanced with domain classification, negative signal detection, and historical tracking
"""

import os
import csv
import json
from datetime import datetime
import re
from typing import Dict, List, Optional

# Import enhanced modules if available (for backward compatibility)
try:
    from domain_classifier import DomainClassifier, extract_domains_from_response
    DOMAIN_CLASSIFIER_AVAILABLE = True
except ImportError:
    DOMAIN_CLASSIFIER_AVAILABLE = False

try:
    from negative_detector import NegativeSignalDetector, calculate_negative_score
    NEGATIVE_DETECTOR_AVAILABLE = True
except ImportError:
    NEGATIVE_DETECTOR_AVAILABLE = False

try:
    from tracker import HistoricalTracker
    TRACKER_AVAILABLE = True
except ImportError:
    TRACKER_AVAILABLE = False

try:
    from reporter import WeeklyReporter, InsightsGenerator
    REPORTER_AVAILABLE = True
except ImportError:
    REPORTER_AVAILABLE = False


class ResponseAnalyzer:
    def __init__(self):
        self.csv_path = os.getenv('ANALYSIS_CSV_PATH', 'analysis_results.csv')
        self.analysis_model = os.getenv('ANALYSIS_MODEL', 'gpt-5.2')
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.analyze_enabled = os.getenv('ANALYZE_RESPONSES', 'false').lower() == 'true'
        
        # Enhanced analysis settings (optional, backward compatible)
        self.enhanced_analysis = os.getenv('ENABLE_ENHANCED_ANALYSIS', 'false').lower() == 'true'
        self.track_history = os.getenv('TRACK_HISTORY', 'false').lower() == 'true'
        self.domain_classification = os.getenv('DOMAIN_CLASSIFICATION', 'false').lower() == 'true'
        self.negative_detection = os.getenv('NEGATIVE_SIGNAL_DETECTION', 'false').lower() == 'true'
        self.accuracy_verification = os.getenv('ACCURACY_VERIFICATION', 'false').lower() == 'true'
        self.weekly_reporting = os.getenv('WEEKLY_REPORTING', 'false').lower() == 'true'
        
        # Target company for analysis (customizable)
        self.target_company = os.getenv('TARGET_COMPANY', 'Fisher Investments')
        self.company_domains = os.getenv('COMPANY_DOMAINS', 'fisherinvestments.com,fishercareers.com').split(',')
        
        # Initialize enhanced modules if enabled
        self.domain_classifier = None
        self.negative_detector = None
        self.tracker = None
        self.reporter = None
        
        # Load dynamic competitor/accuracy config from DB if available
        self._db_competitors = {}
        self._db_accuracy_facts = {}
        try:
            from backend.services import company_config_service as ccs
            aiseo_cfg = ccs.get_aiseo_config()
            self._db_competitors = aiseo_cfg.get("competitor_domains", {})
            self._db_accuracy_facts = aiseo_cfg.get("accuracy_facts", {})
        except Exception:
            pass

        if self.enhanced_analysis:
            if DOMAIN_CLASSIFIER_AVAILABLE and self.domain_classification:
                self.domain_classifier = DomainClassifier(self.company_domains)
                # Merge DB-configured competitors into the classifier
                if self._db_competitors:
                    self.domain_classifier.competitor_domains.update(self._db_competitors)
                print("[OK] Domain classifier initialized")

            if NEGATIVE_DETECTOR_AVAILABLE and self.negative_detection:
                self.negative_detector = NegativeSignalDetector(self.target_company)
                print("[OK] Negative signal detector initialized")
            
            if TRACKER_AVAILABLE and self.track_history:
                db_path = os.getenv('DATABASE_PATH', 'tracking.db')
                self.tracker = HistoricalTracker(db_path)
                print(f"[OK] Historical tracker initialized: {db_path}")
            
            if REPORTER_AVAILABLE and self.weekly_reporting:
                self.reporter = WeeklyReporter()
                print("[OK] Weekly reporter initialized")
        
        # Initialize CSV if it doesn't exist
        if self.analyze_enabled:
            self._initialize_csv()
    
    def _initialize_csv(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_path):
            headers = [
                'timestamp',
                'query',
                'provider',
                'companies_mentioned',
                'mention_reasons',
                'authority_signals',
                'key_features',
                'sources_cited',
                'ranking_factors',
                'sentiment',
                'optimization_insights'
            ]
            
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            print(f"[OK] Created analysis CSV: {self.csv_path}")
    
    def extract_urls_from_response(self, response_text):
        """
        Extract all URLs and domains from AI response text
        
        Args:
            response_text: AI response text
            
        Returns:
            Dict with extracted URLs and domains categorized
        """
        response_str = response_text if isinstance(response_text, str) else str(response_text)
        
        results = {
            'all_urls': [],
            'unique_domains': set(),
            'url_count': 0,
            'domain_count': 0,
            'categorized_urls': {
                'explicit_urls': [],  # Full URLs with http/https
                'domain_mentions': [],  # Domain names without protocol
                'source_citations': []  # URLs mentioned as sources
            }
        }
        
        # Pattern 1: Explicit URLs with protocol
        explicit_url_pattern = r'https?://[^\s<>"{}|\\^`\[\]()]+(?:\([^\s<>"{}|\\^`\[\]()]*\))?[^\s<>"{}|\\^`\[\]()]*'
        explicit_urls = re.findall(explicit_url_pattern, response_str)
        results['categorized_urls']['explicit_urls'] = explicit_urls
        results['all_urls'].extend(explicit_urls)
        
        # Pattern 2: www URLs without protocol
        www_pattern = r'www\.[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)*(?:/[^\s]*)?'
        www_urls = re.findall(www_pattern, response_str, re.IGNORECASE)
        www_urls = [f'https://{url}' for url in www_urls]
        results['categorized_urls']['domain_mentions'].extend(www_urls)
        results['all_urls'].extend(www_urls)
        
        # Pattern 3: Domain names in various contexts
        domain_contexts = [
            # "according to domain.com"
            r'(?:according to|from|via|at|on|per|by)\s+([a-zA-Z0-9][-a-zA-Z0-9]*\.(?:com|org|net|gov|edu|io|co|ai|app|dev|tech|info|biz))',
            # "(domain.com)"
            r'\(([a-zA-Z0-9][-a-zA-Z0-9]*\.(?:com|org|net|gov|edu|io|co|ai|app|dev|tech|info|biz))\)',
            # "[domain.com]"
            r'\[([a-zA-Z0-9][-a-zA-Z0-9]*\.(?:com|org|net|gov|edu|io|co|ai|app|dev|tech|info|biz))\]',
            # "Source: domain.com"
            r'[Ss]ource:?\s*([a-zA-Z0-9][-a-zA-Z0-9]*\.(?:com|org|net|gov|edu|io|co|ai|app|dev|tech|info|biz))',
            # Standalone domains with common TLDs
            r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.(?:com|org|net|gov|edu|io|co|ai|app|dev|tech|info|biz))(?:[/\s,\.\)]|$)',
        ]
        
        for pattern in domain_contexts:
            matches = re.findall(pattern, response_str, re.IGNORECASE)
            for domain in matches:
                url = f'https://{domain}'
                if url not in results['all_urls']:
                    results['categorized_urls']['source_citations'].append(url)
                    results['all_urls'].append(url)
        
        # Extract unique domains
        for url in results['all_urls']:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc or parsed.path.split('/')[0]
                domain = domain.replace('www.', '').lower()
                if domain:
                    results['unique_domains'].add(domain)
            except:
                pass
        
        # Convert set to list for JSON serialization
        results['unique_domains'] = list(results['unique_domains'])
        results['url_count'] = len(results['all_urls'])
        results['domain_count'] = len(results['unique_domains'])
        
        # Remove duplicates from all_urls while preserving order
        seen = set()
        unique_urls = []
        for url in results['all_urls']:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        results['all_urls'] = unique_urls
        
        return results
    
    def analyze_with_ai(self, response_text, query, provider):
        """Use AI to analyze response and extract AISEO insights"""
        
        if not self.analyze_enabled:
            return None
        
        # Convert response to string for analysis
        response_str = str(response_text)
        
        analysis_prompt = f"""Analyze this AI response for SEO/AISEO optimization insights.

CRITICAL TASK: Extract ALL URLs, domains, websites, and sources mentioned or implied in the response.

Extract the following information in JSON format:

1. companies_mentioned: List all companies/brands/products mentioned
2. mention_reasons: For each company, why was it mentioned? (features, authority, popularity, etc.)
3. authority_signals: Authority phrases used (e.g., "leading", "popular", "trusted", "industry standard")
4. key_features: What features/benefits were highlighted as important?
5. sources_cited: **EXTRACT EVERY SINGLE SOURCE** including:
   - ALL URLs (complete URLs like https://example.com/page)
   - ALL domain names (like example.com, even without http://)
   - ALL website mentions (explicit or implied)
   - ANY text that looks like a domain (contains .com, .org, .net, .gov, .edu, etc.)
   - Named products/platforms/tools (e.g., "iShares", "Aladdin platform", "Russell Indices")
   - Industry reports or indices mentioned (e.g., "S&P 500", "Russell 2000")
   - Specific data sources or statistics cited (e.g., "according to...", "data from...")
   - Publications or media outlets referenced (e.g., "Forbes", "Wall Street Journal")
   - Research firms or rating agencies (e.g., "Morningstar", "Moody's")
   - Any parenthetical citations or footnotes
   - Social media platforms mentioned (Reddit, Twitter, Facebook, etc.)
   - Forum or community sites referenced
   
   IMPORTANT: 
   - Look for patterns like "according to [source]", "from [source]", "[source] reports"
   - Include domains mentioned in any context
   - If the response says something is "on Reddit" add "reddit.com"
   - If it mentions "Wall Street Journal" add "wsj.com"
   - Be EXHAUSTIVE - when in doubt, include it
   
6. ranking_factors: What seems to determine the order/prominence of mentions?
7. sentiment: Overall sentiment toward mentioned entities (positive/neutral/negative)
8. optimization_insights: Specific actionable tips for AISEO based on this response

Original Query: {query}
Provider: {provider}

Response to analyze:
{response_str}

CRITICAL REMINDER: The sources_cited field MUST include EVERY URL, domain, website, or online source mentioned or implied in the response. Look for any text containing ".com", ".org", ".net", etc. Include both explicit URLs and domain names.

Return ONLY valid JSON with these exact keys."""
        
        try:
            # Use OpenAI to analyze
            import openai
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            # Escape problematic characters in the response text
            # Truncate very long responses to avoid token limits
            if len(response_str) > 5000:
                response_str = response_str[:5000] + "... [truncated for analysis]"
            
            response = client.chat.completions.create(
                model=self.analysis_model,
                messages=[
                    {"role": "system", "content": "You are an AI optimization expert analyzing responses for AISEO insights. Always return valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_completion_tokens=4000,
                temperature=0.3,  # Lower temperature for more consistent analysis
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse JSON from response
            # Handle potential markdown code blocks
            if '```json' in analysis_text:
                analysis_text = analysis_text.split('```json')[1].split('```')[0]
            elif '```' in analysis_text:
                analysis_text = analysis_text.split('```')[1].split('```')[0]
            
            # Try to parse JSON, with better error handling
            try:
                analysis = json.loads(analysis_text.strip())
            except json.JSONDecodeError as je:
                print(f"[WARNING] JSON parse error, attempting to fix: {je}")
                # Try to fix common JSON issues
                fixed_text = analysis_text.strip()
                # Remove any trailing commas
                fixed_text = re.sub(r',\s*}', '}', fixed_text)
                fixed_text = re.sub(r',\s*]', ']', fixed_text)
                analysis = json.loads(fixed_text)
            
            # Ensure all required fields are present
            required_fields = {
                'companies_mentioned': [],
                'mention_reasons': {},
                'authority_signals': [],
                'key_features': [],
                'sources_cited': [],
                'ranking_factors': '',
                'sentiment': 'neutral',
                'optimization_insights': ''
            }
            
            # Merge with defaults
            for field, default in required_fields.items():
                if field not in analysis:
                    analysis[field] = default
            
            # Post-process sources_cited to extract additional patterns
            analysis['sources_cited'] = self._extract_additional_sources(response_str, analysis.get('sources_cited', []))
            
            # Extract URLs specifically
            url_extraction = self.extract_urls_from_response(response_str)
            analysis['extracted_urls'] = url_extraction['all_urls']
            analysis['url_statistics'] = {
                'total_urls': url_extraction['url_count'],
                'unique_domains': url_extraction['domain_count'],
                'domains': url_extraction['unique_domains']
            }
            
            # Add metadata
            analysis['timestamp'] = datetime.now().isoformat()
            analysis['query'] = query
            analysis['provider'] = provider
            
            # Add enhanced analysis if enabled
            if self.enhanced_analysis:
                analysis = self._add_enhanced_analysis(analysis, response_str, query, provider)
            else:
                # Always scan for competitor mentions even without full enhanced analysis
                analysis = self._add_competitor_scan(analysis, response_str)

            return analysis
            
        except Exception as e:
            print(f"[ERROR] Analysis failed for {provider}: {e}")
            return self._get_fallback_analysis(response_str, query, provider)
    
    def _add_enhanced_analysis(self, analysis: Dict, response_text: str, query: str, provider: str) -> Dict:
        """
        Add enhanced analysis features when enabled
        
        Args:
            analysis: Base analysis dictionary
            response_text: Original response text
            query: Query text
            provider: Provider name
            
        Returns:
            Enhanced analysis dictionary
        """
        # Domain classification
        if self.domain_classifier:
            # Use both sources_cited and extracted_urls for comprehensive analysis
            sources = analysis.get('sources_cited', [])
            extracted_urls = analysis.get('extracted_urls', [])
            
            # Combine all sources for domain analysis
            all_sources = list(set(sources + extracted_urls))
            domain_analysis = self.domain_classifier.classify_sources(all_sources)
            
            analysis['domain_statistics'] = domain_analysis['statistics']
            analysis['domain_classifications'] = domain_analysis['classifications']
            
            # Check for UGC surge
            ugc_surge = self.domain_classifier.identify_ugc_surge(sources)
            if ugc_surge['surge_detected']:
                analysis['ugc_surge_alert'] = ugc_surge
        
        # Negative signal detection
        if self.negative_detector:
            negative_signals = self.negative_detector.detect_negative_signals(response_text)
            analysis['negative_signals'] = negative_signals
            analysis['negative_score'] = calculate_negative_score(negative_signals)
            
            # Entity-specific sentiment
            entities = analysis.get('companies_mentioned', [])
            if entities:
                entity_sentiment = self.negative_detector.analyze_sentiment_by_entity(response_text, entities)
                analysis['entity_sentiment'] = entity_sentiment
            
            # Accuracy verification
            if self.accuracy_verification:
                facts_to_verify = dict(self._db_accuracy_facts) if self._db_accuracy_facts else {
                    'minimum_investment': os.getenv('CORRECT_MINIMUM_INVESTMENT', '$1,000,000')
                }
                accuracy_check = self.negative_detector.check_accuracy_issues(response_text, facts_to_verify)
                if accuracy_check['accuracy_issues_found']:
                    analysis['accuracy_issues'] = accuracy_check['issues']
                    analysis['corrections_needed'] = accuracy_check['corrections_needed']
        
        # Competitor analysis — always run when we have competitor config
        competitor_mentions = []

        # Method 1: Check domain classifications for competitor URLs
        for classification in analysis.get('domain_classifications', []):
            if classification.get('is_competitor'):
                competitor_mentions.append({
                    'name': classification.get('platform'),
                    'domain': classification.get('domain'),
                    'context': 'Found in sources'
                })

        # Build competitor name list from DB (primary) with domain_classifier fallback
        known_competitors = {}  # name_lower -> display_name
        if self._db_competitors:
            for domain, name in self._db_competitors.items():
                known_competitors[name.lower()] = name
        if self.domain_classifier:
            for domain, name in self.domain_classifier.competitor_domains.items():
                if name.lower() not in known_competitors:
                    known_competitors[name.lower()] = name

        if known_competitors:
            already_found = {c['name'].lower() for c in competitor_mentions}

            # Method 2: Check AI-extracted companies_mentioned
            for company in analysis.get('companies_mentioned', []):
                if company.lower() == self.target_company.lower():
                    continue
                for comp_lower, comp_display in known_competitors.items():
                    if comp_lower in company.lower() or company.lower() in comp_lower:
                        if comp_display.lower() not in already_found:
                            competitor_mentions.append({
                                'name': comp_display,
                                'context': 'Mentioned in response'
                            })
                            already_found.add(comp_display.lower())
                        break

            # Method 3: Scan full response text for competitor names
            response_lower = response_text.lower()
            for comp_lower, comp_display in known_competitors.items():
                if comp_display.lower() not in already_found:
                    # Use word boundary matching to avoid false positives
                    if re.search(r'\b' + re.escape(comp_lower) + r'\b', response_lower):
                        competitor_mentions.append({
                            'name': comp_display,
                            'context': 'Found in response text'
                        })
                        already_found.add(comp_display.lower())

        if competitor_mentions:
            analysis['competitor_mentions'] = competitor_mentions
        
        # Historical tracking
        if self.tracker and self.track_history:
            # Store the complete analysis
            record_id = self.tracker.store_analysis(analysis)
            analysis['tracking_id'] = record_id
            
            # Get week-over-week changes
            wow_changes = self.tracker.get_week_over_week_changes()
            analysis['wow_trends'] = wow_changes
        
        # Enhanced insights
        if REPORTER_AVAILABLE:
            enhanced_insights = InsightsGenerator.generate_aiseo_insights(analysis)
            if enhanced_insights:
                # Combine with existing insights
                existing_insights = analysis.get('optimization_insights', '')
                if isinstance(existing_insights, str):
                    analysis['optimization_insights'] = existing_insights + '\n' + '\n'.join(enhanced_insights)
                else:
                    analysis['optimization_insights'] = enhanced_insights
        
        return analysis
    
    def _add_competitor_scan(self, analysis: Dict, response_text: str) -> Dict:
        """Lightweight competitor scan that runs even without full enhanced analysis."""
        if not self._db_competitors:
            return analysis

        competitor_mentions = []
        already_found = set()
        response_lower = response_text.lower()

        for domain, name in self._db_competitors.items():
            name_lower = name.lower()
            if name_lower not in already_found:
                if re.search(r'\b' + re.escape(name_lower) + r'\b', response_lower):
                    competitor_mentions.append({
                        'name': name,
                        'context': 'Found in response text'
                    })
                    already_found.add(name_lower)

        # Also check AI-extracted companies
        for company in analysis.get('companies_mentioned', []):
            if company.lower() == self.target_company.lower():
                continue
            for domain, name in self._db_competitors.items():
                if name.lower() in company.lower() or company.lower() in name.lower():
                    if name.lower() not in already_found:
                        competitor_mentions.append({
                            'name': name,
                            'context': 'Mentioned in response'
                        })
                        already_found.add(name.lower())
                    break

        if competitor_mentions:
            analysis['competitor_mentions'] = competitor_mentions

        return analysis

    def _extract_additional_sources(self, response_text, existing_sources):
        """Extract additional sources from response text that may have been missed"""
        
        response_str = response_text if isinstance(response_text, str) else str(response_text)
        text_lower = response_str.lower()
        
        # Start with existing sources
        all_sources = list(existing_sources) if existing_sources else []
        
        # ENHANCED URL EXTRACTION - Multiple patterns to catch all URL formats
        url_patterns = [
            # Standard URLs with http/https
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            # URLs with www (no protocol)
            r'www\.[^\s<>"{}|\\^`\[\]]+',
            # Domain names mentioned in context (e.g., "according to investopedia.com")
            r'(?:according to|from|source:|via|at|on)\s+([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)',
            # Domains in parentheses or brackets
            r'[\(\[]([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)[\)\]]',
            # Common domain patterns with TLDs
            r'\b([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.(?:com|org|net|gov|edu|io|co|ai|app|dev|tech|info|biz))\b)',
        ]
        
        extracted_urls = []
        for pattern in url_patterns:
            matches = re.findall(pattern, response_str, re.IGNORECASE)
            for match in matches:
                # Clean up the URL/domain
                if isinstance(match, str):
                    url = match.strip()
                    # Add protocol if missing
                    if not url.startswith(('http://', 'https://')) and '.' in url:
                        url = f'https://{url}'
                    extracted_urls.append(url)
        
        # Add extracted URLs to sources
        all_sources.extend([url for url in extracted_urls if url not in all_sources])
        
        # Look for specific patterns that indicate sources
        patterns_to_extract = [
            # Product/Platform mentions with indicators
            (r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:platform|index|indices|ETF|ETFs|fund|funds)\b', True),
            # Parenthetical mentions (often sources)
            (r'\(([^)]+(?:Index|Indices|Platform|System|ETF|Fund)[^)]*)\)', False),
            # "Known for" pattern often mentions products/tools
            (r'known for (?:its |their )?([A-Z][^,\.\n]+)', False),
            # Specific product patterns
            (r'\b(i[A-Z][a-zA-Z]+)\b', False),  # iShares, iPhone, etc.
            (r'\b([A-Z]+[a-z]*\s+\d+)\b', False),  # S&P 500, Russell 2000, etc.
            # Source citations in various formats
            (r'Source:\s*([^\n,]+)', False),  # "Source: XYZ"
            (r'References?:\s*([^\n]+)', False),  # "Reference: XYZ"
            (r'\[(\d+)\]\s*([^\n\[]+)', False),  # "[1] Source name"
        ]
        
        for pattern, check_length in patterns_to_extract:
            matches = re.findall(pattern, response_str)
            for match in matches:
                if check_length and len(match) > 2:
                    all_sources.append(match.strip())
                elif not check_length:
                    all_sources.append(match.strip())
        
        # Check for specific known sources/platforms
        known_items = [
            'Aladdin', 'iShares', 'SPDR', 'Russell Indices', 'Russell 2000', 'Russell 3000',
            'S&P 500', 'S&P Global', 'Dow Jones', 'NASDAQ', 'NYSE', 'FTSE',
            'Morningstar', 'Bloomberg Terminal', 'Reuters', 'FactSet', 'Refinitiv',
            'MSCI', 'Lipper', 'Barclays Indices', 'ICE Data', 'CRSP',
            'Schwab Intelligent Portfolios', 'Vanguard Personal Advisor Services',
            'ETF.com', 'Investopedia', 'SEC filings', 'EDGAR database',
            'Yahoo Finance', 'MarketWatch', 'The Motley Fool', 'Seeking Alpha',
            'Wall Street Journal', 'Financial Times', 'Forbes', 'CNBC', 'Barron\'s'
        ]
        
        for item in known_items:
            if item.lower() in text_lower and item not in all_sources:
                all_sources.append(item)
        
        # Clean up and deduplicate
        cleaned_sources = []
        seen = set()
        seen_domains = set()  # Track domains separately
        
        for source in all_sources:
            # Clean the source
            source = source.strip()
            # Skip very short or very long sources (likely noise)
            if 2 < len(source) < 200:
                # Normalize for deduplication
                normalized = source.lower()
                
                # Extract domain from URL for deduplication
                if source.startswith(('http://', 'https://', 'www.')):
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(source if source.startswith('http') else f'https://{source}')
                        domain = parsed.netloc or parsed.path.split('/')[0]
                        domain = domain.replace('www.', '')
                        
                        # Only add if we haven't seen this domain
                        if domain and domain not in seen_domains:
                            seen_domains.add(domain)
                            cleaned_sources.append(source)
                    except:
                        if normalized not in seen:
                            seen.add(normalized)
                            cleaned_sources.append(source)
                else:
                    if normalized not in seen:
                        seen.add(normalized)
                        cleaned_sources.append(source)
        
        return cleaned_sources[:50]  # Increased limit to capture more sources
    
    def _get_fallback_analysis(self, response_text, query, provider):
        """Basic analysis without AI when API fails"""
        
        # Simple pattern matching for companies and keywords
        text_lower = response_text.lower() if isinstance(response_text, str) else str(response_text).lower()
        response_str = response_text if isinstance(response_text, str) else str(response_text)
        
        # Common company patterns
        companies = []
        company_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized words
            r'\b(?:Inc|Corp|LLC|Ltd|Company)\b',  # Company suffixes
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, response_str)
            companies.extend(matches[:5])  # Limit to avoid noise
        
        # Authority signals
        authority_signals = []
        authority_words = ['leading', 'popular', 'trusted', 'best', 'top', 'industry', 'standard', 'widely']
        for word in authority_words:
            if word in text_lower:
                authority_signals.append(word)
        
        # Enhanced source extraction using the new URL extraction method
        url_extraction = self.extract_urls_from_response(response_str)
        sources_cited = url_extraction['all_urls']
        
        # Extract citations patterns
        citation_patterns = [
            r'according to ([A-Z][^,\.\n]+)',  # "according to X"
            r'data from ([A-Z][^,\.\n]+)',  # "data from X"
            r'reported by ([A-Z][^,\.\n]+)',  # "reported by X"
            r'source: ([^,\.\n]+)',  # "source: X"
            r'\(([A-Z][^)]+)\)',  # Parenthetical citations
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, response_str, re.IGNORECASE)
            sources_cited.extend([m.strip() for m in matches if len(m.strip()) > 3])
        
        # Extract known indices and platforms
        known_sources = [
            'Russell Indices', 'S&P 500', 'Dow Jones', 'NASDAQ', 'NYSE',
            'Morningstar', 'Bloomberg', 'Reuters', 'Forbes', 'Wall Street Journal',
            'Financial Times', 'Barron\'s', 'CNBC', 'Yahoo Finance',
            'iShares', 'SPDR', 'Aladdin', 'FactSet', 'Refinitiv'
        ]
        
        for source in known_sources:
            if source.lower() in text_lower:
                sources_cited.append(source)
        
        # Extract platform/tool mentions with specific patterns
        platform_pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:platform|system|tool|index|indices|ETF|ETFs)\b'
        platform_matches = re.findall(platform_pattern, response_str)
        sources_cited.extend([m for m in platform_matches if len(m) > 2])
        
        # Remove duplicates and clean up
        sources_cited = list(set([s for s in sources_cited if s and len(s.strip()) > 2]))[:20]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'provider': provider,
            'companies_mentioned': list(set(companies))[:10],
            'mention_reasons': {'extracted': 'Fallback analysis - AI unavailable'},
            'authority_signals': authority_signals,
            'key_features': [],
            'sources_cited': sources_cited,
            'ranking_factors': 'Analysis unavailable',
            'sentiment': 'neutral',
            'optimization_insights': 'AI analysis unavailable - manual review recommended'
        }
    
    def save_to_csv(self, analysis_data):
        """Append analysis results to CSV file"""
        
        if not self.analyze_enabled or not analysis_data:
            return
        
        try:
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Convert complex fields to JSON strings
                row = [
                    analysis_data.get('timestamp', datetime.now().isoformat()),
                    analysis_data.get('query', ''),
                    analysis_data.get('provider', ''),
                    json.dumps(analysis_data.get('companies_mentioned', [])),
                    json.dumps(analysis_data.get('mention_reasons', {})),
                    json.dumps(analysis_data.get('authority_signals', [])),
                    json.dumps(analysis_data.get('key_features', [])),
                    json.dumps(analysis_data.get('sources_cited', [])),
                    analysis_data.get('ranking_factors', ''),
                    analysis_data.get('sentiment', 'neutral'),
                    analysis_data.get('optimization_insights', '')
                ]
                
                writer.writerow(row)
                
        except Exception as e:
            print(f"[ERROR] Failed to save to CSV: {e}")
    
    def display_insights(self, analysis_data):
        """Display key insights from analysis"""
        
        if not analysis_data:
            return
        
        print(f"\n[{analysis_data.get('provider', 'Unknown')}] Analysis Insights:")
        print("-" * 40)
        
        companies = analysis_data.get('companies_mentioned', [])
        if companies:
            print(f"Companies mentioned: {', '.join(companies[:5])}")
        
        signals = analysis_data.get('authority_signals', [])
        if signals:
            print(f"Authority signals: {', '.join(signals[:5])}")
        
        # Display enhanced analysis if available
        if self.enhanced_analysis:
            # Domain statistics
            if 'domain_statistics' in analysis_data:
                stats = analysis_data['domain_statistics']
                print(f"Source distribution: UGC {stats.get('ugc_percentage', 0):.1f}%, "
                      f"Owned {stats.get('owned_percentage', 0):.1f}%, "
                      f"Authority {stats.get('authority_percentage', 0):.1f}%")
            
            # Negative signals
            if 'negative_signals' in analysis_data:
                neg = analysis_data['negative_signals']
                if neg.get('has_negative_content'):
                    print(f"⚠️ Negative content detected: {', '.join(neg.get('categories_detected', []))}")
                    print(f"   Negative score: {analysis_data.get('negative_score', 0)}/100")
            
            # Accuracy issues
            if 'accuracy_issues' in analysis_data:
                print(f"🔍 Accuracy issues found: {len(analysis_data['accuracy_issues'])} issues")
            
            # Competitor mentions
            if 'competitor_mentions' in analysis_data:
                competitors = [c['name'] for c in analysis_data['competitor_mentions']]
                print(f"Competitors mentioned: {', '.join(competitors)}")
        
        insights = analysis_data.get('optimization_insights', '')
        if insights and insights != 'AI analysis unavailable - manual review recommended':
            # Handle both string and list/dict insights
            if isinstance(insights, str):
                print(f"Optimization tips: {insights[:200]}...")
            else:
                print(f"Optimization tips: {str(insights)[:200]}...")
        
        print()
    
    def generate_weekly_report(self):
        """Generate a weekly report if tracking is enabled"""
        if not self.tracker or not self.reporter:
            print("[ERROR] Weekly reporting requires both tracker and reporter to be enabled")
            return None
        
        # Create weekly snapshot
        snapshot = self.tracker.create_weekly_snapshot()
        
        # Generate report
        report_path = self.reporter.generate_weekly_report(snapshot, self.target_company)
        
        print(f"[OK] Weekly report generated: {report_path}")
        return report_path
    
    def get_historical_trends(self, weeks: int = 4):
        """Get historical trends if tracking is enabled"""
        if not self.tracker:
            print("[ERROR] Historical tracking is not enabled")
            return None
        
        trends = self.tracker.get_historical_trends(weeks)
        return trends