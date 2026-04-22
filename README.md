# Campus Library Resource Search Engine 

## 🚀 Project Overview
The **Campus Library Resource Search Engine** is a unified search platform and resource catalog designed to aggregate books, journals, and digital resources from multiple publishers into a single, high-performance interface. This project eliminates the need for students to search across fragmented platforms separately.

## 🛠️ Technical Stack
* **Frontend:** React (Port 5173)
* **Backend API:** Flask (Port 5000)
* **Primary Database:** MongoDB
* **Search Engine:** Elasticsearch 8.x (Dockerized)
* **Drivers:** `pymongo`, `elasticsearch < 9.0.0`

## 🏗️ System Architecture
The system follows a multi-layer architecture to ensure decoupling and high performance:

1.  **Client Layer:** React-based Student Search UI and Admin Management Panel.
2.  **Service Layer:** Flask RESTful API handling business logic and data orchestration.
3.  **Data & Search Layer:** MongoDB for persistent storage and Elasticsearch for full-text indexing.

## ✨ Key Features
### 🔍 Student Search Interface
* **Global Keyword Search:** Free-text entry for titles, authors, and summaries.
* **Advanced Matching:** Supports N-gram tokenization for partial matches and fuzzy matching for typo tolerance.
* **Semantic Retrieval:** Vector-based search using cosine similarity to find meaning-based results.
* **Relevance Ranking:** Utilizes BM25 scoring to ensure the most relevant results appear first.
* **Discovery:** A 'Popular Books' section driven by search frequency metadata.

### 🛠️ Administrative Management
* **Full CRUD:** Add library resources via a secure panel(admin).
* **Metadata Flexibility:** Support for  author structures (String or Array formats) and provides Metadata.
