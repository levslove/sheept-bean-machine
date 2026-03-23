"""
Bean Machine — A landing page for a coffee shop called Bean Machine
Built by Sheept 🐑💤 | Type: marketplace | Seed: 87b97ff83816
"""
import json, sqlite3, uuid, hashlib
from datetime import datetime, timezone
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Bean Machine", description="A landing page for a coffee shop called Bean Machine")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
DB = "/tmp/bean_machine_87b97f.db"

@contextmanager
def db():
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    try: yield conn.cursor(); conn.commit()
    finally: conn.close()

def uid(): return uuid.uuid4().hex[:12]
def now(): return datetime.now(timezone.utc).isoformat()
def hash_pw(pw: str) -> str: return hashlib.sha256(pw.encode()).hexdigest()

def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS auth_users (id TEXT PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, role TEXT DEFAULT 'user', created_at TEXT);
        CREATE TABLE IF NOT EXISTS feedback (id TEXT PRIMARY KEY, user_id TEXT, message TEXT, rating INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT, data JSON, user_id TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS listings (id TEXT PRIMARY KEY, seller_id TEXT, title TEXT NOT NULL, description TEXT, price REAL, category TEXT, status TEXT DEFAULT 'active', image_url TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, buyer_id TEXT, listing_id TEXT, quantity INTEGER DEFAULT 1, total REAL, status TEXT DEFAULT 'pending', created_at TEXT);
        CREATE TABLE IF NOT EXISTS sellers (id TEXT PRIMARY KEY, user_id TEXT, shop_name TEXT, bio TEXT, rating REAL DEFAULT 0, total_sales INTEGER DEFAULT 0, created_at TEXT);
        CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, user_id TEXT, item_id TEXT, rating INTEGER, comment TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS categories (id TEXT PRIMARY KEY, name TEXT UNIQUE, description TEXT, parent_id TEXT, sort_order INTEGER DEFAULT 0);
        """)
init()

def get_user(auth: Optional[str] = Header(None)):
    if not auth: raise HTTPException(401, "Missing Auth")
    with db() as c:
        c.execute("SELECT * FROM auth_users WHERE id=?", (auth.replace("Bearer ", ""),))
        u = c.fetchone()
        if not u: raise HTTPException(401, "Invalid token")
        return dict(u)

class RegisterReq(BaseModel): username: str; password: str
class LoginReq(BaseModel): username: str; password: str

@app.post("/register")
def register(r: RegisterReq):
    u = uid()
    with db() as c:
        try: c.execute("INSERT INTO auth_users VALUES (?,?,?,?,?)", (u, r.username, hash_pw(r.password), "user", now()))
        except sqlite3.IntegrityError: raise HTTPException(409, "Username taken")
    return {"user_id": u, "token": u}

@app.post("/login")
def login(r: LoginReq):
    with db() as c:
        c.execute("SELECT * FROM auth_users WHERE username=? AND password_hash=?", (r.username, hash_pw(r.password)))
        u = c.fetchone()
        if not u: raise HTTPException(401, "Invalid credentials")
    return {"user_id": u["id"], "token": u["id"], "username": u["username"]}

class ListingsReq(BaseModel):
    title: str
    price: float

class OrdersReq(BaseModel):
    listing_id: str
    quantity: int = 1

class SellersReq(BaseModel):
    shop_name: str

class ReviewsReq(BaseModel):
    item_id: str
    rating: int
    comment: Optional[str] = None

class CategoriesReq(BaseModel):
    name: str

@app.get("/listings")
def list_listings(limit: int = 50, offset: int = 0):
    with db() as c: c.execute("SELECT * FROM listings ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)); return [dict(r) for r in c.fetchall()]
@app.post("/listings")
def create_listings(r: ListingsReq, auth: Optional[str] = Header(None)):
    get_user(auth); rid = uid(); d = r.dict()
    cols, vals = ", ".join(["id"] + list(d.keys()) + ["created_at"]), [rid] + list(d.values()) + [now()]
    with db() as c: c.execute(f"INSERT INTO listings ({cols}) VALUES ({','.join(['?']*len(vals))})", vals)
    return {"id": rid}
@app.get("/listings/{id}")
def get_listings(id: str):
    with db() as c: c.execute("SELECT * FROM listings WHERE id=?", (id,)); row = c.fetchone()
    if not row: raise HTTPException(404, "Not found")
    return dict(row)
@app.delete("/listings/{id}")
def delete_listings(id: str, auth: Optional[str] = Header(None)):
    get_user(auth)
    with db() as c: c.execute("DELETE FROM listings WHERE id=?", (id,))
    return {"id": id, "deleted": True}
@app.get("/orders")
def list_orders(limit: int = 50, offset: int = 0):
    with db() as c: c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)); return [dict(r) for r in c.fetchall()]
@app.post("/orders")
def create_orders(r: OrdersReq, auth: Optional[str] = Header(None)):
    get_user(auth); rid = uid(); d = r.dict()
    cols, vals = ", ".join(["id"] + list(d.keys()) + ["created_at"]), [rid] + list(d.values()) + [now()]
    with db() as c: c.execute(f"INSERT INTO orders ({cols}) VALUES ({','.join(['?']*len(vals))})", vals)
    return {"id": rid}
@app.get("/orders/{id}")
def get_orders(id: str):
    with db() as c: c.execute("SELECT * FROM orders WHERE id=?", (id,)); row = c.fetchone()
    if not row: raise HTTPException(404, "Not found")
    return dict(row)
@app.delete("/orders/{id}")
def delete_orders(id: str, auth: Optional[str] = Header(None)):
    get_user(auth)
    with db() as c: c.execute("DELETE FROM orders WHERE id=?", (id,))
    return {"id": id, "deleted": True}
@app.get("/sellers")
def list_sellers(limit: int = 50, offset: int = 0):
    with db() as c: c.execute("SELECT * FROM sellers ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)); return [dict(r) for r in c.fetchall()]
@app.post("/sellers")
def create_sellers(r: SellersReq, auth: Optional[str] = Header(None)):
    get_user(auth); rid = uid(); d = r.dict()
    cols, vals = ", ".join(["id"] + list(d.keys()) + ["created_at"]), [rid] + list(d.values()) + [now()]
    with db() as c: c.execute(f"INSERT INTO sellers ({cols}) VALUES ({','.join(['?']*len(vals))})", vals)
    return {"id": rid}
@app.get("/sellers/{id}")
def get_sellers(id: str):
    with db() as c: c.execute("SELECT * FROM sellers WHERE id=?", (id,)); row = c.fetchone()
    if not row: raise HTTPException(404, "Not found")
    return dict(row)
@app.delete("/sellers/{id}")
def delete_sellers(id: str, auth: Optional[str] = Header(None)):
    get_user(auth)
    with db() as c: c.execute("DELETE FROM sellers WHERE id=?", (id,))
    return {"id": id, "deleted": True}
@app.get("/reviews")
def list_reviews(limit: int = 50, offset: int = 0):
    with db() as c: c.execute("SELECT * FROM reviews ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)); return [dict(r) for r in c.fetchall()]
@app.post("/reviews")
def create_reviews(r: ReviewsReq, auth: Optional[str] = Header(None)):
    get_user(auth); rid = uid(); d = r.dict()
    cols, vals = ", ".join(["id"] + list(d.keys()) + ["created_at"]), [rid] + list(d.values()) + [now()]
    with db() as c: c.execute(f"INSERT INTO reviews ({cols}) VALUES ({','.join(['?']*len(vals))})", vals)
    return {"id": rid}
@app.get("/reviews/{id}")
def get_reviews(id: str):
    with db() as c: c.execute("SELECT * FROM reviews WHERE id=?", (id,)); row = c.fetchone()
    if not row: raise HTTPException(404, "Not found")
    return dict(row)
@app.delete("/reviews/{id}")
def delete_reviews(id: str, auth: Optional[str] = Header(None)):
    get_user(auth)
    with db() as c: c.execute("DELETE FROM reviews WHERE id=?", (id,))
    return {"id": id, "deleted": True}
@app.get("/categories")
def list_categories(limit: int = 50, offset: int = 0):
    with db() as c: c.execute("SELECT * FROM categories ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)); return [dict(r) for r in c.fetchall()]
@app.post("/categories")
def create_categories(r: CategoriesReq, auth: Optional[str] = Header(None)):
    get_user(auth); rid = uid(); d = r.dict()
    cols, vals = ", ".join(["id"] + list(d.keys()) + ["created_at"]), [rid] + list(d.values()) + [now()]
    with db() as c: c.execute(f"INSERT INTO categories ({cols}) VALUES ({','.join(['?']*len(vals))})", vals)
    return {"id": rid}
@app.get("/categories/{id}")
def get_categories(id: str):
    with db() as c: c.execute("SELECT * FROM categories WHERE id=?", (id,)); row = c.fetchone()
    if not row: raise HTTPException(404, "Not found")
    return dict(row)
@app.delete("/categories/{id}")
def delete_categories(id: str, auth: Optional[str] = Header(None)):
    get_user(auth)
    with db() as c: c.execute("DELETE FROM categories WHERE id=?", (id,))
    return {"id": id, "deleted": True}

@app.post("/cart/add")
def add_to_cart(listing_id: str, qty: int = 1, auth: Optional[str] = Header(None)):
    u = get_user(auth)
    with db() as c: c.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?)", (uid(), u["id"], listing_id, qty, 0, "cart", now()))
    return {"status": "added to cart"}
@app.get("/cart")
def view_cart(auth: Optional[str] = Header(None)):
    u = get_user(auth)
    with db() as c: c.execute("SELECT * FROM orders WHERE buyer_id=? AND status='cart'", (u["id"],)); return [dict(r) for r in c.fetchall()]

class FeedbackReq(BaseModel): message: str; rating: Optional[int] = None

@app.post("/feedback")
def submit_feedback(r: FeedbackReq, auth: Optional[str] = Header(None)):
    user_id = None
    if auth:
        try: user_id = get_user(auth)["id"]
        except Exception: pass
    with db() as c: c.execute("INSERT INTO feedback VALUES (?,?,?,?,?)", (uid(), user_id, r.message, r.rating, now()))
    return {"message": "Thanks! 🐑"}

@app.get("/stats")
def stats():
    with db() as c:
        c.execute("SELECT COUNT(*) as cnt FROM auth_users"); users = c.fetchone()["cnt"]
    return {"total_users": users, "built_with": "Sheept 🐑"}

@app.get("/health")
def health(): return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
def home(): return FRONTEND_HTML


FRONTEND_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Bean Machine</title><script src="https://cdn.tailwindcss.com"></script>
<style>
:root { --pr:#faf5f0; --sc:#f97316; --ac:#e9aa05; --bg:#fffbf5; --tx:#1c1917; }
* { margin:0; padding:0; box-sizing:border-box; font-family:system-ui; }
body { background:var(--bg); color:var(--tx); }
.nav { display:flex; justify-content:space-between; padding:1rem 2rem; border-bottom:1px solid var(--pr); }
.hero { text-align:center; padding:4rem 2rem; } .hero h1 { color:var(--sc); font-size:3rem; }
.btn { padding:0.5rem 1rem; background:var(--ac); color:#fff; border:none; border-radius:8px; cursor:pointer; }
.section { padding:2rem; max-width:800px; margin:0 auto; } .card { border:1px solid var(--pr); padding:1rem; border-radius:8px; margin-bottom:1rem; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; }
input, textarea { width:100%; padding:0.5rem; margin-bottom:0.5rem; background:var(--bg); color:var(--tx); border:1px solid var(--pr); }
</style></head><body>
<nav class="nav"><div>🐑 Bean Machine</div><a href="#auth" style="color:var(--tx)">Sign In</a></nav>
<section class="hero"><h1>Bean Machine</h1><p>A landing page for a coffee shop called Bean Machine</p></section>
<section class="section" id="browse"><h2>🛍️ Browse</h2><div class="grid" id="listings-grid">Loading...</div></section>
<section class="section" id="auth"><h2>Join</h2><div class="card"><input id="user" placeholder="Username"><input id="pass" type="password" placeholder="Password"><button class="btn" onclick="auth('/register')">Register</button><button class="btn" onclick="auth('/login')">Login</button></div></section>
<footer style="text-align:center;padding:2rem;">Built with 🐑 Sheept</footer>
<script>
const API = window.location.origin; let TOKEN = localStorage.getItem('token');
async function api(path, opts = {}) {
    if(TOKEN) opts.headers = {...opts.headers, 'Authorization': 'Bearer '+TOKEN};
    opts.headers = {...opts.headers, 'Content-Type': 'application/json'};
    const r = await fetch(API+path, opts); if(!r.ok) throw new Error('Error'); return r.json();
}
async function auth(path) {
    try { const d = await api(path, {method:'POST', body:JSON.stringify({username:document.getElementById('user').value, password:document.getElementById('pass').value})}); TOKEN=d.token; localStorage.setItem('token',TOKEN); loadData(); alert('Success!'); } catch(e) { alert('Failed'); }
}
async function loadData() {try { const items = await api('/listings'); document.getElementById('listings-grid').innerHTML = items.map(l => `<div class="card"><h3>${l.title}</h3><p>$${l.price}</p><button class="btn" onclick="api('/cart/add?listing_id='+l.id, {method:'POST'})">Add</button></div>`).join('')||'No listings'; } catch(e) {}}
if(TOKEN) loadData();
</script></body></html>"""
