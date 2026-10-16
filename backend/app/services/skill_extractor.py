import re
from typing import Dict, List, Any, Set, Tuple

# Comprehensive curated skill taxonomy
SKILL_TAXONOMY: Dict[str, Dict[str, List[str]]] = {
    "languages": {
        "Python": ["python", "python3"],
        "JavaScript": ["javascript", "js", "ecmascript"],
        "TypeScript": ["typescript", "ts"],
        "Java": ["java"],
        "C++": ["c++", "cpp"],
        "C#": ["c#", "csharp", "c-sharp"],
        "Go": ["golang", "go language"],  # "go" disambiguated specially
        "Rust": ["rust", "rust-lang"],
        "SQL": ["sql", "t-sql", "pl/sql", "plsql"],
        "HTML/CSS": ["html", "html5", "css", "css3"],
        "PHP": ["php"],
        "Ruby": ["ruby"],
        "Swift": ["swift"],
        "Kotlin": ["kotlin"],
        "R": ["r programming", "r language"],  # "r" disambiguated specially
        "Bash/Shell": ["bash", "shell scripting", "zsh", "powershell"],
        "Scala": ["scala"],
    },
    "frameworks": {
        "React": ["react", "react.js", "reactjs"],
        "FastAPI": ["fastapi"],
        "Node.js": ["node.js", "nodejs", "node"],
        "Express.js": ["express.js", "expressjs"],
        "Django": ["django"],
        "Flask": ["flask"],
        "Next.js": ["next.js", "nextjs"],
        "Vue.js": ["vue", "vue.js", "vuejs"],
        "Angular": ["angular", "angularjs"],
        "Spring Boot": ["spring boot", "spring framework", "spring"],
        "Tailwind CSS": ["tailwind", "tailwindcss"],
        "Bootstrap": ["bootstrap"],
        "Redux": ["redux", "redux toolkit"],
        "GraphQL": ["graphql"],
        "ASP.NET": ["asp.net", ".net core", "dotnet"],
    },
    "databases": {
        "PostgreSQL": ["postgresql", "postgres"],
        "MySQL": ["mysql"],
        "MongoDB": ["mongodb", "mongo"],
        "Redis": ["redis"],
        "SQLite": ["sqlite", "sqlite3"],
        "Supabase": ["supabase"],
        "Oracle": ["oracle db", "oracle database"],
        "Cassandra": ["cassandra"],
        "DynamoDB": ["dynamodb"],
        "Elasticsearch": ["elasticsearch"],
    },
    "developer_tools": {
        "Git": ["git"],
        "GitHub": ["github"],
        "Docker": ["docker"],
        "Kubernetes": ["kubernetes", "k8s"],
        "AWS": ["aws", "amazon web services", "s3", "ec2", "lambda"],
        "Azure": ["azure", "microsoft azure"],
        "GCP": ["gcp", "google cloud platform", "google cloud"],
        "CI/CD": ["ci/cd", "continuous integration", "github actions", "jenkins", "gitlab ci"],
        "Linux": ["linux", "unix", "ubuntu"],
        "Terraform": ["terraform"],
        "Postman": ["postman"],
        "JIRA": ["jira"],
        "Vite": ["vite", "vitejs"],
        "Webpack": ["webpack"],
    },
    "ai_ml_data": {
        "PyTorch": ["pytorch"],
        "TensorFlow": ["tensorflow", "keras"],
        "Machine Learning": ["machine learning", "ml"],
        "Deep Learning": ["deep learning"],
        "Scikit-Learn": ["scikit-learn", "sklearn"],
        "Pandas": ["pandas"],
        "NumPy": ["numpy"],
        "Data Analysis": ["data analysis", "data analytics"],
        "NLP": ["natural language processing", "nlp"],
        "Computer Vision": ["computer vision", "opencv"],
        "LLMs": ["llm", "llms", "large language models"],
        "LangChain": ["langchain"],
    },
    "soft_skills": {
        "Team Leadership": ["leadership", "team lead", "led team", "mentoring"],
        "Agile / Scrum": ["agile", "scrum", "kanban", "sprints"],
        "Problem Solving": ["problem solving", "analytical skills"],
        "Cross-functional Collaboration": ["cross-functional", "stakeholder management"],
        "Code Review": ["code reviews", "peer reviews", "code review"],
        "Technical Writing": ["technical documentation", "api documentation", "technical writing"],
    },
}

