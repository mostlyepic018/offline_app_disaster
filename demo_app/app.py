import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests

BASE = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1:8000")

app = Flask(__name__)

# ---------- Mock Phone ----------
@app.route("/")
@app.route("/mock")
def mock_phone():
    return render_template("mock.html", base=BASE)

@app.post("/send-inbound")
def send_inbound():
    frm = request.form.get("from") or ""
    msg = request.form.get("message") or ""
    r = requests.post(f"{BASE}/receive-sms", json={"from": frm, "message": msg})
    return jsonify(r.json())

@app.get("/get-outbound")
def get_outbound():
    phone = request.args.get("phone")
    limit = request.args.get("limit", 200)
    params = {"limit": limit}
    if phone:
        params["phone"] = phone
    r = requests.get(f"{BASE}/gateway/outbound", params=params)
    return jsonify(r.json())

@app.post("/mark-sent")
def mark_sent():
    ids = request.json or []
    r = requests.post(f"{BASE}/gateway/mark-sent", json=ids)
    return jsonify(r.json())

# ---------- Admin ----------
@app.get("/admin")
def admin_home():
    pend = requests.get(f"{BASE}/disasters/pending").json()
    actv = requests.get(f"{BASE}/disasters/active").json()
    helpq = requests.get(f"{BASE}/messages/help").json()
    return render_template("admin.html", base=BASE, pending=pend, active=actv, helpq=helpq)

@app.post("/approve/<int:did>")
def approve(did: int):
    lat = request.form.get("lat")
    lng = request.form.get("lng")
    body = {"approve": True}
    if lat and lng:
        body.update({"lat": float(lat), "lng": float(lng)})
    requests.post(f"{BASE}/disasters/{did}/verify", json=body)
    return redirect(url_for('admin_home'))

@app.post("/reject/<int:did>")
def reject(did: int):
    requests.post(f"{BASE}/disasters/{did}/verify", json={"approve": False})
    return redirect(url_for('admin_home'))

@app.post("/add-user")
def add_user():
    phone = request.form.get("phone")
    lat = request.form.get("lat")
    lng = request.form.get("lng")
    payload = {"phone": phone}
    if lat: payload["last_lat"] = float(lat)
    if lng: payload["last_lng"] = float(lng)
    requests.post(f"{BASE}/users", json=payload)
    return redirect(url_for('admin_home'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
