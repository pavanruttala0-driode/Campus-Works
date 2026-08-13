import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from urllib.parse import urlparse

DB_NAME = "campusworks.db"

st.set_page_config(
    page_title="CampusWorks",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            year TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            verified INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            technologies TEXT NOT NULL,
            category TEXT NOT NULL,
            github_url TEXT,
            demo_url TEXT,
            team_members TEXT,
            status TEXT DEFAULT 'Pending',
            admin_comment TEXT,
            created_at TEXT NOT NULL,
            verified_at TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def valid_url(value):
    if not value:
        return True
    try:
        p = urlparse(value)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False

def get_student(roll_number):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM students WHERE roll_number = ?",
        (roll_number.strip().upper(),)
    ).fetchone()
    conn.close()
    return row

def create_student(name, roll, dept, year, password):
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO students
               (name, roll_number, department, year, password_hash, verified, created_at)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (
                name.strip(),
                roll.strip().upper(),
                dept,
                year,
                hash_password(password),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "This roll number is already registered."
    finally:
        conn.close()

def authenticate_student(roll, password):
    student = get_student(roll)
    if student and student["password_hash"] == hash_password(password):
        return student
    return None

def add_project(student_id, title, description, technologies, category,
                github, demo, team_members):
    conn = get_db()
    conn.execute(
        """INSERT INTO projects
           (student_id, title, description, technologies, category,
            github_url, demo_url, team_members, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)""",
        (
            student_id,
            title.strip(),
            description.strip(),
            technologies.strip(),
            category,
            github.strip(),
            demo.strip(),
            team_members.strip(),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()

def get_student_projects(student_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM projects WHERE student_id = ? ORDER BY id DESC",
        (student_id,)
    ).fetchall()
    conn.close()
    return rows

def get_public_projects(search="", department="All", category="All"):
    conn = get_db()
    query = """
        SELECT p.*, s.name, s.roll_number, s.department, s.year
        FROM projects p
        JOIN students s ON p.student_id = s.id
        WHERE p.status = 'Verified'
    """
    params = []

    if search.strip():
        query += """ AND (
            p.title LIKE ? OR
            p.technologies LIKE ? OR
            s.name LIKE ? OR
            s.roll_number LIKE ?
        )"""
        term = f"%{search.strip()}%"
        params.extend([term, term, term, term])

    if department != "All":
        query += " AND s.department = ?"
        params.append(department)

    if category != "All":
        query += " AND p.category = ?"
        params.append(category)

    query += " ORDER BY p.id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def get_all_pending_projects():
    conn = get_db()
    rows = conn.execute("""
        SELECT p.*, s.name, s.roll_number, s.department, s.year
        FROM projects p
        JOIN students s ON p.student_id = s.id
        WHERE p.status = 'Pending'
        ORDER BY p.id DESC
    """).fetchall()
    conn.close()
    return rows

def update_project_status(project_id, status, comment=""):
    conn = get_db()
    verified_at = datetime.now().isoformat(timespec="seconds") if status == "Verified" else None
    conn.execute(
        """UPDATE projects
           SET status = ?, admin_comment = ?, verified_at = ?
           WHERE id = ?""",
        (status, comment.strip(), verified_at, project_id),
    )
    conn.commit()
    conn.close()

def get_stats():
    conn = get_db()
    students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    projects = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    verified = conn.execute(
        "SELECT COUNT(*) FROM projects WHERE status = 'Verified'"
    ).fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM projects WHERE status = 'Pending'"
    ).fetchone()[0]
    conn.close()
    return students, projects, verified, pending

def inject_css():
    st.markdown("""
    <style>
    .main {
        background: #f7f9fc;
    }
    .hero {
        padding: 2rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #172554, #2563eb);
        color: white;
        margin-bottom: 1.5rem;
    }
    .hero h1 {
        font-size: 2.6rem;
        margin-bottom: .3rem;
    }
    .card {
        padding: 1.25rem;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        background: white;
        margin-bottom: 1rem;
        box-shadow: 0 3px 12px rgba(0,0,0,.05);
    }
    .verified {
        display: inline-block;
        padding: .3rem .65rem;
        border-radius: 999px;
        background: #dcfce7;
        color: #166534;
        font-weight: 700;
        font-size: .85rem;
    }
    .pending {
        display: inline-block;
        padding: .3rem .65rem;
        border-radius: 999px;
        background: #fef3c7;
        color: #92400e;
        font-weight: 700;
        font-size: .85rem;
    }
    .rejected {
        display: inline-block;
        padding: .3rem .65rem;
        border-radius: 999px;
        background: #fee2e2;
        color: #991b1b;
        font-weight: 700;
        font-size: .85rem;
    }
    .small {
        color: #64748b;
        font-size: .9rem;
    }
    </style>
    """, unsafe_allow_html=True)

def status_badge(status):
    cls = {
        "Verified": "verified",
        "Pending": "pending",
        "Rejected": "rejected",
    }.get(status, "pending")
    icon = {"Verified": "✓", "Pending": "⏳", "Rejected": "✕"}.get(status, "")
    return f'<span class="{cls}">{icon} {status}</span>'

def project_card(project, show_links=True):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2 = st.columns([4, 1])
    with c1:
        st.subheader(project["title"])
        st.write(project["description"])
        st.write(f"**Technologies:** {project['technologies']}")
        st.write(f"**Category:** {project['category']}")
        if "name" in project.keys():
            st.write(
                f"**Student:** {project['name']}  •  "
                f"**Roll No:** {project['roll_number']}  •  "
                f"**Department:** {project['department']}  •  "
                f"**Year:** {project['year']}"
            )
        if project["team_members"]:
            st.write(f"**Team:** {project['team_members']}")
    with c2:
        st.markdown(status_badge(project["status"]), unsafe_allow_html=True)
        if project["status"] == "Verified":
            st.caption("CampusWorks Verified")
    if show_links:
        links = []
        if project["github_url"]:
            links.append(f"[💻 GitHub]({project['github_url']})")
        if project["demo_url"]:
            links.append(f"[🚀 Live Demo]({project['demo_url']})")
        if links:
            st.markdown("  |  ".join(links))
    if project["admin_comment"]:
        st.info(f"Admin feedback: {project['admin_comment']}")
    st.markdown("</div>", unsafe_allow_html=True)

def login_page():
    st.markdown("""
    <div class="hero">
        <h1>🎓 CampusWorks</h1>
        <p>Build. Verify. Showcase.</p>
        <p>A trusted platform for verified student projects.</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Student Login", "📝 Student Registration"])

    with tab1:
        with st.form("student_login"):
            roll = st.text_input("Roll Number", placeholder="e.g. 22A81A0501")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if not roll or not password:
                st.error("Please enter both roll number and password.")
            else:
                student = authenticate_student(roll, password)
                if student:
                    st.session_state.logged_in = True
                    st.session_state.role = "student"
                    st.session_state.user_id = student["id"]
                    st.session_state.roll_number = student["roll_number"]
                    st.rerun()
                else:
                    st.error("Invalid roll number or password.")

    with tab2:
        with st.form("registration"):
            name = st.text_input("Full Name")
            roll = st.text_input("Roll Number", placeholder="e.g. 22A81A0501")
            dept = st.selectbox(
                "Department",
                ["ECE", "CSE", "EEE", "IT", "MECH", "CIVIL", "AIML", "Other"]
            )
            year = st.selectbox("Year", ["1st Year", "2nd Year", "3rd Year", "4th Year"])
            password = st.text_input("Create Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

        if submitted:
            if not all([name.strip(), roll.strip(), password]):
                st.error("Please fill all required fields.")
            elif len(password) < 6:
                st.error("Password must contain at least 6 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                ok, message = create_student(name, roll, dept, year, password)
                if ok:
                    st.success(message + " You can now log in.")
                else:
                    st.error(message)

def student_dashboard():
    student = get_student(st.session_state.roll_number)
    if not student:
        st.session_state.clear()
        st.rerun()

    st.sidebar.success(f"Logged in as\n{student['name']}")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.title("👨‍🎓 Student Dashboard")
    st.caption("Manage your profile and showcase your completed technical projects.")

    projects = get_student_projects(student["id"])
    verified_count = sum(p["status"] == "Verified" for p in projects)
    pending_count = sum(p["status"] == "Pending" for p in projects)

    c1, c2, c3 = st.columns(3)
    c1.metric("My Projects", len(projects))
    c2.metric("Verified", verified_count)
    c3.metric("Pending", pending_count)

    tab1, tab2, tab3 = st.tabs(["📊 Overview", "➕ Add Project", "📁 My Projects"])

    with tab1:
        st.subheader("Student Profile")
        st.markdown(f"""
        **Name:** {student['name']}  
        **Roll Number:** {student['roll_number']}  
        **Department:** {student['department']}  
        **Year:** {student['year']}  
        **Student Status:** {status_badge("Verified")}
        """, unsafe_allow_html=True)

        st.info("Submit completed projects for faculty/admin verification. Approved projects receive the CampusWorks Verified badge.")

    with tab2:
        st.subheader("Submit a Project")
        with st.form("project_form"):
            title = st.text_input("Project Title *")
            description = st.text_area("Project Description *", height=140)
            technologies = st.text_input(
                "Technologies Used *",
                placeholder="Python, Streamlit, Gemini API"
            )
            category = st.selectbox(
                "Project Category *",
                ["AI/ML", "Web Development", "Mobile App", "IoT",
                 "Cybersecurity", "Data Science", "Embedded Systems", "Other"]
            )
            github = st.text_input("GitHub Repository URL")
            demo = st.text_input("Live Demo / Deployment URL")
            team_members = st.text_input(
                "Team Members",
                placeholder="Names separated by commas"
            )
            submit = st.form_submit_button(
                "🚀 Submit for Verification",
                use_container_width=True
            )

        if submit:
            if not title.strip() or not description.strip() or not technologies.strip():
                st.error("Please complete all required fields.")
            elif not valid_url(github) or not valid_url(demo):
                st.error("Please enter valid GitHub/Live Demo URLs starting with http:// or https://.")
            else:
                add_project(
                    student["id"], title, description, technologies,
                    category, github, demo, team_members
                )
                st.success("Project submitted successfully. Status: Pending Verification.")
                st.rerun()

    with tab3:
        st.subheader("My Projects")
        if not projects:
            st.info("You have not submitted any projects yet.")
        else:
            for project in projects:
                project_card(project)

def admin_login():
    st.markdown("""
    <div class="hero">
        <h1>👨‍🏫 Faculty/Admin</h1>
        <p>Review and verify student projects.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("admin_login"):
        admin_id = st.text_input("Admin ID", placeholder="admin")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Admin Login", use_container_width=True)

    if submit:
        if admin_id == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.rerun()
        else:
            st.error("Invalid admin credentials.")

def admin_dashboard():
    st.sidebar.success("Faculty/Admin")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.title("👨‍🏫 Admin Verification Dashboard")

    students, projects, verified, pending = get_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students", students)
    c2.metric("Projects", projects)
    c3.metric("Verified", verified)
    c4.metric("Pending", pending)

    st.divider()
    st.subheader("⏳ Projects Awaiting Verification")
    pending_projects = get_all_pending_projects()

    if not pending_projects:
        st.success("No projects are waiting for verification.")
        return

    for project in pending_projects:
        with st.container(border=True):
            st.subheader(project["title"])
            st.write(f"**Student:** {project['name']}")
            st.write(f"**Roll Number:** {project['roll_number']}")
            st.write(f"**Department:** {project['department']} | **Year:** {project['year']}")
            st.write(f"**Category:** {project['category']}")
            st.write(f"**Technologies:** {project['technologies']}")
            st.write(f"**Description:** {project['description']}")

            if project["team_members"]:
                st.write(f"**Team Members:** {project['team_members']}")

            if project["github_url"]:
                st.markdown(f"💻 [Open GitHub Repository]({project['github_url']})")
            if project["demo_url"]:
                st.markdown(f"🚀 [Open Live Demo]({project['demo_url']})")

            comment = st.text_input(
                "Verification comment",
                key=f"comment_{project['id']}",
                placeholder="Optional feedback for the student"
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve & Verify", key=f"approve_{project['id']}", use_container_width=True):
                    update_project_status(project["id"], "Verified", comment)
                    st.success("Project verified successfully.")
                    st.rerun()
            with col2:
                if st.button("❌ Reject", key=f"reject_{project['id']}", use_container_width=True):
                    if not comment.strip():
                        st.warning("Please add a reason before rejecting.")
                    else:
                        update_project_status(project["id"], "Rejected", comment)
                        st.warning("Project rejected and feedback saved.")
                        st.rerun()

def showcase():
    st.markdown("""
    <div class="hero">
        <h1>🌐 CampusWorks Showcase</h1>
        <p>Discover genuine, verified student projects.</p>
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input(
        "🔎 Search projects",
        placeholder="Search by project, student, roll number or technology..."
    )

    conn = get_db()
    departments = [r[0] for r in conn.execute(
        "SELECT DISTINCT department FROM students ORDER BY department"
    ).fetchall()]
    categories = [r[0] for r in conn.execute(
        "SELECT DISTINCT category FROM projects ORDER BY category"
    ).fetchall()]
    conn.close()

    c1, c2 = st.columns(2)
    with c1:
        department = st.selectbox("Department", ["All"] + departments)
    with c2:
        category = st.selectbox("Category", ["All"] + categories)

    projects = get_public_projects(search, department, category)

    st.write(f"**{len(projects)} verified project(s) found**")

    if not projects:
        st.info("No verified projects match your search.")
    else:
        for project in projects:
            project_card(project)

def main():
    init_db()
    inject_css()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    with st.sidebar:
        st.markdown("## 🎓 CampusWorks")
        st.caption("Build. Verify. Showcase.")
        st.divider()

        if not st.session_state.logged_in:
            page = st.radio(
                "Navigation",
                ["🏠 Home", "🌐 Showcase", "🔐 Student Login", "👨‍🏫 Admin Login"]
            )
        else:
            page = None

    if not st.session_state.logged_in:
        if page == "🏠 Home":
            st.markdown("""
            <div class="hero">
                <h1>🎓 CampusWorks</h1>
                <p>Build. Verify. Showcase.</p>
                <p>
                    A trusted college platform where verified students
                    showcase completed technical projects.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.subheader("Why CampusWorks?")
            c1, c2, c3 = st.columns(3)
            c1.markdown("### 🔐 Trusted\nVerify students using their college roll number.")
            c2.markdown("### ✅ Authentic\nFaculty/admin verification establishes project authenticity.")
            c3.markdown("### 🚀 Discoverable\nMake genuine student projects easy to find.")

            st.divider()
            st.subheader("How it works")
            st.write("**1. Login → 2. Submit → 3. Faculty verifies → 4. Verified badge → 5. Public showcase**")

        elif page == "🌐 Showcase":
            showcase()
        elif page == "🔐 Student Login":
            login_page()
        elif page == "👨‍🏫 Admin Login":
            admin_login()

    elif st.session_state.role == "student":
        student_dashboard()
    elif st.session_state.role == "admin":
        admin_dashboard()

if __name__ == "__main__":
    main()
