
# 💼 SmartResume – AI-Powered Recruitment Automation

SmartResume is an intelligent recruitment automation tool that analyzes resumes, evaluates candidate suitability using ATS scoring, schedules interviews for recommended profiles, and even sends automated emails — all powered by AI and smart parsing logic.

---

## 🚀 Features

- 📄 Upload and parse PDF resumes  
- 🔍 Extract candidate info (Name, Email, Phone, Skills, CGPA, Experience)  
- 🎯 ATS Score Calculation (based on required & preferred skills and CGPA)  
- 📬 Auto Email Invite to Recommended Candidates  
- 🗓️ Interview Scheduling with Google Meet Integration  
- 🛡️ Admin Panel to View All Candidates  
- 🌐 Elegant company landing page (HTML + CSS) with About & Job Description section  

---

## 🏢 Company Landing Page

The landing page includes:

- 🧾 About the Company  
- 💼 Job Role and Description  
- 📬 Resume Upload Form  

---

## 🧠 How It Works

![SmartResume Workflow](image/flow.png)

---

## 🛠️ Tech Stack

### 👨‍💻 Backend
- Python  
- Flask  
- PDFPlumber  
- NLTK  
- SQLite  
- Regex  

### 💅 Frontend
- HTML5  
- CSS3  

### 📬 Email Integration
- SMTP  
- Gmail App Passwords  

---

## 📦 Installation

```bash
git clone https://github.com/yourusername/smartresume.git
cd smartresume
```

```bash
pip install -r requirements.txt
```

```bash
python job.py
```

Make sure to update the following in the code:

```python
EMAIL_ADDRESS = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"
```

---

## 📁 Folder Structure

```
smartresume/
├── job.py
├── index.html 
├── styles.css
├── uploads/
├── requirements.txt
├── candidates.db
└── README.md
```

---

## 🔒 Security Notice

- Use [Gmail App Passwords](https://support.google.com/accounts/answer/185833) instead of real passwords.  
- Don’t push sensitive credentials to GitHub. Use `.env` or environment variables in production.

---

## ✨ Future Improvements

- Upload resume via drag and drop  
- Admin login and access control  
- Export candidate data to Excel/CSV  
- Chatbot assistant for applicants  

---

## 🙌 Acknowledgements

Built with ❤️ using Python and Flask.

---

## 📜 License

MIT License
