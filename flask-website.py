from flask import Flask, render_template, redirect, request, flash, url_for, session
from flask_bootstrap import Bootstrap
from functools import wraps
from flask_googlemaps import GoogleMaps

from flask_wtf import Form, RecaptchaField, FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email, Length, AnyOf, EqualTo

from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired     ## burada gonderdigimiz onay emailinin gecerli oldugu sureyi koyabiliyoruz. ( timed olanda )

app= Flask(__name__)
Bootstrap(app)

s= URLSafeTimedSerializer('thisissecret!')

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'berkelmas96@gmail.com'
app.config['MAIL_PASSWORD'] = 'Berkerberk693693'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

app.config['SECRET_KEY'] = 'kimseyesoyleme'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lc5OnEUAAAAABgsN-tJJe2An78g1DZRc64AqcYg'
app.config['reCAPTCHA_PRIVATE_KEY'] = '6Lc5OnEUAAAAAADMfKH5wsTKr4h8aWhPr_UevdCC'

app.config['MYSQL_HOST'] = 'localhost'
app.config["MYSQL_USER"]= "root" 
app.config["MYSQL_PASSWORD"]= "berk693693"
app.config["MYSQL_DATABASE_PORT"]= 3306   
app.config["MYSQL_DB"]= "kullanicilar"

GoogleMaps(app) 
mysql= MySQL(app)
mail= Mail(app)     ## flask mail baglantimizi kuruyoruz.

## Kullanici giris decarator'umuz.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:      ## eger kullanici giris yaptiysa burasi True gelecek. 
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfayı görüntülemek için giriş yapmalısınız.", "danger")
            return redirect(url_for("giris"))
    return decorated_function
###########


class RegisterForm(FlaskForm):
    isim= StringField('İsim: ', validators=[InputRequired()])
    soyisim= StringField('Soyisim: ', validators=[InputRequired()])
    username= StringField('Kullanıcı Adı: ', validators= [InputRequired(message="Lutfen bos birakmayin.")])
    email= StringField('E-Mail: ', validators=[InputRequired()])
    password= PasswordField('Şifre: ', validators=[Length(min=5, max=20), InputRequired(), EqualTo(fieldname= 'confirm', message="Girdiginiz sifreler uyusmuyor.")])
    confirm= PasswordField('Şifreyi Dogrula: ', validators=[InputRequired()])
    #recaptcha= RecaptchaField()

class LoginForm(FlaskForm):
    username= StringField('Kullanıcı Adı: ', validators= [InputRequired(message="Lutfen bos birakmayin.")])
    password= PasswordField('Şifre: ', validators=[Length(min=5, max=20), InputRequired()])


@app.route("/")
def anasayfa():
    return render_template("anasayfa.html")

@app.route("/deneme")
def deneme():
    return render_template("deneme.html")

