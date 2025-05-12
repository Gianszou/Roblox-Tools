import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import aiohttp
import asyncio
import os
import json
import time

COOKIE_FILE = "cookie.txt"

class RobloxUnfrienderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Roblox Mass Unfriender")
        self.cookie = ""
        self.user_id = ""
        self.friends = []
        self.friend_vars = {}
        self.checkbuttons = {}
        self.delay_ms = tk.IntVar(value=500)
        self.search_var = tk.StringVar()
        self.build_gui()

    def build_gui(self):
        ttk.Label(self.root, text="Roblox Security Cookie:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.cookie_entry = ttk.Entry(self.root, width=70)
        self.cookie_entry.grid(row=1, column=0, padx=10, pady=5)

        load_btn = ttk.Button(self.root, text="Load Cookie", command=self.load_cookie)
        load_btn.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(self.root, text="Delay between unfriends (ms):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.delay_entry = ttk.Entry(self.root, textvariable=self.delay_ms, width=10)
        self.delay_entry.grid(row=2, column=1, padx=10, pady=5)

        fetch_btn = ttk.Button(self.root, text="Fetch Friends", command=lambda: asyncio.run(self.fetch_friends()))
        fetch_btn.grid(row=3, column=0, padx=10, pady=5)

        self.unfriend_btn = ttk.Button(self.root, text="Unfriend All", command=lambda: asyncio.run(self.unfriend_all()))
        self.unfriend_btn.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(self.root, text="Search:").grid(row=4, column=0, sticky="w", padx=10)
        self.search_entry = ttk.Entry(self.root, textvariable=self.search_var, width=50)
        self.search_entry.grid(row=5, column=0, columnspan=2, sticky="w", padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_friends())

        self.checklist_container = ttk.Frame(self.root)
        self.checklist_container.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.canvas = tk.Canvas(self.checklist_container)
        self.scrollbar = ttk.Scrollbar(self.checklist_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.log_output = scrolledtext.ScrolledText(self.root, width=80, height=10, state='disabled')
        self.log_output.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

        self.root.grid_rowconfigure(6, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def log(self, message):
        self.log_output.config(state='normal')
        self.log_output.insert(tk.END, message + '\n')
        self.log_output.config(state='disabled')
        self.log_output.yview(tk.END)

    def load_cookie(self):
        self.cookie = self.cookie_entry.get().strip()
        if not self.cookie:
            if os.path.exists(COOKIE_FILE):
                with open(COOKIE_FILE, 'r') as f:
                    self.cookie = f.read().strip()
                    self.cookie_entry.insert(0, self.cookie)
            else:
                with open(COOKIE_FILE, 'w') as f:
                    f.write("your_cookie_here")
                messagebox.showinfo("Info", "cookie.txt created. Put your .ROBLOSECURITY cookie in it.\n\nTutorial:\n1. Install Cookie Editor Extension.\n2. Go to roblox.com.\n3. Click Cookie Editor, find .ROBLOSECURITY, and copy the value.")
        else:
            with open(COOKIE_FILE, 'w') as f:
                f.write(self.cookie)
        self.log("Cookie loaded.")

    async def get_user_id(self):
        async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": self.cookie}) as session:
            async with session.get("https://users.roblox.com/v1/users/authenticated") as response:
                if response.status == 200:
                    data = await response.json()
                    self.user_id = data.get("id")
                    self.log(f"Logged in as user ID: {self.user_id}")
                else:
                    self.log("Failed to authenticate user.")

    async def fetch_friends(self):
        await self.get_user_id()
        async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": self.cookie}) as session:
            async with session.get(f"https://friends.roblox.com/v1/users/{self.user_id}/friends") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.friends = data.get("data", [])
                    self.display_friends(self.friends)
                    self.log(f"Fetched {len(self.friends)} friends.")
                else:
                    self.log("Failed to fetch friends list.")

    def display_friends(self, friend_list):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.friend_vars.clear()
        self.checkbuttons.clear()
        for friend in friend_list:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(self.scrollable_frame, text=f"{friend['name']} ({friend['id']})", variable=var)
            cb.pack(anchor="w", padx=5, pady=2)
            self.friend_vars[str(friend["id"])] = var
            self.checkbuttons[str(friend["id"])] = cb

    def filter_friends(self):
        search = self.search_var.get().lower()
        filtered = [f for f in self.friends if search in f['name'].lower() or search in str(f['id'])]
        self.display_friends(filtered)

    def get_xcsrf(self):
        import requests
        res = requests.post("https://auth.roblox.com/v2/logout", cookies={".ROBLOSECURITY": self.cookie})
        return res.headers.get("x-csrf-token")

    async def unfriend_all(self):
        delay = self.delay_ms.get() / 1000
        xcsrf = self.get_xcsrf()
        async with aiohttp.ClientSession(
            cookies={".ROBLOSECURITY": self.cookie},
            headers={"X-Csrf-Token": xcsrf}
        ) as session:
            count = 0
            for friend in list(self.friends):
                friend_id = str(friend["id"])
                if self.friend_vars.get(friend_id).get():
                    self.log(f"Whitelisted: {friend['name']} ({friend_id})")
                    continue

                async with session.post(f"https://friends.roblox.com/v1/users/{friend_id}/unfriend") as resp:
                    if resp.status == 200:
                        self.log(f"Unfriended: {friend['name']} ({friend_id})")
                        cb = self.checkbuttons.get(friend_id)
                        if cb:
                            cb.destroy()
                        self.friends.remove(friend)
                        count += 1
                    else:
                        self.log(f"Failed to unfriend: {friend['name']} ({friend_id})")
                await asyncio.sleep(delay)
            self.log(f"Finished unfriending. Total: {count}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RobloxUnfrienderApp(root)
    root.mainloop()
