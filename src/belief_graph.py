"""
Belief graph construction and analysis using NetworkX.
Build and analyze hierarchical belief networks.
"""
import pandas as pd
import networkx as nx
import json
from typing import Dict, List, Tuple
from pathlib import Path


class BeliefGraph:
    """Build and analyze belief graphs."""
    
    def __init__(self):
        """Initialize graph builder."""
        self.graph = None
        
    def build_graph(self, df: pd.DataFrame) -> nx.DiGraph:
        """
        Build directed graph from belief relationships.
        
        Args:
            df: DataFrame with beliefs and parent_belief_id
            
        Returns:
            NetworkX directed graph
        """
        print(f"\n🕸️  Building belief graph...")
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add nodes (beliefs)
        for _, belief in df.iterrows():
            G.add_node(
                belief['belief_id'],
                statement=belief['statement_text'],
                tier=belief['tier_name'],
                importance=int(belief['importance']),
                conviction=float(belief['conviction_score']),
                stability=float(belief['stability_score']),
                category=belief['category']
            )
        
        # Add edges (parent-child relationships)
        edge_count = 0
        for _, belief in df.iterrows():
            if pd.notna(belief['parent_belief_id']):
                # Edge from parent to child
                G.add_edge(
                    belief['parent_belief_id'],
                    belief['belief_id'],
                    weight=float(belief['conviction_score'])
                )
                edge_count += 1
        
        self.graph = G
        
        print(f"   Nodes: {G.number_of_nodes()}")
        print(f"   Edges: {G.number_of_edges()}")
        print(f"   Connected components: {nx.number_weakly_connected_components(G)}")
        
        return G
    
    def calculate_centrality_metrics(self) -> pd.DataFrame:
        """
        Calculate centrality metrics for all nodes.
        
        Returns:
            DataFrame with centrality metrics
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_graph() first.")
        
        metrics = []
        
        # Calculate various centrality measures
        degree_centrality = nx.degree_centrality(self.graph)
        in_degree_centrality = nx.in_degree_centrality(self.graph)
        out_degree_centrality = nx.out_degree_centrality(self.graph)
        
        # Betweenness centrality (how often node is on shortest path)
        try:
            betweenness = nx.betweenness_centrality(self.graph)
        except:
            betweenness = {node: 0 for node in self.graph.nodes()}
        
        # PageRank (importance based on connections)
        try:
            pagerank = nx.pagerank(self.graph)
        except:
            pagerank = {node: 1/self.graph.number_of_nodes() for node in self.graph.nodes()}
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            
            metrics.append({
                'belief_id': node,
                'statement': node_data.get('statement', ''),
                'tier': node_data.get('tier', ''),
                'degree_centrality': degree_centrality.get(node, 0),
                'in_degree_centrality': in_degree_centrality.get(node, 0),
                'out_degree_centrality': out_degree_centrality.get(node, 0),
                'betweenness_centrality': betweenness.get(node, 0),
                'pagerank': pagerank.get(node, 0),
                'in_degree': self.graph.in_degree(node),
                'out_degree': self.graph.out_degree(node)
            })
        
        return pd.DataFrame(metrics)
    
    def find_keystone_beliefs(self, top_n: int = 10) -> List[Dict]:
        """
        Find keystone beliefs (high centrality, foundational).
        
        Args:
            top_n: Number of top beliefs to return
            
        Returns:
            List of keystone belief dictionaries
        """
        if self.graph is None:
            return []
        
        centrality_df = self.calculate_centrality_metrics()
        
        # Sort by PageRank (good overall importance metric)
        top_beliefs = centrality_df.nlargest(top_n, 'pagerank')
        
        return top_beliefs.to_dict('records')
    
    def find_root_beliefs(self) -> List[str]:
        """
        Find root beliefs (no parents).
        
        Returns:
            List of root belief IDs
        """
        if self.graph is None:
            return []
        
        roots = [node for node in self.graph.nodes() if self.graph.in_degree(node) == 0]
        return roots
    
    def find_leaf_beliefs(self) -> List[str]:
        """
        Find leaf beliefs (no children).
        
        Returns:
            List of leaf belief IDs
        """
        if self.graph is None:
            return []
        
        leaves = [node for node in self.graph.nodes() if self.graph.out_degree(node) == 0]
        return leaves
    
    def get_belief_paths(self, start_belief_id: str, end_belief_id: str) -> List[List[str]]:
        """
        Find all paths between two beliefs.
        
        Args:
            start_belief_id: Starting belief ID
            end_belief_id: Ending belief ID
            
        Returns:
            List of paths (each path is a list of belief IDs)
        """
        if self.graph is None:
            return []
        
        try:
            paths = list(nx.all_simple_paths(self.graph, start_belief_id, end_belief_id))
            return paths
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return []
    
    def get_descendants(self, belief_id: str) -> List[str]:
        """
        Get all descendants of a belief.
        
        Args:
            belief_id: Belief ID
            
        Returns:
            List of descendant belief IDs
        """
        if self.graph is None:
            return []
        
        try:
            return list(nx.descendants(self.graph, belief_id))
        except nx.NodeNotFound:
            return []
    
    def get_ancestors(self, belief_id: str) -> List[str]:
        """
        Get all ancestors of a belief.
        
        Args:
            belief_id: Belief ID
            
        Returns:
            List of ancestor belief IDs
        """
        if self.graph is None:
            return []
        
        try:
            return list(nx.ancestors(self.graph, belief_id))
        except nx.NodeNotFound:
            return []
    
    def detect_communities(self) -> Dict[str, int]:
        """
        Detect communities/clusters in belief graph.
        
        Returns:
            Dictionary mapping belief_id to community_id
        """
        if self.graph is None:
            return {}
        
        # Convert to undirected for community detection
        G_undirected = self.graph.to_undirected()
        
        try:
            # Use greedy modularity communities
            communities = nx.community.greedy_modularity_communities(G_undirected)
            
            # Map nodes to community IDs
            community_map = {}
            for i, community in enumerate(communities):
                for node in community:
                    community_map[node] = i
            
            return community_map
        except:
            return {}
    
    def get_graph_stats(self) -> Dict:
        """
        Get comprehensive graph statistics.
        
        Returns:
            Dictionary of statistics
        """
        if self.graph is None:
            return {}
        
        stats = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'is_dag': nx.is_directed_acyclic_graph(self.graph),
            'root_nodes': len(self.find_root_beliefs()),
            'leaf_nodes': len(self.find_leaf_beliefs()),
            'weakly_connected_components': nx.number_weakly_connected_components(self.graph),
            'strongly_connected_components': nx.number_strongly_connected_components(self.graph),
        }
        
        # Average path length (if connected)
        if nx.is_weakly_connected(self.graph):
            try:
                stats['avg_path_length'] = nx.average_shortest_path_length(self.graph)
            except:
                stats['avg_path_length'] = None
        
        # Clustering coefficient
        try:
            G_undirected = self.graph.to_undirected()
            stats['avg_clustering'] = nx.average_clustering(G_undirected)
        except:
            stats['avg_clustering'] = None
        
        return stats
    
    def export_to_json(self, output_path: str):
        """
        Export graph to JSON format.
        
        Args:
            output_path: Path to save JSON
        """
        if self.graph is None:
            print("⚠️  No graph to export")
            return
        
        # Convert to node-link format
        data = nx.node_link_data(self.graph)
        
        # Save to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Exported graph to {output_path}")
    
    def export_to_graphml(self, output_path: str):
        """
        Export graph to GraphML format (for Gephi, Cytoscape).
        
        Args:
            output_path: Path to save GraphML
        """
        if self.graph is None:
            print("⚠️  No graph to export")
            return
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        nx.write_graphml(self.graph, output_path)
        print(f"💾 Exported graph to {output_path} (GraphML format)")
    
    def visualize_hierarchy(self) -> Dict:
        """
        Generate data for hierarchical visualization.
        
        Returns:
            Dictionary with visualization data
        """
        if self.graph is None:
            return {}
        
        # Build hierarchical layout
        roots = self.find_root_beliefs()
        
        def build_tree(node_id: str, visited: set = None) -> Dict:
            if visited is None:
                visited = set()
            
            if node_id in visited:
                return None
            
            visited.add(node_id)
            node_data = self.graph.nodes[node_id]
            
            tree_node = {
                'id': node_id,
                'name': node_data.get('statement', '')[:50] + '...',
                'tier': node_data.get('tier', ''),
                'conviction': node_data.get('conviction', 0),
                'stability': node_data.get('stability', 0),
                'children': []
            }
            
            # Add children
            for child in self.graph.successors(node_id):
                child_tree = build_tree(child, visited)
                if child_tree:
                    tree_node['children'].append(child_tree)
            
            return tree_node
        
        trees = [build_tree(root) for root in roots]
        
        return {
            'roots': trees,
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges()
        }

