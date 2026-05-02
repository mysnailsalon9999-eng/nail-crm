from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
import json, os
from datetime import datetime, date, timedelta
from kivy.utils import platform


# ── Màu sắc ──────────────────────────────────────────────────────────────────
PINK       = (0.831, 0.325, 0.494, 1)
PINK_LIGHT = (0.984, 0.918, 0.941, 1)
PINK_MID   = (0.929, 0.576, 0.694, 1)
WHITE      = (1, 1, 1, 1)
BG         = (0.976, 0.965, 0.957, 1)
MUTED      = (0.533, 0.529, 0.502, 1)
DARK       = (0.173, 0.173, 0.165, 1)
GREEN      = (0.231, 0.427, 0.067, 1)
GREEN_BG   = (0.918, 0.953, 0.871, 1)
AMBER      = (0.729, 0.459, 0.090, 1)
RED        = (0.639, 0.176, 0.176, 1)
RED_BG     = (0.988, 0.922, 0.922, 1)

def get_data_path():
    """Return a writable data path on Android and a local path on desktop."""
    if platform == "android":
        try:
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), "nail_crm_data.json")
        except Exception as e:
            print("ANDROID STORAGE PATH ERROR:", e)
            return os.path.join(os.getcwd(), "nail_crm_data.json")
    return "nail_crm_data.json"

DATA_FILE = get_data_path()

def default_data():
    return {"customers": [], "queue": [], "next_tx_id": 1}

# ── Data layer ────────────────────────────────────────────────────────────────
def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return default_data()
            data.setdefault("customers", [])
            data.setdefault("queue", [])
            data.setdefault("next_tx_id", 1)
            return data
    except Exception as e:
        print("LOAD DATA ERROR:", e)
    return default_data()

def save_data(data):
    try:
        folder = os.path.dirname(DATA_FILE)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("SAVE DATA ERROR:", e)

def update_canvas_rect(widget):
    """Safely update Rectangle/RoundedRectangle background instructions."""
    try:
        for instr in widget.canvas.before.children:
            if hasattr(instr, "pos") and hasattr(instr, "size"):
                instr.pos = widget.pos
                instr.size = widget.size
    except Exception as e:
        print("CANVAS UPDATE ERROR:", e)

def get_next_code(data):
    used = set(c["code"] for c in data["customers"] if c.get("code"))
    n = 1
    while n in used: n += 1
    return n

def auto_archive(data):
    cutoff = date.today() - timedelta(days=180)
    for c in data["customers"]:
        if c["status"] == "active" and c.get("last_visit"):
            try:
                if date.fromisoformat(c["last_visit"]) < cutoff:
                    c["status"] = "archive"
                    if c.get("code"):
                        c["_old_code"] = c["code"]
                        c["code"] = None
            except: pass

def is_birthday_this_month(bd):
    if not bd: return False
    try: return date.fromisoformat(bd).month == date.today().month
    except: return False

def days_since(d):
    if not d: return 9999
    try: return (date.today() - date.fromisoformat(d)).days
    except: return 9999

def fmt_date(d):
    if not d or d == "—": return "—"
    try: return date.fromisoformat(d).strftime("%d/%m/%Y")
    except: return d

# ── Widget helpers ────────────────────────────────────────────────────────────
class RoundBtn(Button):
    def __init__(self, text="", bg=PINK, fg=WHITE, radius=12, **kw):
        super().__init__(text=text, **kw)
        self.bg_color = bg
        self.fg_color = fg
        self.rad = radius
        self.color = fg
        self.background_color = (0,0,0,0)
        self.background_normal = ""
        self.bold = True
        self.font_size = sp(14)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[dp(self.rad)])

class Card(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*WHITE)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])

class StatCard(BoxLayout):
    def __init__(self, value="0", label="", **kw):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(2), **kw)
        self.bind(pos=self._redraw, size=self._redraw)
        self.val_lbl = Label(text=str(value), font_size=sp(22), bold=True,
                             color=PINK, size_hint_y=None, height=dp(30))
        self.lbl_lbl = Label(text=label, font_size=sp(11),
                             color=MUTED, size_hint_y=None, height=dp(16))
        self.add_widget(self.val_lbl)
        self.add_widget(self.lbl_lbl)

    def _redraw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*BG)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])

    def update(self, value, label=None):
        self.val_lbl.text = str(value)
        if label: self.lbl_lbl.text = label

