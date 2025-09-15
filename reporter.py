#!/usr/bin/env python3
"""
Reporting Module for AI Optimization Intelligence
Generates Fisher Investments-style weekly reports and insights
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import csv


class WeeklyReporter:
    """Generates comprehensive weekly reports for AI optimization tracking"""
    
    def __init__(self, reports_dir: str = "reports"):
        """
        Initialize the reporter
        
        Args:
            reports_dir: Directory to save reports
        """
        self.reports_dir = reports_dir
        self._ensure_reports_dir()
    
    def _ensure_reports_dir(self):
        """Create reports directory if it doesn't exist"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def generate_weekly_report(self, snapshot_data: Dict, company_name: str = "Fisher Investments") -> str:
        """
        Generate a Fisher Investments-style weekly report
        
        Args:
            snapshot_data: Weekly snapshot data from tracker
            company_name: Name of the company being tracked
            
        Returns:
            Path to generated report file
        """
        week_start = snapshot_data.get('week_start', '')
        week_end = snapshot_data.get('week_end', '')
        summary = snapshot_data.get('summary', {})
        domain_trends = snapshot_data.get('domain_trends', {})
        ugc_growth = snapshot_data.get('ugc_growth', {})
        wow_changes = snapshot_data.get('wow_changes', {})
        
        # Generate report filename
        report_date = datetime.now().strftime('%Y%m%d')
        report_filename = f"ai_overview_report_{report_date}.md"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        # Build report content
        report_lines = []
        report_lines.append(f"# AI Overview Weekly Report - {company_name}")
        report_lines.append(f"**Week of {week_start} to {week_end}**")
        report_lines.append(f"**Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**\n")
        
        # Key Takeaways Section
        report_lines.append("## Key Takeaways This Week\n")
        report_lines.extend(self._generate_key_takeaways(summary, wow_changes))
        
        # Weekly Statistics Section
        report_lines.append("\n## Weekly Statistics\n")
        report_lines.append(f"- **Total Queries Analyzed:** {summary.get('total_analyses', 0)}")
        report_lines.append(f"- **Unique Queries:** {summary.get('unique_queries', 0)}")
        report_lines.append(f"- **Negative Content Detected:** {summary.get('negative_content_count', 0)} instances")
        report_lines.append(f"- **Accuracy Issues Flagged:** {summary.get('accuracy_issues_count', 0)} issues\n")
        
        # UGC Sites Section
        report_lines.append("### User Generated Content (UGC) Sites\n")
        if ugc_growth.get('platforms'):
            for platform in ugc_growth['platforms'][:10]:  # Top 10 platforms
                report_lines.append(f"**{platform['platform']}** appeared {platform['count']} times "
                                  f"({platform['percentage']}% of UGC)")
                if platform['wow_change'] != 0:
                    change_str = f"+{platform['wow_change']}%" if platform['wow_change'] > 0 else f"{platform['wow_change']}%"
                    report_lines.append(f"  - Week-over-Week Change: {change_str}")
        else:
            report_lines.append("No UGC platforms detected this week.")
        
        # Domain Distribution Section
        report_lines.append("\n### Domain Distribution\n")
        report_lines.append(f"- **Average UGC Percentage:** {summary.get('avg_ugc_percentage', 0)}%")
        report_lines.append(f"- **Average Owned Content:** {summary.get('avg_owned_percentage', 0)}%")
        report_lines.append(f"- **Average Authority Sites:** {summary.get('avg_authority_percentage', 0)}%\n")
        
        # Top Domains Section
        report_lines.append("### Top Domains This Week\n")
        if domain_trends.get('top_domains'):
            report_lines.append("| Domain | Category | Appearances | % of Total | WoW Change |")
            report_lines.append("|--------|----------|-------------|------------|------------|")
            for domain in domain_trends['top_domains'][:15]:  # Top 15 domains
                wow_str = f"+{domain['wow_change']}%" if domain['wow_change'] > 0 else f"{domain['wow_change']}%"
                report_lines.append(f"| {domain['domain']} | {domain['category']} | "
                                  f"{domain['count']} | {domain['percentage']}% | {wow_str} |")
        
        # Week-over-Week Changes Section
        report_lines.append("\n## Week-over-Week Trends\n")
        if wow_changes.get('changes'):
            changes = wow_changes['changes']
            for metric, change_data in changes.items():
                metric_name = metric.replace('_', ' ').title()
                abs_change = change_data['absolute']
                pct_change = change_data['percentage']
                
                direction = "📈" if abs_change > 0 else "📉" if abs_change < 0 else "➡️"
                report_lines.append(f"{direction} **{metric_name}:** {abs_change:+.1f}% ({pct_change:+.1f}% change)")
        
        # Recommendations Section
        report_lines.append("\n## Optimization Recommendations\n")
        recommendations = self._generate_recommendations(summary, wow_changes, ugc_growth)
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        
        # Flagged AI Overviews Section
        if summary.get('accuracy_issues_count', 0) > 0:
            report_lines.append(f"\n## Flagged AI Overviews\n")
            report_lines.append(f"**{summary['accuracy_issues_count']} AI Overviews flagged for accuracy issues**\n")
            report_lines.append("Common issues detected:")
            report_lines.append("- Incorrect minimum investment amounts")
            report_lines.append("- Mischaracterization of events (e.g., comments as lawsuits)")
            report_lines.append("- Attribution to wrong companies\n")
        
        # Write report to file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"[OK] Weekly report generated: {report_path}")
        
        # Also generate CSV summary
        csv_path = self._generate_csv_summary(snapshot_data)
        
        return report_path
    
    def _generate_key_takeaways(self, summary: Dict, wow_changes: Dict) -> List[str]:
        """Generate key takeaways based on data trends"""
        takeaways = []
        
        # Check UGC trend
        if 'ugc_percentage' in wow_changes.get('changes', {}):
            ugc_change = wow_changes['changes']['ugc_percentage']['percentage']
            if ugc_change > 50:
                takeaways.append(f"⚠️ **Significant UGC Growth:** User-generated content increased by {ugc_change:.1f}% "
                               "week-over-week, indicating a shift in AI source preferences.")
            elif ugc_change > 20:
                takeaways.append(f"📈 **UGC Trending Up:** {ugc_change:.1f}% increase in user-generated content citations.")
        
        # Check owned content trend
        if 'owned_percentage' in wow_changes.get('changes', {}):
            owned_change = wow_changes['changes']['owned_percentage']['percentage']
            if owned_change < -20:
                takeaways.append(f"📉 **Owned Content Declining:** Company-owned content visibility decreased by "
                               f"{abs(owned_change):.1f}%, suggesting need for content optimization.")
        
        # Check negative content
        neg_count = summary.get('negative_content_count', 0)
        if neg_count > 10:
            takeaways.append(f"⚠️ **High Negative Content:** {neg_count} instances of negative content detected, "
                           "requiring reputation management attention.")
        
        # Check accuracy issues
        accuracy_issues = summary.get('accuracy_issues_count', 0)
        if accuracy_issues > 5:
            takeaways.append(f"🔍 **Accuracy Concerns:** {accuracy_issues} accuracy issues flagged, "
                           "particularly around minimum investment amounts and historical events.")
        
        # Check top UGC platforms
        if summary.get('top_ugc_platforms'):
            top_platform = summary['top_ugc_platforms'][0]
            if top_platform['count'] > 10:
                takeaways.append(f"💬 **{top_platform['platform']} Dominance:** {top_platform['platform']} "
                               f"appeared {top_platform['count']} times, representing {top_platform['percentage']}% "
                               "of UGC citations.")
        
        if not takeaways:
            takeaways.append("✅ No significant changes detected this week. AI Overview presence remains stable.")
        
        return takeaways
    
    def _generate_recommendations(self, summary: Dict, wow_changes: Dict, ugc_growth: Dict) -> List[str]:
        """Generate actionable recommendations based on trends"""
        recommendations = []
        
        # UGC-based recommendations
        avg_ugc = summary.get('avg_ugc_percentage', 0)
        if avg_ugc > 15:
            recommendations.append("**Increase UGC Engagement:** With UGC content representing "
                                 f"{avg_ugc:.1f}% of citations, develop platform-specific response strategies "
                                 "for Reddit, Yelp, and other community sites.")
        
        # Owned content recommendations
        avg_owned = summary.get('avg_owned_percentage', 0)
        if avg_owned < 30:
            recommendations.append("**Boost Owned Content Authority:** Owned content is underrepresented at "
                                 f"{avg_owned:.1f}%. Consider creating more authoritative, AI-optimized content "
                                 "targeting common queries.")
        
        # Platform-specific recommendations
        if ugc_growth.get('platforms'):
            for platform in ugc_growth['platforms'][:3]:  # Top 3 platforms
                if platform['platform'] == 'Reddit' and platform['count'] > 5:
                    recommendations.append(f"**Reddit Strategy Required:** With {platform['count']} Reddit citations, "
                                         "consider active participation in relevant subreddits and AMA sessions.")
                elif platform['platform'] == 'Yelp' and platform['count'] > 5:
                    recommendations.append(f"**Yelp Review Management:** {platform['count']} Yelp citations detected. "
                                         "Implement review response protocol and encourage satisfied clients to share experiences.")
        
        # Negative content recommendations
        if summary.get('negative_content_count', 0) > 5:
            recommendations.append("**Address Negative Themes:** Create content addressing common criticisms "
                                 "and misconceptions to provide balanced perspective in AI responses.")
        
        # Accuracy recommendations
        if summary.get('accuracy_issues_count', 0) > 0:
            recommendations.append("**Fact Correction Campaign:** Deploy structured data and authoritative content "
                                 "to correct recurring accuracy issues, particularly around fees and minimum investments.")
        
        # Competitive recommendations
        if avg_owned < avg_ugc:
            recommendations.append("**Competitive Content Gap:** UGC is outpacing owned content. "
                                 "Analyze competitor strategies that achieve better AI Overview placement.")
        
        return recommendations
    
    def _generate_csv_summary(self, snapshot_data: Dict) -> str:
        """Generate CSV summary of weekly data"""
        week_start = snapshot_data.get('week_start', '')
        csv_filename = f"weekly_summary_{week_start.replace('-', '')}.csv"
        csv_path = os.path.join(self.reports_dir, csv_filename)
        
        summary = snapshot_data.get('summary', {})
        domain_trends = snapshot_data.get('domain_trends', {})
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write headers and summary data
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Week Start', week_start])
            writer.writerow(['Total Analyses', summary.get('total_analyses', 0)])
            writer.writerow(['Unique Queries', summary.get('unique_queries', 0)])
            writer.writerow(['Avg UGC %', summary.get('avg_ugc_percentage', 0)])
            writer.writerow(['Avg Owned %', summary.get('avg_owned_percentage', 0)])
            writer.writerow(['Avg Authority %', summary.get('avg_authority_percentage', 0)])
            writer.writerow(['Negative Content Count', summary.get('negative_content_count', 0)])
            writer.writerow(['Accuracy Issues', summary.get('accuracy_issues_count', 0)])
            writer.writerow([])
            
            # Write domain data
            writer.writerow(['Domain', 'Category', 'Count', 'Percentage', 'WoW Change'])
            for domain in domain_trends.get('top_domains', [])[:20]:
                writer.writerow([
                    domain['domain'],
                    domain['category'],
                    domain['count'],
                    domain['percentage'],
                    domain['wow_change']
                ])
        
        return csv_path
    
    def generate_comparison_report(self, weeks_data: List[Dict]) -> str:
        """
        Generate a multi-week comparison report
        
        Args:
            weeks_data: List of weekly snapshot data
            
        Returns:
            Path to generated report
        """
        report_date = datetime.now().strftime('%Y%m%d')
        report_filename = f"ai_overview_trend_report_{report_date}.md"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        report_lines = []
        report_lines.append("# AI Overview Trend Analysis Report")
        report_lines.append(f"**Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**\n")
        
        # Trend Summary
        report_lines.append("## Multi-Week Trend Summary\n")
        
        # Create trend table
        report_lines.append("| Week | UGC % | Owned % | Authority % | Negative Count | Accuracy Issues |")
        report_lines.append("|------|-------|---------|-------------|----------------|-----------------|")
        
        for week_data in weeks_data:
            week = week_data.get('week_start', '')
            summary = week_data.get('summary', {})
            report_lines.append(f"| {week} | {summary.get('avg_ugc_percentage', 0):.1f}% | "
                              f"{summary.get('avg_owned_percentage', 0):.1f}% | "
                              f"{summary.get('avg_authority_percentage', 0):.1f}% | "
                              f"{summary.get('negative_content_count', 0)} | "
                              f"{summary.get('accuracy_issues_count', 0)} |")
        
        # Identify trends
        report_lines.append("\n## Trend Analysis\n")
        
        if len(weeks_data) >= 2:
            # Calculate overall trends
            first_week = weeks_data[-1]['summary']
            last_week = weeks_data[0]['summary']
            
            ugc_trend = last_week.get('avg_ugc_percentage', 0) - first_week.get('avg_ugc_percentage', 0)
            owned_trend = last_week.get('avg_owned_percentage', 0) - first_week.get('avg_owned_percentage', 0)
            
            if ugc_trend > 5:
                report_lines.append(f"📈 **UGC Growing:** {ugc_trend:.1f}% increase over {len(weeks_data)} weeks")
            if owned_trend < -5:
                report_lines.append(f"📉 **Owned Content Declining:** {owned_trend:.1f}% decrease over {len(weeks_data)} weeks")
        
        # Write report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        return report_path


