from flask import Flask, request, render_template, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
import secrets
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Author(db.Model):
    author_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    books = db.relationship('Book', backref='author', cascade="all, delete-orphan")

class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('author.author_id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
@app.route('/home', methods=['GET'])
def home():
    title_filter = request.args.get('title', '')
    author_filter = request.args.get('author_id', '')
    query = Book.query
    if title_filter:
        query = query.filter(Book.title.like(f"%{title_filter}%"))
    if author_filter:
        query = query.filter_by(author_id=author_filter)
    books = query.all()
    authors = Author.query.all()
    return render_template('index.html', books=books, authors=authors, title_filter=title_filter, author_filter=author_filter)

@app.route('/manage_book', methods=['GET', 'POST'])
def manage_book():
    if request.method == 'POST':
        if 'add' in request.form:
            title = request.form['title']
            author_id = int(request.form['author_id'])
            new_book = Book(title=title, author_id=author_id)
            db.session.add(new_book)
            db.session.commit()
            flash("Book added successfully!")
        elif 'update' in request.form:
            book_id = request.form['book_id']
            book = Book.query.get(book_id)
            if book:
                book.title = request.form['title']
                book.author_id = int(request.form['author_id'])
                db.session.commit()
                flash("Book updated successfully!")
            else:
                flash("Book not found!")
        return redirect(url_for('home'))
    authors = Author.query.all()
    books = Book.query.all()
    return render_template('manage_book.html', authors=authors, books=books)

@app.route('/delete_book/<int:book_id>')
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash("Book deleted successfully!")
    return redirect(url_for('home'))

@app.route('/manage_author', methods=['GET', 'POST'])
def manage_author():
    if request.method == 'POST':
        if 'add' in request.form:
            name = request.form['name']
            existing_author = Author.query.filter_by(name=name).first()
            if existing_author:
                flash("Author already exists!")
            else:
                new_author = Author(name=name)
                db.session.add(new_author)
                db.session.commit()
                flash("Author added successfully!")
        elif 'delete' in request.form:
            author_id = request.form['author_id']
            author = Author.query.get(author_id)
            if author:
                db.session.delete(author)
                db.session.commit()
                flash("Author and their books deleted successfully!")
            else:
                flash("Author not found!")
        return redirect(url_for('home'))
    authors = Author.query.all()
    return render_template('manage_author.html', authors=authors)

@app.route('/delete_author/<int:author_id>')
def delete_author(author_id):
    author = Author.query.get_or_404(author_id)
    db.session.delete(author)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/export_books', methods=['GET'])
def export_books():
    books = Book.query.all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Book Title', 'Author'])
    for book in books:
        cw.writerow([book.title, book.author.name])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=books.csv"
    output.headers["Content-type"] = "text/csv"
    return output


if __name__ == '__main__':
    app.run(debug=True)
