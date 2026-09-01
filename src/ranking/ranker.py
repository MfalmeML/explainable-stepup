from typing import List, Dict, Any

class ReasonRanker:
    def __init__(self, max_reasons: int = 3):
        self.max_reasons = max_reasons
    
    def select_top_reasons(self, tabular_reasons: List[Dict], graph_reasons: List[Dict]) -> List[Dict]:
        # Combine both lists
        all_reasons = tabular_reasons + graph_reasons
        
        if not all_reasons:
            return []
        
        # Deduplicate by feature/signal name to avoid redundancy. When the
        # same key appears from both sources (e.g. a tabular feature and a
        # graph signal sharing a name), keep whichever has the higher
        # severity_weight rather than whichever appeared first in the list.
        best_by_key: Dict[str, Dict] = {}
        for reason in all_reasons:
            # Use feature name for tabular, signal name for graph
            key = reason.get('feature', reason.get('signal', ''))
            weight = reason.get('severity_weight', 0)
            existing = best_by_key.get(key)
            if existing is None or weight > existing.get('severity_weight', 0):
                best_by_key[key] = reason
        deduplicated = list(best_by_key.values())
        
        # Sort by severity_weight descending
        deduplicated.sort(key=lambda x: x.get('severity_weight', 0), reverse=True)
        
        # Return top k
        return deduplicated[:self.max_reasons]