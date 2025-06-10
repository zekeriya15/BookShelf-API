from flask import Flask, jsonify, request, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv

# create an instance
app = Flask(__name__)
CORS(app)

# db config
DB_USER = os.getenv('MYSQL_USER')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD')
DB_HOST = os.getenv('MYSQL_HOST')
DB_PORT = os.getenv('MYSQL_PORT', 3306) # Provide a default for port
DB_NAME = os.getenv('MYSQL_DB')

# if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
#     raise ValueError("Missing one or more database environment variables. Check your .env file.")

# create database
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# create database object
db = SQLAlchemy(app)

# make sure uploads folder exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# create model
class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_email = db.Column(db.String(225), nullable=False)
    image_path = db.Column(db.String(225), nullable=True)
    title = db.Column(db.String(225), nullable=False)
    author = db.Column(db.String(225), nullable=False)
    genre = db.Column(db.String(225), nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    current_page = db.Column(db.Integer, nullable=False)
    date_modified = db.Column(db.DateTime , nullable=False)
    is_deleted = db.Column(db.Boolean, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'imageUrl': f'{request.host_url.rstrip('/')}/{self.image_path}' if self.image_path else None,
            'title': self.title,
            'author': self.author,
            'genre': self.genre,
            'pages': self.pages,
            'currentPage': self.current_page,
            'dateModified': self.date_modified.isoformat(),
            'isDeleted': self.is_deleted
        }
    
# create db
with app.app_context():
    db.create_all()


# utility function
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
def get_user_email_or_401():
    email = request.headers.get('Authorization')
    if not email:
        return None, {'status': 'error', 
                      'message': 'You need to login first'}, 401
    return email, None, None

def get_reading_or_404(reading_id, email):
    reading = Reading.query.filter_by(id=reading_id).first()
    if not reading:
        return None, {'status': 'error', 'message': 'Reading not found'}, 404

    if reading.owner_email == email or email == '__admin__':
        return reading, None, None
    
    return None, {'status': 'error', 
                  'message': "Forbidden: You don't have access to this resource"}, 403
    
def save_image(image, email, index):
    if image and image.filename and allowed_file(image.filename):
        extension = image.filename.rsplit('.', 1)[1].lower()
        filename = f'{email.split('@')[0]}_{index}.{extension}'
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        return f'static/uploads/{filename}'
    
    return None

def delete_image_file(image_path):
    if image_path:
        full_path = os.path.join(app.root_path, image_path.lstrip('/'))
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            abort(500, description=f'Failed to delete image file: {str(e)}')


# routes

# (GET) https://www.bookshelf.com/
@app.route('/')
def home():
    return jsonify({'message': 'Welcome to BookShelf API'})


# (GET) https://www.bookshelf.com/readings?is_deleted=false
@app.route('/readings', methods=['GET'])
def get_readings():
    email = request.headers.get('Authorization')

    if not email:
        return jsonify([])
    
    is_deleted = request.args.get('is_deleted')
    
    if (email == '__admin__') :
        query = Reading.query
    else:
        query = Reading.query.filter_by(owner_email=email)
    
    if is_deleted == 'true':
        query = query.filter_by(is_deleted=True)
    elif is_deleted == 'false':
        query = query.filter_by(is_deleted=False)

    readings = query.order_by(Reading.date_modified.desc()).all()

    return jsonify([reading.to_dict() for reading in readings])


# GET https://www.bookshelf.com/readings/10
@app.route('/readings/<int:reading_id>', methods=['GET'])
def get_reading(reading_id):
    email, error_data, status_code = get_user_email_or_401()
    if error_data:
        return jsonify(error_data), status_code

    reading, error_data, status_code = get_reading_or_404(reading_id, email)
    if error_data:
        return jsonify(error_data), status_code

    if not reading:
        return jsonify({'status': 'error', 'message': 'Reading not found'}), 404

    return jsonify(reading.to_dict())

 
# (POST) https://www.bookshelf.com/readings
@app.route('/readings', methods=['POST'])
def add_reading():
    email, error_data, status_code = get_user_email_or_401()
    if error_data:
        return jsonify(error_data), status_code

    # use multipart/form-data -> image + form fields
    image = request.files.get('image')  # .get() if theres no file then None
    # image = request.files['image']

    title = request.form.get('title')
    author = request.form.get('author')
    genre = request.form.get('genre')
    pages = request.form.get('pages', type=int)

    if not all([title, author, genre, pages]):
        return jsonify({'status': 'error',
                        'message': 'Missing fields'}), 400
    
    # web_path = None
    image_path = None
    if image and image.filename:
        if allowed_file(image.filename):
            index = Reading.query.filter_by(owner_email=email).count()
            image_path = save_image(image, email, index)
        else:
            return jsonify({'status': 'error',
                            'message': 'Invalid image format (only JPG, JPEG, PNG allowed)'}), 400

    # insert to db
    reading = Reading(
        owner_email=email,
        image_path=image_path,
        title=title,
        author=author,
        genre=genre,
        pages=pages,
        current_page=0,
        date_modified=datetime.now(),
        is_deleted=False
    )

    db.session.add(reading)
    db.session.commit()

    return jsonify({'status': 'success', 'id': reading.id}), 201


# (GET) https://www.bookshelf.com/uploads/yakup15_10.jpg
@app.route('/uploads/<filename>')
def view_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# (PUT) https://www.bookshelf.com/readings/201
@app.route('/readings/<int:reading_id>', methods=['PUT'])
def update_reading(reading_id):
    email, error_data, status_code = get_user_email_or_401()
    if error_data:
        return jsonify(error_data), status_code

    reading, error_data, status_code = get_reading_or_404(reading_id, email)
    if error_data:
        return jsonify(error_data), status_code
    
    # get form data
    form = request.form
    title = form.get('title')
    author = form.get('author')
    genre = form.get('genre')
    pages = form.get('pages', type=int)
    current_page = form.get('currentPage', type=int)

    # update fields if provided
    if title: reading.title = title
    if author: reading.author = author
    if genre: reading.genre = genre
    if pages is not None: reading.pages = pages
    if current_page is not None: reading.current_page = current_page

    # handle new image
    if 'image' in request.files:
        image = request.files['image']
        if image and image.filename:
            if allowed_file(image.filename):
                # if old image exist, delete
                delete_image_file(reading.image_path)

                index = Reading.query.filter_by(owner_email=email).count()
                reading.image_path = save_image(image, email, index)
            else:
                return jsonify({'status': 'error', 
                                'message': 'Invalid image format'}), 400

    reading.date_modified = datetime.now()
    db.session.commit()

    return jsonify({'status': 'success', 
                    'message': 'Reading updated'})


# (PATCH) https://www.bookshelf.com/readings/445/image
@app.route('/readings/<int:reading_id>/image', methods=['PATCH'])
def remove_image(reading_id):
    email, error_data, status_code = get_user_email_or_401()
    if error_data:
        return jsonify(error_data), status_code

    reading, error_data, status_code = get_reading_or_404(reading_id, email)
    if error_data:
        return jsonify(error_data), status_code
    
    # remove the actual image ppath
    if reading.image_path:
        delete_image_file(reading.image_path)
    
    # set image_path to null in db
    reading.image_path = None
    reading.date_modified = datetime.now()
    db.session.commit()

    return jsonify({'status': 'success', 
                    'message': 'Image removed'})


# (PATCH) https://www.bookshelf.com/readings/890/is-deleted
@app.route('/readings/<int:reading_id>/is-deleted', methods=['PATCH'])
def update_delete_status(reading_id):
    email, error_data, status_code = get_user_email_or_401()
    if error_data:
        return jsonify(error_data), status_code

    reading, error_data, status_code = get_reading_or_404(reading_id, email)
    if error_data:
        return jsonify(error_data), status_code
    
    # get request body
    data = request.get_json()

    if not data or 'isDeleted' not in data:
        return jsonify({'status': 'error',
                        'message': 'Missing isDeleted field'}), 404
    
    # update is_deleted in db
    reading.is_deleted = data['isDeleted']
    reading.date_modified = datetime.now()
    db.session.commit()

    return jsonify({'status': 'success',
                    'message': 'isDeleted status updated'})


# (DELETE) https://www.bookshelf.com/readings/900
@app.route('/readings/<int:reading_id>', methods=['DELETE'])
def delete_reading(reading_id):
    email, error_data, status_code = get_user_email_or_401()
    if error_data:
        return jsonify(error_data), status_code

    reading, error_data, status_code = get_reading_or_404(reading_id, email)
    if error_data:
        return jsonify(error_data), status_code
    
    # remove the actual image ppath
    if reading.image_path:
        delete_image_file(reading.image_path)

    # delete resource in db
    db.session.delete(reading)
    db.session.commit()

    return jsonify({'status': 'success',
                    'message': 'Reading deleted'})


# (DELETE) https://www.bookshelf.com/readings/deleted
@app.route('/readings/deleted', methods=['DELETE'])
def delete_soft_deleted_readings():
    email, error_data, status_code = get_user_email_or_401()
    if error_data:
        return jsonify(error_data), status_code

    readings = Reading.query.filter_by(is_deleted=True, owner_email=email).all()
    for reading in readings:
        # remove the actual image ppath
        if reading.image_path:
            delete_image_file(reading.image_path)

        db.session.delete(reading)
    db.session.commit()

    return jsonify({'status': 'success',
                    'message': 'Deleted all Readings in trash'})

if __name__ == '__main__':
    app.run(debug=True)




