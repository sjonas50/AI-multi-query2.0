#!/usr/bin/env python3
"""
Domain Classification Module for AI Optimization Intelligence
Classifies and analyzes source domains for AISEO insights
"""

import re
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Optional
import json


class DomainClassifier:
    """Classifies domains into categories and tracks authority signals"""
    
    def __init__(self, company_domains: List[str] = None):
        """
        Initialize the domain classifier
        
        Args:
            company_domains: List of domains owned by the target company
        """
        self.company_domains = company_domains or []
        
        # UGC platforms
        self.ugc_platforms = {
            'reddit.com': 'Reddit',
            'old.reddit.com': 'Reddit',
            'yelp.com': 'Yelp',
            'm.yelp.com': 'Yelp',
            'quora.com': 'Quora',
            'trustpilot.com': 'Trustpilot',
            'glassdoor.com': 'Glassdoor',
            'indeed.com': 'Indeed',
            'facebook.com': 'Facebook',
            'twitter.com': 'Twitter',
            'x.com': 'X (Twitter)',
            'linkedin.com': 'LinkedIn',
            'youtube.com': 'YouTube',
            'tiktok.com': 'TikTok',
            'bogleheads.org': 'Bogleheads',
            'city-data.com': 'City-Data Forum',
            'answers.yahoo.com': 'Yahoo Answers',
        }
        
        # Review sites
        self.review_sites = {
            'trustpilot.com': 'Trustpilot',
            'yelp.com': 'Yelp',
            'bbb.org': 'Better Business Bureau',
            'consumeraffairs.com': 'ConsumerAffairs',
            'sitejabber.com': 'SiteJabber',
            'g2.com': 'G2',
            'capterra.com': 'Capterra',
            'gartner.com': 'Gartner',
            'forrester.com': 'Forrester',
        }
        
        # Financial news and authority sites
        self.authority_sites = {
            'wsj.com': 'Wall Street Journal',
            'ft.com': 'Financial Times',
            'bloomberg.com': 'Bloomberg',
            'reuters.com': 'Reuters',
            'cnbc.com': 'CNBC',
            'marketwatch.com': 'MarketWatch',
            'barrons.com': "Barron's",
            'forbes.com': 'Forbes',
            'fortune.com': 'Fortune',
            'businessinsider.com': 'Business Insider',
            'economist.com': 'The Economist',
            'nytimes.com': 'New York Times',
            'washingtonpost.com': 'Washington Post',
            'investopedia.com': 'Investopedia',
            'morningstar.com': 'Morningstar',
            'fool.com': 'The Motley Fool',
            'seekingalpha.com': 'Seeking Alpha',
            'nasdaq.com': 'NASDAQ',
            'nyse.com': 'NYSE',
            'sec.gov': 'SEC',
            'finra.org': 'FINRA',
        }
        
        # Financial service competitors (example list - customize as needed)
        self.competitor_domains = {
            'vanguard.com': 'Vanguard',
            'fidelity.com': 'Fidelity',
            'schwab.com': 'Charles Schwab',
            'tdameritrade.com': 'TD Ameritrade',
            'etrade.com': 'E*TRADE',
            'ml.com': 'Merrill Lynch',
            'morganstanley.com': 'Morgan Stanley',
            'gs.com': 'Goldman Sachs',
            'jpmorgan.com': 'JPMorgan',
            'wellsfargo.com': 'Wells Fargo',
            'blackrock.com': 'BlackRock',
            'statestreet.com': 'State Street',
            'northerntrust.com': 'Northern Trust',
            'edwardjones.com': 'Edward Jones',
            'raymondjames.com': 'Raymond James',
            'ameriprise.com': 'Ameriprise',
            'principal.com': 'Principal',
            'prudential.com': 'Prudential',
            'tiaa.org': 'TIAA',
            'usbank.com': 'U.S. Bank',
        }
        
        # Domain authority scores (simplified - could be enhanced with real data)
        self.authority_scores = {
            'high': ['wsj.com', 'ft.com', 'bloomberg.com', 'reuters.com', 'sec.gov', 
                     'forbes.com', 'cnbc.com', 'nytimes.com', 'investopedia.com'],
            'medium': ['marketwatch.com', 'fool.com', 'morningstar.com', 'barrons.com',
                       'seekingalpha.com', 'businessinsider.com'],
            'variable': ['reddit.com', 'quora.com', 'yelp.com', 'trustpilot.com'],
        }
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ''
        
        # Handle URLs without protocol
        if not url.startswith(('http://', 'https://', '//')):
            url = 'https://' + url
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split('/')[0]
            # Remove www prefix for consistency
            domain = domain.replace('www.', '')
            return domain.lower()
        except:
            return ''
    
    def classify_domain(self, url: str) -> Dict[str, any]:
        """
        Classify a domain/URL into categories
        
        Returns:
            Dict with classification details
        """
        domain = self.extract_domain(url)
        
        result = {
            'url': url,
            'domain': domain,
            'category': 'unknown',
            'platform': None,
            'authority_score': 'low',
            'is_ugc': False,
            'is_owned': False,
            'is_competitor': False,
            'is_review_site': False,
            'is_authority': False,
        }
        
        if not domain:
            return result
        
        # Check if owned domain
        if any(owned in domain for owned in self.company_domains):
            result['category'] = 'owned'
            result['is_owned'] = True
            result['authority_score'] = 'owned'
            return result
        
        # Check if UGC platform
        if domain in self.ugc_platforms:
            result['category'] = 'ugc'
            result['platform'] = self.ugc_platforms[domain]
            result['is_ugc'] = True
            result['authority_score'] = 'variable'
            
            # Check if also a review site
            if domain in self.review_sites:
                result['is_review_site'] = True
            return result
        
        # Check if review site (not already classified as UGC)
        if domain in self.review_sites:
            result['category'] = 'review'
            result['platform'] = self.review_sites[domain]
            result['is_review_site'] = True
            result['authority_score'] = 'medium'
            return result
        
        # Check if competitor
        if domain in self.competitor_domains:
            result['category'] = 'competitor'
            result['platform'] = self.competitor_domains[domain]
            result['is_competitor'] = True
            result['authority_score'] = 'high'
            return result
        
        # Check if authority site
        if domain in self.authority_sites:
            result['category'] = 'authority'
            result['platform'] = self.authority_sites[domain]
            result['is_authority'] = True
            result['authority_score'] = 'high'
            return result
        
        # Determine authority score for unknown domains
        if domain in self.authority_scores['high']:
            result['authority_score'] = 'high'
        elif domain in self.authority_scores['medium']:
            result['authority_score'] = 'medium'
        elif domain in self.authority_scores['variable']:
            result['authority_score'] = 'variable'
        
        # Generic classification for unknown domains
        if any(keyword in domain for keyword in ['news', 'media', 'journal', 'times', 'post']):
            result['category'] = 'news'
            result['authority_score'] = 'medium'
        elif any(keyword in domain for keyword in ['blog', 'medium.com', 'substack']):
            result['category'] = 'blog'
            result['authority_score'] = 'low'
        elif any(keyword in domain for keyword in ['.gov', '.edu', '.org']):
            result['category'] = 'institutional'
            result['authority_score'] = 'high'
        else:
            result['category'] = 'third-party'
        
        return result
    
    def classify_sources(self, sources: List[str]) -> Dict[str, any]:
        """
        Classify multiple sources and provide aggregate statistics
        
        Args:
            sources: List of URLs or domain names
            
        Returns:
            Dict with classification statistics and details
        """
        classifications = []
        stats = {
            'total_sources': len(sources),
            'unique_domains': set(),
            'categories': {},
            'platforms': {},
            'ugc_count': 0,
            'owned_count': 0,
            'competitor_count': 0,
            'authority_count': 0,
            'review_count': 0,
            'ugc_platforms': {},
            'authority_distribution': {'high': 0, 'medium': 0, 'low': 0, 'variable': 0, 'owned': 0},
        }
        
        for source in sources:
            classification = self.classify_domain(source)
            classifications.append(classification)
            
            # Update statistics
            domain = classification['domain']
            if domain:
                stats['unique_domains'].add(domain)
            
            category = classification['category']
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
            
            if classification['platform']:
                platform = classification['platform']
                stats['platforms'][platform] = stats['platforms'].get(platform, 0) + 1
            
            if classification['is_ugc']:
                stats['ugc_count'] += 1
                if classification['platform']:
                    ugc_platform = classification['platform']
                    stats['ugc_platforms'][ugc_platform] = stats['ugc_platforms'].get(ugc_platform, 0) + 1
            
            if classification['is_owned']:
                stats['owned_count'] += 1
            
            if classification['is_competitor']:
                stats['competitor_count'] += 1
            
            if classification['is_authority']:
                stats['authority_count'] += 1
            
            if classification['is_review_site']:
                stats['review_count'] += 1
            
            # Authority score distribution
            auth_score = classification['authority_score']
            stats['authority_distribution'][auth_score] += 1
        
        stats['unique_domains'] = len(stats['unique_domains'])
        
        # Calculate percentages
        if stats['total_sources'] > 0:
            stats['ugc_percentage'] = round(100 * stats['ugc_count'] / stats['total_sources'], 1)
            stats['owned_percentage'] = round(100 * stats['owned_count'] / stats['total_sources'], 1)
            stats['authority_percentage'] = round(100 * stats['authority_count'] / stats['total_sources'], 1)
        else:
            stats['ugc_percentage'] = 0
            stats['owned_percentage'] = 0
            stats['authority_percentage'] = 0
        
        return {
            'classifications': classifications,
            'statistics': stats
        }
    
    def get_domain_trends(self, current_sources: List[str], previous_sources: List[str] = None) -> Dict:
        """
        Calculate domain trends between two sets of sources
        
        Args:
            current_sources: Current list of source URLs
            previous_sources: Previous list of source URLs for comparison
            
        Returns:
            Dict with trend analysis
        """
        current = self.classify_sources(current_sources)
        trends = {
            'current_stats': current['statistics'],
            'changes': {}
        }
        
        if previous_sources:
            previous = self.classify_sources(previous_sources)
            trends['previous_stats'] = previous['statistics']
            
            # Calculate changes
            changes = {}
            
            # UGC trend
            prev_ugc = previous['statistics']['ugc_percentage']
            curr_ugc = current['statistics']['ugc_percentage']
            changes['ugc_change'] = round(curr_ugc - prev_ugc, 1)
            changes['ugc_change_pct'] = round(((curr_ugc - prev_ugc) / prev_ugc * 100) if prev_ugc > 0 else 0, 1)
            
            # Owned content trend
            prev_owned = previous['statistics']['owned_percentage']
            curr_owned = current['statistics']['owned_percentage']
            changes['owned_change'] = round(curr_owned - prev_owned, 1)
            changes['owned_change_pct'] = round(((curr_owned - prev_owned) / prev_owned * 100) if prev_owned > 0 else 0, 1)
            
            # Platform-specific changes
            changes['platform_changes'] = {}
            all_platforms = set(list(current['statistics']['platforms'].keys()) + 
                               list(previous['statistics']['platforms'].keys()))
            
            for platform in all_platforms:
                curr_count = current['statistics']['platforms'].get(platform, 0)
                prev_count = previous['statistics']['platforms'].get(platform, 0)
                if curr_count != prev_count:
                    change = curr_count - prev_count
                    pct_change = round((change / prev_count * 100) if prev_count > 0 else 100, 1)
                    changes['platform_changes'][platform] = {
                        'current': curr_count,
                        'previous': prev_count,
                        'change': change,
                        'change_pct': pct_change
                    }
            
            trends['changes'] = changes
        
        return trends
    
    def identify_ugc_surge(self, sources: List[str], threshold: float = 10.0) -> Dict:
        """
        Identify if there's a surge in UGC content
        
        Args:
            sources: List of source URLs
            threshold: Percentage threshold for UGC content to be considered a surge
            
        Returns:
            Dict with UGC surge analysis
        """
        analysis = self.classify_sources(sources)
        stats = analysis['statistics']
        
        surge_detected = stats['ugc_percentage'] >= threshold
        
        result = {
            'surge_detected': surge_detected,
            'ugc_percentage': stats['ugc_percentage'],
            'threshold': threshold,
            'ugc_platforms': stats['ugc_platforms'],
            'top_ugc_platform': None,
            'recommendations': []
        }
        
        if stats['ugc_platforms']:
            # Find top UGC platform
            top_platform = max(stats['ugc_platforms'].items(), key=lambda x: x[1])
            result['top_ugc_platform'] = {
                'name': top_platform[0],
                'count': top_platform[1],
                'percentage': round(100 * top_platform[1] / stats['ugc_count'], 1) if stats['ugc_count'] > 0 else 0
            }
        
        # Generate recommendations based on UGC presence
        if surge_detected:
            result['recommendations'].append("High UGC presence detected - consider increasing brand monitoring on these platforms")
            result['recommendations'].append("Develop platform-specific response strategies for top UGC sources")
            
            if 'Reddit' in stats['ugc_platforms']:
                result['recommendations'].append("Reddit presence is significant - consider Reddit-specific SEO optimization")
            
            if 'Yelp' in stats['ugc_platforms']:
                result['recommendations'].append("Yelp citations detected - review and respond to Yelp feedback")
        
        return result


