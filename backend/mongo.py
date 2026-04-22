from pymongo import MongoClient
from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
from urllib.request import urlopen
import json
from sentence_transformers import SentenceTransformer
from flask_cors import CORS
import yaml
import certifi
import numpy as np
import traceback

model = SentenceTransformer("all-MiniLM-L6-v2")
ca = certifi.where()

# Configuration Constants
DB_NAME = "project"
COLLECTION_NAME = "user"
INDEX_NAME = "books"

class AtlasClient:
    def __init__(self, atlas_uri, dbname):
        # We use the ca for secure connection to Atlas
        self.mongodb_client = MongoClient(atlas_uri, tlsCAFile=ca)
        self.database = self.mongodb_client[dbname]

    def ping(self):
        self.mongodb_client.admin.command("ping")

    def get_collection(self, collection_name):
        collection = self.database[collection_name]
        return collection

    def find(self, collection_name, filter={}, limit=0):
        collection = self.database[collection_name]
        items = list(collection.find(filter=filter, limit=limit))
        return items
    
    def insert(self, collection_name, user_info):
        collection = self.database[collection_name]
        result = collection.insert_one(user_info)
        return result

    def delete(self, collection_name, user_id):
        collection = self.database[collection_name]
        result = collection.delete_one(user_id)
        return result
    
    def update(self, collection_name, user_id, new_value):
        collection = self.database[collection_name]
        result = collection.update_one(user_id, new_value)
        return result

app = Flask(__name__)
CORS(app)

def pretty_response(response):
    outputs = []
    # Safety check for empty results
    if not response or "hits" not in response or len(response["hits"]["hits"]) == 0:
        return "Your search returned no results."
    else:
        for hit in response["hits"]["hits"]:
            output = {
                "id": hit["_id"],
                "score": hit["_score"],
                "title": hit["_source"].get("title", "N/A"),
                "date": hit["_source"].get("publication_date", "N/A"),
                "publisher": hit["_source"].get("publisher", "N/A"),
                "edition": hit["_source"].get("edition", "N/A"),
                "search_times": hit["_source"].get("search_times", 0),
                "author": hit["_source"].get("author", "N/A"),
                "isbn": hit["_source"].get("ISBN-13", "N/A"),
                "genre": hit["_source"].get("genre", "N/A"),
                "summary": hit["_source"].get("summary", "")
            }
            outputs.append(output)
    return outputs

def search_time_increase(response):
    if response == "Your search returned no results.":
        return 0
    for resp in response:
        update_body = {
            "script": {
                "source": "ctx._source.search_times += 1",
                "lang": "painless"
            }
        }
        try:
            client.update(index=INDEX_NAME, id=resp["id"], body=update_body)
        except Exception as e:
            print(f"Error updating search times: {e}")

# --- ACCOUNT MANAGEMENT ROUTES ---

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if 'username' not in data or 'email' not in data:
        return jsonify({"message": "Please enter username and email"}), 400
    
    username = data['username']
    email = data['email']
    
    # FIXED LOGIC: Original was 'if username or email' which was backwards
    if not username or not email:
        return jsonify({"message": "Please enter valid username or email"}), 400
    
    user_info = {
        "username": username,
        "email": email,
        "search_history": [],
        "read_books": []
    }
    
    if atlas_client.find(collection_name=COLLECTION_NAME, filter={"email": email}):
        return jsonify({"message": "Email already exists"}), 400

    resp = atlas_client.insert(collection_name=COLLECTION_NAME, user_info=user_info)
    return jsonify({"message": f"User registered successfully, id: {resp.inserted_id}"}), 200

@app.route('/delete', methods=['POST'])
def delete():
    data = request.json
    email = data['email']

    if not atlas_client.find(collection_name=COLLECTION_NAME, filter={"email": email}):
        return jsonify({"message": "Email do not exist"}), 400

    resp = atlas_client.delete(collection_name=COLLECTION_NAME, user_id={"email": email})
    return jsonify({"message": f"User deleted successfully. See you again"}), 200

@app.route("/searched", methods=['POST'])
def search_history_update():
    data = request.json
    if 'search' not in data or 'email' not in data:
        return jsonify({"message": "Missing search or email"}), 400
    
    email = data['email']
    query = data['search']
    
    if len(query) < 1 or not isinstance(query, list):
        return jsonify({"message": "Invalid search history."}), 400
        
    update = {
        "$push": {
            "search_history": {
                "$each": query
            }
        }
    }
    resp = atlas_client.update(collection_name=COLLECTION_NAME, user_id={"email": email}, new_value=update)
    return jsonify({"message": "User search history updated"}), 200

