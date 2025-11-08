import os
import pandas as pd
import uuid
import chromadb

class portfolio:
    def __init__(self, file_path=None, collection_name="portfolio", data=None):
        
        if data is not None:
            self.data = data
        elif file_path:
            base_dir = os.path.dirname(__file__)
            abs_path = os.path.join(base_dir, file_path)
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"{abs_path} not found. Please create it with your portfolio data.")
            self.data = pd.read_csv(abs_path)
        else:
            raise ValueError("Must provide either a 'data' DataFrame or a 'file_path'.")
            
        self.client = chromadb.PersistentClient("vectorstore")
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def load_portfolio(self):
        if not self.collection.count():
            for _, row in self.data.iterrows():
                self.collection.add(
                    documents=[row["Techstack"]],
                    metadatas={"Links": row["Links"]},
                    ids=[str(uuid.uuid4())]
                )

    def query_links(self, skills, n_results=2):
        if not skills:
            return []
        results = self.collection.query(query_texts=skills, n_results=n_results)
        links = []
        for metadata_list in results.get("metadatas", []):
            for meta in metadata_list:
                if "Links" in meta:
                    links.append(meta["Links"])
        return links