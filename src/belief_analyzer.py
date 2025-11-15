"""
Belief analysis and derived metrics calculation.
Computes various metrics to understand belief systems.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class BeliefAnalyzer:
    """Analyze beliefs and calculate derived metrics."""
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    def analyze(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Perform full analysis on beliefs.
        
        Args:
            df: DataFrame with beliefs
            
        Returns:
            Tuple of (beliefs_with_metrics, summary_stats)
        """
        if df.empty:
            return df, {}
        
        print(f"\n📊 Analyzing beliefs...")
        
        # Calculate all derived metrics
        df_with_metrics = self.calculate_derived_metrics(df)
        
        # Get summary statistics
        summary = self.get_summary_stats(df_with_metrics)
        
        # Identify patterns
        patterns = self.identify_patterns(df_with_metrics)
        summary['patterns'] = patterns
        
        print(f"   ✅ Analysis complete")
        
        return df_with_metrics, summary
    
    def calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all derived metrics for beliefs.
        
        Args:
            df: DataFrame with beliefs
            
        Returns:
            DataFrame with additional metric columns
        """
        result = df.copy()
        
        # Belief Strength = conviction × stability
        result['belief_strength'] = result['conviction_score'] * result['stability_score']
        
        # Foundational Weight = (11 - importance) × conviction
        result['foundational_weight'] = (11 - result['importance']) * result['conviction_score']
        
        # Rigidity Score = conviction × stability × (11 - importance)
        result['rigidity_score'] = (
            result['conviction_score'] * 
            result['stability_score'] * 
            (11 - result['importance'])
        )
        
        # Certainty Gap = conviction - stability
        result['certainty_gap'] = result['conviction_score'] - result['stability_score']
        
        # Influence Score = child_count × conviction
        # Count children for each belief
        child_counts = result['parent_belief_id'].value_counts()
        result['child_count'] = result['belief_id'].map(child_counts).fillna(0)
        result['influence_score'] = result['child_count'] * result['conviction_score']
        
        return result
    
    def get_summary_stats(self, df: pd.DataFrame) -> Dict:
        """
        Get comprehensive summary statistics.
        
        Args:
            df: DataFrame with beliefs and metrics
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_beliefs': len(df),
            'avg_conviction': float(df['conviction_score'].mean()),
            'avg_stability': float(df['stability_score'].mean()),
            'avg_belief_strength': float(df['belief_strength'].mean()),
            'avg_rigidity': float(df['rigidity_score'].mean()),
            
            # By tier
            'beliefs_per_tier': df['tier_name'].value_counts().to_dict(),
            'avg_conviction_per_tier': df.groupby('tier_name')['conviction_score'].mean().to_dict(),
            'avg_stability_per_tier': df.groupby('tier_name')['stability_score'].mean().to_dict(),
            
            # By category
            'beliefs_per_category': df['category'].value_counts().to_dict(),
            'avg_conviction_per_category': df.groupby('category')['conviction_score'].mean().to_dict(),
            
            # By speaker
            'unique_speakers': int(df['speaker_id'].nunique()),
            'beliefs_per_speaker': df['speaker_id'].value_counts().to_dict(),
            
            # Hierarchy
            'root_beliefs': int((df['parent_belief_id'].isna()).sum()),
            'leaf_beliefs': int((~df['belief_id'].isin(df['parent_belief_id'].dropna())).sum()),
            'avg_child_count': float(df['child_count'].mean()),
            
            # Multi-level stats (if applicable)
            'beliefs_per_level': df['discovery_level'].value_counts().to_dict() if 'discovery_level' in df.columns else {},
        }
        
        return stats
    
    def identify_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Identify interesting patterns in belief system.
        
        Args:
            df: DataFrame with beliefs and metrics
            
        Returns:
            Dictionary of identified patterns
        """
        patterns = {}
        
        # Core worldview (foundational beliefs)
        core_worldview = df[
            (df['importance'] <= 3) & 
            (df['stability_score'] > 0.9)
        ]
        patterns['core_worldview_count'] = len(core_worldview)
        patterns['core_worldview_beliefs'] = core_worldview['statement_text'].tolist()[:5]
        
        # Vulnerabilities (high conviction, low stability)
        vulnerabilities = df[
            (df['conviction_score'] > 0.8) & 
            (df['stability_score'] < 0.6)
        ]
        patterns['vulnerable_beliefs_count'] = len(vulnerabilities)
        patterns['vulnerable_beliefs'] = vulnerabilities['statement_text'].tolist()[:5]
        
        # Tribal markers (defines outgroup)
        if 'defines_outgroup' in df.columns:
            tribal = df[df['defines_outgroup'] == True]
            patterns['tribal_markers_count'] = len(tribal)
            patterns['tribal_markers'] = tribal['statement_text'].tolist()[:5]
        
        # Dogmatic beliefs (high conviction in non-foundational)
        dogmatic = df[
            (df['conviction_score'] > 0.9) & 
            (df['importance'] > 5)
        ]
        patterns['dogmatic_beliefs_count'] = len(dogmatic)
        
        # Cognitive dissonance (conflicting beliefs in same domain)
        if len(df) > 1:
            dissonance_count = 0
            for category in df['category'].unique():
                cat_beliefs = df[df['category'] == category]
                if len(cat_beliefs) > 1:
                    conviction_std = cat_beliefs['conviction_score'].std()
                    if conviction_std > 0.3:
                        dissonance_count += 1
            patterns['potential_dissonance_domains'] = dissonance_count
        
        # Dominant domain
        if len(df) > 0:
            dominant_category = df['category'].value_counts().idxmax()
            dominant_percentage = (df['category'].value_counts().max() / len(df)) * 100
            patterns['dominant_domain'] = dominant_category
            patterns['dominant_domain_percentage'] = float(dominant_percentage)
        
        # Rigidity assessment
        high_rigidity = df[df['rigidity_score'] > 7]
        patterns['high_rigidity_count'] = len(high_rigidity)
        patterns['avg_rigidity'] = float(df['rigidity_score'].mean())
        
        # Certainty gap analysis
        large_gap = df[abs(df['certainty_gap']) > 0.3]
        patterns['large_certainty_gap_count'] = len(large_gap)
        
        return patterns
    
    def compare_speakers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compare belief systems across speakers.
        
        Args:
            df: DataFrame with beliefs from multiple speakers
            
        Returns:
            DataFrame with speaker comparison metrics
        """
        if 'speaker_id' not in df.columns or df['speaker_id'].nunique() < 2:
            return pd.DataFrame()
        
        speaker_stats = []
        
        for speaker in df['speaker_id'].unique():
            speaker_df = df[df['speaker_id'] == speaker]
            
            stats = {
                'speaker_id': speaker,
                'total_beliefs': len(speaker_df),
                'avg_conviction': speaker_df['conviction_score'].mean(),
                'avg_stability': speaker_df['stability_score'].mean(),
                'avg_rigidity': speaker_df['rigidity_score'].mean(),
                'core_beliefs': len(speaker_df[speaker_df['importance'] <= 3]),
                'dominant_category': speaker_df['category'].value_counts().idxmax(),
                'tribal_markers': len(speaker_df[speaker_df.get('defines_outgroup', False) == True])
            }
            
            speaker_stats.append(stats)
        
        return pd.DataFrame(speaker_stats)
    
    def find_keystone_beliefs(self, df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
        """
        Identify keystone beliefs (high influence, foundational).
        
        Args:
            df: DataFrame with beliefs and metrics
            top_n: Number of top beliefs to return
            
        Returns:
            DataFrame with top keystone beliefs
        """
        # Sort by influence score and foundational weight
        df_sorted = df.sort_values(
            ['influence_score', 'foundational_weight'],
            ascending=[False, False]
        )
        
        return df_sorted.head(top_n)[[
            'belief_id', 'statement_text', 'tier_name', 
            'conviction_score', 'stability_score',
            'influence_score', 'child_count'
        ]]
    
    def detect_cognitive_dissonance(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect potential cognitive dissonance patterns.
        
        Args:
            df: DataFrame with beliefs
            
        Returns:
            List of dissonance patterns
        """
        dissonance_patterns = []
        
        # Check each category for conflicting high-conviction beliefs
        for category in df['category'].unique():
            cat_beliefs = df[
                (df['category'] == category) & 
                (df['conviction_score'] > 0.7)
            ]
            
            if len(cat_beliefs) > 1:
                # Calculate conviction variance
                conviction_std = cat_beliefs['conviction_score'].std()
                
                if conviction_std > 0.2:
                    dissonance_patterns.append({
                        'category': category,
                        'belief_count': len(cat_beliefs),
                        'conviction_std': float(conviction_std),
                        'beliefs': cat_beliefs['statement_text'].tolist()
                    })
        
        return dissonance_patterns
    
    def export_metrics(self, df: pd.DataFrame, output_path: str):
        """
        Export beliefs with all metrics to CSV.
        
        Args:
            df: DataFrame with beliefs and metrics
            output_path: Path to save CSV
        """
        df.to_csv(output_path, index=False)
        print(f"💾 Exported metrics to {output_path}")

