from flask import Flask, render_template_string, request, session, redirect, url_for, send_from_directory, flash
from datetime import datetime
import secrets
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

DATABASE = 'bazaro.db'
UPLOAD_FOLDER = 'product_images'
ALLOWED_EXTENSIONS = {'png', 'jpeg', 'jpg', 'gif', 'webp'}

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    #Create and return a database connection
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    #onceden yoktu foto columnu onu koymak icin
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("PRAGMA table_info(items)")
    columns = [column[1] for column in cur.fetchall()]
    
    if 'image_filename' not in columns:
        cur.execute('ALTER TABLE items ADD COLUMN image_filename TEXT DEFAULT "temp.jpg"')
        conn.commit()
        print("image_filename column added")
    
    # Add owner_user_id column to track which user added the product
    if 'owner_user_id' not in columns:
        cur.execute('ALTER TABLE items ADD COLUMN owner_user_id INTEGER')
        conn.commit()
        print("owner_user_id column added")
    
    cur.close()
    conn.close()

def get_current_user():
    #get the current user
    user_id = session.get('user_id')
    if user_id:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return dict(user) if user else None
    return None

#image location
@app.route('/product_images/<filename>')
def product_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def render_page(content, page_title='Bazaro'):
    current_user = get_current_user()
    cart = session.get('cart', [])
    
    nav_items = '<a href="/">Home</a><a href="/products">Products</a>'
    
    if current_user:
        cart_badge = f'<span class="cart-badge">{len(cart)}</span>' if len(cart) > 0 else ''
        nav_items += f'''
            <a href="/wallet">Wallet</a>
            <a href="/orders">Orders</a>
            <a href="/profile">Profile</a>
            <a href="/cart">Cart{cart_badge}</a>
            <span>Hello, {current_user['name']}</span>
            <a href="/logout" class="btn btn-danger" style="padding: 0.5rem 1rem; font-size: 0.875rem;">Logout</a>
        '''
    else:
        nav_items += '<a href="/login" class="btn btn-white">Login</a>'
    
    template = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bazaro - {page_title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(to bottom, #EBF4FF, #FFFFFF); min-height: 100vh; }}
        .header {{ background: linear-gradient(to right, #2563EB, #1E40AF); color: white; padding: 1rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 1000; }}
        .header-content {{ max-width: 1200px; margin: 0 auto; padding: 0 1rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }}
        .logo {{ display: flex; align-items: center; gap: 0.5rem; font-size: 1.5rem; font-weight: bold; }}
        .nav-links {{ display: flex; gap: 2rem; align-items: center; flex-wrap: wrap; }}
        .nav-links a {{ color: white; text-decoration: none; transition: opacity 0.3s; }}
        .nav-links a:hover {{ opacity: 0.8; }}
        .btn {{ padding: 0.5rem 1.5rem; border: none; border-radius: 0.5rem; cursor: pointer; font-size: 1rem; font-weight: 600; transition: all 0.3s; text-decoration: none; display: inline-block; }}
        .btn-primary {{ background: #2563EB; color: white; }}
        .btn-primary:hover {{ background: #1D4ED8; }}
        .btn-success {{ background: #059669; color: white; }}
        .btn-success:hover {{ background: #047857; }}
        .btn-danger {{ background: #DC2626; color: white; }}
        .btn-danger:hover {{ background: #B91C1C; }}
        .btn-white {{ background: #2563EB; color: #2563EB; padding: 0.5rem 1.5rem; }}
        .btn-white:hover {{ background: #F3F4F6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1rem; }}
        .card {{ background: white; border-radius: 1rem; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }}
        .grid {{ display: grid; gap: 1.5rem; }}
        .grid-2 {{ grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }}
        .forstock {{position: relative; text-align: center;}}
        .forstock .stock{{position: absolute; top: 43.75%; background: rgb(0, 0, 0); background: rgba(0, 0, 0, 0.5); color: #f1f1f1; width: 92.5%; padding: 157px; border-radius: 15px; text-align: center; left: 50.3%; transform: translate(-50%, -50%);}}
        .grid-3 {{ grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }}
        .grid-4 {{ grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }}
        .product-card {{ background: white; border-radius: 1rem; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.3s, box-shadow 0.3s; cursor: pointer; }}
        .product-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 16px rgba(0,0,0,0.15); }}
        .product-image {{ width: 100%; height: 200px; object-fit: cover; background: #F3F4F6; }}
        .product-info {{ padding: 1rem; }}
        .product-category {{ color: #2563EB; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.5rem; }}
        .product-name {{ font-size: 1.25rem; font-weight: bold; margin-bottom: 0.5rem; }}
        .product-price {{ font-size: 1.5rem; font-weight: bold; color: #2563EB; margin: 1rem 0; }}
        .form-group {{ margin-bottom: 1rem; }}
        .form-group label {{ display: block; margin-bottom: 0.5rem; font-weight: 500; }}
        .form-control {{ width: 100%; padding: 0.75rem; border: 1px solid #D1D5DB; border-radius: 0.5rem; font-size: 1rem; }}
        .form-control:focus {{ outline: none; border-color: #2563EB; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1); }}
        .hero {{ text-align: center; padding: 4rem 0; }}
        .hero h1 {{ font-size: 3rem; margin-bottom: 1rem; color: #1F2937; }}
        .hero p {{ font-size: 1.25rem; color: #6B7280; margin-bottom: 2rem; }}
        .cart-item {{ display: flex; align-items: center; gap: 1rem; padding: 1rem; background: white; border-radius: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 1rem; }}
        .cart-item-image {{ width: 80px; height: 80px; object-fit: cover; border-radius: 0.5rem; background: #F3F4F6; }}
        .cart-item-info {{ flex: 1; }}
        .quantity-controls {{ display: flex; align-items: center; gap: 0.5rem; }}
        .quantity-btn {{ width: 2rem; height: 2rem; border: none; background: #E5E7EB; border-radius: 0.25rem; cursor: pointer; font-weight: bold; }}
        .quantity-btn:hover {{ background: #D1D5DB; }}
        .alert {{ padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }}
        .alert-info {{ background: #DBEAFE; color: #1E40AF; }}
        .alert-success {{ background: #D1FAE5; color: #065F46; }}
        .alert-warning {{ background: #FEF3C7; color: #92400E; }}
        .wallet-card {{ background: linear-gradient(to right, #2563EB, #1E40AF); color: white; padding: 2rem; border-radius: 1rem; margin-bottom: 2rem; }}
        .wallet-balance {{ font-size: 3rem; font-weight: bold; margin-top: 0.5rem; }}
        .order-card {{ background: white; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 1rem; }}
        .status-badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; background: #D1FAE5; color: #065F46; }}
        .cart-badge {{ background: #DC2626; color: white; border-radius: 50%; width: 20px; height: 20px; display: inline-flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold; margin-left: 0.25rem; }}
        .search-bar {{ display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }}
        .search-bar input, .search-bar select {{ flex: 1; min-width: 200px; }}
        .detail-image {{ width: 100%; max-width: 500px; height: 400px; object-fit: cover; border-radius: 1rem; margin-bottom: 2rem; }}
        .seller-link {{ color: #2563EB; text-decoration: none; font-weight: 600; }}
        .seller-link:hover {{ text-decoration: underline; }}
        .seller-card {{ background: linear-gradient(to right, #F3F4F6, #E5E7EB); padding: 2rem; border-radius: 1rem; margin-bottom: 2rem; }}
        .rating {{ color: #F59E0B; font-size: 1.5rem; }}
        @media (max-width: 768px) {{
            .nav-links {{ gap: 1rem; font-size: 0.875rem; }}
            .hero h1 {{ font-size: 2rem; }}
            .grid-4 {{ grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">🛒 Bazaro</div>
            <div class="nav-links">{nav_items}</div>
        </div>
    </div>
    <div class="container">{content}</div>
    <script>
        setTimeout(() => {{
            const alerts = document.querySelectorAll('.alert');
            alerts.forEach(alert => {{
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }});
        }}, 3000);
    </script>
</body>
</html>
    '''
    return template

@app.route('/')
def home():
    content = '''
        <div class="hero">
            <h1>Welcome to Bazaro</h1>
            <p>Your Simple and Reliable Online Marketplace</p>
            <a href="/products" class="btn btn-primary">Start Shopping</a>
        </div>
        
        <div class="grid grid-3">
            <div class="card" style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📦</div>
                <h3 style="margin-bottom: 0.5rem;">Wide Selection</h3>
                <p style="color: #6B7280;">Browse through various categories and find what you need</p>
            </div>
            <div class="card" style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💳</div>
                <h3 style="margin-bottom: 0.5rem;">Digital Wallet</h3>
                <p style="color: #6B7280;">Easy and secure payment with our integrated wallet system</p>
            </div>
            <div class="card" style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">👤</div>
                <h3 style="margin-bottom: 0.5rem;">User Friendly</h3>
                <p style="color: #6B7280;">Simple interface designed for easy navigation</p>
            </div>
        </div>
    '''
    return render_page(content, 'Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            session['user_id'] = user['user_id']
            return redirect('/products')
        else:
            return redirect('/login?error=1')
    
    error = request.args.get('error')
    error_msg = '<div class="alert alert-warning">Invalid credentials. Please try again.</div>' if error else ''
    
    content = f'''
        {error_msg}
        
        <div class="grid grid-2">
            <div class="card">
                <h2 style="margin-bottom: 1.5rem;">Login</h2>
                <form method="POST" action="/login">
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" class="form-control" placeholder="kekik@peynirlitavaboregi.com" required>
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" class="form-control" placeholder="Enter password" required>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Login</button>
                </form>
                <p style="margin-top: 1rem; color: #6B7280; font-size: 0.875rem;">
                    Demo: kekik@peynirlitavaboregi.com / pass
                </p>
            </div>
            
            <div class="card">
                <h2 style="margin-bottom: 1.5rem;">Register</h2>
                <form method="POST" action="/register">
                    <div class="form-group">
                        <label>Name</label>
                        <input type="text" name="name" class="form-control" placeholder="John Doe" required>
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" class="form-control" placeholder="john@example.com" required>
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" class="form-control" placeholder="Create password" required>
                    </div>
                    <button type="submit" class="btn btn-success" style="width: 100%;">Register</button>
                </form>
            </div>
        </div>
    '''
    return render_page(content, 'Login')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO users (name, email, password, wallet_balance) VALUES (?, ?, ?, ?)',
            (name, email, password, 0.0)
        )
        conn.commit()
        user_id = cur.lastrowid
        session['user_id'] = user_id
    except sqlite3.IntegrityError:
        return redirect('/login?error=2')
    finally:
        cur.close()
        conn.close()
    
    return redirect('/products')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/products')
def products():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = 'SELECT * FROM items WHERE 1=1'
    params = []
    
    if search:
        query += ' AND (name LIKE ? OR description LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    if category:
        query += ' AND category_id = ?'
        params.append(int(category))
    
    cur.execute(query, params)
    items = cur.fetchall()
    
    cur.execute('SELECT * FROM categories')
    categories = cur.fetchall()
    
    cur.close()
    conn.close()
    
    products_html = ''
    for item in items:
        cat = next((c for c in categories if c['category_id'] == item['category_id']), None)
        image_url = f'/product_images/{item["image_filename"]}'
        
        products_html += f'''
            <div class="product-card" onclick="window.location.href='/item/{item['item_id']}'">
                <img src="{image_url}" alt="{item['name']}" class="product-image" onerror="this.src='/product_images/temp.jpg'">
                <div class="product-info">
                    <div class="product-category">{cat['name'] if cat else ''}</div>
                    <div class="product-name">{item['name']}</div>
                    <p style="color: #6B7280; font-size: 0.875rem; margin-bottom: 0.5rem;">{item['description'][:50]}...</p>
                    <div class="product-price">${item['price']:.2f}</div>
                    <div style="margin-top: 0.5rem; color: #6B7280; font-size: 0.75rem;">Stock: {item['quantity']}</div>
                </div>
            </div>
        '''
    
    categories_options = ''.join([f'<option value="{c["category_id"]}">{c["name"]}</option>' for c in categories])
    
    current_user = get_current_user()
    add_product_btn = '<a href="/add-product" class="btn btn-success" style="margin-bottom: 1.5rem;">+ Add New Product</a>' if current_user else ''
    
    content = f'''
        <h2 style="margin-bottom: 1.5rem;">Products</h2>
        
        <div class="card">
            <form method="GET" action="/products" class="search-bar">
                <input type="text" name="search" class="form-control" placeholder="Search products..." value="{search}">
                <select name="category" class="form-control">
                    <option value="">All Categories</option>
                    {categories_options}
                </select>
                <button type="submit" class="btn btn-primary">Search</button>
            </form>
        </div>
        
        {add_product_btn}
        
        <div class="grid grid-4">
            {products_html if products_html else '<p>No products found</p>'}
        </div>
    '''
    
    return render_page(content, 'Products')

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM items WHERE item_id = ?', (item_id,))
    item = cur.fetchone()
    
    if not item:
        cur.close()
        conn.close()
        return redirect('/products')
    
    cur.execute('SELECT * FROM categories WHERE category_id = ?', (item['category_id'],))
    category = cur.fetchone()
    is_user = False
    if item['seller_id'] != None:
        cur.execute('SELECT * FROM sellers WHERE seller_id = ?', (item['seller_id'],))
        seller = cur.fetchone()
    else:
        is_user = True
        cur.execute('SELECT * FROM users WHERE user_id = ?', (item['owner_user_id'],))
        seller = cur.fetchone()
    
    cur.close()
    conn.close()

    error = request.args.get('error')

    if item["quantity"] == 0:
        out_of_stock = """<div class="stock"><h1>Out of Stock</h1></div>"""
    else:
        out_of_stock = """"""
    
    if error == "1":
        print(error)
        print("hata1")
        error_msg = '<div class="alert alert-warning">Item out of stock.</div>'
        #image_url = '/product_images/outofstock.jpg'
    elif error == "2":
        print(error)
        print("hata2")
        error_msg = '<div class="alert alert-warning">cant add more.</div>'
        #image_url = f'/product_images/{item["image_filename"]}'
    else:
        print("hata yok")
        print(error)
        error_msg = ""
        #image_url = f'/product_images/{item["image_filename"]}'
    
    image_url = f'/product_images/{item["image_filename"]}'
    
    content = f'''
        {error_msg}
        <div class="card">
            <a href="/products" style="color: #2563EB; text-decoration: none; display: inline-block; margin-bottom: 1rem;">← Back to Products</a>
            
            <div class="grid grid-2">
                <div class="forstock">
                    <img src="{image_url}" alt="{item['name']}" class="detail-image" onerror="this.src='/product_images/temp.jpg'">
                    {out_of_stock}
                </div>
                
                <div>
                    <div class="product-category">{category['name'] if category else 'Uncategorized'}</div>
                    <h1 style="font-size: 2.5rem; margin-bottom: 1rem; color: #1F2937;">{item['name']}</h1>
                    <div class="product-price" style="font-size: 2rem; margin-bottom: 1.5rem;">${item['price']:.2f}</div>
                    
                    <div style="background: #F3F4F6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1.5rem;">
                        <p style="margin-bottom: 0.5rem;"><strong>Stock Available:</strong> {item['quantity']} units</p>
                        <p style="margin-bottom: 0.5rem;"><strong>Seller:</strong> <a href="/seller/{seller['user_id'] if is_user else seller['seller_id']}?isuser={"1" if is_user else "0"}" class="seller-link">{seller['name'] if is_user else seller['seller_name']}</a></p>
                        <p style="margin-bottom: 0;"><strong>Rating:</strong> <span class="rating">{"not rated" if is_user else '⭐' * int(seller['rating'])}</span> ({0 if is_user else seller['rating']:.1f})</p>
                    </div>
                    
                    <h3 style="margin-bottom: 1rem;">Description</h3>
                    <p style="color: #4B5563; line-height: 1.6; margin-bottom: 2rem;">{item['description']}</p>
                    
                    <form method="POST" action="/add-to-cart/{item['item_id']}">
                        <button type="submit" class="btn btn-success" style="width: 100%; padding: 1rem; font-size: 1.125rem;">
                            Add to Cart
                        </button>
                    </form>
                </div>
            </div>
        </div>
    '''
    
    return render_page(content, item['name'])

@app.route('/seller/<int:seller_id>')
def seller_detail(seller_id):
    conn = get_db_connection()
    cur = conn.cursor()
    is_user = True if request.args.get('isuser') == "1" else False

    if is_user:
        cur.execute('SELECT * FROM users WHERE user_id = ?', (seller_id,))
        seller = cur.fetchone()
    else:
        cur.execute('SELECT * FROM sellers WHERE seller_id = ?', (seller_id,))
        seller = cur.fetchone()

    if not seller:
        cur.close()
        conn.close()
        return redirect('/products')

    
    cur.execute('SELECT * FROM items WHERE owner_user_id = ?', (seller_id,)) if is_user else cur.execute('SELECT * FROM items WHERE seller_id = ?', (seller_id,))
    items = cur.fetchall()
    
    cur.close()
    conn.close()
    
    products_html = ''
    for item in items:
        image_url = f'/product_images/{item["image_filename"]}'
        products_html += f'''
            <div class="product-card" onclick="window.location.href='/item/{item['item_id']}'">
                <img src="{image_url}" alt="{item['name']}" class="product-image" onerror="this.src='/product_images/temp.jpg'">
                <div class="product-info">
                    <div class="product-name">{item['name']}</div>
                    <p style="color: #6B7280; font-size: 0.875rem; margin-bottom: 0.5rem;">{item['description'][:50]}...</p>
                    <div class="product-price">${item['price']:.2f}</div>
                </div>
            </div>
        '''
    
    content = f'''
        <a href="/products" style="color: #2563EB; text-decoration: none; display: inline-block; margin-bottom: 1rem;">← Back to Products</a>
        
        <div class="seller-card">
            <div style="display: flex; align-items: center; gap: 2rem;">
                <div style="width: 100px; height: 100px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 2.5rem; font-weight: bold;">
                    {seller["name"][0] if is_user else seller['seller_name'][0]}
                </div>
                <div style="flex: 1;">
                    <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem; color: #1F2937;">{seller['name'] if is_user else seller['seller_name']}</h1>
                    <div class="rating" style="margin-bottom: 1rem;">{"not rated" if is_user else '⭐' * int(seller['rating'])} {0 if is_user else seller['rating']:.1f}</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2 style="margin-bottom: 1.5rem;">Seller Information</h2>
            <div class="grid grid-2">
                <div>
                    <p style="margin-bottom: 1rem;"><strong>Email:</strong> {seller['email']}</p>
                    <p style="margin-bottom: 1rem;"><strong>Phone:</strong> {"users phone number is private" if is_user else seller['phone_number']}</p>
                </div>
                <div>
                    <p style="margin-bottom: 1rem;"><strong>Address:</strong> {"users address is private" if is_user else seller['address']}</p>
                    <p style="margin-bottom: 1rem;"><strong>Products:</strong> {len(items)} items</p>
                </div>
            </div>
        </div>
        
        <h2 style="margin: 2rem 0 1.5rem 0;">Products from {seller['name'] if is_user else seller['seller_name']}</h2>
        <div class="grid grid-4">
            {products_html if products_html else '<p>No products available</p>'}
        </div>
    '''
    
    return render_page(content, seller['name'] if is_user else seller['seller_name'])

@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if not get_current_user():
        return redirect('/login')
    
    if request.method == 'POST':
        # Handle file upload
        image_filename = 'temp.jpg'
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                import time
                filename = f"{int(time.time())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename
        
        current_user = get_current_user()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO items (name, description, price, category_id, seller_id, quantity, image_filename, owner_user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (
                request.form.get('name'),
                request.form.get('description'),
                float(request.form.get('price')),
                int(request.form.get('category_id')),
                None,
                int(request.form.get('quantity')),
                image_filename,
                current_user['user_id']
            )
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/products')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM categories')
    categories = cur.fetchall()
    cur.close()
    conn.close()
    
    categories_options = ''.join([f'<option value="{c["category_id"]}">{c["name"]}</option>' for c in categories])
    
    content = f'''
        <div style="max-width: 600px; margin: 0 auto;">
            <div class="card">
                <h2 style="margin-bottom: 1.5rem;">Add New Product</h2>
                <form method="POST" enctype="multipart/form-data">
                    <div class="form-group">
                        <label>Product Name *</label>
                        <input type="text" name="name" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea name="description" class="form-control" rows="3"></textarea>
                    </div>
                    <div class="form-group">
                        <label>Product Image</label>
                        <input type="file" name="product_image" class="form-control" accept="image/*">
                        <small style="color: #6B7280;">Accepted formats: jpeg, PNG, GIF</small>
                    </div>
                    <div class="grid grid-2">
                        <div class="form-group">
                            <label>Price ($) *</label>
                            <input type="number" step="0.01" name="price" class="form-control" required>
                        </div>
                        <div class="form-group">
                            <label>Quantity *</label>
                            <input type="number" name="quantity" class="form-control" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <select name="category_id" class="form-control">
                            {categories_options}
                        </select>
                    </div>
                    <div style="display: flex; gap: 1rem;">
                        <button type="submit" class="btn btn-success" style="flex: 1;">Add Product</button>
                        <a href="/products" class="btn" style="flex: 1; background: #E5E7EB; text-align: center; line-height: 2.5;">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    '''
    
    return render_page(content, 'Add Product')

@app.route('/delete-product/<int:item_id>', methods=['POST'])
def delete_product(item_id):
    current_user = get_current_user()
    if not current_user:
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if the user owns this product
    cur.execute('SELECT * FROM items WHERE item_id = ? AND owner_user_id = ?', (item_id, current_user['user_id']))
    item = cur.fetchone()
    
    if item:
        # Delete the product image file if it exists and is not the default
        if item['image_filename'] and item['image_filename'] != 'temp.jpg':
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], item['image_filename'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Delete the product from database
        cur.execute('DELETE FROM items WHERE item_id = ?', (item_id,))
        conn.commit()
    
    cur.close()
    conn.close()
    
    return redirect('/profile')

@app.route('/add-to-cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    if not get_current_user():
        return redirect('/login')
    
    cart = session.get('cart', [])
    
    existing = next((c for c in cart if c['item_id'] == item_id), None)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT quantity FROM items WHERE item_id = ?', (item_id,))
    maxquantity = cur.fetchone()[0]

    if maxquantity != 0:   
        if existing:
            if existing['quantity'] < maxquantity:
                existing['quantity'] += 1
            else:
                return redirect(f'/item/{item_id}?error=2')
        else:
            cart.append({'item_id': item_id, 'quantity': 1})
    else:
        return redirect(f'/item/{item_id}?error=1')
    
    session['cart'] = cart
    return redirect(request.referrer or '/products')

@app.route('/cart')
def cart():
    if not get_current_user():
        return redirect('/login')
    
    current_user = get_current_user()
    cart = session.get('cart', [])
    
    if not cart:
        content = '''
            <div class="card" style="text-align: center; padding: 4rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🛒</div>
                <h2 style="margin-bottom: 1rem;">Your cart is empty</h2>
                <a href="/products" class="btn btn-primary">Continue Shopping</a>
            </div>
        '''
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cart_items_html = ''
        total = 0
        
        for cart_item in cart:
            cur.execute('SELECT * FROM items WHERE item_id = ?', (cart_item['item_id'],))
            item = cur.fetchone()
            
            if item:
                subtotal = item['price'] * cart_item['quantity']
                total += subtotal
                image_url = f'/product_images/{item["image_filename"]}'
                
                cart_items_html += f'''
                    <div class="cart-item">
                        <img src="{image_url}" alt="{item['name']}" class="cart-item-image" onerror="this.src='/product_images/temp.jpg'">
                        <div class="cart-item-info">
                            <h3>{item['name']}</h3>
                            <p style="color: #6B7280; font-size: 0.875rem;">{item['description']}</p>
                            <p style="color: #2563EB; font-weight: bold; margin-top: 0.5rem;">${item['price']:.2f}</p>
                        </div>
                        <div class="quantity-controls">
                            <form method="POST" action="/update-cart/{item['item_id']}/decrease" style="display: inline;">
                                <button type="submit" class="quantity-btn">−</button>
                            </form>
                            <span style="min-width: 2rem; text-align: center; font-weight: bold;">{cart_item['quantity']}</span>
                            <form method="POST" action="/update-cart/{item['item_id']}/increase" style="display: inline;">
                                <button type="submit" class="quantity-btn">+</button>
                            </form>
                        </div>
                        <form method="POST" action="/remove-from-cart/{item['item_id']}">
                            <button type="submit" class="btn btn-danger">Remove</button>
                        </form>
                    </div>
                '''
        
        cur.close()
        conn.close()
        
        error = request.args.get('error')
        if error == "1":
            print(error)
            print("hata1")
            error_msg = '<div class="alert alert-warning">cant add more.</div>'
        else:
            error_msg = ""
        
        content = f'''
            {error_msg}
            <h2 style="margin-bottom: 1.5rem;">Shopping Cart</h2>
            
            <div class="grid" style="grid-template-columns: 2fr 1fr;">
                <div>
                    {cart_items_html}
                </div>
                
                <div>
                    <div class="card" style="position: sticky; top: 6rem;">
                        <h3 style="margin-bottom: 1rem;">Order Summary</h3>
                        <div style="border-top: 1px solid #E5E7EB; padding-top: 1rem; margin-top: 1rem;">
                            <div style="display: flex; justify-content: space-between; font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">
                                <span>Total:</span>
                                <span style="color: #2563EB;">${total:.2f}</span>
                            </div>
                        </div>
                        <div class="alert alert-info">
                            <p style="margin: 0; font-size: 0.875rem;">Wallet Balance:</p>
                            <p style="margin: 0; font-size: 1.25rem; font-weight: bold; color: #2563EB;">${current_user['wallet_balance']:.2f}</p>
                        </div>
                        <form method="POST" action="/checkout">
                            <button type="submit" class="btn btn-success" style="width: 100%;">Complete Purchase</button>
                        </form>
                    </div>
                </div>
            </div>
        '''
    
    return render_page(content, 'Cart')

@app.route('/update-cart/<int:item_id>/<action>', methods=['POST'])
def update_cart(item_id, action):
    cart = session.get('cart', [])
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT quantity FROM items WHERE item_id = ?', (item_id,))
    maxquantity = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    item_in_cart = next((c for c in cart if c['item_id'] == item_id), None)
    
    if item_in_cart:
        if action == 'increase':
            if item_in_cart['quantity'] < maxquantity:
                item_in_cart['quantity'] += 1
            else:
                session['cart'] = cart
                return redirect('/cart?error=1')
        elif action == 'decrease':
            item_in_cart['quantity'] -= 1
            if item_in_cart['quantity'] <= 0:
                cart = [c for c in cart if c['item_id'] != item_id]
    
    session['cart'] = cart
    return redirect('/cart')

@app.route('/remove-from-cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    cart = session.get('cart', [])
    cart = [c for c in cart if c['item_id'] != item_id]
    session['cart'] = cart
    return redirect('/cart')

@app.route('/checkout', methods=['POST'])
def checkout():
    current_user = get_current_user()
    if not current_user:
        return redirect('/login')
    
    cart = session.get('cart', [])
    if not cart:
        return redirect('/cart')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    total = 0

    for cart_item in cart:
        cur.execute(
        'SELECT price FROM items WHERE item_id = ?',
        (cart_item['item_id'],))
        item = cur.fetchone()

        if not item:
            continue

        price = item['price']
        subtotal = price * cart_item['quantity']
        total += subtotal

        cur.execute('UPDATE items SET quantity = quantity - ? WHERE item_id = ?',(cart_item['quantity'], cart_item['item_id']))

    
    if current_user['wallet_balance'] < total:
        cur.close()
        conn.close()
        return redirect('/wallet?error=insufficient')
    
    cur.execute(
        'INSERT INTO orders (buyer_id, total_price) VALUES (?, ?)',
        (current_user['user_id'], total)
    )
    order_id = cur.lastrowid
    
    for cart_item in cart:
        cur.execute('SELECT price FROM items WHERE item_id = ?', (cart_item['item_id'],))
        item = cur.fetchone()
        if item:
            cur.execute(
                'INSERT INTO order_items (order_id, item_id, quantity, price) VALUES (?, ?, ?, ?)',
                (order_id, cart_item['item_id'], cart_item['quantity'], item['price'])
            )
    
    cur.execute(
        'INSERT INTO payments (order_id, payment_status, payment_method) VALUES (?, ?, ?)',
        (order_id, 'completed', 'wallet')
    )
    
    cur.execute(
        'UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ?',
        (total, current_user['user_id'])
    )
    
    conn.commit()
    cur.close()
    conn.close()
    
    session['cart'] = []
    return redirect('/orders?success=1')

@app.route('/wallet')
def wallet():
    current_user = get_current_user()
    if not current_user:
        return redirect('/login')
    
    error = request.args.get('error')
    success = request.args.get('success')
    
    alerts = ''
    if error == 'insufficient':
        alerts = '<div class="alert alert-warning">Insufficient wallet balance. Please add funds.</div>'
    if success:
        alerts = '<div class="alert alert-success">Funds added successfully!</div>'
    
    content = f'''
        {alerts}
        
        <h2 style="margin-bottom: 1.5rem;">Digital Wallet</h2>
        
        <div class="wallet-card">
            <p style="font-size: 0.875rem; margin-bottom: 0.5rem;">Current Balance</p>
            <div class="wallet-balance">${current_user['wallet_balance']:.2f}</div>
        </div>
        
        <div style="max-width: 600px; margin: 0 auto;">
            <div class="card">
                <h3 style="margin-bottom: 1.5rem;">Add Funds</h3>
                <form method="POST" action="/add-funds">
                    <div class="form-group">
                        <label>Amount ($)</label>
                        <input type="number" step="0.01" name="amount" class="form-control" placeholder="Enter amount" required>
                    </div>
                    <button type="submit" class="btn btn-success" style="width: 100%;">Add Funds</button>
                </form>
            </div>
        </div>
    '''
    
    return render_page(content, 'Wallet')

@app.route('/add-funds', methods=['POST'])
def add_funds():
    current_user = get_current_user()
    if not current_user:
        return redirect('/login')
    
    amount = float(request.form.get('amount', 0))
    if amount > 0:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id = ?',
            (amount, current_user['user_id'])
        )
        conn.commit()
        cur.close()
        conn.close()
    
    return redirect('/wallet?success=1')

@app.route('/orders')
def orders():
    current_user = get_current_user()
    if not current_user:
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM orders WHERE buyer_id = ? ORDER BY order_date DESC', (current_user['user_id'],))
    user_orders = cur.fetchall()
    
    success = request.args.get('success')
    alerts = '<div class="alert alert-success">Order placed successfully!</div>' if success else ''
    
    if not user_orders:
        content = f'''
            {alerts}
            <div class="card" style="text-align: center; padding: 4rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">📦</div>
                <h2 style="margin-bottom: 1rem;">No orders yet</h2>
                <a href="/products" class="btn btn-primary">Start Shopping</a>
            </div>
        '''
    else:
        orders_html = ''
        for order in user_orders:
            cur.execute('SELECT * FROM payments WHERE order_id = ?', (order['order_id'],))
            payment = cur.fetchone()
            
            cur.execute(
                '''SELECT oi.*, i.name FROM order_items oi 
                   JOIN items i ON oi.item_id = i.item_id 
                   WHERE oi.order_id = ?''',
                (order['order_id'],)
            )
            order_items = cur.fetchall()
            
            items_html = ''
            for order_item in order_items:
                items_html += f'''
                    <div style="display: flex; justify-content: space-between; font-size: 0.875rem; margin-bottom: 0.5rem;">
                        <span>{order_item['name']} x {order_item['quantity']}</span>
                        <span style="font-weight: 600;">${(order_item['price'] * order_item['quantity']):.2f}</span>
                    </div>
                '''
            
            order_date = datetime.fromisoformat(order['order_date']).strftime('%B %d, %Y|%H:%M:%S') if isinstance(order['order_date'], str) else order['order_date'].strftime('%B %d, %Y|%H:%M:%S')
            
            orders_html += f'''
                <div class="order-card">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                        <div>
                            <h3 style="margin-bottom: 0.25rem;">Order #{order['order_id']}</h3>
                            <p style="color: #6B7280; font-size: 0.875rem;">{order_date}</p>
                        </div>
                        <div style="text-align: right;">
                            <p style="font-size: 1.5rem; font-weight: bold; color: #2563EB; margin-bottom: 0.5rem;">${order['total_price']:.2f}</p>
                            <span class="status-badge">{payment['payment_status'] if payment else 'Pending'}</span>
                        </div>
                    </div>
                    <div style="border-top: 1px solid #E5E7EB; padding-top: 1rem;">
                        <h4 style="font-weight: 600; margin-bottom: 0.5rem;">Items:</h4>
                        {items_html}
                    </div>
                </div>
            '''
        
        content = f'''
            {alerts}
            <h2 style="margin-bottom: 1.5rem;">My Orders</h2>
            {orders_html}
        '''
    
    cur.close()
    conn.close()
    
    return render_page(content, 'Orders')

@app.route('/profile')
def profile():
    current_user = get_current_user()
    if not current_user:
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM orders WHERE buyer_id = ?', (current_user['user_id'],))
    user_orders = cur.fetchall()
    total_spent = sum(o['total_price'] for o in user_orders)
    
    # Get products added by this user
    cur.execute('SELECT * FROM items WHERE owner_user_id = ?', (current_user['user_id'],))
    my_products = cur.fetchall()
    
    cur.execute('SELECT * FROM categories')
    categories = cur.fetchall()
    
    cur.close()
    conn.close()
    
    cart = session.get('cart', [])
    
    # Generate HTML for user's products
    my_products_html = ''
    for item in my_products:
        cat = next((c for c in categories if c['category_id'] == item['category_id']), None)
        image_url = f'/product_images/{item["image_filename"]}'
        
        my_products_html += f'''
            <div class="product-card" style="position: relative;">
                <div onclick="window.location.href='/item/{item['item_id']}'" style="cursor: pointer;">
                    <img src="{image_url}" alt="{item['name']}" class="product-image" onerror="this.src='/product_images/temp.jpg'">
                    <div class="product-info">
                        <div class="product-category">{cat['name'] if cat else ''}</div>
                        <div class="product-name">{item['name']}</div>
                        <p style="color: #6B7280; font-size: 0.875rem; margin-bottom: 0.5rem;">{item['description'][:50] if item['description'] else ''}...</p>
                        <div class="product-price">${item['price']:.2f}</div>
                        <div style="margin-top: 0.5rem; color: #6B7280; font-size: 0.75rem;">Stock: {item['quantity']}</div>
                    </div>
                </div>
                <form method="POST" action="/delete-product/{item['item_id']}" style="position: absolute; top: 0.5rem; right: 0.5rem;" onclick="event.stopPropagation();" onsubmit="return confirm('Bu ürünü silmek istediğinize emin misiniz?');">
                    <button type="submit" class="btn btn-danger" style="padding: 0.5rem 0.75rem; font-size: 0.875rem; border-radius: 0.375rem; background: #DC2626; color: white; border: none; cursor: pointer; display: flex; align-items: center; gap: 0.25rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        🗑️ Sil
                    </button>
                </form>
            </div>
        '''
    
    # My products section
    my_products_section = ''
    if my_products:
        my_products_section = f'''
            <div style="margin-top: 2rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="font-weight: bold;">🛍️ My Products ({len(my_products)})</h3>
                    <a href="/add-product" class="btn btn-success" style="font-size: 0.875rem;">+ Add New Product</a>
                </div>
                <div class="grid grid-3">
                    {my_products_html}
                </div>
            </div>
        '''
    else:
        my_products_section = f'''
            <div style="margin-top: 2rem;">
                <h3 style="font-weight: bold; margin-bottom: 1rem;">🛍️ My Products</h3>
                <div class="card" style="text-align: center; padding: 2rem;">
                    <p style="color: #6B7280; margin-bottom: 1rem;">You haven't added any products yet.</p>
                    <a href="/add-product" class="btn btn-success">+ Add Your First Product</a>
                </div>
            </div>
        '''
    
    content = f'''
        <div style="max-width: 1000px; margin: 0 auto;">
            <h2 style="margin-bottom: 1.5rem;">My Profile</h2>
            
            <div class="card">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                    <div style="width: 80px; height: 80px; background: #2563EB; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: bold;">
                        {current_user['name'][0].upper()}
                    </div>
                    <div>
                        <h3 style="margin-bottom: 0.25rem;">{current_user['name']}</h3>
                        <p style="color: #6B7280;">{current_user['email']}</p>
                    </div>
                </div>
                
                <div style="border-top: 1px solid #E5E7EB; padding-top: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                        <span style="color: #6B7280;">User ID:</span>
                        <span style="font-weight: 600;">{current_user['user_id']}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                        <span style="color: #6B7280;">Wallet Balance:</span>
                        <span style="font-weight: 600; color: #2563EB;">${current_user['wallet_balance']:.2f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #6B7280;">Total Orders:</span>
                        <span style="font-weight: 600;">{len(user_orders)}</span>
                    </div>
                </div>
                
                <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #E5E7EB;">
                    <h4 style="font-weight: bold; margin-bottom: 1rem;">Account Statistics</h4>
                    <div class="grid grid-3">
                        <div style="background: #DBEAFE; padding: 1rem; border-radius: 0.5rem;">
                            <p style="color: #6B7280; font-size: 0.875rem; margin-bottom: 0.25rem;">Items in Cart</p>
                            <p style="font-size: 1.5rem; font-weight: bold; color: #2563EB;">{len(cart)}</p>
                        </div>
                        <div style="background: #D1FAE5; padding: 1rem; border-radius: 0.5rem;">
                            <p style="color: #6B7280; font-size: 0.875rem; margin-bottom: 0.25rem;">Total Spent</p>
                            <p style="font-size: 1.5rem; font-weight: bold; color: #059669;">${total_spent:.2f}</p>
                        </div>
                        <div style="background: #FEF3C7; padding: 1rem; border-radius: 0.5rem;">
                            <p style="color: #6B7280; font-size: 0.875rem; margin-bottom: 0.25rem;">My Products</p>
                            <p style="font-size: 1.5rem; font-weight: bold; color: #D97706;">{len(my_products)}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            {my_products_section}
        </div>
    '''
    
    return render_page(content, 'Profile')

if __name__ == '__main__':
    init_database()
    print("\n" + "="*60)
    print("🛒  Starting Bazaro Marketplace with SQLite...")
    print("="*60)
    print("\n📍 Open your browser and go to: http://127.0.0.1:5000")
    print("\n🔐 Demo credentials:")
    print("   Email: kekik@peynirlitavaboregi.com")
    print("   Password: pass")
    print("   Email: bibi@bibi")
    print("   Password: bibi")
    print("\n💾 Database: bazaro.db (SQLite file)")
    print("\n" + "="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
