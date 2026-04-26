"""Admin panel and authentication routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user
from auth import authenticate_user
from logging_utils import read_chatlog, clear_chatlog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = authenticate_user(username, password)
        if user:
            login_user(user)
            return redirect(url_for("admin.view_chatlog"))
        return render_template("login.html", error="Invalid username or password.")
    return render_template("login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


@admin_bp.route("/chatlog")
@login_required
def view_chatlog():
    lines = read_chatlog()
    return render_template("chatlog.html", lines=lines)


@admin_bp.route("/clear_chatlog", methods=["POST"])
@login_required
def clear_chatlog_route():
    clear_chatlog()
    flash("Chat log cleared.")
    return redirect(url_for("admin.view_chatlog"))
