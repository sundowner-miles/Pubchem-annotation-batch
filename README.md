# PubChem Annotation Batch Processing

This project provides a batch processing tool for retrieving annotations from the PubChem database based on Compound IDs (CIDs). It is designed to handle large datasets efficiently, allowing for manual interruption and resumption of the annotation process.

## Project Structure

- **src/**: Contains the main application code.
  - **cli.py**: Command-line interface for user interaction.
  - **processor.py**: Manages the batch processing of annotations.
  - **pubchem.py**: Functions for interacting with the PubChem API.
  - **storage.py**: Handles data reading and writing, including state management.
  - **utils.py**: Utility functions for logging and data validation.
  - **config.py**: Configuration settings for the application.

- **notebooks/**: Contains Jupyter notebooks for testing and demonstration.
  - **get_annotation.ipynb**: Notebook for testing the annotation retrieval process.

- **data/**: Directory for input data files.
  - **inputs/**: Contains input CSV files for batch processing.

- **checkpoints/**: Stores the current state of the batch processing for resumption.

- **scripts/**: Contains scripts for running the application.
  - **run_batch.sh**: Shell script to execute the batch processing.

- **tests/**: Contains unit tests for the application.
  - **test_processor.py**: Tests for the batch processing logic.

- **.gitignore**: Specifies files and directories to be ignored by version control.

- **requirements.txt**: Lists the dependencies required for the project.

- **pyproject.toml**: Project configuration file.

## Installation

To install the required dependencies, run:

```
pip install -r requirements.txt
```

## Usage

To run the batch processing, use the command line interface:

```
python src/cli.py --input data/inputs/Herb-Ingredient_csmiles_replaced.csv
```

You can also run the provided shell script:

```
bash scripts/run_batch.sh
```

## Features

- Batch processing of annotations from PubChem.
- Manual interruption and resumption of the process.
- Error handling and retry logic for API requests.
- State management to save progress and resume later.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.