class SectionLabel(Label):
    def __init__(self, text="", **kw):
        super().__init__(text=text.upper(), font_size=sp(10), bold=True,
                         color=MUTED, halign="left", size_hint_y=None,
                         height=dp(24), **kw)
        self.bind(size=lambda *a: setattr(self, "text_size", (self.width, None)))

class FormField(BoxLayout):
    def __init__(self, label="", hint="", value="", multiline=False, **kw):
        super().__init__(orientation="vertical", spacing=dp(2),
                         size_hint_y=None, height=dp(68), **kw)
        self.add_widget(Label(text=label, font_size=sp(12), color=MUTED,
                              halign="left", size_hint_y=None, height=dp(18),
                              text_size=(Window.width - dp(40), None)))
        self.inp = TextInput(text=str(value), hint_text=hint,
                             multiline=multiline, font_size=sp(14),
                             background_color=WHITE,
                             foreground_color=DARK,
                             cursor_color=PINK,
                             size_hint_y=None, height=dp(42))
        self.add_widget(self.inp)

    @property
    def value(self):
        return self.inp.text.strip()

# ── Popup helpers ─────────────────────────────────────────────────────────────
def show_confirm(title, msg, on_yes):
    content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
    content.add_widget(Label(text=msg, font_size=sp(14), color=DARK,
                             halign="center", text_size=(dp(260), None)))
    btns = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(44))
    popup = Popup(title=title, content=content,
                  size_hint=(None, None), size=(dp(300), dp(180)))
    no  = RoundBtn("Huỷ", bg=BG, fg=DARK)
    yes = RoundBtn("Xác nhận", bg=PINK, fg=WHITE)
    no.bind(on_release=popup.dismiss)
    def _yes(inst):
        popup.dismiss()
        on_yes()
    yes.bind(on_release=_yes)
    btns.add_widget(no); btns.add_widget(yes)
    content.add_widget(btns)
    popup.open()

def show_toast(msg, duration=2.5):
    lbl = Label(text=msg, font_size=sp(13), color=WHITE,
                halign="center", text_size=(dp(280), None))
    p = Popup(title="", content=lbl, separator_height=0,
              size_hint=(None, None), size=(dp(300), dp(80)),
              background_color=(0.1, 0.1, 0.1, 0.85))
    p.open()
    Clock.schedule_once(lambda dt: p.dismiss(), duration)

# ── Visit Popup ───────────────────────────────────────────────────────────────
class VisitPopup(Popup):
    def __init__(self, app, customer, **kw):
        self.app = app
        self.customer = customer
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))

        scroll = ScrollView()
        inner  = BoxLayout(orientation="vertical", spacing=dp(8),
                           size_hint_y=None)
        inner.bind(minimum_height=inner.setter("height"))

        self.f_color = FormField("Màu móng", "VD: Đỏ hồng, #ff6b9d...",
                                 customer.get("color_name",""))
        self.f_book  = FormField("Quyển màu (1-10)", "VD: 3",
                                 str(customer.get("book") or 1))
        self.f_code  = FormField("Số màu (tuỳ chọn)", "VD: 203, A15...")
        self.f_staff = FormField("Nhân viên", "Tên nhân viên...")
        self.f_note  = FormField("Ghi chú", "Ghi chú thêm...")

        for w in [self.f_color, self.f_book, self.f_code,
                  self.f_staff, self.f_note]:
            inner.add_widget(w)

        scroll.add_widget(inner)
        content.add_widget(scroll)

        btns = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(46))
        cancel = RoundBtn("Huỷ", bg=BG, fg=DARK)
        ok     = RoundBtn("✅ Xác nhận +1 lượt", bg=PINK, fg=WHITE)
        cancel.bind(on_release=self.dismiss)
        ok.bind(on_release=self._confirm)
        btns.add_widget(cancel); btns.add_widget(ok)
        content.add_widget(btns)

        super().__init__(
            title=f"💅 +1 Lượt — {customer['name']}",
            content=content,
            size_hint=(0.95, 0.85), **kw)

    def _confirm(self, *a):
        today = date.today().isoformat()
        c = self.customer
        c["visits"]    = c.get("visits", 0) + 1
        c["points"]    = c.get("points", 0) + 1
        c["color_name"]= self.f_color.value
        try: c["book"] = int(self.f_book.value) if self.f_book.value else 1
        except: c["book"] = 1
        c["last_visit"]= today
        if c["status"] == "archive": c["status"] = "active"
        tx = {"id": self.app.data["next_tx_id"], "type": "visit",
              "date": today, "color_name": c["color_name"],
              "book": c["book"], "color_code": self.f_code.value,
              "staff": self.f_staff.value, "note": self.f_note.value}
        self.app.data["next_tx_id"] += 1
        c.setdefault("transactions", []).insert(0, tx)
        save_data(self.app.data)
        self.dismiss()
        msg = f"✅ +1 lượt cho {c['name']}"
        if c.get("points", 0) >= 10: msg += "\n🎁 Đủ ưu đãi!"
        show_toast(msg)
        self.app.refresh_current()

