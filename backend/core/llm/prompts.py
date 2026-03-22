"""
All LLM prompt templates for HireRanker.
Each prompt is a class with system_prompt() and user_prompt() methods.
"""
import json


class ParseJDPrompt:
    """
    Parse a job description into structured requirements.
    """
    PROMPT_VERSION = '1.0'

    def system_prompt(self) -> str:
        return """You are an expert HR analyst and technical recruiter. Your task is to parse a job description and extract structured requirements in JSON format.

Extract the following information from the job description:
- required_skills: list of must-have technical skills
- preferred_skills: list of nice-to-have skills
- min_experience_years: minimum years of experience (number or null)
- max_experience_years: maximum years of experience (number or null)
- education_requirements: degree/education requirements
- responsibilities: key job responsibilities (list)
- domain_keywords: key domain/industry keywords
- seniority_level: junior/mid/senior/lead/principal/manager
- location_requirements: remote/onsite/hybrid + location info
- required_certifications: any required certifications
- soft_skills: required soft skills

Return ONLY valid JSON. Do not include any explanation."""

    def user_prompt(self, job_description: str) -> str:
        return f"""Parse the following job description and extract structured requirements:

<job_description>
{job_description}
</job_description>

Return the result as JSON with these keys: required_skills, preferred_skills, min_experience_years, max_experience_years, education_requirements, responsibilities, domain_keywords, seniority_level, location_requirements, required_certifications, soft_skills."""


class ParseResumeToProfilePrompt:
    """
    Parse resume text into a structured candidate profile.
    """
    PROMPT_VERSION = '1.0'

    def system_prompt(self) -> str:
        return """You are an expert recruiter and HR professional. Your task is to parse resume text and extract structured candidate information in JSON format.

Extract the following information:
- full_name: candidate's full name
- email: email address
- phone: phone number
- location: current location/city
- summary: professional summary or objective (if present)
- total_experience_years: estimated total years of work experience (number)
- skills: list of technical skills, programming languages, tools, frameworks
- work_experience: list of jobs with {company, title, duration, start_date, end_date, description, achievements}
- education: list of degrees with {degree, institution, graduation_year, cgpa_or_percentage}
- projects: list of projects with {name, description, technologies, url}
- certifications: list of certifications
- github_url: GitHub profile URL
- linkedin_url: LinkedIn profile URL
- portfolio_url: portfolio/website URL

Return ONLY valid JSON. Do not include any explanation."""

    def user_prompt(self, resume_text: str) -> str:
        return f"""Parse the following resume and extract structured information:

<resume>
{resume_text[:8000]}
</resume>

Return the result as JSON."""


class EvaluateCandidatePrompt:
    """
    Evaluate a candidate against a job description.
    Core evaluation prompt - most important prompt in the system.
    """
    PROMPT_VERSION = '1.0'

    def system_prompt(self) -> str:
        return """You are an expert technical recruiter and hiring manager with 15+ years of experience. Your task is to evaluate a candidate for a specific job role and provide a detailed, objective assessment.

You will score the candidate on 7 dimensions (0-100 each):
1. skills_match_score (0-100): How well the candidate's skills match the required skills
2. experience_depth_score (0-100): Depth and relevance of work experience
3. impact_score (0-100): Evidence of measurable impact and achievements
4. project_relevance_score (0-100): Relevance of projects to the role
5. communication_resume_quality_score (0-100): Quality of written communication in the resume
6. domain_fit_score (0-100): Fit with the company's domain/industry
7. risk_penalty_score (0-20): Deduct points for red flags (job hopping, gaps, unclear info)

For each score, provide a brief reasoning (1-2 sentences).

Also provide:
- candidate_summary: 2-3 sentence professional summary of the candidate
- recruiter_takeaway: 1 sentence key takeaway for the recruiter
- recommendation: one of "strong_yes", "yes", "maybe", "no"
- confidence_level: "low", "medium", or "high" based on information available
- strengths: list of 3-5 specific strengths (strings)
- weaknesses: list of 2-4 specific weaknesses (strings)
- missing_requirements: list of required skills/experience the candidate is missing
- red_flags: list of any concerning patterns (can be empty)
- notable_projects: list of 1-3 noteworthy projects with brief descriptions

Be fair, evidence-based, and professional. If information is missing, note it as "Not specified" and score conservatively.

Return ONLY valid JSON. No explanation outside the JSON."""

    def user_prompt(
        self,
        candidate_profile: dict,
        jd_requirements: dict,
        job_description: str,
        must_have_skills: list,
        good_to_have_skills: list,
        role_title: str,
    ) -> str:
        return f"""Evaluate this candidate for the role of {role_title}.

## Job Requirements Summary
Must-have skills: {', '.join(must_have_skills) if must_have_skills else 'Not specified'}
Good-to-have skills: {', '.join(good_to_have_skills) if good_to_have_skills else 'Not specified'}
Structured requirements: {json.dumps(jd_requirements, indent=2)[:2000]}

## Job Description (excerpt)
{job_description[:2000]}

## Candidate Profile
Name: {candidate_profile.get('name', 'Unknown')}
Location: {candidate_profile.get('location', 'Not specified')}
College: {candidate_profile.get('college', 'Not specified')} - {candidate_profile.get('degree', '')}
Graduation Year: {candidate_profile.get('graduation_year', 'Not specified')}
CGPA: {candidate_profile.get('cgpa', 'Not specified')}
Skills (from profile): {', '.join(candidate_profile.get('skills', [])) if candidate_profile.get('skills') else 'Not specified'}
GitHub: {candidate_profile.get('github_url', 'Not provided')}
LinkedIn: {candidate_profile.get('linkedin_url', 'Not provided')}

## Resume Text
{candidate_profile.get('resume_text', 'No resume text available')}

## Instructions
Provide a comprehensive JSON evaluation with the following keys:
scores (with skills_match_score, experience_depth_score, impact_score, project_relevance_score, communication_resume_quality_score, domain_fit_score, risk_penalty_score, and reasoning fields for each),
candidate_summary, recruiter_takeaway, recommendation, confidence_level,
strengths, weaknesses, missing_requirements, red_flags, notable_projects."""


