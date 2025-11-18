"""
Utilities to convert belief matrices into ForceAtlas2-ready graph data.
The resulting payload is consumed by the interactive HTML dashboard (Sigma.js).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import networkx as nx


CATEGORY_COLORS = {
    'political': '#FF6B6B',
    'economic': '#FFA94D',
    'moral': '#FFD43B',
    'epistemic': '#69DB7C',
    'tech': '#4DABF7',
    'health': '#B197FC',
    'spiritual': '#FF92C2',
    'social': '#828282',
    'bitcoin': '#FFB347',
    'finance': '#FFD166',
    'other': '#ADB5BD'
}

TIER_ORDER = [
    'Core Axioms',
    'Worldview Pillars',
    'Identity-Defining Values',
    'Meta-Principles',
    'Cross-Domain Rules & Heuristics',
    'Stable Domain Beliefs',
    'Repeated Strategies & Playbooks',
    'Concrete Claims & Predictions',
    'Situational Opinions',
    'Loose Takes / Jokes / Vibes'
]


@dataclass
class ForceAtlas2Generator:
    """Build ForceAtlas2 graph payloads from belief matrices."""

    max_nodes: int = 500
    color_palette: Dict[str, str] = field(default_factory=lambda: CATEGORY_COLORS.copy())

    def build_graph_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return dict with nodes/edges ready for Sigma.js + ForceAtlas2."""
        if df is None or df.empty:
            return {'nodes': [], 'edges': [], 'stats': {}}

        df = self._prepare_dataframe(df)
        graph = self._build_networkx_graph(df)
        positions = self._compute_positions(graph)

        nodes = [self._build_node(row, positions) for _, row in df.iterrows()]
        edges = self._build_edges(df)

        payload = {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'category_counts': df['category'].value_counts().to_dict(),
                'sub_domain_counts': df['sub_domain'].value_counts().to_dict() if 'sub_domain' in df.columns else {},
                'tier_counts': df['tier_name'].value_counts().to_dict()
            }
        }
        return payload

    def export_json(self, df: pd.DataFrame, output_path: str) -> Path:
        """Persist graph data as JSON for the dashboard."""
        data = self.build_graph_data(df)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        return path

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sort and trim dataframe to the maximum node limit."""
        df = df.copy()

        # Determine ranking for trimming: prioritize foundational & high conviction
        df['node_rank'] = (
            (11 - df.get('importance', 10)) * 2 +
            df.get('conviction_score', 0)
        )
        df = df.sort_values('node_rank', ascending=False).head(self.max_nodes)
        df['tier_order'] = df['tier_name'].apply(lambda tier: TIER_ORDER.index(tier) if tier in TIER_ORDER else 99)

        # Ensure textual columns exist
        if 'atomic_belief' not in df.columns:
            df['atomic_belief'] = ''
        if 'certainty' not in df.columns:
            df['certainty'] = ''

        return df

    def _build_node(self, row: pd.Series, positions: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single belief row into a graph node."""
        label = row.get('atomic_belief') or row.get('statement_text') or row['belief_id']
        label = str(label).strip()
        if len(label) > 180:
            label = label[:177] + '...'

        size = self._compute_node_size(
            conviction=row.get('conviction_score', 0),
            importance=row.get('importance', 10)
        )

        color = self.color_palette.get(row.get('category', ''), '#CED4DA')

        return {
            'id': row['belief_id'],
            'label': label,
            'tier': row.get('tier_name', ''),
            'tier_order': row.get('tier_order', 99),
            'category': row.get('category', ''),
            'sub_domain': row.get('sub_domain', ''),
            'importance': int(row.get('importance', 10)),
            'conviction': float(row.get('conviction_score', 0)),
            'stability': float(row.get('stability_score', 0)),
            'certainty': row.get('certainty', ''),
            'speaker': row.get('speaker_id', ''),
            'discovery_level': int(row.get('discovery_level', 0)) if pd.notna(row.get('discovery_level', None)) else None,
            'size': size,
            'color': color,
            'x': positions.get(row['belief_id'], {}).get('x', 0),
            'y': positions.get(row['belief_id'], {}).get('y', 0)
        }

    def _build_edges(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Create edges from parent-child relationships."""
        edges: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            parent_id = row.get('parent_belief_id')
            if pd.isna(parent_id) or not parent_id:
                continue
            # Only include edge if parent also in trimmed node set
            if parent_id not in df['belief_id'].values:
                continue
            edges.append({
                'id': f"{parent_id}->{row['belief_id']}",
                'source': parent_id,
                'target': row['belief_id'],
                'weight': float(row.get('conviction_score', 0)),
                'category': row.get('category', '')
            })
        return edges

    @staticmethod
    def _compute_node_size(conviction: float, importance: float) -> float:
        """Scale node size based on conviction and tier importance."""
        base = max(1, 11 - importance)
        size = 4 + base + (conviction * 4)
        return round(size, 2)

    def _build_networkx_graph(self, df: pd.DataFrame) -> nx.Graph:
        """Create an undirected graph for layout computation."""
        G = nx.Graph()
        for _, row in df.iterrows():
            G.add_node(row['belief_id'])
        for _, row in df.iterrows():
            parent_id = row.get('parent_belief_id')
            if pd.notna(parent_id) and parent_id in G:
                G.add_edge(row['belief_id'], parent_id, weight=row.get('conviction_score', 0.5))
        if G.number_of_edges() == 0:
            # Add minimal edges to keep layout stable
            nodes = list(G.nodes())
            for i in range(len(nodes) - 1):
                G.add_edge(nodes[i], nodes[i + 1], weight=0.1)
        return G

    def _compute_positions(self, graph: nx.Graph) -> Dict[str, Dict[str, float]]:
        """Compute 2D positions using spring layout."""
        if graph.number_of_nodes() == 0:
            return {}
        layout = nx.spring_layout(graph, k=None, iterations=200, seed=42, weight='weight')
        return {node: {'x': float(pos[0]), 'y': float(pos[1])} for node, pos in layout.items()}