# ── Customer Form Popup ───────────────────────────────────────────────────────
class CustomerPopup(Popup):
    def __init__(self, app, customer=None, **kw):
        self.app      = app
        self.customer = customer
        is_new        = customer is None
        title_str     = "Thêm khách mới" if is_new else f"Sửa: {customer['name']}"

        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        scroll  = ScrollView()
        inner   = BoxLayout(orientation="vertical", spacing=dp(8),
                            size_hint_y=None)
        inner.bind(minimum_height=inner.setter("height"))

        self.f_name  = FormField("Tên khách *", "Họ và tên...",
                                 customer["name"] if customer else "")
        self.f_phone = FormField("Số điện thoại", "09xx...",
                                 customer.get("phone","") if customer else "")
        self.f_bday  = FormField("Sinh nhật", "YYYY-MM-DD (VD: 1990-05-20)",
                                 customer.get("birthday","") if customer else "")
        self.f_note  = FormField("Ghi chú", "Thích màu...",
                                 customer.get("note","") if customer else "")

        for w in [self.f_name, self.f_phone, self.f_bday, self.f_note]:
            inner.add_widget(w)

        if not is_new:
            self.f_pts = FormField("Điểm hiện tại", "0",
                                   str(customer.get("points", 0)))
            self.f_code= FormField("Mã KH", "Để trống nếu chưa có",
                                   str(customer.get("code","")) if customer.get("code") else "")
            self.f_color= FormField("Màu móng", "VD: Đỏ hồng...",
                                    customer.get("color_name",""))
            self.f_book = FormField("Quyển màu", "1-10",
                                    str(customer.get("book") or 1))
            for w in [self.f_pts, self.f_code, self.f_color, self.f_book]:
                inner.add_widget(w)
        else:
            next_code = get_next_code(app.data)
            self.auto_code_lbl = Label(
                text=f"✅ Sẽ tự gán mã #{next_code}",
                font_size=sp(13), color=PINK,
                size_hint_y=None, height=dp(30))
            inner.add_widget(self.auto_code_lbl)

        scroll.add_widget(inner)
        content.add_widget(scroll)

        btns = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(46))
        if not is_new:
            del_btn = RoundBtn("🗑️ Xoá", bg=RED_BG, fg=RED)
            del_btn.bind(on_release=self._delete)
            btns.add_widget(del_btn)
        cancel = RoundBtn("Huỷ", bg=BG, fg=DARK)
        save   = RoundBtn("💾 Lưu", bg=PINK, fg=WHITE)
        cancel.bind(on_release=self.dismiss)
        save.bind(on_release=self._save)
        btns.add_widget(cancel)
        btns.add_widget(save)
        content.add_widget(btns)

        super().__init__(title=title_str, content=content,
                         size_hint=(0.95, 0.9), **kw)

    def _save(self, *a):
        name = self.f_name.value
        if not name:
            show_toast("⚠️ Vui lòng nhập tên khách!")
            return
        today = date.today().isoformat()
        bd    = self.f_bday.value

        if self.customer:
            old_pts = self.customer.get("points", 0)
            try: new_pts = int(self.f_pts.value)
            except: new_pts = old_pts
            try: book = int(self.f_book.value)
            except: book = 1
            try: code = int(self.f_code.value) if self.f_code.value.isdigit() else None
            except: code = None
            self.customer.update({
                "name": name, "phone": self.f_phone.value,
                "birthday": bd, "note": self.f_note.value,
                "points": new_pts, "code": code,
                "color_name": self.f_color.value, "book": book,
            })
            if new_pts != old_pts:
                tx = {"id": self.app.data["next_tx_id"], "type": "adjust",
                      "date": today,
                      "note": f"Điều chỉnh: {old_pts} → {new_pts}"}
                self.app.data["next_tx_id"] += 1
                self.customer.setdefault("transactions",[]).insert(0, tx)
        else:
            code = get_next_code(self.app.data)
            self.app.data["customers"].append({
                "id": int(datetime.now().timestamp() * 1000),
                "name": name, "phone": self.f_phone.value,
                "birthday": bd, "code": code,
                "visits": 0, "points": 0,
                "color_name": "", "book": 1,
                "last_visit": today, "transactions": [],
                "note": self.f_note.value, "status": "active"
            })

        save_data(self.app.data)
        self.dismiss()
        show_toast("✅ Đã lưu thành công!")
        self.app.refresh_current()

    def _delete(self, *a):
        def do_delete():
            self.app.data["customers"] = [
                c for c in self.app.data["customers"]
                if c["id"] != self.customer["id"]]
            save_data(self.app.data)
            self.dismiss()
            show_toast("🗑️ Đã xoá khách hàng")
            self.app.refresh_current()
        show_confirm("Xác nhận xoá",
                     f"Xoá {self.customer['name']}\nvà toàn bộ lịch sử?",
                     do_delete)

