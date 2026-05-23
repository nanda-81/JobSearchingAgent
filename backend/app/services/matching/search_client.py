import logging
from elasticsearch import Elasticsearch
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.config import settings
from app.models.job import Job
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class JobSearchClient:
    def __init__(self):
        self.es_url = settings.ELASTICSEARCH_URL
        self.index_name = "pjsap_jobs"
        self.es: Optional[Elasticsearch] = None
        self._connect()

    def _connect(self):
        """Establish connection to Elasticsearch node and create indexes if absent."""
        try:
            self.es = Elasticsearch([self.es_url], retry_on_timeout=True, max_retries=3, timeout=3)
            # Test connection
            if self.es.ping():
                logger.info(f"[Elasticsearch] Connected successfully to node at {self.es_url}")
                # Initialize index if missing
                if not self.es.indices.exists(index=self.index_name):
                    self.es.indices.create(
                        index=self.index_name,
                        body={
                            "mappings": {
                                "properties": {
                                    "title": {"type": "text", "analyzer": "english"},
                                    "company": {"type": "keyword"},
                                    "location": {"type": "text"},
                                    "description": {"type": "text", "analyzer": "english"},
                                    "source": {"type": "keyword"},
                                    "is_remote": {"type": "boolean"},
                                    "posted_at": {"type": "date"}
                                }
                            }
                        }
                    )
                    logger.info(f"[Elasticsearch] Created index '{self.index_name}' successfully.")
            else:
                logger.warning(f"[Elasticsearch] Ping failed to {self.es_url}. Falling back to PostgreSQL for queries.")
                self.es = None
        except Exception as e:
            logger.warning(f"[Elasticsearch] Failed to initialize connection: {str(e)}. Operating in database-fallback mode.")
            self.es = None

    def index_job(self, job: Job) -> bool:
        """Index a job posting into Elasticsearch (graceful fallback if disconnected)."""
        if not self.es:
            return False
        try:
            body = {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description,
                "source": job.source,
                "is_remote": job.is_remote,
                "posted_at": job.posted_at.isoformat() if job.posted_at else None
            }
            self.es.index(index=self.index_name, id=str(job.id), body=body)
            return True
        except Exception as e:
            logger.warning(f"[Elasticsearch] Failed to index job '{job.id}': {str(e)}")
            return False

    def search_jobs(self, query: str, db: Session, limit: int = 20, offset: int = 0) -> List[Job]:
        """
        Search for jobs matching a query string.
        Utilizes Elasticsearch if available; falls back to standard PostgreSQL SQL filters on failure.
        """
        # Attempt Elasticsearch query if connected
        if self.es and query:
            try:
                search_body = {
                    "from": offset,
                    "size": limit,
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "description^1", "location^2", "company^2"],
                            "fuzziness": "AUTO"
                        }
                    }
                }
                res = self.es.search(index=self.index_name, body=search_body)
                hits = res["hits"]["hits"]
                
                # Extract UUIDs and query them from DB to return complete Job models
                job_ids = [hit["_id"] for hit in hits]
                if not job_ids:
                    return []
                    
                # Query PostgreSQL to maintain strict relational state integrity
                db_jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()
                # Maintain the sorting rank returned by Elasticsearch hits
                id_map = {str(j.id): j for j in db_jobs}
                return [id_map[jid] for jid in job_ids if jid in id_map]
                
            except Exception as e:
                logger.warning(f"[Elasticsearch] Search execution failed: {str(e)}. Falling back to PostgreSQL query.")
                # Fall through to PostgreSQL backup
                
        # Graceful Fallback: Execute standard SQL ILIKE pattern filtering
        logger.info(f"[SearchFallback] Executing PostgreSQL ILIKE search for query: '{query}'")
        if not query:
            return db.query(Job).order_by(Job.posted_at.desc()).offset(offset).limit(limit).all()
            
        search_pattern = f"%{query}%"
        return db.query(Job).filter(
            or_(
                Job.title.ilike(search_pattern),
                Job.company.ilike(search_pattern),
                Job.location.ilike(search_pattern),
                Job.description.ilike(search_pattern)
            )
        ).order_by(Job.posted_at.desc()).offset(offset).limit(limit).all()

    def delete_job(self, job_id: str) -> bool:
        """Remove a job from Elasticsearch index."""
        if not self.es:
            return False
        try:
            if self.es.exists(index=self.index_name, id=job_id):
                self.es.delete(index=self.index_name, id=job_id)
                return True
            return False
        except Exception as e:
            logger.warning(f"[Elasticsearch] Failed to delete job '{job_id}': {str(e)}")
            return False
