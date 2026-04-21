from elasticsearch import Elasticsearch

# Forcing IPv4 to bypass the localhost trap
client = Elasticsearch("http://127.0.0.1:9200")

try:
    # client.info() sends a GET request, forcing the server to reveal the actual error
    print(client.info())
except Exception as e:
    print(f"THE REAL ERROR: {e}")