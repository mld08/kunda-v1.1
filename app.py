from functools import wraps
import io
import os
from flask import Flask, Response, render_template, jsonify, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import hashlib
import pandas as pd
from datetime import datetime, time, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

db = SQLAlchemy(app)
application = app
# Configuration des uploads
UPLOAD_FOLDER = 'uploads/rapports'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Créer le dossier d'uploads s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

class Facture(db.Model):
    __tablename__ = 'factures'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numero_facture = db.Column(db.String(50), unique=True, nullable=False)
    nom_client = db.Column(db.Text, nullable=False)
    adresse_client = db.Column(db.Text, nullable=True)
    telephone_client = db.Column(db.String(20), nullable=True)
    email_client = db.Column(db.String(100), nullable=True)
    quantite = db.Column(db.Integer, nullable=True)
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=True)
    montant_ht = db.Column(db.Numeric(10, 2), nullable=True)
    tva = db.Column(db.Numeric(10, 2), nullable=True)
    montant_ttc = db.Column(db.Numeric(10, 2), nullable=True)
    modalite_paiement = db.Column(db.String(50), nullable=True)
    date_facture = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).date())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).date(), onupdate=datetime.utcnow)
    observations = db.Column(db.Text, nullable=True)
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id', ondelete='CASCADE'), nullable=True)
    personnel = db.relationship('Personnel', backref='factures', lazy=True)

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id', ondelete='CASCADE'), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False)  # 'login', 'logout'
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    personnel = db.relationship('Personnel', backref='activities', lazy=True)

    def __repr__(self):
        return f'<UserActivity {self.personnel.username} - {self.activity_type} at {self.created_at}>'

class Journal(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).date())
    action = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id', ondelete='CASCADE'), nullable=True)
    personnel = db.relationship('Personnel', backref='journals', lazy=True)

class Rapport(db.Model):
    __tablename__ = 'rapports'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titre = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    nom_fichier = db.Column(db.String(255), nullable=False)
    chemin_fichier = db.Column(db.String(500), nullable=False)
    type_fichier = db.Column(db.String(10), nullable=False)  # 'pdf' ou 'docx'
    taille_fichier = db.Column(db.Integer, nullable=False)  # en bytes
    semaine_debut = db.Column(db.Date, nullable=False)
    semaine_fin = db.Column(db.Date, nullable=False)
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_modification = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=datetime.utcnow)
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id', ondelete='CASCADE'), nullable=False)
    statut = db.Column(db.Enum('brouillon', 'soumis', 'validé', 'rejeté'), default='brouillon', nullable=False)
    observations = db.Column(db.Text, nullable=True)
    
    # Relations
    personnel = db.relationship('Personnel', backref='rapports_hebdo', lazy=True)

class ProcesVerbal(db.Model):
    __tablename__ = 'proces_verbaux'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titre = db.Column(db.String(255), nullable=False)
    date_reunion = db.Column(db.Date, nullable=False)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=True)
    lieu = db.Column(db.String(255), nullable=True)
    ordre_du_jour = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    decisions_prises = db.Column(db.Text, nullable=True)
    actions_suivre = db.Column(db.Text, nullable=True)
    statut = db.Column(db.Enum('brouillon', 'validé', 'archivé'), default='brouillon', nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('personnels.id', ondelete='CASCADE'), nullable=False)
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_modification = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=datetime.utcnow)
    observations = db.Column(db.Text, nullable=True)
    
    # Relations
    createur = db.relationship('Personnel', foreign_keys=[created_by], backref='proces_verbaux_crees', lazy=True)
    participants = db.relationship('PVParticipant', backref='proces_verbal', lazy=True, cascade='all, delete-orphan')

class PVParticipant(db.Model):
    __tablename__ = 'pv_participants'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    proces_verbal_id = db.Column(db.Integer, db.ForeignKey('proces_verbaux.id', ondelete='CASCADE'), nullable=False)
    personnel_id = db.Column(db.Integer, db.ForeignKey('personnels.id', ondelete='CASCADE'), nullable=False)
    present = db.Column(db.Boolean, default=True, nullable=False)
    role_reunion = db.Column(db.String(100), nullable=True)  # Président, Secrétaire, Participant, etc.
    
    # Relations
    personnel = db.relationship('Personnel', backref='participations_pv', lazy=True)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'danger')
            return redirect(url_for('login'))
        
        # Vérification supplémentaire: s'assurer que l'utilisateur n'a pas de date de départ
        personnel = Personnel.query.get(session['id'])
        if personnel and personnel.date_depart is not None:
            session.clear()
            flash('Votre accès a été révoqué. Veuillez contacter l\'administrateur.', 'error')
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

