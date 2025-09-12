import os
from flask import Flask, render_template, request
from github import Github, GithubException

app = Flask(__name__)

# This is the full name of your repo, e.g., "AbdulRahman-Muhammad/CollepediaImages"
# Using an environment variable is the correct and secure way.
FULL_REPO_NAME = "AbdulRahman-Muhammad/CollepediaImages"

# The PAT is REQUIRED for writing files. There's no way around this.
GITHUB_TOKEN = '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'

# --- VALIDATION ---
if not GITHUB_TOKEN:
    # This will cause an intentional crash if the token is missing, which is good for debugging.
    raise ValueError("CRITICAL: GITHUB_TOKEN environment variable is not set in Vercel!")

# Initialize PyGithub with authentication
g = Github(GITHUB_TOKEN)
try:
    repo = g.get_repo(FULL_REPO_NAME)
except GithubException as e:
    # Handle the case where the repo is not found or the token is invalid
    raise RuntimeError(f"Could not access repository '{FULL_REPO_NAME}'. Check repo name and token permissions.") from e

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['image']
        owner = request.form['owner']
        tags = request.form['tags']
        image_id = "some_unique_id" # You should use uuid.uuid4() here in production
        
        filename = f"{image_id}_{owner}_{tags.replace(' ', '')}.jpg"
        content = file.read()

        # The create_file method REQUIRES authentication.
        repo.create_file(
            path=f"images/{filename}",
            message=f"feat: Add image {filename}",
            content=content,
            branch="main"
        )
        return "تم رفع الصورة بنجاح!", 200
    
    except GithubException as e:
        return f"خطأ من GitHub: {e.data.get('message', 'Unknown error')}", 500
    except Exception as e:
        return f"حدث خطأ: {e}", 500

