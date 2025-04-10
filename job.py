from flask import Flask, request, render_template_string
import pdfplumber
import re
import nltk
from typing import Dict, List, Tuple
import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

nltk.download('punkt', quiet=True)

app = Flask(__name__)

# Email configuration (Update with your credentials)
EMAIL_ADDRESS = "example@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "#####"    #Replace with your App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# SQLite database setup with migration
def init_db():
    conn = sqlite3.connect('candidates.db')
    c = conn.cursor()
    
    # Create table if it doesn't exist (initial schema)
    c.execute('''CREATE TABLE IF NOT EXISTS candidates
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT NOT NULL,
                  phone TEXT NOT NULL,
                  status TEXT NOT NULL)''')
    
    # Check if columns exist and add them if missing
    c.execute("PRAGMA table_info(candidates)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'interview_datetime' not in columns:
        c.execute("ALTER TABLE candidates ADD COLUMN interview_datetime TEXT")
    if 'meet_link' not in columns:
        c.execute("ALTER TABLE candidates ADD COLUMN meet_link TEXT")
    
    conn.commit()
    conn.close()

# Function to save candidate to database
def save_candidate(name: str, email: str, phone: str, status: str, interview_datetime: str = None, meet_link: str = None):
    conn = sqlite3.connect('candidates.db')
    c = conn.cursor()
    c.execute("INSERT INTO candidates (name, email, phone, status, interview_datetime, meet_link) VALUES (?, ?, ?, ?, ?, ?)",
              (name, email, phone, status, interview_datetime, meet_link))
    conn.commit()
    conn.close()

# Function to send email
def send_email(to_email: str, name: str, interview_datetime: str, meet_link: str):
    subject = "Congratulations! Interview Scheduled with Analytics and Modeling Associate"
    body = f"""
    Dear {name},

    Congratulations! Based on your resume analysis, you have been shortlisted as a "Recommended" candidate for a position at Analytics and Modeling Associate.

    We would like to invite you for an interview. Below are the details:
    - Date and Time : {interview_datetime}
    - Google Meet Link : {meet_link}

    Please ensure you are available at the scheduled time. We look forward to speaking with you!

    Best regards,  
    Analytics and Modeling Associate Recruitment Team
    """
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file) -> str:
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = "".join(page.extract_text() or "" for page in pdf.pages)
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

# Function to extract information from resume text
def extract_info(text: str) -> Dict[str, any]:
    info = {
        'name': "Not found",
        'email': "Not found",
        'phone': "Not found",
        'skills': [],
        'experience': {"company": "Not found", "duration": "Not specified"},
        'cgpa': 0.0
    }
    
    text_lower = text.lower()
    
    # Extract name
    name_pattern = r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)+)'
    lines = text.split('\n')
    for line in lines[:10]:
        line = line.strip()
        name_match = re.search(name_pattern, line)
        if name_match and 10 <= len(line) <= 50 and len(line.split()) <= 3:
            info['name'] = name_match.group()
            break
    
    # Extract email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_match = re.search(email_pattern, text)
    if email_match:
        info['email'] = email_match.group()
    
    # Extract phone
    phone_pattern = r'(\+\d{1,3}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        info['phone'] = phone_match.group()
    
    # Extract skills
    skills_list = ['python', 'java', 'C++', 'sql', 'javascript', 'machine learning',
                   'data analysis', 'aws', 'react', 'docker', 'git', 'node.js', 
                   'tensorflow', 'excel', 'communication', 'leadership']
    info['skills'] = [skill for skill in skills_list if skill in text_lower]
    
    # Extract experience
    exp_pattern = r'(?:internship|experience|worked|working)\s+at\s+([A-Za-z\s]+)(?:.*?(\d+)\s*month[s]?)?.*?(ongoing|present)?'
    exp_match = re.search(exp_pattern, text_lower, re.IGNORECASE)
    if exp_match:
        company = exp_match.group(1).strip()
        months = exp_match.group(2)
        ongoing = exp_match.group(3)
        info['experience']['company'] = company
        if ongoing in ['ongoing', 'present']:
            info['experience']['duration'] = "Ongoing"
        elif months:
            info['experience']['duration'] = f"{months} months"
    
    # Extract CGPA
    cgpa_pattern = r'(?:cgpa|gpa)\s*[:\-\s]*(\d+\.?\d*)'
    cgpa_match = re.search(cgpa_pattern, text_lower)
    if cgpa_match:
        info['cgpa'] = float(cgpa_match.group(1))
    
    return info

