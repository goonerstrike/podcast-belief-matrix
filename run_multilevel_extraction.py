#!/usr/bin/env python3
"""
Multi-level belief extraction CLI.
Processes transcripts at multiple abstraction levels.

Usage:
    python run_multilevel_extraction.py --transcript input.txt --episode-id e_001
    python run_multilevel_extraction.py --transcript input.txt --cheap-mode
    python run_multilevel_extraction.py --help
"""
import click
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from src.multilevel_extractor import MultiLevelExtractor
from src.belief_merger import BeliefMerger
from src.belief_linker import BeliefLinker
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
@click.option('--output-dir', '-o', default='output',
              help='Output directory (default: output/)')
@click.option('--no-dedup', is_flag=True,
              help='Skip deduplication step')
@click.option('--no-linking', is_flag=True,
              help='Skip belief linking step')
@click.option('--dedup-threshold', default=0.85, type=float,
              help='Similarity threshold for deduplication (default: 0.85)')
@click.option('--levels', default=None,
              help='Comma-separated list of chunk sizes (e.g., "1,2,4,8")')
@click.option('--no-wandb', is_flag=True,
              help='Skip W&B logging')
@click.option('--config', type=click.Path(exists=True),
              default='config/settings.yaml',
              help='Config file path')
def main(transcript, episode_id, cheap_mode, max_words, model, output_dir,
         no_dedup, no_linking, dedup_threshold, levels, no_wandb, config):
    """Multi-level belief extraction from podcast transcripts."""
    
    # Banner
    print("=" * 80)
    print("🌐 Multi-Level Podcast Belief Extraction Pipeline")
    print("=" * 80)
    
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
    
    # Parse levels
    if levels:
        level_list = [int(x.strip()) for x in levels.split(',')]
    else:
        level_list = None  # Use defaults
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Initialize W&B
    wandb_logger = None
    if not no_wandb and os.getenv('WANDB_MODE') != 'disabled':
        run_name = f"{episode_id}_multilevel_{'cheap' if cheap_mode else 'full'}"
        tags = ['multi-level']
        if cheap_mode:
            tags.append('cheap-mode')
        
        wandb_config = {
            'episode_id': episode_id,
            'model': model,
            'cheap_mode': cheap_mode,
            'max_words': max_words if cheap_mode else None,
            'deduplication': not no_dedup,
            'linking': not no_linking,
            'levels': level_list,
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
    print(f"   Deduplication: {'Disabled' if no_dedup else f'Enabled (threshold: {dedup_threshold})'}")
    print(f"   Belief linking: {'Disabled' if no_linking else 'Enabled'}")
    print(f"   Levels: {level_list if level_list else 'Default (exponential)'}")
    print()
    
    extractor = MultiLevelExtractor(
        api_key=api_key,
        model=model,
        prompts_dir='prompts'
    )
    
    # Extract beliefs at all levels
    print(f"🚀 Starting multi-level extraction...")
    df_raw = extractor.extract_multilevel(
        transcript_path=transcript,
        episode_id=episode_id,
        levels=level_list,
        max_words=max_words if cheap_mode else None
    )
    
    # Save raw beliefs
    raw_output = output_dir / f'beliefs_multilevel_{episode_id}.csv'
    extractor.save_output(df_raw, raw_output)
    
    # Deduplication
    df_dedup = df_raw
    mapping_df = None
    if not no_dedup and len(df_raw) > 1:
        merger = BeliefMerger(similarity_threshold=dedup_threshold)
        df_dedup, mapping_df = merger.merge_beliefs(df_raw, keep_strategy="all")
        
        # Save deduplicated beliefs
        dedup_output = output_dir / f'beliefs_deduplicated_{episode_id}.csv'
        df_dedup.to_csv(dedup_output, index=False)
        print(f"💾 Saved deduplicated beliefs to {dedup_output}")
        
        if mapping_df is not None and not mapping_df.empty:
            mapping_output = output_dir / f'belief_mapping_{episode_id}.csv'
            mapping_df.to_csv(mapping_output, index=False)
            print(f"💾 Saved duplicate mapping to {mapping_output}")
    
    # Belief linking
    df_linked = df_dedup
    if not no_linking:
        linker = BeliefLinker()
        df_linked = linker.link_beliefs(df_dedup)
        
        # Get hierarchy stats
        hierarchy_stats = linker.get_hierarchy_stats(df_linked)
        print(f"\n🌳 Hierarchy Statistics:")
        for key, value in hierarchy_stats.items():
            print(f"   {key}: {value}")
        
        # Save linked beliefs
        linked_output = output_dir / f'beliefs_linked_{episode_id}.csv'
        df_linked.to_csv(linked_output, index=False)
        print(f"💾 Saved linked beliefs to {linked_output}")
    
    # Get cost statistics
    cost_stats = extractor.get_cost_stats()
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"📊 Summary:")
    print(f"   Total beliefs (raw): {len(df_raw)}")
    if not no_dedup:
        print(f"   After deduplication: {len(df_dedup)}")
    print(f"   Final output: {len(df_linked)}")
    print(f"\n💰 Cost:")
    print(f"   Total tokens: {cost_stats['total_tokens']}")
    print(f"   Total cost: ${cost_stats['total_cost']:.4f}")
    print(f"{'='*80}\n")
    
    # Log to W&B
    if wandb_logger:
        print(f"📤 Logging to W&B...")
        wandb_logger.log_beliefs_table(df_linked)
        
        # Log metrics
        metrics = {
            'total_beliefs_raw': len(df_raw),
            'total_beliefs_final': len(df_linked),
            'unique_speakers': int(df_linked['speaker_id'].nunique()),
            'avg_conviction': float(df_linked['conviction_score'].mean()),
            'avg_stability': float(df_linked['stability_score'].mean()),
        }
        
        if 'discovery_level' in df_linked.columns:
            for level in df_linked['discovery_level'].unique():
                count = len(df_linked[df_linked['discovery_level'] == level])
                metrics[f'beliefs_level_{level}'] = count
        
        wandb_logger.log_metrics(metrics)
        wandb_logger.log_cost(cost_stats)
        
        # Log visualizations if we have beliefs
        if len(df_linked) > 0:
            wandb_logger.log_all_visualizations(df_linked)
        
        # Log artifacts
        wandb_logger.log_artifacts(
            transcript_path=transcript,
            output_path=str(linked_output)
        )
        
        wandb_logger.finish()
    
    # Generate and auto-open dashboard
    if len(df_linked) > 0:
        import webbrowser
        from src.dashboard_generator import generate_dashboard_html
        
        dashboard_path = output_dir / f'dashboard_{episode_id}.html'
        
        print(f"\n🎨 Generating dashboard...")
        try:
            generated_html = generate_dashboard_html(
                csv_path=str(linked_output),
                output_html_path=str(dashboard_path),
                episode_id=episode_id
            )
            print(f"💾 Dashboard saved to: {dashboard_path}")
            
            # Auto-open in browser
            print(f"🚀 Opening dashboard in browser...")
            webbrowser.open(f'file://{generated_html}')
            print(f"📊 Dashboard opened!")
        except Exception as e:
            print(f"⚠️  Dashboard generation failed: {e}")
            print(f"   You can still view results in: {linked_output}")
    
    print(f"\n✅ Done! Final beliefs saved to: {linked_output}")


if __name__ == '__main__':
    main()

