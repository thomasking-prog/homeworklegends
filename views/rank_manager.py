# views/rank_manager.py

import customtkinter as ctk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models.rank import Rank

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class RankManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Rank Management")
        self.geometry("700x500")
        self.session = Session()

        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.btn_add = ctk.CTkButton(self, text="Add New Rank", command=self.add_rank_popup)
        self.btn_add.pack(pady=10)

        self.render_table()

    def render_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        headers = ["Name", "Min Points", "Max Points", "Order", "Actions"]
        for i, title in enumerate(headers):
            ctk.CTkLabel(self.table_frame, text=title, font=("Arial", 13, "bold")).grid(row=0, column=i, padx=5, pady=5)

        ranks = self.session.query(Rank).order_by(Rank.order).all()
        for row, rank in enumerate(ranks, start=1):
            ctk.CTkLabel(self.table_frame, text=rank.name).grid(row=row, column=0, padx=5, pady=5)
            ctk.CTkLabel(self.table_frame, text=str(rank.min_points)).grid(row=row, column=1, padx=5, pady=5)
            ctk.CTkLabel(self.table_frame, text=str(rank.max_points) if rank.max_points is not None else "∞").grid(row=row, column=2, padx=5, pady=5)
            ctk.CTkLabel(self.table_frame, text=str(rank.order)).grid(row=row, column=3, padx=5, pady=5)

            actions = ctk.CTkFrame(self.table_frame)
            actions.grid(row=row, column=4, padx=5, pady=5)
            ctk.CTkButton(actions, text="Edit", width=60, command=lambda r=rank: self.edit_rank_popup(r)).pack(side="left", padx=2)
            ctk.CTkButton(actions, text="Delete", fg_color="red", width=60, command=lambda r=rank: self.delete_rank(r)).pack(side="left", padx=2)

    def delete_rank(self, rank):
        self.session.delete(rank)
        self.session.commit()
        self.render_table()

    def add_rank_popup(self):
        self.open_rank_form()

    def edit_rank_popup(self, rank):
        self.open_rank_form(rank)

    def open_rank_form(self, rank=None):
        popup = ctk.CTkToplevel(self)
        popup.title("Edit Rank" if rank else "Add Rank")
        popup.geometry("400x300")

        name_entry = ctk.CTkEntry(popup, placeholder_text="Rank Name")
        name_entry.pack(pady=5)
        if rank: name_entry.insert(0, rank.name)

        min_entry = ctk.CTkEntry(popup, placeholder_text="Min Points")
        min_entry.pack(pady=5)
        if rank: min_entry.insert(0, str(rank.min_points))

        max_entry = ctk.CTkEntry(popup, placeholder_text="Max Points (leave blank = ∞)")
        max_entry.pack(pady=5)
        if rank and rank.max_points is not None: max_entry.insert(0, str(rank.max_points))

        order_entry = ctk.CTkEntry(popup, placeholder_text="Order")
        order_entry.pack(pady=5)
        if rank: order_entry.insert(0, str(rank.order))

        def save():
            name = name_entry.get()
            try:
                min_points = float(min_entry.get())
                max_points = float(max_entry.get()) if max_entry.get().strip() else None
                order = int(order_entry.get())
            except ValueError:
                return

            if rank:
                rank.name = name
                rank.min_points = min_points
                rank.max_points = max_points
                rank.order = order
            else:
                new_rank = Rank(
                    name=name,
                    min_points=min_points,
                    max_points=max_points,
                    order=order
                )
                self.session.add(new_rank)

            self.session.commit()
            popup.destroy()
            self.render_table()

        ctk.CTkButton(popup, text="Save", command=save).pack(pady=10)