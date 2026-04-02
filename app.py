from flask import Flask, render_template, request, redirect, session, Response
import psycopg2
import csv
import io

app = Flask(__name__)
app.secret_key = "secret"

conn = psycopg2.connect(
    dbname="resume_builder",
    user="postgres",
    password="011983",
    host="localhost"
)
cur = conn.cursor()

def is_admin():
    if 'user_id' not in session:
        return False
    user_id = session['user_id']
    cur.execute("SELECT is_admin FROM users WHERE userid=%s", (user_id,))
    user = cur.fetchone()
    return user and user[0]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cur.execute("INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                    (name,email,password))
        conn.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur.execute("SELECT userid, is_admin FROM users WHERE email=%s AND password=%s",
                    (email,password))
        user = cur.fetchone()

        if user:
            session['user_id'] = user[0]
            if user[1]:  # is_admin
                return redirect('/admin')
            else:
                return redirect('/dashboard')

    return render_template('login.html')


@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        try:
            userid = session.get('user_id')
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            summary = request.form.get('summary')
            degree = request.form.get('degree')
            institution = request.form.get('institution')
            edu_start = request.form.get('edu_start')
            edu_end = request.form.get('edu_end')
            skills_str = request.form.get('skills')
            projects_str = request.form.get('projects')

            # create new resume
            cur.execute(
                "INSERT INTO resume(userid, title, name, email, phone, summary) VALUES(%s, %s, %s, %s, %s, %s) RETURNING resumeid",
                (userid, "My Resume", name, email, phone, summary)
            )
            resumeid = cur.fetchone()[0]

            # save education
            cur.execute(
                "INSERT INTO education(userid,resumeid,degree,institution,start_year,end_year) VALUES(%s,%s,%s,%s,%s,%s)",
                (userid, resumeid, degree, institution, edu_start, edu_end)
            )

            # save skills
            if skills_str:
                skills = [s.strip() for s in skills_str.split(',') if s.strip()]
                for skill in skills:
                    cur.execute(
                        "INSERT INTO skills(userid,resumeid,skillname) VALUES(%s,%s,%s)",
                        (userid, resumeid, skill)
                    )

            # save projects
            if projects_str:
                projects = [p.strip() for p in projects_str.split(',') if p.strip()]
                for project in projects:
                    cur.execute(
                        "INSERT INTO projects(userid,resumeid,projectname) VALUES(%s,%s,%s)",
                        (userid, resumeid, project)
                    )

            # save experience
            experience_str = request.form.get('experience')
            if experience_str:
                for line in experience_str.strip().split('\n'):
                    if line.strip():
                        parts = [p.strip() for p in line.split('-')]
                        if len(parts) >= 5:
                            job_title, company, start_date, end_date, description = parts[0], parts[1], parts[2], parts[3], '-'.join(parts[4:])
                            cur.execute(
                                "INSERT INTO experience(userid,resumeid,job_title,company,start_date,end_date,description) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                                (userid, resumeid, job_title, company, start_date, end_date, description)
                            )

            # save achievements
            achievements_str = request.form.get('achievements')
            if achievements_str:
                for achievement in achievements_str.strip().split('\n'):
                    if achievement.strip():
                        cur.execute(
                            "INSERT INTO achievements(userid,resumeid,achievement) VALUES(%s,%s,%s)",
                            (userid, resumeid, achievement.strip())
                        )

            # save courses
            courses_str = request.form.get('courses')
            if courses_str:
                for course in courses_str.strip().split('\n'):
                    if course.strip():
                        parts = course.split('-')
                        if len(parts) >= 2:
                            course_name = parts[0].strip()
                            institution = '-'.join(parts[1:]).strip()
                            cur.execute(
                                "INSERT INTO courses(userid,resumeid,course_name,institution) VALUES(%s,%s,%s,%s)",
                                (userid, resumeid, course_name, institution)
                            )

            # save interests
            interests_str = request.form.get('interests')
            if interests_str:
                for interest in interests_str.strip().split('\n'):
                    if interest.strip():
                        cur.execute(
                            "INSERT INTO interests(userid,resumeid,interest) VALUES(%s,%s,%s)",
                            (userid, resumeid, interest.strip())
                        )

            conn.commit()
            return redirect('/resume')

        except Exception as e:
            conn.rollback()
            return f"An error occurred: {e}"

    return render_template('dashboard.html', is_admin=is_admin())
      

@app.route('/resume')
def resume():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']

    # Get all resumes for this user
    cur.execute("SELECT * FROM resume WHERE userid=%s", (user_id,))
    resumes = cur.fetchall()  # list of resumes

    resume_data = []
    for res in resumes:
        resumeid = res[0]  # assuming first column is resumeid
        cur.execute("SELECT * FROM education WHERE resumeid=%s", (resumeid,))
        edu = cur.fetchall()
        
        cur.execute("SELECT * FROM skills WHERE resumeid=%s", (resumeid,))
        skills = cur.fetchall()
        
        cur.execute("SELECT * FROM projects WHERE resumeid=%s", (resumeid,))
        projects = cur.fetchall()
        
        cur.execute("SELECT * FROM experience WHERE resumeid=%s", (resumeid,))
        experience = cur.fetchall()
        
        cur.execute("SELECT * FROM achievements WHERE resumeid=%s", (resumeid,))
        achievements = cur.fetchall()
        
        cur.execute("SELECT * FROM courses WHERE resumeid=%s", (resumeid,))
        courses = cur.fetchall()
        
        cur.execute("SELECT * FROM interests WHERE resumeid=%s", (resumeid,))
        interests = cur.fetchall()
        
        resume_data.append({
            'resume': res,
            'edu': edu,
            'skills': skills,
            'projects': projects,
            'experience': experience,
            'achievements': achievements,
            'courses': courses,
            'interests': interests
        })

    return render_template('resume.html', resume_data=resume_data, is_admin=is_admin())

@app.route("/resume/<int:resume_id>")
def view_resume(resume_id):
    if 'user_id' not in session:
        return redirect('/login')
    conn = psycopg2.connect(
        host="localhost",
        database="resume_builder",
        user="postgres",
        password="011983"
    )
    cur = conn.cursor()

    # resume
    cur.execute("SELECT * FROM resume WHERE resumeid = %s", (resume_id,))
    res = cur.fetchone()

    # skills
    cur.execute("SELECT * FROM skills WHERE resumeid = %s", (resume_id,))
    skills = cur.fetchall()

    # education
    cur.execute("SELECT * FROM education WHERE resumeid = %s", (resume_id,))
    edu = cur.fetchall()

    # projects
    cur.execute("SELECT * FROM projects WHERE resumeid = %s", (resume_id,))
    projects = cur.fetchall()

    # experience
    cur.execute("SELECT * FROM experience WHERE resumeid = %s", (resume_id,))
    experience = cur.fetchall()

    # achievements
    cur.execute("SELECT * FROM achievements WHERE resumeid = %s", (resume_id,))
    achievements = cur.fetchall()

    # courses
    cur.execute("SELECT * FROM courses WHERE resumeid = %s", (resume_id,))
    courses = cur.fetchall()

    # interests
    cur.execute("SELECT * FROM interests WHERE resumeid = %s", (resume_id,))
    interests = cur.fetchall()

    conn.close()

    return render_template(
        "view_resume.html",
        res=res,
        skills=skills,
        edu=edu,
        projects=projects,
        experience=experience,
        achievements=achievements,
        courses=courses,
        interests=interests
    )

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')


# Delete resume route
@app.route('/delete_resume/<int:resumeid>', methods=['POST'])
def delete_resume(resumeid):
    if 'user_id' not in session:
        return redirect('/login')
    try:
        # Delete from child tables first due to FK constraints
        cur.execute("DELETE FROM education WHERE resumeid=%s", (resumeid,))
        cur.execute("DELETE FROM skills WHERE resumeid=%s", (resumeid,))
        cur.execute("DELETE FROM projects WHERE resumeid=%s", (resumeid,))
        cur.execute("DELETE FROM experience WHERE resumeid=%s", (resumeid,))
        cur.execute("DELETE FROM achievements WHERE resumeid=%s", (resumeid,))
        cur.execute("DELETE FROM courses WHERE resumeid=%s", (resumeid,))
        cur.execute("DELETE FROM interests WHERE resumeid=%s", (resumeid,))
        cur.execute("DELETE FROM resume WHERE resumeid=%s", (resumeid,))
        conn.commit()
    except Exception as e:
        conn.rollback()
    return redirect('/resume')

# Admin Routes
@app.route('/admin')
def admin_dashboard():
    if not is_admin():
        return redirect('/login')
    
    # Get statistics
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM resume")
    total_resumes = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE")
    total_admins = cur.fetchone()[0]
    
    # Get recent users
    cur.execute("SELECT userid, name, email, is_admin FROM users ORDER BY userid DESC LIMIT 10")
    recent_users = cur.fetchall()
    
    return render_template('admin_dashboard.html', 
                         total_users=total_users, 
                         total_resumes=total_resumes,
                         total_admins=total_admins,
                         recent_users=recent_users)

@app.route('/admin/users')
def admin_users():
    if not is_admin():
        return redirect('/login')
    
    cur.execute("SELECT userid, name, email, contact, address, is_admin FROM users ORDER BY userid")
    users = cur.fetchall()
    return render_template('admin_users.html', users=users)

@app.route('/admin/resumes')
def admin_resumes():
    if not is_admin():
        return redirect('/login')
    
    cur.execute("""
        SELECT r.resumeid, r.title, u.name, u.email, r.created_at 
        FROM resume r 
        JOIN users u ON r.userid = u.userid 
        ORDER BY r.created_at DESC
    """)
    resumes = cur.fetchall()
    return render_template('admin_resumes.html', resumes=resumes)

@app.route('/admin/reports')
def admin_reports():
    if not is_admin():
        return redirect('/login')
    
    # Get all users
    cur.execute("SELECT userid, name, email, is_admin FROM users ORDER BY userid")
    users = cur.fetchall()
    
    # Get all resumes
    cur.execute("""
        SELECT r.resumeid, r.title, u.name, u.email, r.created_at 
        FROM resume r 
        JOIN users u ON r.userid = u.userid 
        ORDER BY r.created_at DESC
    """)
    resumes = cur.fetchall()
    
    return render_template('admin_reports.html', users=users, resumes=resumes)

@app.route('/admin/reports/download/users/csv')
def download_users_csv():
    if not is_admin():
        return redirect('/login')
    
    cur.execute("SELECT userid, name, email, is_admin FROM users ORDER BY userid")
    users = cur.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Email', 'Is Admin'])
    for user in users:
        writer.writerow(user)
    
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={"Content-Disposition": "attachment; filename=users_report.csv"})

