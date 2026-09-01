from typing import List, Dict, Any

class ReasonRanker:
    def __init__(self, max_reasons: int = 3):
        self.max_reasons = max_reasons
    
    def select_top_reasons(self, tabular_reasons: List[Dict], graph_reasons: List[Dict]) -> List[Dict]:
        # Combine both lists
        all_reasons = tabular_reasons + graph_reasons
        
        if not all_reasons:
            return []
        
        # Deduplicate by feature/signal name to avoid redundancy
        seen = set()
        deduplicated = []
        for reason in all_reasons:
            # Use feature name for tabular, signal name for graph
            key = reason.get('feature', reason.get('signal', ''))
            if key not in seen:
                seen.add(key)
                deduplicated.append(reason)
        
        # Sort by severity_weight descending
        deduplicated.sort(key=lambda x: x.get('severity_weight', 0), reverse=True)
        
        # Return top k
        return deduplicated[:self.max_reasons]