# Special regex disambiguations for short/ambiguous words
SPECIAL_PATTERNS = {
    "Go": re.compile(r"\b(Golang|Go\s+language|Go\s+programming|\bGo\s*,\s*(Python|Java|Rust|C\+\+)|(Python|Java|Rust|C\+\+)\s*,\s*Go\b)\b"),
    "C": re.compile(r"\b(C\s+programming|C\s+language|C\s*[/,]\s*C\+\+|C\+\+\s*[/,]\s*C)\b"),
    "R": re.compile(r"\b(R\s+programming|R\s+language|Python\s*[/,]\s*R|R\s*[/,]\s*Python)\b"),
    "Express.js": re.compile(r"\b(Express\.js|Expressjs|Node(?:\.js)?\s*[/,]\s*Express|Express\s*[/,]\s*Node)\b", re.IGNORECASE),
}

class SkillExtractorService:
    @classmethod
    def extract_skills(
        cls,
        raw_text: str,
        sections: Dict[str, str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extracts verified skills from text and sections.
        Returns dictionary of categories mapped to lists of extracted skill details.
        """
        if not raw_text or not raw_text.strip():
            return {cat: [] for cat in SKILL_TAXONOMY.keys()}

        sections_dict = sections or {}
        skills_section_text = sections_dict.get("skills", "")
        all_lines = raw_text.splitlines()

        extracted_results: Dict[str, List[Dict[str, Any]]] = {
            cat: [] for cat in SKILL_TAXONOMY.keys()
        }
        seen_skills: Set[str] = set()

        for category, skill_map in SKILL_TAXONOMY.items():
            for canonical_name, aliases in skill_map.items():
                if canonical_name in seen_skills:
                    continue

                is_matched = False
                matched_snippet = ""
                matched_section = "general"
                occurrence_count = 0

                # 1. Check special ambiguous patterns first
                if canonical_name in SPECIAL_PATTERNS:
                    pat = SPECIAL_PATTERNS[canonical_name]
                    match = pat.search(raw_text)
                    if match:
                        is_matched = True
                        matched_snippet = cls._find_snippet_in_lines(match.group(0), all_lines)
                        occurrence_count = len(pat.findall(raw_text))

                # 2. General aliases matching
                if not is_matched:
                    for alias in aliases:
                        # Use word boundaries
                        # Escape special regex chars like ++ or # or .
                        escaped = re.escape(alias)
                        pattern = re.compile(rf"(?<![\w\#\+]){escaped}(?![\w\#\+]|\.(?=[a-zA-Z]))", re.IGNORECASE)

                        matches = list(pattern.finditer(raw_text))
                        if matches:
                            # Additional false-positive filter:
                            # E.g., if alias is "react", ensure it's not "react to" or "reacted"
                            if alias == "react":
                                if not cls._is_valid_react_mention(raw_text, skills_section_text):
                                    continue

                            is_matched = True
                            occurrence_count += len(matches)
                            if not matched_snippet:
                                matched_snippet = cls._find_snippet_in_lines(alias, all_lines)

                if is_matched:
                    seen_skills.add(canonical_name)
                    # Determine source section
                    if skills_section_text and canonical_name.lower() in skills_section_text.lower():
                        matched_section = "skills"
                    elif "projects" in sections_dict and canonical_name.lower() in sections_dict["projects"].lower():
                        matched_section = "projects"
                    elif "experience" in sections_dict and canonical_name.lower() in sections_dict["experience"].lower():
                        matched_section = "experience"

                    extracted_results[category].append({
                        "name": canonical_name,
                        "category": category,
                        "evidence_snippet": matched_snippet or f"Mentioned in resume ({canonical_name})",
                        "source_section": matched_section,
                        "occurrences": occurrence_count,
                    })

        return extracted_results

    @staticmethod
    def _is_valid_react_mention(text: str, skills_section: str) -> bool:
        """
        Guards against common English verb 'react' (e.g. 'react quickly to incidents').
        """
        # If in skills section, it's definitely React the UI library
        if skills_section and re.search(r"\breact(\.js)?\b", skills_section, re.IGNORECASE):
            return True
        # If preceded by or followed by web terms
        if re.search(r"\b(React\s*(Native|JS|\.js|Redux|Hooks|Components|Frontend|Developer|Framework))\b", text, re.IGNORECASE):
            return True
        if re.search(r"\b(with|using|built\s+in|built\s+with)\s+React\b", text):
            return True
        # Capitalized React in list of tech
        if re.search(r"\b(Python|Node|TypeScript|JavaScript|HTML|CSS|Vue|Angular)\s*,\s*React\b", text):
            return True
        return False

    @staticmethod
    def _find_snippet_in_lines(phrase: str, lines: List[str]) -> str:
        """
        Finds the line or sentence containing the matched phrase for evidence citation.
        """
        lower_phrase = phrase.lower()
        for line in lines:
            if lower_phrase in line.lower():
                cleaned = line.strip().lstrip("-*• ")
                return cleaned[:140] if len(cleaned) > 140 else cleaned
        return ""

skill_extractor = SkillExtractorService()
