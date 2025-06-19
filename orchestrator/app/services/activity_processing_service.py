import hashlib
import json
import re
import unicodedata
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import os
from datetime import datetime, timedelta
from pathlib import Path
import uuid

@dataclass
class ActivityRecord:
    """Record for storing activity data and embeddings."""
    activity_id: str
    name: str
    location: str
    category: str
    embedding: np.ndarray

    def to_dict(self) -> Dict:
        """Convert record to dictionary for storage."""
        return {
            'activity_id': self.activity_id,
            'name': self.name,
            'location': self.location,
            'category': self.category,
            'embedding': self.embedding.tolist()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ActivityRecord':
        """Create record from dictionary."""
        return cls(
            activity_id=data['activity_id'],
            name=data['name'],
            location=data['location'],
            category=data['category'],
            embedding=np.array(data['embedding'])
        )

class ActivityProcessingService:
    """
    Service for processing trip plan activities:
    1. Normalize activity data
    2. Use local embeddings for semantic search
    3. Deduplicate activities using vector similarity
    4. Assign consistent IDs to activities
    """
    
    def __init__(self, db_path: str = None, similarity_threshold: float = 0.85):
        """
        Initialize the service with local embedding model and FAISS index.
        
        Args:
            db_path: Path to FAISS index file (optional)
            similarity_threshold: Cosine similarity threshold for matching (0-1)
        """
        # Set up data directory
        self.data_dir = Path(os.getenv('VECTOR_DB_DIR', 'data/vector_db'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Set default db path if not provided
        if db_path is None:
            self.db_path = self.data_dir / 'activities.faiss'
        else:
            self.db_path = Path(db_path)
        
        self.similarity_threshold = similarity_threshold
        
        # Initialize local embedding model (lightweight, runs offline)
        print("Loading local embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB model
        
        # Load activity records first
        self.activities = self._load_activities()
        
        # Then initialize FAISS index
        self._init_index()
    
    def _init_index(self):
        """Initialize or load the FAISS index."""
        try:
            # Create index directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Initialize index_to_id list
            self.index_to_id = []
            
            # Load existing activities and create index
            if self.db_path.exists():
                print(f"Loading existing index from {self.db_path}")
                self.index = faiss.read_index(str(self.db_path))
                
                # Load activity records and create index_to_id mapping
                if self.db_path.with_suffix('.records').exists():
                    with open(self.db_path.with_suffix('.records'), 'rb') as f:
                        records = pickle.load(f)
                        # Sort records by id to ensure consistent order
                        sorted_records = sorted(records.items(), key=lambda x: x[0])
                        self.activities = dict(sorted_records)
                        # Create index_to_id list in same order as FAISS index
                        self.index_to_id = [record_id for record_id, _ in sorted_records]
                        
                        # Verify index size matches records
                        if self.index.ntotal != len(self.index_to_id):
                            print(f"WARNING: Index size ({self.index.ntotal}) doesn't match records count ({len(self.index_to_id)})")
                            # Rebuild index to ensure synchronization
                            self._rebuild_index()
                            
                        print(f"DEBUG: Loaded {len(self.activities)} activities")
                        for activity_id, activity in self.activities.items():
                            print(f"DEBUG: Loaded activity - id: {activity_id}, name: {activity.name}, location: {activity.location}")
            else:
                print("Creating new FAISS index")
                # Create new index
                self.index = faiss.IndexFlatL2(384)  # 384 is the embedding dimension
                self.activities = {}
                self.index_to_id = []
                
        except Exception as e:
            print(f"Error initializing index: {str(e)}")
            # Create new index as fallback
            self.index = faiss.IndexFlatL2(384)
            self.activities = {}
            self.index_to_id = []
            
    def _rebuild_index(self):
        """Rebuild the FAISS index from activities to ensure synchronization."""
        print("Rebuilding FAISS index...")
        # Create new index
        self.index = faiss.IndexFlatL2(384)
        self.index_to_id = []
        
        # Add all activities to index
        for record_id, record in self.activities.items():
            embedding = np.array(record.embedding).astype('float32').reshape(1, -1)
            self.index.add(embedding)
            self.index_to_id.append(record_id)
            print(f"DEBUG: Rebuilt index for activity - id: {record_id}, name: {record.name}")
            
        # Save rebuilt index
        faiss.write_index(self.index, str(self.db_path))
        print(f"Index rebuilt and saved to {self.db_path}")
        print(f"DEBUG: Rebuilt index size: {self.index.ntotal}, activities count: {len(self.activities)}")
    
    def _load_activities(self) -> Dict[str, ActivityRecord]:
        """Load activity records from disk."""
        activities_path = self.db_path.with_suffix('.records')
        if activities_path.exists():
            with open(activities_path, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save_activities(self):
        """Save activity records to disk."""
        activities_path = self.db_path.with_suffix('.records')
        with open(activities_path, 'wb') as f:
            pickle.dump(self.activities, f)
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison:
        - Convert to lowercase
        - Remove accents/diacritics
        - Remove extra whitespace
        - Remove special characters
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove accents/diacritics
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        
        # Remove special characters except spaces and basic punctuation
        text = re.sub(r'[^\w\s\-\.,]', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _create_activity_signature(self, name: str, location: str, category: str = "") -> str:
        """Create a normalized signature for activity comparison."""
        normalized_name = self._normalize_text(name)
        normalized_location = self._normalize_text(location)
        normalized_category = self._normalize_text(category)
        
        # Combine key fields
        signature = f"{normalized_name} | {normalized_location}"
        if normalized_category:
            signature += f" | {normalized_category}"
        
        return signature
    
    def _generate_activity_id(self, name: str, location: str, category: str = "") -> str:
        """Generate a unique ID using UUID."""
        # Generate a new UUID for each call
        unique_id = uuid.uuid4().hex[:16]  # Get first 16 chars of hex representation
        return f"activity_{unique_id}"
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding vector for text using local model."""
        return self.embedding_model.encode([text])[0]
    
    def _search_similar_activities(self, embedding: np.ndarray) -> Optional[Tuple[str, float]]:
        """
        Search for similar activities using FAISS index.
        Similarity is based on embedding vector.
        
        Returns a list of tuples (activity_id, similarity) if similarity > threshold, None otherwise.
        """
        print(f"DEBUG: Searching for similar activities with embedding: {embedding}")
        print(f"DEBUG: Current index size: {self.index.ntotal}")
        print(f"DEBUG: Current activities count: {len(self.activities)}")
        
        if self.index.ntotal > 0:
            # Search for most similar vector
            distances, indices = self.index.search(embedding.reshape(1, -1), 5)
            print(f"DEBUG: FAISS search results - distances: {distances}, indices: {indices}")
            
            # Convert L2 distance to similarity score (0 to 1)
            # L2 distance of 0 means perfect match, higher means more different
            max_distance = 2.0  # Maximum possible L2 distance for normalized vectors
            similarities = 1.0 - (distances[0] / max_distance)
            print(f"DEBUG: Calculated similarity scores: {similarities}")
            
            similar_activities = []
            for i in range(len(indices[0])):
                if indices[0][i] != -1 and similarities[i] >= self.similarity_threshold:
                    try:
                        # Get activity ID from index mapping
                        activity_id = self.index_to_id[indices[0][i]]
                        similar_activities.append((activity_id, similarities[i]))
                    except IndexError as e:
                        print(f"ERROR: Index mismatch - index: {indices[0][i]}, index_to_id length: {len(self.index_to_id)}")
                        print(f"ERROR: index_to_id: {self.index_to_id}")
                        raise
            
            return similar_activities
        
        print("DEBUG: No similar activity found")
        return None
    
    def _store_activity(self, activity_record: ActivityRecord):
        """Store new activity in FAISS index."""
        try:
            # Add embedding to FAISS index
            embedding = activity_record.embedding.astype('float32').reshape(1, -1)
            self.index.add(embedding)
            
            # Store activity record and update index mapping
            self.activities[activity_record.activity_id] = activity_record
            self.index_to_id.append(activity_record.activity_id)
            
            # Save to disk
            faiss.write_index(self.index, str(self.db_path))
            self._save_activities()
            
            print(f"Stored new activity: {activity_record.activity_id}")
            print(f"DEBUG: Activity details - name: {activity_record.name}, location: {activity_record.location}, category: {activity_record.category}")
            print(f"DEBUG: Current index size: {self.index.ntotal}, activities count: {len(self.activities)}")
        except Exception as e:
            print(f"ERROR: Failed to store activity: {str(e)}")
            raise
    
    def process_activity(self, activity_data: Dict) -> Dict:
        """Process a single activity and return it with an activityId."""
        try:
            # Create activity signature
            name = activity_data.get('name', '').lower()
            location = activity_data.get('location', '').lower()
            category = activity_data.get('category', '').lower()
            signature = f"{name} | {location} | {category}"
            print(f"DEBUG: Created signature: {signature}")
            
            # Generate embedding for the activity
            embedding = self._get_embedding(signature)
            print(f"DEBUG: Generated embedding of shape: {embedding.shape}")
            
            # Search for similar activities
            print(f"DEBUG: Searching for similar activities with signature: {signature}")
            print(f"DEBUG: Current index size: {self.index.ntotal}")
            print(f"DEBUG: Current activities count: {len(self.activities)}")
            
            similar_activities = self._search_similar_activities(embedding)
            
            if similar_activities:
                # Get the most similar activity
                similar_id, similarity = similar_activities[0]
                similar_activity = self.activities[similar_id]
                
                # Check if activities are similar enough to reuse ID
                if similarity >= self.similarity_threshold:
                    print(f"DEBUG: Found similar activity: {similar_id} with similarity {similarity}")
                    print(f"DEBUG: Similar activity details - name: {similar_activity.name}, location: {similar_activity.location}")
                    print(f"DEBUG: Current activity details - name: {name}, location: {location}")
                    print(f"DEBUG: Using similarity threshold: {self.similarity_threshold}")
                    
                    # Update the existing activity record with new data
                    updated_record = ActivityRecord(
                        activity_id=similar_id,
                        name=name,
                        location=location,
                        category=category,
                        embedding=embedding
                    )
                    
                    # Update the vector database
                    self.activities[similar_id] = updated_record
                    self._rebuild_index()  # Rebuild index to reflect changes
                    
                    # Return the new activity data with the reused ID
                    return {
                        'name': activity_data.get('name'),
                        'description': activity_data.get('description', ''),
                        'location': activity_data.get('location'),
                        'startTime': activity_data.get('startTime'),
                        'endTime': activity_data.get('endTime'),
                        'participants': activity_data.get('participants'),
                        'category': activity_data.get('category'),
                        'activityId': similar_id
                    }
            
            # If no similar activity found or similarity is too low, create new activity
            activity_id = self._generate_activity_id(name, location, category)
            print(f"DEBUG: Generated new activity ID: {activity_id}")
            
            # Create and store new activity record
            activity_record = ActivityRecord(
                activity_id=activity_id,
                name=name,
                location=location,
                category=category,
                embedding=embedding
            )
            
            self._store_activity(activity_record)
            print(f"Created new activity: {activity_id}")
            
            return {**activity_data, 'activityId': activity_id}
            
        except Exception as e:
            print(f"Error processing activity: {str(e)}")
            # Generate a fallback ID if processing fails
            fallback_id = f"activity_{uuid.uuid4().hex[:16]}"
            return {**activity_data, 'activityId': fallback_id}
    
    def process_trip_plan(self, trip_plan_json: Dict) -> Dict:
        """
        Process entire trip plan JSON, adding activityId to all activities.
        
        Args:
            trip_plan_json: Raw trip plan from LLM
            
        Returns:
            Updated trip plan with activityId fields
        """
        print("Processing trip plan activities...")
        print(f"DEBUG: Number of spans: {len(trip_plan_json.get('spans', []))}")
        processed_plan = trip_plan_json.copy()
        
        # Process activities in each span
        for span_idx, span in enumerate(processed_plan.get('spans', [])):
            print(f"DEBUG: Processing span {span_idx + 1}")
            processed_activities = []
            
            for activity_idx, activity in enumerate(span.get('activities', [])):
                print(f"DEBUG: Processing activity {activity_idx + 1} in span {span_idx + 1}")
                try:
                    processed_activity = self.process_activity(activity)
                    processed_activities.append(processed_activity)
                except Exception as e:
                    print(f"ERROR: Failed to process activity {activity_idx + 1} in span {span_idx + 1}")
                    print(f"ERROR: Activity data: {activity}")
                    raise
            
            span['activities'] = processed_activities
        
        total_activities = sum(len(span.get('activities', [])) for span in processed_plan.get('spans', []))
        print(f"Processed {total_activities} activities")
        return processed_plan
    
    def get_activity_stats(self) -> Dict:
        """Get statistics about stored activities."""
        category_counts = {}
        for activity in self.activities.values():
            category_counts[activity.category] = category_counts.get(activity.category, 0) + 1
        
        return {
            'total_activities': len(self.activities),
            'categories': category_counts,
            'similarity_threshold': self.similarity_threshold
        }
    
    def cleanup_old_activities(self, days_old: int = 30):
        """Remove activities not used in the last N days."""
        # Note: FAISS doesn't support deletion, so we'll need to rebuild the index
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Create new index
        embedding_dim = 384
        new_index = faiss.IndexFlatIP(embedding_dim)
        
        # Keep only recent activities
        new_activities = {}
        for activity_id, activity in self.activities.items():
            if activity.last_used >= cutoff_date:
                new_activities[activity_id] = activity
                embedding = activity.embedding.astype('float32').reshape(1, -1)
                new_index.add(embedding)
        
        # Update index and activities
        self.index = new_index
        self.activities = new_activities
        
        # Save to disk
        faiss.write_index(self.index, str(self.db_path))
        self._save_activities()
        
        deleted_count = len(self.activities) - len(new_activities)
        print(f"Cleaned up {deleted_count} old activities")
        return deleted_count 