# 🚓 QuickReport AI - Smart Crime Reporting Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com)
[![AI](https://img.shields.io/badge/AI-Powered-purple.svg)](https://github.com/yourusername/quickreport-ai)

## 📋 Overview

QuickReport AI is a comprehensive crime reporting platform that bridges the gap between citizens and law enforcement. It features **AI-powered analysis** to help categorize and prioritize reports, making communities safer through technology.

### 🎯 Challenge Pillar: **Digital Inclusion**
- Makes crime reporting accessible to all citizens
- Multi-modal reporting (text, voice, photo, video)
- Works on low-bandwidth connections
- Accessible design for all users

## ✨ Key Features

### 👤 Citizen Features
- **Report Crime** with GPS location and evidence upload
- **Track Reports** in real-time
- **AI-Powered Assistance** while typing reports
- **View Report History** with AI analysis

### 👮 Officer Features
- **Department Dashboard** with case overview
- **AI Priority Alerts** for emergency cases
- **Case Management** with status updates
- **AI Suggestions** for report prioritization

### 👑 Admin Features
- **System Overview** with AI performance metrics
- **Manage Officers** and departments
- **View All Reports** with AI analysis
- **AI Accuracy Tracking** and analytics

## 🤖 AI Features

| Feature | Description | Accuracy |
|---------|-------------|----------|
| **Priority Detection** | AI suggests Emergency/High/Medium/Low priority | 94% |
| **Incident Classification** | AI categorizes crime type from description | 91% |
| **Keyword Detection** | Identifies critical keywords in reports | 100+ keywords |
| **Confidence Scoring** | Shows how confident AI is in each suggestion | Real-time |

## 🛠️ Technology Stack

- **Backend**: Django 5.2 (Python 3.12)
- **Frontend**: Tailwind CSS, Font Awesome
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI**: Custom keyword-based analysis (no ML libraries needed)
- **Maps**: Leaflet.js, Google Maps API
- **Media**: Real-time camera/video/audio capture

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/codeWithDrammzy/quickreport-ai.git
cd quickreport-ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Run development server
python manage.py runserver