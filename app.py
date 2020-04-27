# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 19:42:03 2020

@author: Hetal
"""

from flask import Flask, escape, request
import json
import os
import sqlite3
from sqlite3 import Error
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'files')

try:
    os.makedirs(UPLOAD_FOLDER)
except OSError as e:
    pass

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def sql_connection():
    try:
        con = sqlite3.connect('scantrondatabase.db')
        return con
    except Error:
        print(Error)


@app.route('/', methods=['GET', 'POST'])
def hello():
    name = request.args.get("name", "World")
    return f'Hello, {escape(name)}!!!'


@app.route('/api/tests', methods=['POST'])
def createTest():
    subject = request.get_json()["subject"]
    answer_keys = request.get_json()["answer_keys"]
    conn = sql_connection()
    cursor = conn.cursor()
    test = cursor.execute(
        '''INSERT INTO tests (subject) VALUES(?)''', [subject])
    answers = [(test.lastrowid, key, value)
               for key, value in answer_keys.items()]
    cursor.executemany(
        '''INSERT INTO answerkeys (testid,question,answer) VALUES(?,?,?)''', answers)
    conn.commit()
    response = {"test id": test.lastrowid, "subject": subject,
                "answer_keys": answer_keys, "submissions": []}
    return json.dumps(response)


@app.route('/api/tests/<int:id>/scantrons', methods=['POST'])
def uploadTests(id):

    conn = sql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tests WHERE ID =?", [id])
    testId = cursor.fetchone()
    if testId != None:
        file = request.files['data']
        filepath = "http://localhost:5000/files/"+file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        scantronTest = json.load(
            open((os.path.join(app.config['UPLOAD_FOLDER'], file.filename))))
        cursor.execute(
            "SELECT question, answer from answerkeys where testid = ?", [id])
        correctAnswers = cursor.fetchall()
        answerKeys = {row[0]: row[1] for row in correctAnswers}
        result = {}
        score = 0

        for key in answerKeys.keys():
            if(answerKeys[key] == scantronTest["answers"][key]):
                score += 1
            result[key] = {"actual": scantronTest["answers"]
                           [key], "expected": answerKeys[key]}

        scantronSubmission = cursor.execute('''INSERT INTO submissions (testid, name, subject, scantronurl,score) VALUES (?,?,?,?,?)''', (
            id, scantronTest["name"], scantronTest["subject"], filepath, score))
        scoreDetails = [(id, scantronSubmission.lastrowid, key, values["actual"],
                         values["expected"]) for key, values in result.items()]
        cursor.executemany(
            '''INSERT INTO scoredetails (testid,scantronid,question,actual,expected) VALUES(?,?,?,?,?)''', scoreDetails)
        conn.commit()
        response = {"scantron_id": scantronSubmission.lastrowid, "scantron_url": filepath, "name": scantronTest["name"], "subject": scantronTest["subject"],
                    "score": score, "result": result}
        return json.dumps(response)
    else:
        return "Test ID not found!"

    return "Something went wrong!!"


@app.route('/api/tests/<int:id>', methods=['GET'])
def getSubmissions(id):
    conn = sql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tests WHERE ID =?", [id])
    tests = cursor.fetchone()
    submission = []
    if tests != None:
        cursor.execute("SELECT * from submissions where testid = ?", [id])
        submissionDetails = cursor.fetchall()
        for row in submissionDetails:
            scantronid = row[0]
            result = {}
            cursor.execute(
                "SELECT * from scoredetails where scantronid = ?", [scantronid])
            scoreDetails = cursor.fetchall()
            for score in scoreDetails:
                result[score[3]] = {"actual": score[4], "expected": score[5]}

            submission.append({
                "scantron_id": scantronid, "scantron_url": row[4], "name": row[2], "subject": row[3], "score": row[4], "result": result
            })
        cursor.execute(
            "SELECT question, answer from answerkeys where testid = ?", [id])
        correctAnswers = cursor.fetchall()
        answerKeys = {row[0]: row[1] for row in correctAnswers}

        response = {"test_id": tests[0], "subject": tests[1],
                    "answer_keys": answerKeys, "submissions": submission}

        return json.dumps(response)

    else:
        return("Test ID not found")


if __name__ == "__main__":
    app.run()
