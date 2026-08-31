from attribution.shap_wrapper import ShapAttributor
from attribution.graph_matcher import GraphTemplateMatcher
from ranking.ranker import ReasonRanker

class ExplanationService:
    def __init__(self, model_path, background_path, template_config_path):
        self.shap = ShapAttributor(model_path, background_path)
        self.graph = GraphTemplateMatcher(template_config_path)
        self.ranker = ReasonRanker()
    
    def explain_decision(self, transaction_features, graph_features, decision):
        if decision == "APPROVE":
            return None
        shap_reasons = self.shap.get_attributions(transaction_features)
        graph_reasons = self.graph.match_signals(graph_features)
        return self.ranker.select_top_reasons(shap_reasons, graph_reasons)