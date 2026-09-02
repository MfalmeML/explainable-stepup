import unittest
import sys

def run_all_tests():
    """Run all test suites."""
    test_modules = [
        "tests.unit.test_config_loading",
        "tests.unit.test_shap_wrapper",
        "tests.unit.test_graph_matcher",
        "tests.unit.test_ranker",
        "tests.unit.test_investigator_view",
        "tests.unit.test_outcome_store",
        "tests.integration.test_service",
        "tests.integration.test_validation_loop"
    ]
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for module in test_modules:
        try:
            tests = loader.loadTestsFromName(module)
            suite.addTests(tests)
            print(f"Loaded {module}")
        except ImportError as e:
            print(f"Failed to load {module}: {e}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)