@app.route("/read", methods=['POST'])
def read_books_update():
    data = request.json
    email = data['email']
    query = data['read']
    update = {
        "$push": {
            "read_books": {
                "$each": query
            }
        }
    }
    resp = atlas_client.update(collection_name=COLLECTION_NAME, user_id={"email": email}, new_value=update)
    return jsonify({"message": "User read books updated"}), 200

# --- SEARCH ROUTES ---

@app.route("/elasticsearch")
def elastic_info():
    try:
        info = client.info()
        return jsonify(dict(info))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/elasticsearch/summary")
def search():
    query = request.args.get("query") 
    if not query:
        return jsonify({"message": "No query", "data": []}), 400
        
    response = client.search(
        index=INDEX_NAME,
        knn={
            "field": "summary_vector",
            "query_vector": model.encode(query).tolist(),
            "k": 10,
            "num_candidates": 100,
        },
    )
    results = pretty_response(response)
    search_time_increase(results)
    return jsonify({"message": f"Request success", "data": results}), 200

@app.route("/elasticsearch/filter", methods=['GET'])
def filter():
    author = request.args.get("author") 
    title = request.args.get("title") 
    genre = request.args.get("genre") 
    isbn = request.args.get("isbn") 
    publisher = request.args.get("publisher")
    edition = request.args.get("edition") 

    filter_list = []
    if author: filter_list.append({"match": {"author": author}})
    if isbn: filter_list.append({"term": {"ISBN-13": isbn}})
    if title: filter_list.append({"match_phrase": {"title": title}})
    if publisher: filter_list.append({"term": {"publisher": publisher}})
    if edition: filter_list.append({"term": {"edition": edition}})
    if genre: filter_list.append({"term": {"genre": genre}})

    query = {
        "query": {
            "bool": {
                "filter": filter_list
            }
        }
    }
    response = client.search(index=INDEX_NAME, body=query)
    results = pretty_response(response)
    search_time_increase(results)
    return jsonify({"message": f"Get data successfully", "data": results}), 200

@app.route("/elasticsearch/popular", methods=['GET'])
def popular():
    order = request.args.get("order")
    if order != "asc" and order != "desc":
        order = "desc"
    query = {
        "query": {
            "match_all": {}
        },
        "sort": [
            {
                "search_times": {
                    "order": order
                }
            }
        ]
    }
    response = client.search(index=INDEX_NAME, body=query)
    return jsonify({"message": f"Get data successfully", "data": pretty_response(response)}), 200

@app.route("/elasticsearch/catalog", methods=['GET'])
def get_catalog():
    try:
        # Simplified query to avoid sorting errors
        query = {
            "size": 1000, 
            "query": {"match_all": {}}
        }
        
        response = client.search(index=INDEX_NAME, body=query)
        
        # Log to terminal so you can see it working
        print(f"Catalog fetched {len(response['hits']['hits'])} books")
        
        return jsonify({"data": pretty_response(response)}), 200
        
    except Exception as e:
        print(f"CATALOG ERROR: {str(e)}")
        return jsonify({"message": "Server error", "error": str(e)}), 500
        
