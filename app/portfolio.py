import os
import pandas as pd
import uuid
import chromadb

class Portfolio:
    """
    Manages vector storage and semantic retrieval for candidate portfolio items and project links.
    """
    def __init__(self, file_path=None, collection_name="user_portfolio", data=None, persist_directory="vectorstore"):
        if data is not None:
            if isinstance(data, pd.DataFrame):
                self.data = data.copy()
            elif isinstance(data, list):
                self.data = pd.DataFrame(data)
            else:
                self.data = pd.DataFrame(data)
        elif file_path:
            base_dir = os.path.dirname(__file__)
            abs_path = os.path.join(base_dir, file_path) if not os.path.isabs(file_path) else file_path
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"{abs_path} not found. Please provide valid portfolio data.")
            self.data = pd.read_csv(abs_path)
        else:
            self.data = pd.DataFrame(columns=["Techstack", "Links"])
            
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def load_portfolio(self, clear_existing: bool = True):
        """
        Loads the candidate portfolio data into ChromaDB.
        Clears existing items if clear_existing is True to ensure freshness across uploads.
        """
        if self.data is None or self.data.empty:
            return

        if clear_existing and self.collection.count() > 0:
            try:
                # Delete existing collection and recreate to clear stale data
                self.client.delete_collection(name=self.collection_name)
                self.collection = self.client.get_or_create_collection(name=self.collection_name)
            except Exception:
                pass

        documents = []
        metadatas = []
        ids = []

        for _, row in self.data.iterrows():
            techstack = str(row.get("Techstack", "")).strip()
            links = str(row.get("Links", "")).strip()
            if techstack and links:
                documents.append(techstack)
                metadatas.append({"Links": links, "Techstack": techstack})
                ids.append(str(uuid.uuid4()))

        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def query_links(self, skills, n_results: int = 3):
        """
        Queries ChromaDB for links matching the job's requested skills.
        """
        if not skills or self.collection.count() == 0:
            # If no embeddings or skills, return all available links in the dataset up to n_results
            if self.data is not None and not self.data.empty and "Links" in self.data.columns:
                return [l for l in self.data["Links"].dropna().unique() if str(l).strip()][:n_results]
            return []

        if isinstance(skills, list):
            query_texts = [str(s).strip() for s in skills if str(s).strip()]
        else:
            query_texts = [str(skills).strip()]

        if not query_texts:
            return []

        # Chroma query limit cannot exceed collection count
        count = self.collection.count()
        actual_n = min(n_results, count)

        try:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=actual_n
            )
            links = []
            seen = set()
            for metadata_list in results.get("metadatas", []):
                for meta in metadata_list:
                    if meta and "Links" in meta:
                        link_val = meta["Links"].strip()
                        if link_val and link_val not in seen:
                            seen.add(link_val)
                            links.append(link_val)
            return links
        except Exception:
            # Fallback to dataset links
            if self.data is not None and not self.data.empty and "Links" in self.data.columns:
                return [l for l in self.data["Links"].dropna().unique() if str(l).strip()][:n_results]
            return []

# Backwards compatibility alias
portfolio = Portfolio