#!/usr/bin/env python3
"""
Main script for belief extraction from podcast transcripts.

Usage:
    python run_extraction.py --transcript input.txt --episode-id e_001
    python run_extraction.py --transcript input.txt --cheap-mode
    python run_extraction.py --help
"""
import click
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from src.extractor import BeliefExtractor
from src.wandb_logger import WandbLogger


# Load environment variables
load_dotenv()


@click.command()
@click.option('--transcript', '-t', required=True, type=click.Path(exists=True),
              help='Path to diarized transcript file')
@click.option('--episode-id', '-e', default=None,
              help='Episode identifier (e.g., e_jre_2404)')
@click.option('--cheap-mode', is_flag=True,
              help='Process only first 1000 words for testing')
@click.option('--max-words', default=1000, type=int,
              help='Max words for cheap mode (default: 1000)')
@click.option('--model', default='gpt-4o-mini',
              help='OpenAI model to use (default: gpt-4o-mini)')
@click.option('--output', '-o', default=None,
              help='Output file path (default: output/beliefs_{episode_id}.csv)')
@click.option('--format', '-f', type=click.Choice(['csv', 'json', 'parquet']),
              default='csv', help='Output format (default: csv)')
@click.option('--no-wandb', is_flag=True,
              help='Skip W&B logging')
@click.option('--config', type=click.Path(exists=True),
              default='config/settings.yaml',
              help='Config file path')
def main(transcript, episode_id, cheap_mode, max_words, model, output,
         format, no_wandb, config):
    """Extract beliefs from diarized podcast transcripts."""
    
    # Banner
    print("=" * 60)
    print("🎙️  Podcast Belief Extraction Pipeline")
    print("=" * 60)
    
    # Load config
    if Path(config).exists():
        with open(config, 'r') as f:
            cfg = yaml.safe_load(f)
    else:
        cfg = {}
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        click.echo("❌ Error: OPENAI_API_KEY not found in environment", err=True)
        click.echo("   Create .env file with: OPENAI_API_KEY=your-key-here", err=True)
        return
    
    # Determine episode_id
    if not episode_id:
        episode_id = Path(transcript).stem.replace(' ', '_')[:30]
    
    # Determine output path
    if not output:
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        output = output_dir / f'beliefs_{episode_id}.{format}'
    
    # Initialize W&B
    wandb_logger = None
    if not no_wandb and os.getenv('WANDB_MODE') != 'disabled':
        run_name = f"{episode_id}_{'cheap' if cheap_mode else 'full'}"
        tags = ['cheap-mode'] if cheap_mode else []
        
        wandb_config = {
            'episode_id': episode_id,
            'model': model,
            'cheap_mode': cheap_mode,
            'max_words': max_words if cheap_mode else None,
            'transcript_file': str(transcript)
        }
        
        wandb_logger = WandbLogger(
            project=cfg.get('wandb', {}).get('project', 'podcast-belief-extraction'),
            entity=cfg.get('wandb', {}).get('entity'),
            config=wandb_config,
            name=run_name,
            tags=tags
        )
        print(f"✅ W&B initialized")
    
    # Initialize extractor
    print(f"\n⚙️  Configuration:")
    print(f"   Transcript: {transcript}")
    print(f"   Episode ID: {episode_id}")
    print(f"   Model: {model}")
    print(f"   Cheap mode: {'Yes (' + str(max_words) + ' words)' if cheap_mode else 'No'}")
    print(f"   Output: {output}")
    print()
    
    extractor = BeliefExtractor(
        api_key=api_key,
        model=model,
        prompts_dir='prompts'
    )
    
    # Extract beliefs
    print(f"🚀 Starting extraction...")
    df = extractor.extract_from_file(
        transcript_path=transcript,
        episode_id=episode_id,
        cheap_mode=cheap_mode,
        max_words=max_words
    )
    
    # Save output
    extractor.save_output(df, output, format=format)
    
    # Get statistics
    cost_stats = extractor.get_cost_stats()
    summary_stats = extractor.get_summary_stats(df)
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"   Total beliefs: {summary_stats['total_beliefs']}")
    print(f"   Unique speakers: {len(summary_stats['beliefs_per_speaker'])}")
    print(f"   Avg conviction: {summary_stats['avg_conviction']:.2f}")
    print(f"   Avg stability: {summary_stats['avg_stability']:.2f}")
    print(f"\n💰 Cost:")
    print(f"   Total tokens: {cost_stats['total_tokens']}")
    print(f"   Total cost: ${cost_stats['total_cost']:.4f}")
    
    # Log to W&B
    if wandb_logger:
        print(f"\n📤 Logging to W&B...")
        wandb_logger.log_beliefs_table(df)
        wandb_logger.log_metrics(summary_stats)
        wandb_logger.log_cost(cost_stats)
        wandb_logger.log_all_visualizations(df)
        wandb_logger.log_artifacts(
            transcript_path=transcript,
            output_path=str(output)
        )
        wandb_logger.finish()
    
    print(f"\n✅ Done! Beliefs saved to: {output}")
    print("=" * 60)


if __name__ == '__main__':
    main()

