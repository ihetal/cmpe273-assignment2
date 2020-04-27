# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 19:42:03 2020

@author: Hetal
"""

from flask import Flask, escape, request
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'files')
ALLOWED_EXTENSIONS = {'json'}
try:
    os.makedirs('my_folder')
except OSError as e:
    pass

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


testId =1
scantronId =1
tests ={}
submission ={}
@app.route('/', methods =['GET','POST'])
def hello():
    
    name = request.args.get("name", "World")
    return f'Hello, {escape(name)}!!!'

@app.route('/api/tests', methods =['POST'])
def createTest():
    global testId
    newTest = request.json
    id =testId
    tests[id]={"test id":id, "subject": newTest["subject"], "answer_keys":newTest["answer_keys"], "submissions":[]}
    testId+=1
    return json.dumps(tests[id])

@app.route('/api/tests/<int:id>/scantrons', methods =['POST'])
def uploadTests(id):
    global scantronId
    
    file = request.files['data']
    file.filename = str(scantronId)+".json"
    filepath = "http://localhost:5000/files/"+file.filename
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    scantronTest = json.load(open((os.path.join(app.config['UPLOAD_FOLDER'], file.filename))))
    
    score =0
    result ={}
    if id in tests:
        testAnswers = tests[id]
        for key in testAnswers["answer_keys"].keys():
            if(testAnswers["answer_keys"][key] == scantronTest["answers"][key]):
                score+=1
            result[key]= {"actual":scantronTest["answers"][key], "expected":testAnswers["answer_keys"][key]}

        s_Id = scantronId
        submission[s_Id]={"scantron_id":s_Id, "scantron_url":filepath,"name":scantronTest["name"],"subject":scantronTest["subject"],
        "score":score,"result":result}
        scantronId+=1
        tests[id]["submissions"].append(submission[s_Id])
        return(json.dumps(submission[s_Id]))   
    else:
        return("Test ID not found")
    return "Something went wrong!!"

@app.route('/api/tests/<int:id>', methods=['GET'])
def getSubmissions(id):
    if id in tests:
        return(json.dumps(tests[id]))
    else:
        return("Test ID not found")
    



if __name__ =="__main__":
    app.run()