# Company criteria for freshers
company_criteria = {
    'name': 'Analytics and Modeling Associate',
    'required_skills': ['python', 'sql', 'javascript', 'java', 'C++'],
    'min_cgpa': 8.0,
    'preferred_skills': ['java','React.js']
}

# Function to calculate ATS score
def calculate_ats_score(resume_info: Dict[str, any], criteria: Dict[str, any]) -> Tuple[float, List[str]]:
    score = 0
    details = []
    
    # Required skills (40 points)
    required_skills_match = sum(1 for skill in criteria['required_skills'] if skill in resume_info['skills'])
    req_skill_score = (required_skills_match / len(criteria['required_skills'])) * 40
    score += req_skill_score
    details.append(f"Required Skills: {required_skills_match}/{len(criteria['required_skills'])}")
    
    # CGPA (30 points)
    cgpa_match = resume_info['cgpa'] >= criteria['min_cgpa']
    cgpa_score = 30 if cgpa_match else (resume_info['cgpa'] / criteria['min_cgpa']) * 30
    score += cgpa_score
    details.append(f"CGPA: {resume_info['cgpa']} (Min: {criteria['min_cgpa']})")
    
    # Preferred skills (20 points)
    preferred_skills_match = sum(1 for skill in criteria['preferred_skills'] if skill in resume_info['skills'])
    pref_score = (preferred_skills_match / len(criteria['preferred_skills'])) * 20
    score += pref_score
    details.append(f"Preferred Skills: {preferred_skills_match}/{len(criteria['preferred_skills'])}")
    
    # Contact info (10 points)
    contact_score = 10 if (resume_info['email'] != "Not found" and resume_info['phone'] != "Not found") else 0
    score += contact_score
    details.append("Contact Info: Complete" if contact_score > 0 else "Contact Info: Incomplete")
    
    # Recommendation
    recommendation = "Recommended" if score >= 80 else "Potential" if score >= 60 else "Not Qualified"
    details.append(f"Recommendation: {recommendation}")
    
    return min(score, 100), details

