"""
Automatic insight generation from belief analysis.
Generates natural language insights about belief systems.
"""
import pandas as pd
from typing import Dict, List
from datetime import datetime


class InsightGenerator:
    """Generate natural language insights from belief data."""
    
    def __init__(self):
        """Initialize insight generator."""
        pass
    
    def generate_report(self, df: pd.DataFrame, 
                       summary_stats: Dict,
                       centrality_metrics: pd.DataFrame = None) -> str:
        """
        Generate comprehensive insight report.
        
        Args:
            df: DataFrame with beliefs and metrics
            summary_stats: Summary statistics dictionary
            centrality_metrics: Optional centrality metrics from graph analysis
            
        Returns:
            Markdown formatted report
        """
        print(f"\n📝 Generating insights...")
        
        sections = []
        
        # Header
        sections.append(self._generate_header(summary_stats))
        
        # Core findings
        sections.append(self._generate_core_findings(df, summary_stats))
        
        # Belief distribution
        sections.append(self._generate_distribution_insights(df, summary_stats))
        
        # Strength and rigidity
        sections.append(self._generate_strength_insights(df))
        
        # Patterns
        if 'patterns' in summary_stats:
            sections.append(self._generate_pattern_insights(summary_stats['patterns']))
        
        # Hierarchy insights
        sections.append(self._generate_hierarchy_insights(df, summary_stats))
        
        # Keystone beliefs
        if centrality_metrics is not None and not centrality_metrics.empty:
            sections.append(self._generate_keystone_insights(centrality_metrics))
        
        # Recommendations
        sections.append(self._generate_recommendations(df, summary_stats))
        
        report = "\n\n".join(sections)
        
        print(f"   ✅ Generated {len(sections)} insight sections")
        
        return report
    
    def _generate_header(self, summary_stats: Dict) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""# 🎙️ Belief Matrix Analysis Report

**Generated**: {timestamp}  
**Total Beliefs**: {summary_stats.get('total_beliefs', 0)}  
**Unique Speakers**: {summary_stats.get('unique_speakers', 0)}

---
"""
    
    def _generate_core_findings(self, df: pd.DataFrame, stats: Dict) -> str:
        """Generate core findings section."""
        avg_conviction = stats.get('avg_conviction', 0)
        avg_stability = stats.get('avg_stability', 0)
        
        # Interpret conviction level
        if avg_conviction > 0.8:
            conviction_desc = "**very strong** - speaker shows high certainty across beliefs"
        elif avg_conviction > 0.6:
            conviction_desc = "**moderately strong** - speaker generally confident"
        else:
            conviction_desc = "**tentative** - speaker shows uncertainty or flexibility"
        
        # Interpret stability
        if avg_stability > 0.8:
            stability_desc = "**highly stable** - beliefs are deeply rooted and long-term"
        elif avg_stability > 0.6:
            stability_desc = "**moderately stable** - beliefs are somewhat consistent"
        else:
            stability_desc = "**fluid** - beliefs may change frequently"
        
        return f"""## 🎯 Core Findings

### Overall Conviction: {avg_conviction:.2f}
The speaker's average conviction is {conviction_desc}.

### Overall Stability: {avg_stability:.2f}
The belief system appears {stability_desc}.

### Belief Strength: {stats.get('avg_belief_strength', 0):.2f}
Combined conviction and stability suggests a {self._interpret_strength(stats.get('avg_belief_strength', 0))} belief system.
"""
    
    def _generate_distribution_insights(self, df: pd.DataFrame, stats: Dict) -> str:
        """Generate distribution insights."""
        beliefs_per_tier = stats.get('beliefs_per_tier', {})
        beliefs_per_category = stats.get('beliefs_per_category', {})
        
        # Find dominant tier
        dominant_tier = max(beliefs_per_tier, key=beliefs_per_tier.get) if beliefs_per_tier else "Unknown"
        dominant_tier_count = beliefs_per_tier.get(dominant_tier, 0)
        dominant_tier_pct = (dominant_tier_count / stats.get('total_beliefs', 1)) * 100
        
        # Find dominant category
        dominant_category = max(beliefs_per_category, key=beliefs_per_category.get) if beliefs_per_category else "Unknown"
        dominant_category_count = beliefs_per_category.get(dominant_category, 0)
        dominant_category_pct = (dominant_category_count / stats.get('total_beliefs', 1)) * 100
        
        tier_distribution = "\n".join([
            f"- **{tier}**: {count} beliefs ({count/stats.get('total_beliefs',1)*100:.1f}%)"
            for tier, count in sorted(beliefs_per_tier.items(), key=lambda x: x[1], reverse=True)[:5]
        ])
        
        category_distribution = "\n".join([
            f"- **{cat.capitalize()}**: {count} beliefs ({count/stats.get('total_beliefs',1)*100:.1f}%)"
            for cat, count in sorted(beliefs_per_category.items(), key=lambda x: x[1], reverse=True)[:5]
        ])
        
        return f"""## 📊 Belief Distribution

