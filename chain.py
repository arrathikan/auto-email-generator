import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException

load_dotenv()


class Chain:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("API_KEY"),
            temperature=0
        )

    def extract_jobs(self, clean_text):
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}

            ### INSTRUCTION:
            The scraped text is from the career's page of a website.
            Your job is to extract the job postings and return them in JSON format containing
            the following keys: `role`, `experience`, `skills`, and `description`.
            Only return the valid JSON.

            ### VALID JSON (NO PREAMBLE):"""
        )

        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke({"page_data": clean_text})

        try:
            json_parser = JsonOutputParser()
            json_res = json_parser.parse(res.content)
            return json_res if isinstance(json_res, list) else [json_res]
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")

    def extract_portfolio_data(self, raw_cv_text):
        prompt_parse_cv = PromptTemplate.from_template(
            """
            ### RAW CV TEXT:
            {cv_text}

            ### INSTRUCTION:
            The text above is from a candidate's CV. Your job is to extract the candidate's core technical skills (Techstack) and relevant project links (Links).
            Return the result as a single valid JSON array containing objects. Each object must have two keys: `Techstack` and `Links`.

            - `Techstack`: A comma-separated string of related technical skills for a specific project/area.
            - `Links`: The exact, full URL of the project or certification related to the skills.

            Example of required format:
            [
              {{"Techstack": "Python, TensorFlow, Keras, CNNs", "Links": "https://github.com/user/project1"}},
              {{"Techstack": "SQL, Tableau, Data Cleaning, ETL", "Links": "https://linkedin.com/in/user/dataproject"}}
            ]

            ### VALID JSON ARRAY (NO PREAMBLE):"""
        )

        chain_parse = prompt_parse_cv | self.llm
        res = chain_parse.invoke({"cv_text": raw_cv_text})

        try:
            json_parser = JsonOutputParser()
            json_res = json_parser.parse(res.content)
            if isinstance(json_res, list):
                return json_res
            else:
                return [json_res]
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse portfolio data from CV.")

    def write_mail(
        self,
        job,
        links,
        user_name,
        user_college: str | None = None,
        user_study: str | None = None,
        user_possition: str | None = None,
    ):
        """
        user_college, user_study, user_possition are optional.
        If not provided, they default to "N/A".
        NOTE: 'user_possition' keeps your original spelling to avoid breaking other code.
        """

        # Prepare safe defaults
        user_college = user_college or "N/A"
        user_study = user_study or "N/A"
        user_possition = user_possition or "N/A"

        # Format link list nicely if a list/tuple is provided
        if isinstance(links, (list, tuple)):
            # join with newlines so the LLM sees them clearly
            link_list_text = "\n".join(map(str, links))
        else:
            link_list_text = str(links)

        prompt_email = PromptTemplate.from_template(
            """### JOB DESCRIPTION:
            {job_description}

            ### INSTRUCTION:
            You are {user_name}, a student of the {user_college}, . 
            You are currently studying {user_study} and now you are a {user_possition}.

            Your job is to write a professional email to the client regarding the job mentioned above, 
            explaining how your academic background and skills can contribute to fulfilling their needs. 
            Also add the most relevant ones from the following links to showcase related portfolio work:
            {link_list}

            Do not provide a preamble.

            ### EMAIL (NO PREAMBLE):"""
        )

        chain_email = prompt_email | self.llm
        res = chain_email.invoke({
            "job_description": str(job),
            "link_list": link_list_text,
            "user_name": user_name,
            "user_college": user_college,
            "user_study": user_study,
            "user_possition": user_possition
        })
        return res.content
