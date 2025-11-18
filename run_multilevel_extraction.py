#!/usr/bin/env python3
"""
Multi-level belief extraction CLI.
Processes transcripts at multiple abstraction levels.

Usage:
    # Batch process all transcripts in input/ directory (default)
    python run_multilevel_extraction.py
    python run_multilevel_extraction.py --cheap-mode
    
    # Process single transcript (override)
    python run_multilevel_extraction.py --transcript path/to/file.txt --episode-id e_001
    
    # Custom input directory
    python run_multilevel_extraction.py --input-dir my_transcripts/
"""
import click
import os
import yaml
import glob
import time
from pathlib import Path
from dotenv import load_dotenv
from src.multilevel_extractor import MultiLevelExtractor
from src.belief_merger import BeliefMerger
from src.belief_linker import BeliefLinker
from src.wandb_logger import WandbLogger
from src.belief_analyzer_stats import BeliefStatsAnalyzer
from src.belief_graph_metrics import BeliefGraphMetrics

# Load environment variables
load_dotenv()


def _build_quality_metrics(df_raw, df_dedup, df_linked, mapping_df, hierarchy_stats):
    """Assemble quality metrics for logging."""
    metrics = {
        'raw_beliefs': len(df_raw),
        'post_dedup_beliefs': len(df_dedup),
        'final_beliefs': len(df_linked),
        'retention_rate': round((len(df_linked) / len(df_raw) * 100), 2) if len(df_raw) else 0.0
    }

    if mapping_df is not None and not mapping_df.empty:
        if 'duplicate_group_id' in mapping_df.columns:
            metrics['dedup_duplicate_groups'] = int(mapping_df['duplicate_group_id'].nunique())
        if 'reinforcement_count' in mapping_df.columns:
            metrics['dedup_avg_reinforcement'] = float(round(mapping_df['reinforcement_count'].mean(), 2))
        metrics['duplicate_samples'] = mapping_df.head(25).to_dict(orient='records')

    if hierarchy_stats:
        for key, value in hierarchy_stats.items():
            metrics[f'hierarchy_{key}'] = value

    return metrics


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
@click.option('--workers', default=1, type=int,
              help='Number of parallel workers for API calls (default: 1, recommended: 4)')
@click.option('--no-wandb', is_flag=True,
              help='Skip W&B logging')
@click.option('--config', type=click.Path(exists=True),
              default='config/settings.yaml',
              help='Config file path')
