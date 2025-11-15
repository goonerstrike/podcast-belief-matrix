"""
Multi-level chunking for belief extraction.
Splits transcripts into chunks of varying sizes to capture beliefs at different scales.
"""
from typing import List, Dict
from dataclasses import dataclass
from .transcript_parser import Utterance


@dataclass
class Chunk:
    """A chunk of utterances at a specific level."""
    level: int
    chunk_id: str
    utterances: List[Utterance]
    size: int  # Number of utterances
    
    def to_text(self) -> str:
        """Convert chunk to single text string."""
        return " ".join([u.text for u in self.utterances])
    
    def get_speakers(self) -> List[str]:
        """Get unique speakers in this chunk."""
        return list(set([u.speaker_id for u in self.utterances]))
    
    def get_time_range(self) -> tuple:
        """Get (start_time, end_time) for this chunk."""
        if not self.utterances:
            return ("", "")
        return (self.utterances[0].start_time, self.utterances[-1].end_time)


class TranscriptChunker:
    """Create chunks at multiple abstraction levels."""
    
    # Default exponential chunk sizes (in number of utterances)
    EXPONENTIAL_LEVELS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
    
    def __init__(self, strategy: str = "exponential"):
        """
        Initialize chunker.
        
        Args:
            strategy: Chunking strategy ('exponential', 'linear', 'custom')
        """
        self.strategy = strategy
        
    def chunk_transcript(self, utterances: List[Utterance], 
                        levels: List[int] = None) -> Dict[int, List[Chunk]]:
        """
        Create chunks at multiple levels.
        
        Args:
            utterances: List of utterances from transcript
            levels: Chunk sizes to use (default: EXPONENTIAL_LEVELS)
            
        Returns:
            Dictionary mapping level number to list of chunks
        """
        if levels is None:
            levels = self.EXPONENTIAL_LEVELS
            
        all_chunks = {}
        
        for level_idx, chunk_size in enumerate(levels, start=1):
            # Skip if chunk size is larger than transcript
            if chunk_size > len(utterances):
                print(f"⚠️  Level {level_idx} (size {chunk_size}) > transcript size ({len(utterances)}), skipping")
                continue
                
            chunks = self._create_chunks_at_level(
                utterances, 
                chunk_size, 
                level_idx
            )
            
            all_chunks[level_idx] = chunks
            
        return all_chunks
    
    def _create_chunks_at_level(self, utterances: List[Utterance], 
                                chunk_size: int, level: int) -> List[Chunk]:
        """
        Create overlapping or non-overlapping chunks at a specific level.
        
        Args:
            utterances: List of utterances
            chunk_size: Number of utterances per chunk
            level: Level number (1-10)
            
        Returns:
            List of chunks
        """
        chunks = []
        
        # Use sliding window with stride = chunk_size (non-overlapping)
        # Could be changed to overlapping if needed (stride < chunk_size)
        stride = chunk_size
        
        for i in range(0, len(utterances), stride):
            chunk_utterances = utterances[i:i + chunk_size]
            
            # Only create chunk if we have enough utterances
            if len(chunk_utterances) >= min(chunk_size, 1):
                chunk = Chunk(
                    level=level,
                    chunk_id=f"L{level}_C{len(chunks)+1:04d}",
                    utterances=chunk_utterances,
                    size=len(chunk_utterances)
                )
                chunks.append(chunk)
        
        return chunks
    
    def get_level_summary(self, chunks_by_level: Dict[int, List[Chunk]]) -> str:
        """
        Generate summary of chunking results.
        
        Args:
            chunks_by_level: Dictionary of chunks by level
            
        Returns:
            Summary string
        """
        lines = ["Chunking Summary:", "=" * 60]
        
        for level in sorted(chunks_by_level.keys()):
            chunks = chunks_by_level[level]
            chunk_size = chunks[0].size if chunks else 0
            
            lines.append(f"Level {level:2d} | Size: {chunk_size:4d} utterances | Chunks: {len(chunks):4d}")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    @staticmethod
    def create_full_transcript_chunk(utterances: List[Utterance]) -> Chunk:
        """
        Create a single chunk containing the entire transcript.
        Useful for Level 10 (macro analysis).
        
        Args:
            utterances: All utterances from transcript
            
        Returns:
            Single chunk containing all utterances
        """
        return Chunk(
            level=10,
            chunk_id="L10_FULL",
            utterances=utterances,
            size=len(utterances)
        )