# Fonction utilitaire pour enregistrer dans le journal
def log_activity(action, description, personnel_id=None):
    """Enregistre une activité dans la table Journal"""
    if personnel_id is None:
        personnel_id = session.get('id')
    
    journal = Journal(
        action=action,
        description=description,
        personnel_id=personnel_id
    )
    db.session.add(journal)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Routes à ajouter à votre application Flask après les modèles
@app.route('/')
@login_required
def dashboard():
    # Statistiques générales
    total_personnel = Personnel.query.count()
    personnel_actifs = Personnel.query.filter(Personnel.date_depart.is_(None)).count()
    personnel_inactifs = Personnel.query.filter(Personnel.date_depart.isnot(None)).count()
    
    # Statistiques des projets
    projets_en_cours = Projet.query.filter(Projet.statut == 'en cours').count()
    projets_termines = Projet.query.filter(Projet.statut == 'terminé').count()
    projets_total = Projet.query.count()
    
    # Statistiques des événements
    evenements_en_cours = Evenementiel.query.filter(Evenementiel.statut == 'en cours').count()
    evenements_total = Evenementiel.query.count()
    
    # Revenus par département (somme des montants TTC)
    revenus_trading = db.session.query(func.sum(Trading.montant_ttc)).scalar() or 0
    revenus_academy = db.session.query(func.sum(Academy.montant_ttc)).scalar() or 0
    revenus_digital = db.session.query(func.sum(Digital.montant_ttc)).scalar() or 0
    revenus_total = revenus_trading + revenus_academy + revenus_digital
    
    # Revenus du mois en cours
    premier_jour_mois = datetime.now().replace(day=1).date()
    revenus_mois_trading = db.session.query(func.sum(Trading.montant_ttc)).filter(
        Trading.date_const >= premier_jour_mois
    ).scalar() or 0
    revenus_mois_academy = db.session.query(func.sum(Academy.montant_ttc)).filter(
        Academy.date_const >= premier_jour_mois
    ).scalar() or 0
    revenus_mois_digital = db.session.query(func.sum(Digital.montant_ttc)).filter(
        Digital.date_const >= premier_jour_mois
    ).scalar() or 0
    revenus_mois = revenus_mois_trading + revenus_mois_academy + revenus_mois_digital
    
    # Statistiques par département
    dept_stats = db.session.query(
        Personnel.departement,
        func.count(Personnel.id)
    ).group_by(Personnel.departement).all()
    
    # Statistiques par convention
    convention_stats = db.session.query(
        Personnel.convention,
        func.count(Personnel.id)
    ).group_by(Personnel.convention).all()
    
    # Derniers personnels ajoutés (actifs seulement)
    recent_personnel = Personnel.query.filter(
        Personnel.date_depart.is_(None)
    ).order_by(Personnel.date_arrivee.desc()).limit(5).all()
    
    # Activités récentes du journal (10 dernières)
    recent_activities = Journal.query.join(Personnel).order_by(
        Journal.date.desc()
    ).limit(10).all()
    
    # Statistiques des connexions des 7 derniers jours
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    connexions_query = db.session.query(
        db.func.date(UserActivity.created_at).label('date'),
        db.func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.activity_type == 'login',
        UserActivity.created_at >= seven_days_ago
    ).group_by(
        db.func.date(UserActivity.created_at)
    ).order_by('date').all()

    # Créer un dictionnaire avec les jours de la semaine en français
    jours_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    connexions_par_jour = {}
    connexions_labels = []
    connexions_data = []
    
    for i in range(7):
        date = (datetime.now(timezone.utc) - timedelta(days=6-i)).date()
        jour_semaine = jours_fr[date.weekday()]  # weekday() retourne 0 pour lundi, 1 pour mardi, etc.
        connexions_par_jour[date.strftime('%Y-%m-%d')] = 0
        connexions_labels.append(jour_semaine)

    # Remplir avec les données réelles
    for date, count in connexions_query:
        connexions_par_jour[date.strftime('%Y-%m-%d')] = count
    
    # Créer la liste des données dans l'ordre
    for i in range(7):
        date = (datetime.now(timezone.utc) - timedelta(days=6-i)).date()
        date_str = date.strftime('%Y-%m-%d')
        connexions_data.append(connexions_par_jour.get(date_str, 0))

    # Top 5 des utilisateurs les plus actifs (par nombre d'activités)
    top_users = db.session.query(
        Personnel.nom,
        Personnel.prenom,
        Personnel.departement,
        func.count(Journal.id).label('activity_count')
    ).join(Journal).group_by(
        Personnel.id, Personnel.nom, Personnel.prenom, Personnel.departement
    ).order_by(func.count(Journal.id).desc()).limit(5).all()
    
    # Répartition des revenus par département
    revenus_par_dept = [
        {'departement': 'Trading', 'montant': revenus_trading},
        {'departement': 'Academy', 'montant': revenus_academy},
        {'departement': 'Digital', 'montant': revenus_digital}
    ]
    
    # Prochains événements (dans les 30 prochains jours)
    dans_30_jours = datetime.now().date() + timedelta(days=30)
    prochains_evenements = Evenementiel.query.filter(
        Evenementiel.date_debut >= datetime.now().date(),
        Evenementiel.date_debut <= dans_30_jours,
        Evenementiel.statut.in_(['en attente', 'en cours'])
    ).order_by(Evenementiel.date_debut).limit(5).all()

    # Utilisateurs connectés aujourd'hui
    aujourd_hui = datetime.now(timezone.utc).date()
    debut_journee = datetime.combine(aujourd_hui, time.min).replace(tzinfo=timezone.utc)
    fin_journee = datetime.combine(aujourd_hui, time.max).replace(tzinfo=timezone.utc)

    # Récupération des connexions d'aujourd'hui avec les informations utilisateur
    connexions_aujourd_hui = db.session.query(
        UserActivity.personnel_id,
        UserActivity.ip_address,
        UserActivity.created_at,
        Personnel.nom,
        Personnel.prenom,
        Personnel.departement
    ).join(
        Personnel, UserActivity.personnel_id == Personnel.id
    ).filter(
        UserActivity.activity_type == 'login',
        UserActivity.created_at >= debut_journee,
        UserActivity.created_at <= fin_journee
    ).order_by(
        UserActivity.created_at.desc()
    ).limit(10).all()

    # Formatage des données pour l'affichage
    utilisateurs_connectes_aujourd_hui = []
    for connexion in connexions_aujourd_hui:
        utilisateur = {
            'personnel_id': connexion.personnel_id,
            'ip_address': connexion.ip_address or 'Non disponible',
            'heure_connexion': connexion.created_at.strftime('%H:%M:%S'),
            'nom': connexion.nom,
            'prenom': connexion.prenom,
            'departement': connexion.departement,
            'datetime_connexion': connexion.created_at
        }
        utilisateurs_connectes_aujourd_hui.append(utilisateur)
    
    return render_template('dashboard.html',
                         # Statistiques de base
                         total_personnel=total_personnel,
                         personnel_actifs=personnel_actifs,
                         personnel_inactifs=personnel_inactifs,
                         
                         # Projets et événements
                         projets_en_cours=projets_en_cours,
                         projets_termines=projets_termines,
                         projets_total=projets_total,
                         evenements_en_cours=evenements_en_cours,
                         evenements_total=evenements_total,
                         
                         # Finances
                         revenus_total=revenus_total,
                         revenus_mois=revenus_mois,
                         revenus_par_dept=revenus_par_dept,
                         
                         # Graphiques
                         dept_stats=dept_stats,
                         convention_stats=convention_stats,
                         connexions_labels=connexions_labels,
                         connexions_data=connexions_data,
                         
                         # Listes
                         recent_personnel=recent_personnel,
                         recent_activities=recent_activities,
                         top_users=top_users,
                         prochains_evenements=prochains_evenements,
                         utilisateurs_connectes_aujourd_hui=utilisateurs_connectes_aujourd_hui)