class InsightsGenerator:
    """Generate actionable insights from AI response analysis"""
    
    @staticmethod
    def generate_aiseo_insights(analysis_data: Dict) -> List[str]:
        """
        Generate AISEO optimization insights from analysis
        
        Args:
            analysis_data: Complete analysis data
            
        Returns:
            List of actionable insights
        """
        insights = []
        
        # Domain-based insights
        if 'domain_statistics' in analysis_data:
            stats = analysis_data['domain_statistics']
            
            if stats.get('ugc_percentage', 0) > 20:
                insights.append("High UGC presence - Create authoritative content to compete with community discussions")
            
            if stats.get('owned_percentage', 0) < 25:
                insights.append("Low owned content visibility - Optimize existing content for AI extraction")
            
            if stats.get('authority_percentage', 0) > 50:
                insights.append("Authority sites dominate - Build relationships with key publications for mentions")
        
        # Negative signal insights
        if 'negative_signals' in analysis_data:
            neg = analysis_data['negative_signals']
            
            if neg.get('has_negative_content'):
                categories = neg.get('categories_detected', [])
                if 'aggressive_sales' in categories:
                    insights.append("Address sales perception - Publish content about consultative approach")
                if 'high_fees' in categories:
                    insights.append("Clarify value proposition - Create fee transparency content")
                if 'lawsuits' in categories:
                    insights.append("Monitor legal mentions - Ensure accurate representation of any legal matters")
        
        # Competitor insights
        if 'competitor_mentions' in analysis_data:
            comp_count = len(analysis_data['competitor_mentions'])
            if comp_count > 3:
                insights.append(f"Multiple competitors mentioned ({comp_count}) - Differentiate with unique value props")
        
        # Source diversity insights
        if 'sources_cited' in analysis_data:
            sources = analysis_data['sources_cited']
            if len(sources) < 3:
                insights.append("Limited source diversity - Increase brand presence across multiple platforms")
            if len(sources) > 10:
                insights.append("High source diversity - Focus on top-performing channels for optimization")
        
        return insights


