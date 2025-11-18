"""
Graph-level analytics for belief hierarchies.
Produces summary dictionaries that can be logged to W&B or rendered in dashboards.
"""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from .belief_graph import BeliefGraph


class BeliefGraphMetrics:
    """Compute graph statistics and centrality summaries for beliefs."""

    def analyze(self, df: pd.DataFrame, top_n: int = 5) -> Dict[str, Any]:
        """Build the graph and return aggregate metrics."""
        if df is None or df.empty:
            return {}

        graph_builder = BeliefGraph()
        graph_builder.build_graph(df)

        metrics: Dict[str, Any] = {
            'graph_stats': graph_builder.get_graph_stats()
        }

        centrality_df = graph_builder.calculate_centrality_metrics()
        metrics['centrality'] = self._summarize_centrality(centrality_df, top_n)

        communities = graph_builder.detect_communities()
        metrics['communities'] = self._summarize_communities(communities)

        metrics['keystone_beliefs'] = graph_builder.find_keystone_beliefs(top_n)

        return metrics

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _summarize_centrality(self, df: pd.DataFrame, top_n: int) -> Dict[str, Any]:
        """Return top nodes for key centrality measures."""
        if df.empty:
            return {}

        def _top_records(column: str) -> List[Dict[str, Any]]:
            if column not in df.columns:
                return []
            return (df.nlargest(top_n, column)[
                ['belief_id', 'statement', column, 'tier']
            ].to_dict(orient='records'))

        return {
            'top_pagerank': _top_records('pagerank'),
            'top_betweenness': _top_records('betweenness_centrality'),
            'top_degree': _top_records('degree_centrality'),
            'average_degree': float(round(df['degree_centrality'].mean(), 4)),
            'average_betweenness': float(round(df['betweenness_centrality'].mean(), 4))
        }

    def _summarize_communities(self, community_map: Dict[str, int]) -> Dict[str, Any]:
        """Summaries of detected communities (clusters)."""
        if not community_map:
            return {}

        community_series = pd.Series(community_map, name='community')
        counts = community_series.value_counts().sort_values(ascending=False)
        return {
            'total_communities': int(counts.size),
            'community_sizes': counts.to_dict(),
            'largest_community_size': int(counts.max())
        }


