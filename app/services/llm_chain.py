"""
CareerLens LLM Orchestration, Skill Matching, and Outreach Generation Engine.
Upgraded with structured requirement extraction across 5 categories, exact passage grounding,
technical skill normalization, conflicting evidence detection, and unsupported LLM claim defense.
"""
import os
import re
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from urllib.parse import urlparse

load_dotenv()

SUPPORTED_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "groq/compound-mini",
    "groq/compound",
    "qwen/qwen3.6-27b"
]

# Exact canonical aliases (true equivalents/shorthands)
CANONICAL_ALIASES = {
    "python": ["python", "python3", "py"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "golang": ["golang", "go"],
    "c++": ["c++", "cpp"],
    "c#": ["c#", "csharp", ".net", "dotnet"],
    "kubernetes": ["kubernetes", "k8s"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "mongodb": ["mongodb", "mongo"],
    "react": ["react", "reactjs", "react.js"],
    "node": ["node", "nodejs", "node.js"],
    "vue": ["vue", "vuejs", "vue.js"],
    "angular": ["angular", "angularjs"],
    "fastapi": ["fastapi"],
    "django": ["django", "django rest framework", "drf"],
    "flask": ["flask"],
    "docker": ["docker", "docker-compose", "containerization"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "ci/cd": ["ci/cd", "ci cd", "continuous integration", "continuous deployment"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "nlp": ["nlp", "natural language processing"],
    "computer vision": ["computer vision", "cv"],
    "sql": ["sql", "rdbms", "relational database"],
    "nosql": ["nosql"],
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow", "tf"],
}

# Explicit non-equivalent tool pairs: Tool A does NOT imply knowledge of Tool B
NON_EQUIVALENT_PAIRS = {
    "pytorch": ["tensorflow", "keras"],
    "tensorflow": ["pytorch", "torch", "keras"],
    "aws": ["azure", "gcp"],
    "azure": ["aws", "gcp"],
    "gcp": ["aws", "azure"],
    "python": ["fastapi", "django", "flask"],
    "fastapi": ["python", "django", "flask"],
    "django": ["python", "fastapi", "flask"],
    "flask": ["python", "fastapi", "django"],
    "java": ["javascript"],
    "javascript": ["java"],
    "sql": ["nosql", "mongodb", "cassandra"],
    "nosql": ["sql", "postgresql", "mysql"],
}

def format_tool_display(tool_name: str) -> str:
    display_map = {
        "pytorch": "PyTorch",
        "tensorflow": "TensorFlow",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "python": "Python",
        "sql": "SQL",
        "nosql": "NoSQL",
        "mongodb": "MongoDB",
        "postgresql": "PostgreSQL",
        "javascript": "JavaScript",
        "java": "Java",
        "keras": "Keras",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
    }
    return display_map.get(tool_name.lower(), tool_name.capitalize())

# Related ecosystem families (adjacent tools: candidate knowing tool A does NOT automatically mean they know tool B)
RELATED_ECOSYSTEMS = {
    "Python": {
        "parent": "python",
        "tools": ["python", "fastapi", "django", "flask", "pandas", "numpy", "scipy", "scikit-learn", "pytorch", "tensorflow", "celery", "sqlalchemy"]
    },
    "JavaScript / Web": {
        "parent": "javascript",
        "tools": ["react", "vue", "angular", "node", "express", "nextjs", "next.js", "typescript", "svelte", "redux"]
    },
    "Cloud & DevOps": {
        "parent": "cloud",
        "tools": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible", "jenkins", "github actions", "linux"]
    },
    "Machine Learning & AI": {
        "parent": "machine learning",
        "tools": ["pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "nlp", "computer vision", "opencv", "langchain", "huggingface", "llm"]
    },
    "Databases": {
        "parent": "database",
        "tools": ["postgresql", "mysql", "sqlite", "mongodb", "redis", "cassandra", "dynamodb", "elasticsearch"]
    }
}

def is_valid_url(url: str) -> bool:
    """
    Validates whether a URL is a syntactically valid public web link,
    and strictly rejects placeholder/hallucinated domains and patterns.
    """
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    
    lower_u = u.lower()
    placeholders = [
        "github.com/candidate",
        "github.com/username",
        "github.com/your-username",
        "github.com/profile",
        "example.com",
        "placeholder",
        "project-name",
        "your-portfolio",
        "linkedin.com/in/candidate",
        "mysite.com",
        "domain.com",
        "<url>",
        "[url]",
        "none"
    ]
    if any(p in lower_u for p in placeholders):
        return False
        
    try:
        parsed = urlparse(u)
        return bool(parsed.netloc and "." in parsed.netloc and len(parsed.netloc) >= 4)
    except Exception:
        return False

def sanitize_extracted_portfolio(items: list[dict]) -> list[dict]:
    """
    Validates candidate portfolio items extracted by LLM:
    - Preserves genuine verified URLs.
    - Preserves projects that do NOT have a repository link, keeping Links as '' without inventing one.
    - Strips fabricated or placeholder URLs.
    """
    clean_items = []
    if not isinstance(items, list):
        return clean_items

    for item in items:
        if not isinstance(item, dict):
            continue
        tech = str(item.get("Techstack", "")).strip()
        link = str(item.get("Links", "")).strip()
        if not tech and not link:
            continue
        valid_link = link if is_valid_url(link) else ""
        clean_items.append({
            "Techstack": tech,
            "Links": valid_link
        })
    return clean_items

def skill_match_regex(term: str) -> re.Pattern:
    """
    Constructs a boundary-safe regex pattern for technical skill terms.
    Correctly handles terms with punctuation like 'c++', 'c#', '.net', 'node.js', and 'ci/cd'.
    """
    escaped = re.escape(term.strip())
    prefix = r'(?<![a-zA-Z0-9_])'
    suffix = r'(?![a-zA-Z0-9_+#])' if term[-1] in ('+', '#') else r'(?![a-zA-Z0-9_])'
    return re.compile(f"{prefix}{escaped}{suffix}", re.IGNORECASE)

def extract_exact_cv_passage(term: str, cv_text: str) -> str:
    """
    Extracts the most complete, readable exact sentence or clause from cv_text containing the term.
    """
    if not term or not cv_text:
        return ""
    pat = skill_match_regex(term)
    sentences = re.split(r'[\r\n]+|(?<=[.!?])\s+', cv_text)
    for s in sentences:
        if pat.search(s):
            clean_s = s.strip()
            if clean_s:
                return clean_s[:240]

    m = pat.search(cv_text)
    if m:
        start = max(0, m.start() - 40)
        end = min(len(cv_text), m.end() + 100)
        window = cv_text[start:end].replace('\n', ' ').strip()
        return f"...{window}..."
    return ""

def _determine_category(req: str, imp: str = "") -> str:
    req_l = req.lower()
    imp_l = imp.lower()
    if "irrelevant" in imp_l or "noise" in imp_l:
        return "Irrelevant/Noise"
    if any(k in req_l for k in ["degree", "bachelor", "master", "phd", "education", "b.s", "m.s", "b.sc", "m.sc"]) or "education" in imp_l or "qualif" in imp_l:
        return "Educational Qualification"
    if any(k in req_l for k in ["year", "years", "experience", "senior", "production", "lead"]) or "experience" in imp_l:
        return "Experience Requirement"
    if any(k in req_l for k in ["communication", "teamwork", "collaborat", "interpersonal", "leadership", "mentoring", "problem solving"]) or "soft" in imp_l:
        return "Soft Skill"
    if "pref" in imp_l or "nice" in imp_l or "bonus" in imp_l:
        return "Preferred Technical Skill"
    return "Critical Technical Skill"

def _determine_importance(category: str) -> str:
    cat_l = category.lower()
    if "noise" in cat_l or "irrelevant" in cat_l:
        return "Irrelevant/Noise"
    if "pref" in cat_l:
        return "Preferred requirement"
    if "soft" in cat_l:
        return "Soft skill"
    return "Critical requirement"

def evaluate_requirement(
    requirement: str,
    cv_text: str,
    portfolio_items: list[dict] | None = None,
    category: str = "Critical Technical Skill",
    candidate_profile: dict | None = None
) -> dict:
    """
    Rigorous evidence-based evaluation of a single requirement against candidate CV and portfolio.
    Enforces:
    - Zero unsupported claims.
    - Technical skill normalization (PyTorch != TensorFlow, AWS != Azure, Python != FastAPI).
    - Conflicting evidence detection (e.g. 'no experience in X', 'basic knowledge').
    - Empty CV safety.
    Returns:
    {
        "requirement": str,
        "category": str,
        "importance": str,
        "status": "MATCHED" | "PARTIALLY MATCHED" | "MISSING" | "NOT RELEVANT",
        "supporting_evidence": str (exact passage or ""),
        "candidate_evidence": str,
        "explanation": str,
        "confidence": "High" | "Medium" | "Low",
        "uncertainty": float
    }
    """
    req_clean = requirement.strip()
    category = _determine_category(req_clean, category)
    importance = _determine_importance(category)

    # 1. Empty CV Check
    if not req_clean or not cv_text or not cv_text.strip():
        return {
            "requirement": req_clean or "Requirement",
            "category": category,
            "importance": importance,
            "status": "MISSING",
            "supporting_evidence": "",
            "candidate_evidence": "Candidate CV is empty. No verifiable evidence available.",
            "explanation": "No evidence found in candidate profile or CV.",
            "confidence": "High",
            "uncertainty": 0.05
        }

    req_lower = req_clean.lower()

    # 2. Conflicting Evidence Detection
    # If candidate CV explicitly states "no experience with X", "unfamiliar with X", or "basic knowledge"
    escaped_req = re.escape(req_clean)
    no_exp_pat = re.compile(
        rf'\b(?:no|little|lack(?:ing)?|without|zero|not\s+any)\s+(?:prior\s+|hands-on\s+)?experience\s+(?:in|with)\s+{escaped_req}\b|\b(?:not\s+familiar|unfamiliar)\s+with\s+{escaped_req}\b|\bno\s+production\s+experience\s+(?:in|with)\s+{escaped_req}\b',
        re.IGNORECASE
    )
    m_no_exp = no_exp_pat.search(cv_text)
    if m_no_exp:
        conflict_s = extract_exact_cv_passage(req_clean, cv_text)
        return {
            "requirement": req_clean,
            "category": category,
            "importance": importance,
            "status": "MISSING",
            "supporting_evidence": conflict_s,
            "candidate_evidence": conflict_s,
            "explanation": f"Conflicting evidence in CV: Candidate explicitly notes limited or no experience with '{req_clean}' ('{conflict_s[:120]}').",
            "confidence": "High",
            "uncertainty": 0.1
        }

    basic_exp_pat = re.compile(
        rf'\b(?:basic|elementary|limited|beginner|introductory|minimal)\s+(?:knowledge|familiarity|understanding|skills?|experience)\s+(?:of|with|in)\s+{escaped_req}\b|\b(?:currently\s+|just\s+)?(?:learning|studying|exploring)\s+{escaped_req}\b',
        re.IGNORECASE
    )
    m_basic_exp = basic_exp_pat.search(cv_text)
    if m_basic_exp:
        conflict_s = extract_exact_cv_passage(req_clean, cv_text)
        return {
            "requirement": req_clean,
            "category": category,
            "importance": importance,
            "status": "PARTIALLY MATCHED",
            "supporting_evidence": conflict_s,
            "candidate_evidence": conflict_s,
            "explanation": f"Conflicting evidence in CV: Candidate indicates introductory/basic familiarity with '{req_clean}' rather than full production proficiency ('{conflict_s[:120]}').",
            "confidence": "High",
            "uncertainty": 0.2
        }

    # 3. Educational Qualifications Category
    if category == "Educational Qualification":
        deg_pat = re.compile(r'\b(?:bachelor|b\.?s\.?|b\.?sc|b\.?tech|master|m\.?s\.?|m\.?sc|ph\.?d\.?|doctorate|degree)\b', re.IGNORECASE)
        stem_pat = re.compile(r'\b(?:computer\s+science|cs|software\s+engineering|data\s+science|stem|engineering|information\s+technology|math(?:ematics)?|physics)\b', re.IGNORECASE)
        cs_pat = re.compile(r'\b(?:computer\s+science|cs\b|software\s+engineering|computing)\b', re.IGNORECASE)
        
        has_deg = deg_pat.search(cv_text)
        has_stem = stem_pat.search(cv_text)
        req_asks_cs = cs_pat.search(req_clean)
        
        if has_deg and req_asks_cs:
            if cs_pat.search(cv_text):
                passage = ""
                for s in re.split(r'[\r\n]+|(?<=[.!?])\s+', cv_text):
                    if deg_pat.search(s) and cs_pat.search(s):
                        passage = s.strip()[:240]
                        break
                if not passage:
                    passage = extract_exact_cv_passage("computer science", cv_text) or extract_exact_cv_passage("degree", cv_text)
                return {
                    "requirement": req_clean,
                    "category": category,
                    "importance": importance,
                    "status": "MATCHED",
                    "supporting_evidence": passage,
                    "candidate_evidence": passage,
                    "explanation": f"Verified educational qualification in CV: {passage[:140]}",
                    "confidence": "High",
                    "uncertainty": 0.1
                }
            elif has_stem:
                passage = extract_exact_cv_passage("degree", cv_text) or extract_exact_cv_passage("bachelor", cv_text) or extract_exact_cv_passage("science", cv_text)
                return {
                    "requirement": req_clean,
                    "category": category,
                    "importance": importance,
                    "status": "PARTIALLY MATCHED",
                    "supporting_evidence": passage,
                    "candidate_evidence": passage,
                    "explanation": f"Candidate holds a STEM degree, but exact alignment with {req_clean} is partial or in an adjacent discipline.",
                    "confidence": "Medium",
                    "uncertainty": 0.35
                }
            else:
                passage = extract_exact_cv_passage("degree", cv_text)
                return {
                    "requirement": req_clean,
                    "category": category,
                    "importance": importance,
                    "status": "PARTIALLY MATCHED",
                    "supporting_evidence": passage,
                    "candidate_evidence": passage,
                    "explanation": f"Candidate holds a degree, but in an unrelated discipline.",
                    "confidence": "Medium",
                    "uncertainty": 0.4
                }
        elif has_deg and has_stem:
            passage = ""
            for s in re.split(r'[\r\n]+|(?<=[.!?])\s+', cv_text):
                if deg_pat.search(s) and stem_pat.search(s):
                    passage = s.strip()[:240]
                    break
            if not passage:
                passage = extract_exact_cv_passage("degree", cv_text)
            return {
                "requirement": req_clean,
                "category": category,
                "importance": importance,
                "status": "MATCHED",
                "supporting_evidence": passage,
                "candidate_evidence": passage,
                "explanation": f"Verified educational qualification in CV: {passage[:140]}",
                "confidence": "High",
                "uncertainty": 0.1
            }
        elif has_deg:
            passage = extract_exact_cv_passage("degree", cv_text)
            return {
                "requirement": req_clean,
                "category": category,
                "importance": importance,
                "status": "PARTIALLY MATCHED",
                "supporting_evidence": passage,
                "candidate_evidence": passage,
                "explanation": f"Candidate holds a degree, but exact alignment with {req_clean} is partial or in an adjacent discipline.",
                "confidence": "Medium",
                "uncertainty": 0.35
            }
        else:
            return {
                "requirement": req_clean,
                "category": category,
                "importance": importance,
                "status": "MISSING",
                "supporting_evidence": "",
                "candidate_evidence": f"No degree matching '{req_clean}' found in CV.",
                "explanation": f"No educational qualification matching '{req_clean}' found in candidate profile or CV.",
                "confidence": "High",
                "uncertainty": 0.1
            }

    # 4. Experience Requirements Category
    if category == "Experience Requirement":
        m_yrs = re.search(r'(\d+)\+?\s*years?', req_lower)
        req_years = int(m_yrs.group(1)) if m_yrs else 2
        yrs_in_cv = re.findall(r'(\d+)\+?\s*years?\s+(?:of\s+)?experience', cv_text, re.IGNORECASE)
        max_cv_yrs = max([int(y) for y in yrs_in_cv], default=0)
        
        if max_cv_yrs >= req_years:
            passage = extract_exact_cv_passage("years of experience", cv_text)
            return {
                "requirement": req_clean,
                "category": category,
                "importance": importance,
                "status": "MATCHED",
                "supporting_evidence": passage,
                "candidate_evidence": passage,
                "explanation": f"Verified {max_cv_yrs} years of experience in CV, satisfying the {req_years}+ years requirement.",
                "confidence": "High",
                "uncertainty": 0.1
            }
        elif max_cv_yrs > 0 or "experience" in cv_text.lower():
            passage = extract_exact_cv_passage("experience", cv_text)
            return {
                "requirement": req_clean,
                "category": category,
                "importance": importance,
                "status": "PARTIALLY MATCHED",
                "supporting_evidence": passage,
                "candidate_evidence": passage,
                "explanation": f"Candidate demonstrates relevant project and engineering experience, but specific {req_years}+ years of enterprise tenure is not explicitly evidenced.",
                "confidence": "Medium",
                "uncertainty": 0.35
            }
        else:
            return {
                "requirement": req_clean,
                "category": category,
                "importance": importance,
                "status": "MISSING",
                "supporting_evidence": "",
                "candidate_evidence": "No matching experience tenure found in CV.",
                "explanation": f"No documentation satisfying '{req_clean}' found in candidate CV.",
                "confidence": "High",
                "uncertainty": 0.15
            }

    # 5. Technical Skills (Exact Match via Boundary-Safe Regex)
    direct_pat = skill_match_regex(req_clean)
    if direct_pat.search(cv_text):
        passage = extract_exact_cv_passage(req_clean, cv_text)
        return {
            "requirement": req_clean,
            "category": category,
            "importance": importance,
            "status": "MATCHED",
            "supporting_evidence": passage,
            "candidate_evidence": f'Found in CV: "{passage}"' if passage else f'Found direct mention in CV: "{req_clean}"',
            "explanation": f"Direct verified evidence found for {req_clean} in candidate CV.",
            "confidence": "High",
            "uncertainty": 0.1
        }

    # 6. Canonical Aliases (True exact synonyms: e.g. k8s == Kubernetes, py == Python, cpp == C++)
    for canonical, aliases in CANONICAL_ALIASES.items():
        if req_lower == canonical or any(req_lower == a for a in aliases):
            for form in [canonical] + aliases:
                alias_pat = skill_match_regex(form)
                if alias_pat.search(cv_text):
                    passage = extract_exact_cv_passage(form, cv_text)
                    return {
                        "requirement": req_clean,
                        "category": category,
                        "importance": importance,
                        "status": "MATCHED",
                        "supporting_evidence": passage,
                        "candidate_evidence": f'Found verified skill ({form}) in CV: "{passage}"' if passage else f'Found verified skill ({form}) in CV',
                        "explanation": f"Verified skill via canonical synonym '{form}' matching requirement '{req_clean}'.",
                        "confidence": "High",
                        "uncertainty": 0.1
                    }

    # 7. Portfolio Items Check
    if portfolio_items:
        for p in portfolio_items:
            tech = str(p.get("Techstack", ""))
            link = str(p.get("Links", "")).strip()
            link_str = f" ({link})" if link else ""
            if direct_pat.search(tech):
                return {
                    "requirement": req_clean,
                    "category": category,
                    "importance": importance,
                    "status": "MATCHED",
                    "supporting_evidence": tech,
                    "candidate_evidence": f"Demonstrated in Portfolio: {tech}{link_str}",
                    "explanation": f"Verified directly in candidate verified portfolio project ({tech}).",
                    "confidence": "High",
                    "uncertainty": 0.1
                }
            for canonical, aliases in CANONICAL_ALIASES.items():
                if req_lower == canonical or any(req_lower == a for a in aliases):
                    for form in [canonical] + aliases:
                        if skill_match_regex(form).search(tech):
                            return {
                                "requirement": req_clean,
                                "category": category,
                                "importance": importance,
                                "status": "MATCHED",
                                "supporting_evidence": tech,
                                "candidate_evidence": f"Demonstrated in Portfolio: {tech}{link_str}",
                                "explanation": f"Verified in portfolio project under canonical alias '{form}'.",
                                "confidence": "High",
                                "uncertainty": 0.1
                            }

    # 8. Multi-token Compound Requirements (e.g. "FastAPI and PostgreSQL")
    tokens = [w for w in re.findall(r'\b[a-zA-Z0-9+#.-]{2,}\b', req_lower) 
              if w not in ["and", "with", "the", "for", "experience", "knowledge", "strong", "skills", "ability", "in", "to", "years", "using", "plus", "understanding"]]
    if len(tokens) > 1:
        matched_tokens = []
        missing_tokens = []
        for t in tokens:
            if skill_match_regex(t).search(cv_text):
                matched_tokens.append(t)
            else:
                missing_tokens.append(t)
                
        if matched_tokens and not missing_tokens:
            passage = extract_exact_cv_passage(matched_tokens[0], cv_text)
            return {
                "requirement": req_clean,
                "category": category,
                "importance": importance,
                "status": "MATCHED",
                "supporting_evidence": passage,
                "candidate_evidence": f'Verified in CV: "{passage}"',
                "explanation": f'All required technical components ({", ".join(matched_tokens)}) verified in CV.',
                "confidence": "High",
                "uncertainty": 0.1
            }
        elif matched_tokens:
            passage = extract_exact_cv_passage(matched_tokens[0], cv_text)
            return {
                "requirement": req_clean,
                "category": category,
                "importance": importance,
                "status": "PARTIALLY MATCHED",
                "supporting_evidence": passage,
                "candidate_evidence": f'Found partial match ({", ".join(matched_tokens)}) in CV, but deeper enterprise scope ({", ".join(missing_tokens)}) not explicitly evidenced.',
                "explanation": f'Found partial match ({", ".join(matched_tokens)}) in CV, but ({", ".join(missing_tokens)}) is missing.',
                "confidence": "Medium",
                "uncertainty": 0.4
            }

    # 9. Technical Skill Normalization (Non-equivalencies & Ecosystem checks)
    # Rules:
    # - PyTorch is NOT automatically equivalent to TensorFlow.
    # - AWS experience is NOT automatically equivalent to Azure.
    # - Knowledge of Python does NOT imply knowledge of FastAPI.
    non_eq_candidates = NON_EQUIVALENT_PAIRS.get(req_lower, [])
    found_non_eq = []
    for ne_tool in non_eq_candidates:
        if skill_match_regex(ne_tool).search(cv_text):
            found_non_eq.append(ne_tool)
    if found_non_eq:
        ne_passage = extract_exact_cv_passage(found_non_eq[0], cv_text)
        found_displays = [format_tool_display(t) for t in found_non_eq]
        return {
            "requirement": req_clean,
            "category": category,
            "importance": importance,
            "status": "PARTIALLY MATCHED",
            "supporting_evidence": ne_passage,
            "candidate_evidence": f'Candidate demonstrates {", ".join(found_displays)}, but not {req_clean}.',
            "explanation": f"Technical skill normalization: {req_clean} is not automatically equivalent to {', '.join(found_displays)}. Candidate demonstrates related foundation ({found_displays[0]}), but specific {req_clean} experience is not evidenced.",
            "confidence": "Medium",
            "uncertainty": 0.35
        }

    # Related Ecosystem Check
    for eco_name, eco_data in RELATED_ECOSYSTEMS.items():
        tools = eco_data["tools"]
        req_in_eco = any(req_lower == t or t in req_lower for t in tools)
        if req_in_eco:
            found_eco_tools = []
            for t in tools:
                if t != req_lower and skill_match_regex(t).search(cv_text):
                    found_eco_tools.append(t)
            if found_eco_tools:
                passage = extract_exact_cv_passage(found_eco_tools[0], cv_text)
                return {
                    "requirement": req_clean,
                    "category": category,
                    "importance": importance,
                    "status": "PARTIALLY MATCHED",
                    "supporting_evidence": passage,
                    "candidate_evidence": f'Candidate demonstrates related {eco_name} foundation ({", ".join(found_eco_tools[:3])}), but specific {req_clean} experience is not explicitly demonstrated in CV.',
                    "explanation": f"Candidate demonstrates related {eco_name} foundation ({', '.join(found_eco_tools[:3])}), but specific {req_clean} experience is not explicitly demonstrated in CV.",
                    "confidence": "Medium",
                    "uncertainty": 0.4
                }

    # 10. Missing Skill
    return {
        "requirement": req_clean,
        "category": category,
        "importance": importance,
        "status": "MISSING",
        "supporting_evidence": "",
        "candidate_evidence": f"No direct or related evidence found for '{req_clean}' in candidate profile or CV.",
        "explanation": f"No direct or related evidence found for '{req_clean}' in candidate profile or CV.",
        "confidence": "High",
        "uncertainty": 0.1
    }

def find_cv_evidence(requirement: str, cv_text: str, portfolio_items: list[dict] | None = None, category: str = "Critical Technical Skill") -> tuple[str, str, str]:
    """
    Backward-compatibility wrapper returning (status, candidate_evidence, confidence).
    """
    res = evaluate_requirement(requirement, cv_text, portfolio_items=portfolio_items, category=category)
    return res["status"], res["candidate_evidence"], res["confidence"]

def verify_and_ground_llm_claims(
    evidence_breakdown: list[dict],
    cv_text: str,
    portfolio_items: list[dict] | None = None
) -> list[dict]:
    """
    Grounds LLM claims strictly against candidate CV text and portfolio evidence.
    Never counts unsupported LLM claims as evidence. Replaces hallucinated quotes
    with exact supporting CV passages, or downgrades unsupported matches to MISSING/PARTIALLY MATCHED.
    """
    grounded_items = []
    clean_cv = (cv_text or "").strip()

    for item in evidence_breakdown:
        req_name = str(item.get("requirement", "")).strip()
        category = item.get("category") or _determine_category(req_name, item.get("importance", ""))
        imp = item.get("importance") or _determine_importance(category)
        status = str(item.get("status", "MISSING")).upper()
        explanation = str(item.get("explanation", ""))
        confidence = str(item.get("confidence", "Medium")).capitalize()
        if confidence not in ["High", "Medium", "Low"]:
            confidence = "Medium"

        # If CV is empty, nothing can be matched!
        if not clean_cv:
            grounded_items.append({
                "requirement": req_name,
                "category": category,
                "importance": imp,
                "status": "MISSING",
                "supporting_evidence": "",
                "candidate_evidence": "Candidate CV is empty. No verifiable evidence available.",
                "explanation": "No evidence found in candidate profile or CV.",
                "confidence": "High",
                "uncertainty": 0.05
            })
            continue

        gt_eval = evaluate_requirement(req_name, clean_cv, portfolio_items, category=category)

        if "NOT RELEVANT" in status:
            grounded_items.append({
                "requirement": req_name,
                "category": "Irrelevant/Noise",
                "importance": "Irrelevant/Noise",
                "status": "NOT RELEVANT",
                "supporting_evidence": "",
                "candidate_evidence": "Filtered out by ATS shield.",
                "explanation": "Out-of-scope requirement excluded from candidate scoring.",
                "confidence": "High",
                "uncertainty": 0.0
            })
            continue

        # Grounding check for LLM claims of MATCHED
        if "MATCHED" in status and "PARTIAL" not in status:
            if gt_eval["status"] == "MATCHED":
                exact_passage = gt_eval["supporting_evidence"]
                grounded_items.append({
                    "requirement": req_name,
                    "category": category,
                    "importance": imp,
                    "status": "MATCHED",
                    "supporting_evidence": exact_passage,
                    "candidate_evidence": exact_passage if exact_passage else gt_eval["candidate_evidence"],
                    "explanation": explanation or gt_eval["explanation"],
                    "confidence": "High",
                    "uncertainty": 0.1
                })
            elif gt_eval["status"] == "PARTIALLY MATCHED":
                grounded_items.append({
                    "requirement": req_name,
                    "category": category,
                    "importance": imp,
                    "status": "PARTIALLY MATCHED",
                    "supporting_evidence": gt_eval["supporting_evidence"],
                    "candidate_evidence": gt_eval["candidate_evidence"],
                    "explanation": gt_eval["explanation"],
                    "confidence": "Medium",
                    "uncertainty": 0.35
                })
            else:
                # LLM claimed MATCHED, but skill/evidence is completely absent from CV!
                grounded_items.append({
                    "requirement": req_name,
                    "category": category,
                    "importance": imp,
                    "status": "MISSING",
                    "supporting_evidence": "",
                    "candidate_evidence": "Unsupported claim: No verifiable mention found in uploaded CV.",
                    "explanation": f"Unsupported LLM claim rejected: '{req_name}' does not appear in candidate's CV or portfolio.",
                    "confidence": "High",
                    "uncertainty": 0.8
                })
        elif "PARTIAL" in status:
            if gt_eval["status"] in ["MATCHED", "PARTIALLY MATCHED"]:
                grounded_items.append({
                    "requirement": req_name,
                    "category": category,
                    "importance": imp,
                    "status": gt_eval["status"],
                    "supporting_evidence": gt_eval["supporting_evidence"],
                    "candidate_evidence": gt_eval["candidate_evidence"],
                    "explanation": explanation or gt_eval["explanation"],
                    "confidence": "Medium",
                    "uncertainty": 0.4
                })
            else:
                grounded_items.append(gt_eval)
        else:
            # LLM says MISSING
            if gt_eval["status"] == "MATCHED":
                grounded_items.append(gt_eval)
            else:
                grounded_items.append({
                    "requirement": req_name,
                    "category": category,
                    "importance": imp,
                    "status": "MISSING",
                    "supporting_evidence": "",
                    "candidate_evidence": f"No evidence found in candidate profile or CV for '{req_name}'.",
                    "explanation": explanation or f"No direct or related evidence found for '{req_clean}' in candidate profile or CV.",
                    "confidence": "High",
                    "uncertainty": 0.1
                })

    return grounded_items

def audit_and_calculate_score(evidence_breakdown: list[dict]) -> dict:
    """
    Computes a deterministic, mathematically audited score from evidence items:
    - Critical Requirements (Technical, Experience, Education): 65% weight
    - Preferred Requirements: 25% weight
    - Soft Skills: 10% weight
    - Noise / Not Relevant: 0% weight (excluded)
    """
    crit_items = []
    pref_items = []
    soft_items = []
    noise_items = []
    
    for item in evidence_breakdown:
        imp = str(item.get("importance", "") or "").lower()
        cat = str(item.get("category", "") or "").lower()
        stat = str(item.get("status", "")).upper()
        
        if "noise" in imp or "irrelevant" in imp or "noise" in cat or "irrelevant" in cat or "NOT RELEVANT" in stat:
            noise_items.append(item)
        elif "pref" in imp or "pref" in cat or "nice" in imp or "bonus" in imp:
            pref_items.append(item)
        elif "soft" in imp or "soft" in cat or "collaborat" in imp:
            soft_items.append(item)
        else:
            crit_items.append(item)
            
    def get_points(items):
        if not items:
            return 0.0, 0.0, 0, 0, 0
        earned = 0.0
        n_matched = 0
        n_partial = 0
        n_missing = 0
        for it in items:
            s = str(it.get("status", "")).upper()
            if "MATCHED" in s and "PARTIAL" not in s:
                earned += 1.0
                n_matched += 1
            elif "PARTIAL" in s:
                earned += 0.5
                n_partial += 1
            else:
                n_missing += 1
        pct = (earned / len(items)) * 100.0
        return pct, earned, n_matched, n_partial, n_missing

    crit_pct, crit_earned, c_m, c_p, c_miss = get_points(crit_items)
    pref_pct, pref_earned, p_m, p_p, p_miss = get_points(pref_items)
    soft_pct, soft_earned, s_m, s_p, s_miss = get_points(soft_items)
    
    # Calculate weighted composite with dynamic normalization
    w_crit = 0.65 if crit_items else 0.0
    w_pref = 0.25 if pref_items else 0.0
    w_soft = 0.10 if soft_items else 0.0
    total_w = w_crit + w_pref + w_soft
    
    if total_w > 0:
        raw_score = (w_crit * crit_pct + w_pref * pref_pct + w_soft * soft_pct) / total_w
    else:
        raw_score = 50.0
        
    final_score = int(round(max(10.0, min(99.0, raw_score))))
    
    if final_score >= 85:
        fit_level = "Outstanding Alignment (85–100%)"
    elif final_score >= 70:
        fit_level = "Strong Candidate Match (70–84%)"
    elif final_score >= 50:
        fit_level = "Moderate Fit / High Potential (50–69%)"
    else:
        fit_level = "Early Career / Significant Skill Gaps (<50%)"
        
    return {
        "mathematical_score": final_score,
        "fit_level": fit_level,
        "critical_accuracy": {
            "percentage": round(crit_pct, 1),
            "matched": c_m,
            "partial": c_p,
            "missing": c_miss,
            "total": len(crit_items)
        },
        "preferred_accuracy": {
            "percentage": round(pref_pct, 1),
            "matched": p_m,
            "partial": p_p,
            "missing": p_miss,
            "total": len(pref_items)
        },
        "soft_accuracy": {
            "percentage": round(soft_pct, 1),
            "matched": s_m,
            "partial": s_p,
            "missing": s_miss,
            "total": len(soft_items)
        },
        "formula": f"({round(crit_pct, 1)}% × 65%) + ({round(pref_pct, 1)}% × 25%) + ({round(soft_pct, 1)}% × 10%)"
    }

class Chain:
    """
    Orchestrates LLM prompts for Job Information Extraction, CV Portfolio Extraction,
    deterministic Evidence-Based Fit Auditing, and Outreach Email Generation.
    """
    def __init__(self, model_name: str = "openai/gpt-oss-120b", api_key: str | None = None, temperature: float = 0.2):
        resolved_key = (api_key or os.getenv("API_KEY") or os.getenv("GROQ_API_KEY") or "").strip()
        self.api_key = resolved_key if len(resolved_key) >= 10 else None
        self.model_name = model_name
        self.temperature = temperature
        self.llm = None
        self._init_llm()

    @property
    def has_valid_key(self) -> bool:
        return bool(self.api_key and len(self.api_key) >= 10)

    def _init_llm(self):
        if self.has_valid_key:
            try:
                self.llm = ChatGroq(
                    temperature=self.temperature,
                    groq_api_key=self.api_key,
                    model_name=self.model_name
                )
            except Exception:
                self.llm = None
        else:
            self.llm = None

    def update_config(self, model_name: str | None = None, api_key: str | None = None, temperature: float | None = None):
        if model_name is not None:
            self.model_name = model_name
        if api_key is not None:
            clean_k = api_key.strip()
            self.api_key = clean_k if len(clean_k) >= 10 else None
        if temperature is not None:
            self.temperature = temperature
        self._init_llm()

    def extract_jobs(self, clean_text: str):
        """
        Extracts structured job requirements across 5 core categories:
        1. Critical technical skills
        2. Preferred technical skills
        3. Soft skills
        4. Experience requirements
        5. Educational qualifications
        """
        default_job = [{
            "role": "Target Role",
            "company": "Target Company",
            "contact_email": "",
            "experience": "1-3 years of software engineering experience",
            "skills": ["Python", "Machine Learning", "FastAPI"],
            "critical_technical_skills": ["Python", "Machine Learning"],
            "preferred_technical_skills": ["FastAPI"],
            "critical_requirements": ["Python", "Machine Learning"],
            "preferred_requirements": ["FastAPI"],
            "soft_skills": ["Problem Solving", "Communication"],
            "experience_requirements": ["1-3 years of software engineering experience"],
            "educational_qualifications": ["Bachelor's degree in Computer Science or related STEM field"],
            "general_responsibilities": ["Develop models and software services"],
            "irrelevant_noise": [],
            "domain": "Technology",
            "key_focus_areas": ["Model development", "Backend architecture"],
            "description": clean_text[:500] + ("..." if len(clean_text) > 500 else ""),
            "hiring_manager": "Hiring Team"
        }]

        if not self.has_valid_key or self.llm is None:
            return default_job

        prompt_extract = PromptTemplate.from_template(
            """### SCRAPED TEXT OR JOB POSTING:
{page_data}

### INSTRUCTION:
You are an expert talent acquisition and job requirement relevance analyzer.
Extract structured candidate requirements across 5 distinct categories, separating genuine competencies from company boilerplate.

Extract a valid JSON array of job objects (usually 1 object).
Each object MUST have the following keys:
- `role`: The exact job title (e.g. "Senior ML Engineer", "Full Stack Developer").
- `company`: Name of hiring company (if mentioned, otherwise "the company").
- `contact_email`: Recruiter or application email address if explicitly mentioned, otherwise "".
- `domain`: Industry or technical domain.
- `experience`: Brief experience overview (e.g. "3+ years", "Entry level").
- `critical_technical_skills`: A list of 3-6 core MUST-HAVE technical competencies, programming languages, and frameworks.
- `preferred_technical_skills`: A list of 2-4 NICE-TO-HAVE, bonus, or secondary technical tools.
- `soft_skills`: A list of 2-3 genuine interpersonal or collaborative skills.
- `experience_requirements`: A list of 1-3 specific experience requirements (e.g. ["3+ years of production experience in distributed backend systems"]).
- `educational_qualifications`: A list of 1-2 degree qualifications (e.g. ["Bachelor's or Master's degree in Computer Science or related field"]).
- `general_responsibilities`: A list of 2-4 core day-to-day duties.
- `irrelevant_noise`: A list of any legal boilerplate, office perks, or random unrelated text that should NOT affect candidate technical scoring.
- `skills`: A combined list of the top technical skills (critical + preferred).
- `key_focus_areas`: A list of 2-3 specific engineering goals for this hire.
- `description`: A 2-3 sentence summary of the key mission of this role.
- `hiring_manager`: Name or title of recruiter/manager if mentioned, otherwise "Hiring Team".

Return ONLY valid JSON.

### VALID JSON:"""
        )

        try:
            chain_extract = prompt_extract | self.llm
            res = chain_extract.invoke({"page_data": clean_text[:12000]})
        except Exception:
            return default_job

        try:
            json_parser = JsonOutputParser()
            json_res = json_parser.parse(res.content)
            jobs = json_res if isinstance(json_res, list) else ([json_res] if isinstance(json_res, dict) else default_job)
            for j in jobs:
                if isinstance(j, dict):
                    # Guarantee backward compatibility keys
                    if "critical_requirements" not in j:
                        j["critical_requirements"] = j.get("critical_technical_skills", [])
                    if "preferred_requirements" not in j:
                        j["preferred_requirements"] = j.get("preferred_technical_skills", [])
                    if "skills" not in j:
                        j["skills"] = list(dict.fromkeys(j.get("critical_requirements", []) + j.get("preferred_requirements", [])))
            return jobs
        except OutputParserException:
            content = res.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            try:
                parsed = json.loads(content)
                jobs = parsed if isinstance(parsed, list) else [parsed]
                for j in jobs:
                    if isinstance(j, dict):
                        if "critical_requirements" not in j:
                            j["critical_requirements"] = j.get("critical_technical_skills", [])
                        if "preferred_requirements" not in j:
                            j["preferred_requirements"] = j.get("preferred_technical_skills", [])
                        if "skills" not in j:
                            j["skills"] = list(dict.fromkeys(j.get("critical_requirements", []) + j.get("preferred_requirements", [])))
                return jobs
            except Exception:
                return default_job

    def extract_portfolio_data(self, raw_cv_text: str) -> list[dict]:
        """
        Extracts candidate core technical skills grouped by project or experience.
        Strictly prevents hallucination of placeholder GitHub or website URLs.
        """
        default_res = [
            {"Techstack": "Python, Machine Learning, Data Science", "Links": ""}
        ]

        if not self.has_valid_key or self.llm is None:
            return default_res

        prompt_parse_cv = PromptTemplate.from_template(
            """### CANDIDATE CV / RESUME TEXT:
{cv_text}

### INSTRUCTION:
Extract the candidate's core technical skills (Techstack) grouped by project, expertise area, or experience, along with any relevant URLs/project links (Links).

CRITICAL ACCURACY & NO-HALLUCINATION RULES:
1. Extract ONLY genuine, explicit URLs or GitHub links that are actually written in the candidate's CV text.
2. If a project does NOT have an explicit repository link or URL in the CV, leave `Links` as an EMPTY STRING ("").
3. DO NOT invent, fabricate, guess, or create placeholder links like "https://github.com/candidate/project-name" or "example.com".
4. Projects without repository links are completely valid—preserve them with `Links: ""`.

Return a valid JSON array of objects. Each object must contain:
- `Techstack`: Comma-separated list of technologies and skills for that project/area.
- `Links`: Exact URL from the CV, or "" if not provided.

Return ONLY valid JSON.

### VALID JSON ARRAY:"""
        )

        try:
            chain_parse = prompt_parse_cv | self.llm
            res = chain_parse.invoke({"cv_text": raw_cv_text[:16000]})
        except Exception:
            return default_res

        try:
            json_parser = JsonOutputParser()
            json_res = json_parser.parse(res.content)
            items = json_res if isinstance(json_res, list) else ([json_res] if isinstance(json_res, dict) else [])
            return sanitize_extracted_portfolio(items)
        except Exception:
            raw_text = res.content.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            try:
                parsed = json.loads(raw_text)
                items = parsed if isinstance(parsed, list) else ([parsed] if isinstance(parsed, dict) else [])
                return sanitize_extracted_portfolio(items)
            except Exception:
                return default_res

    def parse_candidate_profile_from_cv(self, raw_cv_text: str) -> dict:
        """
        Extracts candidate personal details and portfolio items directly from the uploaded CV text.
        """
        default_profile = {
            "full_name": "Candidate",
            "position": "Software Engineer",
            "college": "",
            "degree": "",
            "candidate_type": "Student / Recent Graduate",
            "portfolio": []
        }

        if not self.has_valid_key or self.llm is None:
            lines = [line.strip() for line in raw_cv_text.splitlines() if line.strip()]
            name = lines[0] if lines else "Candidate"
            return {
                "full_name": name,
                "position": "Software Engineer",
                "college": "",
                "degree": "",
                "candidate_type": "Student / Recent Graduate",
                "portfolio": [{"Techstack": "Software Development, Python, Web", "Links": ""}]
            }

        prompt_profile = PromptTemplate.from_template(
            """### CANDIDATE CV / RESUME CONTENT:
{cv_text}

### INSTRUCTION:
Extract the candidate's structured profile information and technical portfolio.
Return a valid JSON object with the following keys:
- `full_name`: Candidate's full name.
- `position`: Their current headline or target job title.
- `college`: University, College, or Institution attended (or "" if not found).
- `degree`: Major / Degree field of study (e.g. "B.Sc. in Computer Science" or "" if not found).
- `candidate_type`: Choose ONE of: ["Student / Recent Graduate", "Experienced Professional", "Freelancer / Consultant"].
- `portfolio`: An array of objects with keys `Techstack` and `Links`.

Return ONLY valid JSON.

### VALID JSON:"""
        )

        try:
            chain_profile = prompt_profile | self.llm
            res = chain_profile.invoke({"cv_text": raw_cv_text[:16000]})
            json_parser = JsonOutputParser()
            parsed = json_parser.parse(res.content)
            if isinstance(parsed, dict) and "full_name" in parsed:
                if "portfolio" in parsed and isinstance(parsed["portfolio"], list):
                    parsed["portfolio"] = sanitize_extracted_portfolio(parsed["portfolio"])
                return parsed
        except Exception:
            pass

        return default_profile

    def write_mail(
        self,
        job: dict,
        links: list | str,
        user_name: str,
        user_college: str | None = None,
        user_study: str | None = None,
        user_position: str | None = None,
        user_possition: str | None = None,
        tone: str = "Professional & Persuasive",
        length: str = "Standard (120-180 words)",
        candidate_type: str = "Student / Recent Graduate",
        custom_instructions: str = "",
        cv_text: str = ""
    ) -> dict:
        """
        Drafts a personalized outreach email grounded strictly in candidate's verified accomplishments.
        """
        pos = (user_position or user_possition or "").strip()
        study = (user_study or "").strip()
        college = (user_college or "").strip()
        
        links_list = [links] if isinstance(links, str) else (links or [])
        verified_links = [l.strip() for l in links_list if l and is_valid_url(l)]
        
        role_title = job.get("role", "Target Position")
        company_name = job.get("company", "Company")
        critical_reqs = ", ".join(job.get("critical_requirements", job.get("critical_technical_skills", [])))
        focus_areas = ", ".join(job.get("key_focus_areas", []))

        # Dynamic fallback email
        fallback_subject = [
            f"Application for {role_title} — {user_name}",
            f"{user_name} | {role_title} Application",
            f"Inquiry regarding {role_title} at {company_name}"
        ]
        
        link_mention = f"You can explore my projects here: {verified_links[0]}" if verified_links else "I would welcome the opportunity to walk through my relevant projects."
        study_mention = f" with a focus on {study}" if study else ""
        college_mention = f" from {college}" if college else ""
        
        fallback_body = f"""Dear Hiring Team at {company_name},

I am writing to express my interest in the {role_title} position. As a {pos or 'software engineer'}{study_mention}{college_mention}, I have worked on systems aligning closely with your focus in {focus_areas or 'engineering'}.

My background includes hands-on experience with {critical_reqs or 'modern software engineering'}. {link_mention}

I have attached my resume for your review and look forward to the possibility of discussing how my skills can contribute to {company_name}.

Sincerely,
{user_name}"""

        if not self.has_valid_key or self.llm is None:
            return {
                "subject_lines": fallback_subject,
                "body": fallback_body,
                "match_summary": f"Direct outreach targeting {company_name}'s {role_title} role.",
                "key_highlights_used": [critical_reqs.split(",")[0]] if critical_reqs else ["Software Engineering"],
                "focus_areas_addressed": focus_areas
            }

        prompt_email = PromptTemplate.from_template(
            """### TARGET JOB:
Role: {role}
Company: {company}
Critical Requirements: {critical_reqs}
Key Focus Areas: {focus_areas}

### CANDIDATE PROFILE & VERIFIED EVIDENCE:
Candidate Name: {user_name}
Title / Focus: {pos}
Education: {study} from {college}
Experience Level: {candidate_type}
Verified Links (Candidate URLs): {verified_links}
Additional Instructions / Notes: {custom_instructions}
Candidate Resume Context:
{cv_context}

### INSTRUCTIONS:
Draft an application email that is persuasive, concise, and credible.
- Never invent experience or claim skills not in the candidate context.
- Use tone: {tone} and length: {length}.

Return a valid JSON object matching:
{{
  "subject_lines": ["Compelling Subject Line 1", "Alternative Subject Line 2"],
  "body": "Full body of the email text",
  "match_summary": "1 sentence explaining the fit",
  "key_highlights_used": ["Skill 1", "Project 1"],
  "focus_areas_addressed": "Summary of addressed focus areas"
}}

### VALID JSON:"""
        )

        try:
            chain_mail = prompt_email | self.llm
            res = chain_mail.invoke({
                "role": role_title,
                "company": company_name,
                "critical_reqs": critical_reqs,
                "focus_areas": focus_areas,
                "user_name": user_name,
                "pos": pos,
                "study": study,
                "college": college,
                "candidate_type": candidate_type,
                "verified_links": ", ".join(verified_links) if verified_links else "None provided",
                "custom_instructions": custom_instructions or "None",
                "cv_context": cv_text[:8000] if cv_text else "None",
                "tone": tone,
                "length": length
            })
            json_parser = JsonOutputParser()
            parsed = json_parser.parse(res.content)
            if isinstance(parsed, dict) and "body" in parsed and "subject_lines" in parsed:
                if "subject" not in parsed and parsed["subject_lines"]:
                    parsed["subject"] = parsed["subject_lines"][0]
                return parsed
        except Exception:
            pass

        return {
            "subject": fallback_subject[0],
            "subject_lines": fallback_subject,
            "body": fallback_body,
            "match_summary": f"Direct outreach targeting {company_name}'s {role_title} role.",
            "key_highlights_used": [critical_reqs.split(",")[0]] if critical_reqs else ["Software Engineering"],
            "focus_areas_addressed": focus_areas
        }

    def analyze_job_fit(
        self,
        job: dict,
        portfolio_summary: str,
        user_name: str,
        user_position: str = "Candidate",
        user_study: str = "Computer Science",
        candidate_type: str = "Student / Recent Graduate",
        cv_text: str = ""
    ) -> dict:
        """
        Performs an evidence-based relevance and gap analysis between candidate profile and job requirements.
        Evaluates 5 structured requirement categories:
        1. Critical technical skills
        2. Preferred technical skills
        3. Soft skills
        4. Experience requirements
        5. Educational qualifications
        Classifies requirements into MATCHED, PARTIALLY MATCHED, MISSING, and NOT RELEVANT.
        Strictly prevents unsupported LLM claims from counting as evidence.
        """
        job_reqs = str(job)
        cv_evidence_text = (cv_text[:16000] if cv_text else "") or portfolio_summary
        pre_noise = job.get("irrelevant_noise", []) if isinstance(job, dict) else []

        # Gather structured requirements across all 5 categories
        all_reqs = []
        if isinstance(job, dict):
            # 1. Critical Technical Skills
            crit_tech = job.get("critical_technical_skills") or job.get("critical_requirements") or []
            for r in crit_tech:
                all_reqs.append({"req": r, "category": "Critical Technical Skill", "imp": "Critical requirement"})
                
            # 2. Preferred Technical Skills
            pref_tech = job.get("preferred_technical_skills") or job.get("preferred_requirements") or []
            for r in pref_tech:
                all_reqs.append({"req": r, "category": "Preferred Technical Skill", "imp": "Preferred requirement"})
                
            # 3. Soft Skills
            for r in job.get("soft_skills", []):
                all_reqs.append({"req": r, "category": "Soft Skill", "imp": "Soft skill"})
                
            # 4. Experience Requirements
            exp_reqs = job.get("experience_requirements", [])
            if not exp_reqs and job.get("experience"):
                exp_reqs = [job.get("experience")]
            for r in exp_reqs:
                all_reqs.append({"req": r, "category": "Experience Requirement", "imp": "Critical requirement"})
                
            # 5. Educational Qualifications
            edu_reqs = job.get("educational_qualifications", [])
            for r in edu_reqs:
                all_reqs.append({"req": r, "category": "Educational Qualification", "imp": "Critical requirement"})
                
            # Fallback if no specific categories were found
            if not all_reqs and "skills" in job:
                for r in job.get("skills", []):
                    all_reqs.append({"req": r, "category": "Critical Technical Skill", "imp": "Critical requirement"})

        # Step 1: Pre-Audit candidate CV deterministically
        pre_audited_lines = []
        heuristic_breakdown = []
        for r_obj in all_reqs:
            req_name = r_obj["req"]
            eval_res = evaluate_requirement(
                req_name,
                cv_evidence_text,
                category=r_obj["category"],
                candidate_profile={"user_study": user_study, "user_position": user_position, "candidate_type": candidate_type}
            )
            pre_audited_lines.append(f"- [{eval_res['category']}] {req_name} -> Verified Status: {eval_res['status']} | Evidence: {eval_res['supporting_evidence']}")
            heuristic_breakdown.append(eval_res)

        for n in pre_noise:
            heuristic_breakdown.append({
                "requirement": n,
                "category": "Irrelevant/Noise",
                "importance": "Irrelevant/Noise",
                "status": "NOT RELEVANT",
                "supporting_evidence": "",
                "candidate_evidence": "Filtered out by ATS shield.",
                "explanation": "Out-of-scope requirement excluded from candidate scoring.",
                "confidence": "High",
                "uncertainty": 0.0
            })

        pre_audit_text = "\n".join(pre_audited_lines) if pre_audited_lines else "No structured requirements provided."

        if not self.has_valid_key or self.llm is None:
            audit_meta = audit_and_calculate_score(heuristic_breakdown)
            matched_str = [h["requirement"] for h in heuristic_breakdown if h["status"] == "MATCHED"][:4]
            skill_gp = [h["requirement"] for h in heuristic_breakdown if h["status"] == "MISSING"][:3]
            return {
                "match_score": audit_meta["mathematical_score"],
                "fit_level": audit_meta["fit_level"],
                "matched_strengths": matched_str or ["Technical Fundamentals", "Software Engineering"],
                "skill_gaps": skill_gp or ["Enterprise scale deployment"],
                "strategic_advice": f"Emphasize your demonstrated projects in {user_position} and your rapid capacity to learn missing tools.",
                "evidence_breakdown": heuristic_breakdown,
                "noise_filtered": pre_noise,
                "audit_meta": audit_meta
            }

        prompt_fit = PromptTemplate.from_template(
            """### TARGET JOB REQUIREMENTS & CONTEXT:
Job Details:
{job_details}

### CANDIDATE RESUME / CV EVIDENCE:
Candidate Name: {user_name} ({user_position})
Education: {user_study}
Experience Level / Category: {candidate_type}
Candidate CV & Portfolio Details:
{candidate_evidence}

### PRE-AUDITED VERIFIED EVIDENCE IN CV:
{pre_audited_evidence}

### INSTRUCTIONS:
You are an expert, objective talent assessment and ATS intelligence engine.
Perform a strict, EVIDENCE-BASED candidate-to-job fit and gap analysis.

CRITICAL RULES:
1. NEVER INVENT EVIDENCE: Every claimed match MUST have an exact supporting quote from candidate's CV.
2. DISAMBIGUATE NON-EQUIVALENTS: PyTorch is not automatically equivalent to TensorFlow. AWS is not Azure. Python does not imply FastAPI.
3. PRESERVE CATEGORIES: Return structured items across Critical Technical Skills, Preferred Technical Skills, Soft Skills, Experience Requirements, and Educational Qualifications.

Return ONLY a valid JSON object matching the schema below.

### JSON OUTPUT SCHEMA:
{{
  "match_score": 75,
  "fit_level": "Strong Match (70-84%)",
  "matched_strengths": ["Top 3-5 verified strengths with candidate evidence"],
  "skill_gaps": ["Top 2-4 genuine critical missing requirements"],
  "strategic_advice": "2-3 sentences of strategic advice on how the candidate should address gaps",
  "evidence_breakdown": [
    {{
      "requirement": "Name of requirement or skill",
      "category": "Critical Technical Skill | Preferred Technical Skill | Soft Skill | Experience Requirement | Educational Qualification",
      "importance": "Critical requirement | Preferred requirement | Soft skill",
      "status": "MATCHED | PARTIALLY MATCHED | MISSING | NOT RELEVANT",
      "supporting_evidence": "Exact passage from candidate CV",
      "candidate_evidence": "Exact passage from candidate CV",
      "explanation": "Why this status was assigned",
      "confidence": "High | Medium | Low",
      "uncertainty": 0.1
    }}
  ],
  "noise_filtered": ["List of any irrelevant/noise items ignored during evaluation"]
}}

### VALID JSON:"""
        )

        try:
            chain_fit = prompt_fit | self.llm
            res = chain_fit.invoke({
                "job_details": job_reqs[:6000],
                "user_name": user_name,
                "user_position": user_position,
                "user_study": user_study,
                "candidate_type": candidate_type,
                "candidate_evidence": cv_evidence_text[:16000],
                "pre_audited_evidence": pre_audit_text
            })

            parsed = None
            try:
                json_parser = JsonOutputParser()
                parsed = json_parser.parse(res.content)
            except Exception:
                raw_text = res.content.strip()
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0].strip()
                parsed = json.loads(raw_text)

            if isinstance(parsed, dict) and "evidence_breakdown" in parsed:
                # Crucial Grounding Pass: Reject unsupported LLM claims
                grounded_breakdown = verify_and_ground_llm_claims(parsed["evidence_breakdown"], cv_evidence_text)
                
                # Ensure all pre-audited requirements are represented
                existing_reqs = {item.get("requirement", "").lower() for item in grounded_breakdown}
                for pre_item in heuristic_breakdown:
                    if pre_item.get("requirement", "").lower() not in existing_reqs:
                        grounded_breakdown.append(pre_item)

                audit_meta = audit_and_calculate_score(grounded_breakdown)
                parsed["evidence_breakdown"] = grounded_breakdown
                parsed["match_score"] = audit_meta["mathematical_score"]
                parsed["fit_level"] = audit_meta["fit_level"]
                parsed["audit_meta"] = audit_meta
                return parsed

        except Exception:
            pass

        # Robust, high-accuracy dynamic fallback computed directly from candidate's CV
        audit_meta = audit_and_calculate_score(heuristic_breakdown)
        matched_str = [h["requirement"] for h in heuristic_breakdown if h["status"] == "MATCHED"][:4]
        skill_gp = [h["requirement"] for h in heuristic_breakdown if h["status"] == "MISSING"][:3]
        return {
            "match_score": audit_meta["mathematical_score"],
            "fit_level": audit_meta["fit_level"],
            "matched_strengths": matched_str or ["Technical Fundamentals", "Software Engineering"],
            "skill_gaps": skill_gp or ["Enterprise scale deployment"],
            "strategic_advice": f"Emphasize your demonstrated projects in {user_position} and your rapid capacity to learn missing tools.",
            "evidence_breakdown": heuristic_breakdown,
            "noise_filtered": pre_noise,
            "audit_meta": audit_meta
        }
