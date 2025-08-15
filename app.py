from functools import wraps
import io
import os
from flask import Flask, Response, render_template, jsonify, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import hashlib
import pandas as pd
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
application = app

# Modèles SQLAlchemy
class Personnel(db.Model):
    __tablename__ = 'personnels'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.String(20), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    departement = db.Column(db.Enum('Direction', 'Trading', 'Academy', 'Digital'), default='Trading')
    date_arrivee = db.Column(db.Date, nullable=True)
    date_depart = db.Column(db.Date, nullable=True)
    ecole = db.Column(db.String(100), nullable=True)
    convention = db.Column(db.Enum('Stage', 'CDD', 'CDI'), default='Stage')
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('Administrator', 'Trading', 'Academy', 'Digital', 'Comptabilite'), default='Academy')
    observations = db.Column(db.Text, nullable=True)
    
    # Relations
    tradings = db.relationship('Trading', backref='personnel_trading', lazy=True, cascade='all, delete-orphan')
    academys = db.relationship('Academy', backref='personnel_academy', lazy=True, cascade='all, delete-orphan')
    digitals = db.relationship('Digital', backref='personnel_digital', lazy=True, cascade='all, delete-orphan')

class Trading(db.Model):
    __tablename__ = 'trading'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_const = db.Column(db.Date, nullable=True)
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id', ondelete='CASCADE'), nullable=True)
    type_libelle = db.Column(db.String(255), nullable=True)
    nom_client = db.Column(db.String(255), nullable=True)
    prenom_client = db.Column(db.String(255), nullable=True)
    phone_client = db.Column(db.String(255), nullable=True)
    email_client = db.Column(db.String(255), nullable=True)
    items = db.Column(db.String(255), nullable=True)
    quantite = db.Column(db.Integer, nullable=True)
    prix_unit = db.Column(db.Float, nullable=True)
    montant_ht = db.Column(db.Float, nullable=True)
    tva = db.Column(db.Float, nullable=True)
    montant_ttc = db.Column(db.Float, nullable=True)
    modalite_paiement = db.Column(db.String(255), nullable=True)
    type_paiement = db.Column(db.Enum('Virement bancaire', 'Cheque', 'Especes', 'Paiement mobile'), default='Especes')
    observations = db.Column(db.Text, nullable=True)

class Academy(db.Model):
    __tablename__ = 'academy'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_const = db.Column(db.Date, nullable=True)
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id', ondelete='CASCADE'), nullable=True)
    type_libelle = db.Column(db.String(255), nullable=True)
    nom_client = db.Column(db.String(255), nullable=True)
    prenom_client = db.Column(db.String(255), nullable=True)
    phone_client = db.Column(db.String(255), nullable=True)
    email_client = db.Column(db.String(255), nullable=True)
    items = db.Column(db.String(255), nullable=True)
    quantite = db.Column(db.Integer, nullable=True)
    prix_unit = db.Column(db.Float, nullable=True)
    montant_ht = db.Column(db.Float, nullable=True)
    tva = db.Column(db.Float, nullable=True)
    montant_ttc = db.Column(db.Float, nullable=True)
    modalite_paiement = db.Column(db.String(255), nullable=True)
    type_paiement = db.Column(db.Enum('Virement bancaire', 'Cheque', 'Especes', 'Paiement mobile'), default='Especes')
    observations = db.Column(db.Text, nullable=True)

class Digital(db.Model):
    __tablename__ = 'digital'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_const = db.Column(db.Date, nullable=True)
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id', ondelete='CASCADE'), nullable=True)
    type_libelle = db.Column(db.String(255), nullable=True)
    nom_client = db.Column(db.String(255), nullable=True)
    prenom_client = db.Column(db.String(255), nullable=True)
    phone_client = db.Column(db.String(255), nullable=True)
    email_client = db.Column(db.String(255), nullable=True)
    items = db.Column(db.String(255), nullable=True)
    quantite = db.Column(db.Integer, nullable=True)
    prix_unit = db.Column(db.Float, nullable=True)
    montant_ht = db.Column(db.Float, nullable=True)
    tva = db.Column(db.Float, nullable=True)
    montant_ttc = db.Column(db.Float, nullable=True)
    modalite_paiement = db.Column(db.String(255), nullable=True)
    type_paiement = db.Column(db.Enum('Virement bancaire', 'Cheque', 'Especes', 'Paiement mobile'), default='Especes')
    observations = db.Column(db.Text, nullable=True)

