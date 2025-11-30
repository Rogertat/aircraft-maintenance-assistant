from .retriever import build_index
from .config import DATASET_DIR, INDEX_DIR

def main():
    print(f"Building FAISS index from: {DATASET_DIR}")
    # Ensure the index directory exists
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    stats = build_index()
    print(f"Index built: {stats}")

if __name__ == "__main__":
    main()
