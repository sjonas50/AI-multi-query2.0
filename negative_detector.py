#!/usr/bin/env python3
"""
Negative Signal Detection Module for AI Optimization Intelligence
Identifies and categorizes negative content patterns in AI responses
"""

import re
from typing import Dict, List, Tuple, Optional
import json


class NegativeSignalDetector:
    """Detects and categorizes negative signals in AI-generated content"""
    
    def __init__(self, company_name: str = "Fisher Investments"):
        """
        Initialize the negative signal detector
        
        Args:
            company_name: Name of the company to track negative signals for
        """
        self.company_name = company_name
        self.company_variations = self._generate_company_variations(company_name)
        
        # Define negative signal categories and patterns
        self.negative_patterns = {
            'aggressive_sales': {
                'keywords': [
                    'aggressive', 'pushy', 'persistent', 'relentless', 'hard-sell',
                    'high-pressure', 'annoying', 'harassing', 'spam', 'cold call',
                    'telemarketing', 'won\'t stop calling', 'excessive calls',
                    'sales tactics', 'marketing tactics', 'pushy sales'
                ],
                'phrases': [
                    'aggressive sales', 'pushy sales tactics', 'high pressure sales',
                    'relentless marketing', 'persistent calls', 'aggressive marketing',
                    'hard sell tactics', 'won\'t take no', 'excessive marketing'
                ],
                'severity': 'high'
            },
            'high_fees': {
                'keywords': [
                    'expensive', 'costly', 'overpriced', 'high fee', 'excessive fee',
                    'overcharge', 'not worth', 'too much', 'premium pricing'
                ],
                'phrases': [
                    'high fees', 'expensive fees', 'fees are high', 'higher than',
                    'more expensive than', 'not worth the fee', 'excessive charges',
                    'premium for', 'costs more than'
                ],
                'severity': 'medium'
            },
            'poor_performance': {
                'keywords': [
                    'underperform', 'poor return', 'lost money', 'losses', 'disappointing',
                    'below average', 'mediocre', 'subpar', 'poor results', 'bad performance'
                ],
                'phrases': [
                    'poor performance', 'underperforming', 'didn\'t meet expectations',
                    'lost money', 'significant losses', 'below benchmark',
                    'disappointing returns', 'poor results', 'failed to deliver'
                ],
                'severity': 'high'
            },
            'lawsuits': {
                'keywords': [
                    'lawsuit', 'sued', 'litigation', 'legal action', 'court case',
                    'class action', 'settlement', 'allegations', 'charges', 'investigation'
                ],
                'phrases': [
                    'filed lawsuit', 'legal issues', 'breach of fiduciary',
                    'elder abuse', 'SEC investigation', 'regulatory issues',
                    'class action lawsuit', 'legal troubles', 'sued for'
                ],
                'severity': 'critical'
            },
            'controversies': {
                'keywords': [
                    'controversy', 'scandal', 'controversial', 'backlash', 'criticism',
                    'inappropriate', 'offensive', 'disparaging', 'sexist', 'discriminatory'
                ],
                'phrases': [
                    'controversial remarks', 'faced criticism', 'drew backlash',
                    'inappropriate comments', 'offensive statements', 'controversy in',
                    'criticized for', 'under fire', 'negative publicity'
                ],
                'severity': 'high'
            },
            'poor_service': {
                'keywords': [
                    'unresponsive', 'poor service', 'bad service', 'ignored', 'difficult',
                    'unhelpful', 'incompetent', 'unprofessional', 'rude', 'dismissive'
                ],
                'phrases': [
                    'poor customer service', 'hard to reach', 'won\'t respond',
                    'ignored requests', 'difficult to work with', 'lack of communication',
                    'poor communication', 'unresponsive advisor', 'bad experience'
                ],
                'severity': 'medium'
            },
            'trust_issues': {
                'keywords': [
                    'scam', 'fraud', 'dishonest', 'misleading', 'deceptive', 'unethical',
                    'shady', 'suspicious', 'untrustworthy', 'ripoff', 'scheme'
                ],
                'phrases': [
                    'not trustworthy', 'can\'t trust', 'misleading claims',
                    'deceptive practices', 'bait and switch', 'not transparent',
                    'hidden fees', 'conflicts of interest', 'breach of trust'
                ],
                'severity': 'critical'
            },
            'generic_negative': {
                'keywords': [
                    'complaint', 'problem', 'issue', 'concern', 'negative', 'bad',
                    'poor', 'worst', 'terrible', 'horrible', 'awful', 'avoid'
                ],
                'phrases': [
                    'mixed reviews', 'negative reviews', 'complaints about',
                    'problems with', 'issues with', 'concerns about',
                    'not recommended', 'look elsewhere', 'better alternatives'
                ],
                'severity': 'low'
            }
        }
        
        # Contextual modifiers that can affect severity
        self.modifiers = {
            'amplifiers': ['very', 'extremely', 'highly', 'particularly', 'especially', 'notably'],
            'mitigators': ['somewhat', 'slightly', 'minor', 'small', 'occasional', 'some'],
            'reported': ['allegedly', 'reportedly', 'claimed', 'accused', 'some say', 'critics say'],
            'past': ['was', 'were', 'had', 'used to', 'previously', 'historically', 'in the past']
        }
        
        # Common misattributions to watch for
        self.misattribution_patterns = [
            r'Fisher\s+Capital',  # Different company
            r'Fisher\s+Asset\s+Management',  # Different company
            r'Fisher\s+Brothers',  # Different company
            r'Fisher\s+Funds',  # Different company
        ]
    
    def _generate_company_variations(self, company_name: str) -> List[str]:
        """Generate variations of company name for matching"""
        base_name = company_name.lower()
        variations = [
            base_name,
            base_name.replace(' ', ''),
            base_name.replace(' investments', ''),
        ]
        
        # Add possessive forms
        variations.extend([v + "'s" for v in variations])
        variations.extend([v + "'" for v in variations])
        
        return variations
    
    def detect_negative_signals(self, text: str) -> Dict:
        """
        Detect negative signals in text
        
        Args:
            text: Text to analyze for negative signals
            
        Returns:
            Dict with detected negative signals and analysis
        """
        text_lower = text.lower()
        results = {
            'has_negative_content': False,
            'categories_detected': [],
            'signals': [],
            'severity_score': 0,
            'misattribution_detected': False,
            'specific_issues': [],
            'contextual_factors': [],
            'recommendations': []
        }
        
        # Check for misattributions first
        for pattern in self.misattribution_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                results['misattribution_detected'] = True
                results['specific_issues'].append(f"Possible misattribution: {pattern}")
        
        # Check each negative category
        for category, patterns in self.negative_patterns.items():
            category_found = False
            category_signals = []
            
            # Check keywords
            for keyword in patterns['keywords']:
                if keyword in text_lower:
                    # Check if it's about the target company
                    if self._is_about_company(text_lower, keyword):
                        category_found = True
                        category_signals.append(keyword)
            
            # Check phrases
            for phrase in patterns['phrases']:
                if phrase in text_lower:
                    if self._is_about_company(text_lower, phrase):
                        category_found = True
                        category_signals.append(phrase)
            
            if category_found:
                results['has_negative_content'] = True
                results['categories_detected'].append(category)
                
                signal_entry = {
                    'category': category,
                    'severity': patterns['severity'],
                    'signals_found': list(set(category_signals)),
                    'count': len(category_signals)
                }
                results['signals'].append(signal_entry)
                
                # Add to severity score
                severity_multiplier = {
                    'critical': 5,
                    'high': 3,
                    'medium': 2,
                    'low': 1
                }
                results['severity_score'] += severity_multiplier.get(patterns['severity'], 1) * len(category_signals)
        
        # Check for contextual modifiers
        for modifier_type, modifiers in self.modifiers.items():
            for modifier in modifiers:
                if modifier in text_lower:
                    results['contextual_factors'].append({
                        'type': modifier_type,
                        'modifier': modifier
                    })
        
        # Extract specific issues mentioned
        results['specific_issues'].extend(self._extract_specific_issues(text))
        
        # Generate recommendations based on findings
        if results['has_negative_content']:
            results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _is_about_company(self, text: str, near_text: str) -> bool:
        """
        Check if negative signal is about the target company
        
        Args:
            text: Full text to search
            near_text: Text near which to look for company mention
            
        Returns:
            bool indicating if the negative signal is about the company
        """
        # Simple proximity check - look for company name within 100 characters
        for variation in self.company_variations:
            pattern = rf'{variation}.{{0,100}}{re.escape(near_text)}|{re.escape(near_text)}.{{0,100}}{variation}'
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _extract_specific_issues(self, text: str) -> List[str]:
        """Extract specific issues mentioned in the text"""
        issues = []
        
        # Pattern for year mentions (potential lawsuit/controversy dates)
        year_pattern = r'\b(20\d{2}|19\d{2})\b.{0,50}(?:lawsuit|controversy|investigation|comments?|remarks?)'
        year_matches = re.findall(year_pattern, text, re.IGNORECASE)
        for match in year_matches:
            issues.append(f"Event mentioned from {match}")
        
        # Pattern for specific monetary amounts (fees, losses, etc.)
        money_pattern = r'\$[\d,]+(?:\.\d{2})?|\d+(?:\.\d+)?%\s*(?:fee|loss|charge|cost)'
        money_matches = re.findall(money_pattern, text, re.IGNORECASE)
        for match in money_matches:
            issues.append(f"Specific amount mentioned: {match}")
        
        # Pattern for regulatory bodies
        regulatory_pattern = r'\b(?:SEC|FINRA|DOJ|FTC|CFPB)\b'
        regulatory_matches = re.findall(regulatory_pattern, text)
        for match in regulatory_matches:
            issues.append(f"Regulatory body mentioned: {match}")
        
        return issues
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on detected negative signals"""
        recommendations = []
        
        categories = results.get('categories_detected', [])
        
        if 'aggressive_sales' in categories:
            recommendations.append("Address sales tactics perception - consider publishing sales philosophy and client testimonials")
        
        if 'high_fees' in categories:
            recommendations.append("Clarify fee structure and value proposition - highlight services included in fees")
        
        if 'poor_performance' in categories:
            recommendations.append("Provide transparent performance data with appropriate benchmarks and time horizons")
        
        if 'lawsuits' in categories:
            recommendations.append("Monitor legal mentions for accuracy - consider creating factual clarification content")
        
        if 'controversies' in categories:
            recommendations.append("Develop crisis communication strategy - emphasize current values and improvements")
        
        if 'poor_service' in categories:
            recommendations.append("Showcase client success stories and service improvements")
        
        if 'trust_issues' in categories:
            recommendations.append("Enhance transparency initiatives - publish more educational content about processes")
        
        if results.get('misattribution_detected'):
            recommendations.append("Create clear differentiation content to prevent confusion with other companies")
        
        # Severity-based recommendations
        if results.get('severity_score', 0) > 10:
            recommendations.append("HIGH PRIORITY: Significant negative signals detected - consider reputation management campaign")
        elif results.get('severity_score', 0) > 5:
            recommendations.append("MEDIUM PRIORITY: Monitor and address negative themes proactively")
        
        return recommendations
    
    def analyze_sentiment_by_entity(self, text: str, entities: List[str]) -> Dict:
        """
        Analyze sentiment for specific entities mentioned in text
        
        Args:
            text: Text to analyze
            entities: List of entities to analyze sentiment for
            
        Returns:
            Dict with sentiment analysis per entity
        """
        results = {}
        
        for entity in entities:
            entity_lower = entity.lower()
            results[entity] = {
                'mentioned': False,
                'sentiment': 'neutral',
                'negative_signals': [],
                'positive_signals': [],
                'context': []
            }
            
            # Find sentences mentioning the entity
            sentences = text.split('.')
            for sentence in sentences:
                if entity_lower in sentence.lower():
                    results[entity]['mentioned'] = True
                    results[entity]['context'].append(sentence.strip())
                    
                    # Check for negative signals in this sentence
                    sentence_lower = sentence.lower()
                    for category, patterns in self.negative_patterns.items():
                        for keyword in patterns['keywords']:
                            if keyword in sentence_lower:
                                results[entity]['negative_signals'].append(keyword)
                    
                    # Check for positive signals
                    positive_keywords = [
                        'excellent', 'great', 'outstanding', 'trusted', 'reliable',
                        'professional', 'helpful', 'satisfied', 'recommended', 'best'
                    ]
                    for keyword in positive_keywords:
                        if keyword in sentence_lower:
                            results[entity]['positive_signals'].append(keyword)
            
            # Determine overall sentiment
            neg_count = len(results[entity]['negative_signals'])
            pos_count = len(results[entity]['positive_signals'])
            
            if neg_count > pos_count:
                results[entity]['sentiment'] = 'negative'
            elif pos_count > neg_count:
                results[entity]['sentiment'] = 'positive'
            else:
                results[entity]['sentiment'] = 'neutral'
        
        return results
    
    def check_accuracy_issues(self, text: str, facts_to_verify: Dict) -> Dict:
        """
        Check for potential accuracy issues in text
        
        Args:
            text: Text to check for accuracy
            facts_to_verify: Dict of facts to verify (e.g., {'minimum_investment': '$1,000,000'})
            
        Returns:
            Dict with accuracy check results
        """
        results = {
            'accuracy_issues_found': False,
            'issues': [],
            'corrections_needed': []
        }
        
        # Check minimum investment accuracy
        if 'minimum_investment' in facts_to_verify:
            correct_minimum = facts_to_verify['minimum_investment']
            
            # Look for minimum investment mentions
            min_patterns = [
                r'\$\d+(?:,\d{3})*(?:\s*(?:k|K|thousand|million|M))?(?:\s*minimum)?',
                r'minimum\s*(?:of\s*)?\$\d+(?:,\d{3})*',
                r'at\s*least\s*\$\d+(?:,\d{3})*',
                r'requires?\s*\$\d+(?:,\d{3})*'
            ]
            
            for pattern in min_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if correct_minimum not in match:
                        results['accuracy_issues_found'] = True
                        results['issues'].append({
                            'type': 'incorrect_minimum',
                            'found': match,
                            'correct': correct_minimum
                        })
                        results['corrections_needed'].append(
                            f"Incorrect minimum investment: Found '{match}', should be '{correct_minimum}'"
                        )
        
        # Check for date accuracy (e.g., 2019 comments being called lawsuits)
        date_lawsuit_pattern = r'(20\d{2})\s*(?:comments?|remarks?|statements?).{0,50}lawsuit'
        date_matches = re.findall(date_lawsuit_pattern, text, re.IGNORECASE)
        for year in date_matches:
            results['accuracy_issues_found'] = True
            results['issues'].append({
                'type': 'mischaracterization',
                'description': f'{year} comments incorrectly characterized as lawsuits'
            })
            results['corrections_needed'].append(
                f"Mischaracterization: {year} comments should not be described as lawsuits"
            )
        
        return results


def calculate_negative_score(negative_signals: Dict) -> int:
    """
    Calculate an overall negative score based on detected signals
    
    Args:
        negative_signals: Output from detect_negative_signals
        
    Returns:
        int score (0-100, higher is more negative)
    """
    base_score = negative_signals.get('severity_score', 0)
    
    # Adjust for contextual factors
    for factor in negative_signals.get('contextual_factors', []):
        if factor['type'] == 'amplifiers':
            base_score *= 1.2
        elif factor['type'] == 'mitigators':
            base_score *= 0.8
        elif factor['type'] == 'reported':
            base_score *= 0.9
        elif factor['type'] == 'past':
            base_score *= 0.7
    
    # Cap at 100
    return min(int(base_score), 100)


if __name__ == "__main__":
    # Example usage
    detector = NegativeSignalDetector("Fisher Investments")
    
    # Test text with various negative signals
    test_text = """
    Fisher Investments has received mixed reviews from clients. Some praise their 
    personalized service, while others complain about aggressive sales tactics and 
    persistent marketing calls. The firm charges higher fees than many competitors, 
    typically around 1.25% to 1.5% annually. In 2019, founder Ken Fisher made 
    controversial comments that led to criticism and some clients withdrawing funds.
    Some clients report poor performance and feel the high fees aren't justified.
    The company requires a minimum investment of $500,000, though some sources 
    incorrectly state it's $250,000.
    """
    
    # Detect negative signals
    results = detector.detect_negative_signals(test_text)
    print("Negative Signal Detection Results:")
    print(json.dumps(results, indent=2))
    
    # Check accuracy
    facts = {'minimum_investment': '$1,000,000'}
    accuracy = detector.check_accuracy_issues(test_text, facts)
    print("\nAccuracy Check Results:")
    print(json.dumps(accuracy, indent=2))
    
    # Analyze sentiment by entity
    entities = ['Fisher Investments', 'Ken Fisher', 'Vanguard']
    sentiment = detector.analyze_sentiment_by_entity(test_text, entities)
    print("\nSentiment by Entity:")
    print(json.dumps(sentiment, indent=2))
    
    # Calculate negative score
    score = calculate_negative_score(results)
    print(f"\nOverall Negative Score: {score}/100")