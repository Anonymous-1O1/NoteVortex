from flask import Blueprint,current_app,render_template,session,redirect,abort,url_for,request,flash
from notevortex.forms import LoginForm,RegistorForm,AddNote,EditNote
from notevortex.models import User,Note
from passlib.hash import pbkdf2_sha256
from dataclasses import asdict
import uuid
from datetime import datetime
import functools
from cryptography.fernet import Fernet


pages=Blueprint("pages",__name__,template_folder="templates",static_folder="static")

def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args,**kwargs):
        if session.get("email") is None:
            return redirect(url_for(".login"))
        return route(*args,**kwargs)
    return route_wrapper


def encrypt_note(note:Note):
    note.title=(Fernet(current_app.config["title_crypt"].encode()).encrypt(note.title.encode())).decode()
    note.content=(Fernet(current_app.config["content_crypt"].encode()).encrypt(note.content.encode())).decode()
    return note

def decrypt_note(note:Note):
    note.title=(Fernet(current_app.config["title_crypt"].encode()).decrypt(note.title.encode())).decode()
    note.content=(Fernet(current_app.config["content_crypt"].encode()).decrypt(note.content.encode())).decode()
    return note

@pages.route("/",methods=["POST","GET"])
@login_required
def index():
    user=User(**current_app.db.user.find_one({"_id":session.get("_id")}))
    notes_data,notes,pinned_notes=[],[],[]
    for _id in user.notes:
        if current_app.db.notes.find_one({"_id":_id}):
            notes_data.append(current_app.db.notes.find_one({"_id":_id}))
    for note in [decrypt_note(Note(**note)) for note in notes_data][::-1]:
        if note.pinned:
            pinned_notes.append(note)
        else:
            notes.append(note)
    return render_template("index.html",title="NoteVortex",notes=notes,pinned_notes=pinned_notes)

@pages.route("/add_note",methods=["POST","GET"])
@login_required
def add_note():
    user=User(**current_app.db.user.find_one({"_id":session.get("_id")}))
    form=AddNote()
    if form.validate_on_submit():
        note=Note(
            _id=uuid.uuid4().hex,
            title=(form.title.data).strip(),
            content=form.content.data.strip()
        )

        if not note.content:
            flash("⚠ Content is empty",category="danger")
            return redirect(url_for('.add_note'))
        
        if not note.title:
            if len(note.content)<=30:
                note.title=note.content
            else:
                note.title=f"{note.content[:30]}..."
        
        note=encrypt_note(note)
        current_app.db.notes.insert_one(asdict(note))
        current_app.db.user.update_one({"_id":session.get("_id")},{"$push":{"notes":note._id}})
        return redirect(url_for('.index'))

    return render_template("add_edit_note.html",title="NoteVortex - add note",form=form)

@pages.route("/login",methods=["GET","POST"])
def login():
    if session.get("email"):
        return redirect(url_for(".index"))
    form=LoginForm()
    if form.validate_on_submit():
        user_data=current_app.db.user.find_one({"email":form.email.data})
        if not user_data:
            flash("⚠ Login credentials are incorrect",category="danger")
            return redirect(url_for('.login'))
        user=User(**user_data)
        if user and pbkdf2_sha256.verify(form.password.data,user.password):
            session["_id"]=user._id
            session["email"]=user.email
            return redirect(url_for('.index'))
        flash("⚠ Login credentials are incorrect",category="danger")
    return render_template("login.html",form=form,title="NoteVortex - Login")

@pages.route("/register",methods=["GET","POST"])
def register():
    if session.get("email"):
        return redirect(url_for(".index"))
    form=RegistorForm()
    if form.validate_on_submit():
        user=User(
            _id=uuid.uuid4().hex,
            email=form.email.data,
            password=pbkdf2_sha256.hash(form.password.data)
        )

        if current_app.db.user.find_one({"email":user.email}):
            flash("⚠ Account already exists with this email",category="danger")
            return redirect(url_for('.register'))
        
        current_app.db.user.insert_one(asdict(user))
        flash("User succesfully registered",category="success")
        return redirect(url_for('.login'))
    return render_template("register.html",title="NoteVortex - Register",form=form)

@pages.route("/logout")
@login_required
def logout():
    current_theme=session.get("theme")
    session.clear()
    session["theme"]=current_theme
    return redirect(url_for('.index'))

@pages.get("/change_theme")
def change_theme():
    current_theme=session.get("theme")
    if current_theme=="dark":
        session["theme"]="light"
    else:
        session["theme"]="dark"
    return redirect(request.args.get("current_page"))



@pages.route("/note/<string:_id>/delete")
@login_required
def delete_note(_id:str):
    if not _id in User(**current_app.db.user.find_one({"_id":session.get("_id")})).notes:
        abort(401)
    current_app.db.notes.delete_one({"_id":_id})
    user_data=current_app.db.user.find_one({"_id":session.get("_id")})
    user=User(**user_data)
    user.notes.pop(user.notes.index(_id))
    current_app.db.user.replace_one(current_app.db.user.find_one({"_id":session.get("_id")}),asdict(user))
    return redirect(url_for('.index'))

@pages.route("/notes/<string:_id>/edit",methods=["POST","GET"])
@login_required
def edit_note(_id:str):
    if not _id in User(**current_app.db.user.find_one({"_id":session.get("_id")})).notes:
        abort(401)
    note=decrypt_note(Note(**(current_app.db.notes.find_one({"_id":_id}))))
    form=EditNote(obj=note)
    if form.validate_on_submit():
        
        if not form.content.data.strip():
            flash("⚠ Content is empty",category="danger")
            return redirect(url_for('.add_note'))
        note.title=form.title.data
        note.content=form.content.data.strip()
        if not note.title:
            if len(note.content)<=30:
                note.title=note.content
            else:
                note.title=f"{note.content[:30]}..."



        note.last_edited=datetime.today().strftime("%d/%m/%Y")
        note=encrypt_note(note)
        current_app.db.notes.replace_one(current_app.db.notes.find_one({"_id":_id}),asdict(note))
        return redirect(url_for('.index'))
    return render_template("add_edit_note.html",title="NoteVortex",form=form)

@pages.route("/notes/<string:_id>/view")
@login_required
def view_note(_id:str):
    if not _id in User(**current_app.db.user.find_one({"_id":session.get("_id")})).notes:
        abort(401)
    note=decrypt_note(Note(**current_app.db.notes.find_one({"_id":_id})))
    return render_template("view.html",title="NoteVortex - View",note=note)

@pages.route("/note/<string:_id>/change_pin")
@login_required
def change_pin(_id:str):
    if not _id in User(**current_app.db.user.find_one({"_id":session.get("_id")})).notes:
        abort(401)
    note=Note(**(current_app.db.notes.find_one({"_id":_id})))
    if note.pinned:
        note.pinned=False
    else:
        note.pinned=True

    current_app.db.notes.replace_one(current_app.db.notes.find_one({"_id":_id}),asdict(note))
    return redirect(url_for('.index'))
