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

To run the main analysis pipeline:
```bash
python src/main.py
```

## Development

The project uses several development tools:
- pytest for testing
- pre-commit for code quality checks
- mypy for type checking

## Contact

For any questions or inquiries, please contact arunge3@smail.uni-koeln.de.


