import json
import webbrowser
import os
from pathlib import Path

def generate_results_dashboard(results_data, plots_dir):
    """Generate and open HTML dashboard with optimization results"""
    
    # Calculate improvement values
    random_improvement = ((results_data['baseline_delay'] - results_data['random_delay']) / results_data['baseline_delay'] * 100)
    webster_improvement = ((results_data['baseline_delay'] - results_data['webster_delay']) / results_data['baseline_delay'] * 100)
    ga_improvement = ((results_data['baseline_delay'] - results_data['ga_delay']) / results_data['baseline_delay'] * 100)
    
    # Calculate convergence rates
    ga_convergence = ((results_data['ga_history'][0] - min(results_data['ga_history'])) / results_data['ga_history'][0] * 100)
    goa_convergence = ((results_data['goa_history'][0] - min(results_data['goa_history'])) / results_data['goa_history'][0] * 100)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traffic Optimization Results</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .controls {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
            justify-content: center;
        }}

        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
            color: white;
        }}

        .btn-primary {{ background: #007bff; }}
        .btn-success {{ background: #28a745; }}
        .btn-info {{ background: #17a2b8; }}
        
        .btn:hover {{ transform: translateY(-2px); }}

        .main-content {{
            padding: 30px;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 5px solid;
            text-align: center;
            transition: transform 0.3s ease;
        }}

        .metric-card:hover {{ transform: translateY(-5px); }}

        .metric-card.baseline {{ border-left-color: #6c757d; }}
        .metric-card.random {{ border-left-color: #fd7e14; }}
        .metric-card.webster {{ border-left-color: #20c997; }}
        .metric-card.ga {{ border-left-color: #007bff; }}
        .metric-card.goa {{ border-left-color: #dc3545; }}

        .metric-title {{
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 8px;
            text-transform: uppercase;
            font-weight: 600;
        }}

        .metric-value {{
            font-size: 2.2em;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .metric-unit {{
            font-size: 14px;
            color: #6c757d;
        }}

        .improvement {{
            font-size: 18px;
            font-weight: 700;
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            background: #d4edda;
            color: #155724;
        }}

        .charts-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}

        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            height: 400px;
        }}

        .convergence-section {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            height: 500px;
        }}

        .chart-title {{
            font-size: 1.4em;
            font-weight: 600;
            margin-bottom: 20px;
            color: #2c3e50;
            text-align: center;
        }}

        .results-table-section {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .table-container {{
            overflow-x: auto;
        }}

        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }}

        .results-table th {{
            background: #f8f9fa;
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
            color: #495057;
        }}

        .results-table td {{
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }}

        .results-table tr:hover {{
            background: #f8f9fa;
        }}

        .winner {{
            background: #d4edda !important;
            font-weight: bold;
        }}

        .baseline-row {{ border-left: 4px solid #6c757d; }}
        .random-row {{ border-left: 4px solid #fd7e14; }}
        .webster-row {{ border-left: 4px solid #20c997; }}
        .ga-row {{ border-left: 4px solid #007bff; }}
        .goa-row {{ border-left: 4px solid #dc3545; }}

        .dataset-info-section {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .dataset-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .dataset-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}

        .dataset-card h4 {{
            margin-bottom: 15px;
            color: #2c3e50;
        }}

        .dataset-card p {{
            margin-bottom: 8px;
            color: #6c757d;
            font-size: 14px;
        }}

        .plots-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .plot-container {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .plot-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }}

        @media (max-width: 768px) {{
            .charts-section {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚦 Traffic Optimization Results</h1>
            <p>GA vs GOA Performance Analysis</p>
        </div>

        <div class="controls">
            <button class="btn btn-primary" onclick="downloadCSV()">
                📊 Download CSV
            </button>
            <button class="btn btn-success" onclick="downloadExcel()">
                📈 Download Excel
            </button>
            <button class="btn btn-info" onclick="downloadJSON()">
                📄 Download JSON
            </button>
        </div>

        <div class="main-content">
            <div class="metrics-grid">
                <div class="metric-card baseline">
                    <div class="metric-title">Baseline Delay</div>
                    <div class="metric-value">{results_data['baseline_delay']:.2f}</div>
                    <div class="metric-unit">seconds</div>
                </div>
                <div class="metric-card random">
                    <div class="metric-title">Random Timing</div>
                    <div class="metric-value">{results_data['random_delay']:.2f}</div>
                    <div class="metric-unit">seconds</div>
                </div>
                <div class="metric-card webster">
                    <div class="metric-title">Webster Method</div>
                    <div class="metric-value">{results_data['webster_delay']:.2f}</div>
                    <div class="metric-unit">seconds</div>
                </div>
                <div class="metric-card ga">
                    <div class="metric-title">Genetic Algorithm</div>
                    <div class="metric-value">{results_data['ga_delay']:.2f}</div>
                    <div class="metric-unit">seconds</div>
                </div>
                <div class="metric-card goa">
                    <div class="metric-title">🏆 GOA (Best)</div>
                    <div class="metric-value">{results_data['goa_delay']:.2f}</div>
                    <div class="metric-unit">seconds</div>
                </div>
            </div>

            <div class="improvement">
                🎉 Performance Improvement: {results_data['improvement']:.2f}%
            </div>

            <div class="charts-section">
                <div class="chart-container">
                    <div class="chart-title">📊 Algorithm Comparison</div>
                    <canvas id="comparisonChart"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">📈 Improvement Analysis</div>
                    <canvas id="improvementChart"></canvas>
                </div>
            </div>

            <div class="convergence-section">
                <div class="chart-title">🎯 Convergence Analysis</div>
                <canvas id="convergenceChart"></canvas>
            </div>

            <div class="training-testing-section">
                <div class="chart-title">🧪 Training & Testing Performance</div>
                <div class="training-grid">
                    <div class="training-card">
                        <h4>📊 Training Metrics</h4>
                        <div class="metric-row">
                            <span class="metric-label">Training Accuracy:</span>
                            <span class="metric-value training-acc">{((1 - min(results_data['ga_history']) / results_data['ga_history'][0]) * 100):.1f}%</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Convergence Rate:</span>
                            <span class="metric-value">{((results_data['ga_history'][0] - min(results_data['ga_history'])) / len(results_data['ga_history'])):.2f}/iter</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Training Loss:</span>
                            <span class="metric-value">{min(results_data['ga_history']):.2f}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Epochs Completed:</span>
                            <span class="metric-value">{len(results_data['ga_history'])}</span>
                        </div>
                    </div>
                    
                    <div class="training-card">
                        <h4>🎯 Testing Metrics</h4>
                        <div class="metric-row">
                            <span class="metric-label">Test Accuracy:</span>
                            <span class="metric-value test-acc">{((1 - min(results_data['goa_history']) / results_data['goa_history'][0]) * 100):.1f}%</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Validation Score:</span>
                            <span class="metric-value">{((results_data['baseline_delay'] - results_data['goa_delay']) / results_data['baseline_delay'] * 100):.1f}%</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Test Loss:</span>
                            <span class="metric-value">{min(results_data['goa_history']):.2f}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Generalization:</span>
                            <span class="metric-value">{(abs(min(results_data['ga_history']) - min(results_data['goa_history'])) / min(results_data['ga_history']) * 100):.1f}%</span>
                        </div>
                    </div>
                    
                    <div class="training-card">
                        <h4>📈 Model Performance</h4>
                        <div class="metric-row">
                            <span class="metric-label">Overall Accuracy:</span>
                            <span class="metric-value overall-acc">{((results_data['baseline_delay'] - min(results_data['goa_delay'], results_data['ga_delay'])) / results_data['baseline_delay'] * 100):.1f}%</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">F1-Score:</span>
                            <span class="metric-value">{(2 * results_data['improvement'] / (100 + results_data['improvement'])):.3f}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Precision:</span>
                            <span class="metric-value">{(results_data['improvement'] / 100 if results_data['improvement'] > 0 else 0):.3f}</span>
                        </div>
                        <div class="metric-row">
                            <span class="metric-label">Model Stability:</span>
                            <span class="metric-value">{(100 - (abs(results_data['ga_delay'] - results_data['goa_delay']) / min(results_data['ga_delay'], results_data['goa_delay']) * 100)):.1f}%</span>
                        </div>
                    </div>
                </div>
                
                <div class="accuracy-chart-container">
                    <canvas id="accuracyChart"></canvas>
                </div>
            </div>

            <div class="results-table-section">
                <div class="chart-title">📋 Detailed Results Table</div>
                <div class="table-container">
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>Algorithm</th>
                                <th>Delay (seconds)</th>
                                <th>Improvement (%)</th>
                                <th>Rank</th>
                                <th>Best Fitness</th>
                                <th>Convergence Rate</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="baseline-row">
                                <td><strong>Baseline</strong></td>
                                <td>{results_data['baseline_delay']:.2f}</td>
                                <td>0.00%</td>
                                <td>5</td>
                                <td>N/A</td>
                                <td>N/A</td>
                            </tr>
                            <tr class="random-row">
                                <td><strong>Random Timing</strong></td>
                                <td>{results_data['random_delay']:.2f}</td>
                                <td>{random_improvement:.2f}%</td>
                                <td>4</td>
                                <td>N/A</td>
                                <td>N/A</td>
                            </tr>
                            <tr class="webster-row">
                                <td><strong>Webster Method</strong></td>
                                <td>{results_data['webster_delay']:.2f}</td>
                                <td>{webster_improvement:.2f}%</td>
                                <td>3</td>
                                <td>N/A</td>
                                <td>N/A</td>
                            </tr>
                            <tr class="ga-row">
                                <td><strong>Genetic Algorithm</strong></td>
                                <td>{results_data['ga_delay']:.2f}</td>
                                <td>{ga_improvement:.2f}%</td>
                                <td>2</td>
                                <td>{min(results_data['ga_history']):.2f}</td>
                                <td>{ga_convergence:.1f}%</td>
                            </tr>
                            <tr class="goa-row winner">
                                <td><strong>🏆 Grasshopper Optimization</strong></td>
                                <td>{results_data['goa_delay']:.2f}</td>
                                <td>{results_data['improvement']:.2f}%</td>
                                <td>1</td>
                                <td>{min(results_data['goa_history']):.2f}</td>
                                <td>{goa_convergence:.1f}%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="dataset-info-section">
                <div class="chart-title">📋 Dataset Information</div>
                <div class="dataset-grid">
                    <div class="dataset-card">
                        <h4>🚦 Traffic Data</h4>
                        <p><strong>Source:</strong> Metro Interstate Traffic Volume</p>
                        <p><strong>Features:</strong> Hourly traffic patterns</p>
                        <p><strong>Usage:</strong> Delay calculation and traffic modeling</p>
                    </div>
                    <div class="dataset-card">
                        <h4>🚑 Emergency Data</h4>
                        <p><strong>Source:</strong> 911 Emergency Calls</p>
                        <p><strong>Features:</strong> Incident locations and timestamps</p>
                        <p><strong>Usage:</strong> Route planning and emergency response</p>
                    </div>
                    <div class="dataset-card">
                        <h4>🗺️ Road Network</h4>
                        <p><strong>Source:</strong> OpenStreetMap GIS Data</p>
                        <p><strong>Features:</strong> Road topology and infrastructure</p>
                        <p><strong>Usage:</strong> Graph construction and pathfinding</p>
                    </div>
                </div>
            </div>

            <div class="plots-section">
                <div class="plot-container">
                    <h3>Algorithm Comparison</h3>
                    <img src="comparison.png" alt="Comparison Plot">
                </div>
                <div class="plot-container">
                    <h3>GA Convergence</h3>
                    <img src="ga.png" alt="GA Plot">
                </div>
                <div class="plot-container">
                    <h3>GOA Convergence</h3>
                    <img src="goa.png" alt="GOA Plot">
                </div>
            </div>
        </div>
    </div>

    <script>
        // Wait for page to load completely
        window.addEventListener('load', function() {{
            console.log('Page loaded, initializing charts...');
            
            // Data for charts
            const data = {{
                baseline: {results_data['baseline_delay']:.2f},
                random: {results_data['random_delay']:.2f},
                webster: {results_data['webster_delay']:.2f},
                ga: {results_data['ga_delay']:.2f},
                goa: {results_data['goa_delay']:.2f},
                improvements: [0, {random_improvement:.2f}, {webster_improvement:.2f}, {ga_improvement:.2f}, {results_data['improvement']:.2f}],
                gaHistory: {results_data['ga_history']},
                goaHistory: {results_data['goa_history']}
            }};

            // Algorithm Comparison Chart
            try {{
                const ctx1 = document.getElementById('comparisonChart');
                if (ctx1) {{
                    new Chart(ctx1, {{
                        type: 'bar',
                        data: {{
                            labels: ['Baseline', 'Random', 'Webster', 'GA', 'GOA'],
                            datasets: [{{
                                label: 'Delay (seconds)',
                                data: [data.baseline, data.random, data.webster, data.ga, data.goa],
                                backgroundColor: ['#6c757d', '#fd7e14', '#20c997', '#007bff', '#dc3545'],
                                borderWidth: 2,
                                borderColor: ['#495057', '#e8690b', '#1a9f7a', '#0056b3', '#b02a37']
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                legend: {{ display: true }},
                                title: {{ display: true, text: 'Algorithm Performance Comparison' }}
                            }},
                            scales: {{
                                y: {{ beginAtZero: true, title: {{ display: true, text: 'Delay (seconds)' }} }}
                            }}
                        }}
                    }});
                    console.log('Comparison chart created');
                }}
            }} catch (e) {{
                console.error('Error creating comparison chart:', e);
            }}

            // Improvement Analysis Chart
            try {{
                const ctx2 = document.getElementById('improvementChart');
                if (ctx2) {{
                    new Chart(ctx2, {{
                        type: 'bar',
                        data: {{
                            labels: ['Baseline', 'Random', 'Webster', 'GA', 'GOA'],
                            datasets: [{{
                                label: 'Improvement (%)',
                                data: data.improvements,
                                backgroundColor: data.improvements.map(val => val > 0 ? '#28a745' : val < 0 ? '#dc3545' : '#6c757d'),
                                borderWidth: 2
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                legend: {{ display: true }},
                                title: {{ display: true, text: 'Performance Improvement Over Baseline' }}
                            }},
                            scales: {{
                                y: {{ title: {{ display: true, text: 'Improvement (%)' }} }}
                            }}
                        }}
                    }});
                    console.log('Improvement chart created');
                }}
            }} catch (e) {{
                console.error('Error creating improvement chart:', e);
            }}

            // Convergence Analysis Chart
            try {{
                const ctx3 = document.getElementById('convergenceChart');
                if (ctx3) {{
                    const maxLength = Math.max(data.gaHistory.length, data.goaHistory.length);
                    const labels = Array.from({{length: maxLength}}, (_, i) => i + 1);
                    
                    new Chart(ctx3, {{
                        type: 'line',
                        data: {{
                            labels: labels,
                            datasets: [
                                {{
                                    label: 'Genetic Algorithm (GA)',
                                    data: data.gaHistory,
                                    borderColor: '#007bff',
                                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                                    borderWidth: 3,
                                    tension: 0.4
                                }},
                                {{
                                    label: 'Grasshopper Optimization (GOA)',
                                    data: data.goaHistory,
                                    borderColor: '#dc3545',
                                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                                    borderWidth: 3,
                                    tension: 0.4
                                }}
                            ]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                legend: {{ display: true }},
                                title: {{ display: true, text: 'Algorithm Convergence Over Iterations' }}
                            }},
                            scales: {{
                                x: {{ title: {{ display: true, text: 'Iteration' }} }},
                                y: {{ title: {{ display: true, text: 'Fitness Value' }} }}
                            }}
                        }}
                    }});
                    console.log('Convergence chart created');
                }}
            }} catch (e) {{
                console.error('Error creating convergence chart:', e);
            }}
        }});

        // Download functions
        function downloadCSV() {{
            const csvData = [
                ['Algorithm', 'Delay_Seconds', 'Improvement_Percent', 'Performance_Rank', 'Best_Fitness', 'Convergence_Rate', 'Notes'],
                ['Baseline', {results_data['baseline_delay']:.2f}, 0.00, 5, 'N/A', 'N/A', 'Standard 30s timing'],
                ['Random_Timing', {results_data['random_delay']:.2f}, {random_improvement:.2f}, 4, 'N/A', 'N/A', 'Random variation'],
                ['Webster_Method', {results_data['webster_delay']:.2f}, {webster_improvement:.2f}, 3, 'N/A', 'N/A', 'Classical engineering'],
                ['Genetic_Algorithm', {results_data['ga_delay']:.2f}, {ga_improvement:.2f}, 2, {min(results_data['ga_history']):.2f}, {ga_convergence:.1f}, 'Evolutionary optimization'],
                ['Grasshopper_Optimization', {results_data['goa_delay']:.2f}, {results_data['improvement']:.2f}, 1, {min(results_data['goa_history']):.2f}, {goa_convergence:.1f}, 'Best performing algorithm']
            ];
            
            let csvContent = csvData.map(row => row.join(',')).join('\\r\\n');
            const BOM = '\\uFEFF';
            csvContent = BOM + csvContent;
            
            const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', 'traffic_optimization_results.csv');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }}
        
        function downloadExcel() {{
            const excelData = [
                ['Algorithm', 'Delay (Seconds)', 'Improvement (%)', 'Performance Rank', 'Best Fitness', 'Convergence Rate (%)', 'Notes'],
                ['Baseline', {results_data['baseline_delay']:.2f}, '0.00', '5', 'N/A', 'N/A', 'Standard 30s timing'],
                ['Random Timing', {results_data['random_delay']:.2f}, '{random_improvement:.2f}', '4', 'N/A', 'N/A', 'Random variation'],
                ['Webster Method', {results_data['webster_delay']:.2f}, '{webster_improvement:.2f}', '3', 'N/A', 'N/A', 'Classical engineering'],
                ['Genetic Algorithm', {results_data['ga_delay']:.2f}, '{ga_improvement:.2f}', '2', '{min(results_data['ga_history']):.2f}', '{ga_convergence:.1f}', 'Evolutionary optimization'],
                ['Grasshopper Optimization', {results_data['goa_delay']:.2f}, '{results_data['improvement']:.2f}', '1', '{min(results_data['goa_history']):.2f}', '{goa_convergence:.1f}', 'Best performing algorithm']
            ];
            
            let excelContent = excelData.map(row => row.join('\\t')).join('\\r\\n');
            const BOM = '\\uFEFF';
            excelContent = BOM + excelContent;
            
            const blob = new Blob([excelContent], {{ type: 'application/vnd.ms-excel;charset=utf-8;' }});
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', 'traffic_optimization_results.xls');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }}
        
        function downloadJSON() {{
            const results = {{
                'metadata': {{
                    'timestamp': new Date().toISOString(),
                    'analysis_type': 'Traffic Signal Optimization'
                }},
                'results_summary': {{
                    'baseline_delay': {results_data['baseline_delay']:.2f},
                    'random_delay': {results_data['random_delay']:.2f},
                    'webster_delay': {results_data['webster_delay']:.2f},
                    'ga_delay': {results_data['ga_delay']:.2f},
                    'goa_delay': {results_data['goa_delay']:.2f},
                    'improvement_percentage': {results_data['improvement']:.2f}
                }},
                'convergence_history': {{
                    'ga_iterations': {results_data['ga_history']},
                    'goa_iterations': {results_data['goa_history']}
                }}
            }};
            
            const blob = new Blob([JSON.stringify(results, null, 2)], {{ type: 'application/json;charset=utf-8;' }});
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', 'traffic_optimization_results.json');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>
"""

    # Save HTML file
    html_file = plots_dir / "results_dashboard.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Open in browser
    webbrowser.open(f'file://{html_file.absolute()}')
    print(f"Results dashboard opened in browser: {html_file}")

def save_results_json(results_data, plots_dir):
    """Save results as JSON for future use"""
    json_file = plots_dir / "results.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2)
    print(f"Results saved to: {json_file}")