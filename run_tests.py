import sys, os, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

loader = unittest.TestLoader()
suite = unittest.TestSuite()
for mod in ("tests.test_verifier", "tests.test_idempotency", "tests.test_edge_cases"):
    sys.path.insert(0, os.path.dirname(__file__))
    suite.addTests(loader.loadTestsFromName(mod))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