class Materiel(db.Model):
    __tablename__ = 'materiels'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom_produit = db.Column(db.String(255), nullable=True)
    fournisseur = db.Column(db.String(255), nullable=True)
    date_sortie = db.Column(db.Date, nullable=True)
    date_reception = db.Column(db.Date, nullable=True)
    quantite = db.Column(db.Integer, nullable=True)
    prix_unit = db.Column(db.Float, nullable=True)
    montant_ht = db.Column(db.Float, nullable=True)
    tva = db.Column(db.Float, nullable=True)
    montant_ttc = db.Column(db.Float, nullable=True)
    observations = db.Column(db.Text, nullable=True)

class Finance(db.Model):
    __tablename__ = 'finances'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=True)
    libelle = db.Column(db.Text, nullable=True)
    numero_compte = db.Column(db.String(255), nullable=True)
    credit = db.Column(db.Float, nullable=True)
    debit = db.Column(db.Float, nullable=True)
    montant_ht = db.Column(db.Float, nullable=True)
    tva = db.Column(db.Float, nullable=True)
    montant_ttc = db.Column(db.Float, nullable=True)
    observations = db.Column(db.Text, nullable=True)

class Projet(db.Model):
    __tablename__ = 'projets'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=True)
    budget = db.Column(db.Float, nullable=True)
    statut = db.Column(db.Enum('en attente', 'en cours', 'terminé', 'annulé'), default='en attente', nullable=False)
    departement = db.Column(db.Enum('Trading', 'Academy', 'Digital'), nullable=False)

class Evenementiel(db.Model):
    __tablename__ = 'evenementiels'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=True)
    budget = db.Column(db.Float, nullable=True)
    statut = db.Column(db.Enum('en attente', 'en cours', 'terminé', 'annulé'), default='en attente', nullable=False)
    departement = db.Column(db.Enum('Trading', 'Academy', 'Digital'), nullable=False)

# Décorateurs
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'role' in session and session['role'] == 'Administrator':
            return f(*args, **kwargs)
        else:
            return render_template('not_access.html')
    return wrapper

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'role' not in session:
                flash('Vous n\'avez pas les permissions pour accéder à cette page.', 'danger')
                return redirect(url_for('login'))

            user_role = session['role']
            if user_role in roles or user_role == 'Administrator':
                return f(*args, **kwargs)
            else:
                return render_template('not_access.html')
        return wrapper
    return decorator

# Utils
def init_db():
    """Initialise la base de données et crée l'utilisateur admin par défaut"""
    with app.app_context():
        db.create_all()
        
        # Créer l'utilisateur admin par défaut s'il n'existe pas
        existing_admin = Personnel.query.filter_by(username='admin', role='Administrator').first()
        if not existing_admin:
            admin = Personnel(
                nom='Administrateur',
                prenom='Administrateur',
                username='admin',
                email='sano-logistic@sano-logistic.com',
                phone='777777777',
                departement='Direction',
                date_arrivee=datetime.strptime('2025-01-01', '%Y-%m-%d').date(),
                date_depart=datetime.strptime('2025-01-01', '%Y-%m-%d').date(),
                ecole='SLC',
                convention='CDI',
                password=generate_password_hash('adminSLC123$'),
                role='Administrator',
                observations='Test'
            )
            db.session.add(admin)
            db.session.commit()

# Routes à ajouter à votre application Flask après les modèles

@app.route('/')
@login_required
def dashboard():
    # Statistiques générales
    total_personnel = Personnel.query.count()
    personnel_actifs = Personnel.query.filter(Personnel.date_depart.is_(None)).count()
    
    # Données pour les graphiques
    dept_stats = db.session.query(
        Personnel.departement,
        func.count(Personnel.id)
    ).group_by(Personnel.departement).all()
    
    convention_stats = db.session.query(
        Personnel.convention,
        func.count(Personnel.id)
    ).group_by(Personnel.convention).all()
    
    # Derniers personnels ajoutés
    recent_personnel = Personnel.query.order_by(Personnel.date_arrivee.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_personnel=total_personnel,
                         personnel_actifs=personnel_actifs,
                         dept_stats=dept_stats,
                         convention_stats=convention_stats,
                         recent_personnel=recent_personnel)

# TRADING
@app.route('/trading')
@login_required
@role_required('Trading')
def trading_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    query = Trading.query
    if search:
        query = query.filter(
            (Trading.nom_client.contains(search)) |
            (Trading.prenom_client.contains(search)) |
            (Trading.email_client.contains(search)) |
            (Trading.phone_client.contains(search)) |
            (Trading.type_libelle.contains(search)) |
            (Trading.items.contains(search))
        )
    tradings = query.paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('trading/list.html', tradings=tradings, search=search)

