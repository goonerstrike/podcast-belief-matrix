#!/usr/bin/env python3
"""
Belief analysis CLI.
Analyze belief CSVs and generate insights.

Usage:
    python analyze_beliefs.py beliefs.csv
    python analyze_beliefs.py beliefs.csv --export-metrics
    python analyze_beliefs.py beliefs.csv --export-graph --export-report
"""
import click
import pandas as pd
from pathlib import Path
from src.belief_analyzer import BeliefAnalyzer
from src.belief_graph import BeliefGraph
from src.insight_generator import InsightGenerator


@click.command()
@click.argument('beliefs_file', type=click.Path(exists=True))
@click.option('--export-metrics', is_flag=True,
              help='Export beliefs with calculated metrics to CSV')
@click.option('--export-graph', is_flag=True,
              help='Export belief graph to JSON and GraphML')
@click.option('--export-report', is_flag=True,
              help='Export insight report to markdown')
@click.option('--output-dir', default='output/analysis',
              help='Output directory for exports (default: output/analysis)')
@click.option('--show-keystone', type=int, default=5,
              help='Number of keystone beliefs to show (default: 5)')
@click.option('--show-patterns', is_flag=True,
              help='Display identified patterns')
def main(beliefs_file, export_metrics, export_graph, export_report, 
         output_dir, show_keystone, show_patterns):
    """Analyze beliefs and generate insights."""
    
    # Banner
    print("=" * 80)
    print("📊 Belief Matrix Analysis")
    print("=" * 80)
    
    # Load beliefs
    print(f"\n📂 Loading beliefs from: {beliefs_file}")
    df = pd.read_csv(beliefs_file)
    print(f"   Loaded {len(df)} beliefs")
    
    if df.empty:
        print("⚠️  No beliefs to analyze")
        return
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run analysis
    analyzer = BeliefAnalyzer()
    df_with_metrics, summary_stats = analyzer.analyze(df)
    
    # Display summary
    print(f"\n{'='*80}")
    print(f"📈 Summary Statistics")
    print(f"{'='*80}")
    print(f"Total beliefs: {summary_stats['total_beliefs']}")
    print(f"Avg conviction: {summary_stats['avg_conviction']:.3f}")
    print(f"Avg stability: {summary_stats['avg_stability']:.3f}")
    print(f"Avg belief strength: {summary_stats['avg_belief_strength']:.3f}")
    print(f"Avg rigidity: {summary_stats['avg_rigidity']:.3f}")
    print(f"\nUnique speakers: {summary_stats['unique_speakers']}")
    print(f"Root beliefs: {summary_stats['root_beliefs']}")
    print(f"Leaf beliefs: {summary_stats['leaf_beliefs']}")
    
    # Show tier distribution
    print(f"\n{'='*80}")
    print(f"📊 Belief Distribution by Tier")
    print(f"{'='*80}")
    for tier, count in sorted(summary_stats['beliefs_per_tier'].items(), 
                              key=lambda x: x[1], reverse=True):
        pct = (count / summary_stats['total_beliefs']) * 100
        print(f"   {tier:30s}: {count:4d} ({pct:5.1f}%)")
    
    # Show category distribution  
    print(f"\n{'='*80}")
    print(f"📊 Belief Distribution by Category")
    print(f"{'='*80}")
    for category, count in sorted(summary_stats['beliefs_per_category'].items(),
                                  key=lambda x: x[1], reverse=True):
        pct = (count / summary_stats['total_beliefs']) * 100
        print(f"   {category.capitalize():20s}: {count:4d} ({pct:5.1f}%)")
    
    # Build graph
    graph_builder = BeliefGraph()
    graph = graph_builder.build_graph(df_with_metrics)
    
    # Calculate centrality
    centrality_df = graph_builder.calculate_centrality_metrics()
    
    # Show keystone beliefs
    if show_keystone > 0:
        print(f"\n{'='*80}")
        print(f"🔑 Top {show_keystone} Keystone Beliefs (by PageRank)")
        print(f"{'='*80}")
        top_keystone = centrality_df.nlargest(show_keystone, 'pagerank')
        for i, (_, belief) in enumerate(top_keystone.iterrows(), 1):
            print(f"\n{i}. {belief['statement'][:80]}...")
            print(f"   Tier: {belief['tier']}")
            print(f"   PageRank: {belief['pagerank']:.4f}")
            print(f"   In-degree: {belief['in_degree']} | Out-degree: {belief['out_degree']}")
    
    # Show graph stats
    graph_stats = graph_builder.get_graph_stats()
    print(f"\n{'='*80}")
    print(f"🕸️  Graph Statistics")
    print(f"{'='*80}")
    for key, value in graph_stats.items():
        print(f"   {key}: {value}")
    
    # Show patterns
    if show_patterns and 'patterns' in summary_stats:
        patterns = summary_stats['patterns']
        print(f"\n{'='*80}")
        print(f"🔍 Identified Patterns")
        print(f"{'='*80}")
        
        if patterns.get('core_worldview_count', 0) > 0:
            print(f"\n🏛️  Core Worldview: {patterns['core_worldview_count']} beliefs")
            for belief in patterns.get('core_worldview_beliefs', [])[:3]:
                print(f"   - \"{belief}\"")
        
        if patterns.get('vulnerable_beliefs_count', 0) > 0:
            print(f"\n⚠️  Vulnerable Beliefs: {patterns['vulnerable_beliefs_count']} beliefs")
            for belief in patterns.get('vulnerable_beliefs', [])[:3]:
                print(f"   - \"{belief}\"")
        
        if patterns.get('tribal_markers_count', 0) > 0:
            print(f"\n🎭 Tribal Markers: {patterns['tribal_markers_count']} beliefs")
        
        if patterns.get('dominant_domain'):
            print(f"\n🎯 Dominant Domain: {patterns['dominant_domain']} ({patterns['dominant_domain_percentage']:.1f}%)")
        
        if patterns.get('potential_dissonance_domains', 0) > 0:
            print(f"\n⚡ Cognitive Dissonance: Detected in {patterns['potential_dissonance_domains']} domains")
    
    # Generate insights report
    insight_gen = InsightGenerator()
    report = insight_gen.generate_report(df_with_metrics, summary_stats, centrality_df)
    
    # Export options
    if export_metrics:
        metrics_output = output_dir / f'belief_metrics_{Path(beliefs_file).stem}.csv'
        analyzer.export_metrics(df_with_metrics, metrics_output)
    
    if export_graph:
        json_output = output_dir / f'belief_graph_{Path(beliefs_file).stem}.json'
        graphml_output = output_dir / f'belief_graph_{Path(beliefs_file).stem}.graphml'
        graph_builder.export_to_json(json_output)
        graph_builder.export_to_graphml(graphml_output)
    
    if export_report:
        report_output = output_dir / f'belief_insights_{Path(beliefs_file).stem}.md'
        insight_gen.export_report(report, report_output)
    
    # If no exports requested, show a preview of the report
    if not (export_metrics or export_graph or export_report):
        print(f"\n{'='*80}")
        print("📝 Insight Report Preview")
        print(f"{'='*80}")
        # Show first 1500 characters
        print(report[:1500])
        print("\n...")
        print("\n💡 Use --export-report to save full report")
        print("   Use --export-metrics to save beliefs with calculated metrics")
        print("   Use --export-graph to export belief graph (JSON + GraphML)")
    
    print(f"\n{'='*80}")
    print(f"✅ Analysis complete!")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()

