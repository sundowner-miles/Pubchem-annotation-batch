# Configuration settings for the PubChem annotation batch processing application

API_ENDPOINT = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
TIMEOUT = 10  # seconds for API requests
RETRIES = 3  # number of retries for failed requests
BACKOFF_FACTOR = 1.5  # backoff factor for retries
DELAY_BETWEEN_REQUESTS = 0.2  # delay between requests in seconds
OUTPUT_FILE_NAME = "smiles_annotation_results.csv"  # default output file name
CHECKPOINT_FILE = "checkpoints/state.json"  # path to the checkpoint file for resuming
LOGGING_LEVEL = "INFO"  # logging level for the application