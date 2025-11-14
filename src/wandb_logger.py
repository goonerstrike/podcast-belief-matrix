"""
Weights & Biases integration for belief extraction pipeline.
"""
import wandb
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Optional


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
            'unique_categories': len(stats.get('beliefs_per_category', {}))
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
        print(f"📊 Creating visualizations...")
        
        self.log_tier_distribution(df)
        self.log_category_distribution(df)
        self.log_speaker_comparison(df)
        self.log_conviction_stability_scatter(df)
        self.log_tier_heatmap(df)
        
        print(f"✅ All visualizations logged")
    
    def finish(self):
        """Finish W&B run."""
        wandb.finish()
        print(f"🏁 W&B run finished")

