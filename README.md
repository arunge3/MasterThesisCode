# MasterThesisCode

## Description

This repository contains code developed for Annabelle Runge's master's thesis, focusing on sports event analysis and synchronization. The project implements various approaches for synchronizing sports event data and analyzing game progression phases.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/arunge3/MasterThesisCode.git
    ```
2. Navigate to the project directory:
    ```bash
    cd MasterThesisCode
    ```
3. Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    # On Windows:
    .\.venv\Scripts\activate
    # On macOS and Linux:
    source .venv/bin/activate
    ```
4. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Project Structure

The project is organized into the following main components:

### Source Code (`src/`)
- `main.py`: Entry point for running the synchronization and analysis pipeline
- `main_structure.py`: Core structure and functionality implementation
- `preprocessing/`: Data preprocessing and transformation modules
- `synchronization_approaches/`: Different methods for synchronizing event data
- `evaluation/`: Code for evaluating synchronization results
- `sport_analysis/`: Sports-specific analysis modules
- `plot_functions/`: Visualization and plotting utilities
- `help_functions/`: Utility functions and helper modules
- `variables/`: Configuration and constant definitions
- `existing_code/`: Legacy code from previous implementations

### Testing (`tests/`)
- Unit tests and integration tests for various components

### Configuration
- `pyproject.toml`: Project configuration and dependencies
- `pytest.ini`: Testing configuration
- `.pre-commit-config.yaml`: Pre-commit hooks configuration

### Output
- `figures/`: Generated plots and visualizations

## Usage

The code can be run in two ways:

1. Using the main script:
```bash
python src/main.py
```

2. Using the `approach_plot` function with custom parameters:
```python
from src.main_structure import approach_plot

# Example usage:
approach_plot(
    match_id="your_match_id",  # ID of the match to analyze
    approach="your_approach",   # Name of the synchronization approach to use
    base_path="your_base_path" # Base path for data files
)
```

The `approach_plot` function allows you to:
- Specify which match to analyze using `match_id`
- Choose which synchronization approach to use with `approach`
- Set the base path for data files with `base_path`

## Development

The project uses several development tools:
- pytest for testing
- pre-commit for code quality checks
- mypy for type checking

## Contact

For any questions or inquiries, please contact arunge3@smail.uni-koeln.de.


