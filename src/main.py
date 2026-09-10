from __future__ import annotations

import random
from functools import partial
from pathlib import Path
from typing import List, Callable

import matplotlib
matplotlib.use("Agg")

import numpy as np
import networkx as nx

from dataset_loader import delay_lookup_by_hour, load_ambulance_incident, load_traffic_data
from graph_builder import build_graph
from traffic_model import apply_traffic
from ambulance_model import nearest_node, random_hospital, shortest_route
from fitness import fitness, evaluate_solution
from ga import genetic_algorithm
from goa import grasshopper_optimization
from web_dashboard import generate_results_dashboard, save_results_json
from csv_exporter import save_results_csv, save_detailed_results
from visualization import plot_comparison, plot_convergence, plot_delay_over_time


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TRAFFIC_CSV = DATA_DIR / "Metro_Interstate_Traffic_Volume.csv"
AMBULANCE_CSV = DATA_DIR / "ambulance" / "911.csv"
ROAD_DIR = DATA_DIR / "road_network"

# Remove fixed seed for different results each run
# SEED = 42
# random.seed(SEED)
# np.random.seed(SEED)


def pick_signal_nodes(path: List, k: int) -> List:
    unique_nodes = []
    for node in path:
        if node not in unique_nodes:
            unique_nodes.append(node)
        if len(unique_nodes) >= k:
            break
    return unique_nodes


def webster_timings(flow: np.ndarray, lost_time: float = 16.0) -> np.ndarray:
    sat_flow = 1800.0
    y = np.clip(flow / sat_flow, 0.01, 0.9)
    Y = y.sum()
    C = (1.5 * lost_time + 5) / max(1e-3, 1 - Y)
    g = (y / max(Y, 1e-3)) * (C - lost_time)
    return np.clip(g, 5.0, 60.0)