@app.route('/trading/create', methods=['GET', 'POST'])
@login_required
@role_required('Trading')
def trading_create():
    if request.method == 'POST':
        try:
            trading = Trading(
                date_const=datetime.strptime(request.form['date_const'], '%Y-%m-%d').date() if request.form.get('date_const') else None,
                personnel_id=session.get('id'),
                type_libelle=request.form.get('type_libelle'),
                nom_client=request.form.get('nom_client'),
                prenom_client=request.form.get('prenom_client'),
                phone_client=request.form.get('phone_client'),
                email_client=request.form.get('email_client'),
                items=request.form.get('items'),
                quantite=int(request.form['quantite']) if request.form.get('quantite') else None,
                prix_unit=float(request.form['prix_unit']) if request.form.get('prix_unit') else None,
                montant_ht=float(request.form['montant_ht']) if request.form.get('montant_ht') else None,
                tva=float(request.form['tva']) if request.form.get('tva') else None,
                montant_ttc=float(request.form['montant_ttc']) if request.form.get('montant_ttc') else None,
                modalite_paiement=request.form.get('modalite_paiement'),
                type_paiement=request.form.get('type_paiement', 'Especes'),
                observations=request.form.get('observations')
            )
            db.session.add(trading)
            db.session.commit()
            flash('Trading créé avec succès!', 'success')
            return redirect(url_for('trading_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du trading: {str(e)}', 'error')
    return render_template('trading/create.html')

@app.route('/trading/<int:id>')
@login_required
@role_required('Trading')
def trading_detail(id):
    trading = Trading.query.get_or_404(id)
    return render_template('trading/detail.html', trading=trading, datetime=datetime, timezone=timezone)

@app.route('/trading/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Trading')
def trading_edit(id):
    trading = Trading.query.get_or_404(id)
    if request.method == 'POST':
        try:
            trading.date_const = datetime.strptime(request.form['date_const'], '%Y-%m-%d').date() if request.form.get('date_const') else None
            trading.type_libelle = request.form.get('type_libelle')
            trading.nom_client = request.form.get('nom_client')
            trading.prenom_client = request.form.get('prenom_client')
            trading.phone_client = request.form.get('phone_client')
            trading.email_client = request.form.get('email_client')
            trading.items = request.form.get('items')
            trading.quantite = int(request.form['quantite']) if request.form.get('quantite') else None
            trading.prix_unit = float(request.form['prix_unit']) if request.form.get('prix_unit') else None
            trading.montant_ht = float(request.form['montant_ht']) if request.form.get('montant_ht') else None
            trading.tva = float(request.form['tva']) if request.form.get('tva') else None
            trading.montant_ttc = float(request.form['montant_ttc']) if request.form.get('montant_ttc') else None
            trading.modalite_paiement = request.form.get('modalite_paiement')
            trading.type_paiement = request.form.get('type_paiement', 'Especes')
            trading.observations = request.form.get('observations')
            db.session.commit()
            flash('Trading mis à jour avec succès!', 'success')
            return redirect(url_for('trading_detail', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour du trading: {str(e)}', 'error')
    return render_template('trading/edit.html', trading=trading)

@app.route('/trading/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def trading_delete(id):
    trading = Trading.query.get_or_404(id)
    try:
        db.session.delete(trading)
        db.session.commit()
        flash('Trading supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du trading: {str(e)}', 'error')
    return redirect(url_for('trading_list'))

# ACADEMY
@app.route('/academy')
@login_required
@role_required('Academy')
def academy_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    query = Academy.query
    if search:
        query = query.filter(
            (Academy.nom_client.contains(search)) |
            (Academy.prenom_client.contains(search)) |
            (Academy.email_client.contains(search)) |
            (Academy.phone_client.contains(search)) |
            (Academy.type_libelle.contains(search)) |
            (Academy.items.contains(search))
        )
    academies = query.paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('academy/list.html', academies=academies, search=search)

@app.route('/academy/create', methods=['GET', 'POST'])
@login_required
@role_required('Academy')
def academy_create():
    if request.method == 'POST':
        try:
            academy = Academy(
                date_const=datetime.strptime(request.form['date_const'], '%Y-%m-%d').date() if request.form.get('date_const') else None,
                personnel_id=session.get('id'),
                type_libelle=request.form.get('type_libelle'),
                nom_client=request.form.get('nom_client'),
                prenom_client=request.form.get('prenom_client'),
                phone_client=request.form.get('phone_client'),
                email_client=request.form.get('email_client'),
                items=request.form.get('items'),
                quantite=int(request.form['quantite']) if request.form.get('quantite') else None,
                prix_unit=float(request.form['prix_unit']) if request.form.get('prix_unit') else None,
                montant_ht=float(request.form['montant_ht']) if request.form.get('montant_ht') else None,
                tva=float(request.form['tva']) if request.form.get('tva') else None,
                montant_ttc=float(request.form['montant_ttc']) if request.form.get('montant_ttc') else None,
                modalite_paiement=request.form.get('modalite_paiement'),
                type_paiement=request.form.get('type_paiement', 'Especes'),
                observations=request.form.get('observations')
            )
            db.session.add(academy)
            db.session.commit()
            flash('Academy créé avec succès!', 'success')
            return redirect(url_for('academy_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de l\'academy: {str(e)}', 'error')
    return render_template('academy/create.html')

@app.route('/academy/<int:id>')
@login_required
@role_required('Academy')
def academy_detail(id):
    academy = Academy.query.get_or_404(id)
    return render_template('academy/detail.html', academy=academy, datetime=datetime, timezone=timezone)

@app.route('/academy/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Academy')
def academy_edit(id):
    academy = Academy.query.get_or_404(id)
    if request.method == 'POST':
        try:
            academy.date_const = datetime.strptime(request.form['date_const'], '%Y-%m-%d').date() if request.form.get('date_const') else None
            academy.type_libelle = request.form.get('type_libelle')
            academy.nom_client = request.form.get('nom_client')
            academy.prenom_client = request.form.get('prenom_client')
            academy.phone_client = request.form.get('phone_client')
            academy.email_client = request.form.get('email_client')
            academy.items = request.form.get('items')
            academy.quantite = int(request.form['quantite']) if request.form.get('quantite') else None
            academy.prix_unit = float(request.form['prix_unit']) if request.form.get('prix_unit') else None
            academy.montant_ht = float(request.form['montant_ht']) if request.form.get('montant_ht') else None
            academy.tva = float(request.form['tva']) if request.form.get('tva') else None
            academy.montant_ttc = float(request.form['montant_ttc']) if request.form.get('montant_ttc') else None
            academy.modalite_paiement = request.form.get('modalite_paiement')
            academy.type_paiement = request.form.get('type_paiement', 'Especes')
            academy.observations = request.form.get('observations')
            db.session.commit()
            flash('Academy mis à jour avec succès!', 'success')
            return redirect(url_for('academy_detail', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour de l\'academy: {str(e)}', 'error')
    return render_template('academy/edit.html', academy=academy)

@app.route('/academy/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def academy_delete(id):
    academy = Academy.query.get_or_404(id)
    try:
        db.session.delete(academy)
        db.session.commit()
        flash('Academy supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'academy: {str(e)}', 'error')
    return redirect(url_for('academy_list'))

# DIGITAL
@app.route('/digital')
@login_required
@role_required('Digital')
def digital_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    query = Digital.query
    if search:
        query = query.filter(
            (Digital.nom_client.contains(search)) |
            (Digital.prenom_client.contains(search)) |
            (Digital.email_client.contains(search)) |
            (Digital.phone_client.contains(search)) |
            (Digital.type_libelle.contains(search)) |
            (Digital.items.contains(search))
        )
    digitals = query.paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('digital/list.html', digitals=digitals, search=search)

@app.route('/digital/create', methods=['GET', 'POST'])
@login_required
@role_required('Digital')
def digital_create():
    if request.method == 'POST':
        try:
            digital = Digital(
                date_const=datetime.strptime(request.form['date_const'], '%Y-%m-%d').date() if request.form.get('date_const') else None,
                personnel_id=session.get('id'),
                type_libelle=request.form.get('type_libelle'),
                nom_client=request.form.get('nom_client'),
                prenom_client=request.form.get('prenom_client'),
                phone_client=request.form.get('phone_client'),
                email_client=request.form.get('email_client'),
                items=request.form.get('items'),
                quantite=int(request.form['quantite']) if request.form.get('quantite') else None,
                prix_unit=float(request.form['prix_unit']) if request.form.get('prix_unit') else None,
                montant_ht=float(request.form['montant_ht']) if request.form.get('montant_ht') else None,
                tva=float(request.form['tva']) if request.form.get('tva') else None,
                montant_ttc=float(request.form['montant_ttc']) if request.form.get('montant_ttc') else None,
                modalite_paiement=request.form.get('modalite_paiement'),
                type_paiement=request.form.get('type_paiement', 'Especes'),
                observations=request.form.get('observations')
            )
            db.session.add(digital)
            db.session.commit()
            flash('Digital créé avec succès!', 'success')
            return redirect(url_for('digital_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du digital: {str(e)}', 'error')
    return render_template('digital/create.html')

@app.route('/digital/<int:id>')
@login_required
@role_required('Digital')
def digital_detail(id):
    digital = Digital.query.get_or_404(id)
    return render_template('digital/detail.html', digital=digital, datetime=datetime, timezone=timezone)

@app.route('/digital/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Digital')
def digital_edit(id):
    digital = Digital.query.get_or_404(id)
    if request.method == 'POST':
        try:
            digital.date_const = datetime.strptime(request.form['date_const'], '%Y-%m-%d').date() if request.form.get('date_const') else None
            digital.type_libelle = request.form.get('type_libelle')
            digital.nom_client = request.form.get('nom_client')
            digital.prenom_client = request.form.get('prenom_client')
            digital.phone_client = request.form.get('phone_client')
            digital.email_client = request.form.get('email_client')
            digital.items = request.form.get('items')
            digital.quantite = int(request.form['quantite']) if request.form.get('quantite') else None
            digital.prix_unit = float(request.form['prix_unit']) if request.form.get('prix_unit') else None
            digital.montant_ht = float(request.form['montant_ht']) if request.form.get('montant_ht') else None
            digital.tva = float(request.form['tva']) if request.form.get('tva') else None
            digital.montant_ttc = float(request.form['montant_ttc']) if request.form.get('montant_ttc') else None
            digital.modalite_paiement = request.form.get('modalite_paiement')
            digital.type_paiement = request.form.get('type_paiement', 'Especes')
            digital.observations = request.form.get('observations')
            db.session.commit()
            flash('Digital mis à jour avec succès!', 'success')
            return redirect(url_for('digital_detail', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour du digital: {str(e)}', 'error')
    return render_template('digital/edit.html', digital=digital, datetime=datetime, timezone=timezone)

@app.route('/digital/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def digital_delete(id):
    digital = Digital.query.get_or_404(id)
    try:
        db.session.delete(digital)
        db.session.commit()
        flash('Digital supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du digital: {str(e)}', 'error')
    return redirect(url_for('digital_list'))

# MATERIELS
@app.route('/materiels')
@login_required
@role_required('Comptabilite')
def materiel_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    query = Materiel.query
    if search:
        query = query.filter(
            (Materiel.nom_produit.contains(search)) |
            (Materiel.fournisseur.contains(search))
        )
    materiels = query.paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('materiel/list.html', materiels=materiels, search=search)

@app.route('/materiel/create', methods=['GET', 'POST'])
@login_required
@role_required('Comptabilite')
def materiel_create():
    if request.method == 'POST':
        try:
            materiel = Materiel(
                nom_produit=request.form['nom_produit'],
                fournisseur=request.form.get('fournisseur'),
                date_sortie=datetime.strptime(request.form['date_sortie'], '%Y-%m-%d').date() if request.form.get('date_sortie') else None,
                date_reception=datetime.strptime(request.form['date_reception'], '%Y-%m-%d').date() if request.form.get('date_reception') else None,
                quantite=int(request.form['quantite']) if request.form.get('quantite') else None,
                prix_unit=float(request.form['prix_unit']) if request.form.get('prix_unit') else None,
                montant_ht=float(request.form['montant_ht']) if request.form.get('montant_ht') else None,
                tva=float(request.form['tva']) if request.form.get('tva') else None,
                montant_ttc=float(request.form['montant_ttc']) if request.form.get('montant_ttc') else None,
                observations=request.form.get('observations')
            )
            db.session.add(materiel)
            db.session.commit()
            flash('Matériel créé avec succès!', 'success')
            return redirect(url_for('materiel_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du matériel: {str(e)}', 'error')
    return render_template('materiel/create.html')

@app.route('/materiel/<int:id>')
@login_required
@role_required('Comptabilite')
def materiel_detail(id):
    materiel = Materiel.query.get_or_404(id)
    return render_template('materiel/detail.html', materiel=materiel, datetime=datetime, timezone=timezone)

@app.route('/materiel/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Comptabilite')
def materiel_edit(id):
    materiel = Materiel.query.get_or_404(id)
    if request.method == 'POST':
        try:
            materiel.nom_produit = request.form['nom_produit']
            materiel.fournisseur = request.form.get('fournisseur')
            materiel.date_sortie = datetime.strptime(request.form['date_sortie'], '%Y-%m-%d').date() if request.form.get('date_sortie') else None
            materiel.date_reception = datetime.strptime(request.form['date_reception'], '%Y-%m-%d').date() if request.form.get('date_reception') else None
            materiel.quantite = int(request.form['quantite']) if request.form.get('quantite') else None
            materiel.prix_unit = float(request.form['prix_unit']) if request.form.get('prix_unit') else None
            materiel.montant_ht = float(request.form['montant_ht']) if request.form.get('montant_ht') else None
            materiel.tva = float(request.form['tva']) if request.form.get('tva') else None
            materiel.montant_ttc = float(request.form['montant_ttc']) if request.form.get('montant_ttc') else None
            materiel.observations = request.form.get('observations')
            db.session.commit()
            flash('Matériel mis à jour avec succès!', 'success')
            return redirect(url_for('materiel_detail', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour du matériel: {str(e)}', 'error')
    return render_template('materiel/edit.html', materiel=materiel)

@app.route('/materiel/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def materiel_delete(id):
    materiel = Materiel.query.get_or_404(id)
    try:
        db.session.delete(materiel)
        db.session.commit()
        flash('Matériel supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du matériel: {str(e)}', 'error')
    return redirect(url_for('materiel_list'))

# FINANCES
@app.route('/finances')
@login_required
@role_required('Comptabilite')
def finance_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    query = Finance.query
    if search:
        query = query.filter(
            (Finance.libelle.contains(search)) | 
            (Finance.numero_compte.contains(search))
        )
    finances = query.paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('finance/list.html', finances=finances, search=search)

@app.route('/finance/create', methods=['GET', 'POST'])
@login_required
@role_required('Comptabilite')
def finance_create():
    if request.method == 'POST':
        try:
            finance = Finance(
                date=datetime.strptime(request.form['date'], '%Y-%m-%d').date() if request.form.get('date') else None,
                libelle=request.form.get('libelle'),
                numero_compte=request.form.get('numero_compte'),
                credit=float(request.form['credit']) if request.form.get('credit') else None,
                debit=float(request.form['debit']) if request.form.get('debit') else None,
                montant_ht=float(request.form['montant_ht']) if request.form.get('montant_ht') else None,
                tva=float(request.form['tva']) if request.form.get('tva') else None,
                montant_ttc=float(request.form['montant_ttc']) if request.form.get('montant_ttc') else None,
                observations=request.form.get('observations')
            )
            db.session.add(finance)
            db.session.commit()
            flash('Finance créée avec succès!', 'success')
            return redirect(url_for('finance_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de la finance: {str(e)}', 'error')
    return render_template('finance/create.html')

@app.route('/finance/<int:id>')
@login_required
@role_required('Comptabilite')
def finance_detail(id):
    finance = Finance.query.get_or_404(id)
    return render_template('finance/detail.html', finance=finance, datetime=datetime, timezone=timezone)

@app.route('/finance/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Comptabilite')
def finance_edit(id):
    finance = Finance.query.get_or_404(id)
    if request.method == 'POST':
        try:
            finance.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date() if request.form.get('date') else None
            finance.libelle = request.form.get('libelle')
            finance.numero_compte = request.form.get('numero_compte')
            finance.credit = float(request.form['credit']) if request.form.get('credit') else None
            finance.debit = float(request.form['debit']) if request.form.get('debit') else None
            finance.montant_ht = float(request.form['montant_ht']) if request.form.get('montant_ht') else None
            finance.tva = float(request.form['tva']) if request.form.get('tva') else None
            finance.montant_ttc = float(request.form['montant_ttc']) if request.form.get('montant_ttc') else None
            finance.observations = request.form.get('observations')
            db.session.commit()
            flash('Finance mise à jour avec succès!', 'success')
            return redirect(url_for('finance_detail', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour de la finance: {str(e)}', 'error')
    return render_template('finance/edit.html', finance=finance)

@app.route('/finance/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def finance_delete(id):
    finance = Finance.query.get_or_404(id)
    try:
        db.session.delete(finance)
        db.session.commit()
        flash('Finance supprimée avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de la finance: {str(e)}', 'error')
    return redirect(url_for('finance_list'))

# Personnels
@app.route('/personnels')
@login_required
@role_required('Administrator')
def personnel_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    departement = request.args.get('departement', '', type=str)
    
    query = Personnel.query
    
    if search:
        query = query.filter(
            (Personnel.nom.contains(search)) |
            (Personnel.prenom.contains(search)) |
            (Personnel.username.contains(search)) |
            (Personnel.email.contains(search))
        )
    
    if departement:
        query = query.filter(Personnel.departement == departement)
    
    personnel = query.paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('personnel/list.html', personnel=personnel, search=search, departement=departement)

@app.route('/personnel/create', methods=['GET', 'POST'])
@login_required
@admin_required
def personnel_create():
    if request.method == 'POST':
        try:
            # Vérification de l'unicité de l'username et email
            existing_username = Personnel.query.filter_by(username=request.form['username']).first()
            existing_email = Personnel.query.filter_by(email=request.form['email']).first()
            
            if existing_username:
                flash('Ce nom d\'utilisateur existe déjà.', 'error')
                return render_template('personnel/create.html')
            
            if existing_email:
                flash('Cette adresse email existe déjà.', 'error')
                return render_template('personnel/create.html')
            
            # Hashage du mot de passe
            hashed_password = generate_password_hash(request.form['password'])
            
            # Conversion des dates
            date_arrivee = None
            date_depart = None
            
            if request.form.get('date_arrivee'):
                date_arrivee = datetime.strptime(request.form['date_arrivee'], '%Y-%m-%d').date()
            
            if request.form.get('date_depart'):
                date_depart = datetime.strptime(request.form['date_depart'], '%Y-%m-%d').date()
            
            personnel = Personnel(
                nom=request.form['nom'],
                prenom=request.form['prenom'],
                username=request.form['username'],
                email=request.form['email'],
                phone=request.form.get('phone'),
                departement=request.form['departement'],
                date_arrivee=date_arrivee,
                date_depart=date_depart,
                ecole=request.form.get('ecole'),
                convention=request.form['convention'],
                password=hashed_password,
                role=request.form['role'],
                observations=request.form.get('observations')
            )
            
            db.session.add(personnel)
            db.session.commit()
            
            flash('Personnel créé avec succès!', 'success')
            return redirect(url_for('personnel_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création: {str(e)}', 'error')
    
    return render_template('personnel/create.html')

@app.route('/personnel/<int:id>')
@login_required
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
def personnel_detail(id):
    personnel = Personnel.query.get_or_404(id)
    return render_template('personnel/detail.html', personnel=personnel, datetime=datetime, timezone=timezone)

@app.route('/personnel/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def personnel_edit(id):
    personnel = Personnel.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Vérification de l'unicité de l'username et email (excluant l'utilisateur actuel)
            existing_username = Personnel.query.filter(
                Personnel.username == request.form['username'],
                Personnel.id != id
            ).first()
            
            existing_email = Personnel.query.filter(
                Personnel.email == request.form['email'],
                Personnel.id != id
            ).first()
            
            if existing_username:
                flash('Ce nom d\'utilisateur existe déjà.', 'error')
                return render_template('personnel/edit.html', personnel=personnel)
            
            if existing_email:
                flash('Cette adresse email existe déjà.', 'error')
                return render_template('personnel/edit.html', personnel=personnel)
            
            # Mise à jour des champs
            personnel.nom = request.form['nom']
            personnel.prenom = request.form['prenom']
            personnel.username = request.form['username']
            personnel.email = request.form['email']
            personnel.phone = request.form.get('phone')
            personnel.departement = request.form['departement']
            personnel.ecole = request.form.get('ecole')
            personnel.convention = request.form['convention']
            personnel.role = request.form['role']
            personnel.observations = request.form.get('observations')
            
            # Mise à jour du mot de passe si fourni
            if request.form.get('password'):
                personnel.password = generate_password_hash(request.form['password'])
            
            # Conversion des dates
            if request.form.get('date_arrivee'):
                personnel.date_arrivee = datetime.strptime(request.form['date_arrivee'], '%Y-%m-%d').date()
            else:
                personnel.date_arrivee = None
                
            if request.form.get('date_depart'):
                personnel.date_depart = datetime.strptime(request.form['date_depart'], '%Y-%m-%d').date()
            else:
                personnel.date_depart = None
            
            db.session.commit()
            flash('Personnel mis à jour avec succès!', 'success')
            return redirect(url_for('personnel_detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
    
    return render_template('personnel/edit.html', personnel=personnel)

@app.route('/personnel/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def personnel_delete(id):
    personnel = Personnel.query.get_or_404(id)
    
    try:
        db.session.delete(personnel)
        db.session.commit()
        flash('Personnel supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('personnel_list'))

#PROJETS
@app.route('/projets')
@login_required
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
def projet_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    departement = request.args.get('departement', '', type=str)
    query = Projet.query
    
    if search:
        query = query.filter(
            (Projet.nom.contains(search)) |
            (Projet.description.contains(search))
        )
    if departement:
        query = query.filter(Projet.departement == departement)
    
    projets = query.paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('projet/list.html', projets=projets, search=search, departement=departement)

@app.route('/projet/create', methods=['GET', 'POST'])
@login_required
@admin_required
def projet_create():
    if request.method == 'POST':
        try:
            projet = Projet(
                nom=request.form['nom'],
                description=request.form.get('description'),
                date_debut=datetime.strptime(request.form['date_debut'], '%Y-%m-%d').date(),
                date_fin=datetime.strptime(request.form['date_fin'], '%Y-%m-%d').date() if request.form.get('date_fin') else None,
                budget=float(request.form['budget']) if request.form.get('budget') else None,
                statut=request.form['statut'],
                departement=request.form['departement']
            )
            db.session.add(projet)
            db.session.commit()
            flash('Projet créé avec succès!', 'success')
            return redirect(url_for('projet_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du projet: {str(e)}', 'error')
    return render_template('projet/create.html')

@app.route('/projet/<int:id>')
@login_required
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
def projet_detail(id):
    projet = Projet.query.get_or_404(id)
    return render_template('projet/detail.html', projet=projet, datetime=datetime, timezone=timezone) 

@app.route('/projet/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def projet_edit(id):
    projet = Projet.query.get_or_404(id)
    if request.method == 'POST':
        try:
            projet.nom = request.form['nom']
            projet.description = request.form.get('description')
            projet.date_debut = datetime.strptime(request.form['date_debut'], '%Y-%m-%d').date()
            projet.date_fin = datetime.strptime(request.form['date_fin'], '%Y-%m-%d').date() if request.form.get('date_fin') else None
            projet.budget = float(request.form['budget']) if request.form.get('budget') else None
            projet.statut = request.form['statut']
            projet.departement = request.form['departement']
            db.session.commit()
            flash('Projet mis à jour avec succès!', 'success')
            return redirect(url_for('projet_detail', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour du projet: {str(e)}', 'error')
    return render_template('projet/edit.html', projet=projet, datetime=datetime, timezone=timezone)

@app.route('/projet/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def projet_delete(id):
    projet = Projet.query.get_or_404(id)
    try:
        db.session.delete(projet)
        db.session.commit()
        flash('Projet supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du projet: {str(e)}', 'error')
    return redirect(url_for('projet_list'))

# EVENEMENTIELS
@app.route('/evenementiels')
@login_required
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
def evenementiel_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    departement = request.args.get('departement', '', type=str)
    query = Evenementiel.query
    
    if search:
        query = query.filter(
            (Evenementiel.nom.contains(search)) |
            (Evenementiel.description.contains(search))
        )
    if departement:
        query = query.filter(Evenementiel.departement == departement)
    evenementiels = query.paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('evenementiel/list.html', evenementiels=evenementiels, search=search, departement=departement)

@app.route('/evenementiel/create', methods=['GET', 'POST'])
@login_required
@admin_required
def evenementiel_create():
    if request.method == 'POST':
        try:
            evenementiel = Evenementiel(
                nom=request.form['nom'],
                description=request.form.get('description'),
                date_debut=datetime.strptime(request.form['date_debut'], '%Y-%m-%d').date(),
                date_fin=datetime.strptime(request.form['date_fin'], '%Y-%m-%d').date() if request.form.get('date_fin') else None,
                budget=float(request.form['budget']) if request.form.get('budget') else None,
                statut=request.form['statut'],
                departement=request.form['departement']
            )
            db.session.add(evenementiel)
            db.session.commit()
            flash('Événement créé avec succès!', 'success')
            return redirect(url_for('evenementiel_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de l\'événement: {str(e)}', 'error')
    return render_template('evenementiel/create.html')

@app.route('/evenementiel/<int:id>')
@login_required
@role_required('Administrator', 'Trading', 'Academy', 'Digital')    
def evenementiel_detail(id):
    evenementiel = Evenementiel.query.get_or_404(id)
    return render_template('evenementiel/detail.html', evenementiel=evenementiel, datetime=datetime, timezone=timezone)

@app.route('/evenementiel/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def evenementiel_edit(id):
    evenementiel = Evenementiel.query.get_or_404(id)
    if request.method == 'POST':
        try:
            evenementiel.nom = request.form['nom']
            evenementiel.description = request.form.get('description')
            evenementiel.date_debut = datetime.strptime(request.form['date_debut'], '%Y-%m-%d').date()
            evenementiel.date_fin = datetime.strptime(request.form['date_fin'], '%Y-%m-%d').date() if request.form.get('date_fin') else None
            evenementiel.budget = float(request.form['budget']) if request.form.get('budget') else None
            evenementiel.statut = request.form['statut']
            evenementiel.departement = request.form['departement']
            db.session.commit()
            flash('Événement mis à jour avec succès!', 'success')
            return redirect(url_for('evenementiel_detail', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour de l\'événement: {str(e)}', 'error')
    return render_template('evenementiel/edit.html', evenementiel=evenementiel, datetime=datetime, timezone=timezone)

@app.route('/evenementiel/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def evenementiel_delete(id):
    evenementiel = Evenementiel.query.get_or_404(id)
    try:
        db.session.delete(evenementiel)
        db.session.commit()
        flash('Événement supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'événement: {str(e)}', 'error')
    return redirect(url_for('evenementiel_list'))

# Route de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        personnel = Personnel.query.filter_by(username=username).first()
        
        if personnel and check_password_hash(personnel.password, password):
            session['id'] = personnel.id
            session['username'] = personnel.username
            session['role'] = personnel.role
            session['nom'] = personnel.nom
            session['prenom'] = personnel.prenom
            
            flash('Connexion réussie!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('login'))

# API endpoint pour les données du dashboard
@app.route('/api/dashboard-data')
@login_required
def dashboard_data():
    dept_stats = db.session.query(
        Personnel.departement,
        func.count(Personnel.id)
    ).group_by(Personnel.departement).all()
    
    return jsonify({
        'departements': [{'name': dept, 'count': count} for dept, count in dept_stats]
    })

if __name__ == '__main__':
    init_db()  # Initialiser la base de données et l'utilisateur admin
    app.run(debug=True, host="0.0.0.0")