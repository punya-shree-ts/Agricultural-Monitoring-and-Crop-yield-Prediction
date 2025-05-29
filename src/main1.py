from flask import Flask, render_template, request,session,redirect,url_for
import pandas as pd
import sqlite3
import random
from PIL import Image
import os
import smtplib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.multioutput import MultiOutputClassifier 
from email.message import EmailMessage
from datetime import datetime
import jpgtonpz as convertimg
import NPK_Estimation as NPK

UPLOAD_FOLDER = './static/Uploads/'
#SPECIFIC_FOLDER='./staic/input/'
ALLOWED_EXTENSIONS = {'jpg','jpeg','png'}
label={"apple":0,"Banana":1,"Blackgram":2,"Chickpea":3,"Coconut":4,"coffee":5,"Cotton":6,"Grapes":7,"Jute":8,"Kidney Beans":9,"Lentil":10,"Maize":11,"Mango":12,"Mouth Beans":13,"Mungbeans":14,"Muskmelon":15,"Orange":16,"Papaya":17,"Pigeon Peas":18,"Pomegranate":19,"Rice":20,"Watermelon":21}
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Register the blueprint from the price.py file




@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template("index.html")
    else:
        return render_template('userhomepage.html')
    

@app.route('/croppage', methods=['GET','POST'])
def croppage():
    return render_template("croppage1.html")
@app.route('/loginpage', methods=['GET','POST'])
def loginpage():
    return render_template("uloginpage.html")
@app.route('/signuppage', methods=['GET','POST'])
def signuppage():
    return render_template("reg.html")
@app.route("/signup",methods=['GET','POST'])
def signup():
    global otp, username, name, email, number, password
    username = request.form['user']
    name = request.form['name']
    email = request.form['email']
    number = request.form['mobile']
    password = request.form['password']
    otp = random.randint(1000,5000)
    print(otp)
    msg = EmailMessage()
    msg.set_content("Your OTP is : "+str(otp))
    msg['Subject'] = 'OTP'
    msg['From'] = "poisonousplants2024@gmail.com"
    msg['To'] = email
    
    
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("poisonousplants2024@gmail.com", "wtfghdcknihmbaog")
    s.send_message(msg)
    s.quit()
    return render_template("otpverify.html",uname=username)
@app.route('/predict_lo', methods=['POST'])
def predict_lo():
    global otp, username, name, email, number, password
    if request.method == 'POST':
        message = request.form['message']
        print(message)
        if int(message) == otp:
            print("TRUE")
            con = sqlite3.connect('signup.db')
            cur = con.cursor()
            cur.execute("insert into `info` (`user`,`email`, `password`,`mobile`,`name`) VALUES (?, ?, ?, ?, ?)",(username,email,password,number,name))
            con.commit()
            con.close()
            return render_template("uloginpage.html")
    return render_template("uregpage.html")
@app.route("/signin",methods=['GET','POST'])
def signin():

    mail1 = request.form['user']
    password1 = request.form['password']
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("select `user`, `password` from info where `user` = ? AND `password` = ?",(mail1,password1,))
    data = cur.fetchone()

    if data == None:
        msg="Invalid username or Password"
        print("MSG===",msg)
        return render_template("uloginpage.html",msg=msg)    

    elif mail1 == str(data[0]) and password1 == str(data[1]):
        session['logged_in']=True
        return render_template("userhomepage.html")
    else:
        msg="Invalid username or Password"
        print("MSG===",msg)
        return render_template("uloginpage.html",msg=msg)
