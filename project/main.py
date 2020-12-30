from flask import Flask,render_template,request,redirect,url_for,flash,session
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import requests
from edit import wordEdit
import random


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Lütfen Kayıt Olun veya Giriş Yapın","warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function




class RegisterForm(Form):
    username = StringField("Kullanıcı Adı", validators=[validators.length(min=4,max=25)])
    password = PasswordField("Parola",validators=[validators.length(min=4,max=25),validators.DataRequired(message="Lütfen parola girin"),validators.equal_to(fieldname="confirm")])
    confirm = PasswordField("Parola Doğrulama")

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")

class AnswerForm(Form):
    gridRadios = StringField("gridRadios")


app = Flask(__name__)
app.secret_key="dictonary"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/onurk/Desktop/project/database.db'
db = SQLAlchemy(app)

'x-rapidapi-key':
'x-rapidapi-host': "wordsapiv1.p.rapidapi.com"
headers = {
    }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password = db.Column(db.String(25), unique=True, nullable=False)

class Words(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(), unique=True, nullable=False)
    definitions = db.Column(db.String(), unique=True, nullable=False)

class UsersWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(), unique=False, nullable=False)
    userID = db.Column(db.Integer(), unique=False, nullable=False )
    point = db.Column(db.Integer(), unique=False, nullable=False)
    appeared=db.Column(db.Integer(), unique=False, nullable=False)
    searched=db.Column(db.Integer(), unique=False, nullable=False)
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        username= form.username.data
        password =sha256_crypt.hash(form.password.data)
        newUser= User(username=username,password=password)
        db.session.add(newUser)
        db.session.commit()
        flash("Başarıyla kayıt olundu...","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)


@app.route("/login",methods = ["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data
        userControl=User.query.filter_by(username=username).first()
        if(userControl!=None):
            passControl = userControl.password
            if sha256_crypt.verify(password,passControl):
                flash("Başarıyla Giriş Yapıldı...","success")
                session["logged_in"]=True
                session["username"]=username
                return redirect(url_for("index"))
            else:
                flash("Yanlış Parola Girdiniz...", "danger")
                return redirect(url_for("login"))

        else:
            flash("Kayıtlı Olmayan Kullanıcı...","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html", form=form)


@app.route("/search",methods = ["GET","POST"])
@login_required
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keywords")
        if len(keyword)==0:
            flash("Kelime girin...","warning")
            return redirect(url_for("index"))
        url = "https://wordsapiv1.p.rapidapi.com/words/" + keyword + "/definition"

        response = requests.request("GET", url, headers=headers)
        if response.text == """{"success":false,"message":"word not found"}""":
            flash("Kayıtlı Olmayan Kelime...","danger")
            return redirect(url_for("index"))
        else:
            con=wordEdit()
            word=con.title(definition=response.text)
            definitions=con.means(definition=response.text)
            custObj = Words.query.filter_by(word = word).first()
            if (custObj != None)  :
                username=session["username"]
                userID=User.query.filter_by(username=username).first()
                userID=userID.id
                ctrlsearch = UsersWord.query.filter_by(word = word,userID=userID).first()
                if (ctrlsearch != None):
                    searched=ctrlsearch.searched
                    ctrlsearch.searched=searched+1
                    db.session.commit()
                else:
                    pass

            else:
                newWord = Words(word=word, definitions=str(definitions))
                db.session.add(newWord)
                db.session.commit()

            return render_template("index.html", word=word,definitions=definitions)

@app.route("/logout",methods = ["GET","POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/save/<string:word>",methods = ["GET","POST"])
@login_required
def save(word):
    username=session["username"]
    userID =  User.query.filter_by(username=username).first()
    userID=userID.id
    ctrl = UsersWord.query.filter_by(word=word , userID=userID).first()
    if (ctrl != None):
        flash("kayıtlı kelime...", "warning")
        return redirect(url_for("index"))
    else:
        newUsersWord = UsersWord(word=word, userID=userID,searched=1,point=0,appeared=0)
        db.session.add(newUsersWord)
        db.session.commit()
        flash("kelime kaydedildi...", "success")
        return redirect(url_for("index"))


@app.route("/mywords",methods = ["GET","POST"])
@login_required
def mywords():
    list1=[]
    list2 = []
    list3 = []
    username=session["username"]
    userID =  User.query.filter_by(username=username).first()
    userID=userID.id
    mywords = UsersWord.query.filter_by(userID=userID).all()
    if (mywords == None):
        flash("Henüz kayıtlı kelimeniz bulunmamakta...", "info")
        return redirect(url_for("mywords"))
    else:
        for m in mywords:
            word=m.word
            list1.append(m.word)
            forPower=UsersWord.query.filter_by(userID=userID,word=word).first()
            searched=forPower.searched
            point=forPower.point
            appeared=forPower.appeared
            if appeared>0:
                point=(point/appeared)
            else:
                point=0
            searched=(1/searched)
            power=(point+searched)/2
            power=(power+1)*(searched+appeared)
            if power>100:
                power=100
            else:
                pass
            list3.append(power)
            definitions = Words.query.filter_by(word=word).first()
            definitions=definitions.definitions
            definitions = definitions.strip('[')
            definitions = definitions.strip(']')
            list2.append(definitions)
        lenght=len(list1)

        mywords = UsersWord.query.filter_by(userID=userID).all()
        return render_template("mywords.html", list1=list1,list2=list2,lenght=lenght,list3=list3)




deneme=["",""]
lforfalse=["","",""]
@app.route("/quiz",methods = ["GET","POST"])
@login_required
def quiz():
    username = session["username"]
    userID = User.query.filter_by(username=username).first()
    userID = userID.id
    mywords = UsersWord.query.filter_by(userID=userID).all()
    list = []
    for m in mywords:
        list.append(str(m.word))
    listforchic = []
    for i in range(3):
        word = random.choice(list)
        listforchic.append(str(word))
        list.remove(str(word))

    word = random.choice(listforchic)
    definitions = Words.query.filter_by(word=word).first()
    definitions = definitions.definitions
    definitions = definitions.strip('[')
    definitions = definitions.strip(']')
    deneme.insert(1,word)
    lforfalse.extend(listforchic)
    for i in listforchic:
        mywords = UsersWord.query.filter_by(userID=userID , word=i).first()
        appeared=mywords.appeared
        mywords.appeared=appeared+1
        db.session.commit()

    if request.method=="POST":
        tag=deneme[0]
        chics=lforfalse[0:3]

        gridRadios=request.form.get("options")
        if gridRadios == None:
            flash("seçim yapmalısınız","info")
            return redirect(url_for("quiz"))
        elif gridRadios == tag:
            mywords = UsersWord.query.filter_by(userID=userID, word=tag).first()
            point = mywords.point
            mywords.point = point + 1
            db.session.commit()
            flash("DOĞRU CEVAP )","info")

        else :
            for i in chics:
                mywords = UsersWord.query.filter_by(userID=userID, word=i).first()
                point = mywords.point
                mywords.point = point -1
                db.session.commit()
            mywords = UsersWord.query.filter_by(userID=userID, word=i).first()
            point = mywords.point
            mywords.point = point -1
            db.session.commit()
            flash("YANLIŞ CEVAP  DOĞRUSU: "+tag,"info")

    del deneme[0]
    for i in range(0, 3):
        del lforfalse[0]
    return render_template("quiz.html",definitions=definitions,listforchic=listforchic)

@app.route("/delete/<string:word>",methods = ["GET","POST"])
@login_required
def delete(word):
    username=session["username"]
    id=User.query.filter_by(username=username).first()
    userID=id.id
    obj = UsersWord.query.filter_by(userID=userID, word=word).first()
    if(obj != None):
        db.session.delete(obj)
        db.session.commit()
    else:
        pass
    return redirect(url_for("mywords"))



if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)