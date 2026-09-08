import json
import sys
import os
from datetime import datetime

def migrate_store(store_path: str):
    """Apply schema migrations to the store."""
    if not os.path.exists(store_path):
        print(f"Store not found: {store_path}")
        return
    
    with open(store_path, 'r') as f:
        store = json.load(f)
    
    # Add version if missing
    if '_schema_version' not in store:
        store['_schema_version'] = '1.0'
        store['_migrated_at'] = datetime.utcnow().isoformat()
    
    # Add indexes for performance (in production, use proper DB)
    if '_indexes' not in store:
        store['_indexes'] = {
            'by_decision': {},
            'by_timestamp': []
        }
    
    # Build indexes
    for tx_id, data in store.items():
        if tx_id.startswith('_'):
            continue
        decision = data.get('decision')
        if decision:
            if decision not in store['_indexes']['by_decision']:
                store['_indexes']['by_decision'][decision] = []
            store['_indexes']['by_decision'][decision].append(tx_id)
        
        timestamp = data.get('decision_timestamp')
        if timestamp:
            store['_indexes']['by_timestamp'].append((timestamp, tx_id))
    
    store['_indexes']['by_timestamp'].sort()
    
    # Write back
    with open(store_path, 'w') as f:
        json.dump(store, f, indent=2)
    
    print(f"Migration complete. Store version: {store['_schema_version']}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--store', required=True, help='Path to store file')
    args = parser.parse_args()
    migrate_store(args.store)