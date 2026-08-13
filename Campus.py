import streamlit as st
import requests
from pymongo import MongoClient
from datetime import datetime
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Campus Works Showcase", page_icon="🎓", layout="wide")

# --- DATABASE CONNECTION ---
# st.cache_resource ensures we only connect to the database once
@st.cache_resource
def init_connection():
    # Looks for MONGO_URI in secrets, falls back to local MongoDB for testing
    uri = st.secrets.get("MONGO_URI", "mongodb://localhost:27017/")
    return MongoClient(uri)

client = init_connection()
db = client["campus_works"]
projects_collection = db["projects"]

# --- GITHUB VERIFICATION UTILITY ---
def verify_github_repo(github_url):
    """Checks if a repo has >= 5 commits spanning >= 24 hours."""
    match = re.search(r"github\.com/([^/]+)/([^/]+)", github_url)
    if not match:
        return {"is_authentic": False, "reason": "Invalid GitHub URL format."}
    
    owner, repo = match.groups()
    repo = repo.replace(".git", "")
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    # Use token if available to avoid rate limits
    if "GITHUB_TOKEN" in st.secrets:
        headers["Authorization"] = f"Bearer {st.secrets['GITHUB_TOKEN']}"
        
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            return {"is_authentic": False, "reason": "Repository not found or private."}
            
        commits = response.json()
        if len(commits) < 2:
            return {"is_authentic": False, "reason": "Not enough commit history."}
            
        # GitHub API returns newest commit first
        newest = datetime.strptime(commits[0]['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ")
        oldest = datetime.strptime(commits[-1]['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ")
        
        hours_diff = (newest - oldest).total_seconds() / 3600
        
        if len(commits) >= 5 and hours_diff >= 24:
            return {"is_authentic": True, "commits": len(commits), "hours": round(hours_diff)}
        else:
            return {"is_authentic": False, "reason": "Timeline too short or too few commits."}
            
    except Exception as e:
        return {"is_authentic": False, "reason": str(e)}


# --- NAVIGATION ---
st.sidebar.title("🎓 Campus Works")
page = st.sidebar.radio("Navigate", ["Discovery Hub", "Submit Project", "Admin Dashboard"])

# ==========================================
# PAGE 1: DISCOVERY HUB
# ==========================================
if page == "Discovery Hub":
    st.title("Explore Verified Student Projects")
    st.markdown("Browse technical projects securely verified by faculty and GitHub analysis.")
    st.divider()

    # Fetch only verified projects
    verified_projects = list(projects_collection.find({"is_verified": True}).sort("_id", -1))

    if not verified_projects:
        st.info("No verified projects available yet. Be the first to submit!")
    else:
        # Create a grid layout (3 columns)
        cols = st.columns(3)
        for index, proj in enumerate(verified_projects):
            with cols[index % 3]:
                # Streamlit 1.30+ supports container borders
                with st.container(border=True):
                    st.subheader(proj["title"])
                    st.caption(f"Built by {proj['student_name']} | ✅ Verified")
                    st.write(proj["description"])
                    
                    # Display Tech Stack
                    tech_tags = " | ".join(proj["tech_stack"])
                    st.markdown(f"**Tech:** `{tech_tags}`")
                    
                    # Links
                    st.markdown(f"[View Code (GitHub)]({proj['github_url']})")
                    if proj.get("live_url"):
                        st.markdown(f"[Live Demo]({proj['live_url']})")

# ==========================================
# PAGE 2: SUBMIT PROJECT
# ==========================================
elif page == "Submit Project":
    st.title("Submit Your Project")
    st.markdown("Your code will be automatically analyzed to verify authenticity.")
    
    with st.form("project_submission_form"):
        title = st.text_input("Project Title*", max_chars=100)
        student_name = st.text_input("Student Name*")
        description = st.text_area("Description*", max_chars=500)
        tech_stack = st.text_input("Tech Stack (comma-separated)*", placeholder="Python, Streamlit, MongoDB")
        github_url = st.text_input("GitHub Repository URL*")
        live_url = st.text_input("Live Demo URL (Optional)")
        
        submitted = st.form_submit_button("Submit & Verify")
        
        if submitted:
            if not title or not student_name or not description or not tech_stack or not github_url:
                st.error("Please fill in all required fields marked with *")
            else:
                with st.spinner("Analyzing GitHub repository..."):
                    # 1. Run automated check
                    github_check = verify_github_repo(github_url)
                    
                    # 2. Prepare database document
                    tech_list = [t.strip() for t in tech_stack.split(",") if t.strip()]
                    is_verified = github_check["is_authentic"]
                    
                    new_project = {
                        "title": title,
                        "student_name": student_name,
                        "description": description,
                        "tech_stack": tech_list,
                        "github_url": github_url,
                        "live_url": live_url if live_url else None,
                        "is_verified": is_verified,
                        "github_stats": {
                            "commits": github_check.get("commits", 0),
                            "dev_hours": github_check.get("hours", 0)
                        },
                        "verification_reason": "Auto-verified via GitHub" if is_verified else github_check.get("reason", "Pending manual review")
                    }
                    
                    # 3. Save to MongoDB
                    projects_collection.insert_one(new_project)
                    
                    # 4. Show result to student
                    if is_verified:
                        st.success(f"Success! Project auto-verified ({github_check['commits']} commits over {github_check['hours']} hours).")
                    else:
                        st.warning(f"Submitted. Auto-verification failed: {github_check.get('reason')}. Awaiting manual professor review.")

# ==========================================
# PAGE 3: ADMIN DASHBOARD
# ==========================================
elif page == "Admin Dashboard":
    st.title("Faculty Review Dashboard")
    st.markdown("Manually review and approve projects that failed auto-verification.")
    st.divider()
    
    # Fetch unverified projects
    pending_projects = list(projects_collection.find({"is_verified": False}))
    
    if not pending_projects:
        st.success("All caught up! No pending projects to review.")
    else:
        for proj in pending_projects:
            with st.expander(f"Pending: {proj['title']} by {proj['student_name']}"):
                st.write(f"**Description:** {proj['description']}")
                st.write(f"**Tech Stack:** {', '.join(proj['tech_stack'])}")
                st.write(f"**GitHub URL:** {proj['github_url']}")
                
                # Show why it failed auto-verification
                st.error(f"Auto-Verify Failed Reason: {proj.get('verification_reason', 'Unknown')}")
                
                # Approve Button (Using unique key to prevent UI conflicts)
                if st.button("Approve & Verify Project", key=str(proj["_id"])):
                    projects_collection.update_one(
                        {"_id": proj["_id"]},
                        {"$set": {"is_verified": True, "verification_reason": "Manually verified by Faculty"}}
                    )
                    st.success("Project verified! Refreshing...")
                    st.rerun() # Reloads the UI immediately
                  
