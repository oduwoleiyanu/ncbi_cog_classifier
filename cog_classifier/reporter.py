"""
Report generation module for COG classification results.
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime


class COGReporter:
    """
    Generate reports from COG classification results.
    """
    
    def __init__(self):
        """Initialize COG reporter."""
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, results: List[Dict], output_file: str, 
                       format_type: str = "html"):
        """
        Generate comprehensive classification report.
        
        Args:
            results: Classification results
            output_file: Output report file path
            format_type: Report format (html, txt, json)
        """
        if format_type.lower() == "html":
            self._generate_html_report(results, output_file)
        elif format_type.lower() == "txt":
            self._generate_text_report(results, output_file)
        elif format_type.lower() == "json":
            self._generate_json_report(results, output_file)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")
    
    def _generate_html_report(self, results: List[Dict], output_file: str):
        """Generate HTML report."""
        stats = self._calculate_statistics(results)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COG Classification Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .summary {{
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            border-left: 4px solid #007bff;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .category-bar {{
            height: 20px;
            background-color: #007bff;
            border-radius: 3px;
            margin: 2px 0;
        }}
        .no-hit {{
            color: #dc3545;
        }}
        .good-hit {{
            color: #28a745;
        }}
        .warning {{
            color: #ffc107;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>COG Classification Report</h1>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Total sequences analyzed: {stats['total_sequences']}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats['classified']}</div>
                <div class="stat-label">Classified</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['unclassified']}</div>
                <div class="stat-label">Unclassified</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['errors']}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['classification_rate']:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>
        
        <h2>Functional Category Distribution</h2>
        {self._generate_category_chart_html(stats['category_distribution'])}
        
        <h2>Top COG Assignments</h2>
        {self._generate_top_cogs_table_html(stats['top_cogs'])}
        
        <h2>Detailed Results</h2>
        {self._generate_results_table_html(results)}
        
        <div class="footer">
            <p>Report generated by NCBI COG Classifier</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML report generated: {output_file}")
    
    def _generate_text_report(self, results: List[Dict], output_file: str):
        """Generate plain text report."""
        stats = self._calculate_statistics(results)
        
        report_lines = [
            "COG CLASSIFICATION REPORT",
            "=" * 50,
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 20,
            f"Total sequences: {stats['total_sequences']}",
            f"Classified: {stats['classified']}",
            f"Unclassified: {stats['unclassified']}",
            f"Errors: {stats['errors']}",
            f"Success rate: {stats['classification_rate']:.1f}%",
            "",
            "FUNCTIONAL CATEGORY DISTRIBUTION",
            "-" * 35,
        ]
        
        # Add category distribution
        for category, count in sorted(stats['category_distribution'].items()):
            percentage = (count / stats['classified'] * 100) if stats['classified'] > 0 else 0
            report_lines.append(f"{category}: {count} ({percentage:.1f}%)")
        
        report_lines.extend([
            "",
            "TOP COG ASSIGNMENTS",
            "-" * 20,
        ])
        
        # Add top COGs
        for cog_id, count in list(stats['top_cogs'].items())[:10]:
            percentage = (count / stats['classified'] * 100) if stats['classified'] > 0 else 0
            report_lines.append(f"{cog_id}: {count} ({percentage:.1f}%)")
        
        report_lines.extend([
            "",
            "DETAILED RESULTS",
            "-" * 16,
            f"{'Sequence ID':<20} {'COG ID':<10} {'Category':<8} {'E-value':<12} {'Identity':<8} {'Description':<50}",
            "-" * 108,
        ])
        
        # Add detailed results
        for result in results[:100]:  # Limit to first 100 for text report
            seq_id = result.get('sequence_id', 'Unknown')[:19]
            
            if result.get('error'):
                report_lines.append(f"{seq_id:<20} {'ERROR':<10} {'':<8} {'':<12} {'':<8} {result.get('error', '')[:50]}")
            elif result.get('best_hit'):
                hit = result['best_hit']
                cog_id = hit.get('cog_id', 'N/A')[:9]
                category = hit.get('category', 'N/A')[:7]
                evalue = f"{hit.get('evalue', 0):.1e}"[:11]
                identity = f"{hit.get('identity', 0):.1f}%"[:7]
                description = hit.get('cog_name', 'N/A')[:49]
                
                report_lines.append(f"{seq_id:<20} {cog_id:<10} {category:<8} {evalue:<12} {identity:<8} {description:<50}")
            else:
                report_lines.append(f"{seq_id:<20} {'NO_HIT':<10} {'':<8} {'':<12} {'':<8} {'No significant hits found':<50}")
        
        if len(results) > 100:
            report_lines.append(f"\n... and {len(results) - 100} more results")
        
        report_lines.extend([
            "",
            "-" * 50,
            "Report generated by NCBI COG Classifier"
        ])
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        self.logger.info(f"Text report generated: {output_file}")
    
    def _generate_json_report(self, results: List[Dict], output_file: str):
        """Generate JSON report."""
        stats = self._calculate_statistics(results)
        
        report_data = {
            "metadata": {
                "generated_on": datetime.now().isoformat(),
                "tool": "NCBI COG Classifier",
                "version": "1.0.0"
            },
            "summary": stats,
            "results": results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.info(f"JSON report generated: {output_file}")
    
    def _calculate_statistics(self, results: List[Dict]) -> Dict:
        """Calculate summary statistics from results."""
        stats = {
            "total_sequences": len(results),
            "classified": 0,
            "unclassified": 0,
            "errors": 0,
            "category_distribution": {},
            "top_cogs": {},
            "evalue_distribution": {"1e-10": 0, "1e-5": 0, "1e-3": 0, "0.01": 0, "other": 0}
        }
        
        for result in results:
            if result.get("error"):
                stats["errors"] += 1
            elif result.get("best_hit"):
                stats["classified"] += 1
                
                hit = result["best_hit"]
                
                # Count categories
                category = hit.get("category", "Unknown")
                stats["category_distribution"][category] = stats["category_distribution"].get(category, 0) + 1
                
                # Count COGs
                cog_id = hit.get("cog_id", "Unknown")
                stats["top_cogs"][cog_id] = stats["top_cogs"].get(cog_id, 0) + 1
                
                # E-value distribution
                evalue = hit.get("evalue", 1)
                if evalue <= 1e-10:
                    stats["evalue_distribution"]["1e-10"] += 1
                elif evalue <= 1e-5:
                    stats["evalue_distribution"]["1e-5"] += 1
                elif evalue <= 1e-3:
                    stats["evalue_distribution"]["1e-3"] += 1
                elif evalue <= 0.01:
                    stats["evalue_distribution"]["0.01"] += 1
                else:
                    stats["evalue_distribution"]["other"] += 1
            else:
                stats["unclassified"] += 1
        
        # Calculate success rate
        stats["classification_rate"] = (stats["classified"] / stats["total_sequences"] * 100) if stats["total_sequences"] > 0 else 0
        
        # Sort top COGs
        stats["top_cogs"] = dict(sorted(stats["top_cogs"].items(), key=lambda x: x[1], reverse=True)[:20])
        
        return stats
    
    def _generate_category_chart_html(self, category_distribution: Dict[str, int]) -> str:
        """Generate HTML for category distribution chart."""
        if not category_distribution:
            return "<p>No category data available.</p>"
        
        total = sum(category_distribution.values())
        
        html = "<table><tr><th>Category</th><th>Count</th><th>Percentage</th><th>Distribution</th></tr>"
        
        # COG category names
        category_names = {
            'A': 'RNA processing and modification',
            'B': 'Chromatin structure and dynamics',
            'C': 'Energy production and conversion',
            'D': 'Cell cycle control and mitosis',
            'E': 'Amino acid transport and metabolism',
            'F': 'Nucleotide transport and metabolism',
            'G': 'Carbohydrate transport and metabolism',
            'H': 'Coenzyme transport and metabolism',
            'I': 'Lipid transport and metabolism',
            'J': 'Translation',
            'K': 'Transcription',
            'L': 'Replication, recombination and repair',
            'M': 'Cell wall/membrane biogenesis',
            'N': 'Cell motility',
            'O': 'Posttranslational modification, protein turnover, chaperones',
            'P': 'Inorganic ion transport and metabolism',
            'Q': 'Secondary metabolites biosynthesis, transport and catabolism',
            'R': 'General function prediction only',
            'S': 'Function unknown',
            'T': 'Signal transduction mechanisms',
            'U': 'Intracellular trafficking and secretion',
            'V': 'Defense mechanisms',
            'W': 'Extracellular structures',
            'Y': 'Nuclear structure',
            'Z': 'Cytoskeleton'
        }
        
        for category, count in sorted(category_distribution.items()):
            percentage = (count / total * 100) if total > 0 else 0
            bar_width = percentage
            category_name = category_names.get(category, 'Unknown')
            
            html += f"""
            <tr>
                <td><strong>{category}</strong> - {category_name}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
                <td><div class="category-bar" style="width: {bar_width}%;"></div></td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def _generate_top_cogs_table_html(self, top_cogs: Dict[str, int]) -> str:
        """Generate HTML table for top COGs."""
        if not top_cogs:
            return "<p>No COG data available.</p>"
        
        total = sum(top_cogs.values())
        
        html = "<table><tr><th>COG ID</th><th>Count</th><th>Percentage</th></tr>"
        
        for cog_id, count in list(top_cogs.items())[:10]:
            percentage = (count / total * 100) if total > 0 else 0
            html += f"<tr><td>{cog_id}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
        
        html += "</table>"
        return html
    
    def _generate_results_table_html(self, results: List[Dict]) -> str:
        """Generate HTML table for detailed results."""
        html = """
        <table>
            <tr>
                <th>Sequence ID</th>
                <th>Length</th>
                <th>COG ID</th>
                <th>Category</th>
                <th>E-value</th>
                <th>Identity (%)</th>
                <th>Coverage (%)</th>
                <th>Description</th>
            </tr>
        """
        
        # Show first 50 results in detail
        for result in results[:50]:
            seq_id = result.get('sequence_id', 'Unknown')
            length = result.get('length', 'N/A')
            
            if result.get('error'):
                html += f"""
                <tr class="warning">
                    <td>{seq_id}</td>
                    <td>{length}</td>
                    <td colspan="6">ERROR: {result.get('error', 'Unknown error')}</td>
                </tr>
                """
            elif result.get('best_hit'):
                hit = result['best_hit']
                cog_id = hit.get('cog_id', 'N/A')
                category = hit.get('category', 'N/A')
                evalue = f"{hit.get('evalue', 0):.1e}" if hit.get('evalue') else 'N/A'
                identity = f"{hit.get('identity', 0):.1f}" if hit.get('identity') else 'N/A'
                coverage = f"{hit.get('coverage', 0):.1f}" if hit.get('coverage') else 'N/A'
                description = hit.get('cog_name', 'N/A')
                
                row_class = "good-hit" if hit.get('evalue', 1) < 1e-5 else ""
                
                html += f"""
                <tr class="{row_class}">
                    <td>{seq_id}</td>
                    <td>{length}</td>
                    <td>{cog_id}</td>
                    <td>{category}</td>
                    <td>{evalue}</td>
                    <td>{identity}</td>
                    <td>{coverage}</td>
                    <td>{description}</td>
                </tr>
                """
            else:
                html += f"""
                <tr class="no-hit">
                    <td>{seq_id}</td>
                    <td>{length}</td>
                    <td colspan="6">No significant hits found</td>
                </tr>
                """
        
        if len(results) > 50:
            html += f"""
            <tr>
                <td colspan="8" style="text-align: center; font-style: italic;">
                    ... and {len(results) - 50} more results (see JSON export for complete data)
                </td>
            </tr>
            """
        
        html += "</table>"
        return html