if __name__ == "__main__":
    # Example usage
    reporter = WeeklyReporter()
    
    # Sample snapshot data
    sample_snapshot = {
        'week_start': '2024-01-08',
        'week_end': '2024-01-14',
        'summary': {
            'total_analyses': 150,
            'unique_queries': 45,
            'avg_ugc_percentage': 18.5,
            'avg_owned_percentage': 28.3,
            'avg_authority_percentage': 53.2,
            'negative_content_count': 12,
            'accuracy_issues_count': 3,
            'top_domains': [
                {'domain': 'reddit.com', 'category': 'ugc', 'count': 25, 'percentage': 8.2, 'wow_change': 340},
                {'domain': 'investopedia.com', 'category': 'authority', 'count': 18, 'percentage': 5.9, 'wow_change': -5}
            ],
            'top_ugc_platforms': [
                {'platform': 'Reddit', 'count': 25, 'percentage': 45.5, 'wow_change': 340},
                {'platform': 'Yelp', 'count': 15, 'percentage': 27.3, 'wow_change': 0}
            ]
        },
        'domain_trends': {
            'top_domains': [
                {'domain': 'reddit.com', 'category': 'ugc', 'count': 25, 'percentage': 8.2, 'wow_change': 340}
            ]
        },
        'ugc_growth': {
            'platforms': [
                {'platform': 'Reddit', 'count': 25, 'percentage': 45.5, 'wow_change': 340}
            ]
        },
        'wow_changes': {
            'changes': {
                'ugc_percentage': {'absolute': 5.2, 'percentage': 39.1},
                'owned_percentage': {'absolute': -3.1, 'percentage': -9.9}
            }
        }
    }
    
    # Generate report
    report_path = reporter.generate_weekly_report(sample_snapshot)
    print(f"Report generated: {report_path}")