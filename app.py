from flask import Flask, render_template, request
from github import Github
import uuid

app = Flask(__name__)

# Load configuration from environment variables
GITHUB_TOKEN = "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"
REPO_NAME = "AbdulRahman-Muhammad/CollepediaImages"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['image']
        owner = request.form['owner']
        tags = request.form['tags']
        
        image_id = str(uuid.uuid4())
        
        # Format: {id}_{owner}_{tags}.jpg
        filename = f"{image_id}_{owner}_{tags.replace(' ', '')}.jpg"
        content = file.read()

        # Upload to the 'images' folder in the storage repository
        repo.create_file(
            path=f"images/{filename}",
            message=f"Add image: {filename}",
            content=content,
            branch="main"
        )
        return "تم رفع الصورة بنجاح! سيتم معالجتها قريباً.", 200
    except Exception as e:
        return f"حدث خطأ: {e}", 500