@app.route('/upload',methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        filename = uploaded_file.filename
        print("Filename==",filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        session['filename']=filename
        uploaded_file.save(file_path)
        convertimg.convert_image_to_npz(file_path,"static/Converted/"+filename+".npz")
        n,p,k,ph=NPK.process("static/Converted/"+filename+".npz")
        return render_template("croppage.html",n=n,p=p,k=k,ph=ph)
def get_key(val): 
    for key, value in label.items(): 
         if val == value: 
             return key 
@app.route("/predict",methods=['POST','GET'])
def predict():
    fname=session.get('filename')
    fertilizer=""
    n=request.form['n']
    p=request.form['p']
    k=request.form['k']
    ph=request.form['ph']
    print("N==",n)
    
    print("P==",p)
    print("K==",k)
    print("Ph==",ph)
    n = float(n)
    p = float(p)
    k = float(k)
    ph = float(ph)
    temperature=request.form['temperature']
    humidity=request.form['humidity']
    
    rainfall=request.form['rainfall']
    crop_data=pd.read_csv("Crop_recommendation.csv")
    crop_data.rename(columns = {'label':'Crop'}, inplace = True)
    crop_data = crop_data.dropna()
    x = crop_data[['N', 'P','K','temperature', 'humidity', 'ph', 'rainfall']]
    target = crop_data['Crop']
    print("Target==",target)
    y = pd.get_dummies(target)
    print("Y==",y)
    from sklearn.model_selection import train_test_split
    x_train,x_test,y_train,y_test = train_test_split(x,y,test_size=0.25, random_state= 0)
    gb_clf = GradientBoostingClassifier()
    MultiOutputClassifier(estimator=GradientBoostingClassifier(), n_jobs=-1)
    model = MultiOutputClassifier(gb_clf, n_jobs=-1)
    model.fit(x_train, y_train)
    x_test=[int(n),int(p),int(k),float(temperature),float(humidity),float(ph),float(rainfall)]
    x_test=np.array(x_test)
    x_test=x_test.reshape(1,-1)
    ypred=model.predict(x_test)
    print("Ypred==",ypred)
    print("Y-pred index==",np.argmax(ypred))
    sorted_index_array = np.argsort(ypred, axis=1) 
    print("sorted_index_array==",sorted_index_array)
    sorted_array = np.take_along_axis(ypred, sorted_index_array, axis=1)
    print("sorted_array==",sorted_array)
    
   
    predicted1=get_key(sorted_array[0][0])
    predicted2=get_key(sorted_array[0][1])
    #predicted3=get_key(rslt[2])
    actallabel=get_key(np.argmax(ypred))
    if actallabel=="apple":
        fertilizer="a balanced fertilizer with a ratio of nitrogen (N), phosphorus (P), and potassium (K). Look for a fertilizer with an N-P-K ratio of 10-10-10 or a similar balanced formulation."
    if actallabel=="Banana":
        fertilizer="Banana needs 150-200g N, 40-60g P2O5 and 200-300g K2O/plant/crop"
    if actallabel=="Blackgram":
        fertilizer="20:50 kg N and P2O5 ha-1 of RDF, along with 40 or 30 kg K2O ha-1 of potassium. You can also foliar spray with 1% KCl, 1% KH2PO4, or 0.5% KNO3 during flowering and pod development."
    if actallabel=="Chickpea":
        fertilizer="chickpea include 15-20 kg nitrogen (N) and 50–60 kg phosphorus (P) per ha. If soils are low in potassium (K) an application of 17 to 20 kg/ha K₂O is recommended."
    if actallabel=="Coconut":
        fertilizer="Organic Manure @50kg/palm or 30 kg green manure, 500 g N, 320 g P2O5 and 1200 g K2O/palm/year in two split doses during September and May."
    if actallabel=="Cotton":
        fertilizer="NPK and Mg are the major nutrients and Fe, B, S, and Zn are the microelements required by cotton. Though the NPK doses are determined after a soil analysis, in general Cotton requires 50 kg N, 30 kg P, and 35 Kg of K per acre."
    if actallabel=="Grapes":
        fertilizer="Urea (46-0-0) at 2 to 3 ounces (1/2 cup) or bloodmeal (12-0-0) at 8 ounces (1 ½ cups) per vine"
    if actallabel=="Jute":
        fertilizer="dose of fertilizer (100 % NPK) was sufficient for jute fibre yield while nutrient uptake was significantly higher with 150% NPK but at par only with 100% NPK + 10 tonnes FYM/ha when N and P are considered."
    if actallabel=="Kidney Beans":
        fertilizer="Simply apply OCP eco-aminogro and OCP eco-seaweed every 2-3 weeks to encourage bigger plants and better quality beans."
    if actallabel=="Lentil":
        fertilizer="Phosphorus 40 kg. and Sulphur 20 kg. per hectare in medium to low fertile soils as basal dressing. In lentil grown in calcareous alluvial soils, apply 1.6 kg of Boron per ha as basal to each crop."
    if actallabel=="Maize":
        fertilizer="Apply quarter of the dose of N (136 kg urea/ha); full dose of P2O (469 kg SSP) and K2O (125 kg MoP) basally before sowing."
    if actallabel=="Mango":
        fertilizer="50 grams of zinc sulphate, 50 grams of copper sulphate, and 20 grams of borax per tree/year "
    if actallabel=="Mouth Beans":
        fertilizer="Recommendation is 20-25 tonnes FYM for improving physical condition and improving water holding capacity of soil along with 10 kg N + 40 kg P2O5/ha as basal at the time of sowing or last preparation"
    if actallabel=="Mungbeans":
        fertilizer="For mungbean, 15-20 kg nitrogen, 30-40 kg phosphorus should be applied at sowing time."
    if actallabel=="Muskmelon":
        fertilizer=="Apply FYM 20 t/ha, NPK 40:60:30 kg/ha as basal and N @ 40 kg/ha 30 days after sowing."
    if actallabel=="Orange":
        fertilizer="Use a balanced, slow-release citrus fertilizer, like 6-4-6 or 8-3-9, applied every 6-8 weeks during the growing season"
    if actallabel=="Papaya":
        fertilizer="A fertilizer dose of 250 g N, 250 g P2O5 and 500 g K2O / plant / year recommended"
    if actallabel=="Pigeon Peas":
        fertilizer="Fertilizer recommendation. 8:20:15/ac. At Planting. AllP. 125kg SSP. Rhizobium"
    if actallabel=="Pomegranate":
        fertilizer="with a balanced ratio of nitrogen (N), phosphorus (P), and potassium (K). A balanced N-P-K ratio, such as 10-10-10 or 14-14-14, is generally suitable for pomegranate trees. "
    if actallabel=="Rice":
        fertilizer="Application of rock phosphate + single super phosphate or DAP mixed in different proportions (75:25 or 50:50) is equally effective as SSP or DAP alone."
    if actallabel=="Watermelon":
        fertilizer="Apply FYM 20 t/ha, P 55 kg and K 55 kg as basal and N 55 kg/ha 30 days after sowing."
    



    print("actallabel==",actallabel)
    return render_template("result.html",msg=actallabel,fertilizer=fertilizer,img_src=UPLOAD_FOLDER + fname,predicted1=predicted1)
@app.route("/logout")
def log_out():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
