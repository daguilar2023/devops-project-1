# Blog Application – DevOps Edition

A minimal Flask + SQLite blog application enhanced with automated testing, Docker containerization, GitHub Actions CI/CD, and production deployment to Azure. This README includes local run instructions, testing, Docker usage, and deployment details.

---

# 🚀 Features

## Blog Features
- Create, edit, delete blog posts
- Archive/unarchive posts
- Action logging
- Public homepage showing non-archived posts

## DevOps Enhancements
- Automated pytest suite
- ≥70% code coverage enforced by CI
- Full Docker containerization
- GitHub Actions CI/CD:
  - Runs tests
  - Builds Docker image
  - Deploys automatically to Azure App Service
- Monitoring endpoints:
  - /health
  - /metrics (Prometheus)

---

# 📦 1. Local Setup & Run

## Clone the repo
git clone https://github.com/daguilar2023/devops-project-1.git  
cd devops-project-1

## Create virtual environment
python3 -m venv venv  
source venv/bin/activate  
(Windows: venv\Scripts\activate)

## Install dependencies
pip install -r requirements.txt

## Run the application
flask --app app run

Local URLs:  
Homepage → http://localhost:5000  
Admin panel → http://localhost:5000/admin

If database needs initialization:
flask --app app init-db

---

# 🧪 2. Running Tests Locally

Run the full test suite:
pytest -q

Run with coverage:
pytest --cov=app --cov-report=term-missing

CI enforces ≥70% coverage, so failing tests or low coverage blocks deployment.

---

# 🐳 3. Running App with Docker
Note: To run Docker commands locally, Docker Desktop must be installed and running.

## Build the Docker image
docker build -t blog-app .

## Run the container
docker run -p 5000:5000 blog-app

Then open:
http://localhost:5000

---

# ☁ 4. Deployment (CI/CD via GitHub Actions)

Deployment is fully automated.

## On any push:
- Tests run
- Docker image builds

## On push to main:
- The app is deployed to Azure App Service
- Uses azure/webapps-deploy@v2
- Authentication via AZURE_WEBAPP_PUBLISH_PROFILE secret

No manual deployment required.

---

# 🌐 5. Production Deployment (Azure)

Live application:
https://daniel-blog-code-d0ddbmd2h3e8hxfq.westeurope-01.azurewebsites.net

## Health check
https://daniel-blog-code-d0ddbmd2h3e8hxfq.westeurope-01.azurewebsites.net/health

## Prometheus metrics
https://daniel-blog-code-d0ddbmd2h3e8hxfq.westeurope-01.azurewebsites.net/metrics

---

# 📁 Project Structure

.
├── app.py  
├── blog.db  
├── Dockerfile  
├── prometheus.yml  
├── requirements.txt  
├── templates/  
├── static/  
├── tests/  
├── .github/workflows/ci.yml  
└── README.md  

---

# 📝 Deployment Notes

- SQLite persists inside Azure App Service’s filesystem.
- Redeployments do not erase the database.
- CI/CD triggers on merges into main.

---

# 🎉 Final Notes

This repository now contains:
- CI testing + coverage
- Docker containerization
- Automated Azure deployment
- Monitoring endpoints
- Full documentation
