# Mobility Prediction for NR Handovers

This project implements a user mobility prediction model inspired by the [AgentMove Research Paper](https://arxiv.org/abs/2408.13986). The primary goal is to identify and leverage **periodic patterns** in a user's trajectory to predict future locations.

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Project Structure](#project-structure)
7. [TODOs](#todos)
8. [License](#license)

## Overview

Human mobility often follows cyclical or periodic patterns (e.g., daily commute, regular shopping trips). By analyzing these recurring trajectories, we aim to forecast a user's next location with greater accuracy.

- **Research Paper**: [AgentMove](https://arxiv.org/abs/2408.13986)
- **Current Focus**: Periodic/cyclical motion patterns

Our approach currently involves:

1. Detecting potential periodic intervals (e.g., daily/weekly cycles).
2. Predicting the next location based on learned cyclical behavior.

## Key Features

- **Periodic Pattern Detection**: Identifies recurring trajectories from historical data.
- **Forecasting Framework**: Predicts future locations based on cyclical movement.

## Requirements

- **Python 3.8+**
- Libraries:
  - `numpy`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/unifyair/mobility-prediction.git
   cd mobility-prediction
   ```

2. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Prepare your data:
   - Ensure you have a CSV or similar file with columns like user_id, timestamp, latitude, longitude.
   - Place your data in the data/ directory (or update the config to point to your data location).
2. Run the periodic pattern detection script:
   ```bash
   python detect_periodic_patterns.py --input data/user_trajectory.csv --output results/predicted_locations.csv
   ```
3. Review results:
   - Check the results/ folder for the output files.

## TODOs

- [ ] Data Preprocessing pipeline
- [ ] Visualize plot predictions
- [ ] Refine Periodicity Detection
- [ ] Explore reinforcement learning for dynamic route selection
- [ ] Extending to cell prediction.

## Project Structure

```
periodic-mobility-prediction/
├── data/
│   └── user_trajectory.csv          # Example input data
├── results/
│   └── predicted_locations.csv      # Example output
├── scripts/
│   └── detect_periodic_patterns.py  # Main script for periodic detection
├── util-scripts/
│   └── find-cells.py                # Getting cell location inside the box.
│   └── geojson-smooth.py            # Smoothening a geojson path
│   └── select_top_cells.py          # Select cells near a geojson path
├── requirements.txt
├── README.md
└── LICENSE
```

## License

This project is licensed under the MIT License. Feel free to modify and distribute your own versions. We kindly request citing this repository and the AgentMove research paper if you build upon it for academic or industrial applications.
