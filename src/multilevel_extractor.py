"""
Multi-level belief extraction orchestrator.
Processes transcripts at multiple abstraction levels to capture beliefs across scales.
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from .transcript_parser import TranscriptParser, Utterance
from .classifier import BeliefClassifier, BeliefClassification
from .chunker import TranscriptChunker, Chunk
from tqdm import tqdm


class MultiLevelExtractor:
    """Extract beliefs at multiple abstraction levels."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini",
                 prompts_dir: str = "prompts",
                 chunking_strategy: str = "exponential"):
        """
        Initialize multi-level extractor.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for classification
            prompts_dir: Directory with prompt templates
            chunking_strategy: Strategy for chunking ('exponential', 'linear', 'custom')
        """
        self.classifier = BeliefClassifier(
            api_key=api_key,
            model=model,
            prompts_dir=prompts_dir
        )
        self.chunker = TranscriptChunker(strategy=chunking_strategy)
        self.model = model
        
    def extract_multilevel(self, transcript_path: str,
                          episode_id: Optional[str] = None,
                          levels: List[int] = None,
                          max_words: Optional[int] = None) -> pd.DataFrame:
        """
        Extract beliefs at multiple levels from transcript.
        
        Args:
            transcript_path: Path to diarized transcript
            episode_id: Episode identifier
            levels: Chunk sizes to use (default: exponential [1,2,4,8,16,32,64,128,256,512])
            max_words: Limit transcript words for testing (cheap mode)
            
        Returns:
            DataFrame with all beliefs tagged by discovery level
        """
        print(f"\n{'='*80}")
        print(f"🌐 Multi-Level Belief Extraction")
        print(f"{'='*80}")
        
        # Parse transcript
        parser = TranscriptParser(episode_id=episode_id)
        utterances = parser.parse_file(transcript_path)
        
        if max_words:
            utterances = parser.truncate(utterances, max_words=max_words)
            print(f"🔸 Limited to first {max_words} words ({len(utterances)} utterances)")
        
        print(f"📄 Parsed {len(utterances)} utterances from {len(parser.get_speakers(utterances))} speakers")
        
        # Create chunks at all levels
        print(f"\n📐 Creating chunks...")
        chunks_by_level = self.chunker.chunk_transcript(utterances, levels=levels)
        print(self.chunker.get_level_summary(chunks_by_level))
        
        # Extract beliefs at each level
        all_beliefs = []
        total_levels = len(chunks_by_level)
        
        for level_num, chunks in sorted(chunks_by_level.items()):
            print(f"\n🔍 Level {level_num}/{total_levels}: Processing {len(chunks)} chunks...")
            
            level_beliefs = self._extract_from_chunks(
                chunks, 
                level_num, 
                episode_id
            )
            
            all_beliefs.extend(level_beliefs)
            print(f"   ✅ Found {len(level_beliefs)} beliefs at Level {level_num}")
        
        # Convert to DataFrame
        if not all_beliefs:
            print(f"\n⚠️  No beliefs found across all levels")
            return self._empty_dataframe()
        
        df = self._to_dataframe(all_beliefs, episode_id)
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"📊 Multi-Level Extraction Summary")
        print(f"{'='*80}")
        print(f"Total beliefs found: {len(df)}")
        print(f"Beliefs by level:")
        for level in sorted(df['discovery_level'].unique()):
            count = len(df[df['discovery_level'] == level])
            print(f"   Level {level:2d}: {count:4d} beliefs")
        print(f"{'='*80}\n")
        
        return df
    
    def _extract_from_chunks(self, chunks: List[Chunk], 
                            level: int, episode_id: str) -> List[Dict]:
        """
        Extract beliefs from all chunks at a specific level.
        
        Args:
            chunks: List of chunks to process
            level: Level number
            episode_id: Episode identifier
            
        Returns:
            List of belief dictionaries with metadata
        """
        beliefs = []
        
        # Process each chunk
        for chunk in tqdm(chunks, desc=f"Level {level}", leave=False):
            # For each chunk, we treat it as a single "meta-utterance"
            # This allows the classifier to see the full context
            
            # Create a synthetic utterance representing this chunk
            chunk_text = chunk.to_text()
            speakers = chunk.get_speakers()
            start_time, end_time = chunk.get_time_range()
            
            # Get primary speaker (most utterances in chunk)
            speaker_counts = {}
            for utt in chunk.utterances:
                speaker_counts[utt.speaker_id] = speaker_counts.get(utt.speaker_id, 0) + 1
            primary_speaker = max(speaker_counts, key=speaker_counts.get) if speaker_counts else "UNKNOWN"
            
            # Classify this chunk
            classification = self.classifier.classify(
                speaker_id=primary_speaker,
                timestamp=start_time,
                statement_text=chunk_text
            )
            
            # Only keep beliefs
            if classification.is_belief:
                belief_dict = {
                    'discovery_level': level,
                    'chunk_id': chunk.chunk_id,
                    'chunk_size': chunk.size,
                    'speaker_id': classification.speaker_id,
                    'timestamp': classification.timestamp,
                    'statement_text': classification.statement_text,
                    'is_belief': classification.is_belief,
                    'filter_confidence': classification.filter_confidence,
                    'tier_name': classification.tier_name,
                    'importance': classification.importance,
                    'conviction_score': classification.conviction_score,
                    'stability_score': classification.stability_score,
                    'category': classification.category,
                    'parent_hint': classification.parent_hint,
                    'defines_outgroup': classification.defines_outgroup,
                    'episode_id': episode_id
                }
                beliefs.append(belief_dict)
        
        return beliefs
    
    def _to_dataframe(self, beliefs: List[Dict], episode_id: str) -> pd.DataFrame:
        """
        Convert beliefs to DataFrame.
        
        Args:
            beliefs: List of belief dictionaries
            episode_id: Episode identifier
            
        Returns:
            DataFrame with proper schema
        """
        # Add belief IDs
        for i, belief in enumerate(beliefs, start=1):
            belief['belief_id'] = f'b_{i:04d}'
            belief['parent_belief_id'] = None  # Will be filled by linker
        
        # Define column order
        columns = [
            'belief_id', 'discovery_level', 'chunk_id', 'chunk_size',
            'speaker_id', 'episode_id', 'timestamp', 'statement_text',
            'importance', 'tier_name', 'category', 
            'conviction_score', 'stability_score',
            'parent_hint', 'parent_belief_id', 'defines_outgroup',
            'filter_confidence'
        ]
        
        df = pd.DataFrame(beliefs)
        
        # Ensure all columns exist
        for col in columns:
            if col not in df.columns:
                df[col] = None
        
        return df[columns]
    
    def _empty_dataframe(self) -> pd.DataFrame:
        """Return empty DataFrame with correct schema."""
        columns = [
            'belief_id', 'discovery_level', 'chunk_id', 'chunk_size',
            'speaker_id', 'episode_id', 'timestamp', 'statement_text',
            'importance', 'tier_name', 'category', 
            'conviction_score', 'stability_score',
            'parent_hint', 'parent_belief_id', 'defines_outgroup',
            'filter_confidence'
        ]
        return pd.DataFrame(columns=columns)
    
    def get_cost_stats(self):
        """Get cost statistics from classifier."""
        return self.classifier.get_cost_stats()
    
    def save_output(self, df: pd.DataFrame, output_path: str):
        """
        Save beliefs to CSV.
        
        Args:
            df: Beliefs DataFrame
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        print(f"💾 Saved {len(df)} beliefs to {output_path}")