# ── Queue Popup ───────────────────────────────────────────────────────────────
class QueuePopup(Popup):
    def __init__(self, app, **kw):
        self.app = app
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        self.f_name  = FormField("Tên khách *", "Tên khách...")
        self.f_phone = FormField("Số điện thoại", "09xx...")
        self.f_note  = FormField("Ghi chú", "Ghi chú...")
        for w in [self.f_name, self.f_phone, self.f_note]:
            content.add_widget(w)
        btns = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(46))
        cancel = RoundBtn("Huỷ", bg=BG, fg=DARK)
        ok     = RoundBtn("✅ Thêm vào hàng chờ", bg=PINK, fg=WHITE)
        cancel.bind(on_release=self.dismiss)
        ok.bind(on_release=self._save)
        btns.add_widget(cancel); btns.add_widget(ok)
        content.add_widget(btns)
        super().__init__(title="Thêm vào hàng chờ", content=content,
                         size_hint=(0.95, 0.7), **kw)

    def _save(self, *a):
        name = self.f_name.value
        if not name:
            show_toast("⚠️ Vui lòng nhập tên!")
            return
        self.app.data["queue"].append({
            "id": int(datetime.now().timestamp() * 1000),
            "name": name, "phone": self.f_phone.value,
            "note": self.f_note.value,
            "added_date": date.today().isoformat()
        })
        save_data(self.app.data)
        self.dismiss()
        show_toast("✅ Đã thêm vào hàng chờ")
        self.app.refresh_current()

# ── Customer Row ──────────────────────────────────────────────────────────────
class CustomerRow(BoxLayout):
    def __init__(self, app, customer, **kw):
        super().__init__(orientation="horizontal", spacing=dp(6),
                         size_hint_y=None, height=dp(72),
                         padding=[dp(10), dp(6), dp(10), dp(6)], **kw)
        self.app = app
        self.c   = customer
        self.bind(pos=self._redraw, size=self._redraw)

        # Avatar
        c = customer
        initials = "".join(w[0] for w in c["name"].split() if w)[-2:].upper()
        av = Label(text=initials, font_size=sp(15), bold=True,
                   color=WHITE, size_hint=(None, None),
                   size=(dp(42), dp(42)))
        with av.canvas.before:
            Color(*PINK)
            self._av_rect = RoundedRectangle(radius=[dp(21)])
        av.bind(pos=lambda *a: setattr(self._av_rect, "pos", av.pos),
                size=lambda *a: setattr(self._av_rect, "size", av.size))
        self.add_widget(av)

        # Info
        info = BoxLayout(orientation="vertical", spacing=dp(2))
        bd_tag = " 🎂" if is_birthday_this_month(c.get("birthday")) else ""
        code_str = f"  #Mã {c['code']}" if c.get("code") else "  Chưa có mã"
        pts = c.get("points", 0)
        mau = c.get("color_name","")
        mau_str = f"🎨 Q{c.get('book','?')} {mau}" if mau else ""
        pts_str = f"⭐{c.get('visits',0)} lượt  |  💎{pts} điểm{'  🎁' if pts>=10 else ''}"

        info.add_widget(Label(
            text=f"{c['name']}{bd_tag}{code_str}",
            font_size=sp(14), bold=True, color=DARK,
            halign="left", size_hint_y=None, height=dp(22),
            text_size=(Window.width * 0.45, None)))
        info.add_widget(Label(
            text=pts_str, font_size=sp(11), color=MUTED,
            halign="left", size_hint_y=None, height=dp(18),
            text_size=(Window.width * 0.45, None)))
        if mau_str:
            info.add_widget(Label(
                text=mau_str, font_size=sp(11), color=MUTED,
                halign="left", size_hint_y=None, height=dp(16),
                text_size=(Window.width * 0.45, None)))
        self.add_widget(info)

        # Buttons
        btn_box = BoxLayout(orientation="vertical", spacing=dp(4),
                            size_hint=(None, 1), width=dp(80))
        visit_btn = RoundBtn("💅 +1", bg=PINK, fg=WHITE, radius=8,
                             font_size=sp(12), size_hint_y=None, height=dp(30))
        edit_btn  = RoundBtn("✏️ Sửa", bg=BG, fg=DARK, radius=8,
                             font_size=sp(12), size_hint_y=None, height=dp(26))
        visit_btn.bind(on_release=lambda *a: self._visit())
        edit_btn.bind(on_release=lambda *a: self._edit())
        btn_box.add_widget(visit_btn)
        btn_box.add_widget(edit_btn)
        if not c.get("code"):
            code_btn = RoundBtn("🔢 Gán", bg=GREEN_BG, fg=GREEN, radius=8,
                               font_size=sp(11), size_hint_y=None, height=dp(22))
            code_btn.bind(on_release=lambda *a: self._assign())
            btn_box.add_widget(code_btn)
        self.add_widget(btn_box)

    def _redraw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*WHITE)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])

    def _visit(self):
        VisitPopup(self.app, self.c).open()

    def _edit(self):
        CustomerPopup(self.app, self.c).open()

    def _assign(self):
        self.c["code"] = get_next_code(self.app.data)
        save_data(self.app.data)
        show_toast(f"✅ Đã gán mã #{self.c['code']}")
        self.app.refresh_current()

