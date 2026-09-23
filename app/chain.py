import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException

load_dotenv()

SUPPORTED_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "groq/compound-mini",
    "groq/compound",
    "qwen/qwen3.6-27b"
]

import re

COMMON_TECH_SYNONYMS = {
    "python": ["python", "py", "django", "fastapi", "flask", "pandas", "numpy", "scipy"],
    "javascript": ["javascript", "js", "typescript", "ts", "node", "nodejs", "react", "vue", "angular", "nextjs", "express"],
    "typescript": ["typescript", "ts", "javascript", "js"],
    "react": ["react", "reactjs", "react.js", "next.js", "nextjs", "redux", "frontend"],
    "node": ["node", "nodejs", "node.js", "express", "expressjs", "nestjs", "backend"],
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda", "cloudwatch", "iam", "dynamodb"],
    "azure": ["azure", "microsoft azure", "blob storage", "azure functions"],
    "gcp": ["gcp", "google cloud", "bigquery", "google cloud platform"],
    "docker": ["docker", "container", "containers", "containerization", "docker-compose"],
    "kubernetes": ["kubernetes", "k8s", "helm", "kubectl", "cluster", "orchestration"],
    "sql": ["sql", "postgresql", "postgres", "mysql", "sqlite", "relational database", "rdbms", "queries"],
    "nosql": ["nosql", "mongodb", "mongo", "redis", "dynamodb", "cassandra"],
    "machine learning": ["machine learning", "ml", "deep learning", "ai", "artificial intelligence", "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras", "models"],
    "pytorch": ["pytorch", "torch", "deep learning", "neural networks", "tensor"],
    "tensorflow": ["tensorflow", "tf", "keras"],
    "nlp": ["nlp", "natural language processing", "llm", "large language models", "transformers", "huggingface", "bert", "gpt", "spacy", "langchain"],
    "ci/cd": ["ci/cd", "ci", "cd", "continuous integration", "continuous deployment", "github actions", "gitlab ci", "jenkins"],
    "git": ["git", "github", "gitlab", "version control"],
    "rest api": ["rest", "restful", "api", "apis", "fastapi", "flask", "endpoints", "json"],
    "graphql": ["graphql", "apollo", "query language"],
    "linux": ["linux", "unix", "bash", "shell scripting", "ubuntu"],
    "c++": ["c++", "cpp"],
    "java": ["java", "spring", "springboot", "spring boot"],
    "go": ["go", "golang"],
    "fastapi": ["fastapi", "python", "rest api", "pydantic", "starlette", "backend"],
    "django": ["django", "django rest framework", "python", "drf", "backend"],
    "flask": ["flask", "python", "werkzeug", "jinja"],
}

def find_cv_evidence(requirement: str, cv_text: str, portfolio_items: list[dict] | None = None) -> tuple[str, str, str]:
    """
    Scans candidate CV text and portfolio for verifiable evidence matching a requirement.
    Returns: (status: 'MATCHED'|'PARTIALLY MATCHED'|'MISSING', evidence_quote: str, confidence: str)
    """
    req_clean = requirement.strip().lower()
    if not req_clean or not cv_text:
        return "MISSING", "No evidence found in candidate profile.", "Low"
        
    cv_lower = cv_text.lower()
    
    # 1. Direct exact phrase match
    if req_clean in cv_lower:
        sentences = re.split(r'[.\n\r]+', cv_text)
        for s in sentences:
            if req_clean in s.lower():
                clean_s = s.strip()
                if len(clean_s) > 12:
                    return "MATCHED", f'Found in CV: "{clean_s[:160]}"', "High"
        return "MATCHED", f'Found direct mention in CV: "{req_clean}"', "High"
        
    # 2. Extract key technical tokens (ignore common stop words)
    tokens = [w for w in re.findall(r'\b[a-zA-Z0-9+#.-]{2,}\b', req_clean) 
              if w not in ["and", "with", "the", "for", "experience", "knowledge", "strong", "skills", "ability", "in", "to", "years", "using"]]
    
    if tokens and all(t in cv_lower for t in tokens):
        for s in re.split(r'[.\n\r]+', cv_text):
            if any(t in s.lower() for t in tokens):
                clean_s = s.strip()
                if len(clean_s) > 12:
                    return "MATCHED", f'Verified in CV: "{clean_s[:160]}"', "High"

    # 3. Check Tech Synonyms
    for key, syns in COMMON_TECH_SYNONYMS.items():
        if key in req_clean or any(s in req_clean for s in syns):
            matched_syns = [s for s in syns if s in cv_lower]
            if matched_syns:
                for s in re.split(r'[.\n\r]+', cv_text):
                    if any(ms in s.lower() for ms in matched_syns):
                        clean_s = s.strip()
                        return "MATCHED", f'Found related tech ({", ".join(matched_syns[:3])}) in CV: "{clean_s[:160]}"', "High"

    # 4. Check candidate portfolio projects
    if portfolio_items:
        for p in portfolio_items:
            tech = str(p.get("Techstack", "")).lower()
            if req_clean in tech or any(t in tech for t in tokens if len(t) > 3):
                return "MATCHED", f'Demonstrated in Portfolio: {p.get("Techstack")} ({p.get("Links", "")})', "High"

    # 5. Partial token match
    if tokens and any(t in cv_lower for t in tokens if len(t) > 3):
        matched_tokens = [t for t in tokens if t in cv_lower and len(t) > 3]
        return "PARTIALLY MATCHED", f'Found partial mention ({", ".join(matched_tokens)}) in CV, but deeper enterprise scope unverified.', "Medium"

    return "MISSING", "No evidence found in candidate profile or CV.", "High"

