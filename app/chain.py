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

class Chain:
    def __init__(self, model_name: str = "openai/gpt-oss-120b", api_key: str | None = None, temperature: float = 0.2):
        resolved_key = api_key or os.getenv("API_KEY") or os.getenv("GROQ_API_KEY")
        if not resolved_key:
            resolved_key = "dummy_key"
        
        self.model_name = model_name if model_name in SUPPORTED_MODELS or "/" in model_name else "openai/gpt-oss-120b"
        self.api_key = resolved_key
        self.temperature = temperature
        self._init_llm()

    def _init_llm(self):
        self.llm = ChatGroq(
            model=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature
        )

    def update_config(self, model_name: str | None = None, api_key: str | None = None, temperature: float | None = None):
        if model_name:
            self.model_name = model_name
        if api_key:
            self.api_key = api_key
        if temperature is not None:
            self.temperature = temperature
        self._init_llm()

    def extract_jobs(self, clean_text: str):
        prompt_extract = PromptTemplate.from_template(
            """### SCRAPED TEXT OR JOB POSTING:
{page_data}

### INSTRUCTION:
The text above is from a job opening / careers page or job description.
Extract all distinct job postings and return them as a valid JSON array of objects.
Each object must have the following keys:
- `role`: The exact job title (e.g. "Senior Python Engineer")
- `company`: Name of hiring company (if available, else "the company")
- `contact_email`: The recruiter, HR, or application email address if mentioned (e.g. "careers@company.com" or "jobs@startup.io"), otherwise ""
- `experience`: Required experience level / years (e.g. "2+ years", "Entry Level", or "Not specified")
- `skills`: A list of strings of the top 4-8 required technical & professional skills
- `description`: A 2-3 sentence summary of the key responsibilities and mission of this role
- `hiring_manager`: Name or title of recruiter/manager if mentioned, otherwise "Hiring Team"

Return ONLY valid JSON with no conversational preamble or markdown code fences outside JSON.

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

    def write_mail(
        self,
        job,
        links,
        user_name: str,
        user_college: str | None = None,
        user_study: str | None = None,
        user_position: str | None = None,
        user_possition: str | None = None,
        tone: str = "Professional & Persuasive",
        length: str = "Standard (200-250 words)",
        candidate_type: str = "Student / Recent Graduate",
        custom_instructions: str = ""
    ):
        position = user_position or user_possition or "Candidate"
        college = user_college if user_college and user_college.strip() else "University"
        study = user_study if user_study and user_study.strip() else "Computer Science & Software"

        if isinstance(links, (list, tuple)):
            clean_links = [str(l).strip() for l in links if str(l).strip()]
            link_list_text = "\n".join(f"- {l}" for l in clean_links) if clean_links else "No specific links provided."
        else:
            link_list_text = str(links) if links else "No specific links provided."

        prompt_email = PromptTemplate.from_template(
            """### TARGET JOB DETAILS:
{job_description}

### CANDIDATE PROFILE:
- Name: {user_name}
- Candidate Status / Level: {candidate_type}
- Role / Headline: {user_position}
- Academic Institution / Background: {user_college}
- Degree / Specialization: {user_study}

### RELEVANT PORTFOLIO & PROJECT LINKS TO INCLUDE:
{link_list}

### EMAIL STYLE & CONFIGURATION:
- Desired Tone: {tone}
- Desired Length: {length}
- Special Custom Instructions: {custom_instructions}

### INSTRUCTIONS:
1. Act as an expert cold outreach copywriter who writes emails that get replies from hiring managers and founders.
2. Generate a JSON response with:
   - `subject_lines`: An array of 3 distinct, compelling, high-converting email subject lines (e.g. tailored, curiosity-inducing, value-driven).
   - `body`: The complete, ready-to-send email body.
   - `match_summary`: A concise 1-2 sentence explanation of why the candidate is a strong fit.
   - `key_highlights_used`: An array of the top 3-4 skills/projects highlighted in the email.

3. Formatting guidelines for `body`:
   - Start directly with a warm greeting to the hiring manager/team.
   - Introduce the candidate briefly ({user_name}, {user_position} with background in {user_study} at {user_college}).
   - Directly hook the recipient by addressing their specific job needs.
   - Seamlessly embed the relevant portfolio links with natural context (e.g., "You can see my recent implementation here: [URL]").
   - Include a low-friction Call to Action (e.g. "Would you be open to a brief 10-minute chat this Thursday?").
   - Close professionally with {user_name}'s sign-off.
   - Do NOT include placeholders like [Company Name] if company is known; use actual job details.

Return ONLY a valid JSON object.

### JSON OUTPUT:"""
        )

        chain_email = prompt_email | self.llm
        res = chain_email.invoke({
            "job_description": str(job),
            "link_list": link_list_text,
            "user_name": user_name,
            "user_college": college,
            "user_study": study,
            "user_position": position,
            "tone": tone,
            "length": length,
            "candidate_type": candidate_type,
            "custom_instructions": custom_instructions or "None"
        })

        try:
            json_parser = JsonOutputParser()
            parsed = json_parser.parse(res.content)
            if isinstance(parsed, dict) and "body" in parsed:
                return parsed
        except Exception:
            pass

        raw_text = res.content.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        return {
            "subject_lines": [
                f"Application for {job.get('role', 'Opportunity')} - {user_name}",
                f"{user_name} - {job.get('role', 'Role')} Portfolio & Background",
                f"Quick question regarding {job.get('role', 'Role')} at {job.get('company', 'your team')}"
            ] if isinstance(job, dict) else [f"Opportunity Inquiry - {user_name}"],
            "body": raw_text,
            "match_summary": "Tailored application email matched with candidate portfolio.",
            "key_highlights_used": job.get("skills", []) if isinstance(job, dict) else []
        }

    def analyze_job_fit(self, job: dict, portfolio_summary: str, user_name: str, user_position: str, user_study: str):
        """
        Analyzes candidate profile & portfolio against job requirements to calculate
        match score, matched strengths, missing keywords, and strategic interview/email advice.
        """
        prompt_fit = PromptTemplate.from_template(
            """### TARGET JOB DETAILS:
{job_details}

### CANDIDATE PROFILE & PORTFOLIO:
- Candidate: {user_name} ({user_position})
- Background / Education: {user_study}
- Portfolio & Tech Stack:
{portfolio_summary}

### INSTRUCTIONS:
Perform a deep candidate-to-job fit evaluation.
Return a valid JSON object with the following exact keys:
- `match_score`: An integer between 40 and 98 representing the overall fit percentage.
- `fit_level`: String: "Excellent Match (85%+)", "Strong Match (70-84%)", or "Moderate / High Potential (50-69%)".
- `matched_strengths`: Array of strings (top 3-5 specific strengths & skills that directly match the role).
- `skill_gaps`: Array of strings (top 2-4 missing keywords, requirements, or nice-to-haves from the job description).
- `strategic_advice`: A 2-3 sentence strategic recommendation explaining how the candidate should position themselves in the email and interviews to bridge any skill gaps.

Return ONLY valid JSON.

### JSON OUTPUT:"""
        )

        chain_fit = prompt_fit | self.llm
        res = chain_fit.invoke({
            "job_details": str(job),
            "portfolio_summary": portfolio_summary,
            "user_name": user_name,
            "user_position": user_position,
            "user_study": user_study
        })

        try:
            json_parser = JsonOutputParser()
            parsed = json_parser.parse(res.content)
            if isinstance(parsed, dict) and "match_score" in parsed:
                return parsed
        except Exception:
            pass

        # Fallback
        return {
            "match_score": 85,
            "fit_level": "Strong Match (70-84%)",
            "matched_strengths": job.get("skills", ["Python", "Machine Learning", "System Design"])[:4],
            "skill_gaps": ["Domain-specific toolsets", "Advanced production telemetry"],
            "strategic_advice": f"Emphasize your hands-on project portfolio in {user_position} and your ability to rapidly ramp up on any specialized internal tools."
        }

    def write_followup_mail(self, job: dict, user_name: str, days_since: int = 4):
        """
        Generates a concise, polite follow-up email for an existing application.
        """
        prompt_followup = PromptTemplate.from_template(
            """### JOB DETAILS:
Role: {role}
Company: {company}
Candidate Name: {user_name}
Days Since Initial Outreach: {days_since} days

### INSTRUCTION:
Write a polite, concise, and high-impact follow-up email.
1. Mention that you reached out a few days ago regarding the {role} position.
2. Reiterate your excitement and highlight one strong reason why you can add immediate value.
3. Keep it under 100 words.
4. Include a courteous call to action.

Return a valid JSON object with:
- `subject`: The follow-up subject line (e.g. "Following up: {role} - {user_name}")
- `body`: The email text.

### JSON:"""
        )

        chain_follow = prompt_followup | self.llm
        res = chain_follow.invoke({
            "role": job.get("role", "the role"),
            "company": job.get("company", "your team"),
            "user_name": user_name,
            "days_since": days_since
        })

        try:
            json_parser = JsonOutputParser()
            parsed = json_parser.parse(res.content)
            if isinstance(parsed, dict) and "body" in parsed:
                return parsed
        except Exception:
            pass

        return {
            "subject": f"Following up: {job.get('role', 'Application')} - {user_name}",
            "body": f"Hi Hiring Team,\n\nI hope you're having a great week! I'm following up on my application for the {job.get('role', 'open')} role at {job.get('company', 'your company')} that I sent a few days ago.\n\nI remains very excited about the mission and would love the opportunity to briefly connect.\n\nBest regards,\n{user_name}"
        }
