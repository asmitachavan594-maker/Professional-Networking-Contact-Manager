"""
Professional Networking Contact Manager
Python + Tkinter + MySQL

Install connector: py -m pip install mysql-connector-python
Run: py professional_contact_manager.py
py 
The app asks for your MySQL password and creates its database/table automatically.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from mysql.connector import Error

DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_NAME = "professional_networking_db"


class ContactManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Networking Contact Manager")
        self.root.geometry("1120x700")
        self.root.minsize(950, 600)
        self.connection = None
        self.selected_id = None

        password = simpledialog.askstring(
            "MySQL Login", "Enter your MySQL password:", show="*", parent=root
        )
        if password is None:
            root.destroy()
            return
        if not self.connect_db(password):
            root.destroy()
            return
        self.build_ui()
        self.load_contacts()

    def connect_db(self, password):
        try:
            server = mysql.connector.connect(
                host=DB_HOST, port=DB_PORT, user=DB_USER, password=password
            )
            cur = server.cursor()
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cur.close()
            server.close()

            self.connection = mysql.connector.connect(
                host=DB_HOST, port=DB_PORT, user=DB_USER,
                password=password, database=DB_NAME
            )
            cur = self.connection.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    contact_id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(120) NOT NULL,
                    job_title VARCHAR(120),
                    company VARCHAR(150),
                    email VARCHAR(150),
                    phone VARCHAR(30),
                    industry VARCHAR(100),
                    linkedin VARCHAR(255),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.connection.commit()
            cur.close()
            return True
        except Error as exc:
            messagebox.showerror(
                "MySQL Connection Error",
                f"Could not connect to MySQL:\n\n{exc}\n\n"
                "Check that MySQL Server is running, the password is correct, "
                "and DB_PORT is correct (usually 3306)."
            )
            return False

    def build_ui(self):
        header = ttk.Frame(self.root, padding=14)
        header.pack(fill="x")
        ttk.Label(
            header, text="Professional Networking Contact Manager",
            font=("Segoe UI", 19, "bold")
        ).pack(anchor="w")
        ttk.Label(
            header, text="Save, search, and manage professional connections"
        ).pack(anchor="w", pady=(3, 0))

        form = ttk.LabelFrame(self.root, text="Contact Details", padding=12)
        form.pack(fill="x", padx=14, pady=(0, 10))

        self.name = tk.StringVar()
        self.job = tk.StringVar()
        self.company = tk.StringVar()
        self.email = tk.StringVar()
        self.phone = tk.StringVar()
        self.industry = tk.StringVar()
        self.linkedin = tk.StringVar()
        self.search_var = tk.StringVar()

        fields = [
            ("Full Name *", self.name, 0, 0),
            ("Job Title", self.job, 0, 2),
            ("Company", self.company, 1, 0),
            ("Email", self.email, 1, 2),
            ("Phone", self.phone, 2, 0),
            ("Industry", self.industry, 2, 2),
            ("LinkedIn URL", self.linkedin, 3, 0),
        ]
        for label, variable, row, col in fields:
            ttk.Label(form, text=label).grid(
                row=row, column=col, sticky="w", padx=(0, 8), pady=5
            )
            ttk.Entry(form, textvariable=variable, width=40).grid(
                row=row, column=col + 1, sticky="ew", padx=(0, 18), pady=5
            )

        ttk.Label(form, text="Notes").grid(
            row=3, column=2, sticky="nw", padx=(0, 8), pady=5
        )
        self.notes = tk.Text(form, height=3, width=40, wrap="word")
        self.notes.grid(row=3, column=3, sticky="ew", pady=5)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        actions = ttk.Frame(self.root, padding=(14, 0))
        actions.pack(fill="x", pady=(0, 10))
        for text, command in [
            ("Add Contact", self.add_contact),
            ("Update Selected", self.update_contact),
            ("Delete Selected", self.delete_contact),
            ("Clear Form", self.clear_form),
            ("Refresh", self.load_contacts),
        ]:
            ttk.Button(actions, text=text, command=command).pack(
                side="left", padx=(0, 8)
            )

        search = ttk.Frame(self.root, padding=(14, 0, 14, 8))
        search.pack(fill="x")
        ttk.Label(search, text="Search name/company/email:").pack(side="left")
        entry = ttk.Entry(search, textvariable=self.search_var, width=35)
        entry.pack(side="left", padx=8)
        entry.bind("<Return>", lambda _event: self.search_contacts())
        ttk.Button(search, text="Search", command=self.search_contacts).pack(side="left", padx=3)
        ttk.Button(search, text="Show All", command=self.load_contacts).pack(side="left", padx=3)

        table = ttk.Frame(self.root, padding=(14, 0, 14, 10))
        table.pack(fill="both", expand=True)
        cols = ("id", "name", "job", "company", "email", "phone", "industry")
        self.tree = ttk.Treeview(table, columns=cols, show="headings")
        config = {
            "id": ("ID", 48), "name": ("Full Name", 165),
            "job": ("Job Title", 140), "company": ("Company", 160),
            "email": ("Email", 190), "phone": ("Phone", 110),
            "industry": ("Industry", 125)
        }
        for col, (heading, width) in config.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, minwidth=45, anchor="w")
        ys = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        xs = ttk.Scrollbar(table, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        table.rowconfigure(0, weight=1)
        table.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self.select_contact)

        self.status = tk.StringVar(value=f"Connected to database: {DB_NAME}")
        ttk.Label(
            self.root, textvariable=self.status, relief="sunken",
            anchor="w", padding=5
        ).pack(fill="x", side="bottom")

    def form_data(self):
        return (
            self.name.get().strip(), self.job.get().strip(),
            self.company.get().strip(), self.email.get().strip(),
            self.phone.get().strip(), self.industry.get().strip(),
            self.linkedin.get().strip(), self.notes.get("1.0", "end").strip()
        )

    def add_contact(self):
        data = self.form_data()
        if not data[0]:
            messagebox.showwarning("Missing Information", "Full Name is required.")
            return
        try:
            cur = self.connection.cursor()
            cur.execute("""
                INSERT INTO contacts
                (full_name, job_title, company, email, phone, industry, linkedin, notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, data)
            self.connection.commit()
            cur.close()
            self.load_contacts()
            self.clear_form()
            messagebox.showinfo("Success", "Contact added successfully.")
        except Error as exc:
            messagebox.showerror("Database Error", str(exc))

    def fetch(self, term=None):
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            cur = self.connection.cursor()
            if term:
                pattern = "%" + term + "%"
                cur.execute("""
                    SELECT contact_id, full_name, job_title, company, email, phone, industry
                    FROM contacts
                    WHERE full_name LIKE %s OR company LIKE %s OR email LIKE %s
                    ORDER BY full_name
                """, (pattern, pattern, pattern))
            else:
                cur.execute("""
                    SELECT contact_id, full_name, job_title, company, email, phone, industry
                    FROM contacts ORDER BY full_name
                """)
            rows = cur.fetchall()
            for row in rows:
                self.tree.insert("", "end", values=row)
            cur.close()
            self.status.set(f"Connected to {DB_NAME} | Contacts shown: {len(rows)}")
        except Error as exc:
            messagebox.showerror("Database Error", str(exc))

    def load_contacts(self):
        self.fetch()

    def search_contacts(self):
        term = self.search_var.get().strip()
        self.fetch(term if term else None)

    def select_contact(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        self.selected_id = int(self.tree.item(selected[0], "values")[0])
        try:
            cur = self.connection.cursor()
            cur.execute("""
                SELECT full_name, job_title, company, email, phone, industry, linkedin, notes
                FROM contacts WHERE contact_id=%s
            """, (self.selected_id,))
            row = cur.fetchone()
            cur.close()
            if row:
                for variable, value in zip(
                    (self.name, self.job, self.company, self.email, self.phone,
                     self.industry, self.linkedin), row[:7]
                ):
                    variable.set(value or "")
                self.notes.delete("1.0", "end")
                self.notes.insert("1.0", row[7] or "")
        except Error as exc:
            messagebox.showerror("Database Error", str(exc))

    def update_contact(self):
        if not self.selected_id:
            messagebox.showwarning("Select Contact", "Select a contact from the table first.")
            return
        data = self.form_data()
        if not data[0]:
            messagebox.showwarning("Missing Information", "Full Name is required.")
            return
        try:
            cur = self.connection.cursor()
            cur.execute("""
                UPDATE contacts SET full_name=%s, job_title=%s, company=%s,
                email=%s, phone=%s, industry=%s, linkedin=%s, notes=%s
                WHERE contact_id=%s
            """, data + (self.selected_id,))
            self.connection.commit()
            cur.close()
            self.load_contacts()
            self.clear_form()
            messagebox.showinfo("Success", "Contact updated successfully.")
        except Error as exc:
            messagebox.showerror("Database Error", str(exc))

    def delete_contact(self):
        if not self.selected_id:
            messagebox.showwarning("Select Contact", "Select a contact from the table first.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete the selected contact?"):
            return
        try:
            cur = self.connection.cursor()
            cur.execute("DELETE FROM contacts WHERE contact_id=%s", (self.selected_id,))
            self.connection.commit()
            cur.close()
            self.load_contacts()
            self.clear_form()
            messagebox.showinfo("Success", "Contact deleted successfully.")
        except Error as exc:
            messagebox.showerror("Database Error", str(exc))

    def clear_form(self):
        self.selected_id = None
        for variable in (
            self.name, self.job, self.company, self.email, self.phone,
            self.industry, self.linkedin
        ):
            variable.set("")
        self.notes.delete("1.0", "end")
        for item in self.tree.selection():
            self.tree.selection_remove(item)


def main():
    root = tk.Tk()
    ContactManager(root)
    if root.winfo_exists():
        root.mainloop()


if __name__ == "__main__":
    main()
