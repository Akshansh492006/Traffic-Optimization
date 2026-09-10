from __future__ import annotations

import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pandas as pd


class AccuracyTracker:
    """Track training and testing accuracy for optimization algorithms"""
    
    def __init__(self):
        self.training_history = {
            'ga': {'fitness': [], 'accuracy': [], 'predictions': [], 'targets': []},
            'goa': {'fitness': [], 'accuracy': [], 'predictions': [], 'targets': []}
        }
        self.testing_results = {
            'ga': {'accuracy': 0.0, 'mae': 0.0, 'mse': 0.0, 'r2': 0.0},
            'goa': {'accuracy': 0.0, 'mae': 0.0, 'mse': 0.0, 'r2': 0.0}
        }
        self.baseline_metrics = {'accuracy': 0.0, 'mae': 0.0, 'mse': 0.0, 'r2': 0.0}
        
    def calculate_accuracy(self, predicted_delay: float, actual_delay: float, tolerance: float = 5.0) -> float:
        """Calculate accuracy based on delay prediction within tolerance"""
        error = abs(predicted_delay - actual_delay)
        accuracy = max(0.0, 1.0 - (error / max(actual_delay, 1.0)))
        return min(accuracy, 1.0) * 100  # Convert to percentage
    
    def update_training_accuracy(self, algorithm: str, fitness_value: float, 
                               predicted_delay: float, actual_delay: float):
        """Update training accuracy for given algorithm"""
        accuracy = self.calculate_accuracy(predicted_delay, actual_delay)
        self.training_history[algorithm]['fitness'].append(fitness_value)
        self.training_history[algorithm]['accuracy'].append(accuracy)
        self.training_history[algorithm]['predictions'].append(predicted_delay)
        self.training_history[algorithm]['targets'].append(actual_delay)
    
    def calculate_testing_metrics(self, algorithm: str, predictions: List[float], 
                                targets: List[float]) -> Dict[str, float]:
        """Calculate comprehensive testing metrics"""
        predictions = np.array(predictions)
        targets = np.array(targets)
        
        # Accuracy (percentage within tolerance)
        accuracies = [self.calculate_accuracy(p, t) for p, t in zip(predictions, targets)]
        avg_accuracy = np.mean(accuracies)
        
        # Regression metrics
        mae = mean_absolute_error(targets, predictions)
        mse = mean_squared_error(targets, predictions)
        r2 = r2_score(targets, predictions) if len(set(targets)) > 1 else 0.0
        
        metrics = {
            'accuracy': avg_accuracy,
            'mae': mae,
            'mse': mse,
            'r2': r2,
            'rmse': np.sqrt(mse)
        }
        
        self.testing_results[algorithm] = metrics
        return metrics
    
    def set_baseline_metrics(self, baseline_delay: float, optimized_delays: Dict[str, float]):
        """Set baseline metrics for comparison"""
        targets = [baseline_delay] * len(optimized_delays)
        predictions = list(optimized_delays.values())
        
        accuracies = [self.calculate_accuracy(p, baseline_delay) for p in predictions]
        self.baseline_metrics = {
            'accuracy': np.mean(accuracies),
            'mae': mean_absolute_error(targets, predictions),
            'mse': mean_squared_error(targets, predictions),
            'r2': r2_score(targets, predictions) if len(set(targets)) > 1 else 0.0
        }
    
    def get_training_accuracy_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of training accuracy for both algorithms"""
        summary = {}
        for algo in ['ga', 'goa']:
            if self.training_history[algo]['accuracy']:
                summary[algo] = {
                    'final_accuracy': self.training_history[algo]['accuracy'][-1],
                    'avg_accuracy': np.mean(self.training_history[algo]['accuracy']),
                    'max_accuracy': np.max(self.training_history[algo]['accuracy']),
                    'min_accuracy': np.min(self.training_history[algo]['accuracy']),
                    'improvement': (self.training_history[algo]['accuracy'][-1] - 
                                  self.training_history[algo]['accuracy'][0]) if len(self.training_history[algo]['accuracy']) > 1 else 0.0
                }
            else:
                summary[algo] = {'final_accuracy': 0.0, 'avg_accuracy': 0.0, 'max_accuracy': 0.0, 'min_accuracy': 0.0, 'improvement': 0.0}
        return summary
    
    def plot_training_accuracy(self, save_path: Optional[Path] = None):
        """Plot training accuracy curves for both algorithms"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Accuracy plot
        for algo in ['ga', 'goa']:
            if self.training_history[algo]['accuracy']:
                ax1.plot(self.training_history[algo]['accuracy'], 
                        label=f'{algo.upper()} Accuracy', linewidth=2)
        
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Accuracy (%)')
        ax1.set_title('Training Accuracy Over Time')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Fitness plot
        for algo in ['ga', 'goa']:
            if self.training_history[algo]['fitness']:
                ax2.plot(self.training_history[algo]['fitness'], 
                        label=f'{algo.upper()} Fitness', linewidth=2)
        
        ax2.set_xlabel('Iteration')
        ax2.set_ylabel('Fitness (Delay)')
        ax2.set_title('Training Fitness Over Time')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def plot_testing_comparison(self, save_path: Optional[Path] = None):
        """Plot testing metrics comparison"""
        algorithms = ['GA', 'GOA']
        metrics = ['accuracy', 'mae', 'r2']
        metric_names = ['Accuracy (%)', 'MAE (seconds)', 'R² Score']
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        for i, (metric, name) in enumerate(zip(metrics, metric_names)):
            values = [self.testing_results['ga'][metric], self.testing_results['goa'][metric]]
            colors = ['skyblue', 'lightcoral']
            
            bars = axes[i].bar(algorithms, values, color=colors)
            axes[i].set_title(f'Testing {name}')
            axes[i].set_ylabel(name)
            axes[i].grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                axes[i].text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                           f'{value:.2f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
        plt.close()
    
    def save_accuracy_report(self, save_path: Path):
        """Save comprehensive accuracy report"""
        report = {
            'training_summary': self.get_training_accuracy_summary(),
            'testing_results': self.testing_results,
            'baseline_metrics': self.baseline_metrics,
            'training_history': {
                algo: {
                    'final_accuracy': hist['accuracy'][-1] if hist['accuracy'] else 0.0,
                    'accuracy_trend': hist['accuracy'][-10:] if len(hist['accuracy']) >= 10 else hist['accuracy'],
                    'fitness_trend': hist['fitness'][-10:] if len(hist['fitness']) >= 10 else hist['fitness']
                }
                for algo, hist in self.training_history.items()
            }
        }
        
        with open(save_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    def print_accuracy_summary(self):
        """Print formatted accuracy summary"""
        print("\n" + "="*60)
        print("ACCURACY SUMMARY REPORT")
        print("="*60)
        
        # Training Summary
        print("\nTRAINING ACCURACY:")
        print("-" * 30)
        training_summary = self.get_training_accuracy_summary()
        for algo, metrics in training_summary.items():
            print(f"{algo.upper()}:")
            print(f"  Final Accuracy: {metrics['final_accuracy']:.2f}%")
            print(f"  Average Accuracy: {metrics['avg_accuracy']:.2f}%")
            print(f"  Max Accuracy: {metrics['max_accuracy']:.2f}%")
            print(f"  Improvement: {metrics['improvement']:.2f}%")
            print()
        
        # Testing Summary
        print("TESTING METRICS:")
        print("-" * 30)
        for algo, metrics in self.testing_results.items():
            print(f"{algo.upper()}:")
            print(f"  Accuracy: {metrics['accuracy']:.2f}%")
            print(f"  MAE: {metrics['mae']:.2f} seconds")
            print(f"  RMSE: {metrics['rmse']:.2f} seconds")
            print(f"  R² Score: {metrics['r2']:.3f}")
            print()
        
        # Best Algorithm
        best_algo = 'GA' if self.testing_results['ga']['accuracy'] > self.testing_results['goa']['accuracy'] else 'GOA'
        print(f"BEST PERFORMING ALGORITHM: {best_algo}")
        print("="*60)


def create_test_scenarios(G, base_path, signal_nodes, num_scenarios: int = 20, seed: int = 42) -> List[Tuple[np.ndarray, float]]:
    """Create test scenarios with known optimal solutions"""
    from fitness import evaluate_solution
    
    rng = np.random.default_rng(seed)
    scenarios = []
    
    for i in range(num_scenarios):
        # Generate test timing configurations
        test_timings = rng.uniform(10, 50, size=len(signal_nodes))
        if test_timings.sum() > 120:
            test_timings *= 120.0 / test_timings.sum()
        
        # Calculate actual delay
        try:
            _, _, _, actual_delay = evaluate_solution(G, base_path, signal_nodes, test_timings)
            scenarios.append((test_timings, actual_delay))
        except Exception:
            continue
    
    return scenarios


__all__ = ["AccuracyTracker", "create_test_scenarios"]