import http.server
import json
import os
import urllib.parse
import urllib.request
import base64
import hashlib
import hmac
from datetime import datetime
from http import cookies
import uuid
import socketserver
import traceback

DATA_DIR = "data"
SUBMISSIONS_FILE = os.path.join(DATA_DIR, "submissions.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
COURSES_FILE = os.path.join(DATA_DIR, "courses.json")
os.makedirs(DATA_DIR, exist_ok=True)

# Admin password (for mock/dev purposes)
ADMIN_PWD = "elevate_admin_2026"

# Razorpay API Keys
RZP_KEY_ID = "rzp_test_SjmMrhkSJZmqVw"
RZP_KEY_SECRET = "QcYyKiSE6Csdq01U6gpYj3nr"
RZP_QR_LINK = "https://rzp.io/rzp/RGec1vv"

# Ensure initial data files exist
for file in [SUBMISSIONS_FILE, USERS_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f) if "submissions" in file else json.dump({}, f)

if not os.path.exists(COURSES_FILE):
    with open(COURSES_FILE, "w") as f:
        json.dump({}, f)

STATIC_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
SESSIONS = {}

# Load existing sessions
if os.path.exists(SESSIONS_FILE):
    try:
        with open(SESSIONS_FILE, "r") as f:
            SESSIONS = json.load(f)
    except:
        SESSIONS = {}

def save_sessions():
    try:
        with open(SESSIONS_FILE, "w") as f:
            json.dump(SESSIONS, f)
            f.flush()
    except Exception as e:
        print(f"[RECOVERABLE ERROR] Could not save sessions: {e}", flush=True)

class ElevateHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, format, *args):
        # Professional standard output logging
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

    def do_POST(self):
        try:
            # surgical path normalization
            parsed = urllib.parse.urlparse(self.path)
            clean_path = parsed.path
            
            if clean_path == "/api/contact": self.handle_form("contact")
            elif clean_path == "/api/admission": self.handle_form("admission")
            elif clean_path == "/api/login": self.handle_login()
            elif clean_path == "/api/logout": self.handle_logout()
            elif clean_path == "/api/payment": self.handle_payment()
            elif clean_path == "/api/create_order": self.handle_create_order()
            elif clean_path == "/api/verify_payment": self.handle_verify_payment()
            elif clean_path == "/api/admin/action": self.handle_admin_action()
            elif clean_path == "/api/admin/course": self.handle_course_admin()
            else:
                self.send_error(404, "API Endpoint Not Found")
        except Exception as e:
            print(f"[ERROR POST] {traceback.format_exc()}", flush=True)
            self.send_json(500, {"success": False, "message": "Server error occurred."})

    def do_GET(self):
        try:
            # surgical path normalization
            parsed = urllib.parse.urlparse(self.path)
            clean_path = parsed.path
            
            if clean_path == "/admin" or clean_path == "/admin/":
                self.send_response(302)
                self.send_header("Location", "/admin.html")
                self.end_headers()
                return
            elif clean_path == "/api/session":
                return self.handle_session()
            elif clean_path == "/api/courses":
                return self.serve_courses()
            elif clean_path == "/api/admin/data":
                return self.serve_admin_data()
            else:
                # Standard file serving always uses the clean path
                orig_path = self.path
                self.path = clean_path
                try:
                    super().do_GET()
                finally:
                    self.path = orig_path
        except Exception as e:
            print(f"[ERROR GET] {traceback.format_exc()}", flush=True)
            try: self.send_error(500, "Internal Server Error")
            except: pass

    def send_json(self, code, obj):
        try:
            response = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(response)
            self.wfile.flush()
        except BrokenPipeError:
            pass

    # --- LOGIC HANDLERS ---
    def handle_form(self, form_type):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8")
        
        if "application/json" in self.headers.get("Content-Type", ""):
            data = json.loads(raw_body)
        else:
            parsed = urllib.parse.parse_qs(raw_body)
            data = {k: v[0] for k, v in parsed.items()}

        data["type"] = form_type
        data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["id"] = f"{form_type[:3].upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        data["status"] = "Pending"
        
        with open(SUBMISSIONS_FILE, "r") as f:
            submissions = json.load(f)
        submissions.append(data)
        with open(SUBMISSIONS_FILE, "w") as f:
            json.dump(submissions, f, indent=2)

        self.send_json(200, {"success": True, "message": "Received successfully", "id": data["id"]})

    def handle_payment(self):
        content_length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        sub_id = data.get("id")
        
        with open(SUBMISSIONS_FILE, "r") as f:
            submissions = json.load(f)
        
        found = None
        for s in submissions:
            if s.get("id") == sub_id:
                s["status"] = "Paid"
                found = s
                break
        
        if found:
            with open(SUBMISSIONS_FILE, "w") as f:
                json.dump(submissions, f, indent=2)
            
            # Auto-enroll in USERS
            if found.get("type") == "admission" and found.get("email"):
                email = found["email"].strip().lower()
                with open(USERS_FILE, "r") as f:
                    users = json.load(f)
                if email not in users:
                    users[email] = {
                        "name": found.get("name", "User"),
                        "password": "password123",
                        "enrolled": []
                    }
                prog = found.get("program")
                if prog and prog not in users[email]["enrolled"]:
                    users[email]["enrolled"].append(prog)
                with open(USERS_FILE, "w") as f:
                    json.dump(users, f, indent=2)
            
            self.send_json(200, {"success": True, "message": "Enrollment completed."})
        else:
            self.send_json(404, {"success": False, "message": "Inquiry not found."})

    def handle_login(self):
        content_length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        email, pwd = data.get("email"), data.get("password")
        
        if email:
            email = email.strip().lower()
        
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
            
        if email in users and users[email].get("password") == pwd:
            token = str(uuid.uuid4())
            SESSIONS[token] = email
            save_sessions() # Persist the session
            
            resp = json.dumps({"success": True}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.send_header("Set-Cookie", f"session={token}; Path=/; HttpOnly; SameSite=Lax")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp)
            self.wfile.flush()
        else:
            self.send_json(401, {"success": False, "message": "Invalid credentials"})

    def handle_session(self):
        email = self.get_current_user()
        if not email: return self.send_json(200, {"success": False})
            
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        with open(COURSES_FILE, "r") as f:
            courses = json.load(f)
            
        user = users.get(email, {})
        enrolled_details = []
        for cid in user.get("enrolled", []):
            if cid in courses:
                enrolled_details.append({
                    "id": cid, "title": courses[cid]["title"],
                    "modules": courses[cid].get("modules", []),
                    "meet_link": courses[cid].get("meet_link", "")
                })
        self.send_json(200, {"success": True, "user": {"name": user.get("name"), "email": email}, "enrolled": enrolled_details})

    def handle_logout(self):
        token = ""
        if "Cookie" in self.headers:
            c = cookies.SimpleCookie(self.headers["Cookie"])
            if "session" in c:
                token = c["session"].value
        
        if token in SESSIONS:
            del SESSIONS[token]
            save_sessions()
            
        self.send_response(200)
        self.send_header("Set-Cookie", "session=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"success": True}).encode("utf-8"))

    def get_current_user(self):
        if "Cookie" in self.headers:
            c = cookies.SimpleCookie(self.headers["Cookie"])
            if "session" in c:
                return SESSIONS.get(c["session"].value)
        return None

    def serve_courses(self):
        with open(COURSES_FILE, "r") as f:
            self.send_json(200, json.load(f))

    def handle_create_order(self):
        """Create a Razorpay order server-side and return order_id to frontend."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
            
            amount_inr = int(data.get("amount", 0))
            receipt = data.get("receipt", f"rcpt_{uuid.uuid4().hex[:8]}")
            
            # Razorpay expects amount in paise (1 INR = 100 paise)
            amount_paise = amount_inr * 100
            
            order_payload = json.dumps({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt
            }).encode("utf-8")
            
            # Basic auth: key_id:key_secret base64 encoded
            credentials = base64.b64encode(f"{RZP_KEY_ID}:{RZP_KEY_SECRET}".encode()).decode()
            
            req = urllib.request.Request(
                "https://api.razorpay.com/v1/orders",
                data=order_payload,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req) as resp:
                order = json.loads(resp.read().decode("utf-8"))
            
            self.send_json(200, {
                "success": True,
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "key_id": RZP_KEY_ID,
                "qr_link": RZP_QR_LINK
            })
        except Exception as e:
            print(f"[Razorpay Order Error] {traceback.format_exc()}", flush=True)
            # Fallback: return QR link if Razorpay API fails
            self.send_json(200, {
                "success": True,
                "fallback": True,
                "qr_link": RZP_QR_LINK,
                "key_id": RZP_KEY_ID
            })

    def handle_verify_payment(self):
        """Verify Razorpay payment signature and enroll the student."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
            
            order_id = data.get("razorpay_order_id", "")
            payment_id = data.get("razorpay_payment_id", "")
            signature = data.get("razorpay_signature", "")
            submission_id = data.get("submission_id", "")
            email = data.get("email", "").strip().lower()
            
            # Verify HMAC-SHA256 signature
            msg = f"{order_id}|{payment_id}"
            expected = hmac.new(
                RZP_KEY_SECRET.encode("utf-8"),
                msg.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            if expected != signature:
                return self.send_json(400, {"success": False, "message": "Payment verification failed"})
            
            # Payment is genuine — mark submission as Paid and create user account
            if submission_id:
                with open(SUBMISSIONS_FILE, "r") as f: subs = json.load(f)
                for s in subs:
                    if s["id"] == submission_id:
                        s["status"] = "Paid"
                        s["payment_id"] = payment_id
                        break
                with open(SUBMISSIONS_FILE, "w") as f: json.dump(subs, f, indent=2)
            
            if email:
                with open(USERS_FILE, "r") as f: users = json.load(f)
                program = data.get("program", "")
                if email not in users:
                    users[email] = {"name": data.get("name", "Student"), "password": "password123", "enrolled": []}
                if program and program not in users[email]["enrolled"]:
                    users[email]["enrolled"].append(program)
                with open(USERS_FILE, "w") as f: json.dump(users, f, indent=2)
            
            self.send_json(200, {
                "success": True,
                "message": f"Payment verified! Welcome to Elevate Global. Login with {email}."
            })
        except Exception as e:
            print(f"[Razorpay Verify Error] {traceback.format_exc()}", flush=True)
            self.send_json(500, {"success": False, "message": "Verification error"})



    def serve_admin_data(self):
        # Check simple auth header or query for basic protection during testing
        auth = self.headers.get("Authorization")
        if auth != f"Bearer {ADMIN_PWD}":
            # For simplicity in this demo, check a query param if header is missing
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            if params.get("key", [""])[0] != ADMIN_PWD:
                return self.send_json(403, {"success": False, "message": "Unauthorized"})

        with open(SUBMISSIONS_FILE, "r") as f: subs = json.load(f)
        with open(USERS_FILE, "r") as f: users = json.load(f)
        with open(COURSES_FILE, "r") as f: courses = json.load(f)
        self.send_json(200, {"success": True, "submissions": subs, "users": users, "courses": courses})

    def handle_admin_action(self):
        content_length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        # Verify Key
        if data.get("key") != ADMIN_PWD: return self.send_json(403, {"success": False})

        sub_id, action = data.get("id"), data.get("action")
        if action == "mark_enrolled":
            with open(SUBMISSIONS_FILE, "r") as f: subs = json.load(f)
            found = next((s for s in subs if s["id"] == sub_id), None)
            if found:
                found["status"] = "Enrolled"
                with open(SUBMISSIONS_FILE, "w") as f: json.dump(subs, f, indent=2)
                if found.get("email"):
                    with open(USERS_FILE, "r") as f: users = json.load(f)
                    em = found["email"]
                    if em not in users: users[em] = {"name": found.get("name", "User"), "password": "password123", "enrolled": []}
                    if found.get("program") and found["program"] not in users[em]["enrolled"]:
                        users[em]["enrolled"].append(found["program"])
                    with open(USERS_FILE, "w") as f: json.dump(users, f, indent=2)
            self.send_json(200, {"success": True})
        
        elif action == "save_user":
            email = data.get("email", "").strip().lower()
            if not email: return self.send_json(400, {"success": False, "message": "Email required"})
            
            with open(USERS_FILE, "r") as f: users = json.load(f)
            
            name = data.get("name", "Student")
            password = data.get("password", "password123")
            enrolled = data.get("enrolled", [])
            
            if email not in users:
                users[email] = {"name": name, "password": password, "enrolled": enrolled}
            else:
                if name: users[email]["name"] = name
                if password: users[email]["password"] = password
                users[email]["enrolled"] = enrolled
                
            with open(USERS_FILE, "w") as f: json.dump(users, f, indent=2)
            self.send_json(200, {"success": True})

    def handle_course_admin(self):
        content_length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        if data.get("key") != ADMIN_PWD: return self.send_json(403, {"success": False})

        cid, action = data.get("course_id"), data.get("action")
        with open(COURSES_FILE, "r") as f: courses = json.load(f)
        if cid in courses:
            if action == "update_meet": courses[cid]["meet_link"] = data.get("meet_link", "")
            elif action == "add_module":
                if "modules" not in courses[cid]: courses[cid]["modules"] = []
                courses[cid]["modules"].append({"title": data.get("title", ""), "link": data.get("link", "")})
            with open(COURSES_FILE, "w") as f: json.dump(courses, f, indent=2)
            self.send_json(200, {"success": True})

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True

if __name__ == "__main__":
    PORT = 8080
    server = ThreadedHTTPServer(("", PORT), ElevateHandler)
    print("=" * 60)
    print(" Elevate Global - Robust Multithreaded LMS Backend")
    print(f" Website : http://localhost:{PORT}")
    print(f" Admin Default Key : {ADMIN_PWD}")
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
