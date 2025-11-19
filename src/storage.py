def save_state(state, filepath):
    import json
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def load_state(filepath):
    import json
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

def append_to_csv(data, filepath):
    import pandas as pd
    df = pd.DataFrame(data)
    df.to_csv(filepath, mode='a', header=False, index=False, encoding='utf-8-sig')

def read_csv(filepath):
    import pandas as pd
    return pd.read_csv(filepath, encoding='utf-8-sig')