### By Tier
The most common belief tier is **{dominant_tier}** ({dominant_tier_pct:.1f}% of beliefs).

{tier_distribution}

**Interpretation**: {self._interpret_tier_distribution(dominant_tier, dominant_tier_pct)}

### By Category
The dominant domain is **{dominant_category}** ({dominant_category_pct:.1f}% of beliefs).

{category_distribution}

**Interpretation**: {self._interpret_category_focus(dominant_category, dominant_category_pct)}
"""
    
    def _generate_strength_insights(self, df: pd.DataFrame) -> str:
        """Generate strength and rigidity insights."""
        avg_rigidity = df['rigidity_score'].mean()
        
        # Find most rigid beliefs
        top_rigid = df.nlargest(3, 'rigidity_score')[['statement_text', 'rigidity_score']]
        rigid_list = "\n".join([
            f"{i+1}. \"{row['statement_text'][:80]}...\" (rigidity: {row['rigidity_score']:.2f})"
            for i, (_, row) in enumerate(top_rigid.iterrows())
        ])
        
        # Find vulnerabilities (high conviction, low stability)
        vulnerabilities = df[
            (df['conviction_score'] > 0.8) & 
            (df['stability_score'] < 0.6)
        ]
        
        vuln_section = ""
        if len(vulnerabilities) > 0:
            vuln_list = "\n".join([
                f"- \"{row['statement_text'][:80]}...\" (conviction: {row['conviction_score']:.2f}, stability: {row['stability_score']:.2f})"
                for _, row in vulnerabilities.head(3).iterrows()
            ])
            vuln_section = f"""
### ⚠️ Vulnerable Beliefs
{len(vulnerabilities)} beliefs show high conviction but low stability (potentially unstable):

{vuln_list}

**Implication**: These beliefs are strongly held now but may be susceptible to change.
"""
        
        return f"""## 💪 Strength & Rigidity

### Average Rigidity: {avg_rigidity:.2f}
{self._interpret_rigidity(avg_rigidity)}

### Most Rigid Beliefs
{rigid_list}

{vuln_section}
"""
    
    def _generate_pattern_insights(self, patterns: Dict) -> str:
        """Generate pattern insights."""
        sections = []
        
        # Core worldview
        core_count = patterns.get('core_worldview_count', 0)
        if core_count > 0:
            core_beliefs = patterns.get('core_worldview_beliefs', [])
            core_list = "\n".join([f"- \"{b}\"" for b in core_beliefs[:3]])
            sections.append(f"""### 🏛️ Core Worldview ({core_count} beliefs)
{core_list}

**Significance**: These foundational beliefs shape everything else.""")
        
        # Tribal markers
        tribal_count = patterns.get('tribal_markers_count', 0)
        if tribal_count > 0:
            sections.append(f"""### 🎭 Tribal Identity ({tribal_count} beliefs)
{tribal_count} beliefs define in-group vs out-group boundaries.

**Implication**: Strong tribal identity - these beliefs mark social belonging.""")
        
        # Cognitive dissonance
        dissonance_domains = patterns.get('potential_dissonance_domains', 0)
        if dissonance_domains > 0:
            sections.append(f"""### ⚡ Cognitive Dissonance
Detected conflicting beliefs in {dissonance_domains} domains.

**Implication**: Potential internal contradictions that may cause psychological tension.""")
        
        # Domain focus
        dominant_domain = patterns.get('dominant_domain', '')
        dominant_pct = patterns.get('dominant_domain_percentage', 0)
        if dominant_domain:
            sections.append(f"""### 🎯 Domain Focus
{dominant_pct:.1f}% of beliefs are about **{dominant_domain}**.

**Interpretation**: This is the primary area of intellectual/ideological focus.""")
        
        return f"""## 🔍 Patterns & Insights

