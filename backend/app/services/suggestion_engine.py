import uuid
from typing import Dict, List, Any

class SuggestionEngine:
    @classmethod
    def aggregate_findings(
        cls,
        section_info: Dict[str, Any],
        bullet_evaluations: List[Dict[str, Any]],
        grammar_info: Dict[str, Any],
        ats_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Consolidates and prioritizes findings across all analysis engines.
        """
        all_findings: List[Dict[str, Any]] = []

        # 1. Section & Structural Findings
        for missing in section_info.get("missing_sections", []):
            sec_name = missing["section"].replace("_", " ").title()
            severity = "error" if missing["importance"] == "critical" else "missing"
            all_findings.append({
                "id": f"sec-{uuid.uuid4().hex[:8]}",
                "type": severity,
                "category": "structure",
                "title": f"Missing Section: {sec_name}",
                "location": f"Structure: {sec_name}",
                "explanation": missing["message"],
                "original_snippet": f"Section '{sec_name}' absent from document",
                "proposed_correction": f"Insert a clearly headed '{sec_name}' section.",
                "status": "pending",
            })

        for contact_issue in section_info.get("contact_issues", []):
            all_findings.append({
                "id": f"contact-{uuid.uuid4().hex[:8]}",
                "type": "error",
                "category": "formatting",
                "title": "Contact Information Defect",
                "location": "Header: Contact Information",
                "explanation": contact_issue,
                "original_snippet": "Incomplete contact block",
                "proposed_correction": "Provide a complete email, phone number, and location at the very top of your resume.",
                "status": "pending",
            })

        if section_info.get("section_order_status") == "unusual":
            all_findings.append({
                "id": f"order-{uuid.uuid4().hex[:8]}",
                "type": "improvement",
                "category": "structure",
                "title": "Unconventional Section Hierarchy",
                "location": "Full Document",
                "explanation": section_info.get("section_order_message", ""),
                "original_snippet": "Section order: Contact placed late",
                "proposed_correction": "Reorder sections to place Contact Information first, followed by Summary, Education/Experience, Skills, and Projects.",
                "status": "pending",
            })

        # 2. Bullet Point Findings
        for idx, bullet in enumerate(bullet_evaluations):
            if bullet.get("issues"):
                all_findings.append({
                    "id": f"bullet-{idx+1}-{uuid.uuid4().hex[:6]}",
                    "type": bullet.get("severity", "improvement"),
                    "category": "impact",
                    "title": f"Action Impact in {bullet.get('section', 'Experience').title()}",
                    "location": f"Section: {bullet.get('section', 'Experience').title()}",
                    "explanation": " • ".join(bullet["issues"]),
                    "original_snippet": bullet.get("original_snippet", ""),
                    "proposed_correction": bullet.get("suggested_rewrite", ""),
                    "status": "pending",
                })

        # 3. Grammar & Style Findings
        for item in grammar_info.get("issues", []):
            all_findings.append({
                "id": f"style-{uuid.uuid4().hex[:8]}",
                "type": item["type"],
                "category": item.get("category", "style"),
                "title": item["title"],
                "location": item["location"],
                "explanation": item["explanation"],
                "original_snippet": item["original_snippet"],
                "proposed_correction": item["proposed_correction"],
                "status": "pending",
            })

        # 4. ATS & Keyword Findings
        for item in ats_info.get("issues", []):
            all_findings.append({
                "id": f"ats-{uuid.uuid4().hex[:8]}",
                "type": item["type"],
                "category": item.get("category", "formatting"),
                "title": item["title"],
                "location": item["location"],
                "explanation": item["explanation"],
                "original_snippet": item["original_snippet"],
                "proposed_correction": item["proposed_correction"],
                "status": "pending",
            })

        # Priority Sort: error -> improvement -> missing -> keyword
        priority_map = {"error": 1, "improvement": 2, "missing": 3, "keyword": 4}
        all_findings.sort(key=lambda x: priority_map.get(x["type"], 5))

        return all_findings

suggestion_engine = SuggestionEngine()
