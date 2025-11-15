"""
Dashboard HTML generator with embedded data.
Creates standalone dashboard HTML files with CSV data pre-loaded.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime


def generate_dashboard_html(csv_path: str, output_html_path: str, episode_id: str = None) -> str:
    """
    Generate dashboard HTML with embedded CSV data.
    
    Args:
        csv_path: Path to beliefs CSV
        output_html_path: Where to save HTML
        episode_id: Optional episode identifier
        
    Returns:
        Path to generated HTML file
    """
    # Read CSV data
    df = pd.read_csv(csv_path)
    
    # Convert to JSON for embedding with proper escaping
    import json
    records = df.to_dict(orient='records')
    beliefs_json = json.dumps(records, indent=2, ensure_ascii=False)
    
    # Get metadata
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    csv_filename = Path(csv_path).name
    episode_label = f" - {episode_id}" if episode_id else ""
    
    # Read the base dashboard template
    template_path = Path(__file__).parent.parent / 'dashboard_analytics.html'
    with open(template_path, 'r') as f:
        template_html = f.read()
    
    # Modify the HTML to:
    # 1. Hide the file upload section
    # 2. Add a banner showing source file
    # 3. Embed the CSV data
    # 4. Auto-trigger analysis on load
    
    # Add style to hide upload area
    hide_upload_css = """
        .file-upload {
            display: none;
        }
        
        .data-info {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        
        .data-info h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .data-info p {
            color: #666;
            margin: 5px 0;
        }
    """
    
    # Insert CSS before </style>
    modified_html = template_html.replace('</style>', f'{hide_upload_css}\n    </style>')
    
    # Add data info banner after header
    data_info_html = f"""
        <div class="data-info">
            <h3>📊 Loaded Data</h3>
            <p><strong>Source:</strong> {csv_filename}</p>
            <p><strong>Episode:</strong> {episode_id or 'N/A'}</p>
            <p><strong>Generated:</strong> {timestamp}</p>
            <p><strong>Beliefs:</strong> {len(df)}</p>
        </div>
    """
    
    # Insert data info after opening <div id="content">
    modified_html = modified_html.replace(
        '<div id="content">',
        f'<div id="content" class="active">\n{data_info_html}'
    )
    
    # Embed the data and auto-trigger analysis
    # Replace the original empty beliefsData with our embedded data
    modified_html = modified_html.replace(
        'let beliefsData = [];',
        f'let beliefsData = {beliefs_json};'
    )
    
    # Add auto-analyze script
    auto_analyze_script = """
        // Auto-analyze on page load
        window.addEventListener('DOMContentLoaded', function() {
            console.log('Dashboard loaded with', beliefsData.length, 'beliefs');
            if (beliefsData.length > 0) {
                analyzeBeliefs();
            } else {
                console.error('No beliefs data found!');
            }
        });
    """
    
    # Insert auto-analyze script before the closing </script> tag
    script_insert_pos = modified_html.rfind('</script>')
    modified_html = (
        modified_html[:script_insert_pos] + 
        '\n' + auto_analyze_script + '\n' +
        modified_html[script_insert_pos:]
    )
    
    # Also remove the file upload event handlers since we don't need them
    # Comment out the file handling code
    modified_html = modified_html.replace(
        'uploadArea.addEventListener(\'click\',',
        '// uploadArea.addEventListener(\'click\','
    )
    modified_html = modified_html.replace(
        'uploadArea.addEventListener(\'dragover\',',
        '// uploadArea.addEventListener(\'dragover\','
    )
    modified_html = modified_html.replace(
        'uploadArea.addEventListener(\'dragleave\',',
        '// uploadArea.addEventListener(\'dragleave\','
    )
    modified_html = modified_html.replace(
        'uploadArea.addEventListener(\'drop\',',
        '// uploadArea.addEventListener(\'drop\','
    )
    modified_html = modified_html.replace(
        'fileInput.addEventListener(\'change\',',
        '// fileInput.addEventListener(\'change\','
    )
    
    # Update title
    title = f"Belief Analytics - {episode_id}{episode_label}" if episode_id else f"Belief Analytics - {csv_filename}"
    modified_html = modified_html.replace(
        '<title>Belief Analytics Dashboard</title>',
        f'<title>{title}</title>'
    )
    
    # Write the modified HTML
    output_path = Path(output_html_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(modified_html)
    
    return str(output_path.absolute())

