#!/usr/bin/env python3
"""
View belief rankings with weights in a formatted table.

Usage:
    python view_rankings.py output/beliefs_episode.csv
    python view_rankings.py output/beliefs_episode.csv --sort conviction
    python view_rankings.py output/beliefs_episode.csv --top 20
"""
import click
import pandas as pd
from pathlib import Path
from tabulate import tabulate


def truncate_text(text, max_length=60):
    """Truncate text to max length."""
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text


@click.command()
@click.argument('beliefs_file', type=click.Path(exists=True))
@click.option('--sort', '-s', 
              type=click.Choice(['importance', 'conviction', 'stability', 'tier']),
              default='importance',
              help='Sort by: importance (default), conviction, stability, or tier')
@click.option('--top', '-n', type=int, default=None,
              help='Show only top N beliefs')
@click.option('--speaker', type=str, default=None,
              help='Filter by speaker ID')
@click.option('--tier', type=str, default=None,
              help='Filter by tier name')
@click.option('--category', type=str, default=None,
              help='Filter by category')
@click.option('--sub-domain', 'sub_domain', type=str, default=None,
              help='Filter by sub-domain slug (case-insensitive)')
@click.option('--min-conviction', type=float, default=0.0,
              help='Minimum conviction score (0.0-1.0)')
@click.option('--export', type=click.Path(), default=None,
              help='Export filtered results to CSV')
@click.option('--format', 'output_format',
              type=click.Choice(['table', 'markdown', 'csv', 'json']),
              default='table',
              help='Output format')
def main(beliefs_file, sort, top, speaker, tier, category, sub_domain,
         min_conviction, export, output_format):
    """View belief rankings with weights."""
    
    # Load beliefs
    df = pd.read_csv(beliefs_file)
    
    print(f"\n{'='*100}")
    print(f"🎙️  BELIEF RANKINGS: {Path(beliefs_file).name}")
    print(f"{'='*100}\n")
    
    # Show summary stats
    print(f"📊 Summary Statistics:")
    print(f"   Total Beliefs: {len(df)}")
    print(f"   Speakers: {df['speaker_id'].nunique()}")
    print(f"   Avg Conviction: {df['conviction_score'].mean():.2f}")
    print(f"   Avg Stability: {df['stability_score'].mean():.2f}")
    print()
    
    # Apply filters
    filtered_df = df.copy()
    
    if speaker:
        filtered_df = filtered_df[filtered_df['speaker_id'] == speaker]
        print(f"🔍 Filtered by speaker: {speaker}")
    
    if tier:
        filtered_df = filtered_df[filtered_df['tier_name'].str.contains(tier, case=False)]
        print(f"🔍 Filtered by tier: {tier}")
    
    if category:
        filtered_df = filtered_df[filtered_df['category'] == category]
        print(f"🔍 Filtered by category: {category}")
    
    if sub_domain:
        if 'sub_domain' not in filtered_df.columns:
            filtered_df['sub_domain'] = 'general'
        filtered_df = filtered_df[
            filtered_df['sub_domain'].str.contains(sub_domain, case=False, na=False)
        ]
        print(f"🔍 Filtered by sub-domain: {sub_domain}")
    
    if min_conviction > 0:
        filtered_df = filtered_df[filtered_df['conviction_score'] >= min_conviction]
        print(f"🔍 Filtered by conviction >= {min_conviction}")
    
    if len(filtered_df) < len(df):
        print(f"   Results: {len(filtered_df)} beliefs")
        print()
    
    # Sort
    if sort == 'importance':
        filtered_df = filtered_df.sort_values('importance')
        sort_label = "Importance (Foundational → Casual)"
    elif sort == 'conviction':
        filtered_df = filtered_df.sort_values('conviction_score', ascending=False)
        sort_label = "Conviction (Strongest → Weakest)"
    elif sort == 'stability':
        filtered_df = filtered_df.sort_values('stability_score', ascending=False)
        sort_label = "Stability (Most Stable → Least Stable)"
    else:  # tier
        filtered_df = filtered_df.sort_values(['importance', 'conviction_score'], 
                                              ascending=[True, False])
        sort_label = "Tier + Conviction"
    
    # Limit results
    if top:
        filtered_df = filtered_df.head(top)
    
    # Prepare display data
    display_df = filtered_df.copy()
    if 'sub_domain' not in display_df.columns:
        display_df['sub_domain'] = 'general'
    display_df['statement'] = display_df['statement_text'].apply(lambda x: truncate_text(x, 50))
    display_df['conv'] = display_df['conviction_score'].apply(lambda x: f"{x:.2f}")
    display_df['stab'] = display_df['stability_score'].apply(lambda x: f"{x:.2f}")
    display_df['rank'] = display_df['importance']
    
    # Select columns for display
    display_cols = ['belief_id', 'speaker_id', 'rank', 'tier_name', 'category',
                    'sub_domain', 'conv', 'stab', 'statement']
    
    # Output based on format
    if output_format == 'table':
        print(f"📋 Rankings (sorted by {sort_label}):")
        print()
        print(tabulate(
            display_df[display_cols],
            headers=['ID', 'Speaker', 'Rank', 'Tier', 'Category', 'Sub-domain', 'Conv', 'Stab', 'Statement'],
            tablefmt='fancy_grid',
            showindex=False
        ))
    elif output_format == 'markdown':
        print(f"## Rankings (sorted by {sort_label})\n")
        print(tabulate(
            display_df[display_cols],
            headers=['ID', 'Speaker', 'Rank', 'Tier', 'Category', 'Sub-domain', 'Conv', 'Stab', 'Statement'],
            tablefmt='github',
            showindex=False
        ))
    elif output_format == 'csv':
        print(filtered_df.to_csv(index=False))
    elif output_format == 'json':
        print(filtered_df.to_json(orient='records', indent=2))
    
    # Tier breakdown
    if output_format in ['table', 'markdown']:
        print(f"\n{'='*100}")
        print(f"📊 Belief Breakdown by Tier:")
        print()
        
        tier_summary = filtered_df.groupby('tier_name').agg({
            'belief_id': 'count',
            'conviction_score': 'mean',
            'stability_score': 'mean'
        }).rename(columns={'belief_id': 'count'})
        tier_summary['avg_conv'] = tier_summary['conviction_score'].apply(lambda x: f"{x:.2f}")
        tier_summary['avg_stab'] = tier_summary['stability_score'].apply(lambda x: f"{x:.2f}")
        
        print(tabulate(
            tier_summary[['count', 'avg_conv', 'avg_stab']],
            headers=['Tier', 'Count', 'Avg Conv', 'Avg Stab'],
            tablefmt='fancy_grid'
        ))
    
    # Export if requested
    if export:
        filtered_df.to_csv(export, index=False)
        print(f"\n💾 Exported {len(filtered_df)} beliefs to: {export}")
    
    print(f"\n{'='*100}\n")


if __name__ == '__main__':
    main()