# ── Screens ───────────────────────────────────────────────────────────────────
class BaseScreen(Screen):
    def __init__(self, app_ref, **kw):
        super().__init__(**kw)
        self.app_ref = app_ref
        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle()
        self.bind(pos=self._upd_bg, size=self._upd_bg)

    def _upd_bg(self, *a):
        self._bg.pos  = self.pos
        self._bg.size = self.size

    def refresh(self):
        pass


class CustomerScreen(BaseScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(app_ref, name="customers", **kw)
        self.current_filter = "all"
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", spacing=0)

        # Topbar
        topbar = BoxLayout(orientation="vertical", size_hint_y=None,
                           height=dp(110), padding=dp(10), spacing=dp(6))
        with topbar.canvas.before:
            Color(*WHITE); Rectangle(pos=topbar.pos, size=topbar.size)
        topbar.bind(pos=lambda *a, w=topbar: update_canvas_rect(w),
                    size=lambda *a, w=topbar: update_canvas_rect(w))

        # Title + stats
        title_row = BoxLayout(size_hint_y=None, height=dp(30))
        title_row.add_widget(Label(text="👥 Khách hàng", font_size=sp(18),
                                   bold=True, color=DARK, halign="left",
                                   text_size=(dp(200), None)))
        self.chips = BoxLayout(spacing=dp(6))
        self.chip_widgets = {}
        for k, l in [("kh","Khách"),("vip","VIP"),("uu","Ưu đãi"),("cho","Hàng chờ")]:
            c = BoxLayout(orientation="vertical", padding=dp(4))
            with c.canvas.before:
                Color(*BG)
                RoundedRectangle(pos=c.pos, size=c.size, radius=[dp(6)])
            c.bind(pos=lambda i,v,w=c: self._upd_chip(w),
                   size=lambda i,v,w=c: self._upd_chip(w))
            vl = Label(text="0", font_size=sp(14), bold=True, color=PINK)
            ll = Label(text=l, font_size=sp(9), color=MUTED)
            c.add_widget(vl); c.add_widget(ll)
            self.chips.add_widget(c)
            self.chip_widgets[k] = vl
        title_row.add_widget(self.chips)
        topbar.add_widget(title_row)

        # Search
        self.search = TextInput(hint_text="🔍 Tìm tên, SĐT, mã KH...",
                                multiline=False, font_size=sp(13),
                                size_hint_y=None, height=dp(36),
                                background_color=BG, foreground_color=DARK)
        self.search.bind(text=lambda *a: self.refresh())
        topbar.add_widget(self.search)

        # Filter chips
        filter_row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(6))
        self.filter_btns = {}
        for fk, fl in [("all","Tất cả"),("vip","⭐ VIP"),
                        ("promo","🎁 Ưu đãi"),("bday","🎂 SN"),("idle","😴 Lâu")]:
            btn = ToggleButton(text=fl, group="filter", font_size=sp(11),
                               background_normal="", background_down="",
                               size_hint_x=None, width=dp(70))
            btn.bind(on_release=lambda b, k=fk: self._set_filter(k))
            if fk == "all":
                btn.state = "down"
                btn.background_color = PINK
                btn.color = WHITE
            else:
                btn.background_color = WHITE
                btn.color = MUTED
            filter_row.add_widget(btn)
            self.filter_btns[fk] = btn
        topbar.add_widget(filter_row)
        root.add_widget(topbar)

        # List
        self.scroll = ScrollView()
        self.list_layout = BoxLayout(orientation="vertical", spacing=dp(6),
                                     padding=[dp(8), dp(8), dp(8), dp(80)],
                                     size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.scroll.add_widget(self.list_layout)
        root.add_widget(self.scroll)

        # FAB buttons
        fab_box = BoxLayout(orientation="horizontal", spacing=dp(10),
                            size_hint=(None, None), size=(dp(230), dp(46)),
                            pos_hint={"right":0.98, "y":0.01})
        queue_btn = RoundBtn("+ Hàng chờ", bg=WHITE, fg=PINK, radius=23,
                             font_size=sp(13))
        new_btn   = RoundBtn("+ Khách mới", bg=PINK, fg=WHITE, radius=23,
                             font_size=sp(13))
        queue_btn.bind(on_release=lambda *a: QueuePopup(self.app_ref).open())
        new_btn.bind(on_release=lambda *a: CustomerPopup(self.app_ref).open())
        fab_box.add_widget(queue_btn)
        fab_box.add_widget(new_btn)

        from kivy.uix.floatlayout import FloatLayout
        fl = FloatLayout()
        fl.add_widget(root)
        fl.add_widget(fab_box)
        self.add_widget(fl)

    def _upd_chip(self, w):
        update_canvas_rect(w)

    def _set_filter(self, f):
        self.current_filter = f
        for k, btn in self.filter_btns.items():
            if k == f:
                btn.background_color = PINK
                btn.color = WHITE
            else:
                btn.background_color = WHITE
                btn.color = MUTED
        self.refresh()

    def refresh(self):
        data = self.app_ref.data
        active = [c for c in data["customers"] if c["status"] != "archive"]
        # Update chips
        self.chip_widgets["kh"].text  = str(len(active))
        self.chip_widgets["vip"].text = str(sum(1 for c in active if c.get("visits",0)>=10))
        self.chip_widgets["uu"].text  = str(sum(1 for c in active if c.get("points",0)>=10))
        self.chip_widgets["cho"].text = str(len(data["queue"]))

        # Filter
        q = self.search.text.lower().strip()
        lst = active[:]
        if q:
            lst = [c for c in lst if q in c["name"].lower()
                   or q in c.get("phone","")
                   or (c.get("code") and q in str(c["code"]))]
        f = self.current_filter
        if f == "vip":   lst = [c for c in lst if c.get("visits",0)>=10]
        if f == "promo": lst = [c for c in lst if c.get("points",0)>=10]
        if f == "bday":  lst = [c for c in lst if is_birthday_this_month(c.get("birthday"))]
        if f == "idle":  lst = [c for c in lst if days_since(c.get("last_visit"))>90]

        self.list_layout.clear_widgets()
        if not lst:
            self.list_layout.add_widget(
                Label(text="Không tìm thấy khách hàng", font_size=sp(14),
                      color=MUTED, size_hint_y=None, height=dp(60)))
        for c in lst:
            self.list_layout.add_widget(CustomerRow(self.app_ref, c))


class QueueScreen(BaseScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(app_ref, name="queue", **kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        hdr  = BoxLayout(size_hint_y=None, height=dp(54), padding=dp(12))
        with hdr.canvas.before:
            Color(*WHITE); Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda *a, w=hdr: update_canvas_rect(w),
                 size=lambda *a, w=hdr: update_canvas_rect(w))
        hdr.add_widget(Label(text="⏳ Hàng chờ", font_size=sp(18),
                             bold=True, color=DARK, halign="left",
                             text_size=(dp(300), None)))
        root.add_widget(hdr)
        self.scroll = ScrollView()
        self.lst = BoxLayout(orientation="vertical", spacing=dp(6),
                             padding=dp(8), size_hint_y=None)
        self.lst.bind(minimum_height=self.lst.setter("height"))
        self.scroll.add_widget(self.lst)
        root.add_widget(self.scroll)

        fab = RoundBtn("+ Thêm vào hàng chờ", bg=PINK, fg=WHITE, radius=23,
                       font_size=sp(13), size_hint=(None, None),
                       size=(dp(220), dp(46)),
                       pos_hint={"center_x":0.5, "y":0.01})
        fab.bind(on_release=lambda *a: QueuePopup(self.app_ref).open())

        from kivy.uix.floatlayout import FloatLayout
        fl = FloatLayout()
        fl.add_widget(root)
        fl.add_widget(fab)
        self.add_widget(fl)

    def refresh(self):
        self.lst.clear_widgets()
        for qi in self.app_ref.data["queue"]:
            row = BoxLayout(orientation="horizontal", spacing=dp(8),
                            size_hint_y=None, height=dp(64),
                            padding=[dp(10), dp(8), dp(10), dp(8)])
            with row.canvas.before:
                Color(*WHITE)
                RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(10)])
            row.bind(pos=lambda i,v,r=row: self._upd_row(r),
                     size=lambda i,v,r=row: self._upd_row(r))
            info = BoxLayout(orientation="vertical")
            info.add_widget(Label(text=qi["name"], font_size=sp(14),
                                  bold=True, color=DARK, halign="left",
                                  text_size=(dp(200), None), size_hint_y=None, height=dp(22)))
            info.add_widget(Label(text=qi.get("phone","") + "  " + qi.get("note",""),
                                  font_size=sp(11), color=MUTED, halign="left",
                                  text_size=(dp(200), None), size_hint_y=None, height=dp(18)))
            row.add_widget(info)
            btns = BoxLayout(spacing=dp(6), size_hint=(None,1), width=dp(140))
            promo = RoundBtn("✅ Gán mã", bg=PINK, fg=WHITE, radius=8,
                             font_size=sp(11), size_hint_y=None, height=dp(34))
            promo.bind(on_release=lambda *a, q=qi: self._promote(q))
            dele = RoundBtn("🗑️", bg=RED_BG, fg=RED, radius=8,
                            font_size=sp(13), size_hint=(None,None),
                            size=(dp(36),dp(34)))
            dele.bind(on_release=lambda *a, q=qi: self._delete(q))
            btns.add_widget(promo); btns.add_widget(dele)
            row.add_widget(btns)
            self.lst.add_widget(row)

        if not self.app_ref.data["queue"]:
            self.lst.add_widget(Label(text="Hàng chờ trống ✅",
                                      font_size=sp(14), color=MUTED,
                                      size_hint_y=None, height=dp(60)))

    def _upd_row(self, r):
        update_canvas_rect(r)

    def _promote(self, qi):
        code = get_next_code(self.app_ref.data)
        self.app_ref.data["customers"].append({
            "id": int(datetime.now().timestamp()*1000),
            "name": qi["name"], "phone": qi.get("phone",""),
            "birthday": "", "code": code,
            "visits": 0, "points": 0, "color_name": "", "book": 1,
            "last_visit": date.today().isoformat(),
            "transactions": [], "note": qi.get("note",""), "status": "active"
        })
        self.app_ref.data["queue"] = [x for x in self.app_ref.data["queue"]
                                       if x["id"] != qi["id"]]
        save_data(self.app_ref.data)
        show_toast(f"✅ Đã gán mã #{code} cho {qi['name']}")
        self.refresh()

    def _delete(self, qi):
        self.app_ref.data["queue"] = [x for x in self.app_ref.data["queue"]
                                       if x["id"] != qi["id"]]
        save_data(self.app_ref.data)
        self.refresh()


