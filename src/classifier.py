"""
Two-stage belief classification system.
Stage 1: Filter for beliefs
Stage 2: Classify belief details
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from openai import OpenAI


@dataclass
class BeliefClassification:
    """Result of belief classification."""
    # Core fields
    speaker_id: str
    timestamp: str
    statement_text: str
    
    # Stage 1 results
    is_belief: bool
    filter_confidence: float
    
    # Atomic belief extraction (NEW)
    atomic_belief: Optional[str] = None
    certainty: Optional[str] = None  # "binary" or "hedged"
    
    # Stage 2 results (only if is_belief=True)
    tier_name: Optional[str] = None
    importance: Optional[int] = None
    conviction_score: Optional[float] = None
    stability_score: Optional[float] = None
    category: Optional[str] = None
    parent_hint: Optional[str] = None
    defines_outgroup: Optional[bool] = None
    
    # Full question responses
    stage1_responses: Optional[Dict] = None
    stage2_responses: Optional[Dict] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'speaker_id': self.speaker_id,
            'timestamp': self.timestamp,
            'statement_text': self.statement_text,
            'is_belief': self.is_belief,
            'filter_confidence': self.filter_confidence,
            'atomic_belief': self.atomic_belief,
            'certainty': self.certainty,
            'tier_name': self.tier_name,
            'importance': self.importance,
            'conviction_score': self.conviction_score,
            'stability_score': self.stability_score,
            'category': self.category,
            'parent_hint': self.parent_hint,
            'defines_outgroup': self.defines_outgroup,
            'stage1_responses': self.stage1_responses,
            'stage2_responses': self.stage2_responses
        }


class BeliefClassifier:
    """Two-stage belief classifier."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", 
                 temperature: float = 0.1, prompts_dir: str = "prompts"):
        """
        Initialize classifier.
        
        Args:
            api_key: OpenAI API key
            model: Model to use
            temperature: Temperature for generation
            prompts_dir: Directory containing prompt templates
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.prompts_dir = Path(prompts_dir)
        
        # Load prompts
        self.stage1_prompt = self._load_prompt("stage1_filter.txt")
        self.stage2_prompt = self._load_prompt("stage2_classify.txt")
        self.atomic_extraction_prompt = self._load_prompt("atomic_belief_extraction.txt")
        
        # Cost tracking
        self.total_tokens = 0
        self.total_cost = 0.0
        
    def _load_prompt(self, filename: str) -> str:
        """Load prompt template from file."""
        filepath = self.prompts_dir / filename
        with open(filepath, 'r') as f:
            return f.read()
    
    def _call_llm(self, prompt: str) -> Tuple[str, int, int]:
        """
        Call OpenAI API.
        
        Returns:
            (response_text, prompt_tokens, completion_tokens)
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        # Update cost tracking (gpt-4o-mini pricing)
        cost = (prompt_tokens * 0.00015 / 1000) + (completion_tokens * 0.0006 / 1000)
        self.total_tokens += (prompt_tokens + completion_tokens)
        self.total_cost += cost
        
        return content, prompt_tokens, completion_tokens
    
    def stage1_filter(self, speaker_id: str, timestamp: str, 
                     statement_text: str) -> Dict:
        """
        Stage 1: Filter if statement is a belief.
        
        Returns:
            Dictionary with filter results
        """
        prompt = self.stage1_prompt.format(
            speaker_id=speaker_id,
            timestamp=timestamp,
            statement_text=statement_text
        )
        
        response, _, _ = self._call_llm(prompt)
        
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "is_belief": False,
                "confidence": 0.0,
                "reasoning": "Failed to parse LLM response"
            }
    
    def stage2_classify(self, speaker_id: str, timestamp: str,
                       statement_text: str) -> Dict:
        """
        Stage 2: Classify belief details.
        
        Returns:
            Dictionary with classification results
        """
        prompt = self.stage2_prompt.format(
            speaker_id=speaker_id,
            timestamp=timestamp,
            statement_text=statement_text
        )
        
        response, _, _ = self._call_llm(prompt)
        
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # Fallback
            return {
                "tier_name": "Unknown",
                "importance": 10,
                "conviction_score": 0.5,
                "stability_score": 0.5,
                "category": "other",
                "parent_hint": "",
                "defines_outgroup": False
            }
    
    def extract_atomic_beliefs(self, speaker_id: str, timestamp: str,
                               statement_text: str) -> List[Dict]:
        """
        Extract atomic beliefs from a statement.
        
        Args:
            speaker_id: Speaker identifier
            timestamp: Time in transcript
            statement_text: The statement to analyze
            
        Returns:
            List of dicts with 'belief' and 'certainty' keys
        """
        prompt = self.atomic_extraction_prompt.format(
            speaker_id=speaker_id,
            timestamp=timestamp,
            statement_text=statement_text
        )
        
        response, _, _ = self._call_llm(prompt)
        
        try:
            result = json.loads(response)
            return result.get("atomic_beliefs", [])
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return []
    
    def classify(self, speaker_id: str, timestamp: str,
                statement_text: str) -> BeliefClassification:
        """
        Full two-stage classification.
        
        Args:
            speaker_id: Speaker identifier
            timestamp: Time in transcript
            statement_text: The statement to classify
            
        Returns:
            BeliefClassification object
        """
        # Stage 1: Filter
        stage1 = self.stage1_filter(speaker_id, timestamp, statement_text)
        
        is_belief = stage1.get("is_belief", False)
        confidence = stage1.get("confidence", 0.0)
        
        if not is_belief:
            # Not a belief, skip stage 2 and atomic extraction
            return BeliefClassification(
                speaker_id=speaker_id,
                timestamp=timestamp,
                statement_text=statement_text,
                is_belief=False,
                filter_confidence=confidence,
                stage1_responses=stage1
            )
        
        # Extract atomic beliefs
        atomic_beliefs = self.extract_atomic_beliefs(speaker_id, timestamp, statement_text)
        
        # Use first atomic belief if available, otherwise use original statement
        atomic_belief = None
        certainty = None
        if atomic_beliefs and len(atomic_beliefs) > 0:
            atomic_belief = atomic_beliefs[0].get("belief")
            certainty = atomic_beliefs[0].get("certainty")
        
        # Stage 2: Classify
        stage2 = self.stage2_classify(speaker_id, timestamp, statement_text)
        
        return BeliefClassification(
            speaker_id=speaker_id,
            timestamp=timestamp,
            statement_text=statement_text,
            is_belief=True,
            filter_confidence=confidence,
            atomic_belief=atomic_belief,
            certainty=certainty,
            tier_name=stage2.get("tier_name"),
            importance=stage2.get("importance"),
            conviction_score=stage2.get("conviction_score"),
            stability_score=stage2.get("stability_score"),
            category=stage2.get("category"),
            parent_hint=stage2.get("parent_hint", ""),
            defines_outgroup=stage2.get("defines_outgroup"),
            stage1_responses=stage1,
            stage2_responses=stage2
        )
    
    def classify_batch(self, utterances: List[Dict]) -> List[BeliefClassification]:
        """
        Classify multiple utterances.
        
        Args:
            utterances: List of dicts with speaker_id, timestamp, text
            
        Returns:
            List of BeliefClassification objects
        """
        results = []
        
        for utterance in utterances:
            classification = self.classify(
                speaker_id=utterance['speaker_id'],
                timestamp=utterance.get('start_time', utterance.get('timestamp', '')),
                statement_text=utterance['text']
            )
            results.append(classification)
        
        return results
    
    def get_cost_stats(self) -> Dict:
        """Get cost statistics."""
        return {
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'model': self.model
        }