def extract_domains_from_response(response_text: str) -> List[str]:
    """
    Helper function to extract all URLs and domains from response text
    
    Args:
        response_text: Text containing URLs
        
    Returns:
        List of extracted URLs/domains
    """
    urls = []
    
    # Pattern for full URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls.extend(re.findall(url_pattern, response_text))
    
    # Pattern for www domains
    www_pattern = r'www\.[^\s<>"{}|\\^`\[\]]+'
    urls.extend(re.findall(www_pattern, response_text))
    
    # Pattern for domain mentions (e.g., "reddit.com")
    domain_pattern = r'\b[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+\b'
    potential_domains = re.findall(domain_pattern, response_text)
    
    # Filter to likely domains
    for domain in potential_domains:
        if any(tld in domain for tld in ['.com', '.org', '.net', '.gov', '.edu', '.io', '.co']):
            if not domain.startswith('http'):
                urls.append(domain)
    
    return list(set(urls))  # Remove duplicates


if __name__ == "__main__":
    # Example usage
    classifier = DomainClassifier(company_domains=['fisherinvestments.com', 'fishercareers.com'])
    
    # Test sources
    test_sources = [
        'https://www.fisherinvestments.com/en-us',
        'https://reddit.com/r/investing/comments/abc123',
        'https://yelp.com/biz/fisher-investments',
        'https://www.wsj.com/articles/fisher-investments',
        'https://www.vanguard.com',
        'https://www.investopedia.com/fisher-review',
        'https://trustpilot.com/review/fisherinvestments.com',
        'bloomberg.com/news/fisher',
    ]
    
    # Classify sources
    results = classifier.classify_sources(test_sources)
    
    print("Classification Results:")
    print(json.dumps(results['statistics'], indent=2))
    
    # Check for UGC surge
    surge = classifier.identify_ugc_surge(test_sources)
    print("\nUGC Surge Analysis:")
    print(json.dumps(surge, indent=2))