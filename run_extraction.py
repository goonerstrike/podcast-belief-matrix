#!/usr/bin/env python3
"""
Main script for belief extraction from podcast transcripts.

Usage:
    # Process transcript from input/ directory (default)
    python run_extraction.py
    python run_extraction.py --cheap-mode
    
    # Process specific file (override)
    python run_extraction.py --transcript path/to/file.txt --episode-id e_001
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
@click.option('--transcript', '-t', type=click.Path(exists=True), default=None,
              help='Single transcript file to process (overrides --input-dir)')
@click.option('--input-dir', '-i', type=click.Path(exists=True), default='input',
              help='Directory containing transcript files (default: input/)')
@click.option('--episode-id', '-e', default=None,
              help='Episode identifier (only used with --transcript)')
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
def main(transcript, input_dir, episode_id, cheap_mode, max_words, model, output,
         format, no_wandb, config):
    """Extract beliefs from diarized podcast transcripts.
    
    By default, scans input/ directory and processes the first .txt file found.
    Use --transcript to process a specific file instead.
    """
    
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
    
    # Determine which transcript to process
    if transcript:
        # Single file override
        transcript_path = transcript
        print(f"📄 Processing single transcript: {transcript}\n")
    else:
        # Scan input directory
        input_path = Path(input_dir)
        txt_files = sorted(input_path.glob('*.txt'))
        
        if not txt_files:
            click.echo(f"❌ No .txt files found in {input_dir}/", err=True)
            click.echo(f"   Drop transcript files in {input_dir}/ directory", err=True)
            return
        
        if len(txt_files) > 1:
            print(f"📂 Found {len(txt_files)} transcript(s) in {input_dir}/")
            for idx, txt_file in enumerate(txt_files, 1):
                print(f"   {idx}. {txt_file.name}")
            print(f"\n⚠️  Processing first file: {txt_files[0].name}")
            print(f"   (Use run_multilevel_extraction.py for batch processing)\n")
        else:
            print(f"📂 Found transcript: {txt_files[0].name}\n")
        
        transcript_path = str(txt_files[0])
    
    # Determine episode_id
    if not episode_id:
        episode_id = Path(transcript_path).stem.replace(' ', '_').replace('-', '_')[:50]
    
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
            'transcript_file': str(transcript_path)
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
    print(f"   Transcript: {transcript_path}")
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
        transcript_path=transcript_path,
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
            transcript_path=transcript_path,
            output_path=str(output)
        )
        wandb_logger.finish()
    
    print(f"\n✅ Done! Beliefs saved to: {output}")
    print("=" * 60)


if __name__ == '__main__':
    main()

