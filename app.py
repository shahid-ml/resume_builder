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
    if request.method == 'POST':
        try:
            userid = session.get('user_id')
            degree = request.form.get('degree')
            institution = request.form.get('institution')
            skill = request.form.get('skill')
            project = request.form.get('project')

            # create new resume
            cur.execute(
                "INSERT INTO resume(userid, title) VALUES(%s, %s) RETURNING resumeid",
                (userid, "My Resume")
            )
            resumeid = cur.fetchone()[0]

            # save education
            cur.execute(
                "INSERT INTO education(userid,resumeid,degree,institution) VALUES(%s,%s,%s,%s)",
                (userid, resumeid, degree, institution)
            )

            # save skills
            cur.execute(
                "INSERT INTO skills(userid,resumeid,skillname) VALUES(%s,%s,%s)",
                (userid, resumeid, skill)
            )

            # save projects
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

if __name__ == "__main__":
    app.run(debug=True)