class StatsScreen(BaseScreen):
    def __init__(self, app_ref, **kw):
        super().__init__(app_ref, name="stats", **kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        hdr = BoxLayout(size_hint_y=None, height=dp(54), padding=dp(12))
        with hdr.canvas.before:
            Color(*WHITE); Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda *a, w=hdr: update_canvas_rect(w),
                 size=lambda *a, w=hdr: update_canvas_rect(w))
        hdr.add_widget(Label(text="📊 Thống kê", font_size=sp(18),
                             bold=True, color=DARK, halign="left",
                             text_size=(dp(300), None)))
        root.add_widget(hdr)

        self.scroll = ScrollView()
        self.content = BoxLayout(orientation="vertical", spacing=dp(10),
                                 padding=dp(12), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroll.add_widget(self.content)
        root.add_widget(self.scroll)
        self.add_widget(root)

    def refresh(self):
        self.content.clear_widgets()
        data = self.app_ref.data
        active = [c for c in data["customers"] if c["status"] != "archive"]
        rows = [
            ("👥 Tổng khách hoạt động",      len(active)),
            ("💅 Tổng lượt làm",              sum(c.get("visits",0) for c in active)),
            ("⭐ Khách VIP (≥10 lượt)",       sum(1 for c in active if c.get("visits",0)>=10)),
            ("🎁 Đủ ưu đãi (≥10 điểm)",      sum(1 for c in active if c.get("points",0)>=10)),
            ("🎂 Sinh nhật tháng này",         sum(1 for c in active if is_birthday_this_month(c.get("birthday")))),
            ("⏳ Hàng chờ",                   len(data["queue"])),
            ("📦 Lưu trữ",                    sum(1 for c in data["customers"] if c["status"]=="archive")),
        ]
        for label, val in rows:
            row = BoxLayout(size_hint_y=None, height=dp(52),
                            padding=[dp(12),dp(8),dp(12),dp(8)])
            with row.canvas.before:
                Color(*WHITE)
                RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(10)])
            row.bind(pos=lambda i,v,r=row: self._upd(r),
                     size=lambda i,v,r=row: self._upd(r))
            row.add_widget(Label(text=label, font_size=sp(14), color=DARK,
                                 halign="left", text_size=(dp(250),None)))
            row.add_widget(Label(text=str(val), font_size=sp(20),
                                 bold=True, color=PINK,
                                 size_hint=(None,1), width=dp(60),
                                 halign="right", text_size=(dp(60),None)))
            self.content.add_widget(row)

    def _upd(self, r):
        update_canvas_rect(r)


