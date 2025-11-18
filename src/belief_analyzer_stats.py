"""
Advanced statistical analysis utilities for belief matrices.
Calculates distributions, correlations, outliers, and content metrics
that will be logged to Weights & Biases.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


def _safe_corr(series_a: pd.Series, series_b: pd.Series) -> Optional[float]:
    """Return Pearson correlation if both series have >1 non-null values."""
    if series_a is None or series_b is None:
        return None
    if series_a.count() < 2 or series_b.count() < 2:
        return None
    try:
        corr = series_a.corr(series_b)
        if pd.isna(corr):
            return None
        return float(round(corr, 4))
    except Exception:
        return None


def _value_percentages(series: pd.Series) -> Dict[str, Any]:
    """Return counts and percentages for a categorical series."""
    if series is None or series.empty:
        return {'counts': {}, 'percentages': {}}

    counts = series.value_counts()
    total = counts.sum() if counts.sum() else 1
    percents = (counts / total * 100).round(2)
    return {
        'counts': counts.to_dict(),
        'percentages': percents.to_dict()
    }


@dataclass
class BeliefStatsAnalyzer:
    """
    Performs advanced statistical analysis on belief matrices.
    Intended to feed rich metrics into W&B dashboards and HTML reports.
    """

    min_statement_length: int = 40  # characters considered “long”

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run the full suite of statistical analyses."""
        if df is None or df.empty:
            return {}

        df = df.copy()
        self._ensure_metric_columns(df)

        return {
            'distributions': self._compute_distributions(df),
            'score_statistics': self._compute_score_statistics(df),
            'correlations': self._compute_correlations(df),
            'outliers': self._detect_outliers(df),
            'content_metrics': self._analyze_content(df),
            'multi_level': self._analyze_multilevel(df),
            'speaker_profiles': self._analyze_speakers(df)
        }

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _ensure_metric_columns(self, df: pd.DataFrame) -> None:
        """Guarantee derived metric columns exist for downstream stats."""
        if 'sub_domain' not in df.columns:
            df['sub_domain'] = 'general'
        else:
            df['sub_domain'] = df['sub_domain'].fillna('general')
        if 'belief_strength' not in df.columns:
            df['belief_strength'] = df['conviction_score'] * df['stability_score']

        if 'rigidity_score' not in df.columns:
            df['rigidity_score'] = (
                df['conviction_score'] *
                df['stability_score'] *
                (11 - df['importance'])
            )

        if 'certainty_gap' not in df.columns:
            df['certainty_gap'] = df['conviction_score'] - df['stability_score']

        if 'statement_text' in df.columns and 'statement_length' not in df.columns:
            df['statement_length'] = df['statement_text'].astype(str).str.len()

    def _compute_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate categorical distributions and their percentages."""
        distributions = {}

        for column in [
            'tier_name',
            'category',
            'sub_domain',
            'speaker_id',
            'certainty',
            'discovery_level'
        ]:
            if column in df.columns:
                distributions[column] = _value_percentages(df[column])

        # Importance (tier number) bucketed into high/mid/low
        importance_bins = pd.cut(
            df['importance'],
            bins=[0, 3, 7, 10],
            labels=['core (1-3)', 'mid (4-7)', 'surface (8-10)'],
            include_lowest=True
        )
        distributions['importance_band'] = _value_percentages(importance_bins)

        return distributions

    def _compute_score_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Aggregate summary statistics for numeric columns."""
        metrics: Dict[str, Any] = {}
        numeric_columns = [
            'conviction_score',
            'stability_score',
            'belief_strength',
            'rigidity_score',
            'certainty_gap',
            'statement_length'
        ]

        for column in numeric_columns:
            if column not in df.columns:
                continue

            series = df[column].dropna()
            if series.empty:
                continue

            metrics[column] = {
                'mean': float(round(series.mean(), 4)),
                'median': float(round(series.median(), 4)),
                'std': float(round(series.std(ddof=0), 4)) if len(series) > 1 else 0.0,
                'min': float(round(series.min(), 4)),
                'max': float(round(series.max(), 4)),
                'quartiles': {
                    'q25': float(round(series.quantile(0.25), 4)),
                    'q50': float(round(series.quantile(0.50), 4)),
                    'q75': float(round(series.quantile(0.75), 4))
                }
            }

        return metrics

    def _compute_correlations(self, df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """Compute key pairwise correlations."""
        correlations = {
            'conviction_vs_stability': _safe_corr(
                df['conviction_score'], df['stability_score']
            ),
            'importance_vs_conviction': _safe_corr(
                df['importance'], df['conviction_score']
            ),
            'importance_vs_stability': _safe_corr(
                df['importance'], df['stability_score']
            ),
            'statement_length_vs_conviction': _safe_corr(
                df.get('statement_length'), df['conviction_score']
            ),
            'statement_length_vs_stability': _safe_corr(
                df.get('statement_length'), df['stability_score']
            ),
            'stability_vs_belief_strength': _safe_corr(
                df['stability_score'], df['belief_strength']
            )
        }

        if 'discovery_level' in df.columns:
            correlations['discovery_level_vs_conviction'] = _safe_corr(
                df['discovery_level'], df['conviction_score']
            )

        return correlations

    def _detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify notable outliers for dashboards."""
        outliers: Dict[str, Any] = {}

        def _serialize(rows: pd.DataFrame, cols: List[str], limit: int = 5):
            if rows.empty:
                return []
            return rows[cols].head(limit).to_dict(orient='records')

        # Extreme conviction / stability
        high_conviction = df[df['conviction_score'] >= 0.95]
        low_stability = df[df['stability_score'] <= 0.3]

        outliers['high_conviction'] = _serialize(
            high_conviction.sort_values('conviction_score', ascending=False),
            ['belief_id', 'statement_text', 'conviction_score', 'tier_name']
        )

        outliers['low_stability'] = _serialize(
            low_stability.sort_values('stability_score'),
            ['belief_id', 'statement_text', 'stability_score', 'tier_name']
        )

        # Large certainty gap (|conviction - stability| > 0.4)
        large_gap = df[abs(df['certainty_gap']) > 0.4]
        outliers['large_certainty_gap'] = _serialize(
            large_gap.assign(
                certainty_gap=large_gap['certainty_gap'].abs()
            ).sort_values('certainty_gap', ascending=False),
            ['belief_id', 'statement_text', 'certainty_gap', 'tier_name']
        )

        # Long statements
        if 'statement_length' in df.columns:
            long_statements = df[df['statement_length'] >= self.min_statement_length]
            outliers['long_statements'] = _serialize(
                long_statements.sort_values('statement_length', ascending=False),
                ['belief_id', 'statement_text', 'statement_length', 'tier_name']
            )

        return outliers

    def _analyze_content(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze textual characteristics."""
        if 'statement_text' not in df.columns:
            return {}

        statement_lengths = df['statement_text'].astype(str).str.len()
        avg_length = float(round(statement_lengths.mean(), 2))
        median_length = float(round(statement_lengths.median(), 2))

        # Vocabulary richness (unique words / total words)
        token_counts = df['statement_text'].astype(str).str.split().apply(len)
        total_words = token_counts.sum()
        unique_words = len(set(' '.join(df['statement_text'].astype(str)).split()))
        vocab_richness = float(round(unique_words / total_words, 4)) if total_words else 0.0

        # Hedged vs binary certainty ratio
        certainty_stats = {}
        if 'certainty' in df.columns:
            certainty_stats = _value_percentages(df['certainty'])

        return {
            'avg_statement_length': avg_length,
            'median_statement_length': median_length,
            'vocabulary_richness': vocab_richness,
            'avg_words_per_statement': float(round(token_counts.mean(), 2)),
            'certainty_distribution': certainty_stats
        }

    def _analyze_multilevel(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze reinforcement across multi-level extraction."""
        if 'discovery_level' not in df.columns:
            return {}

        stats: Dict[str, Any] = {
            'level_distribution': _value_percentages(df['discovery_level'])
        }

        if 'reinforcement_count' in df.columns:
            stats['reinforcement_stats'] = {
                'avg_reinforcement': float(round(df['reinforcement_count'].mean(), 2)),
                'max_reinforcement': int(df['reinforcement_count'].max()),
                'multi_level_beliefs': int((df['reinforcement_count'] > 1).sum())
            }

        return stats

    def _analyze_speakers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Summaries per speaker to highlight dominant voices."""
        if 'speaker_id' not in df.columns:
            return {}

        speaker_stats = []
        for speaker in df['speaker_id'].unique():
            speaker_df = df[df['speaker_id'] == speaker]
            speaker_stats.append({
                'speaker_id': speaker,
                'belief_count': int(len(speaker_df)),
                'avg_conviction': float(round(speaker_df['conviction_score'].mean(), 3)),
                'avg_stability': float(round(speaker_df['stability_score'].mean(), 3)),
                'dominant_category': speaker_df['category'].value_counts().idxmax(),
                'dominant_sub_domain': (
                    speaker_df['sub_domain'].value_counts().idxmax()
                    if 'sub_domain' in speaker_df.columns and speaker_df['sub_domain'].notna().any()
                    else None
                ),
                'core_belief_ratio': float(round(
                    len(speaker_df[speaker_df['importance'] <= 3]) / len(speaker_df),
                    3
                ))
            })

        return {
            'speaker_summary': speaker_stats,
            'speaker_distribution': _value_percentages(df['speaker_id'])
        }


