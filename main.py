from flask import Flask, render_template, redirect, request, abort
from data import db_session
from data.users import User
from data.dreams import Dreams
from forms.user import RegisterForm, LoginForm
from forms.dreams import DreamsForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/dreams.db")

    @login_manager.user_loader
    def load_user(user_id):
        db_sess = db_session.create_session()
        return db_sess.query(User).get(user_id)

    @app.route("/")
    def index():
        db_sess = db_session.create_session()
        if current_user.is_authenticated:
            dreams = db_sess.query(Dreams).filter(
                (Dreams.user == current_user) | (Dreams.is_private != True))
        else:
            dreams = db_sess.query(Dreams).filter(Dreams.is_private != True)
        return render_template("index.html", dreams=dreams)

    @app.route('/register', methods=['GET', 'POST'])
    def reqister():
        form = RegisterForm()
        if form.validate_on_submit():
            if form.password.data != form.password_again.data:
                return render_template('register.html', title='Регистрация',
                                       form=form,
                                       message="Пароли не совпадают")
            db_sess = db_session.create_session()
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return render_template('register.html', title='Регистрация',
                                       form=form,
                                       message="Такой пользователь уже есть")
            user = User(
                name=form.name.data,
                email=form.email.data,
            )
            user.set_password(form.password.data)
            db_sess.add(user)
            db_sess.commit()
            return redirect('/login')
        return render_template('register.html', title='Регистрация', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
        return render_template('login.html', title='Авторизация', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect("/")

    @app.route('/dreams', methods=['GET', 'POST'])
    @login_required
    def add_dreams():
        form = DreamsForm()
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            dreams = Dreams()
            dreams.title = form.title.data
            dreams.content = form.content.data
            dreams.is_private = form.is_private.data
            current_user.news.append(dreams)
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect('/')
        return render_template('dreams.html', title='Добавление сна',
                               form=form)

    @app.route('/dreams/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_dreams(id):
        form = DreamsForm()
        if request.method == "GET":
            db_sess = db_session.create_session()
            dreams = db_sess.query(Dreams).filter(Dreams.id == id,
                                              Dreams.user == current_user
                                              ).first()
            if dreams:
                form.title.data = dreams.title
                form.content.data = dreams.content
                form.is_private.data = dreams.is_private
            else:
                abort(404)
        if form.validate_on_submit():
            db_sess = db_session.create_session()
            dreams = db_sess.query(Dreams).filter(Dreams.id == id,
                                              Dreams.user == current_user
                                              ).first()
            if dreams:
                dreams.title = form.title.data
                dreams.content = form.content.data
                dreams.is_private = form.is_private.data
                db_sess.commit()
                return redirect('/')
            else:
                abort(404)
        return render_template('dreams.html',
                               title='Редактирование сна',
                               form=form
                               )

    @app.route('/dreams_delete/<int:id>', methods=['GET', 'POST'])
    @login_required
    def news_delete(id):
        db_sess = db_session.create_session()
        dreams = db_sess.query(Dreams).filter(Dreams.id == id,
                                          Dreams.user == current_user
                                          ).first()
        if dreams:
            db_sess.delete(dreams)
            db_sess.commit()
        else:
            abort(404)
        return redirect('/')

    app.run()


if __name__ == '__main__':
    main()
