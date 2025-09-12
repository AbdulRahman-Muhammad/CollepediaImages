import os
import uuid
import json
import re
import time
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify
from github import Github, GithubException
import requests

app = Flask(__name__)

# --- CONFIGURATION ---
FULL_REPO_NAME = os.environ.get("GITHUB_REPO", "AbdulRahman-Muhammad/CollepediaImages")
DATA_JSON_URL = f"https://raw.githubusercontent.com/{FULL_REPO_NAME}/main/data.json"
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
CACHE_MAX_AGE_SECONDS = 300  # Cache data for 5 minutes

# --- GITHUB CLIENT (FOR UPLOADS ONLY) ---
if not GITHUB_TOKEN:
    raise ValueError("CRITICAL: GITHUB_TOKEN environment variable is not set!")
g = Github(GITHUB_TOKEN)
try:
    repo = g.get_repo(FULL_REPO_NAME)
except GithubException:
    raise RuntimeError(f"Could not access repo '{FULL_REPO_NAME}'. Check name and token.")

# --- IN-MEMORY CACHE ---
cache = {"data": None, "timestamp": 0}

def get_cached_data():
    global cache
    now = time.time()
    if not cache["data"] or (now - cache["timestamp"] > CACHE_MAX_AGE_SECONDS):
        response = requests.get(DATA_JSON_URL)
        response.raise_for_status()
        cache["data"] = response.json()
        cache["timestamp"] = now
    return cache["data"]

# --- ROUTES ---

@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/upload-page')
def upload_page():
    return render_template('upload.html')

@app.route('/documentation')
def documentation():
    return render_template('documentation.html')
    
@app.route('/search')
def search_api():
    try:
        all_images = get_cached_data()
        query = request.args.get('q', '').strip()
        
        # Advanced Search Logic
        # (This is a simplified parser for demonstration; a real-world version would be more complex)
        
        results = all_images

        # Handle sorting
        sort_match = re.search(r'sort:(\w+)-(asc|desc)', query)
        if sort_match:
            sort_by, direction = sort_match.groups()
            query = re.sub(r'sort:\w+-(asc|desc)', '', query).strip()
            if sort_by == 'date':
                results.sort(key=lambda x: x.get('timestamp', ''), reverse=(direction == 'desc'))

        # Simple keyword/tag filtering (with OR logic)
        or_groups = [part.strip() for part in query.split(' OR ')]
        
        final_results = []
        for image in results:
            image_tags_lower = {tag.lower() for tag in image.get('Tags', [])}
            image_owner_lower = image.get('owner', '').lower()

            for group in or_groups:
                must_match_all = True
                
                # Split by space for AND conditions within the group
                and_parts = group.split()
                for part in and_parts:
                    part_lower = part.lower()
                    
                    if part_lower.startswith('owner:'):
                        if not part_lower[6:] == image_owner_lower:
                            must_match_all = False; break
                    elif part_lower.startswith('-'):
                        if part_lower[1:] in image_tags_lower:
                            must_match_all = False; break
                    elif '*' in part_lower: # Wildcard
                        regex = re.compile(part_lower.replace('*', '.*'))
                        if not any(regex.match(tag) for tag in image_tags_lower):
                           must_match_all = False; break
                    else: # Simple tag
                        if not part_lower in image_tags_lower:
                            must_match_all = False; break
                
                if must_match_all:
                    final_results.append(image)
                    break 

        return jsonify(list({v['id']:v for v in final_results}.values())) # Return unique results
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload_handler():
    # This logic remains largely the same but is now only for writing data.
    try:
        file = request.files['image']
        owner = request.form['owner']
        tags_str = request.form['tags']
        tags_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
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
        except GithubException:
            data = []
            json_sha = None

        new_entry = {
            "index": len(data),
            "owner": owner,
            "Tags": tags_list,
            "id": image_id,
            "Url": f"https://raw.githubusercontent.com/{FULL_REPO_NAME}/main/{image_path}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        data.append(new_entry)
        
        new_content = json.dumps(data, indent=2)
        
        if json_sha:
            repo.update_file(json_path, f"docs: Update JSON for {image_id}", new_content, json_sha, branch="main")
        else:
            repo.create_file(json_path, "docs: Create initial data.json", new_content, branch="main")

        return "Image uploaded and data updated successfully!", 200

    except Exception as e:
        return f"An error occurred: {e}", 500

