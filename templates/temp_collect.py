import sys
import json
import pytest

sys.stdout.reconfigure(encoding='utf-8')

class CollectorPlugin:
    def pytest_collection_modifyitems(self, items):
        print("JSON_START")
        print(json.dumps([item.nodeid for item in items]))
        print("JSON_END")

if __name__ == "__main__":
    args = ["--collect-only", "--continue-on-collection-errors", "-q"] + sys.argv[1:]
    pytest.main(args, plugins=[CollectorPlugin()])
