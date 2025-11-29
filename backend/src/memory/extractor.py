"""
Memory Extractor - Extract structured information from CV/JD using LLM
"""
import fitz  # PyMuPDF
import os
import json
from typing import Dict, Optional
import google.generativeai as genai


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file using PyMuPDF
    """
    try:
        doc = fitz.open(file_path)
        text = "\n\n".join([page.get_text() for page in doc])
        doc.close()
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from text file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error extracting text from TXT: {e}")
        return ""


def get_gemini_model():
    """Get Gemini model instance"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')


def generate_cv_summary(cv_text: str) -> str:
    """
    Generate a concise CV summary using Gemini
    """
    if not cv_text:
        return None
    
    try:
        model = get_gemini_model()
        
        prompt = f"""Summarize this CV in 10-15 lines, highlighting:
- Professional background
- Key skills and expertise
- Years of experience
- Notable achievements or projects
- Education background

CV Content:
{cv_text[:4000]}

Summary:"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating CV summary: {e}")
        return None


def extract_cv_details(cv_text: str) -> Optional[Dict]:
    """
    Extract structured information from CV using Gemini
    Returns JSON with all key details
    """
    if not cv_text:
        return None
    
    try:
        model = get_gemini_model()
        
        prompt = f"""Extract structured information from this CV and return ONLY valid JSON (no markdown, no code blocks, just JSON):

{{
  "name": "",
  "email": "",
  "phone": "",
  "location": "",
  "total_experience_years": "",
  "current_role": "",
  "roles": [],
  "skills": {{
    "languages": [],
    "frameworks": [],
    "databases": [],
    "cloud_platforms": [],
    "tools": [],
    "other": []
  }},
  "projects": [
    {{
      "name": "",
      "description": "",
      "tech_stack": [],
      "impact": "",
      "duration": ""
    }}
  ],
  "education": {{
    "degree": "",
    "institution": "",
    "year": "",
    "field": ""
  }},
  "certifications": [],
  "strengths": [],
  "weaknesses": [],
  "domains": [],
  "achievements": [],
  "languages_spoken": []
}}

CV Content:
{cv_text[:6000]}

Return only the JSON object:"""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Parse JSON
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Error parsing CV JSON: {e}")
        print(f"Response was: {response.text[:500]}")
        return None
    except Exception as e:
        print(f"Error extracting CV details: {e}")
        return None


def generate_jd_summary(jd_text: str) -> str:
    """
    Generate a concise JD summary using Gemini
    """
    if not jd_text:
        return None
    
    try:
        model = get_gemini_model()
        
        prompt = f"""Summarize this job description in 10-15 lines, highlighting:
- Job title and role
- Key responsibilities
- Required experience level
- Must-have skills
- Company/team context

Job Description:
{jd_text[:4000]}

Summary:"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating JD summary: {e}")
        return None


def extract_jd_details(jd_text: str) -> Optional[Dict]:
    """
    Extract structured requirements from JD using Gemini
    Returns JSON with all key requirements
    """
    if not jd_text:
        return None
    
    try:
        model = get_gemini_model()
        
        prompt = f"""Extract structured job requirements from this job description and return ONLY valid JSON (no markdown, no code blocks, just JSON):

{{
  "role": "",
  "company": "",
  "location": "",
  "job_type": "",
  "required_experience_years": "",
  "must_have_skills": {{
    "languages": [],
    "frameworks": [],
    "databases": [],
    "cloud_platforms": [],
    "tools": [],
    "other": []
  }},
  "good_to_have_skills": {{
    "languages": [],
    "frameworks": [],
    "databases": [],
    "cloud_platforms": [],
    "tools": [],
    "other": []
  }},
  "domain_knowledge_needed": [],
  "responsibilities": [],
  "qualifications": [],
  "preferred_qualifications": []
}}

Job Description:
{jd_text[:6000]}

Return only the JSON object:"""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Parse JSON
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Error parsing JD JSON: {e}")
        print(f"Response was: {response.text[:500]}")
        return None
    except Exception as e:
        print(f"Error extracting JD details: {e}")
        return None

