from src.data.initialize_store import initialize_outcome_store

if __name__ == "__main__":
    store = initialize_outcome_store("outcome_store.json", num_cases=25)
    print(f"Created {len(store)} test cases")