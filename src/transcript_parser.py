"""
Parse diarized podcast transcripts.
Format: SPEAKER_ID | START_TIME | END_TIME | TEXT
"""
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Utterance:
    """Single speaker utterance from transcript."""
    speaker_id: str
    start_time: str
    end_time: str
    text: str
    episode_id: Optional[str] = None
    utterance_id: Optional[str] = None
    
    def __post_init__(self):
        """Clean up text."""
        self.text = self.text.strip()
        
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'speaker_id': self.speaker_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'text': self.text,
            'episode_id': self.episode_id,
            'utterance_id': self.utterance_id
        }


class TranscriptParser:
    """Parse diarized transcripts."""
    
    # Pattern: SPEAKER_A | 00:00:00 | 00:00:26 | Text content
    PATTERN = re.compile(r'^([A-Z_]+)\s*\|\s*([0-9:]+)\s*\|\s*([0-9:]+)\s*\|\s*(.+)$')
    
    def __init__(self, episode_id: Optional[str] = None):
        """
        Initialize parser.
        
        Args:
            episode_id: Episode identifier (e.g., e_jre_2404)
        """
        self.episode_id = episode_id
        
    def parse_file(self, filepath: str) -> List[Utterance]:
        """
        Parse transcript file.
        
        Args:
            filepath: Path to transcript file
            
        Returns:
            List of Utterance objects
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_text(content)
    
    def parse_text(self, text: str) -> List[Utterance]:
        """
        Parse transcript text.
        
        Args:
            text: Raw transcript text
            
        Returns:
            List of Utterance objects
        """
        utterances = []
        lines = text.strip().split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            match = self.PATTERN.match(line)
            if match:
                speaker_id, start_time, end_time, text = match.groups()
                
                utterance = Utterance(
                    speaker_id=speaker_id,
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    episode_id=self.episode_id,
                    utterance_id=f"u_{i+1:04d}"
                )
                utterances.append(utterance)
            else:
                # Try to handle malformed lines
                if '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4:
                        utterance = Utterance(
                            speaker_id=parts[0],
                            start_time=parts[1],
                            end_time=parts[2],
                            text='|'.join(parts[3:]),
                            episode_id=self.episode_id,
                            utterance_id=f"u_{i+1:04d}"
                        )
                        utterances.append(utterance)
        
        return utterances
    
    def filter_speakers(self, utterances: List[Utterance], 
                       speaker_ids: List[str]) -> List[Utterance]:
        """
        Filter utterances by speaker IDs.
        
        Args:
            utterances: List of utterances
            speaker_ids: List of speaker IDs to keep
            
        Returns:
            Filtered list of utterances
        """
        return [u for u in utterances if u.speaker_id in speaker_ids]
    
    def get_speakers(self, utterances: List[Utterance]) -> List[str]:
        """
        Get unique speaker IDs.
        
        Args:
            utterances: List of utterances
            
        Returns:
            List of unique speaker IDs
        """
        return sorted(list(set(u.speaker_id for u in utterances)))
    
    def truncate(self, utterances: List[Utterance], max_words: int = 1000) -> List[Utterance]:
        """
        Truncate transcript to first N words (for cheap testing).
        
        Args:
            utterances: List of utterances
            max_words: Maximum number of words
            
        Returns:
            Truncated list of utterances
        """
        word_count = 0
        truncated = []
        
        for utterance in utterances:
            words_in_utterance = len(utterance.text.split())
            if word_count + words_in_utterance > max_words:
                # Include partial utterance up to word limit
                remaining = max_words - word_count
                words = utterance.text.split()[:remaining]
                truncated_text = ' '.join(words)
                
                truncated.append(Utterance(
                    speaker_id=utterance.speaker_id,
                    start_time=utterance.start_time,
                    end_time=utterance.end_time,
                    text=truncated_text,
                    episode_id=utterance.episode_id,
                    utterance_id=utterance.utterance_id
                ))
                break
            else:
                truncated.append(utterance)
                word_count += words_in_utterance
        
        return truncated

