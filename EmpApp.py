from flask import Flask, render_template, request, redirect, url_for, flash
from pymysql import connections, cursors
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb
)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route("/payroll", methods=['GET', 'POST'])
def payroll():
    return render_template('Payroll.html')

@app.route("/attendance", methods=['GET', 'POST'])
def attendance():
    return render_template('Attendance.html')

@app.route("/leave", methods=['GET', 'POST'])
def leave():
    return render_template('Leave.html')
@app.route("/nuke", methods=['GET'])
def NUKE():
    qStr = "DROP TABLE payroll"
    cursor = db_conn.cursor(cursors.DictCursor)
    try:
        cursor.execute(qStr)
        db_conn.commit()

    except Exception as e:
        print(str(e))
    finally:
        cursor.close()

def getEmp():

    qStr = "SELECT * FROM employee"
    cursor = db_conn.cursor(cursors.DictCursor)

    try:
        cursor.execute(qStr)
        emp = cursor.fetchall()
        print(emp)

    except Exception as e:
        print(str(e))
    finally:
        cursor.close()

    return emp

def getLeaves():

    qStr = "SELECT * FROM Leaves"
    cursor = db_conn.cursor(cursors.DictCursor)

    try:
        cursor.execute(qStr)
        leaves = cursor.fetchall()
        print(leaves)

    except Exception as e:
        print(str(e))
    finally:
        cursor.close()

    return leaves

@app.route("/delete_leave/<int:leave_id>", methods=['POST'])
def delete_leave(leave_id):
    empLeaves = getLeaves()

    qStr = "DELETE FROM Leaves WHERE leave_id=%s"
    cursor = db_conn.cursor(cursors.DictCursor)
    try:
        cursor.execute(qStr,(leave_id))
        db_conn.commit()

    except Exception as e:
        print(str(e))
    finally:
        cursor.close()
    
    return redirect(url_for('leaveTable'))

@app.route("/employee", methods=['GET', 'POST'])
def employee():

    #populate employees table
    employees = getEmp()

    return render_template('Employee.html', employees=employees)

@app.route("/emp", methods=['GET', 'POST'])
def emp():
    return render_template('AddEmp.html')

@app.route("/leaveTable", methods=['GET', 'POST'])
def leaveTable():

    #populate employees table // are the leave table and emp table same? 
    empLeaves = getLeaves()

    return render_template('LeaveTable.html', empLeaves=empLeaves)


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            print(str(e))

    finally:
        cursor.close()

    return render_template('Employee.html', employees=getEmp())

    #print("all modification done...")
    #return render_template('AddEmpOutput.html', name=emp_name)



@app.route("/addPayroll", methods=['POST'])
def AddSalary():
    empID = request.form['EmpID']
    empName = request.form['EmpName']
    empRate = request.form['EmpRate']
    empOT = request.form['EmpOT']
    empType = request.form.get('EmpType')
    print(empType)

    insert_sql = "INSERT INTO payroll (emp_ID, emp_Name, emp_Rate, emp_OT, emp_Type) VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    try:

        cursor.execute(insert_sql, (empID, empName, int(empRate), int(empOT), empType))
        db_conn.commit()
    
    finally:
        cursor.close()

    print("all modification done...")
    return render_template('Payroll.html')
 
# (B) HELPER FUNCTION - SEARCH USERS
def getusers(search):
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT * FROM payroll WHERE emp_ID=%s",
        (search)
    )
    results = cursor.fetchall()
    cursor.close()
    return results

@app.route("/searchPayroll", methods=['GET','POST'])
def searchPayroll():
    # (C1) SEARCH FOR USERS
    if request.method == "POST":
        data = dict(request.form)
        print(data)
        users = getusers(data["searchEmp"])
        print(users)
    else:
        users = []
    
    # (C2) RENDER HTML PAGE
    return render_template("Payroll.html", usr=users[0])


def getLastID():
    cursor = db_conn.cursor()

    try:
        cursor.execute("SELECT LAST_INSERT_ID()")
        id = cursor.fetchone()
    finally:
        cursor.close()

    print(id)
    return id

@app.route("/editPayroll", methods=['GET','POST'])
def searchEditPayroll():
    # (C1) SEARCH FOR USERS
    if request.method == "POST":
        data = dict(request.form)
        print(data)
        users = getusers(data["searchEmpPayroll"])
        print(users)
    else:
        users = []
    
    # (C2) RENDER HTML PAGE
    return render_template("Payroll.html")

@app.route("/applyLeave", methods=['POST'])
def applyLeave():
    data = request.form
    empId = data['empId']
    name = data['name']
    leaveType = data['leaveType']
    desc = data['desc']
    startDate = data['datemin']
    endDate = data['datemax']
    leave_image_file = request.files['leave_image_file']

    
    
    #print(request.form)

    insert_sql = "INSERT INTO Leaves (emp_id, emp_name, leave_desc, leave_type, leave_startDate, leave_endDate) VALUES (%s, %s, %s, %s, %s, %s);"
    cursor = db_conn.cursor()

    # if leave_image_file.filename == "":
    #     return "Please select a file"

    try:
        cursor.execute(insert_sql, (empId, name, desc, leaveType, startDate, endDate))
        db_conn.commit()
        leave_id = getLastID()

        if leave_image_file.filename != "":

            leave_image_file_name_in_s3 = "leave-id-" + str(leave_id) + "_image_file"
            s3 = boto3.resource('s3')

            try:
                print("Data inserted in MySQL RDS... uploading leave image to S3...")
                s3.Bucket(custombucket).put_object(Key=leave_image_file_name_in_s3, Body=leave_image_file)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location['LocationConstraint'])

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    custombucket,
                    leave_image_file_name_in_s3)

            except Exception as e:
                print(str(e))

        flash("Leave applied!", 'green')
    except Exception as e:
        print(str(e))
        flash('An error occured: '+ str(e), 'red')
    finally:
        cursor.close()

    return redirect(url_for('leave'))


if __name__ == '__main__':
    app.secret_key = "76541"
    app.run(host='0.0.0.0', port=80, debug=True)