@app.route("/elasticsearch/customize", methods=['POST'])
def customize():
    try:
        data = request.json
        if not data or 'email' not in data:
            return jsonify({"message": "Please enter email"}), 400
        
        email = data['email']
        user_list = atlas_client.find(collection_name=COLLECTION_NAME, filter={"email": email})

        if not user_list:
            search_history = []
            read_books = []
        else:
            user = user_list[0]
            search_history = user.get("search_history", [])
            read_books = user.get("read_books", [])

        if len(search_history) < 1:
            query = {
                "query": {"match_all": {}},
                "sort": [{"search_times": {"order": "desc"}}],
                "size": 10
            }
            response = client.search(index=INDEX_NAME, body=query)
            return jsonify({"message": "Get data successfully", "data": pretty_response(response)}), 200

        # Vector average calculation
        query_vector = model.encode(search_history).mean(axis=0)
        query_vector_list = query_vector.tolist()

        search_body = {
            "query": {
                "bool": {
                    "must": {
                        "knn": {
                            "field": "book_vector",
                            "query_vector": query_vector_list,
                            "k": 10,
                            "num_candidates": 100
                        }
                    }
                }
            }
        }

        if read_books:
            search_body["query"]["bool"]["must_not"] = {
                "terms": {"_id": read_books}
            }

        response = client.search(index=INDEX_NAME, body=search_body)
        return jsonify({"message": "Request success", "data": pretty_response(response)}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route("/elasticsearch/insert", methods=['POST'])
def insert():
    try:
        books = request.json
        if not books:
            return jsonify({"message": "No data provided"}), 400
            
        if not isinstance(books, list): 
            books = [books]
        
        operations = []
        for book in books:
            # Ensure every field is a string and has a fallback
            title = str(book.get('title', 'Untitled'))
            author = str(book.get('author', 'Unknown'))
            genre = str(book.get('genre', 'General'))
            summary = str(book.get('summary', 'No summary provided.'))

            # Create the vectors
            summary_vec = model.encode(summary).tolist()
            # Combine all text for the general book vector
            combined_text = f"{author} {genre} {title} {summary}"
            book_vec = model.encode(combined_text).tolist()

            # Clean the book object before sending to ES
            new_book = {
                "title": title,
                "author": author,
                "genre": genre,
                "summary": summary,
                "publication_date": book.get('publication_date', '2024-01-01'),
                "publisher": book.get('publisher', 'N/A'),
                "edition": int(book.get('edition', 1)),
                "search_times": 0,
                "summary_vector": summary_vec,
                "book_vector": book_vec
            }

            operations.append({"index": {"_index": INDEX_NAME}})
            operations.append(new_book)
        
        if operations:
            client.bulk(index=INDEX_NAME, operations=operations, refresh=True)
            return jsonify({"message": "Successfully inserted into Elasticsearch"}), 200
        
        return jsonify({"message": "No valid books to insert"}), 400

    except Exception as e:
        # This will print the EXACT error in your VS Code terminal
        print("--- INSERT ERROR ---")
        traceback.print_exc() 
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500
# --- MAIN BLOCK ---

if __name__ == "__main__":
    with open("config.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    
    url = config["mongodb_url"] 
    port = config["port"] 

    atlas_client = AtlasClient(url, DB_NAME)
    app.secret_key = "CSE-512-GROUP-PROJECT-2024"

    client = Elasticsearch("http://127.0.0.1:9200")

    mappings = {
        "properties": {
            "title": {"type": "text"},
            "genre": {"type": "keyword"}, 
            "summary_vector": {"type": "dense_vector", "dims": 384},
            "ISBN_13": {"type": "keyword"},
            "publisher": {"type": "keyword"},
            "publication_date": {
                "type": "date",
                "format": "yyyy-MM-dd||yyyy-M-d||epoch_millis"
            },
            "edition": {"type": "integer"},
            "search_times": {"type": "integer"},
            "book_vector": {"type": "dense_vector", "dims": 384},
        }
    }

    # Initial Indexing logic
    try:
        idx_exists = client.indices.exists(index=INDEX_NAME)
        if not idx_exists:
            client.indices.create(index=INDEX_NAME, mappings=mappings)
            
            with open('books.json', 'r', encoding='utf-8') as f:
                books = json.load(f)
            
            print(f"I found {len(books)} books. Starting initial indexing...")
            operations = []
            for book in books:
                operations.append({"index": {"_index": INDEX_NAME}})
                
                # Logic to handle list or string for author/genre
                author = " ".join(book["author"]) if isinstance(book["author"], list) else str(book["author"])
                genre = " ".join(book["genre"]) if isinstance(book["genre"], list) else str(book["genre"])
                summary = str(book.get("summary", ""))
                title = str(book.get("title", ""))

                book["summary_vector"] = model.encode(summary).tolist()
                combined_text = f"{author} {genre} {title} {summary}"
                book["book_vector"] = model.encode(combined_text).tolist()
                
                if "search_times" not in book:
                    book["search_times"] = 0
                
                operations.append(book)

            client.bulk(index=INDEX_NAME, operations=operations, refresh=True)
            print("Successfully indexed initial books!")
    except Exception as e:
        print(f"Pre-load error: {e}")

    print(f"Starting Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)