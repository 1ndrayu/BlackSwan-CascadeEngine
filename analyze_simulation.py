import csv
from collections import defaultdict

def analyze_data(input_file="simulation_results.csv", output_file="analyzed_metrics.csv"):
    try:
        with open(input_file, mode='r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}. Please run the simulation generator first.")
        return

    if not data:
        print("Error: No data found in the input file.")
        return

    # Group data by Mode and Density
    # Structure: dict[Mode][Density] = list_of_rows
    grouped_data = defaultdict(lambda: defaultdict(list))
    
    for row in data:
        mode = row['Mode']
        density = row['Density']
        grouped_data[mode][density].append(row)

    print(f"Analyzing {len(data)} total simulation runs...")

    # Prepare for output
    output_rows = []
    
    for mode, densities in grouped_data.items():
        for density, rows in densities.items():
            total_runs = len(rows)
            broken_runs = sum(1 for r in rows if r['System_Broken'] == 'True')
            failure_rate = (broken_runs / total_runs) * 100 if total_runs > 0 else 0
            
            systemic_impacts = [float(r['Systemic_Impact']) for r in rows]
            impact_factors = [float(r['Impact_Factor']) for r in rows]
            
            avg_impact = sum(systemic_impacts) / total_runs
            max_impact = max(systemic_impacts)
            
            avg_factor = sum(impact_factors) / total_runs
            max_factor = max(impact_factors)
            
            # Find the most common break point density for this group
            break_points = [r['Break_Point_Density'] for r in rows if r['Break_Point_Density'] != 'Safe']
            most_common_bp = "Safe"
            if break_points:
                most_common_bp = max(set(break_points), key=break_points.count)

            output_rows.append({
                "Mode": mode,
                "Density": density,
                "Total_Runs": total_runs,
                "Broken_Runs": broken_runs,
                "Failure_Rate_%": round(failure_rate, 2),
                "Avg_Systemic_Impact": round(avg_impact, 2),
                "Max_Systemic_Impact": round(max_impact, 2),
                "Avg_Impact_Factor": round(avg_factor, 2),
                "Max_Impact_Factor": round(max_factor, 2),
                "Dominant_Break_Point": most_common_bp
            })

    # Sort the output by Mode, then by float(Density)
    output_rows.sort(key=lambda x: (x['Mode'], float(x['Density'])))

    # Write to output CSV
    fieldnames = [
        "Mode", "Density", "Total_Runs", "Broken_Runs", "Failure_Rate_%", 
        "Avg_Systemic_Impact", "Max_Systemic_Impact", "Avg_Impact_Factor", 
        "Max_Impact_Factor", "Dominant_Break_Point"
    ]

    with open(output_file, mode='w', newline='') as f:
        writer = csv.DictReader(f) # Just for fieldnames? No, need DictWriter
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)

    print(f"\n[SUCCESS] Analysis complete. Metrics written to {output_file}")
    
    # Print a quick terminal summary table
    print("\n" + "="*85)
    print(f"{'Mode':<15} | {'Density':<10} | {'Failure Rate':<15} | {'Avg Impact Multiplier':<25}")
    print("-" * 85)
    for row in output_rows:
        print(f"{row['Mode']:<15} | {row['Density']:<10} | {row['Failure_Rate_%']:<13}% | {row['Avg_Impact_Factor']:<25.2f}x")
    print("="*85 + "\n")

if __name__ == "__main__":
    analyze_data()