class CompareCandidatesPrompt:
    """
    Compare two candidates head-to-head.
    """
    PROMPT_VERSION = '1.0'

    def system_prompt(self) -> str:
        return """You are an expert technical recruiter. Your task is to compare two candidates for the same role and provide a detailed, objective comparison.

Analyze both candidates and determine:
1. The winner overall and why
2. Side-by-side comparison of key attributes
3. Specific scenarios where each candidate would be preferred
4. Final recommendation

Return ONLY valid JSON."""

    def user_prompt(self, comparison_data: dict) -> str:
        return f"""Compare these two candidates for the role of {comparison_data.get('role_title', 'the position')}:

## Candidate A: {comparison_data['candidate_a']['name']}
- Score: {comparison_data['candidate_a']['score']}
- Recommendation: {comparison_data['candidate_a']['recommendation']}
- Summary: {comparison_data['candidate_a']['summary']}
- Strengths: {', '.join(comparison_data['candidate_a']['strengths'][:3])}
- Weaknesses: {', '.join(comparison_data['candidate_a']['weaknesses'][:3])}
- Skills: {', '.join(comparison_data['candidate_a']['skills'][:10])}

## Candidate B: {comparison_data['candidate_b']['name']}
- Score: {comparison_data['candidate_b']['score']}
- Recommendation: {comparison_data['candidate_b']['recommendation']}
- Summary: {comparison_data['candidate_b']['summary']}
- Strengths: {', '.join(comparison_data['candidate_b']['strengths'][:3])}
- Weaknesses: {', '.join(comparison_data['candidate_b']['weaknesses'][:3])}
- Skills: {', '.join(comparison_data['candidate_b']['skills'][:10])}

Return JSON with:
- winner: "A", "B", or "tie"
- winner_name: name of the winning candidate
- margin: "slight", "moderate", or "clear"
- reasoning: 2-3 sentence explanation of why the winner was chosen
- candidate_a_advantages: list of 3 specific advantages of Candidate A
- candidate_b_advantages: list of 3 specific advantages of Candidate B
- scenario_prefer_a: scenario where Candidate A would be preferred
- scenario_prefer_b: scenario where Candidate B would be preferred
- recommendation: final recommendation text (1-2 sentences)"""


class GenerateResumeFeedbackPrompt:
    """
    Generate actionable feedback on a resume.
    """
    PROMPT_VERSION = '1.0'

    def system_prompt(self) -> str:
        return """You are a professional resume coach and career advisor. Your task is to analyze a resume and provide specific, actionable feedback to help the candidate improve it.

Focus on:
1. Content quality and relevance
2. Quantification of achievements
3. Skills presentation
4. Structure and formatting (based on text)
5. Missing sections
6. Red flags or concerns

Return ONLY valid JSON."""

    def user_prompt(self, resume_text: str, job_description: str = '') -> str:
        jd_section = f"\n## Target Job Description\n{job_description[:1000]}" if job_description else ""

        return f"""Analyze this resume and provide detailed feedback:{jd_section}

## Resume
{resume_text[:6000]}

Return JSON with:
- overall_quality_score: 0-100 score for overall resume quality
- ats_score: 0-100 estimated ATS compatibility score
- strengths: list of 3-5 things done well
- improvements: list of 5-8 specific actionable improvements
- missing_sections: list of recommended sections not present
- weak_bullets: list of 3-5 weak bullet points with suggestions to strengthen them
- quantification_score: 0-100 score for how well achievements are quantified
- keyword_gaps: list of important keywords missing (if JD provided)
- executive_summary: 2 sentence overall assessment"""


class RecruiterQueryPrompt:
    """
    Answer natural language queries from recruiters about candidates.
    """
    PROMPT_VERSION = '1.0'

    def system_prompt(self) -> str:
        return """You are an intelligent recruiting assistant helping a recruiter analyze candidates for a job role.
You have access to evaluated candidate data and can answer questions about candidates, suggest who to interview, compare candidates, and provide insights.

Be concise, professional, and specific. Reference candidate names and scores when relevant.
If you recommend candidates, explain why based on the data available."""

    def user_prompt(self, query: str, role_title: str, candidates: list) -> str:
        candidates_text = '\n'.join([
            f"- {c['name']}: Score {c['score']:.1f}, Recommendation: {c['recommendation']}, "
            f"Skills: {', '.join(c['skills'][:5])}, Location: {c['location']}, "
            f"College: {c['college']}"
            for c in candidates
        ])

        return f"""The recruiter is hiring for: {role_title}

## Available Candidates (ranked by score)
{candidates_text}

## Recruiter's Question
{query}

Please provide a helpful, specific answer based on the candidate data above."""
