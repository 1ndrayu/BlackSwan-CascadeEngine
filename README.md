# CASCADE RISK ENGINE: Fracture Telemetry

![Project Logo](https://img.shields.io/badge/CASCADE-RISK_ENGINE-EB4444?style=for-the-badge&logo=databricks&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Build](https://img.shields.io/badge/Build-Stable-10B981?style=for-the-badge)

**CASCADE** is a high-performance risk simulation architecture designed to model and visualize cascading failure points in complex, multidimensional systems. By utilizing a 4D Tensor-based "Risk Cube," the engine identifies "fracture points" where localized shocks evolve into systemic collapses.

---

## 🌪️ The Concept: Fracture Telemetry

Traditional risk models often fail to capture the recursive nature of cascading failures. CASCADE treats risk as a propagation problem:
- **Multidimensional Shocks**: Shocks are tracked across **Assets**, **Regions**, **Scenarios**, and **Time**.
- **Graph-Based Propagation**: An optimized traversal engine simulates how a single node failure ripples through its dependencies.
- **Performance Profiling**: The system measures latency and "cascade density" to find the exact threshold where a system breaks (The Performance Cliff).

## 🛠️ Core Technology Stack

- **Engine logic**: High-concurrency Python with **NumPy** for tensor operations.
- **Data Structure**: Selective Sparse/Dense 4D Matrix (Risk Cube) for scalability.
- **Frontend**: Premium "Bento Refined" Dashboard using **Vanilla JS**, **Chart.js**, and **CSS3**.
- **Server**: Lightweight **FastAPI-style** JSON API over native Python HTTP.

## 📁 Project Structure

```text
project_black_swan/
├── engine.py       # RiskCube (4D Tensor) & RippleEngine (Graph Logic)
├── api.py          # Simulation orchestration & impact calculation
├── server.py       # RESTful API endpoints & static asset delivery
├── telemetry.py    # Performance & timing instrumentation
├── index.html      # High-fidelity Fracture Telemetry Dashboard
├── script.js       # Dynamic charting & UI interactivity
├── styles.css      # Modern Glassmorphism & Bento Grid styling
└── run_project.bat # One-click setup & launch script
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher.
- `pip` (Python package manager).

### One-Click Launch (Windows)
Simply run the included batch script to initialize the environment and start the dashboard:
```bash
./project_black_swan/run_project.bat
```
*This script will automatically create a virtual environment, install dependencies from `requirements.txt`, and launch the web server.*

### Manual Setup
1. **Navigate to the core directory**:
   ```bash
   cd project_black_swan
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the server**:
   ```bash
   python server.py
   ```
4. **Access the Dashboard**:
   Open `http://localhost:8081` in your browser.

## 📊 Visualizing Risk
The dashboard allows you to define "Stress Parameters" (Density, Scale, Shock Magnitude) and run real-time simulations. The output identifies:
- **Latency Overload**: When the system's ability to calculate risk becomes non-linear.
- **Cascade Factor**: The ratio of systemic impact vs. initial shock.
- **Break Points**: The specific density threshold where traversal complexity spikes.

---

> [!NOTE]
> *This project was developed to explore the limits of recursive dependency modeling in high-volatility environments.*
