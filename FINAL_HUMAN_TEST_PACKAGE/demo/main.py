import requests
from fake_legacy_module import LegacyClass  # ERROR: Module not found

def fetch_data():
    client = LegacyClass()
    return client.get_data()

if __name__ == "__main__":
    print(fetch_data())
