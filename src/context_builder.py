"""
Context builder for belief extraction.
Extracts context windows around detected beliefs.
"""
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class ContextWindow:
    """Context window around a belief utterance."""
    context_before: List[Dict]  # 10 utterances before
    target_utterance: Dict
    context_after: List[Dict]  # 10 utterances after
    context_chunk_ids: List[str]  # IDs of all utterances in window


class ContextBuilder:
    """Build context windows for belief analysis."""
    
    def get_context_window(self, utterances: List, target_index: int, 
                          window_size: int = 10) -> ContextWindow:
        """
        Extract context window around target utterance.
        
        Args:
            utterances: List of Utterance objects
            target_index: Index of the target utterance
            window_size: Number of utterances before/after (default: 10)
            
        Returns:
            ContextWindow with before/target/after utterances
        """
        # Extract before context (up to window_size)
        start_idx = max(0, target_index - window_size)
        context_before = utterances[start_idx:target_index]
        
        # Target utterance
        target = utterances[target_index]
        
        # Extract after context (up to window_size)
        end_idx = min(len(utterances), target_index + window_size + 1)
        context_after = utterances[target_index + 1:end_idx]
        
        # Collect all chunk IDs
        chunk_ids = []
        for i, u in enumerate(context_before, start=start_idx):
            chunk_ids.append(u.utterance_id if hasattr(u, 'utterance_id') and u.utterance_id else f"u_{i:04d}")
        chunk_ids.append(target.utterance_id if hasattr(target, 'utterance_id') and target.utterance_id else f"u_{target_index:04d}")
        for i, u in enumerate(context_after, start=target_index + 1):
            chunk_ids.append(u.utterance_id if hasattr(u, 'utterance_id') and u.utterance_id else f"u_{i:04d}")
        
        return ContextWindow(
            context_before=[u.to_dict() for u in context_before],
            target_utterance=target.to_dict(),
            context_after=[u.to_dict() for u in context_after],
            context_chunk_ids=chunk_ids
        )
    
    def build_episode_metadata(self, episode_id: str, utterances: List) -> Dict:
        """
        Build episode metadata from utterances.
        
        Args:
            episode_id: Episode identifier
            utterances: List of Utterance objects
            
        Returns:
            Dictionary with episode metadata
        """
        # Extract unique speakers
        speakers = sorted(list(set(u.speaker_id for u in utterances)))
        
        return {
            'episode_id': episode_id,
            'speakers': speakers,
            'total_utterances': len(utterances)
        }
    
    def format_context_for_prompt(self, context: ContextWindow, 
                                  metadata: Dict) -> Dict[str, str]:
        """
        Format context window for LLM prompt.
        
        Args:
            context: ContextWindow object
            metadata: Episode metadata
            
        Returns:
            Dictionary with formatted strings for prompt
        """
        try:
            # Format context before
            context_before_str = ""
            for i, utt in enumerate(context.context_before, 1):
                context_before_str += f"[{utt.get('start_time', '')}] {utt.get('speaker_id', '')}: \"{utt.get('text', '')}\"\n"
            
            # Format context after
            context_after_str = ""
            for i, utt in enumerate(context.context_after, 1):
                context_after_str += f"[{utt.get('start_time', '')}] {utt.get('speaker_id', '')}: \"{utt.get('text', '')}\"\n"
            
            return {
                'episode_id': metadata.get('episode_id', 'unknown'),
                'speaker_list': ', '.join(metadata.get('speakers', [])),
                'context_before': context_before_str.strip(),
                'context_after': context_after_str.strip(),
                'speaker_id': context.target_utterance.get('speaker_id', ''),
                'timestamp': context.target_utterance.get('start_time', ''),
                'statement_text': context.target_utterance.get('text', '')
            }
        except Exception as e:
            print(f"⚠️  Warning: Context formatting failed: {e}")
            return {
                'episode_id': metadata.get('episode_id', 'unknown'),
                'speaker_list': '',
                'context_before': '',
                'context_after': '',
                'speaker_id': '',
                'timestamp': '',
                'statement_text': ''
            }


