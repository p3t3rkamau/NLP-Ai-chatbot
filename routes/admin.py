"""
routes/admin.py - Admin panel and authentication routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, login_user
from auth import authenticate_user
from logging_utils import read_chatlog, clear_chatlog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """Admin login page."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = authenticate_user(username, password)
        if user:
            login_user(user)
            return redirect(url_for("admin.view_chatlog"))
        return render_template("login.html", error="Invalid username or password.")
    return render_template("login.html")


@admin_bp.route("/chatlog")
@login_required
def view_chatlog():
    """View chatlog entries."""
    lines = read_chatlog()
    return render_template("chatlog.html", lines=lines)


@admin_bp.route("/clear_chatlog", methods=["POST"])
@login_required
def clear_chatlog_route():
    """Clear all chatlog entries."""
    clear_chatlog()
    flash("Chat log cleared.")
    return redirect(url_for("admin.view_chatlog"))
