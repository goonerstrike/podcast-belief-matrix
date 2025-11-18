"""
Main belief extraction pipeline.
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional
from .transcript_parser import TranscriptParser, Utterance
from .classifier import BeliefClassifier, BeliefClassification


class BeliefExtractor:
    """Main pipeline for extracting beliefs from transcripts."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini",
                 prompts_dir: str = "prompts"):
        """
        Initialize extractor.
        
        Args:
            api_key: OpenAI API key
            model: Model to use
            prompts_dir: Directory with prompt templates
        """
        self.classifier = BeliefClassifier(
            api_key=api_key,
            model=model,
            prompts_dir=prompts_dir
        )
        
    def extract_from_file(self, transcript_path: str, 
                         episode_id: Optional[str] = None,
                         cheap_mode: bool = False,
                         max_words: int = 1000) -> pd.DataFrame:
        """
        Extract beliefs from transcript file.
        
        Args:
            transcript_path: Path to diarized transcript
            episode_id: Episode identifier
            cheap_mode: If True, only process first max_words
            max_words: Max words for cheap mode
            
        Returns:
            DataFrame with belief matrix
        """
        # Parse transcript
        parser = TranscriptParser(episode_id=episode_id)
        utterances = parser.parse_file(transcript_path)
        
        if cheap_mode:
            utterances = parser.truncate(utterances, max_words=max_words)
            print(f"🔸 Cheap mode: Processing first {max_words} words ({len(utterances)} utterances)")
        
        print(f"📄 Parsed {len(utterances)} utterances from {len(parser.get_speakers(utterances))} speakers")
        
        # Classify utterances
        print(f"🤖 Classifying statements...")
        classifications = self.classifier.classify_batch([u.to_dict() for u in utterances], parallel=self.parallel)
        
        # Filter for beliefs only
        beliefs = [c for c in classifications if c.is_belief]
        
        print(f"✅ Found {len(beliefs)} beliefs out of {len(classifications)} statements")
        
        # Convert to DataFrame
        df = self._to_dataframe(beliefs, episode_id=episode_id)
        
        return df
    
    def extract_from_utterances(self, utterances: List[Utterance],
                               episode_id: Optional[str] = None) -> pd.DataFrame:
        """
        Extract beliefs from list of utterances.
        
        Args:
            utterances: List of Utterance objects
            episode_id: Episode identifier
            
        Returns:
            DataFrame with belief matrix
        """
        classifications = self.classifier.classify_batch([u.to_dict() for u in utterances])
        beliefs = [c for c in classifications if c.is_belief]
        return self._to_dataframe(beliefs, episode_id=episode_id)
    
    def _to_dataframe(self, beliefs: List[BeliefClassification],
                     episode_id: Optional[str] = None) -> pd.DataFrame:
        """
        Convert beliefs to DataFrame matching the schema.
        
        Schema:
        belief_id, speaker_id, episode_id, timestamp, statement_text,
        atomic_belief, certainty, importance, tier_name, category, 
        conviction_score, stability_score, parent_hint, parent_belief_id
        """
        records = []
        
        for i, belief in enumerate(beliefs, start=1):
            record = {
                'belief_id': f'b_{i:04d}',
                'speaker_id': belief.speaker_id,
                'episode_id': episode_id or belief.statement_text[:20],
                'timestamp': belief.timestamp,
                'statement_text': belief.statement_text,
                'atomic_belief': belief.atomic_belief,
                'certainty': belief.certainty,
                'importance': belief.importance,
                'tier_name': belief.tier_name,
                'category': belief.category,
                'conviction_score': belief.conviction_score,
                'stability_score': belief.stability_score,
                'parent_hint': belief.parent_hint or '',
                'parent_belief_id': None  # To be filled in post-processing
            }
            records.append(record)
        
        # Ensure correct column order
        columns = [
            'belief_id', 'speaker_id', 'episode_id', 'timestamp',
            'statement_text', 'atomic_belief', 'certainty', 
            'importance', 'tier_name', 'category',
            'conviction_score', 'stability_score', 'parent_hint',
            'parent_belief_id'
        ]
        
        if not records:
            # Return empty dataframe with correct columns
            return pd.DataFrame(columns=columns)
        
        df = pd.DataFrame(records)
        return df[columns]
    
    def save_output(self, df: pd.DataFrame, output_path: str,
                   format: str = 'csv'):
        """
        Save beliefs to file.
        
        Args:
            df: Beliefs DataFrame
            output_path: Output file path
            format: Output format (csv, json, parquet)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'csv':
            df.to_csv(output_path, index=False)
        elif format == 'json':
            df.to_json(output_path, orient='records', indent=2)
        elif format == 'parquet':
            df.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"💾 Saved {len(df)} beliefs to {output_path}")
    
    def get_cost_stats(self):
        """Get cost statistics from classifier."""
        return self.classifier.get_cost_stats()
    
    def get_summary_stats(self, df: pd.DataFrame) -> dict:
        """
        Get summary statistics.
        
        Args:
            df: Beliefs DataFrame
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_beliefs': len(df),
            'beliefs_per_speaker': df.groupby('speaker_id').size().to_dict(),
            'beliefs_per_tier': df.groupby('tier_name').size().to_dict(),
            'beliefs_per_category': df.groupby('category').size().to_dict(),
            'avg_conviction': df['conviction_score'].mean(),
            'avg_stability': df['stability_score'].mean(),
            'conviction_by_tier': df.groupby('tier_name')['conviction_score'].mean().to_dict(),
            'stability_by_tier': df.groupby('tier_name')['stability_score'].mean().to_dict()
        }
        
        return stats