def main(transcript, input_dir, episode_id, cheap_mode, max_words, model, output_dir,
         no_dedup, no_linking, dedup_threshold, levels, workers, no_wandb, config):
    """Multi-level belief extraction from podcast transcripts.
    
    By default, scans input/ directory and processes all .txt files.
    Use --transcript to process a single file instead.
    """
    
    # Banner
    print("=" * 80)
    print("🌐 Multi-Level Podcast Belief Extraction Pipeline")
    print("=" * 80)
    
    # Validate workers
    if workers > 10:
        click.echo("⚠️  WARNING: Using more than 10 workers may hit OpenAI rate limits", err=True)
        click.echo("   Recommended: 4-6 workers for optimal performance", err=True)
    
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
    
    stats_analyzer = BeliefStatsAnalyzer()
    graph_metrics_analyzer = BeliefGraphMetrics()

    # Determine which transcripts to process
    transcripts_to_process = []
    
    if transcript:
        # Single file override
        transcripts_to_process = [(transcript, episode_id)]
        print(f"📄 Processing single transcript: {transcript}\n")
    else:
        # Batch mode: scan input directory
        input_path = Path(input_dir)
        txt_files = sorted(input_path.glob('*.txt'))
        
        if not txt_files:
            click.echo(f"❌ No .txt files found in {input_dir}/", err=True)
            click.echo(f"   Drop transcript files in {input_dir}/ directory", err=True)
            return
        
        print(f"📂 Found {len(txt_files)} transcript(s) in {input_dir}/")
        for txt_file in txt_files:
            # Auto-generate episode_id from filename
            auto_episode_id = txt_file.stem.replace(' ', '_').replace('-', '_')[:50]
            transcripts_to_process.append((str(txt_file), auto_episode_id))
            print(f"   - {txt_file.name} → {auto_episode_id}")
        print()
    
    # Process each transcript
    for idx, (transcript_path, auto_episode_id) in enumerate(transcripts_to_process, 1):
        if len(transcripts_to_process) > 1:
            print(f"\n{'='*80}")
            print(f"📝 Processing {idx}/{len(transcripts_to_process)}: {Path(transcript_path).name}")
            print(f"{'='*80}\n")
        
        # Use auto_episode_id
        episode_id = auto_episode_id
        
        # Parse levels
        if levels:
            level_list = [int(x.strip()) for x in levels.split(',')]
        else:
            level_list = None  # Use defaults
        
        # Create per-episode output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        run_output_dir = output_path / episode_id
        run_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize W&B
        wandb_logger = None
        if not no_wandb and os.getenv('WANDB_MODE') != 'disabled':
            run_name = f"{episode_id}_multilevel_{'cheap' if cheap_mode else 'full'}_w{workers}"
            tags = ['multi-level']
            if cheap_mode:
                tags.append('cheap-mode')
            # Add benchmark tags if this is a benchmark run
            if 'bench_' in episode_id:
                tags.extend(['benchmark', 'worker-comparison'])
            
            wandb_config = {
                'episode_id': episode_id,
                'model': model,
                'cheap_mode': cheap_mode,
                'max_words': max_words if cheap_mode else None,
                'deduplication': not no_dedup,
                'linking': not no_linking,
                'levels': level_list,
                'workers': workers,
                'transcript_file': transcript_path
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
        print(f"   Workers: {workers} {'(parallel)' if workers > 1 else '(sequential)'}")
        print(f"   Cheap mode: {'Yes (' + str(max_words) + ' words)' if cheap_mode else 'No'}")
        print(f"   Deduplication: {'Disabled' if no_dedup else f'Enabled (threshold: {dedup_threshold})'}")
        print(f"   Belief linking: {'Disabled' if no_linking else 'Enabled'}")
        print(f"   Levels: {level_list if level_list else 'Default (exponential)'}")
        print()
        
        extractor = MultiLevelExtractor(
            api_key=api_key,
            model=model,
            prompts_dir='prompts',
            max_workers=workers
        )
        
        # Extract beliefs at all levels
        print(f"🚀 Starting multi-level extraction...")
        start_time = time.time()
        df_raw = extractor.extract_multilevel(
            transcript_path=transcript_path,
            episode_id=episode_id,
            levels=level_list,
            max_words=max_words if cheap_mode else None
        )
        end_time = time.time()
        total_extraction_time = end_time - start_time
        
        # Save raw beliefs
        raw_output = run_output_dir / f'beliefs_multilevel_{episode_id}.csv'
        extractor.save_output(df_raw, raw_output)
        
        # Deduplication
        df_dedup = df_raw
        mapping_df = None
        if not no_dedup and len(df_raw) > 1:
            merger = BeliefMerger(similarity_threshold=dedup_threshold)
            df_dedup, mapping_df = merger.merge_beliefs(df_raw, keep_strategy="all")
            
            # Save deduplicated beliefs
            dedup_output = run_output_dir / f'beliefs_deduplicated_{episode_id}.csv'
            df_dedup.to_csv(dedup_output, index=False)
            print(f"💾 Saved deduplicated beliefs to {dedup_output}")
            
            if mapping_df is not None and not mapping_df.empty:
                mapping_output = run_output_dir / f'belief_mapping_{episode_id}.csv'
                mapping_df.to_csv(mapping_output, index=False)
                print(f"💾 Saved duplicate mapping to {mapping_output}")
        
        # Belief linking
        df_linked = df_dedup
        hierarchy_stats = {}
        linked_output = run_output_dir / f'beliefs_linked_{episode_id}.csv'
        if not no_linking:
            linker = BeliefLinker()
            df_linked = linker.link_beliefs(df_dedup)
            
            # Get hierarchy stats
            hierarchy_stats = linker.get_hierarchy_stats(df_linked)
            print(f"\n🌳 Hierarchy Statistics:")
            for key, value in hierarchy_stats.items():
                print(f"   {key}: {value}")
            
            # Save linked beliefs
            df_linked.to_csv(linked_output, index=False)
            print(f"💾 Saved linked beliefs to {linked_output}")
        else:
            df_linked.to_csv(linked_output, index=False)
            print(f"💾 Saved beliefs (linking skipped) to {linked_output}")
        
        stats_payload = stats_analyzer.analyze(df_linked)
        graph_metrics = graph_metrics_analyzer.analyze(df_linked)
        quality_metrics = _build_quality_metrics(df_raw, df_dedup, df_linked, mapping_df, hierarchy_stats)
        
        # Get cost statistics
        cost_stats = extractor.get_cost_stats()
        
        # Calculate performance metrics
        total_chunks = len(df_raw)  # Each row is a chunk that was processed
        throughput = total_chunks / total_extraction_time if total_extraction_time > 0 else 0
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"📊 Summary:")
        print(f"   Total beliefs (raw): {len(df_raw)}")
        if not no_dedup:
            print(f"   After deduplication: {len(df_dedup)}")
        print(f"   Final output: {len(df_linked)}")
        print(f"\n⏱️  Performance:")
        print(f"   Extraction time: {total_extraction_time:.2f}s")
        print(f"   Throughput: {throughput:.2f} chunks/sec")
        print(f"   Workers: {workers}")
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
            wandb_logger.log_statistical_analysis(stats_payload)
            wandb_logger.log_graph_metrics(graph_metrics)
            wandb_logger.log_quality_metrics(quality_metrics)
            
            # Log performance metrics
            performance_stats = {
                'total_time': total_extraction_time,
                'workers': workers,
                'total_chunks': total_chunks,
                'throughput': throughput
            }
            wandb_logger.log_performance(performance_stats)
            
            # Log artifacts
            wandb_logger.log_artifacts(
                transcript_path=transcript_path,
                output_path=str(linked_output)
            )
            
            wandb_logger.finish()
        
        # Dashboard generation disabled (handled separately)
        print("ℹ️  Local dashboard generation is currently disabled. Use W&B for analytics.")
        print(f"\n✅ Done! Final beliefs saved to: {linked_output}")


if __name__ == '__main__':
    main()

