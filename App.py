import Admin as a
import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
import Product
import Client
import Order
import Outgoings
import Treasury
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import webbrowser
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from tkcalendar import DateEntry
from datetime import datetime
from Transfer import Transfer
import sys

def resource_path(relative_path):
    """Get path to resource for PyInstaller or normal run"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

pdfmetrics.registerFont(TTFont('ArabicFont', resource_path('assets/ArabicFont.ttf')))


def arabic(text):
    if not text:
        return ""
    try:
        # Handle numeric values differently
        if isinstance(text, (int, float)):
            return str(text)
        reshaped_text = arabic_reshaper.reshape(str(text))
        return get_display(reshaped_text)
    except:
        return str(text) 

Product.Product.initialize_file()

def start_login_page():
    global frame, entry_username, entry_password

    clear_window()

    frame = ctk.CTkFrame(master=root, corner_radius=15)
    frame.place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkLabel(frame, text="معصرة المتحدة", font=("Arial", 28, "bold")).pack(pady=(30, 20))

    entry_username = ctk.CTkEntry(frame, placeholder_text="اسم المستخدم", font=("Arial", 14), width=300)
    entry_username.pack(pady=10)

    entry_password = ctk.CTkEntry(frame, placeholder_text="كلمة المرور", font=("Arial", 14), show="*", width=300)
    entry_password.pack(pady=10)

    ctk.CTkButton(frame, text="تسجيل دخول", command=attempt_login, font=("Arial", 14), width=200).pack(pady=(20, 30))


def attempt_login():
    f = open(resource_path("data/login"), "r")
    admin = a.Admin(f.readline().strip(), f.readline().strip())
    f.close()
    username = entry_username.get()
    password = entry_password.get()
    if admin.login(username, password):
        open_dashboard()
    else:
        messagebox.showerror("Login Failed", "Invalid credentials")

def open_dashboard():
    clear_window()

    # Sidebar
    sidebar = ctk.CTkFrame(root, width=200, corner_radius=0)
    sidebar.pack(side="left", fill="y")

    ctk.CTkLabel(sidebar, text="معصرة المتحدة", font=("Arial", 20, "bold")).pack(pady=(20, 10))

    # Main dashboard area
    main_area = ctk.CTkFrame(root, fg_color="transparent")
    main_area.pack(side="left", expand=True, fill="both")

    def clear_main_area_and_show(view_function):
        for widget in main_area.winfo_children():
            widget.destroy()
        view_function()

    def on_treasury():
        for widget in main_area.winfo_children():
            widget.destroy()

        treasury = Treasury.Treasury()

        ctk.CTkLabel(main_area, text="الخزنة", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        balance_label = ctk.CTkLabel(main_area,
                            text=f"الرصيد الكلي: {treasury.total_balance} ج.م",
                            font=("Arial", 18, "bold"),
                            text_color=("black", "white"))
        balance_label.grid(row=0, column=0, sticky="e", padx=20)

        # === Dark Treeview Styling ===
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2a2d2e",
                        foreground="white",
                        rowheight=25,
                        fieldbackground="#2a2d2e",
                        font=("Arial", 12))
        style.configure("Treeview.Heading",
                        background="#1f2326",
                        foreground="white",
                        font=("Arial", 13, "bold"))
        style.map("Treeview", background=[("selected", "#3a3d3f")])

        # === Table Frame ===
        table_frame = ctk.CTkFrame(main_area)
        table_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)

        columns = ("ID", "Client ID", "Total Price", "Date")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=150)
        tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        filter_frame = ctk.CTkFrame(main_area)
        filter_frame.grid(row=0, column=1, pady=(10, 10), padx=20, sticky="e")

        ctk.CTkLabel(filter_frame, text="من:").grid(row=0, column=0, padx=5)
        start_entry = DateEntry(filter_frame, date_pattern="yyyy-mm-dd", width=12)
        start_entry.set_date(datetime.now().date())
        start_entry.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(filter_frame, text="إلى:").grid(row=0, column=2, padx=5)
        end_entry = DateEntry(filter_frame, date_pattern="yyyy-mm-dd", width=12)
        end_entry.set_date(datetime.now().date())
        end_entry.grid(row=0, column=3, padx=5)

        ctk.CTkButton(
            filter_frame,
            text="تصفية",
            command=lambda: apply_orders_filter(
                tree_widget=tree,
                from_date=start_entry.get_date(),
                to_date=end_entry.get_date(),
                balance_label=balance_label,
                include_outgoings=True
            ),
            font=("Arial", 14)
        ).grid(row=0, column=4, padx=10)

        main_area.rowconfigure(1, weight=1)
        main_area.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)


        def refresh_orders(from_date=None, to_date=None):
            from datetime import datetime
            tree.delete(*tree.get_children())
            total = 0

            if from_date is None and to_date is None:
                today = datetime.now().date()
                from_date = to_date = today

            orders = Order.Order.load_orders_from_json(from_date=from_date, to_date=to_date)
            for order in orders:
                tree.insert("", "end", values=(order.id, order.client_id, order.total_price, order.date))
                total += order.total_price

            outgoings_total = sum(o.price for o in Outgoings.Outgoings.load_all(from_date=from_date, to_date=to_date))
            treasury.total_balance = total - outgoings_total
            balance_label.configure(text=f"الرصيد الكلي: {treasury.total_balance:.2f} ج.م", font=("Arial", 16, "bold"))

        def apply_orders_filter(tree_widget, from_date, to_date, balance_label=None, include_outgoings=True):
            tree_widget.delete(*tree_widget.get_children())
            total = 0

            orders = Order.Order.load_orders_from_json(from_date=from_date, to_date=to_date)
            for order in orders:
                tree_widget.insert("", "end", values=(order.id, order.client_id, order.total_price, order.date))
                total += order.total_price

            if balance_label and include_outgoings:
                outgoings_total = sum(o.price for o in Outgoings.Outgoings.load_all(from_date=from_date, to_date=to_date))
                treasury.total_balance = total - outgoings_total
                balance_label.configure(text=f"الرصيد الكلي: {treasury.total_balance:.2f} ج.م", font=("Arial", 16, "bold"))


        def open_add_order():
            win = ctk.CTkToplevel(root)
            win.title("إضافة طلب")
            win.geometry("600x500")
            win.grab_set()

            ctk.CTkLabel(win, text="إضافة طلب جديد", font=("Arial", 20, "bold")).pack(pady=10)

            # === Frame for Selections ===
            form_frame = ctk.CTkFrame(win)
            form_frame.pack(pady=10, padx=20, fill="x")

            # Client Selection
            clients = [c for c in Client.Client.load_all() if c.role == "شراء"]
            client_dict = {f"{c.id} - {c.name}": c for c in clients}
            combo_values = ["اختر عميل"] + list(client_dict.keys())
            client_combo = ctk.CTkComboBox(form_frame, values=combo_values)
            client_combo.set("اختر عميل")
            client_combo.pack(pady=5, fill="x", expand=True)

            # Product Selection
            products = Product.Product.load_all()
            product_names = [p.name for p in products]
            product_combo = ctk.CTkComboBox(form_frame, values=product_names)
            product_combo.set("اختر منتج")
            product_combo.pack(pady=5, fill="x")

            quantity_entry = ctk.CTkEntry(form_frame, placeholder_text="الكمية المطلوبة", font=("Arial", 14))
            quantity_entry.pack(pady=5, fill="x")

            final_price_entry = ctk.CTkEntry(form_frame, placeholder_text="السعر النهائي للقطعة", font=("Arial", 14))
            final_price_entry.pack(pady=5, fill="x")

            cash_paid_entry = ctk.CTkEntry(form_frame, placeholder_text="المبلغ المدفوع الآن", font=("Arial", 14))
            cash_paid_entry.pack(pady=5, fill="x")

            # === Order Summary Display ===
            summary = ctk.CTkTextbox(win, height=100)
            summary.pack(padx=20, pady=10, fill="both")
            summary.insert("end", "قائمة الطلب فارغة\n")
            summary.configure(state="disabled")

            current_order = Order.Order(client_id="", products=[], total_price=0, cash_paid_now=0)

            # === Add Product to Order Function ===
            def add_product_to_order():
                product_name = product_combo.get()
                quantity = quantity_entry.get()
                final_price = final_price_entry.get()

                if not product_name or not quantity or not final_price:
                    messagebox.showerror("خطأ", "يرجى ملء جميع الحقول")
                    return

                try:
                    quantity = float(quantity)
                    final_price = float(final_price)
                except ValueError:
                    messagebox.showerror("خطأ", "الكمية والسعر يجب أن يكونا أرقام صحيحة")
                    return

                product = next((p for p in products if p.name == product_name), None)
                if not product:
                    messagebox.showerror("خطأ", "المنتج غير موجود")
                    return

                try:
                    current_order.add_product(product, final_price, quantity)
                except ValueError as e:
                    messagebox.showerror("خطأ", str(e))
                    return

                # Update summary
                summary.configure(state="normal")
                summary.insert("end", f"{product_name} - {quantity} × {final_price} ج.م\n")
                summary.insert("end", f"السعر الإجمالي: {current_order.total_price} ج.م\n")
                summary.configure(state="disabled")

            def save_order():
                client_key = client_combo.get()
                client = client_dict.get(client_key, None)
                if not client:
                    messagebox.showerror("خطأ", "يرجى اختيار عميل صحيح")
                    return
                if not current_order.products:
                    messagebox.showerror("خطأ", "الطلب فارغ")
                    return

                try:
                    cash_paid_now = float(cash_paid_entry.get())
                except ValueError:
                    messagebox.showerror("خطأ", "المبلغ المدفوع يجب أن يكون رقمًا")
                    return

                current_order.client_id = client.id
                current_order.cash_paid_now = cash_paid_now
                client.previous_balance += (current_order.total_price - cash_paid_now)

                # Save updated client info
                clients = Client.Client.load_all()
                for i, c in enumerate(clients):
                    if c.id == client.id:
                        clients[i] = client
                        break
                Client.Client.save_all(clients)

                # Save updated product quantities
                Product.Product.save_all(products)

                # Save order to file
                orders = Order.Order.load_orders_from_json()
                orders.append(current_order)
                Order.Order.save_orders_to_json(orders)
                refresh_orders()
                messagebox.showinfo("نجاح", "تم حفظ الطلب")
                win.destroy()

            # === Buttons ===
            button_frame = ctk.CTkFrame(win)
            button_frame.pack(pady=10)

            add_btn = ctk.CTkButton(button_frame, text="إضافة منتج", command=add_product_to_order, font=("Arial", 14))
            add_btn.grid(row=0, column=0, padx=10)

            save_btn = ctk.CTkButton(button_frame, text="حفظ الطلب", command=save_order, font=("Arial", 14))
            save_btn.grid(row=0, column=1, padx=10)


        def delete_order():
            selected = tree.selection()
            if selected:
                selected = selected[0]
                order_id = tree.item(selected, "values")[0]

                orders = Order.Order.load_orders_from_json()
                order_to_delete = None
                for o in orders:
                    if o.id == order_id:
                        order_to_delete = o
                        break

                if order_to_delete:
                    try:
                        # Restore product quantities
                        all_products = Product.Product.load_all()
                        for product, quantity, final_price in order_to_delete.products:
                            for p in all_products:
                                if p.name == product.name:
                                    p.quantity += quantity
                                    break
                        Product.Product.save_all(all_products)
                    except Exception as e:
                        raise ValueError(f"خطأ أثناء استعادة الكميات: {e}")

                    try:
                        # Adjust client balance
                        clients = Client.Client.load_all()
                        for c in clients:
                            if c.id == order_to_delete.client_id:
                                c.previous_balance -= (order_to_delete.total_price - order_to_delete.cash_paid_now)
                                break
                        Client.Client.save_all(clients)
                    except Exception as e:
                        raise ValueError(f"خطأ أثناء تعديل رصيد العميل: {e}")

                    # Remove order from list
                    orders = [o for o in orders if o.id != order_id]
                    Order.Order.save_orders_to_json(orders)

                    refresh_orders()
                    messagebox.showinfo("تم", "تم حذف الطلب")
        
        def show_order_details(order, client):
            detail_win = ctk.CTkToplevel()
            detail_win.title("تفاصيل الطلب")
            detail_win.geometry("700x600")
            detail_win.grab_set()

            # === Header Labels ===
            ctk.CTkLabel(detail_win, text="معصرة المتحدة", font=("Arial", 24, "bold")).pack(pady=(10, 5))
            ctk.CTkLabel(detail_win, text="فاتورة مبيعات", font=("Arial", 18)).pack(pady=(0, 15))

            top_info_frame = ctk.CTkFrame(detail_win)
            top_info_frame.pack(fill="x", padx=20)

            ctk.CTkLabel(top_info_frame, text=f"عميل: {client.name}", font=("Arial", 12), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(top_info_frame, text=f"التاريخ: {order.date}", font=("Arial", 12), anchor="e").pack(side="right", padx=5)

            tree_frame = ctk.CTkFrame(detail_win)
            tree_frame.pack(pady=10, fill="both", expand=True, padx=20)

            columns = ("name", "quantity", "unit_price", "total_price")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
            tree.heading("name", text="اسم المنتج", anchor="center")
            tree.heading("quantity", text="الكمية", anchor="center")
            tree.heading("unit_price", text="سعر الوحدة", anchor="center")
            tree.heading("total_price", text="السعر الإجمالي", anchor="center")
            tree.pack(fill="both", expand=True)

            for product, qty, price in order.products:
                total = qty * price
                tree.insert("", "end", values=(product.name, qty, price, total))

            balance_before = client.previous_balance - (order.total_price - order.cash_paid_now)

            summary_frame = ctk.CTkFrame(detail_win)
            summary_frame.pack(fill="x", padx=20, pady=10)

            ctk.CTkLabel(summary_frame, text=f"الرصيد السابق: {balance_before:.2f} ج.م", font=("Arial", 12), anchor="w").pack(fill="x", pady=2)
            ctk.CTkLabel(summary_frame, text=f"إجمالي الفاتورة: {order.total_price:.2f} ج.م", font=("Arial", 12), anchor="w").pack(fill="x", pady=2)
            ctk.CTkLabel(summary_frame, text=f"المدفوع نقدا: {order.cash_paid_now:.2f} ج.م", font=("Arial", 12), anchor="w").pack(fill="x", pady=2)
            ctk.CTkLabel(summary_frame, text=f"الرصيد الحالي: {client.previous_balance:.2f} ج.م", font=("Arial", 12) ,anchor="w").pack(fill="x", pady=2)
            export_btn = ctk.CTkButton(detail_win, text="تصدير كـ PDF", command=lambda: export_order_as_pdf(order, client), font=("Arial", 14))
            export_btn.pack(pady=10)

            def export_order_as_pdf(order, client):
                filename = f"فاتورة_{order.id}.pdf"
                output_dir = "output"
                image_path = os.path.join("assets", "logo.png")
                PADDING = 20
                IMAGE_WIDTH = 90
                IMAGE_HEIGHT = 60
                pdf_path = os.path.join(output_dir, filename)
                c = canvas.Canvas(pdf_path, pagesize=A4)
                width, height = A4
                X = PADDING + 30
                Y = height - IMAGE_HEIGHT - PADDING - 10
                c.drawImage(resource_path(image_path), X, Y, width=IMAGE_WIDTH, height=IMAGE_HEIGHT)
                y = height - 50

                c.setFont("ArabicFont", 20)
                c.drawCentredString(width / 2, y, arabic("معصرة المتحدة"))

                y -= 30
                c.setFont("ArabicFont", 14)
                c.drawCentredString(width / 2, y, arabic("فاتورة مبيعات"))

                y -= 40
                c.setFont("ArabicFont", 12)
                c.drawRightString(width - 50, y, arabic(f"العميل: {client.name}"))
                c.drawString(50, y, arabic(f"التاريخ: {order.date}"))

                y -= 20
                c.line(50, y, width - 50, y)
                y -= 20

                c.setFont("ArabicFont", 12)
                c.drawString(50, y, arabic("المنتج"))
                c.drawString(200, y, arabic("الكمية"))
                c.drawString(300, y, arabic("سعر الوحدة"))
                c.drawString(420, y, arabic("السعر الإجمالي"))

                y -= 10
                c.line(50, y, width - 50, y)
                y -= 20

                for product, quantity, unit_price in order.products:
                    if y < 100:
                        c.showPage()
                        y = height - 50
                        c.setFont("ArabicFont", 12)

                    total = unit_price * quantity
                    c.drawString(50, y, arabic(product.name))
                    c.drawString(200, y, arabic(str(quantity)))
                    c.drawString(300, y, arabic(f"{unit_price:.2f}"))
                    c.drawString(420, y, arabic(f"{total:.2f}"))
                    y -= 20

                y -= 10
                c.line(50, y, width - 50, y)
                y -= 30

                new_balance = client.previous_balance + order.total_price - order.cash_paid_now

                c.setFont("ArabicFont", 12)
                c.drawString(50, y, arabic(f"الرصيد السابق: {client.previous_balance:.2f}"))
                y -= 20
                c.drawString(50, y, arabic(f"إجمالي الطلب: {order.total_price:.2f}"))
                y -= 20
                c.drawString(50, y, arabic(f"المبلغ المدفوع: {order.cash_paid_now:.2f}"))
                y -= 20
                c.drawString(50, y, arabic(f"الرصيد بعد المعاملة: {new_balance:.2f}"))

                c.save()

                abs_path = os.path.abspath(pdf_path)
                final = resource_path(abs_path)
                webbrowser.open(f"file://{final}")


        def show_selected_order_details():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("خطأ", "يرجى اختيار طلب لعرض التفاصيل")
                return

            order_id = tree.item(selected[0], "values")[0]
            orders = Order.Order.load_orders_from_json()
            clients = Client.Client.load_all()

            order = next((o for o in orders if o.id == order_id), None)
            if not order:
                messagebox.showerror("خطأ", "الطلب غير موجود")
                return

            client = next((c for c in clients if c.id == order.client_id), None)
            if not client:
                messagebox.showerror("خطأ", "العميل المرتبط بالطلب غير موجود")
                return

            show_order_details(order, client)

        def open_outgoings_window():
            win = ctk.CTkToplevel(root)
            win.title("المصروفات")
            win.geometry("600x400")
            win.grab_set()
            style = ttk.Style()
            style.theme_use("default")
            style.configure("Treeview",
                           background="#2a2d2e",
                            foreground="white",
                            rowheight=25,
                            fieldbackground="#2a2d2e",
                            font=("Arial", 12))
            style.configure("Treeview.Heading",
                            background="#1f2326",
                            foreground="white",
                            font=("Arial", 13, "bold"))
            style.map("Treeview", background=[("selected", "#3a3d3f")])
            columns = ("ID", "Name", "Price", "Date")
            out_tree = ttk.Treeview(win, columns=columns, show="headings")
            for col in columns:
                out_tree.heading(col, text=col)
                out_tree.column(col, anchor="center", width=120)
            out_tree.pack(padx=10, pady=10, expand=True, fill="both")

            def refresh_outgoings():
                out_tree.delete(*out_tree.get_children())
                for o in Outgoings.Outgoings.load_all():
                    out_tree.insert("", "end", values=(o.id, o.name, o.price, o.date))
                refresh_orders()

            def add_outgoing():
                sub_win = ctk.CTkToplevel(win)
                sub_win.title("إضافة مصروف")
                sub_win.geometry("400x200")
                sub_win.grab_set()

                name_entry = ctk.CTkEntry(sub_win, placeholder_text="اسم المصروف", font=("Arial", 14))
                name_entry.pack(pady=10)
                price_entry = ctk.CTkEntry(sub_win, placeholder_text="القيمة", font=("Arial", 14))
                price_entry.pack(pady=10)

                def confirm_add():
                    try:
                        name = name_entry.get()
                        price = float(price_entry.get())
                        new_out = Outgoings.Outgoings(name, price)
                        treasury.add_outgoing(new_out)
                        refresh_outgoings()
                        sub_win.destroy()
                        messagebox.showinfo("تم", "تمت إضافة المصروف")
                    except Exception as e:
                        messagebox.showerror("خطأ", str(e))

                ctk.CTkButton(sub_win, text="إضافة", command=confirm_add, font=("Arial", 14)).pack(pady=10)

            def delete_outgoing():
                selected = out_tree.selection()
                if selected:
                    selected = selected[0]
                    out_id = out_tree.item(selected, "values")[0]
                    outgoings = Outgoings.Outgoings.load_all()
                    for o in outgoings:
                        if o.id == out_id:
                            treasury.remove_outgoing(o)
                            break
                    Outgoings.Outgoings.save_all([o for o in outgoings if o.id != out_id])
                    refresh_outgoings()
                    messagebox.showinfo("تم", "تم حذف المصروف")

            # Outgoings Buttons
            btn_frame = ctk.CTkFrame(win)
            btn_frame.pack(pady=10)
            ctk.CTkButton(btn_frame, text="إضافة مصروف", command=add_outgoing, font=("Arial", 14)).pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text="حذف مصروف", command=delete_outgoing, font=("Arial", 14)).pack(side="left", padx=10)

            refresh_outgoings()

        # === Action Buttons ===
        action_frame = ctk.CTkFrame(main_area)
        action_frame.grid(row=2, column=0, columnspan=3, pady=10, padx=20, sticky="w")
        ctk.CTkButton(action_frame, text="إضافة طلب", command=open_add_order, font=("Arial", 14)).grid(row=0, column=0, padx=10)
        ctk.CTkButton(action_frame, text="حذف طلب", command=delete_order, font=("Arial", 14)).grid(row=0, column=1, padx=10)
        ctk.CTkButton(action_frame, text="عرض المصروفات", command=open_outgoings_window, font=("Arial", 14)).grid(row=0, column=2, padx=10)
        ctk.CTkButton(action_frame, text="عرض التفاصيل", command=show_selected_order_details, font=("Arial", 14)).grid(row=0, column=3, padx=10)

        refresh_orders()

    def on_products():
        for widget in main_area.winfo_children():
            widget.destroy()

        ctk.CTkLabel(main_area, text="المنتجات", font=("Arial", 24, "bold")).grid(row=0, column=0, pady=(20, 10), columnspan=2)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2a2d2e",
                        foreground="white",
                        rowheight=25,
                        fieldbackground="#2a2d2e",
                        font=("Arial", 12))
        style.configure("Treeview.Heading",
                        background="#1f2326",
                        foreground="white",
                        font=("Arial", 13, "bold"))
        style.map("Treeview", background=[("selected", "#3a3d3f")])

        table_frame = ctk.CTkFrame(main_area)
        table_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)

        columns = ("Name", "Price", "Quantity")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        tree.heading("Name", text="اسم المنتج")
        tree.heading("Price", text="السعر")
        tree.heading("Quantity", text="الكمية")
        tree.column("Name", width=200, anchor="center")
        tree.column("Price", width=100, anchor="center")
        tree.column("Quantity", width=100, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        main_area.rowconfigure(1, weight=1)
        main_area.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        def refresh_table():
            tree.delete(*tree.get_children())
            for p in Product.Product.load_all():
                tree.insert("", "end", values=(p.name, p.price, p.quantity))

        def clear_entries():
            name_entry.delete(0, "end")
            price_entry.delete(0, "end")
            quantity_entry.delete(0, "end")


        refresh_table()

        # === Entry Fields ===
        entry_frame = ctk.CTkFrame(main_area)
        entry_frame.grid(row=2, column=0, pady=10, padx=20, sticky="ew", columnspan=2)

        name_entry = ctk.CTkEntry(entry_frame, placeholder_text="اسم المنتج", font=("Arial", 14))
        name_entry.grid(row=0, column=0, padx=5)

        price_entry = ctk.CTkEntry(entry_frame, placeholder_text="السعر", font=("Arial", 14))
        price_entry.grid(row=0, column=1, padx=5)

        quantity_entry = ctk.CTkEntry(entry_frame, placeholder_text="الكمية", font=("Arial", 14))
        quantity_entry.grid(row=0, column=2, padx=5)

        # === Button Frame ===
        button_frame = ctk.CTkFrame(main_area)
        button_frame.grid(row=3, column=0, pady=10, padx=20, sticky="w", columnspan=2)

        add_btn = ctk.CTkButton(button_frame, text="إضافة", font=("Arial", 14))
        add_btn.grid(row=0, column=0, padx=10)

        edit_btn = ctk.CTkButton(button_frame, text="تعديل", font=("Arial", 14))
        delete_btn = ctk.CTkButton(button_frame, text="حذف", font=("Arial", 14))

        def add_product():
            try:
                name = name_entry.get()
                price = float(price_entry.get())
                quantity = float(quantity_entry.get())
                new_product = Product.Product(name, price, quantity)
                new_product.add_product()
                refresh_table()
                clear_entries()
                messagebox.showinfo("تم", "تمت إضافة المنتج")
            except ValueError:
                messagebox.showerror("خطأ", "الرجاء إدخال سعر وكمية صحيحة")

        def edit_product():
            selected = tree.focus()
            if not selected:
                return
            try:
                old_name = tree.item(selected, "values")[0]
                new_name = name_entry.get()
                new_price = float(price_entry.get())
                new_quantity = float(quantity_entry.get())

                all_products = Product.Product.load_all()
                for p in all_products:
                    if p.name == old_name:
                        p.edit_product(new_name, new_price, new_quantity)
                        break
                Product.Product.save_all(all_products)
                refresh_table()
                clear_entries()
                messagebox.showinfo("تم", "تم تعديل المنتج")
            except ValueError:
                messagebox.showerror("خطأ", "السعر والكمية يجب أن تكون أرقام")

        def delete_product():
            selected = tree.focus()
            if not selected:
                return
            name = tree.item(selected, "values")[0]
            confirm = messagebox.askyesno("تأكيد", f"هل تريد حذف المنتج '{name}'؟")
            if confirm:
                all_products = Product.Product.load_all()
                all_products = [p for p in all_products if p.name != name]
                Product.Product.save_all(all_products)
                refresh_table()
                clear_entries()
                messagebox.showinfo("تم", "تم حذف المنتج")

        def on_tree_select(event):
            selected = tree.focus()
            if selected:
                values = tree.item(selected, "values")
                clear_entries()
                name_entry.insert(0, values[0])
                price_entry.insert(0, values[1])
                quantity_entry.insert(0, values[2])

                # Show edit and delete buttons
                edit_btn.grid(row=0, column=1, padx=10)
                delete_btn.grid(row=0, column=2, padx=10)
            else:
                # Hide edit and delete buttons
                edit_btn.grid_forget()
                delete_btn.grid_forget()

        # Bind selection event
        tree.bind("<<TreeviewSelect>>", on_tree_select)

        # Link functions to buttons
        add_btn.configure(command=add_product)
        edit_btn.configure(command=edit_product)
        delete_btn.configure(command=delete_product)

    def on_Clients():
        for widget in main_area.winfo_children():
            widget.destroy()

        ctk.CTkLabel(main_area, text="العملاء", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, pady=(20, 10), columnspan=2, sticky="w")

        # === Treeview Styling ===
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2a2d2e",
                        foreground="white",
                        rowheight=25,
                        fieldbackground="#2a2d2e",
                        font=("Arial", 12))
        style.configure("Treeview.Heading",
                        background="#1f2326",
                        foreground="white",
                        font=("Arial", 13, "bold"))
        style.map("Treeview", background=[("selected", "#3a3d3f")])

        # === Search Bar ===
        search_frame = ctk.CTkFrame(main_area)
        search_frame.grid(row=0, column=1, padx=20, pady=(20, 10), sticky="e", columnspan=1)

        search_entry = ctk.CTkEntry(search_frame, placeholder_text="ابحث عن عميل...", font=("Arial", 14))
        search_entry.grid(row=0, column=0, padx=5)

        # === Table Frame ===
        table_frame = ctk.CTkFrame(main_area)
        table_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)

        columns = ("ID", "Name", "Phone", "Role", "Previous Balance")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text={
                "ID": "ID",
                "Name": "اسم العميل",
                "Phone": "رقم الهاتف",
                "Role": "الوظيفة",
                "Previous Balance": "الرصيد السابق"
            }[col])
            tree.column(col, anchor="center", width=150)
        tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        main_area.rowconfigure(1, weight=1)
        main_area.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # === Entry Fields ===
        entry_frame = ctk.CTkFrame(main_area)
        entry_frame.grid(row=2, column=0, pady=10, padx=20, sticky="ew", columnspan=2)

        name_entry = ctk.CTkEntry(entry_frame, placeholder_text="اسم العميل", font=("Arial", 14))
        name_entry.grid(row=0, column=0, padx=5)

        phone_entry = ctk.CTkEntry(entry_frame, placeholder_text="رقم الهاتف", font=("Arial", 14))
        phone_entry.grid(row=0, column=1, padx=5)

        role_entry = ctk.CTkComboBox(entry_frame, values=["", "بيع", "شراء"])
        role_entry.set("")
        role_entry.grid(row=0, column=2, padx=5)

        # === Button Frame ===
        button_frame = ctk.CTkFrame(main_area)
        button_frame.grid(row=3, column=0, pady=10, padx=20, sticky="w", columnspan=2)

        add_btn = ctk.CTkButton(button_frame, text="إضافة", font=("Arial", 14))
        add_btn.grid(row=0, column=0, padx=10)

        edit_btn = ctk.CTkButton(button_frame, text="تعديل", font=("Arial", 14))
        edit_btn.grid(row=0, column=1, padx=10)
        edit_btn.grid_remove()

        delete_btn = ctk.CTkButton(button_frame, text="حذف", font=("Arial", 14))
        delete_btn.grid(row=0, column=2, padx=10)
        delete_btn.grid_remove()

        def clear_entries():
            name_entry.delete(0, "end")
            phone_entry.delete(0, "end")
            role_entry.set("")

        def refresh_table(filter_text=""):
            tree.delete(*tree.get_children())
            for c in Client.Client.load_all():
                if filter_text:
                    query = filter_text.lower()
                    if (query in c.name.lower() or query in c.phone or query in c.role):
                        tree.insert("", "end", values=(c.id, c.name, c.phone, c.role, c.previous_balance))
                else:
                    tree.insert("", "end", values=(c.id, c.name, c.phone, c.role, c.previous_balance))

        def add_client():
            try:
                name = name_entry.get()
                phone = phone_entry.get()
                role = role_entry.get()
                if not name or not phone or role not in ["بيع", "شراء"]:
                    messagebox.showerror("خطأ", "جميع الحقول مطلوبة واختيار الوظيفة إجباري")
                    return
                new_client = Client.Client(name, phone, role)
                new_client.add_client()
                refresh_table()
                clear_entries()
                messagebox.showinfo("تم", "تمت إضافة العميل")
            except Exception as e:
                messagebox.showerror("Exception", str(e))

        def edit_client():
            selected = tree.selection()
            if selected:
                selected = selected[0]
                values = tree.item(selected, "values")
                client_id = values[0]
                new_name = name_entry.get()
                new_phone = phone_entry.get()
                new_role = role_entry.get()
                if not new_name or not new_phone or new_role not in ["بيع", "شراء"]:
                    messagebox.showerror("خطأ", "جميع الحقول مطلوبة")
                    return
                clients = Client.Client.load_all()
                for c in clients:
                    if c.id == client_id:
                        c.edit_client(new_name, new_phone, new_role)
                        break
                Client.Client.save_all(clients)
                refresh_table()
                clear_entries()
                messagebox.showinfo("تم", "تم تعديل العميل")

        def delete_client():
            selected = tree.selection()
            if selected:
                selected = selected[0]
                values = tree.item(selected, "values")
                client_id = values[0]
                confirm = messagebox.askyesno("تأكيد", f"هل تريد حذف العميل '{values[1]}'؟")
                if confirm:
                    clients = Client.Client.load_all()
                    clients = [c for c in clients if c.id != client_id]
                    Client.Client.save_all(clients)
                    refresh_table()
                    clear_entries()
                    messagebox.showinfo("تم", "تم حذف العميل")

        def on_tree_select(event):
            selected_items = tree.selection()
            if selected_items:
                selected = selected_items[0]
                values = tree.item(selected, "values")
                clear_entries()
                name_entry.insert(0, values[1])
                phone_entry.insert(0, values[2])
                role_entry.set(values[3])

                edit_btn.grid()
                delete_btn.grid()
            else:
                edit_btn.grid_remove()
                delete_btn.grid_remove()


        def on_search_typing(event):
            query = search_entry.get().strip().lower()
            refresh_table(query)

        # Bind events
        tree.bind("<<TreeviewSelect>>", on_tree_select)
        search_entry.bind("<KeyRelease>", on_search_typing)

        # Button commands
        add_btn.configure(command=add_client)
        edit_btn.configure(command=edit_client)
        delete_btn.configure(command=delete_client)

        # Initial display
        refresh_table()


    def on_transfers():
        for widget in main_area.winfo_children():
            widget.destroy()

        ctk.CTkLabel(main_area, text="سجل النقلات", font=("Arial", 24, "bold")).pack(pady=20)

        # === Filter Frame ===
        filter_frame = ctk.CTkFrame(main_area)
        filter_frame.pack(pady=10)

        ctk.CTkLabel(filter_frame, text="من:").grid(row=0, column=0, padx=5)
        from_entry = DateEntry(filter_frame, date_pattern="yyyy-mm-dd", width=12)
        from_entry.set_date(datetime.now().date())
        from_entry.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(filter_frame, text="إلى:").grid(row=0, column=2, padx=5)
        to_entry = DateEntry(filter_frame, date_pattern="yyyy-mm-dd", width=12)
        to_entry.set_date(datetime.now().date())
        to_entry.grid(row=0, column=3, padx=5)

        def apply_filter():
            tree.delete(*tree.get_children())
            from_date = from_entry.get_date()
            to_date = to_entry.get_date()

            for t in Transfer.load_all():
                t_date = datetime.strptime(t.date[:10], "%Y-%m-%d").date()
                if from_date <= t_date <= to_date:
                    tree.insert("", "end", values=(t.transfer_id, t.client_name, t.product_name, t.quantity, t.price, t.cash_paid_now, t.date))

        def show_all():
            refresh_transfers()

        ctk.CTkButton(filter_frame, text="تصفية", command=apply_filter, font=("Arial", 14)).grid(row=0, column=4, padx=10)
        ctk.CTkButton(filter_frame, text="عرض الكل", command=show_all, font=("Arial", 14)).grid(row=0, column=5, padx=5)

        # === Treeview ===
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", rowheight=25,
                        fieldbackground="#2a2d2e", font=("Arial", 12))
        style.configure("Treeview.Heading", background="#1f2326", foreground="white", font=("Arial", 13, "bold"))
        style.map("Treeview", background=[("selected", "#3a3d3f")])

        table_frame = ctk.CTkFrame(main_area)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("transfer_id", "client_name", "product_name", "quantity", "price", "cash_paid_now", "date")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=140)
        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        def refresh_transfers():
            tree.delete(*tree.get_children())
            for t in Transfer.load_all():
                tree.insert("", "end", values=(t.transfer_id, t.client_name, t.product_name, t.quantity, t.price, t.cash_paid_now, t.date))

        def open_add_transfer():
            win = ctk.CTkToplevel(root)
            win.title("إضافة نقلة")
            win.geometry("400x450")
            win.grab_set()

            ctk.CTkLabel(win, text="إضافة نقلة جديدة", font=("Arial", 18, "bold")).pack(pady=10)
            form_frame = ctk.CTkFrame(win)
            form_frame.pack(pady=10, padx=20, fill="x")

            clients = [c for c in Client.Client.load_all() if c.role == "بيع"]
            client_dict = {f"{c.id} - {c.name}": c for c in clients}
            client_combo = ctk.CTkComboBox(form_frame, values=["اختر عميل"] + list(client_dict.keys()))
            client_combo.set("اختر عميل")
            client_combo.pack(pady=5, fill="x")

            products = Product.Product.load_all()
            product_dict = {p.name: p for p in products}
            product_combo = ctk.CTkComboBox(form_frame, values=["اختر منتج"] + list(product_dict.keys()))
            product_combo.set("اختر منتج")
            product_combo.pack(pady=5, fill="x")

            quantity_entry = ctk.CTkEntry(form_frame, placeholder_text="الكمية", font=("Arial", 14))
            quantity_entry.pack(pady=5, fill="x")

            price_entry = ctk.CTkEntry(form_frame, placeholder_text="السعر", font=("Arial", 14))
            price_entry.pack(pady=5, fill="x")

            cash_paid_entry = ctk.CTkEntry(form_frame, placeholder_text="المدفوع الآن", font=("Arial", 14))
            cash_paid_entry.pack(pady=5, fill="x")

            def confirm_add():
                client_key = client_combo.get()
                product_name = product_combo.get()
                quantity = quantity_entry.get()
                price = price_entry.get()
                cash_paid_now = cash_paid_entry.get()

                if client_key == "اختر عميل" or product_name == "اختر منتج" or not quantity or not price or not cash_paid_now:
                    messagebox.showerror("خطأ", "يرجى ملء جميع الحقول")
                    return

                try:
                    quantity = float(quantity)
                    price = float(price)
                    cash_paid_now = float(cash_paid_now)
                except ValueError:
                    messagebox.showerror("خطأ", "يرجى إدخال أرقام صحيحة")
                    return

                client = client_dict[client_key]
                transfer = Transfer(client.name, product_name, quantity, price, cash_paid_now)
                transfer.add_transfer()

                product = product_dict[product_name]
                product.quantity += quantity
                product._update_in_file()

                client.previous_balance += (price - cash_paid_now)
                client._update_in_file()

                refresh_transfers()
                win.destroy()
                messagebox.showinfo("نجاح", "تمت إضافة النقلة")

            ctk.CTkButton(form_frame, text="إضافة", command=confirm_add).pack(pady=10)

        def delete_transfer():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("خطأ", "يرجى اختيار نقلة للحذف")
                return

            item = tree.item(selected[0])
            transfer_id = item['values'][0]
            client_name = item['values'][1]
            product_name = item['values'][2]
            quantity = float(item['values'][3])
            price = float(item['values'][4])
            cash_paid_now = float(item['values'][5])

            transfers = Transfer.load_all()
            transfer = next((t for t in transfers if t.transfer_id == transfer_id), None)

            if transfer:
                transfer.remove_transfer()

                products = Product.Product.load_all()
                for p in products:
                    if p.name == product_name:
                        p.quantity -= quantity
                        break
                Product.Product.save_all(products)

                clients = Client.Client.load_all()
                for c in clients:
                    if c.name == client_name:
                        c.previous_balance -= (price - cash_paid_now)
                        c._update_in_file()
                        break

                refresh_transfers()
                messagebox.showinfo("تم", "تم حذف النقلة")

        action_frame = ctk.CTkFrame(main_area)
        action_frame.pack(pady=10)
        ctk.CTkButton(action_frame, text="إضافة نقلة", command=open_add_transfer, font=("Arial", 14)).pack(side="left", padx=10)
        ctk.CTkButton(action_frame, text="حذف نقلة", command=delete_transfer, font=("Arial", 14)).pack(side="left", padx=10)

        refresh_transfers()
 

    def show_change_password():
        on_Cpassword(main_area)

    def on_logout():
        start_login_page()

    ctk.CTkButton(sidebar, text="الخزنة", command=lambda: clear_main_area_and_show(on_treasury), font=("Arial", 14)).pack(pady=10)
    ctk.CTkButton(sidebar, text="المنتجات", command=lambda: clear_main_area_and_show(on_products), font=("Arial", 14)).pack(pady=10)
    ctk.CTkButton(sidebar, text="سجل العملاء", command=lambda: clear_main_area_and_show(on_Clients), font=("Arial", 14)).pack(pady=10)
    ctk.CTkButton(sidebar, text="سجل النقلات", command=lambda: clear_main_area_and_show(on_transfers), font=("Arial", 14)).pack(pady=10)
    ctk.CTkButton(sidebar, text="تغيير كلمة السر", command=show_change_password, font=("Arial", 14)).pack(pady=10)
    ctk.CTkButton(sidebar, text="تسجيل خروج", command=on_logout, font=("Arial", 14)).pack(pady=20)

    clear_main_area_and_show(on_treasury)
    root.state("zoomed")


def on_Cpassword(main_area):
    for widget in main_area.winfo_children():
        widget.destroy()

    ctk.CTkLabel(main_area, text="Change Password", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

    new_pass_entry = ctk.CTkEntry(main_area, show="*", placeholder_text="New Password", width=300)
    new_pass_entry.pack(pady=10)

    confirm_pass_entry = ctk.CTkEntry(main_area, show="*", placeholder_text="Confirm Password", width=300)
    confirm_pass_entry.pack(pady=10)

    def update_password():
        new_pass = new_pass_entry.get()
        confirm_pass = confirm_pass_entry.get()

        if not new_pass or not confirm_pass:
            messagebox.showerror("Error", "Both fields are required.")
        elif new_pass != confirm_pass:
            messagebox.showerror("Error", "Passwords do not match.")
        else:
            with open("login", "r") as f:
                lines = f.readlines()
            lines[1] = new_pass + "\n"
            with open("login", "w") as f:
                f.writelines(lines)
            messagebox.showinfo("Success", "Password updated successfully.")
            clear_main_area_and_show(lambda: ctk.CTkLabel(main_area, text="الخزنة", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=40))


    ctk.CTkButton(main_area, text="Update Password", command=update_password).pack(pady=20)



def clear_window():
    for widget in root.winfo_children():
        widget.destroy()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Admin Panel")
root.state("zoomed")
root.resizable(True, True)

start_login_page()

root.mainloop()