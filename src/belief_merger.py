"""
Belief deduplication and merging across abstraction levels.
Uses semantic similarity to identify duplicate beliefs found at different scales.
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class BeliefMerger:
    """Deduplicate and merge beliefs found at multiple levels."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize belief merger.
        
        Args:
            similarity_threshold: Cosine similarity threshold for considering beliefs duplicates (0-1)
        """
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
    def merge_beliefs(self, df: pd.DataFrame, 
                     keep_strategy: str = "all") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Merge duplicate beliefs across levels.
        
        Args:
            df: DataFrame with beliefs from all levels
            keep_strategy: How to handle duplicates:
                - "all": Keep all instances, add reinforcement tags
                - "best": Keep only the best-fit level
                - "merge": Create single entry with merged metadata
                
        Returns:
            Tuple of (deduplicated_df, mapping_df)
        """
        if df.empty:
            return df, pd.DataFrame()
        
        print(f"\n🔗 Deduplicating beliefs...")
        print(f"   Input: {len(df)} beliefs")
        print(f"   Similarity threshold: {self.similarity_threshold}")
        
        # Find duplicate groups
        duplicate_groups = self._find_duplicates(df)
        
        if keep_strategy == "all":
            result_df, mapping_df = self._keep_all_with_tags(df, duplicate_groups)
        elif keep_strategy == "best":
            result_df, mapping_df = self._keep_best_fit(df, duplicate_groups)
        else:  # merge
            result_df, mapping_df = self._merge_duplicates(df, duplicate_groups)
        
        print(f"   Output: {len(result_df)} beliefs")
        print(f"   Found {len(duplicate_groups)} duplicate groups")
        
        return result_df, mapping_df
    
    def _find_duplicates(self, df: pd.DataFrame) -> List[List[int]]:
        """
        Find groups of duplicate beliefs using semantic similarity.
        
        Args:
            df: DataFrame with beliefs
            
        Returns:
            List of lists, where each inner list contains indices of duplicate beliefs
        """
        if len(df) < 2:
            return []
        
        # Vectorize statements
        statements = df['statement_text'].fillna('').tolist()
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform(statements)
            similarity_matrix = cosine_similarity(tfidf_matrix)
        except:
            # Fallback: no vectorization possible
            return []
        
        # Find duplicate groups
        groups = []
        processed = set()
        
        for i in range(len(df)):
            if i in processed:
                continue
            
            # Find all beliefs similar to this one
            similar_indices = np.where(similarity_matrix[i] >= self.similarity_threshold)[0]
            
            # Only create group if there are duplicates
            if len(similar_indices) > 1:
                group = [idx for idx in similar_indices if idx not in processed]
                if len(group) > 1:
                    groups.append(group)
                    processed.update(group)
        
        return groups
    
    def _keep_all_with_tags(self, df: pd.DataFrame, 
                           duplicate_groups: List[List[int]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Keep all belief instances but add reinforcement metadata.
        
        Args:
            df: DataFrame with beliefs
            duplicate_groups: List of duplicate groups
            
        Returns:
            Tuple of (tagged_df, mapping_df)
        """
        result_df = df.copy()
        
        # Add reinforcement columns
        result_df['duplicate_group_id'] = None
        result_df['reinforcement_levels'] = None
        result_df['reinforcement_count'] = 1
        
        # Tag duplicates
        mapping_records = []
        for group_id, indices in enumerate(duplicate_groups):
            levels = result_df.iloc[indices]['discovery_level'].tolist()
            
            for idx in indices:
                result_df.at[idx, 'duplicate_group_id'] = f'dup_{group_id+1:04d}'
                result_df.at[idx, 'reinforcement_levels'] = ','.join(map(str, sorted(levels)))
                result_df.at[idx, 'reinforcement_count'] = len(indices)
                
                mapping_records.append({
                    'belief_id': result_df.at[idx, 'belief_id'],
                    'duplicate_group_id': f'dup_{group_id+1:04d}',
                    'is_primary': idx == indices[0],
                    'reinforcement_count': len(indices)
                })
        
        mapping_df = pd.DataFrame(mapping_records)
        
        return result_df, mapping_df
    
    def _keep_best_fit(self, df: pd.DataFrame,
                      duplicate_groups: List[List[int]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Keep only the best-fit instance from each duplicate group.
        Best fit = highest conviction at most appropriate level.
        
        Args:
            df: DataFrame with beliefs  
            duplicate_groups: List of duplicate groups
            
        Returns:
            Tuple of (deduplicated_df, mapping_df)
        """
        indices_to_keep = set(range(len(df)))
        mapping_records = []
        
        for group_id, indices in enumerate(duplicate_groups):
            group_df = df.iloc[indices]
            
            # Score each belief: conviction * (1 / abs(level - ideal_level))
            # Ideal level based on importance tier
            scores = []
            for idx in indices:
                belief = df.iloc[idx]
                ideal_level = self._get_ideal_level(belief['importance'])
                level_penalty = 1 / (1 + abs(belief['discovery_level'] - ideal_level))
                score = belief['conviction_score'] * level_penalty
                scores.append(score)
            
            # Keep the best scoring belief
            best_idx = indices[np.argmax(scores)]
            indices_to_remove = [idx for idx in indices if idx != best_idx]
            indices_to_keep -= set(indices_to_remove)
            
            # Record mapping
            for idx in indices:
                mapping_records.append({
                    'belief_id': df.iloc[idx]['belief_id'],
                    'duplicate_group_id': f'dup_{group_id+1:04d}',
                    'kept_belief_id': df.iloc[best_idx]['belief_id'],
                    'is_primary': idx == best_idx,
                    'score': scores[indices.index(idx)]
                })
        
        result_df = df.iloc[list(indices_to_keep)].reset_index(drop=True)
        mapping_df = pd.DataFrame(mapping_records)
        
        return result_df, mapping_df
    
    def _merge_duplicates(self, df: pd.DataFrame,
                         duplicate_groups: List[List[int]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Merge duplicate beliefs into single entries.
        
        Args:
            df: DataFrame with beliefs
            duplicate_groups: List of duplicate groups
            
        Returns:
            Tuple of (merged_df, mapping_df)
        """
        indices_to_keep = set(range(len(df)))
        merged_beliefs = []
        mapping_records = []
        
        for group_id, indices in enumerate(duplicate_groups):
            group_df = df.iloc[indices]
            
            # Create merged belief
            merged = {
                'belief_id': df.iloc[indices[0]]['belief_id'],  # Use first belief's ID
                'discovery_level': int(group_df['discovery_level'].mode().iloc[0]),  # Most common level
                'chunk_id': ','.join(group_df['chunk_id'].astype(str)),
                'chunk_size': int(group_df['chunk_size'].mean()),
                'speaker_id': group_df['speaker_id'].mode().iloc[0],
                'episode_id': group_df['episode_id'].iloc[0],
                'timestamp': group_df['timestamp'].iloc[0],
                'statement_text': group_df['statement_text'].iloc[0],  # Use first statement
                'importance': int(group_df['importance'].mode().iloc[0]),
                'tier_name': group_df['tier_name'].mode().iloc[0],
                'category': group_df['category'].mode().iloc[0],
                'conviction_score': float(group_df['conviction_score'].mean()),
                'stability_score': float(group_df['stability_score'].mean()),
                'parent_hint': group_df['parent_hint'].iloc[0],
                'parent_belief_id': None,
                'defines_outgroup': bool(group_df['defines_outgroup'].mode().iloc[0]),
                'filter_confidence': float(group_df['filter_confidence'].mean()),
                'reinforcement_count': len(indices),
                'reinforcement_levels': ','.join(map(str, sorted(group_df['discovery_level'])))
            }
            merged_beliefs.append(merged)
            
            # Remove original indices from keep set
            indices_to_keep -= set(indices)
            
            # Record mapping
            for idx in indices:
                mapping_records.append({
                    'original_belief_id': df.iloc[idx]['belief_id'],
                    'merged_belief_id': merged['belief_id'],
                    'duplicate_group_id': f'dup_{group_id+1:04d}'
                })
        
        # Keep non-duplicate beliefs as-is
        kept_df = df.iloc[list(indices_to_keep)].copy()
        kept_df['reinforcement_count'] = 1
        kept_df['reinforcement_levels'] = kept_df['discovery_level'].astype(str)
        
        # Combine merged and kept beliefs
        merged_df = pd.DataFrame(merged_beliefs)
        result_df = pd.concat([kept_df, merged_df], ignore_index=True)
        
        mapping_df = pd.DataFrame(mapping_records)
        
        return result_df, mapping_df
    
    @staticmethod
    def _get_ideal_level(importance: int) -> int:
        """
        Get ideal discovery level for a belief based on its importance tier.
        
        Args:
            importance: Importance score (1-10)
            
        Returns:
            Ideal level number (1-10)
        """
        # Core axioms (1-2) should be found at high levels (9-10)
        # Casual takes (9-10) should be found at low levels (1-2)
        # Reverse mapping
        return 11 - importance

