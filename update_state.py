import os
import json
import sys

STATE_FILE = "portfolio_state.json"

def show_help():
    print("\n🛠️  Portfolio State Manager")
    print("Usage: python3 update_state.py <TOKEN> <FIELD> <VALUE>")
    print("Example: python3 update_state.py SOL balance 0.25")
    print("Example: python3 update_state.py ATOM avg_buy 2.15")
    print("Available Fields: balance, avg_buy\n")

def main():
    if len(sys.argv) != 4:
        show_help()
        return

    token = sys.argv[1].upper()
    field = sys.argv[2].lower()
    
    try:
        value = float(sys.argv[3])
    except ValueError:
        print(f"❌ Error: Value '{sys.argv[3]}' must be a valid number.")
        return

    if not os.path.exists(STATE_FILE):
        print(f"❌ Error: {STATE_FILE} not found in current directory.")
        return

    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return

    if token not in state:
        print(f"⚠️ Token '{token}' not found in state. Creating new entry...")
        state[token] = {"balance": 0.0, "avg_buy": 0.0}

    if field not in state[token]:
        print(f"❌ Error: Field '{field}' does not exist for {token}. Use 'balance' or 'avg_buy'.")
        return

    old_val = state[token][field]
    state[token][field] = value

    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
        print(f"✅ Success! Updated {token} {field}: {old_val} ➡️ {value}")
    except Exception as e:
        print(f"❌ Error saving state file: {e}")

if __name__ == "__main__":
    main()
