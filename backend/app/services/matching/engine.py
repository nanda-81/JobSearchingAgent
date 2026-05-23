import logging
import re
from typing import Tuple, Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.job import Job
from app.models.profile import UserProfile

logger = logging.getLogger(__name__)

def calculate_match_score(job: Job, profile: UserProfile) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate a precise, multi-factor job match score from 0.0 to 1.0.
    Returns (match_score, match_details).
    """
    details = {
        "title_match": 0.0,
        "location_match": 0.0,
        "salary_match": 0.0,
        "experience_match": 0.0,
        "semantic_match": 0.0,
        "matched_keywords": [],
        "reasons": []
    }

    title_desc_lower = f"{job.title.lower()} {job.description.lower()}"
    
    # 1. STRICT BLOCK: Excluded Keywords (Force 0.0 score immediately if found)
    excluded_keywords = profile.excluded_keywords or []
    for ext_kw in excluded_keywords:
        if ext_kw.lower().strip() and ext_kw.lower().strip() in title_desc_lower:
            details["reasons"].append(f"Blocked: Excluded keyword '{ext_kw}' discovered.")
            return 0.0, {"blocked": True, "reason": f"Contains excluded keyword: {ext_kw}"}

    score = 0.0

    # 2. TITLE MATCHING (Weight: 0.35)
    title_weight = 0.35
    title_matched = False
    target_titles = profile.target_titles or []
    if target_titles:
        for target_title in target_titles:
            # Check if target title exists as a word or substring in job title
            if target_title.lower().strip() and target_title.lower().strip() in job.title.lower():
                title_matched = True
                details["title_match"] = title_weight
                details["reasons"].append(f"Matched target title: '{target_title}'")
                break
        if not title_matched:
            details["reasons"].append("Did not match target job titles.")
    else:
        # Default full score if user hasn't configured target titles
        details["title_match"] = title_weight
        title_matched = True
        
    score += details["title_match"]

    # 3. LOCATION / REMOTE MATCHING (Weight: 0.15)
    location_weight = 0.15
    location_matched = False
    target_locations = profile.target_locations or []
    
    # If job is remote and profile wants Remote
    profile_locations_lower = [loc.lower().strip() for loc in target_locations if loc]
    if job.is_remote and "remote" in profile_locations_lower:
        location_matched = True
        details["location_match"] = location_weight
        details["reasons"].append("Matched remote work preference.")
    elif target_locations:
        for loc in profile_locations_lower:
            if loc in job.location.lower():
                location_matched = True
                details["location_match"] = location_weight
                details["reasons"].append(f"Matched geographical location preference: '{loc}'")
                break
        if not location_matched:
            details["reasons"].append(f"Location mismatch (Job in '{job.location}').")
    else:
        details["location_match"] = location_weight
        location_matched = True
        
    score += details["location_match"]

    # 4. SALARY MATCHING (Weight: 0.15)
    salary_weight = 0.15
    if profile.salary_min is not None:
        if job.salary_max is not None:
            if job.salary_max >= profile.salary_min:
                details["salary_match"] = salary_weight
                details["reasons"].append(f"Salary is competitive (Max {job.salary_currency}{job.salary_max} >= Min {job.salary_currency}{profile.salary_min}).")
            else:
                details["reasons"].append(f"Salary too low (Max {job.salary_currency}{job.salary_max} < Min {job.salary_currency}{profile.salary_min}).")
        else:
            # Salary undisclosed by employer, award default 50% partial credit
            details["salary_match"] = salary_weight * 0.5
            details["reasons"].append("Salary undisclosed (awarded default baseline credit).")
    else:
        # User doesn't have a salary restriction
        details["salary_match"] = salary_weight
        
    score += details["salary_match"]

    # 5. EXPERIENCE LEVEL ALIGNMENT (Weight: 0.10)
    exp_weight = 0.10
    exp_profile = (profile.experience_level or "mid").lower().strip()
    
    # Simple semantic heuristics for experience levels
    exp_indicators = {
        "junior": ["junior", "entry level", "associate", "intern", "grad"],
        "mid": ["mid", "intermediate", "2-5 years", "3+ years"],
        "senior": ["senior", "sr.", "5+ years", "8+ years", "architect"],
        "lead": ["lead", "principal", "manager", "director", "staff"]
    }
    
    # Check if job title contains matching descriptors
    job_title_lower = job.title.lower()
    matched_job_level = "mid"  # default baseline
    for level, keywords in exp_indicators.items():
        if any(kw in job_title_lower for kw in keywords):
            matched_job_level = level
            break
            
    if exp_profile == matched_job_level:
        details["experience_match"] = exp_weight
        details["reasons"].append(f"Experience level matched: '{exp_profile}'")
    else:
        # Partial credit if they are close
        if (exp_profile == "senior" and matched_job_level == "lead") or (exp_profile == "lead" and matched_job_level == "senior"):
            details["experience_match"] = exp_weight * 0.75
            details["reasons"].append(f"Close experience level matching ('{exp_profile}' vs '{matched_job_level}').")
        else:
            details["reasons"].append(f"Experience level mismatch ('{exp_profile}' vs '{matched_job_level}').")
            
    score += details["experience_match"]

    # 6. SEMANTIC & KEYWORD TF-IDF SIMILARITY (Weight: 0.25)
    semantic_weight = 0.25
    keywords = profile.keywords or []
    
    # Construct search text for profile preferences
    profile_terms = []
    if target_titles:
        profile_terms.extend(target_titles)
    if target_locations:
        profile_terms.extend(target_locations)
    if keywords:
        profile_terms.extend(keywords)
        
    profile_text = " ".join(profile_terms)
    job_text = f"{job.title} {job.location} {job.description}"
    
    # Check positive keywords matches
    for kw in keywords:
        if kw.lower().strip() and kw.lower().strip() in title_desc_lower:
            details["matched_keywords"].append(kw)
            
    if details["matched_keywords"]:
        details["reasons"].append(f"Discovered matching keywords: {', '.join(details['matched_keywords'])}")

    if profile_text.strip():
        try:
            # Compute TF-IDF Cosine Similarity
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform([profile_text, job_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Bound and scale
            similarity_bounded = max(0.0, min(1.0, float(similarity)))
            details["semantic_match"] = similarity_bounded * semantic_weight
            details["reasons"].append(f"Semantic similarity match: {int(similarity_bounded * 100)}%")
        except Exception as e:
            # Fail gracefully, award average baseline based on direct keyword matching
            logger.warning(f"Could not calculate TF-IDF similarity: {str(e)}")
            if keywords:
                ratio = len(details["matched_keywords"]) / len(keywords)
                details["semantic_match"] = ratio * semantic_weight
            else:
                details["semantic_match"] = semantic_weight * 0.5
    else:
        details["semantic_match"] = semantic_weight
        
    score += details["semantic_match"]

    # Clamp total score between 0.0 and 1.0
    final_score = max(0.0, min(1.0, float(score)))
    return final_score, details
