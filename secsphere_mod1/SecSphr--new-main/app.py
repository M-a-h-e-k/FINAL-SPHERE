import os
import csv
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///securesphere.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'csv', 'txt', 'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    organization = db.Column(db.String(120))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class ProductStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='in_progress')  # in_progress, questions_done, under_review, review_done, completed
    questions_completed = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
class ScoreHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    total_score = db.Column(db.Integer, default=0)
    max_score = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Float, default=0.0)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuestionnaireResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    section = db.Column(db.String(100))
    question = db.Column(db.String(300))
    answer = db.Column(db.String(200))
    comment = db.Column(db.Text)
    evidence_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_reviewed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)

class LeadComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey('questionnaire_response.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    comment = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, needs_revision, rejected, client_reply
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('lead_comment.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    parent_comment = db.relationship('LeadComment', remote_side=[id], backref='replies')
    response = db.relationship('QuestionnaireResponse', backref='lead_comments')
    lead = db.relationship('User', foreign_keys=[lead_id], backref='lead_comments_made')
    client = db.relationship('User', foreign_keys=[client_id], backref='lead_comments_received')
    product = db.relationship('Product', backref='lead_comments')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_questionnaire():
    sections = {}
    with open('devweb.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        current_dimension = None
        current_question_obj = None
        for row in reader:
            dimension = row['Dimensions'].strip()
            question = row['Questions'].strip()
            description = row['Description'].strip()
            option = row['Options'].strip()
            # New dimension starts
            if dimension:
                current_dimension = dimension
                if current_dimension not in sections:
                    sections[current_dimension] = []
            # New question starts
            if question:
                # Save previous question to section (if exists)
                if current_question_obj:
                    sections[current_dimension].append(current_question_obj)
                current_question_obj = {
                    'question': question,
                    'description': description,
                    'options': []
                }
            # Add option to current question
            if current_question_obj is not None and option:
                current_question_obj['options'].append(option)
        # Add last question
        if current_question_obj:
            sections[current_dimension].append(current_question_obj)
    return sections

QUESTIONNAIRE = load_questionnaire()
SECTION_IDS = list(QUESTIONNAIRE.keys())

# Database initialization
def init_database():
    """Initialize database and create tables if they don't exist"""
    with app.app_context():
        db.create_all()
        
        # Check if new columns exist and add them if they don't
        try:
            # Test if the new columns exist by running a simple query
            db.session.execute(db.text("SELECT is_reviewed FROM questionnaire_response LIMIT 1"))
        except Exception:
            # Column doesn't exist, add it
            try:
                db.session.execute(db.text("ALTER TABLE questionnaire_response ADD COLUMN is_reviewed BOOLEAN DEFAULT 0"))
                db.session.commit()
                print("Added is_reviewed column to questionnaire_response table")
            except Exception as e:
                print(f"Could not add is_reviewed column: {e}")
        
        try:
            # Test if score column exists
            db.session.execute(db.text("SELECT score FROM questionnaire_response LIMIT 1"))
        except Exception:
            # Column doesn't exist, add it
            try:
                db.session.execute(db.text("ALTER TABLE questionnaire_response ADD COLUMN score INTEGER DEFAULT 0"))
                db.session.commit()
                print("Added score column to questionnaire_response table")
            except Exception as e:
                print(f"Could not add score column: {e}")
        
        # Check if LeadComment table has the new created_at column
        try:
            db.session.execute(db.text("SELECT created_at FROM lead_comment LIMIT 1"))
        except Exception:
            try:
                db.session.execute(db.text("ALTER TABLE lead_comment ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                db.session.commit()
                print("Added created_at column to lead_comment table")
            except Exception as e:
                print(f"Could not add created_at column: {e}")
        
        # Remove the old is_read column if it exists
        try:
            db.session.execute(db.text("SELECT is_read FROM lead_comment LIMIT 1"))
            # If we get here, the column exists, so we should remove it
            try:
                # SQLite doesn't support DROP COLUMN directly, so we'll just ignore it
                print("Note: is_read column exists but will be ignored")
            except Exception:
                pass
        except Exception:
            # Column doesn't exist, which is good
            pass
        
        print("Database initialized successfully!")

def calculate_score_for_answer(question, answer):
    """Calculate score for a specific question-answer pair based on CSV data"""
    try:
        with open('devweb.csv', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                q = row['Questions'].strip()
                option = row['Options'].strip()
                scores_text = row.get('Scores', '').strip()
                
                if q == question and option == answer and scores_text:
                    # Parse the score from the CSV
                    try:
                        score = int(scores_text)
                        return score * 20  # Scale 1-5 to 20-100 scoring system
                    except (ValueError, IndexError):
                        return 0
    except FileNotFoundError:
        print("CSV file not found, using default scoring")
    
    # Default scoring based on option letter if CSV parsing fails
    if answer.startswith('A)'):
        return 20  # Lowest score
    elif answer.startswith('B)'):
        return 40
    elif answer.startswith('C)'):
        return 60
    elif answer.startswith('D)'):
        return 80
    elif answer.startswith('E)'):
        return 100  # Highest score
    else:
        # Fallback to original logic
        if answer.lower() in ['yes', 'fully implemented', 'high']:
            return 100
        elif answer.lower() in ['partially', 'medium']:
            return 50
        elif answer.lower() in ['no', 'not implemented', 'low']:
            return 0
        else:
            return 25

def update_product_status(product_id, user_id):
    """Update product status based on current responses and reviews"""
    status_record = ProductStatus.query.filter_by(product_id=product_id, user_id=user_id).first()
    if not status_record:
        status_record = ProductStatus(product_id=product_id, user_id=user_id)
        db.session.add(status_record)
    
    # Count total questions and answered questions
    total_questions = sum(len(questions) for questions in QUESTIONNAIRE.values())
    answered_questions = QuestionnaireResponse.query.filter_by(
        product_id=product_id, user_id=user_id
    ).count()
    
    # Count reviewed questions (with safety check for is_reviewed column)
    try:
        reviewed_questions = QuestionnaireResponse.query.filter_by(
            product_id=product_id, user_id=user_id, is_reviewed=True
        ).count()
    except Exception:
        # If is_reviewed column doesn't exist yet, assume no questions are reviewed
        reviewed_questions = 0
    
    # Update status based on progress
    if answered_questions == 0:
        status_record.status = 'in_progress'
    elif answered_questions == total_questions and reviewed_questions == 0:
        status_record.status = 'questions_done'
    elif reviewed_questions > 0 and reviewed_questions < answered_questions:
        status_record.status = 'under_review'
    elif reviewed_questions == answered_questions and answered_questions == total_questions:
        # Check if all reviews are approved
        approved_count = db.session.query(LeadComment).join(QuestionnaireResponse).filter(
            QuestionnaireResponse.product_id == product_id,
            QuestionnaireResponse.user_id == user_id,
            LeadComment.status == 'approved'
        ).count()
        
        if approved_count == answered_questions:
            status_record.status = 'completed'
        else:
            status_record.status = 'review_done'
    else:
        status_record.status = 'in_progress'
    
    status_record.questions_completed = answered_questions
    status_record.total_questions = total_questions
    status_record.last_updated = datetime.utcnow()
    
    db.session.commit()
    return status_record.status

def calculate_and_store_scores(product_id, user_id):
    """Calculate scores for all sections and store in ScoreHistory"""
    responses = QuestionnaireResponse.query.filter_by(
        product_id=product_id, user_id=user_id
    ).all()
    
    section_scores = {}
    section_max_scores = {}
    
    # Calculate scores by section
    for response in responses:
        section = response.section
        if section not in section_scores:
            section_scores[section] = 0
            section_max_scores[section] = 0
        
        # Calculate score for this response
        score = calculate_score_for_answer(response.question, response.answer)
        try:
            response.score = score
        except Exception:
            # If score column doesn't exist yet, skip setting it
            pass
        section_scores[section] += score
        
        # Calculate max possible score for this question
        max_score = 100  # Default max score per question
        section_max_scores[section] += max_score
    
    # Store scores in ScoreHistory
    for section, total_score in section_scores.items():
        max_score = section_max_scores.get(section, 1)
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Remove old score record for this section
        ScoreHistory.query.filter_by(
            product_id=product_id, user_id=user_id, section_name=section
        ).delete()
        
        # Add new score record
        score_record = ScoreHistory(
            product_id=product_id,
            user_id=user_id,
            section_name=section,
            total_score=total_score,
            max_score=max_score,
            percentage=percentage
        )
        db.session.add(score_record)
    
    db.session.commit()
    return section_scores

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Access denied!')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        organization = request.form.get('organization')
        # Server-side validation
        if not username or not email or not password or not role:
            flash('Please fill in all fields.')
            return redirect(url_for('register'))
        if role == 'client' and not organization:
            flash('Organization name required for client.')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))
        import re
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            flash('Invalid email format.')
            return redirect(url_for('register'))
        if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
            flash('Password must be at least 8 characters and include uppercase, lowercase, and number.')
            return redirect(url_for('register'))
        hash_pwd = generate_password_hash(password)
        user = User(username=username, email=email, password=hash_pwd, role=role, organization=organization)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash('Invalid credentials.')
            return redirect(url_for('login'))
        session['user_id'] = user.id
        session['role'] = user.role
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required()
def dashboard():
    role = session['role']
    user_id = session['user_id']
    if role == 'client':
        products = Product.query.filter_by(owner_id=user_id).all()
        # Check assessment completion for each product
        products_with_status = []
        for product in products:
            # Get product status
            status_record = ProductStatus.query.filter_by(product_id=product.id, user_id=user_id).first()
            if not status_record:
                # Create initial status record
                status_record = ProductStatus(product_id=product.id, user_id=user_id)
                db.session.add(status_record)
                db.session.commit()
            
            # Get responses and calculate progress
            responses = QuestionnaireResponse.query.filter_by(product_id=product.id, user_id=user_id).all()
            completed_sections = set([r.section for r in responses])
            total_sections = len(SECTION_IDS)
            completed_sections_count = len(completed_sections)
            
            # Find next section to continue
            next_section_idx = 0
            for i, section in enumerate(SECTION_IDS):
                if section not in completed_sections:
                    next_section_idx = i
                    break
            
            # Get latest scores
            latest_scores = ScoreHistory.query.filter_by(
                product_id=product.id, user_id=user_id
            ).order_by(ScoreHistory.calculated_at.desc()).all()
            
            total_score = sum(score.total_score for score in latest_scores)
            max_possible_score = sum(score.max_score for score in latest_scores)
            overall_percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
            
            product_info = {
                'id': product.id,
                'name': product.name,
                'owner_id': product.owner_id,
                'status': status_record.status,
                'status_display': status_record.status.replace('_', ' ').title(),
                'completed_sections': completed_sections_count,
                'total_sections': total_sections,
                'next_section_idx': next_section_idx,
                'progress_percentage': round((completed_sections_count / total_sections) * 100, 1),
                'answered_questions': status_record.questions_completed,
                'total_questions': status_record.total_questions,
                'overall_score': round(overall_percentage, 1),
                'last_updated': status_record.last_updated
            }
            products_with_status.append(product_info)
        
        # Get comments count (all comments for this client)
        unread_comments = LeadComment.query.filter_by(client_id=user_id).count()
        
        return render_template('dashboard_client.html', products=products_with_status, unread_comments=unread_comments)
    elif role == 'lead':
        # Get all responses with user and product information
        resps = db.session.query(QuestionnaireResponse, User, Product).join(
            User, QuestionnaireResponse.user_id == User.id
        ).join(
            Product, QuestionnaireResponse.product_id == Product.id
        ).all()
        
        # Organize responses by client and product
        clients_data = {}
        for resp, user, product in resps:
            if user.id not in clients_data:
                clients_data[user.id] = {
                    'user': user,
                    'products': {}
                }
            if product.id not in clients_data[user.id]['products']:
                clients_data[user.id]['products'][product.id] = {
                    'product': product,
                    'responses': []
                }
            clients_data[user.id]['products'][product.id]['responses'].append(resp)
        
        return render_template('dashboard_lead.html', clients_data=clients_data)
    elif role == 'superuser':
        products = Product.query.all()
        
        # Get detailed product data with responses and scoring
        products_data = []
        for product in products:
            responses = QuestionnaireResponse.query.filter_by(product_id=product.id).all()
            
            # Calculate scores by dimension
            dimension_scores = {}
            for resp in responses:
                if resp.section not in dimension_scores:
                    dimension_scores[resp.section] = {'total': 0, 'count': 0}
                
                # Simple scoring based on answer (this can be made more sophisticated)
                score = 0
                if 'yes' in resp.answer.lower() or 'high' in resp.answer.lower():
                    score = 100
                elif 'partially' in resp.answer.lower() or 'medium' in resp.answer.lower():
                    score = 50
                elif 'no' in resp.answer.lower() or 'low' in resp.answer.lower():
                    score = 0
                else:
                    score = 25  # Default for other answers
                
                dimension_scores[resp.section]['total'] += score
                dimension_scores[resp.section]['count'] += 1
            
            # Calculate average scores for each dimension
            for dimension in dimension_scores:
                if dimension_scores[dimension]['count'] > 0:
                    dimension_scores[dimension]['average'] = dimension_scores[dimension]['total'] / dimension_scores[dimension]['count']
                else:
                    dimension_scores[dimension]['average'] = 0
            
            # Get product owner info
            owner = User.query.get(product.owner_id)
            
            products_data.append({
                'product': product,
                'owner': owner,
                'responses': responses,
                'dimension_scores': dimension_scores,
                'total_responses': len(responses)
            })
        
        # Get comments data for admin dashboard
        recent_comments = LeadComment.query.order_by(LeadComment.created_at.desc()).limit(10).all()
        total_comments = LeadComment.query.count()
        approved_comments = LeadComment.query.filter_by(status='approved').count()
        pending_comments = LeadComment.query.filter(LeadComment.status.in_(['pending', 'under_review', 'needs_revision'])).count()
        rejected_comments = LeadComment.query.filter_by(status='rejected').count()
        
        return render_template('dashboard_superuser.html', 
                             products_data=products_data,
                             recent_comments=recent_comments,
                             total_comments=total_comments,
                             approved_comments=approved_comments,
                             pending_comments=pending_comments,
                             rejected_comments=rejected_comments)
    return redirect(url_for('index'))

def is_assessment_complete(product_id, user_id):
    """Check if assessment is complete for a product"""
    completed_sections = set([
        r.section for r in QuestionnaireResponse.query.filter_by(
            product_id=product_id, user_id=user_id
        ).all()
    ])
    return len(completed_sections) == len(SECTION_IDS)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required('client')
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        if not name:
            flash('Product name required.')
            return redirect(url_for('add_product'))
        product = Product(name=name, owner_id=session['user_id'])
        db.session.add(product)
        db.session.commit()
        flash('Product added. Now fill the questionnaire.')
        return redirect(url_for('fill_questionnaire_section', product_id=product.id, section_idx=0))
    return render_template('add_product.html')

@app.route('/fill_questionnaire/<int:product_id>/section/<int:section_idx>', methods=['GET', 'POST'])
@login_required('client')
def fill_questionnaire_section(product_id, section_idx):
    product = Product.query.get_or_404(product_id)
    sections = SECTION_IDS
    if section_idx >= len(sections):
        flash("All sections complete!")
        return redirect(url_for('dashboard'))
    section_name = sections[section_idx]
    questions = QUESTIONNAIRE[section_name]
    
    # Get existing responses for this section to pre-populate form
    existing_responses = QuestionnaireResponse.query.filter_by(
        product_id=product_id, 
        user_id=session['user_id'], 
        section=section_name
    ).all()
    
    # Create a dictionary for quick lookup of existing responses
    existing_answers = {}
    for resp in existing_responses:
        for i, q in enumerate(questions):
            if q['question'] == resp.question:
                existing_answers[i] = resp
                break
    
    if request.method == 'POST':
        # Get lead comments for validation
        response_ids = [resp.id for resp in existing_responses]
        lead_comments = {}
        if response_ids:
            comments = LeadComment.query.filter(LeadComment.response_id.in_(response_ids)).all()
            for comment in comments:
                lead_comments[comment.response_id] = comment
        
        # Delete existing responses for this section before adding new ones (except approved ones)
        responses_to_delete = []
        for resp in existing_responses:
            lead_comment = lead_comments.get(resp.id)
            if not lead_comment or lead_comment.status != 'approved':
                responses_to_delete.append(resp.id)
        
        if responses_to_delete:
            QuestionnaireResponse.query.filter(QuestionnaireResponse.id.in_(responses_to_delete)).delete()
        
        for i, q in enumerate(questions):
            # Check if this question is approved
            existing_resp = existing_answers.get(i)
            if existing_resp:
                lead_comment = lead_comments.get(existing_resp.id)
                if lead_comment and lead_comment.status == 'approved':
                    # Keep the approved response as-is, don't update it
                    continue
            
            answer = request.form.get(f'answer_{i}')
            comment = request.form.get(f'comment_{i}')
            file = request.files.get(f'evidence_{i}')
            evidence_path = ""
            
            # Keep existing evidence if no new file uploaded
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{product_id}_{section_idx}_{i}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                evidence_path = filepath
            elif i in existing_answers:
                evidence_path = existing_answers[i].evidence_path or ''
            
            resp = QuestionnaireResponse(
                user_id=session['user_id'],
                product_id=product_id,
                section=section_name,
                question=q['question'],
                answer=answer,
                comment=comment,
                evidence_path=evidence_path
            )
            db.session.add(resp)
        db.session.commit()
        
        # Update product status and calculate scores
        status = update_product_status(product_id, session['user_id'])
        calculate_and_store_scores(product_id, session['user_id'])
        
        if section_idx + 1 < len(sections):
            return redirect(url_for('fill_questionnaire_section', product_id=product_id, section_idx=section_idx+1))
        else:
            if status == 'questions_done':
                flash("Questions completed! Waiting for review.")
            elif status == 'completed':
                flash("Assessment completed successfully!")
            else:
                flash("Section saved successfully!")
            return redirect(url_for('dashboard'))
    
    completed_sections = [
        s.section for s in QuestionnaireResponse.query.filter_by(product_id=product_id, user_id=session['user_id']).distinct(QuestionnaireResponse.section)
    ]
    progress = [(i, s, (s in completed_sections)) for i, s in enumerate(sections)]
    
    # Get review status for questions in this section
    question_review_status = {}
    if existing_responses:
        response_ids = [resp.id for resp in existing_responses]
        lead_comments = LeadComment.query.filter(LeadComment.response_id.in_(response_ids)).all()
        for comment in lead_comments:
            for resp in existing_responses:
                if resp.id == comment.response_id:
                    for i, q in enumerate(questions):
                        if q['question'] == resp.question:
                            question_review_status[i] = comment.status
                            break
    
    return render_template(
        'fill_questionnaire_section.html',
        product=product,
        section_name=section_name,
        questions=questions,
        section_idx=section_idx,
        total_sections=len(sections),
        progress=progress,
        existing_answers=existing_answers,
        question_review_status=question_review_status
    )

@app.route('/product/<int:product_id>/results')
@login_required('client')
def product_results(product_id):
    resps = QuestionnaireResponse.query.filter_by(product_id=product_id, user_id=session['user_id']).all()
    # Get lead comments for this product
    lead_comments = LeadComment.query.filter_by(product_id=product_id, client_id=session['user_id']).order_by(LeadComment.created_at.desc()).all()
    return render_template('product_results.html', responses=resps, lead_comments=lead_comments)

@app.route('/client/comments')
@login_required('client')
def client_comments():
    comments = LeadComment.query.filter_by(client_id=session['user_id']).order_by(LeadComment.created_at.desc()).all()
    return render_template('client_comments.html', comments=comments)

@app.route('/client/comment/<int:comment_id>/read')
@login_required('client')
def mark_comment_read(comment_id):
    comment = LeadComment.query.get_or_404(comment_id)
    if comment.client_id == session['user_id']:
        # Comment read functionality can be implemented later if needed
        pass
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/client/comment/<int:comment_id>/reply', methods=['POST'])
@login_required('client')
def client_reply_comment(comment_id):
    parent_comment = LeadComment.query.get_or_404(comment_id)
    if parent_comment.client_id != session['user_id']:
        flash('Unauthorized access.')
        return redirect(url_for('dashboard'))
    
    reply_text = request.form['reply']
    evidence_file = request.files.get('evidence')
    
    if reply_text.strip():
        evidence_path = None
        # Handle evidence upload if provided
        if evidence_file and evidence_file.filename and allowed_file(evidence_file.filename):
            filename = secure_filename(evidence_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            evidence_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
            evidence_file.save(evidence_path)
        
        # Create a reply comment
        reply_comment = LeadComment(
            response_id=parent_comment.response_id,
            lead_id=parent_comment.lead_id,  # Send back to the original lead
            client_id=session['user_id'],
            product_id=parent_comment.product_id,
            comment=reply_text,  # Remove the "Client Reply:" prefix for cleaner display
            status='client_reply',
            parent_comment_id=comment_id
        )
        db.session.add(reply_comment)
        
        # If evidence provided, also update the original response
        if evidence_path and parent_comment.response_id:
            original_response = QuestionnaireResponse.query.get(parent_comment.response_id)
            if original_response:
                original_response.evidence_path = evidence_path
                original_response.comment = reply_text
        
        db.session.commit()
        flash('Reply sent to lead successfully.')
    
    return redirect(request.referrer or url_for('client_comments'))

@app.route('/lead/comment/<int:comment_id>/reply', methods=['POST'])
@login_required('lead')
def lead_reply_comment(comment_id):
    parent_comment = LeadComment.query.get_or_404(comment_id)
    if parent_comment.lead_id != session['user_id']:
        flash('Unauthorized access.')
        return redirect(url_for('dashboard'))
    
    reply_text = request.form['reply']
    status = request.form.get('review_status', 'pending')
    
    if reply_text.strip():
        # Create a reply comment
        reply_comment = LeadComment(
            response_id=parent_comment.response_id,
            lead_id=session['user_id'],
            client_id=parent_comment.client_id,
            product_id=parent_comment.product_id,
            comment=reply_text,
            status=status,
            parent_comment_id=comment_id
        )
        db.session.add(reply_comment)
        
        # Update the original response if needed
        if parent_comment.response_id and status in ['needs_revision', 'rejected']:
            original_response = QuestionnaireResponse.query.get(parent_comment.response_id)
            if original_response:
                original_response.is_reviewed = False  # Allow client to modify
        
        db.session.commit()
        flash('Reply sent to client successfully.')
    
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/review/<int:response_id>', methods=['GET', 'POST'])
@login_required('lead')
def review_questionnaire(response_id):
    resp = QuestionnaireResponse.query.get_or_404(response_id)
    if request.method == 'POST':
        comment = request.form['lead_comment']
        status = request.form.get('review_status', 'pending')
        
        # Create lead comment
        lead_comment = LeadComment(
            response_id=response_id,
            lead_id=session['user_id'],
            client_id=resp.user_id,
            product_id=resp.product_id,
            comment=comment,
            status=status
        )
        db.session.add(lead_comment)
        
        # Mark response as reviewed (with safety check)
        try:
            resp.is_reviewed = True
        except Exception:
            # If is_reviewed column doesn't exist yet, skip setting it
            pass
        
        db.session.commit()
        
        # Update product status and recalculate scores
        update_product_status(resp.product_id, resp.user_id)
        calculate_and_store_scores(resp.product_id, resp.user_id)
        
        flash('Review comment sent to client.')
        return redirect(url_for('dashboard'))
    return render_template('review_questionnaire.html', response=resp)

@app.route('/admin/product/<int:product_id>/details')
@login_required('superuser')
def admin_product_details(product_id):
    resps = QuestionnaireResponse.query.filter_by(product_id=product_id).all()
    return render_template('admin_product_details.html', responses=resps, product_id=product_id)

@app.route('/admin/create_product', methods=['GET', 'POST'])
@login_required('superuser')
def admin_create_product():
    if request.method == 'POST':
        product_name = request.form['product_name']
        client_id = request.form['client_id']
        
        # Verify client exists
        client = User.query.filter_by(id=client_id, role='client').first()
        if not client:
            flash('Invalid client selected.')
            return redirect(url_for('admin_create_product'))
        
        # Create product
        product = Product(name=product_name, owner_id=client_id)
        db.session.add(product)
        db.session.commit()
        
        flash(f'Product "{product_name}" created successfully for {client.username}.')
        return redirect(url_for('dashboard'))
    
    # Get all clients for the form
    clients = User.query.filter_by(role='client').all()
    return render_template('admin_create_product.html', clients=clients)

@app.route('/admin/analytics')
@login_required('superuser')
def admin_analytics():
    # Get all products and their scores for analytics
    products = Product.query.all()
    analytics_data = []
    
    for product in products:
        responses = QuestionnaireResponse.query.filter_by(product_id=product.id).all()
        if responses:
            # Calculate average score for this product
            total_score = 0
            total_questions = 0
            section_scores = {}
            
            for response in responses:
                if response.answer.isdigit():
                    score = int(response.answer)
                    total_score += score
                    total_questions += 1
                    
                    if response.section not in section_scores:
                        section_scores[response.section] = []
                    section_scores[response.section].append(score)
            
            if total_questions > 0:
                avg_score = total_score / total_questions
                owner = User.query.get(product.owner_id)
                
                analytics_data.append({
                    'product': product,
                    'owner': owner,
                    'avg_score': avg_score,
                    'total_responses': len(responses),
                    'section_scores': {k: sum(v)/len(v) for k, v in section_scores.items()}
                })
    
    return render_template('admin_analytics.html', analytics_data=analytics_data)

@app.route('/admin/products/delete/<int:product_id>')
@login_required('superuser')
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    QuestionnaireResponse.query.filter_by(product_id=product_id).delete()
    db.session.delete(product)
    db.session.commit()
    flash('Product and all responses deleted.')
    return redirect(url_for('dashboard'))

@app.route('/api/product/<int:product_id>/scores')
@login_required()
def api_product_scores(product_id):
    resps = QuestionnaireResponse.query.filter_by(product_id=product_id).all()
    section_scores = {}
    section_max_scores = {}
    section_counts = {}
    total_score = 0
    total_max_score = 0
    csv_map = {}
    
    # Build scoring map from CSV
    with open('devweb.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dimension = row['Dimensions'].strip()
            question = row['Questions'].strip()
            if question:  # Only process rows with questions
                options = [o.strip() for o in row['Options'].split('\n') if o.strip()]
                scores = []
                for s in row['Scores'].split('\n'):
                    s = s.strip()
                    if s.isdigit():
                        scores.append(int(s))
                    else:
                        scores.append(0)
                
                if len(options) == len(scores):
                    csv_map[question] = dict(zip(options, scores))
                    if dimension not in section_max_scores:
                        section_max_scores[dimension] = 0
                    if scores:
                        section_max_scores[dimension] += max(scores)
                        total_max_score += max(scores)
    
    # Calculate actual scores
    question_scores = {}
    for r in resps:
        sec = r.section
        if sec not in section_scores:
            section_scores[sec] = 0
            section_counts[sec] = 0
        
        score = csv_map.get(r.question, {}).get(r.answer, 0)
        section_scores[sec] += score
        section_counts[sec] += 1
        total_score += score
        
        # Store individual question scores
        question_scores[f"{r.question}:{r.answer}"] = score
    
    # Calculate percentages
    section_labels = list(section_scores.keys())
    section_values = [section_scores[k] for k in section_labels]
    section_percentages = []
    
    for section in section_labels:
        max_section_score = section_max_scores.get(section, 1)
        percentage = (section_scores[section] / max_section_score * 100) if max_section_score > 0 else 0
        section_percentages.append(round(percentage, 1))
    
    overall_percentage = (total_score / total_max_score * 100) if total_max_score > 0 else 0
    
    return jsonify({
        "section_labels": section_labels,
        "section_scores": section_values,
        "section_percentages": section_percentages,
        "section_max_scores": [section_max_scores.get(k, 0) for k in section_labels],
        "total_score": total_score,
        "max_score": total_max_score,
        "overall_percentage": round(overall_percentage, 1),
        "sections_count": len(section_labels),
        "question_scores": question_scores
    })

@app.route('/api/superuser/all_scores')
@login_required('superuser')
def api_all_scores():
    products = Product.query.all()
    all_scores = []
    
    for product in products:
        product_data = {}
        resps = QuestionnaireResponse.query.filter_by(product_id=product.id).all()
        
        if resps:
            # Get scores for this product
            section_scores = {}
            section_max_scores = {}
            total_score = 0
            total_max_score = 0
            csv_map = {}
            
            # Build scoring map
            with open('devweb.csv', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dimension = row['Dimensions'].strip()
                    question = row['Questions'].strip()
                    if question:
                        options = [o.strip() for o in row['Options'].split('\n') if o.strip()]
                        scores = []
                        for s in row['Scores'].split('\n'):
                            s = s.strip()
                            if s.isdigit():
                                scores.append(int(s))
                            else:
                                scores.append(0)
                        
                        if len(options) == len(scores):
                            csv_map[question] = dict(zip(options, scores))
                            if dimension not in section_max_scores:
                                section_max_scores[dimension] = 0
                            if scores:
                                section_max_scores[dimension] += max(scores)
                                total_max_score += max(scores)
            
            # Calculate scores
            for r in resps:
                sec = r.section
                if sec not in section_scores:
                    section_scores[sec] = 0
                
                score = csv_map.get(r.question, {}).get(r.answer, 0)
                section_scores[sec] += score
                total_score += score
            
            overall_percentage = (total_score / total_max_score * 100) if total_max_score > 0 else 0
            
            # Get owner info
            owner = User.query.get(product.owner_id)
            
            product_data = {
                'id': product.id,
                'name': product.name,
                'owner': owner.username if owner else 'Unknown',
                'organization': owner.organization if owner else 'Unknown',
                'total_score': total_score,
                'max_score': total_max_score,
                'percentage': round(overall_percentage, 1),
                'section_scores': section_scores,
                'section_percentages': {k: round((v / section_max_scores.get(k, 1) * 100), 1) 
                                       for k, v in section_scores.items()}
            }
        else:
            product_data = {
                'id': product.id,
                'name': product.name,
                'owner': 'Unknown',
                'organization': 'Unknown',
                'total_score': 0,
                'max_score': 0,
                'percentage': 0,
                'section_scores': {},
                'section_percentages': {}
            }
        
        all_scores.append(product_data)
    
    return jsonify(all_scores)

if __name__ == '__main__':
    os.makedirs('static/uploads', exist_ok=True)
    init_database()
    app.run(debug=True)