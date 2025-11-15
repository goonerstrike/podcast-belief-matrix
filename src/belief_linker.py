"""
Belief parent-child relationship linker.
Matches parent_hint text to actual beliefs to build hierarchical structure.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class BeliefLinker:
    """Link parent-child relationships between beliefs."""
    
    def __init__(self, similarity_threshold: float = 0.6):
        """
        Initialize belief linker.
        
        Args:
            similarity_threshold: Minimum similarity to consider a match
        """
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
    def link_beliefs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Link parent hints to actual belief IDs.
        
        Args:
            df: DataFrame with beliefs containing parent_hint field
            
        Returns:
            DataFrame with parent_belief_id field filled in
        """
        if df.empty:
            return df
        
        print(f"\n🔗 Linking parent-child relationships...")
        print(f"   Total beliefs: {len(df)}")
        
        result_df = df.copy()
        
        # Find parent matches
        matches_found = 0
        for idx, belief in result_df.iterrows():
            parent_hint = belief.get('parent_hint', '')
            
            # Skip if no parent hint
            if not parent_hint or pd.isna(parent_hint) or parent_hint.strip() == '':
                continue
            
            # Find matching parent
            parent_id = self._find_parent(parent_hint, result_df, idx)
            
            if parent_id:
                result_df.at[idx, 'parent_belief_id'] = parent_id
                matches_found += 1
        
        # Validate no circular dependencies
        self._validate_hierarchy(result_df)
        
        print(f"   Matched {matches_found} parent-child relationships")
        print(f"   Orphaned beliefs: {len(result_df[result_df['parent_belief_id'].isna() & result_df['parent_hint'].notna()])}")
        
        return result_df
    
    def _find_parent(self, parent_hint: str, df: pd.DataFrame, 
                    current_idx: int) -> str:
        """
        Find best matching parent belief for a hint.
        
        Args:
            parent_hint: Text description of parent belief
            df: DataFrame with all beliefs
            current_idx: Index of current belief (to avoid self-loops)
            
        Returns:
            Parent belief_id or None
        """
        # Get candidate parent beliefs (more foundational = lower importance)
        current_importance = df.iloc[current_idx]['importance']
        candidates = df[
            (df.index != current_idx) &  # Not self
            (df['importance'] < current_importance)  # More foundational
        ]
        
        if candidates.empty:
            return None
        
        # Vectorize parent hint and candidate statements
        texts = [parent_hint] + candidates['statement_text'].fillna('').tolist()
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Calculate similarity between hint (first row) and all candidates
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
            
            # Find best match above threshold
            best_idx = np.argmax(similarities)
            best_similarity = similarities[best_idx]
            
            if best_similarity >= self.similarity_threshold:
                return candidates.iloc[best_idx]['belief_id']
        except:
            # Fallback: simple text matching
            for idx, candidate in candidates.iterrows():
                if parent_hint.lower() in candidate['statement_text'].lower():
                    return candidate['belief_id']
        
        return None
    
    def _validate_hierarchy(self, df: pd.DataFrame):
        """
        Validate no circular dependencies in belief hierarchy.
        
        Args:
            df: DataFrame with parent_belief_id filled in
        """
        # Build adjacency list
        children = {}
        for _, belief in df.iterrows():
            belief_id = belief['belief_id']
            parent_id = belief['parent_belief_id']
            
            if pd.notna(parent_id):
                if parent_id not in children:
                    children[parent_id] = []
                children[parent_id].append(belief_id)
        
        # Check for cycles using DFS
        def has_cycle(node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            if node in children:
                for child in children[node]:
                    if child not in visited:
                        if has_cycle(child, visited, rec_stack):
                            return True
                    elif child in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        visited = set()
        for belief_id in df['belief_id']:
            if belief_id not in visited:
                if has_cycle(belief_id, visited, set()):
                    print(f"   ⚠️  Warning: Circular dependency detected involving {belief_id}")
    
    def build_hierarchy_tree(self, df: pd.DataFrame) -> Dict:
        """
        Build hierarchical tree structure from beliefs.
        
        Args:
            df: DataFrame with linked beliefs
            
        Returns:
            Dictionary representing tree structure
        """
        # Find root beliefs (no parent)
        roots = df[df['parent_belief_id'].isna()]['belief_id'].tolist()
        
        # Build children mapping
        children_map = {}
        for _, belief in df.iterrows():
            parent_id = belief['parent_belief_id']
            if pd.notna(parent_id):
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(belief['belief_id'])
        
        # Build tree recursively
        def build_subtree(belief_id: str) -> Dict:
            belief = df[df['belief_id'] == belief_id].iloc[0]
            
            node = {
                'belief_id': belief_id,
                'statement': belief['statement_text'],
                'importance': int(belief['importance']),
                'tier': belief['tier_name'],
                'conviction': float(belief['conviction_score']),
                'stability': float(belief['stability_score']),
                'children': []
            }
            
            if belief_id in children_map:
                for child_id in children_map[belief_id]:
                    node['children'].append(build_subtree(child_id))
            
            return node
        
        tree = {
            'roots': [build_subtree(root_id) for root_id in roots],
            'total_beliefs': len(df),
            'root_count': len(roots)
        }
        
        return tree
    
    def get_hierarchy_stats(self, df: pd.DataFrame) -> Dict:
        """
        Get statistics about belief hierarchy.
        
        Args:
            df: DataFrame with linked beliefs
            
        Returns:
            Dictionary of statistics
        """
        total = len(df)
        has_parent = df['parent_belief_id'].notna().sum()
        is_parent = df['belief_id'].isin(df['parent_belief_id'].dropna()).sum()
        roots = (df['parent_belief_id'].isna()).sum()
        leaves = (~df['belief_id'].isin(df['parent_belief_id'].dropna())).sum()
        
        # Calculate max depth
        def get_depth(belief_id: str, df: pd.DataFrame, memo: Dict = None) -> int:
            if memo is None:
                memo = {}
            if belief_id in memo:
                return memo[belief_id]
            
            belief = df[df['belief_id'] == belief_id]
            if belief.empty:
                return 0
            
            parent_id = belief.iloc[0]['parent_belief_id']
            if pd.isna(parent_id):
                depth = 0
            else:
                depth = 1 + get_depth(parent_id, df, memo)
            
            memo[belief_id] = depth
            return depth
        
        depths = [get_depth(bid, df) for bid in df['belief_id']]
        max_depth = max(depths) if depths else 0
        avg_depth = np.mean(depths) if depths else 0
        
        return {
            'total_beliefs': total,
            'has_parent': has_parent,
            'is_parent': is_parent,
            'root_beliefs': roots,
            'leaf_beliefs': leaves,
            'max_depth': max_depth,
            'avg_depth': avg_depth,
            'connectivity': (has_parent / total * 100) if total > 0 else 0
        }