def main():
    try:
        print("Loading datasets...")
        # Check if required data files exist
        if not TRAFFIC_CSV.exists():
            raise FileNotFoundError(f"Traffic data file not found: {TRAFFIC_CSV}")
        if not AMBULANCE_CSV.exists():
            raise FileNotFoundError(f"Ambulance data file not found: {AMBULANCE_CSV}")
        if not ROAD_DIR.exists():
            raise FileNotFoundError(f"Road network directory not found: {ROAD_DIR}")
        
        traffic_df = load_traffic_data(TRAFFIC_CSV)
        delay_lookup = delay_lookup_by_hour(traffic_df)
        # Use different seeds for different results
        base_seed = np.random.randint(0, 10000)
        incident_lat, incident_lon = load_ambulance_incident(AMBULANCE_CSV, seed=base_seed)
    except Exception as e:
        print(f"Error loading datasets: {e}")
        return

    try:
        print("Building road network graph...")
        G = build_graph(ROAD_DIR, max_edges=4000)
        
        if G.number_of_nodes() == 0:
            raise ValueError("Graph construction resulted in empty graph")
        
        apply_traffic(G, delay_lookup, hour=8, seed=base_seed)
        incident_node = nearest_node(G, incident_lat, incident_lon)
    except Exception as e:
        print(f"Error building graph or finding incident node: {e}")
        return

    # Find valid path with better error handling
    base_path = None
    max_attempts = 20  # Increased attempts
    for attempt in range(max_attempts):
        try:
            hospital_node = random_hospital(G, seed=base_seed + attempt)
            base_path, _ = shortest_route(G, hospital_node, incident_node, use_priority=True)
            if base_path and len(base_path) > 1:
                print(f"Valid path found on attempt {attempt + 1} with {len(base_path)} nodes")
                break
        except Exception as e:
            if attempt < 5:  # Only print first few errors to avoid spam
                print(f"Attempt {attempt + 1} failed: {e}")
            continue
    
    if not base_path or len(base_path) <= 1:
        print(f"Error: Could not find valid path between hospital and incident after {max_attempts} attempts")
        print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return

    signal_nodes = pick_signal_nodes(base_path, k=min(8, len(base_path)))
    dim = len(signal_nodes)
    
    if dim == 0:
        print("Error: No signal nodes found")
        print(f"Path length: {len(base_path)}, Path: {base_path[:10]}...")  # Show first 10 nodes
        return
    
    print(f"Found {dim} signal nodes for optimization")

    rng = np.random.default_rng(base_seed)

    baseline_timings = np.full(dim, 30.0)

    # Random baseline with validation
    base = np.full(dim, 30.0)
    noise = rng.uniform(0.85, 1.15, size=dim)
    random_timings = np.clip(base * noise, 10.0, 50.0)
    if random_timings.sum() > 120:
        random_timings *= 120.0 / random_timings.sum()
    
    # Ensure minimum timing constraints
    random_timings = np.maximum(random_timings, 5.0)

    # Webster with better flow estimation
    flow_guess = rng.uniform(400, 900, size=dim)
    try:
        webster = webster_timings(flow_guess)
        if webster.sum() > 120:
            webster *= 120.0 / webster.sum()
        # Ensure minimum timing constraints
        webster = np.maximum(webster, 5.0)
    except Exception as e:
        print(f"Warning: Webster timing calculation failed: {e}")
        webster = np.full(dim, 25.0)  # Fallback to reasonable default

    # Evaluate baseline solutions
    try:
        baseline_fit, _, baseline_series, baseline_delay = evaluate_solution(
            G, base_path, signal_nodes, baseline_timings
        )

        random_fit, _, _, random_delay = evaluate_solution(
            G, base_path, signal_nodes, random_timings
        )

        webster_fit, _, _, webster_delay = evaluate_solution(
            G, base_path, signal_nodes, webster
        )
    except Exception as e:
        print(f"Error evaluating baseline solutions: {e}")
        return

    # Create a properly typed fitness function wrapper
    def fit_func(timings: np.ndarray) -> float:
        return float(fitness(G, base_path, signal_nodes, timings))

    print("Running GA...")
    try:
        ga_best, ga_fit, ga_hist = genetic_algorithm(
            dim=dim,
            fitness_func=fit_func,
            bounds=(5, 60),
            pop_size=60,
            generations=80,
            mutation_rate=0.15,
            elite_size=2,
            seed=base_seed,
        )

        if ga_best.sum() > 120:
            ga_best *= 120.0 / ga_best.sum()
        
        # Validate GA results
        if len(ga_hist) == 0:
            raise ValueError("GA returned empty history")
        if np.any(np.isnan(ga_best)) or np.any(np.isinf(ga_best)):
            raise ValueError("GA returned invalid solution")
            
        print(f"GA completed successfully. Best fitness: {ga_fit:.2f}")
        
    except Exception as e:
        print(f"Error running GA: {e}")
        return

    print("Running GOA (multi-start)...")
    try:
        best_goa = None
        best_goa_fit = float("inf")
        best_goa_hist = []
        best_goa_delay = float("inf")
        successful_runs = 0
        
        for restart in range(3):
            try:
                candidate, cand_fit, cand_hist = grasshopper_optimization(
                    dim=dim,
                    fitness_func=fit_func,
                    bounds=(5, 60),
                    population_size=30,
                    iterations=80,
                    seed=base_seed + restart,
                )
                
                if candidate.sum() > 120:
                    candidate *= 120.0 / candidate.sum()
                
                # Validate candidate solution
                if np.any(np.isnan(candidate)) or np.any(np.isinf(candidate)):
                    print(f"GOA restart {restart + 1} produced invalid solution, skipping")
                    continue
                
                _, _, _, cand_delay = evaluate_solution(G, base_path, signal_nodes, candidate)
                successful_runs += 1
                
                if cand_delay < best_goa_delay:
                    best_goa_delay = cand_delay
                    best_goa = candidate
                    best_goa_fit = cand_fit
                    best_goa_hist = cand_hist
                    
            except Exception as restart_error:
                print(f"GOA restart {restart + 1} failed: {restart_error}")
                continue
        
        if successful_runs == 0:
            raise ValueError("All GOA restarts failed")
        
        goa_best, goa_fit, goa_hist = best_goa, best_goa_fit, best_goa_hist
        print(f"GOA completed with {successful_runs}/3 successful runs. Best fitness: {goa_fit:.2f}")
        
    except Exception as e:
        print(f"Error running GOA: {e}")
        return

    # Calculate real delays
    try:
        _, _, _, ga_delay = evaluate_solution(G, base_path, signal_nodes, ga_best)
        goa_delay = best_goa_delay
    except Exception as e:
        print(f"Error calculating final delays: {e}")
        return

    # Calculate improvement with safety checks
    if baseline_delay > 0:
        improvement = (baseline_delay - goa_delay) / baseline_delay * 100
        ga_improvement = (baseline_delay - ga_delay) / baseline_delay * 100
        random_improvement = (baseline_delay - random_delay) / baseline_delay * 100
        webster_improvement = (baseline_delay - webster_delay) / baseline_delay * 100
    else:
        print("Warning: Baseline delay is zero or negative, cannot calculate improvement")
        improvement = ga_improvement = random_improvement = webster_improvement = 0

    # Calculate accuracy metrics
    # Training accuracy (convergence performance)
    if len(ga_hist) > 0 and ga_hist[0] > 0:
        ga_training_accuracy = ((ga_hist[0] - min(ga_hist)) / ga_hist[0]) * 100
    else:
        ga_training_accuracy = 0
    
    if len(goa_hist) > 0 and goa_hist[0] > 0:
        goa_training_accuracy = ((goa_hist[0] - min(goa_hist)) / goa_hist[0]) * 100
    else:
        goa_training_accuracy = 0
    
    # Test accuracy (performance against baseline)
    ga_test_accuracy = max(0, ga_improvement)
    goa_test_accuracy = max(0, improvement)
    
    # Overall model accuracy (best performance)
    overall_accuracy = max(ga_test_accuracy, goa_test_accuracy)
    
    # Convergence rate (improvement per iteration)
    if len(ga_hist) > 1:
        ga_convergence_rate = (ga_hist[0] - min(ga_hist)) / len(ga_hist)
    else:
        ga_convergence_rate = 0
        
    if len(goa_hist) > 1:
        goa_convergence_rate = (goa_hist[0] - min(goa_hist)) / len(goa_hist)
    else:
        goa_convergence_rate = 0
    
    # Model stability (consistency between algorithms)
    if min(ga_delay, goa_delay) > 0:
        model_stability = 100 - (abs(ga_delay - goa_delay) / min(ga_delay, goa_delay) * 100)
    else:
        model_stability = 0

    print("\n=== RESULTS ===")
    print(f"Normal delay: {baseline_delay:.2f}")
    print(f"Random delay: {random_delay:.2f}")
    print(f"Webster delay: {webster_delay:.2f}")
    print(f"GA delay: {ga_delay:.2f}")
    print(f"GOA delay: {goa_delay:.2f}")
    print(f"Improvement: {improvement:.2f}%")
    
    print("\n=== ACCURACY METRICS ===")
    print(f"Training Accuracy:")
    print(f"  GA Training Accuracy: {ga_training_accuracy:.2f}%")
    print(f"  GOA Training Accuracy: {goa_training_accuracy:.2f}%")
    
    print(f"\nTest Accuracy:")
    print(f"  GA Test Accuracy: {ga_test_accuracy:.2f}%")
    print(f"  GOA Test Accuracy: {goa_test_accuracy:.2f}%")
    
    print(f"\nOverall Performance:")
    print(f"  Overall Model Accuracy: {overall_accuracy:.2f}%")
    print(f"  Model Stability: {model_stability:.2f}%")
    
    print(f"\nConvergence Analysis:")
    print(f"  GA Convergence Rate: {ga_convergence_rate:.2f} units/iteration")
    print(f"  GOA Convergence Rate: {goa_convergence_rate:.2f} units/iteration")
    
    print(f"\nAlgorithm Improvements:")
    print(f"  Random vs Baseline: {random_improvement:.2f}%")
    print(f"  Webster vs Baseline: {webster_improvement:.2f}%")
    print(f"  GA vs Baseline: {ga_improvement:.2f}%")
    print(f"  GOA vs Baseline: {improvement:.2f}%")

    if goa_delay > 0 and not np.isnan(goa_fit) and not np.isinf(goa_fit):
        print(f"\nFitness vs Real ratio: {goa_fit / goa_delay:.3f}")
    else:
        print("\nFitness vs Real ratio: N/A")

    # Generate plots and dashboard
    try:
        plots_dir = Path(__file__).resolve().parent.parent / "plots"
        plots_dir.mkdir(exist_ok=True)

        plot_convergence(goa_hist, "GOA", plots_dir / "goa.png")
        plot_convergence(ga_hist, "GA", plots_dir / "ga.png")

        plot_comparison(
            {
                "Normal": baseline_delay,
                "Random": random_delay,
                "Webster": webster_delay,
                "GA": ga_delay,
                "GOA": goa_delay,
            },
            plots_dir / "comparison.png",
        )

        # Prepare results data for web dashboard
        results_data = {
            "baseline_delay": float(baseline_delay),
            "random_delay": float(random_delay),
            "webster_delay": float(webster_delay),
            "ga_delay": float(ga_delay),
            "goa_delay": float(goa_delay),
            "improvement": float(improvement),
            "ga_improvement": float(ga_improvement),
            "random_improvement": float(random_improvement),
            "webster_improvement": float(webster_improvement),
            "ga_history": [float(x) for x in ga_hist],
            "goa_history": [float(x) for x in goa_hist],
            "ga_training_accuracy": float(ga_training_accuracy),
            "goa_training_accuracy": float(goa_training_accuracy),
            "ga_test_accuracy": float(ga_test_accuracy),
            "goa_test_accuracy": float(goa_test_accuracy),
            "overall_accuracy": float(overall_accuracy),
            "model_stability": float(model_stability),
            "ga_convergence_rate": float(ga_convergence_rate),
            "goa_convergence_rate": float(goa_convergence_rate)
        }

        # Save results and generate web dashboard
        save_results_json(results_data, plots_dir)
        save_results_csv(results_data, plots_dir)
        save_detailed_results(results_data, plots_dir, {
            'Signal_Nodes_Count': len(signal_nodes),
            'Path_Length': len(base_path),
            'Random_Seed': base_seed,
            'Graph_Nodes': G.number_of_nodes(),
            'Graph_Edges': G.number_of_edges()
        })
        generate_results_dashboard(results_data, plots_dir)
        
    except Exception as e:
        print(f"Error generating plots/dashboard: {e}")
        print("Results calculated successfully but visualization failed")
        # Still save basic results even if visualization fails
        try:
            save_results_json(results_data, plots_dir)
            print("Basic results saved despite visualization error")
        except Exception as save_error:
            print(f"Failed to save even basic results: {save_error}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error in main execution: {e}")
        import traceback
        traceback.print_exc()
