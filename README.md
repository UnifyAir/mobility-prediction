# Mobility Prediction for NR Handovers

This project implements a user mobility prediction model inspired by the [AgentMove Research Paper](https://arxiv.org/abs/2408.13986). The primary goal is to identify and leverage **periodic patterns** in a user's trajectory to predict future locations.

## Table of Contents

- [Mobility Prediction for NR Handovers](#mobility-prediction-for-nr-handovers)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Key Features](#key-features)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Usage](#usage)
  - [TODOs](#todos)
  - [Project Structure](#project-structure)
  - [License](#license)

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

- **Python 3.10+**
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
1. Set the gemini api key in .env:
   ```bash
   GEMINI_API_KEY=
   ```

2. Run the api server
   ```bash
   bash run.sh
   ```

3. Test the results with following curl request: 
   ```bash
   curl --location 'http://localhost:8000/predict' \
   --header 'Content-Type: application/json' \
   --data '{
      "user_id": "1",
      "cell_tower_loads": {
         "187650": 70,
         "187648": 10,
         "306258": 10,
         "334594": 15,
         "334593": 20
      },
      "current_cell_tower": "187648",
      "timestamp": 0
   }'
   ```

## TODOs
- [X] Extending to cell prediction.
- [ ] Data Preprocessing pipeline
- [ ] Visualize plot predictions
- [ ] Refine Periodicity Detection
- [ ] Explore reinforcement learning for dynamic route selection

## Project Structure

```
mobility-prediction/
├── data/
│   └── user_trajectory.csv          # Example input data
├── util-scripts/
│   └── find-cells.py                # Getting cell location inside the box.
│   └── geojson_smooth.py            # Smoothening a geojson path
│   └── geojson_to_csv.py            # Smoothening a geojson path
│   └── common_utils.py              # Common helper libraries for util script 
│   └── select_top_cells.py          # Select cells near a geojson path
├── api/
│   ├── __init__.py
│   ├── app.py                       # FastAPI backend agent
│   ├── database.py                  # Database initialization and operations
│   ├── models.py                    # Pydantic models for request validation
│   ├── services.py                  # Core logic for prediction and LLM integration
│   └── utils.py                     # Utility functions (e.g., CSV loading)
├── requirements.txt
├── run.sh
├── .env
├── README.md
└── LICENSE
```

## License

This project is licensed under the MIT License. Feel free to modify and distribute your own versions. We kindly request citing this repository and the AgentMove research paper if you build upon it for academic or industrial applications.
