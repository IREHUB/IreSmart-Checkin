import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import csv

# ================= DATABASE =================
conn = sqlite3.connect("attendance_system.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    username TEXT UNIQUE,
    password TEXT,
    approved INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER,
    timestamp TEXT,
    date TEXT,
    status TEXT,
    UNIQUE(staff_id, date)
)
""")

cursor.execute("SELECT * FROM admin WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO admin (username,password) VALUES ('admin','admin123')")
conn.commit()

# ================= UI HELPERS =================
def clear():
    for w in root.winfo_children():
        w.destroy()

def card(title):
    wrapper = tk.Frame(root, bg="#e9edf3")
    wrapper.pack(fill="both", expand=True)

    frame = tk.Frame(wrapper, bg="grey", bd=2, relief="ridge")
    frame.place(relx=0.5, rely=0.5, anchor="center", width=950, height=550)

    tk.Label(frame, text=title, bg="white",
             font=("Segoe UI", 18, "bold")).pack(pady=15)
    ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=20)

    return frame

def styled_table(parent, cols):
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview",
                    font=("Segoe UI", 10),
                    rowheight=28,
                    borderwidth=2,
                    relief="solid")
    style.configure("Treeview.Heading",
                    font=("Segoe UI", 11, "bold"))

    tree = ttk.Treeview(parent, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor="center")
    tree.pack(fill="both", expand=True, padx=15, pady=10)
    return tree

# ================= MAIN MENU =================
def main_menu():
    clear()
    frame = card("Secondary School Staff Attendance System")

    btn = tk.Frame(frame, bg="grey")
    btn.pack(pady=80)

    tk.Button(btn, text="Admin Login", width=30, height=3,
              command=admin_login).pack(pady=10)

    tk.Button(btn, text="Staff Login / Register", width=30, height=3,
              command=staff_login).pack(pady=10)

# ================= ADMIN =================
def admin_login():
    clear()
    frame = card("Admin Login")

    form = tk.Frame(frame, bg="grey")
    form.pack(pady=60)

    tk.Label(form, text="Username", bg="white").grid(row=0, column=0, sticky="w")
    u = tk.Entry(form, width=30)
    u.grid(row=0, column=1, pady=5)

    tk.Label(form, text="Password", bg="white").grid(row=1, column=0, sticky="w")
    p = tk.Entry(form, width=30, show="*")
    p.grid(row=1, column=1, pady=5)

    tk.Button(frame, text="Login", width=25,
              command=lambda: do_admin_login(u.get(), p.get())).pack(pady=15)

    tk.Button(frame, text="Back", command=main_menu).pack()

def do_admin_login(u, p):
    cursor.execute("SELECT * FROM admin WHERE username=? AND password=?", (u,p))
    if cursor.fetchone():
        admin_dashboard()
    else:
        messagebox.showerror("Error", "Invalid login")

def admin_dashboard():
    clear()
    frame = card("Admin Dashboard")

    grid = tk.Frame(frame, bg="grey")
    grid.pack(pady=50)

    buttons = [
        ("View Staff", view_staff),
        ("Approve Staff", approve_staff),
        ("Attendance Records", view_attendance),
        ("Import Staff (CSV)", import_staff),
        ("Export Today's Attendance", export_attendance),
        ("Logout", main_menu)
    ]

    for i, (txt, cmd) in enumerate(buttons):
        tk.Button(grid, text=txt, width=35, height=2,
                  command=cmd).grid(row=i, column=0, pady=6)

def change_admin_password():
    clear()
    frame = card("Change Admin Password")

    form = tk.Frame(frame, bg="white")
    form.pack(pady=50)

    tk.Label(form, text="Old Password", bg="white").grid(row=0, column=0, pady=5)
    old = tk.Entry(form, width=30, show="*")
    old.grid(row=0, column=1)

    tk.Label(form, text="New Password", bg="white").grid(row=1, column=0, pady=5)
    new = tk.Entry(form, width=30, show="*")
    new.grid(row=1, column=1)

    tk.Label(form, text="Confirm Password", bg="white").grid(row=2, column=0, pady=5)
    confirm = tk.Entry(form, width=30, show="*")
    confirm.grid(row=2, column=1)

    tk.Button(frame, text="Update Password",
              command=lambda: update_admin_password(
                  old.get(), new.get(), confirm.get()
              )).pack(pady=15)

    tk.Button(frame, text="Back to Dashboard",
              command=admin_dashboard).pack()

def update_admin_password(old, new, confirm):
    if not old or not new or not confirm:
        messagebox.showerror("Error", "All fields required")
        return

    if new != confirm:
        messagebox.showerror("Error", "Passwords do not match")
        return

    cursor.execute("SELECT password FROM admin WHERE username='admin'")
    if old != cursor.fetchone()[0]:
        messagebox.showerror("Error", "Old password incorrect")
        return

    cursor.execute("UPDATE admin SET password=? WHERE username='admin'", (new,))
    conn.commit()
    messagebox.showinfo("Success", "Password updated")
    admin_dashboard()

# ================= STAFF VIEWS =================
def view_staff():
    clear()
    frame = card("All Staff")

    tree = styled_table(frame, ("ID","Name","Username","Approved"))

    cursor.execute("SELECT id,name,username,approved FROM staff")
    for r in cursor.fetchall():
        tree.insert("", "end", values=r)

    tk.Button(frame, text="Delete Selected",
              command=lambda: delete_staff(tree)).pack(pady=5)

    tk.Button(frame, text="Back to Dashboard",
              command=admin_dashboard).pack()

def delete_staff(tree):
    sel = tree.focus()
    if not sel:
        return
    sid = tree.item(sel)["values"][0]
    cursor.execute("DELETE FROM staff WHERE id=?", (sid,))
    cursor.execute("DELETE FROM attendance WHERE staff_id=?", (sid,))
    conn.commit()
    view_staff()

def approve_staff():
    clear()
    frame = card("Pending Staff Approval")

    tree = styled_table(frame, ("ID","Name","Username"))

    cursor.execute("SELECT id,name,username FROM staff WHERE approved=0")
    for r in cursor.fetchall():
        tree.insert("", "end", values=r)

    tk.Button(frame, text="Approve Selected",
              command=lambda: approve_one(tree)).pack(pady=5)
    tk.Button(frame, text="Back to Dashboard",
              command=admin_dashboard).pack()

def approve_one(tree):
    sel = tree.focus()
    if sel:
        sid = tree.item(sel)["values"][0]
        cursor.execute("UPDATE staff SET approved=1 WHERE id=?", (sid,))
        conn.commit()
        approve_staff()

# ================= ATTENDANCE =================
def view_attendance():
    clear()
    frame = card("Attendance Records")

    tree = styled_table(frame, ("ID","Staff","Time","Date","Status"))

    cursor.execute("""
    SELECT attendance.id, staff.name, attendance.timestamp,
           attendance.date, attendance.status
    FROM attendance JOIN staff ON staff.id=attendance.staff_id
    """)
    for r in cursor.fetchall():
        tree.insert("", "end", values=r)

    tk.Button(frame, text="Delete Selected",
              command=lambda: delete_att(tree)).pack(pady=5)
    tk.Button(frame, text="Back to Dashboard",
              command=admin_dashboard).pack()

def delete_att(tree):
    sel = tree.focus()
    if sel:
        aid = tree.item(sel)["values"][0]
        cursor.execute("DELETE FROM attendance WHERE id=?", (aid,))
        conn.commit()
        view_attendance()

def register_staff(name, username, password):
    if not name or not username or not password:
        messagebox.showerror("Error", "All fields are required")
        return

    try:
        cursor.execute(
            "INSERT INTO staff (name, username, password, approved) VALUES (?,?,?,0)",
            (name, username, password)
        )
        conn.commit()
        messagebox.showinfo(
            "Success",
            "Registration successful.\nAwait admin approval."
        )
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists")

# ================= STAFF =================
def staff_login():
    clear()
    frame = card("Staff Login & Registration")

    form = tk.Frame(frame, bg="grey")
    form.pack(pady=30)

    tk.Label(form, text="Username", bg="white").grid(row=0, column=0)
    u = tk.Entry(form, width=25)
    u.grid(row=0, column=1)

    tk.Label(form, text="Password", bg="white").grid(row=1, column=0)
    p = tk.Entry(form, width=25, show="*")
    p.grid(row=1, column=1)

    tk.Button(frame, text="Login",
              command=lambda: staff_dashboard(u.get(), p.get())).pack(pady=10)

    ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=50, pady=15)

    tk.Label(frame, text="Register New Staff", bg="white",
             font=("Segoe UI", 12, "bold")).pack()

    n = tk.Entry(frame, width=35)
    ru = tk.Entry(frame, width=35)
    rp = tk.Entry(frame, width=35, show="*")

    for e, t in zip([n,ru,rp],["Name","Username","Password"]):
        tk.Label(frame, text=t, bg="white").pack()
        e.pack()

    tk.Button(frame, text="Register",
              command=lambda: register_staff(n.get(), ru.get(), rp.get())).pack(pady=10)
    tk.Button(frame, text="Back", command=main_menu).pack()

def staff_dashboard(u,p):
    cursor.execute("SELECT id FROM staff WHERE username=? AND password=?", (u,p))
    r = cursor.fetchone()
    if not r:
        messagebox.showerror("Error","Invalid login")
        return

    clear()
    frame = card("Staff Dashboard")

    time_lbl = tk.Label(frame, font=("Segoe UI", 14), bg="white")
    time_lbl.pack(pady=20)

    def clock():
        time_lbl.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        root.after(1000, clock)
    clock()

    tk.Button(frame, text="Mark Attendance", width=30, height=2,
              command=lambda: mark_attendance(r[0])).pack(pady=20)

    tk.Button(frame, text="Logout", command=main_menu).pack()

def mark_attendance(sid):
    now = datetime.now()
    try:
        cursor.execute(
            "INSERT INTO attendance (staff_id,timestamp,date,status) VALUES (?,?,?,?)",
            (sid, now.strftime("%Y-%m-%d %H:%M:%S"),
             now.strftime("%Y-%m-%d"), "Present")
        )
        conn.commit()
        messagebox.showinfo("Success","Attendance marked with exact time")
    except:
        messagebox.showerror("Error","Attendance already marked today")

# ================= CSV =================
def import_staff():
    f = filedialog.askopenfilename(filetypes=[("CSV","*.csv")])
    if not f:
        return
    with open(f) as file:
        for r in csv.DictReader(file):
            try:
                cursor.execute(
                    "INSERT INTO staff (name,username,password) VALUES (?,?,?)",
                    (r["name"], r["username"], r["password"]))
            except:
                pass
    conn.commit()

def export_attendance():
    f = filedialog.asksaveasfilename(defaultextension=".csv")
    if not f:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
    SELECT staff.name, attendance.timestamp, attendance.status
    FROM attendance JOIN staff ON staff.id=attendance.staff_id
    WHERE attendance.date=?
    """,(today,))
    with open(f,"w",newline="") as file:
        w = csv.writer(file)
        w.writerow(["Name","Time","Status"])
        w.writerows(cursor.fetchall())

# ================= RUN =================
root = tk.Tk()
root.title("School Staff Attendance System")
root.geometry("1100x700")
root.configure(bg="#e9edf3")
main_menu()
root.mainloop()
