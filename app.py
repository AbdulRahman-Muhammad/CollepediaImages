import os
import uuid
import json
import base64
from flask import Flask, render_template, request
from github import Github, GithubException

app = Flask(__name__)

# The full name of your repo, e.g., "AbdulRahman-Muhammad/CollepediaImages"
FULL_REPO_NAME = "AbdulRahman-Muhammad/CollepediaImages"
GITHUB_TOKEN = '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'

# --- Initialization and Validation ---
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
        # 1. Get data from the form
        file = request.files['image']
        owner = request.form['owner']
        tags_str = request.form['tags']
        tags_list = [tag.strip() for tag in tags_str.split(',')]
        
        image_id = str(uuid.uuid4())
        image_filename = f"{image_id}.jpg"
        image_path = f"images/{image_filename}"
        
        # 2. Upload the image directly with its final name
        repo.create_file(
            path=image_path,
            message=f"feat: Add image {image_filename}",
            content=file.read(),
            branch="main"
        )

        # 3. Get the current data.json
        json_path = "data.json"
        try:
            # We need the file's SHA to update it
            json_file = repo.get_contents(json_path, ref="main")
            json_content_decoded = json_file.decoded_content.decode('utf-8')
            data = json.loads(json_content_decoded)
            json_sha = json_file.sha
        except GithubException as e:
            if e.status == 404: # If data.json doesn't exist yet
                data = []
                json_sha = None # Will create the file instead of updating
            else:
                raise e

        # 4. Append the new image data
        new_entry = {
            "index": len(data),
            "owner": owner,
            "Tags": tags_list,
            "id": image_id,
            "Url": f"https://raw.githubusercontent.com/{FULL_REPO_NAME}/main/{image_path}"
        }
        data.append(new_entry)
        
        # 5. Update data.json in the repository
        # If the file didn't exist, sha is None and this will create it
        if json_sha:
             repo.update_file(
                path=json_path,
                message=f"docs: Update JSON for image {image_id}",
                content=json.dumps(data, indent=2),
                sha=json_sha, # Provide the SHA of the old file
                branch="main"
            )
        else: # Create the file if it didn't exist
            repo.create_file(
                path=json_path,
                message="docs: Create initial data.json",
                content=json.dumps(data, indent=2),
                branch="main"
            )

        return "تم رفع الصورة وتحديث البيانات بنجاح!", 200

    except GithubException as e:
        return f"خطأ من GitHub: {e.data.get('message', 'Unknown error')}", 500
    except Exception as e:
        return f"حدث خطأ غير متوقع: {e}", 500