# ── Bottom Navigation ─────────────────────────────────────────────────────────
class BottomNav(BoxLayout):
    def __init__(self, sm, **kw):
        super().__init__(size_hint_y=None, height=dp(58),
                         padding=[0, dp(4), 0, dp(4)], **kw)
        self.sm = sm
        with self.canvas.before:
            Color(*WHITE)
            Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)
        self.btns = {}
        for key, icon, label in [
            ("customers","👥","Khách"),
            ("queue",    "⏳","Hàng chờ"),
            ("stats",    "📊","Thống kê"),
        ]:
            btn = BoxLayout(orientation="vertical", spacing=0)
            ico = Label(text=icon, font_size=sp(22), size_hint_y=None, height=dp(28))
            lbl = Label(text=label, font_size=sp(10), color=MUTED,
                        size_hint_y=None, height=dp(16))
            btn.add_widget(ico); btn.add_widget(lbl)
            btn.bind(on_touch_down=lambda touch, k=key, b=btn:
                     self._on_tap(touch, k, b) if b.collide_point(*touch.pos) else None)
            self.add_widget(btn)
            self.btns[key] = (ico, lbl)
        self._highlight("customers")

    def _upd(self, *a):
        update_canvas_rect(self)

    def _on_tap(self, touch, key, btn):
        self.sm.current = key
        self._highlight(key)

    def _highlight(self, active):
        for k, (ico, lbl) in self.btns.items():
            if k == active:
                ico.color = PINK; lbl.color = PINK
            else:
                ico.color = MUTED; lbl.color = MUTED


# ── Main App ──────────────────────────────────────────────────────────────────
class NailCRMApp(App):
    def build(self):
        self.title = "Nail CRM"
        self.data  = load_data()
        auto_archive(self.data)
        save_data(self.data)

        Window.clearcolor = BG

        root = BoxLayout(orientation="vertical", spacing=0)

        self.sm = ScreenManager(transition=SlideTransition(duration=0.2))
        self.screens = {
            "customers": CustomerScreen(self),
            "queue":     QueueScreen(self),
            "stats":     StatsScreen(self),
        }
        for s in self.screens.values():
            self.sm.add_widget(s)

        self.nav = BottomNav(self.sm)
        root.add_widget(self.sm)
        root.add_widget(self.nav)

        self.refresh_current()
        return root

    def refresh_current(self):
        for s in self.screens.values():
            s.refresh()

if __name__ == "__main__":
    NailCRMApp().run()
