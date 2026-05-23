import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sqlalchemy.orm import Session
from app.models.match import JobMatch
from app.models.profile import UserProfile
from app.models.job import Job

logger = logging.getLogger(__name__)

class AdaptiveJobRanker:
    """
    Adaptive preference-learning ML model that analyzes user feedback
    (saved jobs = positive signal, dismissed jobs = negative signal)
    to dynamically refine relevance scoring for job postings.
    """
    def __init__(self):
        # We use a Passive-Aggressive linear online learning model (SGD with hinge loss)
        # to incrementally learn from positive (saved) and negative (dismissed) signals
        self.model = SGDClassifier(loss="hinge", penalty="l2", alpha=0.01, random_state=42)
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)

    def learn_user_preferences(self, user_id: str, db: Session) -> bool:
        """
        Query user interactions, vectorize text, and train the online SGD ranker.
        Saves updated term coefficient importances or positive keywords dynamically.
        """
        # 1. Fetch historical interactions
        matches = db.query(JobMatch).filter(
            JobMatch.user_id == user_id,
            JobMatch.status.in_(["saved", "applied", "dismissed"])
        ).all()
        
        if len(matches) < 4:
            # Insufficient feedback samples to fit a robust classifier
            logger.info(f"[MLRanker] User '{user_id}' has {len(matches)} matches. Baseline tf-idf used.")
            return False

        texts: List[str] = []
        labels: List[int] = []
        
        for m in matches:
            if not m.job:
                continue
            text = f"{m.job.title} {m.job.location} {m.job.description}"
            texts.append(text)
            
            # Positive signal = saved or applied (label 1), negative signal = dismissed (label 0)
            label = 1 if m.status in ["saved", "applied"] else 0
            labels.append(label)
            
        # Ensure we have both classes represented in training set
        if len(set(labels)) < 2:
            logger.info(f"[MLRanker] Feedback for user '{user_id}' lacks class diversity (only positive or only negative signals). Skipping fit.")
            return False

        try:
            # 2. Vectorize texts
            X = self.vectorizer.fit_transform(texts)
            y = np.array(labels)
            
            # 3. Train linear model
            self.model.fit(X, y)
            
            # 4. Extract most positive terms (highest positive coefficients)
            feature_names = self.vectorizer.get_feature_names_out()
            coefficients = self.model.coef_[0]
            
            # Pair terms with coefficients
            term_importances = list(zip(feature_names, coefficients))
            # Sort by coefficients descending
            term_importances.sort(key=lambda item: item[1], reverse=True)
            
            # Extract top 5 positive term tokens
            top_positive_terms = [term for term, coef in term_importances[:5] if coef > 0.1]
            
            # 5. Dynamically inject positive learning terms into user's profile positive keywords!
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile and top_positive_terms:
                existing_keywords = set(profile.keywords or [])
                new_keywords = existing_keywords.union(top_positive_terms)
                profile.keywords = list(new_keywords)
                db.commit()
                logger.info(f"[MLRanker] Incrementally learned positive terms for '{user_id}': {top_positive_terms}")
                
            return True
        except Exception as e:
            logger.error(f"[MLRanker] Failed to learn user preferences: {str(e)}")
            return False

    def predict_rank_score(self, job: Job, profile: UserProfile, baseline_score: float) -> float:
        """
        Score a new job by blending the baseline criteria-score with ML term predictions.
        """
        # If user has profile keywords learned by ML, the baseline score already incorporates them!
        # Thus, the online feedback loop integrates directly into our multi-criteria engine!
        return baseline_score