@app.route('/admin/reports/download/resumes/csv')
def download_resumes_csv():
    if not is_admin():
        return redirect('/login')
    
    cur.execute("""
        SELECT r.resumeid, r.title, u.name, u.email, r.created_at 
        FROM resume r 
        JOIN users u ON r.userid = u.userid 
        ORDER BY r.created_at DESC
    """)
    resumes = cur.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Title', 'User Name', 'User Email', 'Created At'])
    for resume in resumes:
        writer.writerow(resume)
    
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={"Content-Disposition": "attachment; filename=resumes_report.csv"})

@app.route('/admin/user/<int:user_id>')
def admin_user_detail(user_id):
    if not is_admin():
        return redirect('/login')
    
    # Get user info
    cur.execute("SELECT * FROM users WHERE userid=%s", (user_id,))
    user = cur.fetchone()
    
    if not user:
        return "User not found", 404
    
    # Get user's resumes
    cur.execute("SELECT * FROM resume WHERE userid=%s", (user_id,))
    resumes = cur.fetchall()
    
    return render_template('admin_user_detail.html', user=user, resumes=resumes)

@app.route('/admin/toggle_admin/<int:user_id>', methods=['POST'])
def toggle_admin(user_id):
    if not is_admin():
        return redirect('/login')
    
    cur.execute("UPDATE users SET is_admin = NOT is_admin WHERE userid=%s", (user_id,))
    conn.commit()
    return redirect('/admin/users')

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not is_admin():
        return redirect('/login')
    
    try:
        # Delete user's resumes and related data first
        cur.execute("SELECT resumeid FROM resume WHERE userid=%s", (user_id,))
        resume_ids = [r[0] for r in cur.fetchall()]
        
        for resume_id in resume_ids:
            cur.execute("DELETE FROM education WHERE resumeid=%s", (resume_id,))
            cur.execute("DELETE FROM skills WHERE resumeid=%s", (resume_id,))
            cur.execute("DELETE FROM projects WHERE resumeid=%s", (resume_id,))
            cur.execute("DELETE FROM experience WHERE resumeid=%s", (resume_id,))
            cur.execute("DELETE FROM achievements WHERE resumeid=%s", (resume_id,))
            cur.execute("DELETE FROM courses WHERE resumeid=%s", (resume_id,))
            cur.execute("DELETE FROM interests WHERE resumeid=%s", (resume_id,))
            cur.execute("DELETE FROM resume WHERE resumeid=%s", (resume_id,))
        
        # Delete user
        cur.execute("DELETE FROM users WHERE userid=%s", (user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
    
    return redirect('/admin/users')

@app.route('/admin/delete_resume/<int:resume_id>', methods=['POST'])
def admin_delete_resume(resume_id):
    if not is_admin():
        return redirect('/login')
    
    try:
        # Delete from child tables first
        cur.execute("DELETE FROM education WHERE resumeid=%s", (resume_id,))
        cur.execute("DELETE FROM skills WHERE resumeid=%s", (resume_id,))
        cur.execute("DELETE FROM projects WHERE resumeid=%s", (resume_id,))
        cur.execute("DELETE FROM experience WHERE resumeid=%s", (resume_id,))
        cur.execute("DELETE FROM achievements WHERE resumeid=%s", (resume_id,))
        cur.execute("DELETE FROM courses WHERE resumeid=%s", (resume_id,))
        cur.execute("DELETE FROM interests WHERE resumeid=%s", (resume_id,))
        cur.execute("DELETE FROM resume WHERE resumeid=%s", (resume_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
    
    return redirect('/admin/resumes')

if __name__ == "__main__":
    app.run(debug=True)