@app.route('/journal')
@login_required
@admin_required
def journal_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    query = Journal.query
    if search:
        query = query.filter(
            (Journal.action.contains(search)) |
            (Journal.description.contains(search))
        )
    journals = query.paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('journal/list.html', journals=journals, search=search)

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
            db.session.flush()  # Pour obtenir l'ID du trading créé
            
            # Enregistrement dans le journal
            log_activity(
                action='CREATION_TRADING',
                description=f"Création d'un nouveau trading ID: {trading.id} - Client: {trading.nom_client} {trading.prenom_client}"
            )
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

            # Enregistrement dans le journal
            log_activity(
                action='MISE_A_JOUR_TRADING',
                description=f"Mise à jour du trading ID: {trading.id} - Client: {trading.nom_client} {trading.prenom_client}"
            )

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
        # Enregistrement dans le journal
        log_activity(
            action='SUPPRESSION_TRADING',
            description=f"Suppression du trading ID: {trading.id} - Client: {trading.nom_client} {trading.prenom_client}"
        )
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
            db.session.flush()  # Pour obtenir l'ID de l'academy créé
            # Enregistrement dans le journal
            log_activity(
                action='CREATION_ACADEMY',
                description=f"Création d'une nouvelle academy ID: {academy.id} - Client: {academy.nom_client} {academy.prenom_client}",
            )

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
            # Enregistrement dans le journal
            log_activity(
                action='MISE_A_JOUR_ACADEMY',
                description=f"Mise à jour de l'academy ID: {academy.id} - Client: {academy.nom_client} {academy.prenom_client}",
            )
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
        # Enregistrement dans le journal
        log_activity(
            action='SUPPRESSION_ACADEMY',
            description=f"Suppression de l'academy ID: {academy.id} - Client: {academy.nom_client} {academy.prenom_client}",
        )

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
            db.session.flush()  # Pour obtenir l'ID du digital créé
            # Enregistrement dans le journal
            log_activity(
                action='CREATION_DIGITAL',
                description=f"Création d'un nouveau digital ID: {digital.id} - Client: {digital.nom_client} {digital.prenom_client}",
            )

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
            # Enregistrement dans le journal
            log_activity(
                action='MISE_A_JOUR_DIGITAL',
                description=f"Mise à jour du digital ID: {digital.id} - Client: {digital.nom_client} {digital.prenom_client}",
            )
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
        # Enregistrement dans le journal
        log_activity(
            action='SUPPRESSION_DIGITAL',
            description=f"Suppression du digital ID: {digital.id} - Client: {digital.nom_client} {digital.prenom_client}",
        )
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
            db.session.flush()  # Pour obtenir l'ID du matériel créé
            # Enregistrement dans le journal
            log_activity(
                action='CREATION_MATERIEL',
                description=f"Création d'un nouveau matériel ID: {materiel.id} - Produit: {materiel.nom_produit}"
            )
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
            # Enregistrement dans le journal
            log_activity(
                action='MISE_A_JOUR_MATERIEL',
                description=f"Mise à jour du matériel ID: {materiel.id} - Produit: {materiel.nom_produit}"
            )
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
        # Enregistrement dans le journal
        log_activity(
            action='SUPPRESSION_MATERIEL',
            description=f"Suppression du matériel ID: {materiel.id} - Produit: {materiel.nom_produit}"
        )
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
            db.session.flush()  # Pour obtenir l'ID de la finance créée
            # Enregistrement dans le journal
            log_activity(
                action='CREATION_FINANCE',
                description=f"Création d'une nouvelle finance ID: {finance.id} - Libellé: {finance.libelle}"
            )
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
            # Enregistrement dans le journal
            log_activity(
                action='MISE_A_JOUR_FINANCE',
                description=f"Mise à jour de la finance ID: {finance.id} - Libellé: {finance.libelle}"
            )

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
        # Enregistrement dans le journal
        log_activity(
            action='SUPPRESSION_FINANCE',
            description=f"Suppression de la finance ID: {finance.id} - Libellé: {finance.libelle}"
        )
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
            db.session.flush()  # Pour obtenir l'ID du personnel créé
            # Enregistrement dans le journal
            log_activity(
                action='CREATION_PERSONNEL',
                description=f"Création d'un nouveau personnel ID: {personnel.id} - Nom: {personnel.nom} {personnel.prenom}",
            )
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
            
            # Enregistrement dans le journal
            log_activity(
                action='MISE_A_JOUR_PERSONNEL',
                description=f"Mise à jour du personnel ID: {personnel.id} - Nom: {personnel.nom} {personnel.prenom}",
            )
            
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
        # Enregistrement dans le journal
        log_activity(
            action='SUPPRESSION_PERSONNEL',
            description=f"Suppression du personnel ID: {personnel.id} - Nom: {personnel.nom} {personnel.prenom}",
        )
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
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
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
            db.session.flush()  # Pour obtenir l'ID du projet créé
            # Enregistrement dans le journal
            log_activity(
                action='CREATION_PROJET',
                description=f"Création d'un nouveau projet ID: {projet.id} - Nom: {projet.nom}",
            )
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
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
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
            # Enregistrement dans le journal
            log_activity(
                action='MISE_A_JOUR_PROJET',
                description=f"Mise à jour du projet ID: {projet.id} - Nom: {projet.nom}",
            )
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
        # Enregistrement dans le journal
        log_activity(
            action='SUPPRESSION_PROJET',
            description=f"Suppression du projet ID: {projet.id} - Nom: {projet.nom}",
        )
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
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
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
            db.session.flush()  # Pour obtenir l'ID de l'événement créé
            # Enregistrement dans le journal
            log_activity(
                action='CREATION_EVENEMENTIEL',
                description=f"Création d'un nouvel événement ID: {evenementiel.id} - Nom: {evenementiel.nom}",
            )
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
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
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
            # Enregistrement dans le journal
            log_activity(
                action='MISE_A_JOUR_EVENEMENTIEL',
                description=f"Mise à jour de l'événement ID: {evenementiel.id} - Nom: {evenementiel.nom}",
            )
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
        # Enregistrement dans le journal
        log_activity(
            action='SUPPRESSION_EVENEMENTIEL',
            description=f"Suppression de l'événement ID: {evenementiel.id} - Nom: {evenementiel.nom}",
        )
        db.session.delete(evenementiel)
        db.session.commit()
        flash('Événement supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'événement: {str(e)}', 'error')
    return redirect(url_for('evenementiel_list'))

# Routes pour la gestion des rapports
@app.route('/rapports')
@login_required
def rapport_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    # Chaque utilisateur ne voit que ses propres rapports (sauf admin)
    if session['role'] == 'Administrator':
        query = Rapport.query.join(Personnel)
    else:
        query = Rapport.query.filter(Rapport.personnel_id == session['id'])
    
    if search:
        if session['role'] == 'Administrator':
            query = query.filter(
                (Rapport.titre.contains(search)) |
                (Rapport.description.contains(search)) |
                (Personnel.nom.contains(search)) |
                (Personnel.prenom.contains(search))
            )
        else:
            query = query.filter(
                (Rapport.titre.contains(search)) |
                (Rapport.description.contains(search))
            )
    
    rapports = query.order_by(Rapport.date_creation.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('rapport/list.html', rapports=rapports, search=search)

@app.route('/rapport/create', methods=['GET', 'POST'])
@login_required
def rapport_create():
    if request.method == 'POST':
        try:
            # Vérification du fichier
            if 'fichier' not in request.files:
                flash('Aucun fichier sélectionné', 'error')
                return render_template('rapport/create.html')
            
            file = request.files['fichier']
            if file.filename == '':
                flash('Aucun fichier sélectionné', 'error')
                return render_template('rapport/create.html')
            
            if not allowed_file(file.filename):
                flash('Type de fichier non autorisé. Seuls les fichiers PDF, DOC et DOCX sont acceptés.', 'error')
                return render_template('rapport/create.html')
            
            # Vérification de la taille du fichier
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                flash('Le fichier est trop volumineux (maximum 16MB)', 'error')
                return render_template('rapport/create.html')
            
            # Génération d'un nom de fichier sécurisé
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{session['id']}_{timestamp}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # Sauvegarde du fichier
            file.save(file_path)
            
            # Création de l'enregistrement
            rapport = Rapport(
                titre=request.form['titre'],
                description=request.form.get('description'),
                nom_fichier=file.filename,
                chemin_fichier=file_path,
                type_fichier=filename.rsplit('.', 1)[1].lower(),
                taille_fichier=file_size,
                semaine_debut=datetime.strptime(request.form['semaine_debut'], '%Y-%m-%d').date(),
                semaine_fin=datetime.strptime(request.form['semaine_fin'], '%Y-%m-%d').date(),
                personnel_id=session['id'],
                statut=request.form.get('statut', 'brouillon'),
                observations=request.form.get('observations')
            )
            
            db.session.add(rapport)
            db.session.flush()
            
            # Enregistrement dans le journal
            log_activity(
                action='CREATION_RAPPORT',
                description=f"Création d'un nouveau rapport ID: {rapport.id} - Titre: {rapport.titre}"
            )
            
            db.session.commit()
            flash('Rapport ajouté avec succès!', 'success')
            return redirect(url_for('rapport_list'))
            
        except Exception as e:
            db.session.rollback()
            # Supprimer le fichier en cas d'erreur
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            flash(f'Erreur lors de l\'ajout du rapport: {str(e)}', 'error')
    
    return render_template('rapport/create.html')

@app.route('/rapport/<int:id>')
@login_required
def rapport_detail(id):
    rapport = Rapport.query.get_or_404(id)
    
    # Vérification des droits d'accès
    if session['role'] != 'Administrator' and rapport.personnel_id != session['id']:
        return render_template('not_access.html')
    
    return render_template('rapport/detail.html', rapport=rapport)

@app.route('/rapport/<int:id>/download')
@login_required
def rapport_download(id):
    rapport = Rapport.query.get_or_404(id)
    
    # Vérification des droits d'accès
    if session['role'] != 'Administrator' and rapport.personnel_id != session['id']:
        return render_template('not_access.html')
    
    if not os.path.exists(rapport.chemin_fichier):
        flash('Fichier introuvable', 'error')
        return redirect(url_for('rapport_detail', id=id))
    
    return send_file(
        rapport.chemin_fichier,
        as_attachment=True,
        download_name=rapport.nom_fichier
    )

@app.route('/rapport/bulk-action', methods=['POST'])
@login_required
def rapport_bulk_action():
    """Actions en lot sur plusieurs rapports"""
    if session['role'] != 'Administrator':
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    action = request.json.get('action')
    rapport_ids = request.json.get('rapports', [])
    
    if not rapport_ids:
        return jsonify({'error': 'Aucun rapport sélectionné'}), 400
    
    try:
        rapports = Rapport.query.filter(Rapport.id.in_(rapport_ids)).all()
        
        if action == 'delete':
            for rapport in rapports:
                # Supprimer le fichier physique
                if os.path.exists(rapport.chemin_fichier):
                    os.remove(rapport.chemin_fichier)
                
                log_activity(
                    action='SUPPRESSION_BULK_RAPPORT',
                    description=f"Suppression en lot du rapport ID: {rapport.id}"
                )
                
                db.session.delete(rapport)
        
        elif action == 'validate':
            for rapport in rapports:
                rapport.statut = 'validé'
                rapport.date_modification = datetime.now(timezone.utc)
                
                log_activity(
                    action='VALIDATION_BULK_RAPPORT',
                    description=f"Validation en lot du rapport ID: {rapport.id}"
                )
        
        elif action == 'reject':
            observations = request.json.get('observations', 'Rejeté en lot')
            for rapport in rapports:
                rapport.statut = 'rejeté'
                rapport.observations = observations
                rapport.date_modification = datetime.now(timezone.utc)
                
                log_activity(
                    action='REJET_BULK_RAPPORT',
                    description=f"Rejet en lot du rapport ID: {rapport.id}"
                )
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Action "{action}" appliquée à {len(rapports)} rapport(s)'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/rapport/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def rapport_edit(id):
    rapport = Rapport.query.get_or_404(id)
    
    # Vérification des droits d'accès
    if session['role'] != 'Administrator' and rapport.personnel_id != session['id']:
        return render_template('not_access.html')
    
    if request.method == 'POST':
        try:
            old_file_path = rapport.chemin_fichier
            
            # Mise à jour des informations de base
            rapport.titre = request.form['titre']
            rapport.description = request.form.get('description')
            rapport.semaine_debut = datetime.strptime(request.form['semaine_debut'], '%Y-%m-%d').date()
            rapport.semaine_fin = datetime.strptime(request.form['semaine_fin'], '%Y-%m-%d').date()
            rapport.observations = request.form.get('observations')
            rapport.date_modification = datetime.now(timezone.utc)
            
            # Seul l'admin peut changer le statut
            if session['role'] == 'Administrator':
                rapport.statut = request.form.get('statut', rapport.statut)
            
            # Vérification s'il y a un nouveau fichier
            if 'fichier' in request.files and request.files['fichier'].filename != '':
                file = request.files['fichier']
                
                if not allowed_file(file.filename):
                    flash('Type de fichier non autorisé.', 'error')
                    return render_template('rapport/edit.html', rapport=rapport)
                
                # Vérification de la taille
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    flash('Le fichier est trop volumineux (maximum 16MB)', 'error')
                    return render_template('rapport/edit.html', rapport=rapport)
                
                # Suppression de l'ancien fichier
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                
                # Sauvegarde du nouveau fichier
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{session['id']}_{timestamp}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                # Mise à jour des informations du fichier
                rapport.nom_fichier = file.filename
                rapport.chemin_fichier = file_path
                rapport.type_fichier = filename.rsplit('.', 1)[1].lower()
                rapport.taille_fichier = file_size
            
            # Enregistrement dans le journal
            log_activity(
                action='MISE_A_JOUR_RAPPORT',
                description=f"Mise à jour du rapport ID: {rapport.id} - Titre: {rapport.titre}"
            )
            
            db.session.commit()
            flash('Rapport mis à jour avec succès!', 'success')
            return redirect(url_for('rapport_detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
    
    return render_template('rapport/edit.html', rapport=rapport)

@app.route('/rapport/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def rapport_delete(id):
    rapport = Rapport.query.get_or_404(id)
    
    # Vérification des droits d'accès (seul l'admin ou le propriétaire peut supprimer)
    if session['role'] != 'Administrator' and rapport.personnel_id != session['id']:
        return render_template('not_access.html')
    
    try:
        # Suppression du fichier physique
        if os.path.exists(rapport.chemin_fichier):
            os.remove(rapport.chemin_fichier)
        
        # Enregistrement dans le journal
        log_activity(
            action='SUPPRESSION_RAPPORT',
            description=f"Suppression du rapport ID: {rapport.id} - Titre: {rapport.titre}"
        )
        
        db.session.delete(rapport)
        db.session.commit()
        flash('Rapport supprimé avec succès!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('rapport_list'))

@app.route('/proces-verbaux')
@login_required
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
def proces_verbal_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    statut = request.args.get('statut', '', type=str)
    
    query = ProcesVerbal.query.join(Personnel, ProcesVerbal.created_by == Personnel.id)
    
    if search:
        query = query.filter(
            (ProcesVerbal.titre.contains(search)) |
            (ProcesVerbal.ordre_du_jour.contains(search)) |
            (ProcesVerbal.lieu.contains(search)) |
            (Personnel.nom.contains(search)) |
            (Personnel.prenom.contains(search))
        )
    
    if statut:
        query = query.filter(ProcesVerbal.statut == statut)
    
    proces_verbaux = query.order_by(ProcesVerbal.date_reunion.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('proces_verbal/list.html', 
                         proces_verbaux=proces_verbaux, 
                         search=search, 
                         statut=statut)

@app.route('/proces-verbal/create', methods=['GET', 'POST'])
@login_required
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
def proces_verbal_create():
    if request.method == 'POST':
        try:
            # Création du procès-verbal
            pv = ProcesVerbal(
                titre=request.form['titre'],
                date_reunion=datetime.strptime(request.form['date_reunion'], '%Y-%m-%d').date(),
                heure_debut=datetime.strptime(request.form['heure_debut'], '%H:%M').time(),
                heure_fin=datetime.strptime(request.form['heure_fin'], '%H:%M').time() if request.form.get('heure_fin') else None,
                lieu=request.form.get('lieu'),
                ordre_du_jour=request.form['ordre_du_jour'],
                description=request.form.get('description'),
                decisions_prises=request.form.get('decisions_prises'),
                actions_suivre=request.form.get('actions_suivre'),
                statut=request.form.get('statut', 'brouillon'),
                created_by=session['id'],
                observations=request.form.get('observations')
            )
            
            db.session.add(pv)
            db.session.flush()  # Pour obtenir l'ID
            
            # Ajouter les participants
            participants_ids = request.form.getlist('participants')
            roles_reunion = request.form.getlist('roles_reunion')
            presents = request.form.getlist('presents')
            
            for i, participant_id in enumerate(participants_ids):
                if participant_id:  # Vérifier que l'ID n'est pas vide
                    participant = PVParticipant(
                        proces_verbal_id=pv.id,
                        personnel_id=int(participant_id),
                        present=str(participant_id) in presents,
                        role_reunion=roles_reunion[i] if i < len(roles_reunion) else None
                    )
                    db.session.add(participant)
            
            # Enregistrement dans le journal
            log_activity(
                action='CREATION_PROCES_VERBAL',
                description=f"Création d'un nouveau procès-verbal ID: {pv.id} - Titre: {pv.titre}"
            )
            
            db.session.commit()
            flash('Procès-verbal créé avec succès!', 'success')
            return redirect(url_for('proces_verbal_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du procès-verbal: {str(e)}', 'error')
    
    # Récupérer la liste du personnel actif pour le formulaire
    personnel_actif = Personnel.query.filter(Personnel.date_depart.is_(None)).order_by(Personnel.nom, Personnel.prenom).all()
    
    return render_template('proces_verbal/create.html', personnel_actif=personnel_actif)

@app.route('/proces-verbal/<int:id>')
@login_required
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
def proces_verbal_detail(id):
    pv = ProcesVerbal.query.get_or_404(id)
    
    # Récupérer les participants avec leurs informations
    participants = db.session.query(PVParticipant, Personnel).join(
        Personnel, PVParticipant.personnel_id == Personnel.id
    ).filter(PVParticipant.proces_verbal_id == id).all()
    
    return render_template('proces_verbal/detail.html', pv=pv, participants=participants)

@app.route('/proces-verbal/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Administrator', 'Trading', 'Academy', 'Digital')
def proces_verbal_edit(id):
    pv = ProcesVerbal.query.get_or_404(id)
    
    # Vérification des droits (seul le créateur ou admin peut modifier)
    if session['role'] != 'Administrator' and pv.created_by != session['id']:
        return render_template('not_access.html')
    
    if request.method == 'POST':
        try:
            # Mise à jour des informations de base
            pv.titre = request.form['titre']
            pv.date_reunion = datetime.strptime(request.form['date_reunion'], '%Y-%m-%d').date()
            pv.heure_debut = datetime.strptime(request.form['heure_debut'], '%H:%M').time()
            pv.heure_fin = datetime.strptime(request.form['heure_fin'], '%H:%M').time() if request.form.get('heure_fin') else None
            pv.lieu = request.form.get('lieu')
            pv.ordre_du_jour = request.form['ordre_du_jour']
            pv.description = request.form.get('description')
            pv.decisions_prises = request.form.get('decisions_prises')
            pv.actions_suivre = request.form.get('actions_suivre')
            pv.observations = request.form.get('observations')
            pv.date_modification = datetime.now(timezone.utc)
            
            # Seul l'admin peut changer le statut
            if session['role'] == 'Administrator':
                pv.statut = request.form.get('statut', pv.statut)
            
            # Supprimer les anciens participants
            PVParticipant.query.filter_by(proces_verbal_id=pv.id).delete()
            
            # Ajouter les nouveaux participants
            participants_ids = request.form.getlist('participants')
            roles_reunion = request.form.getlist('roles_reunion')
            presents = request.form.getlist('presents')
            
            for i, participant_id in enumerate(participants_ids):
                if participant_id:
                    participant = PVParticipant(
                        proces_verbal_id=pv.id,
                        personnel_id=int(participant_id),
                        present=str(participant_id) in presents,
                        role_reunion=roles_reunion[i] if i < len(roles_reunion) else None
                    )
                    db.session.add(participant)
            
            # Enregistrement dans le journal
            log_activity(
                action='MISE_A_JOUR_PROCES_VERBAL',
                description=f"Mise à jour du procès-verbal ID: {pv.id} - Titre: {pv.titre}"
            )
            
            db.session.commit()
            flash('Procès-verbal mis à jour avec succès!', 'success')
            return redirect(url_for('proces_verbal_detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
    
    # Récupérer les données pour le formulaire
    personnel_actif = Personnel.query.filter(Personnel.date_depart.is_(None)).order_by(Personnel.nom, Personnel.prenom).all()
    participants_actuels = PVParticipant.query.filter_by(proces_verbal_id=id).all()
    
    return render_template('proces_verbal/edit.html', 
                         pv=pv, 
                         personnel_actif=personnel_actif,
                         participants_actuels=participants_actuels)

@app.route('/proces-verbal/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def proces_verbal_delete(id):
    pv = ProcesVerbal.query.get_or_404(id)
    try:
        # Enregistrement dans le journal
        log_activity(
            action='SUPPRESSION_PROCES_VERBAL',
            description=f"Suppression du procès-verbal ID: {pv.id} - Titre: {pv.titre}"
        )
        
        db.session.delete(pv)
        db.session.commit()
        flash('Procès-verbal supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du procès-verbal: {str(e)}', 'error')
    
    return redirect(url_for('proces_verbal_list'))

@app.route('/api/personnel-search')
@login_required
def personnel_search():
    """API pour la recherche de personnel (utilisée dans le formulaire de création)"""
    term = request.args.get('term', '')
    
    personnel = Personnel.query.filter(
        Personnel.date_depart.is_(None),  # Seulement le personnel actif
        (Personnel.nom.contains(term)) | 
        (Personnel.prenom.contains(term)) |
        (Personnel.username.contains(term))
    ).limit(10).all()
    
    results = []
    for p in personnel:
        results.append({
            'id': p.id,
            'text': f"{p.nom} {p.prenom} ({p.departement})",
            'departement': p.departement,
            'role': p.role
        })
    
    return jsonify(results)

# Route de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        personnel = Personnel.query.filter_by(username=username).first()
        
        if personnel and check_password_hash(personnel.password, password):
            # Vérifier si le personnel a une date de départ
            if personnel.date_depart is not None:
                flash('Accès refusé. Votre compte a été désactivé.', 'error')
                return render_template('login.html')
            
            session['id'] = personnel.id
            session['username'] = personnel.username
            session['role'] = personnel.role
            session['nom'] = personnel.nom
            session['prenom'] = personnel.prenom
            
            # Enregistrer l'activité de connexion
            activity = UserActivity(
                personnel_id=personnel.id,  # Correction: utiliser personnel_id au lieu de user_id
                activity_type='login',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500]
            )
            db.session.add(activity)
            db.session.commit()
            
            flash(f'Connexion réussie! Bienvenue {personnel.username}', 'success')
            session.permanent = True
            
            return redirect(url_for('dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
    
    return render_template('login.html')

# Route de déconnexion modifiée
@app.route('/logout')
def logout():
    # Enregistrer l'activité de déconnexion si l'utilisateur est connecté
    if 'id' in session:  # Correction: utiliser 'id' au lieu de 'user_id'
        activity = UserActivity(
            personnel_id=session['id'],  # Correction: utiliser personnel_id
            activity_type='logout',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )
        db.session.add(activity)
        db.session.commit()

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