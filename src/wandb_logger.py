"""
Weights & Biases integration for belief extraction pipeline.
"""
import wandb
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Optional, Any


class WandbLogger:
    """W&B logging for belief extraction."""
    
    def __init__(self, project: str = "podcast-belief-extraction",
                 entity: Optional[str] = None,
                 config: Optional[Dict] = None,
                 name: Optional[str] = None,
                 tags: Optional[list] = None):
        """
        Initialize W&B logger.
        
        Args:
            project: W&B project name
            entity: W&B entity (username/team)
            config: Run configuration
            name: Run name
            tags: Run tags
        """
        self.run = wandb.init(
            project=project,
            entity=entity,
            config=config,
            name=name,
            tags=tags or []
        )
        
    def log_beliefs_table(self, df: pd.DataFrame):
        """
        Log beliefs as interactive W&B table.
        
        Args:
            df: Beliefs DataFrame
        """
        # Convert any problematic types
        df_clean = df.copy()
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].astype(str)
        
        table = wandb.Table(dataframe=df_clean)
        wandb.log({"beliefs_table": table})
        print(f"📊 Logged beliefs table to W&B")
    
    def log_metrics(self, stats: Dict):
        """
        Log summary metrics.
        
        Args:
            stats: Dictionary of statistics
        """
        metrics = {
            'total_beliefs': stats.get('total_beliefs', 0),
            'avg_conviction': stats.get('avg_conviction', 0),
            'avg_stability': stats.get('avg_stability', 0),
            'unique_speakers': len(stats.get('beliefs_per_speaker', {})),
            'unique_tiers': len(stats.get('beliefs_per_tier', {})),
            'unique_categories': len(stats.get('beliefs_per_category', {})),
            'unique_sub_domains': len(stats.get('beliefs_per_sub_domain', {}))
        }
        
        wandb.log(metrics)
        print(f"📈 Logged metrics to W&B")
    
    def log_cost(self, cost_stats: Dict):
        """
        Log cost information.
        
        Args:
            cost_stats: Cost statistics from classifier
        """
        wandb.log({
            'total_tokens': cost_stats.get('total_tokens', 0),
            'total_cost_usd': cost_stats.get('total_cost', 0),
            'model': cost_stats.get('model', 'unknown')
        })
        print(f"💰 Logged cost: ${cost_stats.get('total_cost', 0):.4f}")
    
    def log_performance(self, performance_stats: Dict):
        """
        Log performance/timing metrics.
        
        Args:
            performance_stats: Dictionary with timing information
        """
        metrics = {
            'extraction_time_seconds': performance_stats.get('total_time', 0),
            'workers': performance_stats.get('workers', 1),
            'total_chunks': performance_stats.get('total_chunks', 0),
            'throughput_chunks_per_second': performance_stats.get('throughput', 0)
        }
        
        # Add per-level timing if available
        if 'level_times' in performance_stats:
            for level, time_val in performance_stats['level_times'].items():
                metrics[f'level_{level}_time_seconds'] = time_val
        
        wandb.log(metrics)
        print(f"⏱️  Logged performance: {performance_stats.get('total_time', 0):.2f}s with {performance_stats.get('workers', 1)} workers")
    
    # ------------------------------------------------------------------ #
    # Advanced stats logging
    # ------------------------------------------------------------------ #

    def log_statistical_analysis(self, stats: Dict[str, Any]):
        """Log advanced statistical analysis results."""
        if not stats:
            return

        score_stats = stats.get('score_statistics', {})
        flattened_scores = {}
        for metric, values in score_stats.items():
            for key, value in values.items():
                if isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        flattened_scores[f'stats/{metric}/{key}_{sub_key}'] = sub_val
                else:
                    flattened_scores[f'stats/{metric}/{key}'] = value
        if flattened_scores:
            wandb.log(flattened_scores)

        # Distributions
        distributions = stats.get('distributions', {})
        for name, payload in distributions.items():
            table = self._distribution_table(payload)
            wandb.log({f'distributions/{name}': table})

        # Correlations
        correlations = stats.get('correlations', {})
        corr_payload = {
            f'correlations/{k}': v
            for k, v in correlations.items()
            if v is not None
        }
        if corr_payload:
            wandb.log(corr_payload)

        # Outliers as tables
        outliers = stats.get('outliers', {})
        for name, rows in outliers.items():
            if not rows:
                continue
            columns = list(rows[0].keys())
            table = wandb.Table(columns=columns, data=[list(row.values()) for row in rows])
            wandb.log({f'outliers/{name}': table})

        # Content metrics
        content_metrics = stats.get('content_metrics', {})
        scalar_metrics = {
            f'content/{k}': v
            for k, v in content_metrics.items()
            if isinstance(v, (int, float))
        }
        if scalar_metrics:
            wandb.log(scalar_metrics)

        certainty_distribution = content_metrics.get('certainty_distribution')
        if certainty_distribution:
            table = self._distribution_table(certainty_distribution)
            wandb.log({'content/certainty_distribution': table})

        # Multi-level stats
        multi_level = stats.get('multi_level', {})
        for key, value in multi_level.items():
            if isinstance(value, dict):
                table = self._distribution_table(value)
                wandb.log({f'multi_level/{key}': table})
            else:
                wandb.log({f'multi_level/{key}': value})

        # Speaker summary
        speaker_profiles = stats.get('speaker_profiles', {})
        summary_rows = speaker_profiles.get('speaker_summary', [])
        if summary_rows:
            columns = list(summary_rows[0].keys())
            table = wandb.Table(columns=columns, data=[list(row.values()) for row in summary_rows])
            wandb.log({'speakers/summary': table})

    def log_graph_metrics(self, graph_metrics: Dict[str, Any]):
        """Log graph analytics (centrality, communities, keystone beliefs)."""
        if not graph_metrics:
            return

        graph_stats = graph_metrics.get('graph_stats', {})
        if graph_stats:
            wandb.log({f'graph/{k}': v for k, v in graph_stats.items()})

        centrality = graph_metrics.get('centrality', {})
        for key in ['top_pagerank', 'top_betweenness', 'top_degree']:
            rows = centrality.get(key, [])
            if rows:
                columns = list(rows[0].keys())
                table = wandb.Table(columns=columns, data=[list(row.values()) for row in rows])
                wandb.log({f'graph/{key}': table})

        for scalar_key in ['average_degree', 'average_betweenness']:
            if scalar_key in centrality:
                wandb.log({f'graph/{scalar_key}': centrality[scalar_key]})

        communities = graph_metrics.get('communities', {})
        if communities:
            wandb.log({
                'graph/communities/total': communities.get('total_communities', 0),
                'graph/communities/largest': communities.get('largest_community_size', 0)
            })
            sizes = communities.get('community_sizes', {})
            if sizes:
                table = wandb.Table(
                    columns=['community_id', 'size'],
                    data=[[cid, size] for cid, size in sizes.items()]
                )
                wandb.log({'graph/communities/sizes': table})

        keystone = graph_metrics.get('keystone_beliefs', [])
        if keystone:
            columns = list(keystone[0].keys())
            table = wandb.Table(columns=columns, data=[list(row.values()) for row in keystone])
            wandb.log({'graph/keystone_beliefs': table})

    def log_quality_metrics(self, metrics: Dict[str, Any]):
        """Log deduplication and linking quality metrics."""
        if not metrics:
            return

        scalar_metrics = {
            f'quality/{k}': v
            for k, v in metrics.items()
            if isinstance(v, (int, float))
        }
        if scalar_metrics:
            wandb.log(scalar_metrics)

        for key, value in metrics.items():
            if isinstance(value, list) and value:
                columns = list(value[0].keys())
                table = wandb.Table(columns=columns, data=[list(row.values()) for row in value])
                wandb.log({f'quality/{key}': table})
    
    def log_tier_distribution(self, df: pd.DataFrame):
        """
        Create and log tier distribution chart.
        
        Args:
            df: Beliefs DataFrame
        """
        tier_counts = df['tier_name'].value_counts()
        
        fig = px.bar(
            x=tier_counts.index,
            y=tier_counts.values,
            labels={'x': 'Tier', 'y': 'Count'},
            title='Belief Distribution by Tier'
        )
        fig.update_xaxes(tickangle=45)
        
        wandb.log({"tier_distribution": fig})
    
    def log_category_distribution(self, df: pd.DataFrame):
        """
        Create and log category distribution chart.
        
        Args:
            df: Beliefs DataFrame
        """
        category_counts = df['category'].value_counts()
        
        fig = px.pie(
            values=category_counts.values,
            names=category_counts.index,
            title='Belief Distribution by Category'
        )
        
        wandb.log({"category_distribution": fig})
    
    def log_sub_domain_distribution(self, df: pd.DataFrame):
        """
        Create and log sub-domain distribution chart (top 20).
        """
        if 'sub_domain' not in df.columns:
            return
        sub_counts = df['sub_domain'].fillna('general').value_counts().head(20)
        if sub_counts.empty:
            return
        
        fig = px.bar(
            x=sub_counts.index,
            y=sub_counts.values,
            labels={'x': 'Sub-domain', 'y': 'Count'},
            title='Top Sub-domains'
        )
        fig.update_xaxes(tickangle=45)
        wandb.log({"sub_domain_distribution": fig})
    
    def log_speaker_comparison(self, df: pd.DataFrame):
        """
        Create and log speaker comparison chart.
        
        Args:
            df: Beliefs DataFrame
        """
        speaker_stats = df.groupby('speaker_id').agg({
            'belief_id': 'count',
            'conviction_score': 'mean',
            'stability_score': 'mean'
        }).rename(columns={'belief_id': 'count'})
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Belief Count',
            x=speaker_stats.index,
            y=speaker_stats['count'],
            yaxis='y'
        ))
        
        fig.add_trace(go.Scatter(
            name='Avg Conviction',
            x=speaker_stats.index,
            y=speaker_stats['conviction_score'],
            yaxis='y2',
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title='Beliefs per Speaker with Avg Conviction',
            yaxis=dict(title='Belief Count'),
            yaxis2=dict(title='Avg Conviction', overlaying='y', side='right', range=[0, 1]),
            hovermode='x'
        )
        
        wandb.log({"speaker_comparison": fig})
    
    def log_conviction_stability_scatter(self, df: pd.DataFrame):
        """
        Create conviction vs stability scatter plot.
        
        Args:
            df: Beliefs DataFrame
        """
        fig = px.scatter(
            df,
            x='conviction_score',
            y='stability_score',
            color='tier_name',
            size='importance',
            hover_data=['statement_text', 'speaker_id'],
            title='Conviction vs Stability by Tier',
            labels={
                'conviction_score': 'Conviction Score',
                'stability_score': 'Stability Score'
            }
        )
        
        wandb.log({"conviction_stability_scatter": fig})
    
    def log_tier_heatmap(self, df: pd.DataFrame):
        """
        Create heatmap of tier vs category.
        
        Args:
            df: Beliefs DataFrame
        """
        pivot = pd.crosstab(df['tier_name'], df['category'])
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='Viridis'
        ))
        
        fig.update_layout(
            title='Belief Heatmap: Tier vs Category',
            xaxis_title='Category',
            yaxis_title='Tier'
        )
        
        wandb.log({"tier_category_heatmap": fig})
    
    def log_artifacts(self, transcript_path: Optional[str] = None,
                     output_path: Optional[str] = None):
        """
        Log files as W&B artifacts.
        
        Args:
            transcript_path: Path to input transcript
            output_path: Path to output beliefs file
        """
        artifact = wandb.Artifact('belief-extraction-run', type='results')
        
        if transcript_path:
            artifact.add_file(transcript_path, name='transcript.txt')
        
        if output_path:
            artifact.add_file(output_path, name='beliefs.csv')
        
        wandb.log_artifact(artifact)
        print(f"📦 Logged artifacts to W&B")
    
    def log_all_visualizations(self, df: pd.DataFrame):
        """
        Log all standard visualizations.
        
        Args:
            df: Beliefs DataFrame
        """
        if df.empty:
            print(f"⚠️  Skipping visualizations (no beliefs found)")
            return
        
        print(f"📊 Creating visualizations...")
        
        self.log_tier_distribution(df)
        self.log_category_distribution(df)
        self.log_sub_domain_distribution(df)
        self.log_speaker_comparison(df)
        self.log_conviction_stability_scatter(df)
        self.log_tier_heatmap(df)
        
        print(f"✅ All visualizations logged")
    
    def finish(self):
        """Finish W&B run."""
        wandb.finish()
        print(f"🏁 W&B run finished")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _distribution_table(self, payload: Dict[str, Any]) -> wandb.Table:
        """Create a W&B table showing counts and percentages."""
        table = wandb.Table(columns=['label', 'count', 'percentage'])
        counts = payload.get('counts', {})
        percentages = payload.get('percentages', {})
        for label, count in counts.items():
            pct = percentages.get(label, 0)
            table.add_data(label, count, pct)
        return table