@app.route("/kayitol", methods= ['POST', 'GET'])
def kayitol(): 
    form = RegisterForm(request.form)
    """
    if form.validate_on_submit():
    """
    if request.method == 'POST': 
        if form.validate_on_submit():
            username= form.username.data
                                             ## Burada datalarimizi form elementlerimizden cekiyoruz.
            password= form.password.data
            isim= form.isim.data
            soyisim= form.soyisim.data

            email= form.email.data          ## emailimize hesap onayi icin mail gonderecegiz. Bu nedenle parametre gozumun onunde olsun diye buraya koydum.
            token= s.dumps(email, salt='email-confirmation')

            ## daha once ayni email veya username'in olup olmadigina gore kullanici kaydini engelleme komutu:
            cursor= mysql.connection.cursor()
            
            email_sorgu= 'select email from kullanici where email= %s'
            cursor.execute(email_sorgu,(email,))
            sayi_email = cursor.fetchall()

            username_sorgu= 'select username from kullanici where username= %s'
            cursor.execute(username_sorgu,(username,))
            sayi_username= cursor.fetchall()

            if len(sayi_email) == 0 and len(sayi_username) == 0:            ## Burada daha once ayni isimde email veya kullanici adi olup olmadigini buluyoruz.
                
                msg = Message(
                        'Flask-Website Üyelik Onayı',
                        sender='berkelmas96@gmail.com',
                        recipients=
                        [email])
            

            
                msg.body='Flask-Websitesi Üyelik Onayı\n\nÜyeliğinizi onaylamak için aşağıdaki linke tıklayabilirsiniz.\nlocalhost:5000/confirm_email/{}'.format(token) + '.txt'
                msg.html=render_template('mail_html.html', token=token)         ## Buradaki gibi cift msg'yi html formatinda email gonderebilmek icin yaptik.
                mail.send(msg)
                
                cursor= mysql.connection.cursor()
                
                sorgu_ekle= "insert into kullanici(isim, soyisim, username, email, password) values(%s, %s, %s, %s, %s)" 
                cursor.execute(sorgu_ekle,(isim, soyisim, username, email, password)) 
                mysql.connection.commit()   ## veritabaninda degisiklik yaptigimiz icin commit fonksiyonumuzu kullandık.
            
                flash("Tebrikler, başarı ile kaydınız gerçekleştirildi.", "success")

                cursor.close()  # burada da veritabani baglantimizi kapattik. 

                return render_template('hesapaktiflestir.html', email=email, token= token)
            elif len(sayi_email) > 0:
                flash("Bu mail ile daha once kayit yapilmis, sifrenizi mi unuttunuz?", "danger")
                return render_template("kayitol.html", form= form)
            elif len(sayi_username) > 0:
                flash("Bu kullanıcı adı daha önce alınmış, şifrenizi mi unuttunuz?", "danger")
                return render_template("kayitol.html", form= form)
            else:
                flash("Validatorler onaylanmadi.", "danger")
                return render_template("kayitol.html", form= form)

    else:
        
        return render_template("kayitol.html", form= form)

@app.route("/confirm_email/<token>")
def email_confirm(token):
    email = s.loads(token, salt="email-confirmation")
    
    ## sql baglantimiz ile hesabin aktiflik durumunu degistirelim. 
    cursor= mysql.connection.cursor()
    sorgu_aktif= "update kullanici SET aktiflik = 1 where email= %s"
    cursor.execute(sorgu_aktif,(email,))
    mysql.connection.commit()

    cursor.close()

    flash("tebrikler, email adresiniz onaylandi, hesabiniz kullanima hazir.")
    return render_template("mail_onaylandi.html")

@app.route('/giris', methods= ['POST', 'GET'])
def giris(): 
    form= LoginForm(request.form)
        ## Formdan verilerimzi aliyoruz.

    if request.method == 'POST':
        username= form.username.data
        password= form.password.data
            ## Database baglantimizi sagliyoruz.
        cursor= mysql.connection.cursor()

        sorgu_username= 'select username from kullanici where username= %s'
        cursor.execute(sorgu_username,(username,))
        data_username= cursor.fetchall()
        if len(data_username) > 0: 
            sorgu_password= 'select password from kullanici where username= %s and password= %s'
            cursor.execute(sorgu_password,(username, password))
            data_password= cursor.fetchall()
            if len(data_password) > 0: 
                sorgu_aktiflik= 'select aktiflik from kullanici where username= %s and password= %s and aktiflik= %s'
                aktiflik= 1
                cursor.execute(sorgu_aktiflik,(username, password, aktiflik))
                data_aktiflik= cursor.fetchall()
                if len(data_aktiflik) > 0:
                    session['logged_in'] = True
                    session['username'] = username
                    flash("Kullanıcı  Girişi Başarılı.", 'success')
                    return render_template('giris.html', form= form)
                else:
                    flash("Hesabiniz su an aktif degil, lutfen hesabiniza gelen maili onaylayarak aktif hale getirin.", 'danger')
                    return render_template('giris.html', form= form)
            else:
                flash("Parola yanlis, lutfen tekrar deneyin.", 'danger')
                return render_template('giris.html', form= form)
        else: 
            flash("boyle bir kullanici bulunmuyor.", 'danger')
            return render_template("giris.html", form= form)
    else: 
        ## method GET oldugunda direk html sayfamizi cagiriyoruz.
        return render_template("giris.html", form= form)


@app.route('/cikisyap')
def cikisyap():
    session.clear()
    flash('Tebrikler, basari ile cikis yaptiniz.', 'warning')
    return redirect(url_for('giris'))

if __name__ == "__main__":
    app.run(debug= True)



