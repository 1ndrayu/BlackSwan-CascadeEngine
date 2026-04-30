import csv
import time
from datetime import datetime
from api import run_simulation

def generate_simulation_logs(filename="simulation_results.csv"):
    # Define parameters for testing
    modes = ['isolated', 'regional', 'systemic', 'black_swan']
    densities = [0.1, 0.5, 1.0, 2.0, 5.0]
    dimension_scales = [10, 50, 100, 250, 500]
    regions = 20
    scenarios = 10
    time_units = 12
    initial_shock = 1000000.0
    num_nodes = 500

    print(f"Generating simulation logs to {filename}...")

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow([
            "Timestamp", "Mode", "Dimension_Scale", "Density", 
            "Regions", "Scenarios", "Time_Units", "Active_Nodes", 
            "Initial_Shock", "Systemic_Impact", "System_Broken", 
            "Break_Point_Density", "Impact_Factor"
        ])

        for mode in modes:
            print(f"\n--- Running scenario: {mode.upper()} ---")
            results = run_simulation(
                densities=densities,
                dimension_scales=dimension_scales,
                regions=regions,
                scenarios=scenarios,
                time_units=time_units,
                initial_shock=initial_shock,
                num_nodes=num_nodes,
                mode=mode
            )

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            is_broken = results["hasBroken"]
            break_point = results["breakPointDensity"]
            factor = results["factor"]

            for dataset in results["datasets"]:
                dim_scale = dataset["label"]
                impacts = dataset["data"]
                
                for density, impact in zip(densities, impacts):
                    writer.writerow([
                        timestamp,
                        mode,
                        dim_scale,
                        density,
                        regions,
                        scenarios,
                        time_units,
                        num_nodes,
                        initial_shock,
                        impact,
                        is_broken,
                        break_point,
                        factor
                    ])
                    
    print(f"\n[SUCCESS] Logs successfully written to {filename}")

if __name__ == "__main__":
    generate_simulation_logs()