{chr(10).join(sections)}
"""
    
    def _generate_hierarchy_insights(self, df: pd.DataFrame, stats: Dict) -> str:
        """Generate hierarchy insights."""
        root_count = stats.get('root_beliefs', 0)
        leaf_count = stats.get('leaf_beliefs', 0)
        avg_children = stats.get('avg_child_count', 0)
        
        # Interpret hierarchy structure
        if root_count < 5:
            structure = "**tightly organized** - few foundational axioms support everything else"
        elif root_count < 10:
            structure = "**moderately organized** - several independent belief clusters"
        else:
            structure = "**loosely organized** - many independent beliefs without clear hierarchy"
        
        return f"""## 🌳 Hierarchical Structure

- **Root Beliefs**: {root_count} (foundational, no parents)
- **Leaf Beliefs**: {leaf_count} (no children, concrete conclusions)
- **Avg Children per Belief**: {avg_children:.2f}

**Structure**: The belief system is {structure}.
"""
    
    def _generate_keystone_insights(self, centrality_df: pd.DataFrame) -> str:
        """Generate keystone belief insights."""
        top_keystone = centrality_df.nlargest(5, 'pagerank')
        
        keystone_list = "\n".join([
            f"{i+1}. \"{row['statement'][:80]}...\" ({row['tier']}, PageRank: {row['pagerank']:.3f})"
            for i, (_, row) in enumerate(top_keystone.iterrows())
        ])
        
        return f"""## 🔑 Keystone Beliefs

These beliefs have the highest influence in the belief network:

{keystone_list}

**Significance**: Challenging these beliefs would destabilize many dependent beliefs.
"""
    
    def _generate_recommendations(self, df: pd.DataFrame, stats: Dict) -> str:
        """Generate recommendations."""
        recommendations = []
        
        # Based on rigidity
        avg_rigidity = df['rigidity_score'].mean()
        if avg_rigidity > 7:
            recommendations.append("- **High Rigidity Detected**: Consider exploring beliefs that contradict strongly-held assumptions to reduce dogmatism.")
        
        # Based on vulnerabilities
        vulnerabilities = len(df[(df['conviction_score'] > 0.8) & (df['stability_score'] < 0.6)])
        if vulnerabilities > 3:
            recommendations.append(f"- **{vulnerabilities} Vulnerable Beliefs**: Examine why these strongly-held beliefs have low stability.")
        
        # Based on hierarchy
        root_count = stats.get('root_beliefs', 0)
        if root_count > 10:
            recommendations.append("- **Fragmented Hierarchy**: Consider identifying deeper axioms that unify independent belief clusters.")
        
        # Based on dissonance
        if 'patterns' in stats:
            dissonance = stats['patterns'].get('potential_dissonance_domains', 0)
            if dissonance > 0:
                recommendations.append(f"- **Cognitive Dissonance in {dissonance} Domains**: Resolve conflicting beliefs to reduce psychological tension.")
        
        if not recommendations:
            recommendations.append("- **Well-Integrated System**: Beliefs appear coherent and internally consistent.")
        
        return f"""## 💡 Recommendations

{chr(10).join(recommendations)}
"""
    
    # Helper interpretation methods
    
    def _interpret_strength(self, strength: float) -> str:
        if strength > 0.75:
            return "robust and well-defended"
        elif strength > 0.5:
            return "moderately strong"
        else:
            return "weak or exploratory"
    
    def _interpret_tier_distribution(self, dominant_tier: str, pct: float) -> str:
        if "Core" in dominant_tier or "Worldview" in dominant_tier:
            return "Focus on foundational principles - philosophical thinker"
        elif "Domain" in dominant_tier or "Claims" in dominant_tier:
            return "Focus on specific domains - practical orientation"
        else:
            return "Mixed focus across abstraction levels"
    
    def _interpret_category_focus(self, category: str, pct: float) -> str:
        interpretations = {
            'epistemic': "Focus on knowledge and truth - epistemologically-minded",
            'moral': "Focus on ethics and values - morally-driven thinking",
            'political': "Focus on power and systems - politically-oriented",
            'tech': "Focus on technology - technologically-engaged",
            'economic': "Focus on markets and resources - economically-minded",
        }
        return interpretations.get(category, f"Primary intellectual focus is {category}")
    
    def _interpret_rigidity(self, rigidity: float) -> str:
        if rigidity > 7:
            return "**High rigidity** - strong resistance to belief change, potential dogmatism"
        elif rigidity > 4:
            return "**Moderate rigidity** - balanced between conviction and flexibility"
        else:
            return "**Low rigidity** - open to belief revision and new evidence"
    
    def export_report(self, report: str, output_path: str):
        """
        Export report to markdown file.
        
        Args:
            report: Report text
            output_path: Path to save report
        """
        with open(output_path, 'w') as f:
            f.write(report)
        
        print(f"💾 Exported report to {output_path}")