# HTML template for main page (unchanged)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Analytics and Modeling Associate Resume Analyzer</title>
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; }
        body { 
            margin: 0; padding: 20px; 
            background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%); 
            min-height: 100vh; 
        }
        .container { 
            max-width: 900px; margin: 0 auto; 
            background: white; padding: 30px; 
            border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.15); 
        }
        h1 { color: #1a3c34; text-align: center; margin-bottom: 25px; font-size: 2em; }
        .upload-form { text-align: center; margin-bottom: 30px; }
        input[type="file"] { padding: 12px; margin-right: 15px; border: 1px solid #ddd; border-radius: 5px; }
        input[type="submit"] { 
            padding: 12px 25px; background: #16a085; color: white; 
            border: none; border-radius: 5px; cursor: pointer; transition: background 0.3s ease; 
        }
        input[type="submit"]:hover { background: #138d75; }
        .result { padding: 25px; border: 2px solid #e8f1f2; border-radius: 10px; background: #f9fbfc; }
        .result h2 { 
            color: #1a3c34; margin-top: 0; border-bottom: 3px solid #16a085; 
            padding-bottom: 10px; font-size: 1.5em; 
        }
        .result p { margin: 12px 0; font-size: 1.1em; }
        .result ul { list-style: none; padding: 0; }
        .result li { padding: 10px; border-bottom: 1px solid #eee; font-size: 1em; }
        .success { color: #27ae60; font-weight: bold; }
        .warning { color: #e67e22; font-weight: bold; }
        .error { color: #c0392b; font-weight: bold; }
        .score { 
            font-size: 28px; color: #1a3c34; text-align: center; 
            margin: 25px 0; background: #ecf0f1; padding: 10px; border-radius: 8px; 
        }
        .error-msg { color: #c0392b; text-align: center; font-weight: bold; font-size: 1.2em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Analytics and Modeling Associate Resume Analyzer</h1>
        <div class="upload-form">
            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="resume" accept=".pdf">
                <input type="submit" value="Analyze Resume">
            </form>
        </div>
        {% if error %}
            <p class="error-msg">{{ error }}</p>
        {% endif %}
        {% if result %}
            <div class="result">
                <h2>Resume Analysis</h2>
                <p><b>Name:</b> {{ result.name }}</p>
                <p><b>Email:</b> {{ result.email }}</p>
                <p><b>Phone:</b> {{ result.phone }}</p>
                <p><b>Skills:</b> {{ result.skills|join(', ') }}</p>
                <p><b>Experience:</b> {{ result.experience.company }} - {{ result.experience.duration }}</p>
                <p><b>CGPA:</b> {{ result.cgpa }}</p>
                <p class="score"><b>ATS Score:</b> {{ result.ats_score }}/100</p>
                <ul>
                {% for detail in result.details %}
                    <li {% if 'Recommendation' in detail %} 
                        class="{% if 'Recommended' in detail %}success{% elif 'Potential' in detail %}warning{% else %}error{% endif %}"
                        {% endif %}>{{ detail }}</li>
                {% endfor %}
                </ul>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# Admin panel HTML template (unchanged)
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel - Candidate List</title>
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; }
        body { 
            margin: 0; padding: 20px; 
            background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%); 
            min-height: 100vh; 
        }
        .container { 
            max-width: 1200px; margin: 0 auto; 
            background: white; padding: 30px; 
            border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.15); 
        }
        h1 { color: #1a3c34; text-align: center; margin-bottom: 25px; font-size: 2em; }
        table { 
            width: 100%; border-collapse: collapse; margin-top: 20px; 
        }
        th, td { 
            padding: 12px; text-align: left; border-bottom: 1px solid #ddd; 
        }
        th { 
            background: #16a085; color: white; font-weight: bold; 
        }
        tr:nth-child(even) { background: #f9fbfc; }
        tr:hover { background: #ecf0f1; }
        .success { color: #27ae60; font-weight: bold; }
        .warning { color: #e67e22; font-weight: bold; }
        a { color: #16a085; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Admin Panel - Candidate List</h1>
        <table>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Status</th>
                <th>Interview DateTime</th>
                <th>Google Meet Link</th>
            </tr>
            {% for candidate in candidates %}
            <tr>
                <td>{{ candidate[0] }}</td>
                <td>{{ candidate[1] }}</td>
                <td>{{ candidate[2] }}</td>
                <td>{{ candidate[3] }}</td>
                <td class="{% if candidate[4] == 'Recommended' %}success{% else %}warning{% endif %}">
                    {{ candidate[4] }}
                </td>
                <td>{{ candidate[5] or 'Not Scheduled' }}</td>
                <td>
                    {% if candidate[6] %}
                        <a href="{{ candidate[6] }}" target="_blank">{{ candidate[6] }}</a>
                    {% else %}
                        Not Scheduled
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def upload_resume():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return render_template_string(HTML_TEMPLATE, error="No file uploaded")
        file = request.files['resume']
        if file.filename == '':
            return render_template_string(HTML_TEMPLATE, error="No file selected")
        if file and file.filename.endswith('.pdf'):
            temp_path = os.path.join("uploads", file.filename)
            os.makedirs("uploads", exist_ok=True)
            file.save(temp_path)
            
            text = extract_text_from_pdf(temp_path)
            if text.startswith("Error"):
                os.remove(temp_path)
                return render_template_string(HTML_TEMPLATE, error=text)
            
            resume_info = extract_info(text)
            ats_score, details = calculate_ats_score(resume_info, company_criteria)
            
            result = {
                'name': resume_info['name'],
                'email': resume_info['email'],
                'phone': resume_info['phone'],
                'skills': resume_info['skills'],
                'experience': resume_info['experience'],
                'cgpa': resume_info['cgpa'],
                'ats_score': ats_score,
                'details': details
            }
            
            # Handle recommendation and email for Recommended candidates
            recommendation = [d for d in details if "Recommendation" in d][0].split(": ")[1]
            if recommendation in ["Recommended", "Potential"]:
                # For Recommended candidates, schedule an interview and send email
                if recommendation == "Recommended":
                    interview_datetime = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
                    meet_link = "https://meet.google.com/cof-qvyn-evg" 
                    save_candidate(
                        resume_info['name'],
                        resume_info['email'],
                        resume_info['phone'],
                        recommendation,
                        interview_datetime,
                        meet_link
                    )
                    if resume_info['email'] != "Not found":
                        send_email(resume_info['email'], resume_info['name'], interview_datetime, meet_link)
                else:  # Potential candidates
                    save_candidate(
                        resume_info['name'],
                        resume_info['email'],
                        resume_info['phone'],
                        recommendation
                    )
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return render_template_string(HTML_TEMPLATE, result=result)
        else:
            return render_template_string(HTML_TEMPLATE, error="Please upload a PDF file")
    return render_template_string(HTML_TEMPLATE)

@app.route('/admin')
def admin_panel():
    conn = sqlite3.connect('candidates.db')
    c = conn.cursor()
    c.execute("SELECT * FROM candidates")
    candidates = c.fetchall()
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, candidates=candidates)

if __name__ == '__main__':
    init_db()  
    app.run(debug=True, port=5000)