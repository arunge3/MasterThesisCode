# MasterThesisCode

## Description

This repo contains code that was created as part of Annabelle Runge's master's thesis. 

The code can be executed via the main.py function. The game number must also be passed. However, the paths may need to be changed. The paths are based on the directory "D" and the corresponding hard drive that contains the data. 

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/arunge3/MasterThesisCode.git
    ```
2. Navigate to the project directory:
    ```bash
    cd MasterThesisCode
    ```
3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Used python version: 3.9.13
5. Create a virtual environment:
    ```bash
    python -m venv env
    ```
6. Activate the virtual environment:
    - On Windows:
        ```bash
        .\env\Scripts\activate
        ```
    - On macOS and Linux:
        ```bash
        source env/bin/activate
        ```

## Usage

To run the main script, use the following command:
```bash
python main.py
```

## Project Structure

- `computeDifference/`: Contains code to calculate the differences between newly annotated and original events. 
- `existingCode/`: Code that was already available from Manuel Bassek. 
- `figures/`: Contains the generated plots that represent the synchronisation of the game progression phases and event data.
- `helpFunctions/`: Auxiliary functions that are used for reformatted.
- `plotFunctions/`: Contains code that performs the rule-based synchronisation and code that creates the graphics.
- `main.py`: This function must be executed so that the rule-based synchronisation is carried out for a game. 
- `reformat_json`: The code was used to prepare the event data for the annotation module. 
- `README.md`: Project documentation.

## Contact

For any questions or inquiries, please contact arunge3@smail.uni-koeln.de.


