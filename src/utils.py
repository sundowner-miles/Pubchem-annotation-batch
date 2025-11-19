def log_message(message):
    """Logs a message to the console."""
    print(f"[LOG] {message}")

def validate_cid(cid):
    """Validates the format of a CID."""
    if not isinstance(cid, (int, str)):
        raise ValueError("CID must be an integer or string.")
    cid_str = str(cid).strip()
    if not cid_str.isdigit() or int(cid_str) <= 0:
        raise ValueError("CID must be a positive integer.")
    return cid_str

def validate_smiles(smiles):
    """Validates the format of a SMILES string."""
    if not isinstance(smiles, str):
        raise ValueError("SMILES must be a string.")
    if not smiles:
        raise ValueError("SMILES cannot be empty.")
    return smiles.strip()

def save_checkpoint(state, filepath):
    """Saves the current state to a checkpoint file."""
    import json
    with open(filepath, 'w') as f:
        json.dump(state, f)
    log_message(f"Checkpoint saved to {filepath}")

def load_checkpoint(filepath):
    """Loads the current state from a checkpoint file."""
    import json
    try:
        with open(filepath, 'r') as f:
            state = json.load(f)
        log_message(f"Checkpoint loaded from {filepath}")
        return state
    except FileNotFoundError:
        log_message("No checkpoint found, starting fresh.")
        return None
    except json.JSONDecodeError:
        log_message("Error decoding checkpoint file, starting fresh.")
        return None