import csv
from pathlib import Path
from datetime import datetime

def save_results_csv(results_data, plots_dir):
    """Save optimization results to CSV file with separate columns"""
    
    csv_file = plots_dir / "optimization_results.csv"
    
    # Prepare data for CSV
    csv_data = [
        ['Algorithm', 'Delay (seconds)', 'Improvement (%)', 'Performance Rank', 'Notes'],
        ['Baseline', f"{results_data['baseline_delay']:.2f}", '0.00', '5', 'Standard 30s timing'],
        ['Random Timing', f"{results_data['random_delay']:.2f}", 
         f"{((results_data['baseline_delay'] - results_data['random_delay']) / results_data['baseline_delay'] * 100):.2f}", 
         '4', 'Random variation of baseline'],
        ['Webster Method', f"{results_data['webster_delay']:.2f}", 
         f"{((results_data['baseline_delay'] - results_data['webster_delay']) / results_data['baseline_delay'] * 100):.2f}", 
         '3', 'Classical traffic engineering'],
        ['Genetic Algorithm', f"{results_data['ga_delay']:.2f}", 
         f"{((results_data['baseline_delay'] - results_data['ga_delay']) / results_data['baseline_delay'] * 100):.2f}", 
         '2', 'Evolutionary optimization'],
        ['Grasshopper Optimization', f"{results_data['goa_delay']:.2f}", 
         f"{results_data['improvement']:.2f}", '1', 'Best performing algorithm']
    ]
    
    # Write CSV file
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
    
    print(f"CSV results saved to: {csv_file}")
    
    # Also create detailed convergence CSV
    convergence_csv = plots_dir / "convergence_history.csv"
    
    # Prepare convergence data
    max_iterations = max(len(results_data['ga_history']), len(results_data['goa_history']))
    convergence_data = [['Iteration', 'GA_Fitness', 'GOA_Fitness']]
    
    for i in range(max_iterations):
        ga_val = results_data['ga_history'][i] if i < len(results_data['ga_history']) else ''
        goa_val = results_data['goa_history'][i] if i < len(results_data['goa_history']) else ''
        convergence_data.append([i + 1, ga_val, goa_val])
    
    # Write convergence CSV
    with open(convergence_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(convergence_data)
    
    print(f"Convergence history saved to: {convergence_csv}")

def save_detailed_results(results_data, plots_dir, additional_info=None):
    """Save comprehensive results with metadata"""
    
    detailed_file = plots_dir / "detailed_results.csv"
    
    # Create detailed results with metadata
    detailed_data = [
        ['Metric', 'Value', 'Unit', 'Description'],
        ['Timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '', 'Analysis run time'],
        ['', '', '', ''],  # Empty row for separation
        ['DELAY RESULTS', '', '', ''],
        ['Baseline Delay', f"{results_data['baseline_delay']:.2f}", 'seconds', 'Standard 30s timing for all signals'],
        ['Random Timing Delay', f"{results_data['random_delay']:.2f}", 'seconds', 'Random variation around baseline'],
        ['Webster Method Delay', f"{results_data['webster_delay']:.2f}", 'seconds', 'Classical traffic engineering approach'],
        ['Genetic Algorithm Delay', f"{results_data['ga_delay']:.2f}", 'seconds', 'Evolutionary optimization result'],
        ['Grasshopper Optimization Delay', f"{results_data['goa_delay']:.2f}", 'seconds', 'Swarm intelligence optimization result'],
        ['', '', '', ''],  # Empty row
        ['PERFORMANCE METRICS', '', '', ''],
        ['Best Algorithm', 'Grasshopper Optimization' if results_data['goa_delay'] <= results_data['ga_delay'] else 'Genetic Algorithm', '', 'Algorithm with lowest delay'],
        ['Overall Improvement', f"{results_data['improvement']:.2f}", '%', 'Improvement over baseline'],
        ['GA vs Baseline Improvement', f"{((results_data['baseline_delay'] - results_data['ga_delay']) / results_data['baseline_delay'] * 100):.2f}", '%', 'GA improvement over baseline'],
        ['GOA vs GA Improvement', f"{((results_data['ga_delay'] - results_data['goa_delay']) / results_data['ga_delay'] * 100):.2f}", '%', 'GOA improvement over GA'],
        ['', '', '', ''],  # Empty row
        ['ALGORITHM PARAMETERS', '', '', ''],
        ['GA Generations', '80', 'iterations', 'Number of GA generations'],
        ['GA Population Size', '60', 'individuals', 'GA population size'],
        ['GOA Iterations', '80', 'iterations', 'Number of GOA iterations'],
        ['GOA Population Size', '30', 'grasshoppers', 'GOA swarm size'],
        ['GOA Restarts', '3', 'runs', 'Number of GOA multi-start runs']
    ]
    
    # Add additional info if provided
    if additional_info:
        detailed_data.extend([
            ['', '', '', ''],  # Empty row
            ['ADDITIONAL INFO', '', '', '']
        ])
        for key, value in additional_info.items():
            detailed_data.append([key, str(value), '', ''])
    
    # Write detailed CSV
    with open(detailed_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(detailed_data)
    
    print(f"Detailed results saved to: {detailed_file}")