def audit_and_calculate_score(evidence_breakdown: list[dict]) -> dict:
    """
    Computes a deterministic, mathematically audited score from evidence items:
    - Critical Requirements: 65% weight
    - Preferred Requirements: 25% weight
    - Soft Skills: 10% weight
    - Noise / Not Relevant: 0% weight (excluded)
    """
    crit_items = []
    pref_items = []
    soft_items = []
    noise_items = []
    
    for item in evidence_breakdown:
        imp = str(item.get("importance", "")).lower()
        stat = str(item.get("status", "")).upper()
        
        if "noise" in imp or "irrelevant" in imp or "NOT RELEVANT" in stat:
            noise_items.append(item)
        elif "pref" in imp or "nice" in imp or "bonus" in imp:
            pref_items.append(item)
        elif "soft" in imp or "interpersonal" in imp or "collaborat" in imp:
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
    def __init__(self, model_name: str = "openai/gpt-oss-120b", api_key: str | None = None, temperature: float = 0.2):
        resolved_key = (api_key or os.getenv("API_KEY") or os.getenv("GROQ_API_KEY") or "").strip()
        self.api_key = resolved_key
        self.model_name = model_name if model_name in SUPPORTED_MODELS or "/" in model_name else "openai/gpt-oss-120b"
        self.temperature = temperature
        self._init_llm()

    @property
    def has_valid_key(self) -> bool:
        return bool(self.api_key and self.api_key != "dummy_key" and len(self.api_key.strip()) > 10)

    def _init_llm(self):
        if self.has_valid_key:
            self.llm = ChatGroq(
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature
            )
        else:
            self.llm = None

    def update_config(self, model_name: str | None = None, api_key: str | None = None, temperature: float | None = None):
        if model_name:
            self.model_name = model_name
        if api_key is not None:
            self.api_key = api_key.strip()
        if temperature is not None:
            self.temperature = temperature
        self._init_llm()

    def extract_jobs(self, clean_text: str):
        if not self.has_valid_key or self.llm is None:
            return [{
                "role": "Target Role",
                "company": "Target Company",
                "contact_email": "",
                "experience": "Relevant Experience",
                "skills": ["Python", "Machine Learning", "FastAPI"],
                "critical_requirements": ["Python", "Machine Learning"],
                "preferred_requirements": ["FastAPI"],
                "general_responsibilities": ["Develop models and software services"],
                "soft_skills": ["Problem Solving", "Communication"],
                "irrelevant_noise": [],
                "domain": "Technology",
                "key_focus_areas": ["Model development", "Backend architecture"],
                "description": clean_text[:300] + "...",
                "hiring_manager": "Hiring Team"
            }]

        prompt_extract = PromptTemplate.from_template(
            """### SCRAPED TEXT OR JOB POSTING:
{page_data}

### INSTRUCTION:
You are an expert talent acquisition and job description relevance analyzer.
Analyze the job description above carefully. Extract structured information and separate genuine candidate requirements from boilerplate, company background, and unrelated text.

Extract a valid JSON array of job objects (usually 1 object).
Each object MUST have the following keys:
- `role`: The exact job title (e.g. "AI/ML Engineer Intern", "Senior Python Backend Developer").
- `company`: Name of hiring company (if mentioned, otherwise "the company").
- `contact_email`: Recruiter, HR, or application email address if explicitly mentioned, otherwise "".
- `domain`: Industry/domain (e.g. "Artificial Intelligence", "Fintech", "HealthTech", "Cloud SaaS").
- `experience`: Required experience level (e.g. "Internship / Student", "Entry Level", "1-3 years", "5+ years Senior").
- `critical_requirements`: A list of 3-6 core MUST-HAVE technical competencies, programming languages, and frameworks that are genuinely central to this role.
- `preferred_requirements`: A list of 2-4 NICE-TO-HAVE, bonus, or secondary tools/skills.
- `general_responsibilities`: A list of 2-4 core day-to-day duties.
- `soft_skills`: A list of 2-3 genuine interpersonal or collaborative skills.
- `irrelevant_noise`: A list of any requirements or text that are clearly unrelated to the core role, random noise, misplaced preferences (e.g. "experience with marine biology" in a software job), or legal boilerplate that should NOT affect candidate suitability.
- `skills`: A combined list of the top technical skills (critical + preferred) for search indexing.
- `key_focus_areas`: A list of 2-3 specific engineering problems or goals this hire will work on.
- `description`: A 2-3 sentence summary of the key responsibilities and mission of this role.
- `hiring_manager`: Name or title of recruiter/manager if mentioned, otherwise "Hiring Team".

IMPORTANT:
- Do NOT classify random noise or boilerplate as critical requirements.
- Distinguish between MUST-HAVE skills and NICE-TO-HAVE skills.

Return ONLY valid JSON.

### VALID JSON:"""
        )

        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke({"page_data": clean_text})

        try:
            json_parser = JsonOutputParser()
            json_res = json_parser.parse(res.content)
            if isinstance(json_res, list):
                return json_res
            elif isinstance(json_res, dict):
                return [json_res]
            return []
        except OutputParserException:
            content = res.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            import json
            try:
                parsed = json.loads(content)
                return parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                return [{
                    "role": "Target Job Role",
                    "company": "Target Company",
                    "experience": "Relevant Experience",
                    "skills": ["Python", "Machine Learning", "Communication"],
                    "critical_requirements": ["Python", "Machine Learning"],
                    "preferred_requirements": [],
                    "general_responsibilities": ["Software development"],
                    "soft_skills": ["Communication"],
                    "irrelevant_noise": [],
                    "domain": "Technology",
                    "key_focus_areas": ["Engineering"],
                    "description": clean_text[:300] + "...",
                    "hiring_manager": "Hiring Team"
                }]

    def extract_portfolio_data(self, raw_cv_text: str):
        prompt_parse_cv = PromptTemplate.from_template(
            """### CANDIDATE CV / RESUME TEXT:
{cv_text}

### INSTRUCTION:
Extract the candidate's core technical skills (Techstack) grouped by project, expertise area, or experience, along with any relevant URLs/project links (Links).
If a project doesn't have an explicit link in the text, use their GitHub or LinkedIn profile URL if available, or a descriptive placeholder like "https://github.com/candidate/project-name".

Return a valid JSON array of objects. Each object must contain:
- `Techstack`: Comma-separated list of technologies and skills for that project/area.
- `Links`: Exact URL or repository link representing this project/experience.

Example:
[
  {{"Techstack": "Python, FastAPI, Streamlit, LangChain, Groq", "Links": "https://github.com/candidate/cold-email-generator"}},
  {{"Techstack": "React, TypeScript, TailwindCSS, Next.js", "Links": "https://github.com/candidate/saas-dashboard"}},
  {{"Techstack": "PyTorch, Computer Vision, OpenCV, YOLO", "Links": "https://github.com/candidate/object-detection"}}
]

Return ONLY valid JSON.

### VALID JSON ARRAY:"""
        )

        chain_parse = prompt_parse_cv | self.llm
        res = chain_parse.invoke({"cv_text": raw_cv_text})

        try:
            json_parser = JsonOutputParser()
            json_res = json_parser.parse(res.content)
            if isinstance(json_res, list):
                return json_res
            elif isinstance(json_res, dict):
                return [json_res]
            return []
        except Exception:
            return [
                {"Techstack": "Python, Machine Learning, Data Science", "Links": "https://github.com/profile"}
            ]

    def parse_candidate_profile_from_cv(self, raw_cv_text: str) -> dict:
        """
        Extracts candidate personal details (name, target position, college, degree, candidate type)
        and portfolio items directly from the uploaded CV text using LLM.
        """
        if not self.has_valid_key or self.llm is None:
            lines = [line.strip() for line in raw_cv_text.splitlines() if line.strip()]
            name = lines[0] if lines else "Candidate"
            return {
                "full_name": name,
                "position": "Software Engineer",
                "college": "",
                "degree": "",
                "candidate_type": "Experienced Professional",
                "portfolio": [{"Techstack": "Software Development, Python, Web", "Links": "https://github.com"}]
            }

        prompt_profile = PromptTemplate.from_template(
            """### CANDIDATE CV / RESUME CONTENT:
{cv_text}

### INSTRUCTION:
Extract the candidate's structured profile information and technical portfolio.
Return a valid JSON object with the following keys:
- `full_name`: Candidate's full name.
- `position`: Their current title or target job title (e.g. "Full Stack Developer", "Data Scientist", "Software Engineer").
- `college`: University, College, or Institution attended (or "" if not found).
- `degree`: Major / Degree field of study (e.g. "B.Sc. in Computer Science" or "" if not found).
- `candidate_type`: Choose ONE of: ["Student / Recent Graduate", "Experienced Professional", "Freelancer / Consultant"].
- `portfolio`: An array of objects with keys `Techstack` (comma-separated tech skills) and `Links` (URLs or GitHub links mentioned, or "https://github.com/candidate/project-name").

Return ONLY valid JSON.

### VALID JSON:"""
        )

        try:
            chain_profile = prompt_profile | self.llm
            res = chain_profile.invoke({"cv_text": raw_cv_text[:4000]})
            json_parser = JsonOutputParser()
            parsed = json_parser.parse(res.content)
            if isinstance(parsed, dict) and "full_name" in parsed:
                return parsed
        except Exception:
            pass

        return {
            "full_name": "Candidate",
            "position": "Software Engineer",
            "college": "",
            "degree": "",
            "candidate_type": "Student / Recent Graduate",
            "portfolio": []
        }


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
    ):
        position = user_position or user_possition or "Candidate"
        college = user_college if user_college and user_college.strip() else "University"
        study = user_study if user_study and user_study.strip() else "Computer Science"

        if isinstance(links, (list, tuple)):
            clean_links = [str(l).strip() for l in links if str(l).strip()]
            link_list_text = "\n".join(f"- {l}" for l in clean_links) if clean_links else "No specific links provided."
        else:
            link_list_text = str(links) if links else "No specific links provided."

        role_title = job.get("role", "the role") if isinstance(job, dict) else "the role"
        company_name = job.get("company", "the team") if isinstance(job, dict) else "the team"
        domain = job.get("domain", "Technology") if isinstance(job, dict) else "Technology"
        focus_areas = ", ".join(job.get("key_focus_areas", [])) if isinstance(job, dict) and job.get("key_focus_areas") else "Core engineering & development"
        critical_reqs = ", ".join(job.get("critical_requirements", job.get("skills", []))) if isinstance(job, dict) else "Software Engineering"
        job_desc = job.get("description", str(job)) if isinstance(job, dict) else str(job)
        hiring_mgr = job.get("hiring_manager", "Hiring Team") if isinstance(job, dict) else "Hiring Team"

        clean_link = clean_links[0] if isinstance(links, (list, tuple)) and clean_links else ""
        link_mention = f" You can explore one of my relevant implementations here: {clean_link}." if clean_link else ""
        fallback_body = (
            f"Hi {company_name} Team,\n\n"
            f"I came across your {role_title} opening and was particularly drawn to your work in {domain}. "
            f"As a {position} with a background in {study} from {college}, my hands-on experience directly focuses on {critical_reqs}.{link_mention}\n\n"
            f"Given your focus on {focus_areas}, I would love the chance to discuss how I can contribute to your projects. "
            f"Would you be open to a brief 10-minute conversation next week?\n\n"
            f"Best regards,\n{user_name}"
        )

        if not self.has_valid_key or self.llm is None:
            offline_subjs = [
                f"{user_name} - {role_title} / {critical_reqs.split(',')[0]}",
                f"{role_title} inquiry - {user_name}",
                f"Quick question regarding {company_name}'s {role_title} role"
            ]
            return {
                "subject": offline_subjs[0],
                "subject_lines": offline_subjs,
                "body": fallback_body,
                "match_summary": f"Targeted candidate alignment around {critical_reqs}.",
                "key_highlights_used": [critical_reqs.split(",")[0]] if critical_reqs else ["Engineering"],
                "focus_areas_addressed": focus_areas
            }

        prompt_email = PromptTemplate.from_template(
            """### TARGET ROLE & COMPANY CONTEXT:
Job Title: {role}
Company: {company}
Industry / Domain: {domain}
Key Focus Areas: {focus_areas}
Critical Must-Have Requirements: {critical_reqs}
Job Description Overview:
{job_desc}
Addressed Recruiter/Team: {hiring_mgr}

### CANDIDATE PROFILE & VERIFIED EVIDENCE:
- Candidate Name: {user_name}
- Career Level: {candidate_type} (e.g. Student, Recent Graduate, Experienced)
- Current Role / Headline: {user_position}
- Education: {user_study} at {user_college}
- Candidate Background & CV Highlights:
{cv_highlights}

### CANDIDATE PROJECT & PORTFOLIO LINKS (EMBED RELEVANT ONES ONLY):
{link_list}

### EMAIL CONFIGURATION:
- Tone: {tone}
- Desired Length: 120-180 words (concise, sharp, and respectful of the recruiter's time)
- Custom Candidate Angle: {custom_instructions}

### CRITICAL HUMAN-WRITTEN COPYWRITING RULES:
1. NEVER USE FIXED TEMPLATES OR SWAP NAMES INTO A SCRIPT. Each company and tech stack must get a completely unique email.
2. ABSOLUTELY FORBIDDEN AI CLICHÉS AND BANNED PHRASES:
   - DO NOT write: "I am writing to express my interest in..."
   - DO NOT write: "I am thrilled to apply" / "I am excited to apply"
   - DO NOT write: "esteemed company" / "prestigious organization"
   - DO NOT write: "I believe I am an ideal candidate" / "perfect fit"
   - DO NOT write: "I am confident that my skills align"
   - DO NOT write: "I would be a valuable asset"
   - DO NOT write: "Dear Hiring Manager," (start with "Hi {company} Team," or "Hi {hiring_mgr},")
   - Avoid excessive corporate buzzwords, generic flattery, or dramatic adjectives.
3. TAILORED, NATURAL OPENING:
   - Start with a natural, conversational hook referencing specific technical work, product challenges, or team initiatives from the job posting.
   - Example openers:
     * "I noticed {company}'s {role} opening and was particularly drawn to your focus on {focus_areas}."
     * "I saw your team is building {domain} infrastructure and wanted to reach out regarding the {role} position."
4. GROUNDED IN REAL EVIDENCE:
   - Identify 2-3 genuine focus areas in the job description. Connect them directly to the candidate's actual projects, tools, and background.
   - Mention specific technologies, tools, and concrete project outcomes from the candidate's CV.
   - Do NOT invent or claim experience the candidate does not have.
   - Weave relevant portfolio links seamlessly into the prose (e.g., "I recently built a project addressing this: [Link]").
5. NATURAL HUMAN VOICE & CONCISENESS:
   - Sound like a real person ({candidate_type}). Simple, confident, articulate English.
   - Use short paragraphs (2-3 sentences each).
   - Total email body length MUST be around 120-180 words.
6. LOW-FRICTION CALL TO ACTION:
   - Close with a polite, casual next step (e.g., "Would you be open to a brief 10-minute chat next week?" or "Happy to share my code repository or provide additional details if helpful.").
   - Sign off naturally with {user_name}.

Return ONLY a valid JSON object matching the requested schema.

### JSON OUTPUT SCHEMA:
{{
  "subject_lines": ["Subject 1 (Tailored)", "Subject 2 (Value-driven)", "Subject 3 (Curiosity/Direct)"],
  "body": "Complete email text",
  "match_summary": "1-2 sentences on why this specific outreach connects with their needs",
  "key_highlights_used": ["Skill/Project 1", "Skill/Project 2"],
  "focus_areas_addressed": "Summary of specific job needs addressed"
}}

### VALID JSON:"""
        )

        chain_email = prompt_email | self.llm
        cv_summary = (cv_text[:2500] if cv_text else "") or (f"Portfolio Tech: {link_list_text}\nRole: {position}\nStudy: {study}")

        res = chain_email.invoke({
            "role": role_title,
            "company": company_name,
            "domain": domain,
            "focus_areas": focus_areas,
            "critical_reqs": critical_reqs,
            "job_desc": job_desc[:2000],
            "hiring_mgr": hiring_mgr,
            "user_name": user_name,
            "candidate_type": candidate_type,
            "user_position": position,
            "user_study": study,
            "user_college": college,
            "cv_highlights": cv_summary,
            "link_list": link_list_text,
            "tone": tone,
            "custom_instructions": custom_instructions or "None"
        })

        try:
            json_parser = JsonOutputParser()
            parsed = json_parser.parse(res.content)
            if isinstance(parsed, dict) and "body" in parsed:
                subjs = parsed.get("subject_lines") or []
                if not isinstance(subjs, list) or not subjs:
                    if parsed.get("subject"):
                        subjs = [parsed["subject"]]
                    else:
                        subjs = [f"{role_title} inquiry - {user_name}"]
                parsed["subject_lines"] = subjs
                parsed["subject"] = subjs[0]
                return parsed
        except Exception:
            pass

        raw_text = res.content.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        import json
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict) and "body" in parsed:
                subjs = parsed.get("subject_lines") or []
                if not isinstance(subjs, list) or not subjs:
                    if parsed.get("subject"):
                        subjs = [parsed["subject"]]
                    else:
                        subjs = [f"{role_title} inquiry - {user_name}"]
                parsed["subject_lines"] = subjs
                parsed["subject"] = subjs[0]
                return parsed
        except Exception:
            pass

        fallback_subjects = [
            f"{user_name} - {role_title} / {domain}",
            f"{role_title} inquiry - {user_name}",
            f"Quick note regarding {company_name}'s {role_title} position"
        ]
        return {
            "subject": fallback_subjects[0],
            "subject_lines": fallback_subjects,
            "body": raw_text if len(raw_text) > 40 else fallback_body,
            "match_summary": f"Tailored outreach targeting {company_name}'s {role_title} role.",
            "key_highlights_used": [critical_reqs.split(",")[0]] if critical_reqs else ["Engineering"],
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
        Classifies requirements into MATCHED, PARTIALLY MATCHED, MISSING, and NOT RELEVANT.
        Applies mathematical weighted scoring grounded in verified CV evidence.
        """
        job_reqs = str(job)
        cv_evidence_text = (cv_text[:8000] if cv_text else "") or portfolio_summary
        pre_noise = job.get("irrelevant_noise", []) if isinstance(job, dict) else []

        # Step 1: Pre-Audit candidate CV against all extracted requirements
        all_reqs = []
        if isinstance(job, dict):
            for r in job.get("critical_requirements", []):
                all_reqs.append({"req": r, "imp": "Critical requirement"})
            for r in job.get("preferred_requirements", []):
                all_reqs.append({"req": r, "imp": "Preferred requirement"})
            for r in job.get("soft_skills", []):
                all_reqs.append({"req": r, "imp": "Soft skill"})
            if not all_reqs and "skills" in job:
                for r in job.get("skills", []):
                    all_reqs.append({"req": r, "imp": "Critical requirement"})

        pre_audited_lines = []
        heuristic_breakdown = []
        for r_obj in all_reqs:
            req_name = r_obj["req"]
            status, quote, conf = find_cv_evidence(req_name, cv_evidence_text)
            pre_audited_lines.append(f"- [{r_obj['imp']}] {req_name} -> Verified Status: {status} | Evidence: {quote}")
            heuristic_breakdown.append({
                "requirement": req_name,
                "importance": r_obj["imp"],
                "status": status,
                "candidate_evidence": quote,
                "explanation": f"Verified via direct CV and portfolio scan ({conf} confidence).",
                "confidence": conf
            })

        for n in pre_noise:
            heuristic_breakdown.append({
                "requirement": n,
                "importance": "Irrelevant/Noise",
                "status": "NOT RELEVANT",
                "candidate_evidence": "Filtered out by ATS shield.",
                "explanation": "Out-of-scope requirement excluded from candidate scoring.",
                "confidence": "High"
            })

        pre_audit_text = "\n".join(pre_audited_lines) if pre_audited_lines else "No structured requirements provided."

        if not self.has_valid_key or self.llm is None:
            # High-accuracy dynamic fallback computed directly from candidate's CV
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

### INSTRUCTIONS:
You are an expert, objective talent assessment and ATS intelligence engine.
Perform a strict, EVIDENCE-BASED candidate-to-job fit and gap analysis.

RULES:
1. DO NOT FORCE MATCHES:
   - Never invent or assume a connection between the CV and job requirements.
   - For every requirement, classify it into EXACTLY ONE of:
     * `MATCHED`: Verified concrete evidence in candidate's CV/portfolio.
     * `PARTIALLY MATCHED`: Candidate has related foundation, coursework, or adjacent skill, but lacks the requested years of experience, production scale, or enterprise depth. You MUST explain why it is partial.
     * `MISSING`: Genuinely required by the job, but completely absent from candidate's profile.
     * `NOT RELEVANT`: Boilerplate, legal disclaimers, or random unrelated text (e.g., "experience in marine biology" for a Python backend role).
2. EXPERIENCE LEVEL SENSITIVITY:
   - If the job demands 5+ years of senior production experience and the candidate is a student/junior with project experience, mark as `PARTIALLY MATCHED` (skill present, but seniority/experience gap exists).
3. FILTER IRRELEVANT NOISE:
   - Any random or boilerplate requirements identified as `NOT RELEVANT` must have ZERO weight and must NOT lower the score or appear as critical skill gaps.
4. WEIGHTED SCORING CALCULATION:
   - Critical Requirements (core technical must-haves): 65% of score weight.
   - Preferred Requirements (nice-to-haves): 25% of score weight.
   - Soft Skills (collaboration/communication): 10% of score weight.
   - Noise / Irrelevant: 0% weight.
   - Calculate `match_score` as a realistic integer between 15 and 98 based on weighted achievement.
   - Assign `fit_level`:
     * 85-98: "Excellent Match (85%+)"
     * 70-84: "Strong Match (70-84%)"
     * 50-69: "Moderate Fit / High Potential (50-69%)"
     * Below 50: "Early Career / Significant Skill Gaps (<50%)"

### PRE-AUDITED EVIDENCE DISCOVERED IN CANDIDATE CV:
{pre_audited_evidence}

Return ONLY a valid JSON object matching the schema below.

### JSON OUTPUT SCHEMA:
{{
  "match_score": 75,
  "fit_level": "Strong Match (70-84%)",
  "matched_strengths": ["Top 3-5 verified strengths with candidate evidence"],
  "skill_gaps": ["Top 2-4 genuine critical missing requirements"],
  "strategic_advice": "2-3 sentences of strategic advice on how the candidate should address gaps in their email and interviews",
  "evidence_breakdown": [
    {{
      "requirement": "Name of requirement or skill",
      "importance": "Critical requirement | Preferred requirement | Soft skill | Irrelevant/Noise",
      "status": "MATCHED | PARTIALLY MATCHED | MISSING | NOT RELEVANT",
      "candidate_evidence": "Exact quote or proof from candidate profile (or 'No evidence found in CV')",
      "explanation": "Why this status was assigned",
      "confidence": "High | Medium | Low"
    }}
  ],
  "noise_filtered": ["List of any irrelevant/noise items ignored during evaluation"]
}}

### VALID JSON:"""
        )

        try:
            chain_fit = prompt_fit | self.llm
            res = chain_fit.invoke({
                "job_details": job_reqs[:4000],
                "user_name": user_name,
                "user_position": user_position,
                "user_study": user_study,
                "candidate_type": candidate_type,
                "candidate_evidence": cv_evidence_text[:8000],
                "pre_audited_evidence": pre_audit_text
            })

            try:
                json_parser = JsonOutputParser()
                parsed = json_parser.parse(res.content)
                if isinstance(parsed, dict) and "evidence_breakdown" in parsed:
                    audit_meta = audit_and_calculate_score(parsed["evidence_breakdown"])
                    parsed["match_score"] = audit_meta["mathematical_score"]
                    parsed["fit_level"] = audit_meta["fit_level"]
                    parsed["audit_meta"] = audit_meta
                    return parsed
            except Exception:
                pass

            raw_text = res.content.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            import json
            try:
                parsed = json.loads(raw_text)
                if isinstance(parsed, dict) and "evidence_breakdown" in parsed:
                    audit_meta = audit_and_calculate_score(parsed["evidence_breakdown"])
                    parsed["match_score"] = audit_meta["mathematical_score"]
                    parsed["fit_level"] = audit_meta["fit_level"]
                    parsed["audit_meta"] = audit_meta
                    return parsed
            except Exception:
                pass
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


