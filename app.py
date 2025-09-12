import os
import uuid
import json
from flask import Flask, render_template, request
from github import Github, GithubException

app = Flask(__name__)

# --- DEBUGGING SECTION ---
# This part will help us see what Vercel is actually providing to our app.
print("--- Starting Application ---")
github_token_from_env = os.environ.get('GITHUB_TOKEN')

if github_token_from_env:
    # Print only the first 4 and last 4 characters for security.
    # This confirms the token exists without exposing it.
    print(f"✅ GITHUB_TOKEN environment variable found.")
    print(f"   Token preview: {github_token_from_env[:4]}...{github_token_from_env[-4:]}")
else:
    # This message is a clear indicator of the problem.
    print("❌ CRITICAL: GITHUB_TOKEN environment variable was NOT FOUND or is EMPTY.")
# --- END DEBUGGING SECTION ---


FULL_REPO_NAME = "AbdulRahman-Muhammad/CollepediaImages"
GITHUB_TOKEN = github_token_from_env # Use the variable we just checked

if not GITHUB_TOKEN:
    raise ValueError("CRITICAL: GITHUB_TOKEN environment variable is not set!")

g = Github(GITHUB_TOKEN)
try:
    repo = g.get_repo(FULL_REPO_NAME)
except GithubException as e:
    raise RuntimeError(f"Could not access repo '{FULL_REPO_NAME}'. Check name and token permissions.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['image']
        owner = request.form['owner']
        tags_str = request.form['tags']
        tags_list = [tag.strip() for tag in tags_str.split(',')]
        
        image_id = str(uuid.uuid4())
        image_filename = f"{image_id}.jpg"
        image_path = f"images/{image_filename}"
        
        repo.create_file(
            path=image_path,
            message=f"feat: Add image {image_filename}",
            content=file.read(),
            branch="main"
        )

        json_path = "data.json"
        try:
            json_file = repo.get_contents(json_path, ref="main")
            data = json.loads(json_file.decoded_content.decode('utf-8'))
            json_sha = json_file.sha
        except GithubException as e:
            if e.status == 404:
                data = []
                json_sha = None
            else:
                raise e

        # --- IMPORTANT CHANGE: Reverted to the direct raw link ---
        new_entry = {
            "index": len(data),
            "owner": owner,
            "Tags": tags_list,
            "id": image_id,
            "Url": f"https://raw.githubusercontent.com/{FULL_REPO_NAME}/main/{image_path}"
        }
        data.append(new_entry)
        
        new_content = json.dumps(data, indent=2)
        
        if json_sha:
            repo.update_file(json_path, f"docs: Update JSON for {image_id}", new_content, json_sha, branch="main")
        else:
            repo.create_file(json_path, "docs: Create initial data.json", new_content, branch="main")

        return "تم رفع الصورة وتحديث البيانات بنجاح!", 200

    except Exception as e:
        return f"حدث خطأ: {e}", 500

