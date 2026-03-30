from flask import Flask, render_template, request, redirect, session
import psycopg2

app = Flask(__name__)
app.secret_key = "secret"

conn = psycopg2.connect(
    dbname="resume_builder",
    user="postgres",
    password="011983",
    host="localhost"
)
cur = conn.cursor()

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

        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s",
                    (email,password))
        user = cur.fetchone()

        if user:
            session['user_id'] = user[0]
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

            conn.commit()
            return redirect('/resume')

        except Exception as e:
            conn.rollback()
            return f"An error occurred: {e}"

    return render_template('dashboard.html')
      

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
        
        resume_data.append({
            'resume': res,
            'edu': edu,
            'skills': skills,
            'projects': projects
        })

    return render_template('resume.html', resume_data=resume_data)

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

    conn.close()

    return render_template(
        "view_resume.html",
        res=res,
        skills=skills,
        edu=edu,
        projects=projects
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
        cur.execute("DELETE FROM resume WHERE resumeid=%s", (resumeid,))
        conn.commit()
    except Exception as e:
        conn.rollback()
    return redirect('/resume')

if __name__ == "__main__":
    app.run(debug=True)