#!/usr/bin/env python3
"""
Historical Tracking Module for AI Optimization Intelligence
Tracks and analyzes trends in AI responses over time
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib


class HistoricalTracker:
    """Tracks AI response analysis over time for trend detection"""
    
    def __init__(self, db_path: str = "tracking.db"):
        """
        Initialize the historical tracker
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main analysis history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                provider TEXT NOT NULL,
                response_hash TEXT,
                companies_mentioned TEXT,
                sources_cited TEXT,
                sentiment TEXT,
                negative_signals TEXT,
                domain_stats TEXT,
                ugc_percentage REAL,
                owned_percentage REAL,
                authority_percentage REAL,
                accuracy_issues TEXT,
                full_analysis TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Domain trends table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS domain_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL,
                domain TEXT NOT NULL,
                category TEXT,
                platform TEXT,
                appearance_count INTEGER,
                percentage REAL,
                wow_change REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(week_start, domain)
            )
        ''')
        
        # UGC growth tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ugc_growth (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL,
                platform TEXT NOT NULL,
                mention_count INTEGER,
                percentage REAL,
                wow_change REAL,
                queries_appeared TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(week_start, platform)
            )
        ''')
        
        # Accuracy issues table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accuracy_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                provider TEXT NOT NULL,
                issue_type TEXT,
                incorrect_value TEXT,
                correct_value TEXT,
                description TEXT,
                flagged_status TEXT DEFAULT 'new',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Weekly snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL,
                week_end TEXT NOT NULL,
                total_queries INTEGER,
                total_analyses INTEGER,
                avg_ugc_percentage REAL,
                avg_owned_percentage REAL,
                avg_authority_percentage REAL,
                top_domains TEXT,
                top_ugc_platforms TEXT,
                negative_content_count INTEGER,
                accuracy_issues_count INTEGER,
                summary_stats TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(week_start)
            )
        ''')
        
        # Competitor mentions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                provider TEXT NOT NULL,
                competitor_name TEXT,
                mention_context TEXT,
                sentiment TEXT,
                ranking_position INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_analysis(self, analysis_data: Dict) -> int:
        """
        Store analysis results in the database
        
        Args:
            analysis_data: Complete analysis data from analyzer
            
        Returns:
            int: ID of inserted record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate hash of response for deduplication
        response_text = str(analysis_data.get('response', ''))
        response_hash = hashlib.md5(response_text.encode()).hexdigest()
        
        # Extract key metrics
        domain_stats = analysis_data.get('domain_statistics', {})
        negative_signals = analysis_data.get('negative_signals', {})
        
        cursor.execute('''
            INSERT INTO analysis_history (
                timestamp, query, provider, response_hash,
                companies_mentioned, sources_cited, sentiment,
                negative_signals, domain_stats,
                ugc_percentage, owned_percentage, authority_percentage,
                accuracy_issues, full_analysis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis_data.get('timestamp', datetime.now().isoformat()),
            analysis_data.get('query', ''),
            analysis_data.get('provider', ''),
            response_hash,
            json.dumps(analysis_data.get('companies_mentioned', [])),
            json.dumps(analysis_data.get('sources_cited', [])),
            analysis_data.get('sentiment', 'neutral'),
            json.dumps(negative_signals),
            json.dumps(domain_stats),
            domain_stats.get('ugc_percentage', 0),
            domain_stats.get('owned_percentage', 0),
            domain_stats.get('authority_percentage', 0),
            json.dumps(analysis_data.get('accuracy_issues', [])),
            json.dumps(analysis_data)
        ))
        
        record_id = cursor.lastrowid
        
        # Store competitor mentions if present
        if 'competitor_mentions' in analysis_data:
            for competitor in analysis_data['competitor_mentions']:
                cursor.execute('''
                    INSERT INTO competitor_mentions (
                        timestamp, query, provider, competitor_name,
                        mention_context, sentiment, ranking_position
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_data.get('timestamp'),
                    analysis_data.get('query'),
                    analysis_data.get('provider'),
                    competitor.get('name'),
                    competitor.get('context'),
                    competitor.get('sentiment'),
                    competitor.get('position')
                ))
        
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_week_over_week_changes(self, current_week: str = None) -> Dict:
        """
        Calculate week-over-week changes in key metrics
        
        Args:
            current_week: ISO week string (YYYY-WW), defaults to current week
            
        Returns:
            Dict with WoW changes
        """
        if not current_week:
            current_week = datetime.now().strftime('%Y-W%U')
        
        # Parse week string to get date range
        year, week = current_week.split('-W')
        current_start = datetime.strptime(f'{year} {week} 1', '%Y %U %w')
        previous_start = current_start - timedelta(days=7)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current week stats
        cursor.execute('''
            SELECT 
                AVG(ugc_percentage) as avg_ugc,
                AVG(owned_percentage) as avg_owned,
                AVG(authority_percentage) as avg_authority,
                COUNT(*) as total_analyses
            FROM analysis_history
            WHERE datetime(timestamp) >= ? AND datetime(timestamp) < ?
        ''', (current_start.isoformat(), (current_start + timedelta(days=7)).isoformat()))
        
        current_stats = cursor.fetchone()
        
        # Get previous week stats
        cursor.execute('''
            SELECT 
                AVG(ugc_percentage) as avg_ugc,
                AVG(owned_percentage) as avg_owned,
                AVG(authority_percentage) as avg_authority,
                COUNT(*) as total_analyses
            FROM analysis_history
            WHERE datetime(timestamp) >= ? AND datetime(timestamp) < ?
        ''', (previous_start.isoformat(), current_start.isoformat()))
        
        previous_stats = cursor.fetchone()
        
        conn.close()
        
        # Calculate changes
        changes = {
            'week': current_week,
            'current': {
                'ugc_percentage': current_stats[0] or 0,
                'owned_percentage': current_stats[1] or 0,
                'authority_percentage': current_stats[2] or 0,
                'total_analyses': current_stats[3] or 0
            },
            'previous': {
                'ugc_percentage': previous_stats[0] or 0,
                'owned_percentage': previous_stats[1] or 0,
                'authority_percentage': previous_stats[2] or 0,
                'total_analyses': previous_stats[3] or 0
            },
            'changes': {}
        }
        
        # Calculate percentage changes
        for metric in ['ugc_percentage', 'owned_percentage', 'authority_percentage']:
            current_val = changes['current'][metric]
            previous_val = changes['previous'][metric]
            
            if previous_val > 0:
                pct_change = ((current_val - previous_val) / previous_val) * 100
            else:
                pct_change = 100 if current_val > 0 else 0
            
            changes['changes'][metric] = {
                'absolute': round(current_val - previous_val, 2),
                'percentage': round(pct_change, 2)
            }
        
        return changes
    
    def track_domain_trends(self, week_start: str = None) -> Dict:
        """
        Track domain appearance trends
        
        Args:
            week_start: Start date of the week (YYYY-MM-DD)
            
        Returns:
            Dict with domain trend analysis
        """
        if not week_start:
            # Default to current week's Monday
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        
        week_end = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all domain statistics for the week
        cursor.execute('''
            SELECT domain_stats, sources_cited
            FROM analysis_history
            WHERE date(timestamp) >= ? AND date(timestamp) <= ?
        ''', (week_start, week_end))
        
        results = cursor.fetchall()
        
        # Aggregate domain appearances
        domain_counts = {}
        total_sources = 0
        
        for row in results:
            if row[0]:  # domain_stats
                stats = json.loads(row[0])
                # Process domain statistics
                if 'domain_classifications' in stats:
                    for domain_info in stats['domain_classifications']:
                        domain = domain_info.get('domain', '')
                        if domain:
                            if domain not in domain_counts:
                                domain_counts[domain] = {
                                    'count': 0,
                                    'category': domain_info.get('category', 'unknown'),
                                    'platform': domain_info.get('platform', '')
                                }
                            domain_counts[domain]['count'] += 1
                            total_sources += 1
            
            if row[1]:  # sources_cited
                sources = json.loads(row[1])
                # Extract domains from sources if not already processed
                # (This is a fallback for backward compatibility)
                pass
        
        # Calculate percentages and store in database
        for domain, info in domain_counts.items():
            percentage = (info['count'] / total_sources * 100) if total_sources > 0 else 0
            
            # Get previous week's data for WoW calculation
            previous_week_start = (datetime.strptime(week_start, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT appearance_count, percentage
                FROM domain_trends
                WHERE week_start = ? AND domain = ?
            ''', (previous_week_start, domain))
            
            previous_data = cursor.fetchone()
            wow_change = 0
            if previous_data:
                wow_change = ((info['count'] - previous_data[0]) / previous_data[0] * 100) if previous_data[0] > 0 else 0
            
            # Store or update domain trend
            cursor.execute('''
                INSERT OR REPLACE INTO domain_trends (
                    week_start, domain, category, platform,
                    appearance_count, percentage, wow_change
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                week_start, domain, info['category'], info['platform'],
                info['count'], percentage, wow_change
            ))
        
        conn.commit()
        
        # Get top domains for the week
        cursor.execute('''
            SELECT domain, category, platform, appearance_count, percentage, wow_change
            FROM domain_trends
            WHERE week_start = ?
            ORDER BY appearance_count DESC
            LIMIT 20
        ''', (week_start,))
        
        top_domains = []
        for row in cursor.fetchall():
            top_domains.append({
                'domain': row[0],
                'category': row[1],
                'platform': row[2],
                'count': row[3],
                'percentage': round(row[4], 2),
                'wow_change': round(row[5], 2) if row[5] else 0
            })
        
        conn.close()
        
        return {
            'week_start': week_start,
            'week_end': week_end,
            'total_domains': len(domain_counts),
            'total_sources': total_sources,
            'top_domains': top_domains
        }
    
    def track_ugc_growth(self, week_start: str = None) -> Dict:
        """
        Track UGC platform growth trends
        
        Args:
            week_start: Start date of the week (YYYY-MM-DD)
            
        Returns:
            Dict with UGC growth analysis
        """
        if not week_start:
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        
        week_end = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get UGC platform data for the week
        cursor.execute('''
            SELECT query, domain_stats
            FROM analysis_history
            WHERE date(timestamp) >= ? AND date(timestamp) <= ?
        ''', (week_start, week_end))
        
        results = cursor.fetchall()
        
        # Aggregate UGC platform appearances
        ugc_platforms = {}
        total_ugc_mentions = 0
        
        for row in results:
            query = row[0]
            if row[1]:
                stats = json.loads(row[1])
                if 'ugc_platforms' in stats:
                    for platform, count in stats['ugc_platforms'].items():
                        if platform not in ugc_platforms:
                            ugc_platforms[platform] = {
                                'count': 0,
                                'queries': set()
                            }
                        ugc_platforms[platform]['count'] += count
                        ugc_platforms[platform]['queries'].add(query)
                        total_ugc_mentions += count
        
        # Store UGC growth data
        for platform, info in ugc_platforms.items():
            percentage = (info['count'] / total_ugc_mentions * 100) if total_ugc_mentions > 0 else 0
            
            # Get previous week's data
            previous_week_start = (datetime.strptime(week_start, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT mention_count
                FROM ugc_growth
                WHERE week_start = ? AND platform = ?
            ''', (previous_week_start, platform))
            
            previous_data = cursor.fetchone()
            wow_change = 0
            if previous_data:
                prev_count = previous_data[0]
                if prev_count > 0:
                    wow_change = ((info['count'] - prev_count) / prev_count) * 100
                elif info['count'] > 0:
                    wow_change = 100  # New platform appearance
            
            # Store UGC growth data
            cursor.execute('''
                INSERT OR REPLACE INTO ugc_growth (
                    week_start, platform, mention_count,
                    percentage, wow_change, queries_appeared
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                week_start, platform, info['count'],
                percentage, wow_change,
                json.dumps(list(info['queries']))
            ))
        
        conn.commit()
        
        # Get UGC growth summary
        cursor.execute('''
            SELECT platform, mention_count, percentage, wow_change
            FROM ugc_growth
            WHERE week_start = ?
            ORDER BY mention_count DESC
        ''', (week_start,))
        
        ugc_summary = []
        for row in cursor.fetchall():
            ugc_summary.append({
                'platform': row[0],
                'count': row[1],
                'percentage': round(row[2], 2),
                'wow_change': round(row[3], 2) if row[3] else 0
            })
        
        conn.close()
        
        return {
            'week_start': week_start,
            'week_end': week_end,
            'total_ugc_mentions': total_ugc_mentions,
            'platforms': ugc_summary,
            'platform_count': len(ugc_platforms)
        }
    
    def create_weekly_snapshot(self, week_start: str = None) -> Dict:
        """
        Create a comprehensive weekly snapshot
        
        Args:
            week_start: Start date of the week (YYYY-MM-DD)
            
        Returns:
            Dict with weekly snapshot data
        """
        if not week_start:
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        
        week_end = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
        
        # Get domain trends
        domain_trends = self.track_domain_trends(week_start)
        
        # Get UGC growth
        ugc_growth = self.track_ugc_growth(week_start)
        
        # Get WoW changes
        wow_changes = self.get_week_over_week_changes()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get additional weekly statistics
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT query) as unique_queries,
                COUNT(*) as total_analyses,
                AVG(ugc_percentage) as avg_ugc,
                AVG(owned_percentage) as avg_owned,
                AVG(authority_percentage) as avg_authority
            FROM analysis_history
            WHERE date(timestamp) >= ? AND date(timestamp) <= ?
        ''', (week_start, week_end))
        
        stats = cursor.fetchone()
        
        # Count negative content
        cursor.execute('''
            SELECT COUNT(*)
            FROM analysis_history
            WHERE date(timestamp) >= ? AND date(timestamp) <= ?
            AND negative_signals IS NOT NULL
            AND json_extract(negative_signals, '$.has_negative_content') = 1
        ''', (week_start, week_end))
        
        negative_count = cursor.fetchone()[0]
        
        # Count accuracy issues
        cursor.execute('''
            SELECT COUNT(*)
            FROM accuracy_issues
            WHERE date(timestamp) >= ? AND date(timestamp) <= ?
        ''', (week_start, week_end))
        
        accuracy_issues_count = cursor.fetchone()[0]
        
        # Create summary
        summary = {
            'unique_queries': stats[0],
            'total_analyses': stats[1],
            'avg_ugc_percentage': round(stats[2] or 0, 2),
            'avg_owned_percentage': round(stats[3] or 0, 2),
            'avg_authority_percentage': round(stats[4] or 0, 2),
            'top_domains': domain_trends['top_domains'][:5],
            'top_ugc_platforms': ugc_growth['platforms'][:5],
            'negative_content_count': negative_count,
            'accuracy_issues_count': accuracy_issues_count,
            'wow_changes': wow_changes['changes']
        }
        
        # Store snapshot
        cursor.execute('''
            INSERT OR REPLACE INTO weekly_snapshots (
                week_start, week_end, total_queries, total_analyses,
                avg_ugc_percentage, avg_owned_percentage, avg_authority_percentage,
                top_domains, top_ugc_platforms,
                negative_content_count, accuracy_issues_count,
                summary_stats
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            week_start, week_end,
            summary['unique_queries'], summary['total_analyses'],
            summary['avg_ugc_percentage'], summary['avg_owned_percentage'],
            summary['avg_authority_percentage'],
            json.dumps(summary['top_domains']),
            json.dumps(summary['top_ugc_platforms']),
            summary['negative_content_count'],
            summary['accuracy_issues_count'],
            json.dumps(summary)
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'week_start': week_start,
            'week_end': week_end,
            'summary': summary,
            'domain_trends': domain_trends,
            'ugc_growth': ugc_growth,
            'wow_changes': wow_changes
        }
    
    def get_historical_trends(self, weeks: int = 4) -> List[Dict]:
        """
        Get historical trends for the past N weeks
        
        Args:
            weeks: Number of weeks to retrieve
            
        Returns:
            List of weekly snapshots
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT week_start, summary_stats
            FROM weekly_snapshots
            ORDER BY week_start DESC
            LIMIT ?
        ''', (weeks,))
        
        trends = []
        for row in cursor.fetchall():
            trends.append({
                'week_start': row[0],
                'summary': json.loads(row[1])
            })
        
        conn.close()
        
        return trends
    
    def flag_accuracy_issue(self, issue: Dict) -> int:
        """
        Flag an accuracy issue for tracking
        
        Args:
            issue: Dict with issue details
            
        Returns:
            ID of inserted record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO accuracy_issues (
                timestamp, query, provider, issue_type,
                incorrect_value, correct_value, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            issue.get('timestamp', datetime.now().isoformat()),
            issue.get('query', ''),
            issue.get('provider', ''),
            issue.get('issue_type', ''),
            issue.get('incorrect_value', ''),
            issue.get('correct_value', ''),
            issue.get('description', '')
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id


if __name__ == "__main__":
    # Example usage
    tracker = HistoricalTracker()
    
    # Example analysis data
    sample_analysis = {
        'timestamp': datetime.now().isoformat(),
        'query': 'best investment firms',
        'provider': 'OpenAI',
        'companies_mentioned': ['Vanguard', 'Fidelity', 'Charles Schwab'],
        'sources_cited': ['investopedia.com', 'reddit.com/r/investing', 'wsj.com'],
        'sentiment': 'positive',
        'domain_statistics': {
            'ugc_percentage': 25.0,
            'owned_percentage': 10.0,
            'authority_percentage': 65.0,
            'ugc_platforms': {
                'Reddit': 2,
                'Quora': 1
            }
        }
    }
    
    # Store analysis
    record_id = tracker.store_analysis(sample_analysis)
    print(f"Stored analysis with ID: {record_id}")
    
    # Get WoW changes
    wow = tracker.get_week_over_week_changes()
    print("\nWeek-over-Week Changes:")
    print(json.dumps(wow, indent=2))
    
    # Create weekly snapshot
    snapshot = tracker.create_weekly_snapshot()
    print("\nWeekly Snapshot:")
    print(json.dumps(snapshot, indent=2))