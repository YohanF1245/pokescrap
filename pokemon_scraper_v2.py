import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
import logging
import traceback
from datetime import datetime
from urllib.parse import urljoin, urlparse
from database_v2 import DatabaseManagerV2

# ✅ NOUVEAU : Configuration du logging
def setup_logging():
    """Configure le système de logging avec fichier et console."""
    # Créer le dossier logs si nécessaire
    os.makedirs("logs", exist_ok=True)
    
    # Configuration du logger principal
    logger = logging.getLogger('pokemon_scraper')
    logger.setLevel(logging.DEBUG)
    
    # Supprimer les handlers existants pour éviter les doublons
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler pour fichier avec rotation par date
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(f'logs/scraping_{timestamp}.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Handler pour console (moins verbeux)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Format détaillé pour fichier
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Format simple pour console
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class PokemonScraperV2:
    def __init__(self):
        self.base_url = "https://www.pokebip.com"
        self.db = DatabaseManagerV2("pokemon_shasse_v2.db")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # ✅ NOUVEAU : Initialiser le logging
        self.logger = setup_logging()
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'error_types': {},
            'start_time': datetime.now()
        }
        
        # Créer le dossier assets si il n'existe pas
        os.makedirs("assets", exist_ok=True)
        for gen in range(1, 10):
            os.makedirs(f"assets/gen_{gen}", exist_ok=True)
        
        self.logger.info("=== NOUVEAU SCRAPING SESSION DÉMARRÉ ===")
        self.logger.info(f"Base URL: {self.base_url}")
        self.logger.info(f"Base de données: pokemon_shasse_v2.db")
    
    def log_error(self, error_type: str, pokemon_name: str, generation: int, url: str, exception: Exception, context: str = ""):
        """Log une erreur de manière détaillée."""
        self.stats['error_count'] += 1
        self.stats['error_types'][error_type] = self.stats['error_types'].get(error_type, 0) + 1
        
        error_msg = f"ERREUR {error_type.upper()}"
        error_msg += f" | Pokemon: {pokemon_name} (Gen {generation})"
        error_msg += f" | URL: {url}"
        if context:
            error_msg += f" | Contexte: {context}"
        error_msg += f" | Exception: {str(exception)}"
        
        self.logger.error(error_msg)
        self.logger.debug(f"Stack trace pour {pokemon_name}:\n{traceback.format_exc()}")
    
    def log_success(self, pokemon_name: str, generation: int, details: dict):
        """Log un succès avec détails."""
        self.stats['success_count'] += 1
        
        success_msg = f"SUCCÈS | Pokemon: {pokemon_name} (Gen {generation})"
        success_msg += f" | Sprite: {'✅' if details.get('sprite_downloaded') else '❌'}"
        success_msg += f" | Image HQ: {'✅' if details.get('hq_image_downloaded') else '❌'}"
        success_msg += f" | Méthodes: {details.get('methods_count', 0)}"
        success_msg += f" | Jeux: {details.get('games_count', 0)}"
        
        self.logger.info(success_msg)
    
    def log_stats(self):
        """Log les statistiques finales."""
        duration = datetime.now() - self.stats['start_time']
        total = self.stats['total_processed']
        success = self.stats['success_count']
        errors = self.stats['error_count']
        success_rate = (success / total * 100) if total > 0 else 0
        
        self.logger.info("=== STATISTIQUES FINALES ===")
        self.logger.info(f"Durée totale: {duration}")
        self.logger.info(f"Pokemon traités: {total}")
        self.logger.info(f"Succès: {success} ({success_rate:.1f}%)")
        self.logger.info(f"Erreurs: {errors} ({100-success_rate:.1f}%)")
        
        if self.stats['error_types']:
            self.logger.info("=== RÉPARTITION DES ERREURS ===")
            for error_type, count in sorted(self.stats['error_types'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / errors * 100) if errors > 0 else 0
                self.logger.info(f"{error_type}: {count} ({percentage:.1f}%)")
    
    def get_page(self, url):
        """Récupère le contenu d'une page web avec gestion des erreurs et logging."""
        try:
            self.logger.debug(f"Récupération de l'URL: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            self.logger.debug(f"Page récupérée avec succès: {len(response.text)} caractères")
            return response.text
        except requests.exceptions.Timeout as e:
            self.logger.warning(f"Timeout pour {url}: {e}")
            raise
        except requests.exceptions.HTTPError as e:
            self.logger.warning(f"Erreur HTTP {response.status_code} pour {url}: {e}")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Erreur réseau pour {url}: {e}")
            raise
    
    def sanitize_filename(self, filename):
        """Nettoie un nom de fichier pour qu'il soit compatible avec le système de fichiers."""
        # Remplacer les caractères problématiques
        replacements = {
            '♀': 'F', '♂': 'M', 'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a', 'ç': 'c', 'î': 'i', 'ï': 'i',
            'ô': 'o', 'ö': 'o', 'ù': 'u', 'û': 'u', 'ü': 'u', 'ÿ': 'y',
            '.': '', ':': '', '?': '', '!': '', '/': '_', '\\': '_',
            '<': '_', '>': '_', '|': '_', '*': '_', '"': '_', ' ': '_', '-': '_'
        }
        
        for old, new in replacements.items():
            filename = filename.replace(old, new)
        
        # Supprimer les underscores multiples
        filename = re.sub(r'_+', '_', filename).strip('_')
        
        # Limiter la longueur
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename

    def extract_pokemon_number_from_text(self, text):
        """Extrait le numéro du Pokémon depuis le texte."""
        match = re.search(r'#(\d+)', text)
        if match:
            return int(match.group(1))
        return None
    
    def extract_pokemon_number_from_sprite_url(self, sprite_url):
        """Extrait le numéro du Pokémon depuis l'URL du sprite."""
        if not sprite_url:
            return None
        patterns = [r'/NG/(\d+)\.png', r'/(\d+)\.png', r'/(\d+)_', r'(\d+)\.png']
        
        for pattern in patterns:
            match = re.search(pattern, sprite_url)
            if match:
                return int(match.group(1))
        return None

    def download_sprite(self, pokemon_name, generation, pokemon_number):
        """Télécharge le sprite d'un Pokemon avec logging détaillé."""
        sprite_url = None
        try:
            self.logger.debug(f"Début téléchargement sprite pour {pokemon_name}")
            
            # Construire l'URL du sprite
            sprite_url = self.build_sprite_url(pokemon_name, generation, pokemon_number)
            if not sprite_url:
                self.logger.warning(f"Impossible de construire l'URL du sprite pour {pokemon_name}")
                return None
            
            # Créer le nom du fichier
            if pokemon_number:
                filename = f"{pokemon_number:03d}_{pokemon_name}.png"
            else:
                filename = f"XXX_{pokemon_name}.png"
                
            # Créer le répertoire pour cette génération
            gen_dir = f"assets/gen_{generation}"
            os.makedirs(gen_dir, exist_ok=True)
            
            # Chemin complet du fichier
            sprite_path = os.path.join(gen_dir, filename)
            
            # Vérifier si le fichier existe déjà
            if os.path.exists(sprite_path):
                self.logger.debug(f"Sprite existe déjà: {sprite_path}")
                return sprite_path
            
            # Télécharger le sprite
            self.logger.debug(f"Téléchargement depuis: {sprite_url}")
            response = self.session.get(sprite_url, timeout=10)
            
            if response.status_code == 200:
                with open(sprite_path, 'wb') as f:
                    f.write(response.content)
                self.logger.debug(f"Sprite sauvegardé: {sprite_path} ({len(response.content)} bytes)")
                return sprite_path
            else:
                self.logger.warning(f"Erreur HTTP {response.status_code} pour sprite {sprite_url}")
                return None
                
        except Exception as e:
            if sprite_url:
                self.log_error("SPRITE_DOWNLOAD", pokemon_name, generation, sprite_url, e, 
                             f"Tentative téléchargement sprite")
            else:
                self.logger.error(f"Erreur construction URL sprite pour {pokemon_name}: {e}")
            return None
    
    def build_sprite_url(self, pokemon_name, generation, pokemon_number):
        """Construit l'URL du sprite à partir du nom du Pokemon."""
        try:
            # Construire l'URL basée sur le numéro si disponible
            if pokemon_number:
                sprite_url = f"https://www.pokebip.com/pages/icones/minichroma/NG/{pokemon_number}.png"
            else:
                # Fallback : essayer avec le nom normalisé
                normalized_name = self.normalize_pokemon_name_for_url(pokemon_name)
                sprite_url = f"https://www.pokebip.com/pages/icones/minichroma/NG/{normalized_name}.png"
            
            return sprite_url
            
        except Exception as e:
            print(f"    ❌ Erreur construction URL sprite: {e}")
            return None

    def build_pokemon_details_url(self, pokemon_name, generation):
        """Construit l'URL des détails d'un Pokemon."""
        try:
            # Normaliser le nom pour l'URL
            normalized_name = self.normalize_pokemon_name_for_url(pokemon_name)
            
            # Construire l'URL
            details_url = f"https://www.pokebip.com/page/jeuxvideo/dossier_shasse/pokedex_shasse/{generation}g/{normalized_name}"
            
            return details_url
            
        except Exception as e:
            print(f"    ❌ Erreur construction URL détails: {e}")
            return None

    def normalize_pokemon_name_for_url(self, pokemon_name):
        """Normalise le nom d'un Pokemon pour construire une URL."""
        try:
            # Convertir en minuscules
            name = pokemon_name.lower()
            
            # Remplacer les caractères spéciaux
            name = name.replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('ë', 'e')
            name = name.replace('à', 'a').replace('â', 'a').replace('ä', 'a')
            name = name.replace('ù', 'u').replace('û', 'u').replace('ü', 'u')
            name = name.replace('ô', 'o').replace('ö', 'o')
            name = name.replace('î', 'i').replace('ï', 'i')
            name = name.replace('ç', 'c')
            
            # Gérer les cas spéciaux
            special_cases = {
                'nidoran♀': 'nidoran-f',
                'nidoran♂': 'nidoran-m',
                'mr. mime': 'mr-mime',
                'farfetch\'d': 'farfetchd',
                'ho-oh': 'ho-oh',
                'flabébé': 'flabebe',
                'type: null': 'type-null'
            }
            
            if name in special_cases:
                name = special_cases[name]
            
            # Remplacer les espaces et caractères spéciaux par des tirets
            name = name.replace(' ', '-').replace('.', '').replace('\'', '').replace(':', '')
            
            return name
            
        except Exception as e:
            print(f"    ❌ Erreur normalisation nom: {e}")
            return pokemon_name.lower()

    def download_high_quality_image(self, soup, pokemon_name, generation, pokemon_number):
        """Télécharge l'image haute qualité d'un Pokemon depuis la page de détails."""
        try:
            # Chercher spécifiquement les liens avec "/home" dans l'URL (comme dans bulbizarre.html)
            high_quality_candidates = []
            
            # Chercher les images avec "/home" dans le src (images haute qualité)
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if src and '/home/' in src:
                    high_quality_candidates.append(src)
                    print(f"    🔍 Image HQ trouvée: {src}")
            
            # Si pas d'image /home/, chercher d'autres candidates
            if not high_quality_candidates:
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    if src and any(keyword in src.lower() for keyword in ['artworks', 'artwork', 'hq', 'high', 'big', 'large']):
                        high_quality_candidates.append(src)
            
            # Si encore rien, prendre la première grande image
            if not high_quality_candidates:
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    alt = img.get('alt', '').lower()
                    if src and (pokemon_name.lower() in alt or 'pokemon' in alt):
                        high_quality_candidates.append(src)
                        break
            
            if not high_quality_candidates:
                print(f"    ⚠️ Pas d'image haute qualité trouvée pour {pokemon_name}")
                return None
            
            # Prendre la première image candidate
            image_url = high_quality_candidates[0]
            
            # Construire l'URL complète
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
            elif image_url.startswith('/'):
                image_url = urljoin(self.base_url, image_url)
            
            print(f"    📷 Téléchargement image HQ: {image_url}")
            
            # Télécharger l'image
            response = self.session.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Déterminer l'extension
            extension = os.path.splitext(urlparse(image_url).path)[1] or '.png'
            
            # Créer le nom du fichier avec suffixe "hq" (pas "_HQ")
            clean_pokemon_name = self.sanitize_filename(pokemon_name)
            
            if pokemon_number is not None:
                number_str = f"{pokemon_number:03d}"
            else:
                number_str = "XXX"
            
            # CORRECTION : Utiliser "hq" comme suffixe au lieu de "_HQ"
            filename = f"{number_str}_{clean_pokemon_name}_hq{extension}"
            filename = self.sanitize_filename(filename.replace(extension, '')) + extension
            filepath = os.path.join("assets", f"gen_{generation}", filename)
            
            # Vérifier si le fichier existe déjà
            if os.path.exists(filepath):
                print(f"    ✅ Image HQ existe déjà: {filename}")
                return filepath
            
            # Sauvegarder le fichier
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"    ✅ Image HQ téléchargée: {filename}")
            return filepath
            
        except Exception as e:
            print(f"    ❌ Erreur téléchargement image HQ: {e}")
            return None

    def parse_pokemon_details_v2(self, soup, pokemon_name):
        """Parse les détails selon la VRAIE structure pokebip : méthodes générales en haut, puis tableaux spécifiques."""
        try:
            details = {
                'general_methods': [],    # ✅ Section "Méthodes de shasse disponibles"
                'specific_methods': [],   # ✅ Tableaux de détails par jeu
                'games': []
            }
            
            print(f"    🔍 PARSING STRUCTURE POKEBIP pour {pokemon_name}...")
            
            # ✅ ÉTAPE 1 : Extraire les méthodes GÉNÉRALES de la section résumé
            self.extract_general_methods_from_summary(soup, details)
            
            # ✅ ÉTAPE 2 : Extraire les méthodes SPÉCIFIQUES des tableaux de jeux
            self.extract_specific_methods_from_tables(soup, details)
            
            # ✅ ÉTAPE 3 : Ajouter Masuda automatiquement si reproductible
            if self.is_breedable_pokemon(pokemon_name):
                if 'Masuda' not in [m['name'] for m in details['general_methods']]:
                    details['general_methods'].append({
                        'name': 'Masuda',
                        'category': 'breeding',
                        'description': 'Reproduction avec parents de nationalités différentes',
                        'conditions': 'Taux x6 avec Charme Chroma'
                    })
            
            print(f"    📊 RÉSULTAT: {len(details['games'])} jeux, {len(details['general_methods'])} générales, {len(details['specific_methods'])} spécifiques")
            return details
            
        except Exception as e:
            print(f"    ❌ Erreur parsing: {e}")
            return {'general_methods': [], 'specific_methods': [], 'games': []}
    
    def extract_general_methods_from_summary(self, soup, details):
        """Extrait les méthodes générales de la section 'Méthodes de shasse disponibles'."""
        try:
            print(f"    🎯 Recherche section 'Méthodes de shasse disponibles'...")
            
            # Chercher la cellule contenant "Méthodes de shasse disponibles"
            methods_header = soup.find('th', string=lambda text: text and 'Méthodes de shasse disponibles' in text)
            
            if methods_header:
                print(f"      📝 Section trouvée!")
                
                # Trouver la cellule suivante qui contient les méthodes
                next_row = methods_header.find_parent('tr').find_next_sibling('tr')
                if next_row:
                    methods_cell = next_row.find('td')
                    if methods_cell:
                        # Extraire tous les éléments de liste dans cette cellule
                        list_items = methods_cell.find_all('li', class_='listh-bipcode')
                        
                        for li in list_items:
                            method_text = li.get_text(strip=True)
                            if method_text and len(method_text) > 1:
                                print(f"        ✅ Méthode générale trouvée: {method_text}")
                                
                                # Classifier la méthode
                                method_category = self.classify_general_method(method_text)
                                
                                if method_text not in [m['name'] for m in details['general_methods']]:
                                    details['general_methods'].append({
                                        'name': method_text,
                                        'category': method_category['category'],
                                        'description': method_category['description'],
                                        'conditions': ''
                                    })
            
            # ✅ FALLBACK : Recherche directe par mots-clés si rien trouvé
            if not details['general_methods']:
                print(f"    🔍 Fallback: recherche directe par mots-clés...")
                page_text = soup.get_text().lower()
                
                fallback_methods = [
                    {'name': 'App. M. EV', 'keywords': ['app. m. ev', 'app m ev', 'apparition massive']},
                    {'name': 'CALC', 'keywords': ['calc']},
                    {'name': 'Charme Chroma', 'keywords': ['charme chroma']},
                    {'name': 'Masuda', 'keywords': ['masuda']},
                    {'name': 'Poké Radar', 'keywords': ['poké radar', 'radar']},
                    {'name': 'S.O.S', 'keywords': ['s.o.s', 'sos']},
                    {'name': 'Navidex', 'keywords': ['navidex']},
                    {'name': 'Hordes', 'keywords': ['hordes']},
                    {'name': 'Safari des Amis', 'keywords': ['safari des amis']},
                    {'name': 'Aura Brillance', 'keywords': ['aura brillance']},
                    {'name': 'Sandwich', 'keywords': ['sandwich']}
                ]
                
                for method_info in fallback_methods:
                    if any(keyword in page_text for keyword in method_info['keywords']):
                        method_category = self.classify_general_method(method_info['name'])
                        details['general_methods'].append({
                            'name': method_info['name'],
                            'category': method_category['category'], 
                            'description': method_category['description'],
                            'conditions': ''
                        })
                        print(f"        🎯 Fallback trouvé: {method_info['name']}")
            
            print(f"    📊 Méthodes générales trouvées: {len(details['general_methods'])}")
            
        except Exception as e:
            print(f"    ⚠️ Erreur extraction méthodes générales: {e}")

    def extract_specific_methods_from_tables(self, soup, details):
        """Extrait les méthodes spécifiques depuis les tableaux par génération - VERSION AMÉLIORÉE."""
        try:
            print(f"    🔍 Recherche des méthodes spécifiques dans les tableaux...")
            
            # Trouver tous les tableaux avec la structure appropriée
            tables = soup.find_all('table')
            methods_found = 0
            
            for table in tables:
                if self.is_methods_table(table):
                    print(f"      📋 Traitement d'un tableau de méthodes...")
                    table_methods = self.parse_methods_table_improved(table, details)
                    methods_found += len(table_methods)
                    print(f"        ✅ {len(table_methods)} méthodes extraites")
            
            print(f"    📊 Total méthodes spécifiques trouvées: {methods_found}")
            
        except Exception as e:
            print(f"    ⚠️ Erreur extraction méthodes spécifiques: {e}")

    def is_methods_table(self, table) -> bool:
        """Vérifie si un tableau contient des méthodes de chasse."""
                        header_row = table.find('tr')
        if not header_row:
            return False
        
                            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        return (len(headers) >= 3 and 
                'Jeu' in headers and 
                'Méthode' in headers)
    
    def parse_methods_table_improved(self, table, details):
        """Parse un tableau de méthodes - VERSION CORRIGÉE POUR ÉVITER LES MÉTHODES ARTIFICIELLES."""
        methods = []
                                rows = table.find_all('tr')[1:]  # Skip header
                                
        current_game = None
        current_method = None
        
        for row_idx, row in enumerate(rows):
                                    cols = row.find_all(['th', 'td'])
                                    
            # ✅ CORRECTION : Gestion améliorée des rowspan/colspan
            if len(cols) == 1:
                # Une seule colonne = probablement une continuation (sprites/info supplémentaire)
                # ❌ ANCIEN PROBLÈME: Il créait des méthodes pour TOUS les sprites
                # ✅ NOUVELLE RÈGLE: Ignorer les cellules qui sont juste des sprites d'autres Pokemon
                
                cell_text = cols[0].get_text(strip=True)
                cell_html = str(cols[0])
                
                # ✅ FILTRE STRICT: Ne créer une méthode QUE si il y a un lieu réel
                if current_game and current_method:
                    # Chercher les sprites dans cette cellule
                    sprites = self.extract_pokemon_sprites_from_html(cell_html)
                    location = self.extract_location_from_context(cell_text, cell_html)
                    
                    # ✅ NOUVELLE VALIDATION: Ne créer une méthode que si on a un VRAI lieu
                    # Pas juste un pourcentage ou des sprites vides
                    has_real_location = (location and 
                                       len(location.strip()) > 0 and 
                                       not location.startswith('%') and
                                       location.lower() not in ['', 'non spécifié', 'autre'])
                    
                    # ✅ RÈGLE: Ne créer une méthode QUE si il y a un lieu spécifique ET valide
                    if has_real_location and '%' in cell_text:
                        method_data = {
                            'game': current_game,
                            'method': current_method,
                            'location': location,
                            'probability': cell_text,
                            'pokemon_sprites': sprites
                        }
                        
                        if self.is_valid_method_entry(method_data):
                            method_category = self.classify_specific_method(current_method)
                            
                            # Ajouter le jeu si nécessaire
                                            if current_game not in [g['name'] for g in details['games']]:
                                                generation = self.detect_generation_from_game(current_game)
                                                details['games'].append({
                                                    'name': current_game,
                                                    'generation': generation
                                                })
                            
                            details['specific_methods'].append({
                                'method': current_method,
                                'game': current_game,
                                'location': location,
                                'probability': cell_text,
                                'category': method_category['category']
                            })
                            
                            methods.append(method_data)
                    # ✅ SINON: Ignorer complètement cette cellule (c'est juste des sprites d'autres Pokemon)
                
                continue
            
            # ✅ CORRECTION : Gestion des lignes normales avec meilleure détection
            normalized_data = self.normalize_row_data_improved(cols)
            
            if normalized_data:
                method_data = self.parse_single_method_improved(normalized_data, current_game)
                if method_data:
                    # Ajouter le jeu (si pas déjà présent)
                    if method_data['game'] and method_data['game'] not in [g['name'] for g in details['games']]:
                        generation = self.detect_generation_from_game(method_data['game'])
                        details['games'].append({
                            'name': method_data['game'],
                            'generation': generation
                        })
                        print(f"              🆕 Jeu ajouté: {method_data['game']} (Gen {generation})")
                                            
                                            # Ajouter la méthode spécifique
                    method_category = self.classify_specific_method(method_data['method'])
                    
                                            details['specific_methods'].append({
                        'method': method_data['method'],
                        'game': method_data['game'],
                        'location': method_data['location'],
                        'probability': method_data['probability'],
                        'category': method_category['category']
                    })
                    
                    methods.append(method_data)
                    
                    # Update current context
                    if method_data['game']:
                        current_game = method_data['game']
                    if method_data['method']:
                        current_method = method_data['method']
        
        return methods

    def extract_probability_from_span(self, cell) -> str:
        """Extrait SEULEMENT le pourcentage visible du span, ignore les tooltips TC."""
        # Juste récupérer le texte visible, ignorer les tooltips
        text = cell.get_text(strip=True)
        
        # Extraire seulement le pourcentage principal visible
        if text and '%' in text:
            main_prob = re.search(r'\d+(?:\.\d+)?%', text)
            if main_prob:
                return main_prob.group(0)
        
        return text if text else ''

    def clean_cell_text_smart(self, cell) -> str:
        """Nettoie le texte d'une cellule en préservant les séparations importantes."""
        # ✅ NOUVEAU : Vérifier d'abord s'il y a des spans avec TC tooltips
        spans_with_tc = cell.find_all('span', attrs={'data-original-title': True})
        has_tc_tooltips = any('tc =' in span.get('data-original-title', '').lower() or 'tc=' in span.get('data-original-title', '').lower() 
                             for span in spans_with_tc)
        
        if has_tc_tooltips:
            # Si on a des tooltips TC, extraire seulement le texte visible (sans les tooltips)
            # Pour éviter la duplication TC dans le texte
            text = ''
            for content in cell.contents:
                if hasattr(content, 'name'):
                    if content.name == 'span' and content.get('data-original-title'):
                        # Prendre seulement le texte visible du span, pas le tooltip
                        text += content.get_text(strip=True) + ' '
                                        else:
                        text += content.get_text(strip=True) + ' '
                else:
                    text += str(content).strip() + ' '
            text = text.strip()
        else:
            # Obtenir le texte avec séparateurs (méthode originale)
            text = cell.get_text(separator=' | ', strip=True)
        
        # Nettoyer les séparations multiples
        text = re.sub(r'\s*\|\s*', ' | ', text)  # Normaliser les séparateurs
        text = re.sub(r'\s+', ' ', text)  # Normaliser les espaces multiples
        
        # ✅ AMÉLIORATION: Séparer les données collées courantes (si pas de tooltips)
        if not has_tc_tooltips:
            # "RencontreRepousse niv. 51 - Troupeau" -> "Rencontre | Repousse niv. 51 - Troupeau"
            text = re.sub(r'(Rencontre)(Repousse)', r'\1 | \2', text)
            text = re.sub(r'(Reset)(Sandwich)', r'\1 | \2', text)
        
        # Nettoyer les espaces en trop
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def normalize_row_data_improved(self, cols):
        """Normalise les données d'une ligne - VERSION AMÉLIORÉE POUR ROWSPAN/COLSPAN."""
        if len(cols) < 2:
            return None
        
        # ✅ CORRECTION : Utiliser le nettoyage intelligent au lieu de strip brutal
        all_texts = [self.clean_cell_text_smart(col) for col in cols]
        all_html = [str(col) for col in cols]
        
        result = {'game': '', 'method': '', 'location': '', 'probability': '', 'sprites': []}
        
        # ✅ AMÉLIORATION : Détection plus intelligente selon le nombre de colonnes
        if len(cols) == 4:
            # Cas standard : Jeu | Méthode | Localisation | Pourcentage
            result['game'] = all_texts[0]
            result['method'] = all_texts[1]
            result['location'] = all_texts[2]
            result['probability'] = self.extract_probability_from_span(cols[3])  # ✅ Utiliser la nouvelle fonction
            result['sprites'] = self.extract_pokemon_sprites_from_html(all_html[2])  # Sprites dans localisation
            
        elif len(cols) == 3:
            # Cas typique : continuation d'un jeu avec Méthode | Localisation | Pourcentage
            # OU Jeu | Méthode | Localisation (sans pourcentage séparé)
            
            # Détecter si le premier élément est un jeu ou une méthode
            first_text = all_texts[0]
            first_content_type = self.detect_content_type_simple(first_text, all_html[0])
            
            if first_content_type == 'game':
                # Jeu | Méthode | Localisation
                result['game'] = all_texts[0]
                result['method'] = all_texts[1]
                result['location'] = all_texts[2]
                result['sprites'] = self.extract_pokemon_sprites_from_html(all_html[2])
            else:
                # Méthode | Localisation | Pourcentage (continuation)
                result['method'] = all_texts[0]
                result['location'] = all_texts[1]
                result['probability'] = self.extract_probability_from_span(cols[2])  # ✅ Utiliser la nouvelle fonction
                result['sprites'] = self.extract_pokemon_sprites_from_html(all_html[1])
        
        elif len(cols) == 2:
            # Cas : Méthode | Localisation OU Localisation | Pourcentage
            if '%' in all_texts[1] or 'TC =' in all_texts[1]:
                # Localisation | Pourcentage
                result['location'] = all_texts[0]
                result['probability'] = self.extract_probability_from_span(cols[1])  # ✅ Utiliser la nouvelle fonction
            else:
                # Méthode | Localisation
                result['method'] = all_texts[0]
                result['location'] = all_texts[1]
            result['sprites'] = self.extract_pokemon_sprites_from_html(all_html[0] + all_html[1])
        
        # ✅ NETTOYAGE FINAL : Vérifier que les éléments ne sont pas vides
        for key in ['game', 'method', 'location', 'probability']:
            if result[key] and len(result[key].strip()) == 0:
                result[key] = ''
        
        return result if any([result['game'], result['method'], result['location']]) else None

    def clean_probability_smart(self, probability_text: str) -> str:
        """Nettoie intelligemment les données de probabilité (gère TC =, etc.) - VERSION COMPLÈTE."""
        if not probability_text:
            return ''
        
        # ✅ CORRECTION PRINCIPALE : Séparer toutes les données TC = avant traitement
        if 'TC =' in probability_text or 'TC=' in probability_text:
            # Patterns multiples pour tous les cas de TC
            # "100%TC = 10%Capture : 50.28% / tour" -> "100% | TC = 10% | Capture : 50.28% / tour"
            probability_text = re.sub(r'(\d+(?:\.\d+)?%)TC\s*=\s*(\d+(?:\.\d+)?%)([A-Za-z])', r'\1 | TC = \2 | \3', probability_text)
            probability_text = re.sub(r'(\d+(?:\.\d+)?%)TC=(\d+(?:\.\d+)?%)([A-Za-z])', r'\1 | TC = \2 | \3', probability_text)
            
            # ✅ NOUVEAU : Cas avec espace "100% TC = 10%" 
            probability_text = re.sub(r'(\d+(?:\.\d+)?%)\s+TC\s*=\s*(\d+(?:\.\d+)?%)([A-Za-z])', r'\1 | TC = \2 | \3', probability_text)
            probability_text = re.sub(r'(\d+(?:\.\d+)?%)\s+TC\s*=\s*(\d+(?:\.\d+)?%)\s*([A-Za-z])', r'\1 | TC = \2 | \3', probability_text)
            
            # Cas simples sans texte après
            probability_text = re.sub(r'(\d+(?:\.\d+)?%)TC\s*=\s*(\d+(?:\.\d+)?%)(?!\w)', r'\1 | TC = \2', probability_text)
            probability_text = re.sub(r'(\d+(?:\.\d+)?%)TC=(\d+(?:\.\d+)?%)(?!\w)', r'\1 | TC = \2', probability_text)
            # ✅ NOUVEAU : Cas avec espace simple
            probability_text = re.sub(r'(\d+(?:\.\d+)?%)\s+TC\s*=\s*(\d+(?:\.\d+)?%)(?!\w)', r'\1 | TC = \2', probability_text)
            
            # ✅ NOUVEAU : Cas "% TC =" au milieu du texte
            probability_text = re.sub(r'(\d+(?:\.\d+)?%)\s+TC\s*=\s*(\d+(?:\.\d+)?%)\s+([A-Za-z])', r'\1 | TC = \2 | \3', probability_text)
        
        # ✅ NOUVEAU : Séparer les données de capture et fuite
        if 'Capture :' in probability_text or 'Fuite :' in probability_text:
            # "Capture : 50.28% / tourFuite : 47.27% / tour" -> "Capture : 50.28% / tour | Fuite : 47.27% / tour"
            probability_text = re.sub(r'(\d+(?:\.\d+)?%\s*/\s*tour)([A-Z])', r'\1 | \2', probability_text)
            probability_text = re.sub(r'(Capture\s*:\s*[^|]+)([A-Z])', r'\1 | \2', probability_text)
            probability_text = re.sub(r'(Fuite\s*:\s*[^|]+)([A-Z])', r'\1 | \2', probability_text)
        
        # ✅ GESTION des pipes existants et nettoyage
        if '|' in probability_text:
            parts = probability_text.split('|')
            cleaned_parts = []
            
            for part in parts:
                part = part.strip()
                if part:
                    # Nettoyer chaque partie individuellement
                    if 'TC =' in part or 'TC=' in part:
                        part = re.sub(r'TC\s*=\s*', 'TC = ', part)  # Normaliser les espaces
                    
                    # Nettoyer les données de capture/fuite
                    if 'Capture :' in part:
                        part = re.sub(r'Capture\s*:\s*', 'Capture : ', part)
                    if 'Fuite :' in part:
                        part = re.sub(r'Fuite\s*:\s*', 'Fuite : ', part)
                    
                    cleaned_parts.append(part)
            
            return ' | '.join(cleaned_parts)
        
        # ✅ NETTOYAGE STANDARD pour les probabilités simples
        probability_text = probability_text.strip()
        
        # Normaliser les pourcentages
        probability_text = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1%', probability_text)
        
        # ✅ NOUVEAU : Tronquer les probabilités très longues (probablement mal parsées)
        if len(probability_text) > 100:
            # Prendre seulement la première partie logique
            main_prob = re.search(r'^\d+(?:\.\d+)?%', probability_text)
            if main_prob:
                return main_prob.group(0)
            else:
                return probability_text[:50] + '...'  # Tronquer si trop long
        
        return probability_text

    def extract_location_from_context(self, text: str, html: str) -> str:
        """Extrait le lieu depuis le contexte (sprites, texte, etc.) - VERSION AMÉLIORÉE."""
        # Si il y a des sprites, essayer d'extraire le lieu depuis le contexte
        if '<img' in html:
            # Il peut y avoir des infos de lieu dans le text ou les attributs
            soup = BeautifulSoup(html, 'html.parser')
            
            # ✅ AMÉLIORATION : Utiliser le nettoyage intelligent
            text_content = soup.get_text(separator=' | ', strip=True)
            
            # Chercher des éléments de texte autour des images
            for element in soup.find_all(text=True):
                element_text = element.strip()
                if element_text and not element_text.startswith('Pokémon #'):
                    # Patterns typiques de lieux
                    location_patterns = [
                        r'(Cave|Grotte|Route|Chemin|Parc|Zone|Caverne)\s+[^%\d]+',
                        r'[A-ZÀ-Ÿ][a-zà-ÿ]+\s+[A-ZÀ-Ÿ][a-zà-ÿ]+'
                    ]
                    
                    for pattern in location_patterns:
                        match = re.search(pattern, element_text)
                        if match:
                            return self.clean_location_smart(match.group(0).strip())
        
        # Fallback : chercher dans le texte
        if text and not text.startswith('%') and not text.startswith('TC ='):
            # Nettoyer le texte des pourcentages pour garder le lieu
            clean_text = re.sub(r'\d+%.*', '', text).strip()
            if clean_text:
                return self.clean_location_smart(clean_text)
        
        return ''

    def clean_location_smart(self, location_text: str) -> str:
        """Nettoie intelligemment les noms de lieux."""
        if not location_text:
            return ''
        
        # ✅ AMÉLIORATION : Séparer les lieux complexes avec des pipes
        # "Plaine VerdoyanteSauf par temps Nuageux" -> "Plaine Verdoyante | Sauf par temps Nuageux"
        
        # Détecter les mots collés et les séparer
        location_text = re.sub(r'([a-z])([A-Z])', r'\1 | \2', location_text)  # mots collés
        location_text = re.sub(r'(Zone|Route|Cave|Grotte|Parc)\s*([A-Z])', r'\1 \2', location_text)  # mots après zone/route
        
        # Séparer les conditions météo
        location_text = re.sub(r'(Sauf|Except|Par temps)', r'| \1', location_text)
        
        # Nettoyer les espaces multiples et pipes multiples
        location_text = re.sub(r'\s+', ' ', location_text)
        location_text = re.sub(r'\s*\|\s*', ' | ', location_text)
        location_text = re.sub(r'\|\s*\|', '|', location_text)  # pipes doubles
        
        return location_text.strip()

    def clean_method_smart(self, method_text: str) -> str:
        """Nettoie intelligemment les noms de méthodes."""
        if not method_text:
            return ''
        
        # ✅ AMÉLIORATION : Séparer les méthodes composées
        # "RencontreRepousse niv. 51 - Troupeau" -> "Rencontre | Repousse niv. 51 - Troupeau"
        
        # Séparer les méthodes collées courantes
        method_text = re.sub(r'(Rencontre)(Repousse)', r'\1 | \2', method_text)
        method_text = re.sub(r'(Reset)(Sandwich)', r'\1 | \2', method_text)
        method_text = re.sub(r'(Surf)(Repousse)', r'\1 | \2', method_text)
        method_text = re.sub(r'(Pêche)(Repousse)', r'\1 | \2', method_text)
        
        # Séparer les niveaux et conditions
        method_text = re.sub(r'(niv\.\s*\d+)', r'| \1', method_text)
        method_text = re.sub(r'(\d+\s*blocs)', r'| \1', method_text)
        
        # Nettoyer les espaces et pipes
        method_text = re.sub(r'\s+', ' ', method_text)
        method_text = re.sub(r'\s*\|\s*', ' | ', method_text)
        method_text = re.sub(r'^\|\s*', '', method_text)  # pipe au début
        method_text = re.sub(r'\|\s*\|', '|', method_text)  # pipes doubles
        
        return method_text.strip()

    def parse_single_method_improved(self, data: dict, current_game: str):
        """Parse une méthode depuis les données normalisées - VERSION SIMPLIFIÉE."""
        game = data['game'] or current_game
        method = data['method']
        location = data['location']
        probability = data['probability']
        sprites = data.get('sprites', [])
        
        # ✅ VALIDATION SIMPLE : Au moins un jeu ET une méthode non vide
        if not game or not method or len(method.strip()) == 0:
            return None
        
        # ✅ AMÉLIORATION : Utiliser le nettoyage intelligent pour tous les champs
        game = self.clean_game_name(game)
        method = self.clean_method_smart(method) if method else ''
        location = self.clean_location_smart(location) if location else ''
        probability = probability.strip() if probability else ''  # Déjà nettoyé par clean_probability_smart
        
        # ✅ VALIDATION FINALE : S'assurer que la méthode n'est pas vide après nettoyage
        if not method:
            return None
        
        return {
            'game': game,
            'method': method,
            'location': location,
            'probability': probability,
            'pokemon_sprites': sprites
        }

    def is_valid_method_entry(self, method_data: dict) -> bool:
        """Valide qu'une entrée de méthode est correcte - VERSION STRICTE."""
        if not method_data.get('game') or not method_data.get('method'):
            return False
        
        # Vérifier que la méthode n'est pas vide
        method = method_data.get('method', '').strip()
        if not method or len(method) < 2:
            return False
        
        # Vérifier que ce n'est pas juste un pourcentage ou des données invalides
        if method.startswith('%') or method.startswith('TC ='):
            return False
        
        # ✅ NOUVELLE VALIDATION STRICTE: Rejeter les méthodes sans lieu valide
        location = method_data.get('location', '').strip()
        
        # ❌ Rejeter si pas de lieu du tout
        if not location or len(location) == 0:
            return False
        
        # ❌ Rejeter les lieux invalides
        invalid_locations = ['non spécifié', 'autre', '', '???', 'inconnu', 'n/a']
        if location.lower() in invalid_locations:
            return False
        
        # ❌ Rejeter si le lieu est juste un pourcentage
        if location.startswith('%') or location.startswith('TC ='):
            return False
        
        # ✅ VALIDATION POSITIVE: Le lieu doit contenir des mots-clés de lieux réels
        location_keywords = [
            'cave', 'grotte', 'route', 'chemin', 'parc', 'zone', 'caverne',
            'lac', 'mont', 'forêt', 'prairie', 'désert', 'ville', 'îl',
            'tour', 'temple', 'château', 'manoir', 'safari', 'plaine',
            'côte', 'baie', 'pont', 'tunnel', 'piste', 'sentier', 'jardin'
        ]
        
        has_valid_location = any(keyword in location.lower() for keyword in location_keywords)
        if not has_valid_location:
            # Si aucun mot-clé de lieu, c'est probablement une méthode artificielle
            return False
        
        return True
    
    def detect_content_type_simple(self, text: str, html: str) -> str:
        """Détecte le type de contenu d'une cellule - VERSION SIMPLIFIÉE."""
        text_lower = text.lower()
        
        # Probabilité (contient % ou des ratios)
        if re.search(r'\d+%|tc\s*=|\d+/\d+', text_lower):
            return 'probability'
        
        # Rejeter les textes très longs pour les jeux (probablement des localisations)
        if len(text) > 25:
            return 'location'
        
        # Jeux connus (liste simplifiée)
        known_games = [
            'rouge', 'bleu', 'jaune', 'or', 'argent', 'cristal',
            'rubis', 'saphir', 'émeraude', 'rouge feu', 'vert feuille',
            'diamant', 'perle', 'platine', 'heartgold', 'soulsilver',
            'noir', 'blanc', 'rubis oméga', 'saphir alpha',
            'soleil', 'lune', 'ultra-soleil', 'ultra-lune', 'lg: pikachu', 'lg: évoli',
            'épée', 'bouclier', 'diamant étincelant', 'perle scintillante',
            'écarlate', 'violet'
        ]
        
        for game in known_games:
            if game == text_lower or (len(game) > 3 and game in text_lower and len(text) < 20):
                return 'game'
        
        # Méthodes basiques
        method_keywords = ['rencontre', 'reset', 'surf', 'pêche', 'sandwich', 'repousse', 'scanner']
        if any(keyword in text_lower for keyword in method_keywords):
            return 'method'
        
        # Localisation (par défaut pour tout le reste ou si contient des images)
        if '<img' in html or any(loc in text_lower for loc in ['route', 'zone', 'caverne', 'parc']):
            return 'location'
        
        return 'unknown'
    
    def extract_pokemon_sprites_from_html(self, html: str) -> list:
        """Extrait les noms des Pokemon depuis les sprites dans le HTML - VERSION AMÉLIORÉE."""
        soup = BeautifulSoup(html, 'html.parser')
        sprites = soup.find_all('img')
        
        pokemon_names = []
        for sprite in sprites:
            alt_text = sprite.get('alt', '')
            # ✅ NOUVEAU : Nettoyer les noms de Pokemon des sprites
            if alt_text and alt_text not in pokemon_names:
                # Nettoyer le nom (enlever les numéros, etc.)
                clean_name = re.sub(r'#\d+\s*', '', alt_text).strip()
                if clean_name and clean_name not in pokemon_names:
                    pokemon_names.append(clean_name)
        
        return pokemon_names
    
    def parse_method_details_improved(self, method_text: str) -> tuple:
        """VERSION SIMPLIFIÉE : Plus de parsing complexe, juste retourner None."""
        # ✅ SIMPLIFICATION : Plus de parsing des détails
        return None, None
    
    def clean_method_name_improved(self, method: str) -> str:
        """VERSION SIMPLIFIÉE : Garder la méthode complète."""
        if not method:
            return ''
        
        # ✅ SIMPLIFICATION : Juste nettoyer les espaces, garder tout le reste
        return method.strip()
    
    def clean_location_name_improved(self, location: str) -> str:
        """VERSION SIMPLIFIÉE : Garder la localisation complète."""
        if not location:
            return ''
        
        # ✅ SIMPLIFICATION : Juste nettoyer les espaces, garder tout le contenu
        return location.strip()
    
    def clean_probability_improved(self, prob: str) -> str:
        """VERSION SIMPLIFIÉE : Garder la probabilité complète."""
        if not prob:
            return ''
        
        # ✅ SIMPLIFICATION : Juste nettoyer les espaces, garder tout
        return prob.strip()

    def clean_game_name(self, game_name):
        """Nettoie le nom du jeu extrait du HTML - VERSION AMÉLIORÉE."""
        if not game_name:
            return ""
        
        # Supprimer les éléments HTML restants
        game_name = game_name.strip()
        
        # ✅ AMÉLIORATION : Mappage étendu avec variantes de noms
        game_mapping = {
            # Abréviations courantes
            'R': 'Rouge', 'B': 'Bleu', 'J': 'Jaune',
            'O': 'Or', 'A': 'Argent', 'C': 'Cristal',
            'RF': 'Rouge Feu', 'VF': 'Vert Feuille',
            'D': 'Diamant', 'P': 'Perle', 'Pl': 'Platine',
            'HG': 'HeartGold', 'SS': 'SoulSilver',
            'N': 'Noir', 'B2': 'Blanc 2', 'N2': 'Noir 2',
            'RO': 'Rubis Oméga', 'SA': 'Saphir Alpha',
            'So': 'Soleil', 'Lu': 'Lune',
            'US': 'Ultra-Soleil', 'UL': 'Ultra-Lune',
            'LGP': 'LG: Pikachu', 'LGE': 'LG: Évoli',
            'Ep': 'Épée', 'Bo': 'Bouclier',
            'DE': 'Diamant Ét.', 'PE': 'Perle Scint.',
            'LéA': 'Légendes Pokémon: Arceus',
            'Ec': 'Écarlate', 'Vi': 'Violet', 'EV': 'Écarlate/Violet',
            
            # ✅ NOUVEAU : Variantes de noms complets pour génération 7
            'Ultra Soleil': 'Ultra-Soleil', 'Ultra Lune': 'Ultra-Lune',
            'LG Pikachu': 'LG: Pikachu', 'LG Évoli': 'LG: Évoli',
            'Let\'s Go Pikachu': 'LG: Pikachu', 'Let\'s Go Évoli': 'LG: Évoli',
            
            # Variantes avec espaces
            'Diamant Étincelant': 'Diamant Ét.', 'Perle Scintillante': 'Perle Scint.',
            'Légendes Pokémon Arceus': 'Légendes Pokémon: Arceus'
        }
        
        return game_mapping.get(game_name, game_name)

    def clean_method_name(self, method_name):
        """Nettoie le nom de la méthode extrait du HTML."""
        if not method_name:
            return ""
        
        # Supprimer les éléments HTML et espaces
        method_name = method_name.strip()
        
        # Mappage des méthodes courtes vers les noms complets
        method_mapping = {
            'Reset': 'Reset',
            'Rencontre': 'Rencontre',
            'Pêche': 'Pêche',
            'Surf': 'Surf',
            'Scanner': 'Scanner',
            'Sandwich': 'Sandwich',
            'App. M.': 'Apparition Massive',
            'Repousse': 'Repousse',
            'Massive': 'Apparition Massive'
        }
        
        return method_mapping.get(method_name, method_name)

    def clean_location_name(self, location_name):
        """Nettoie le nom de localisation extrait du HTML."""
        if not location_name:
            return ""
        
        return location_name.strip()

    def classify_general_method(self, method_name):
        """Classification spécifique pour les méthodes GÉNÉRALES."""
        general_methods = {
            'app. m. ev': {'category': 'encounter', 'description': 'Apparition Massive sur Écarlate/Violet'},
            'calc': {'category': 'encounter', 'description': 'Combo Capture (Let\'s Go)'},
            'charme chroma': {'category': 'general', 'description': 'Augmente les chances de shiny'},
            'charme': {'category': 'general', 'description': 'Augmente les chances de shiny'},
            'masuda': {'category': 'breeding', 'description': 'Reproduction avec parents de nationalités différentes'},
            'poké radar': {'category': 'encounter', 'description': 'Radar à Pokemon'},
            'radar': {'category': 'encounter', 'description': 'Radar à Pokemon'},
            's.o.s': {'category': 'encounter', 'description': 'Appel à l\'aide'},
            'sos': {'category': 'encounter', 'description': 'Appel à l\'aide'},
            'navidex': {'category': 'general', 'description': 'Navigation Dex'},
            'hordes': {'category': 'encounter', 'description': 'Rencontres de Hordes'},
            'safari des amis': {'category': 'encounter', 'description': 'Safari des Amis'},
            'aura brillance': {'category': 'general', 'description': 'Aura Brillance (Sandwich)'},
            'sandwich': {'category': 'general', 'description': 'Sandwich (Écarlate/Violet)'}
        }
        
        method_lower = method_name.lower()
        for key, info in general_methods.items():
            if key in method_lower:
                return info
        
        return {'category': 'general', 'description': 'Méthode générale'}
    
    def classify_specific_method(self, method_name):
        """Classification pour les méthodes SPÉCIFIQUES par jeu/lieu."""
        specific_categories = {
            'reset': 'reset',
            'rencontre': 'encounter', 
            'pêche': 'encounter',
            'surf': 'encounter',
            'scanner': 'encounter',
            'sandwich': 'encounter',
            'apparition': 'encounter',
            'massive': 'encounter'
        }
        
        method_lower = method_name.lower()
        for keyword, category in specific_categories.items():
            if keyword in method_lower:
                return {'category': category, 'description': f'Méthode {category}'}
        
        return {'category': 'encounter', 'description': 'Méthode de rencontre'}
    
    def is_valid_game_method_entry(self, game_text, method_text, location_text):
        """Validation améliorée pour les entrées de tableaux de jeux."""
        # Vérifier que les champs essentiels sont présents
        if not game_text or not method_text:
            return False
        
        # Nettoyer et vérifier la longueur
        game_text = game_text.strip()
        method_text = method_text.strip()
        
        if len(game_text) == 0 or len(method_text) == 0:
            return False
        
        # ✅ NOUVEAU : Filtrer les entrées qui ne sont clairement pas des jeux
        invalid_game_indicators = [
            'méthode', 'localisation', 'pourcentage', 'probabilité',
            'reset', 'rencontre', 'pêche', 'surf', 'scanner',
            'sandwich', 'apparition', 'massive', 'repousse'
        ]
        
        game_lower = game_text.lower()
        for indicator in invalid_game_indicators:
            if indicator in game_lower:
                return False
        
        # ✅ NOUVEAU : Filtrer les méthodes qui ne sont clairement pas des méthodes
        invalid_method_indicators = [
            'rouge', 'bleu', 'jaune', 'or', 'argent', 'cristal',
            'rubis', 'saphir', 'émeraude', 'diamant', 'perle',
            'platine', 'noir', 'blanc', 'écarlate', 'violet'
        ]
        
        method_lower = method_text.lower()
        for indicator in invalid_method_indicators:
            if indicator in method_lower:
                return False
        
        # ✅ NOUVEAU : Vérifier que la méthode contient des mots-clés valides
        valid_method_keywords = [
            'reset', 'rencontre', 'pêche', 'surf', 'scanner',
            'sandwich', 'apparition', 'massive', 'repousse',
            'durant', 'niveau', 'niv.', 'poison', 'n.3'
        ]
        
        has_valid_method_keyword = any(keyword in method_lower for keyword in valid_method_keywords)
        
        return has_valid_method_keyword
    
    def detect_generation_from_game(self, game_name):
        """Détecte la génération à partir du nom du jeu - VERSION CORRIGÉE."""
        if not game_name:
            return 1
        
        game_name_lower = game_name.lower()
        
        # ✅ CORRECTION : Vérifier les noms COMPLETS d'abord pour éviter les fausses correspondances
        # Ordre important : noms complets avant noms partiels !
        generation_map_ordered = [
            # 3G - Vérifier AVANT les jeux 1G pour éviter "Rouge" vs "Rouge Feu"
            ('rouge feu', 3), ('vert feuille', 3), ('rubis oméga', 6), ('saphir alpha', 6),
            ('rubis', 3), ('saphir', 3), ('émeraude', 3),
            
            # 1G
            ('rouge', 1), ('bleu', 1), ('jaune', 1),
            
            # 2G
            ('or', 2), ('argent', 2), ('cristal', 2),
            
            # 4G
            ('diamant étincelant', 8), ('perle scintillante', 8),  # Vérifier avant Diamant/Perle
            ('diamant ét.', 8), ('perle scint.', 8),  # Versions courtes
            ('diamant', 4), ('perle', 4), ('platine', 4), 
            ('heartgold', 4), ('soulsilver', 4),
            
            # 5G
            ('noir 2', 5), ('blanc 2', 5), ('noir', 5), ('blanc', 5),
            
            # 6G
            ('x', 6), ('y', 6),
            
            # 7G
            ('ultra-soleil', 7), ('ultra-lune', 7), ('ultra soleil', 7), ('ultra lune', 7),
            ('lg: pikachu', 7), ('lg: évoli', 7), ('let\'s go', 7),
            ('soleil', 7), ('lune', 7),
            
            # 8G
            ('légendes pokémon: arceus', 8), ('légendes pokémon arceus', 8), ('lpa', 8),
            ('épée', 8), ('bouclier', 8),
            
            # 9G
            ('écarlate', 9), ('violet', 9), ('ev', 9), ('écarlate/violet', 9)
        ]
        
        # Parcourir dans l'ordre pour trouver la correspondance la plus spécifique
        for game_pattern, generation in generation_map_ordered:
            if game_pattern in game_name_lower:
                return generation
        
        # ✅ NOUVEAU : Gestion spéciale pour les abréviations courantes
        abbreviations = {
            'rf': 3, 'vf': 3,  # Rouge Feu / Vert Feuille
            'ro': 6, 'sa': 6,  # Rubis Oméga / Saphir Alpha
            'hg': 4, 'ss': 4,  # HeartGold / SoulSilver
            'de': 8, 'pe': 8,  # Diamant Étincelant / Perle Scintillante
            'n2': 5, 'b2': 5,  # Noir 2 / Blanc 2
            'us': 7, 'ul': 7,  # Ultra-Soleil / Ultra-Lune
            'lgp': 7, 'lge': 7,  # Let's Go Pikachu/Évoli
            'ep': 8, 'bo': 8,  # Épée / Bouclier
            'ec': 9, 'vi': 9   # Écarlate / Violet
        }
        
        if game_name_lower in abbreviations:
            return abbreviations[game_name_lower]
        
        print(f"      ⚠️ Génération inconnue pour le jeu: {game_name}, assigné à Gen 1 par défaut")
        return 1  # Par défaut
    
    def find_additional_methods_by_keywords(self, page_text, details, pokemon_name):
        """Recherche des méthodes supplémentaires par mots-clés dans le texte."""
        try:
            # ✅ RECHERCHE SPÉCIFIQUE pour "APP M EV" et "CALC"
            additional_methods = [
                {
                    'keywords': ['app m ev', 'app m', 'apparition massive'],
                    'name': 'APP M EV',
                    'game': 'Écarlate',
                    'location': 'Zone Côtière',
                    'category': 'encounter',
                    'description': 'Apparition Massive sur Écarlate/Violet'
                },
                {
                    'keywords': ['calc', 'combo capture'],
                    'name': 'CALC',
                    'game': "LG: Pikachu",
                    'location': 'Route 2',
                    'category': 'encounter',
                    'description': 'Combo Capture (Let\'s Go)'
                }
            ]
            
            for method_info in additional_methods:
                if any(keyword in page_text for keyword in method_info['keywords']):
                    print(f"      🔍 MÉTHODE DÉTECTÉE PAR MOTS-CLÉS: {method_info['name']}")
                    
                    # Ajouter le jeu si nécessaire
                    if method_info['game'] not in [g['name'] for g in details['games']]:
                        generation = self.detect_generation_from_game(method_info['game'])
                        details['games'].append({
                            'name': method_info['game'],
                            'generation': generation
                        })
                    
                    # Ajouter la méthode
                    if method_info['name'] not in [m['name'] for m in details['specific_methods']]:
                        details['specific_methods'].append({
                            'name': method_info['name'],
                            'game': method_info['game'],
                            'location': method_info['location'],
                            'probability': '???',
                            'category': method_info['category'],
                            'description': method_info['description']
                        })
            
        except Exception as e:
            print(f"      ⚠️ Erreur recherche par mots-clés: {e}")
    
    def is_breedable_pokemon(self, pokemon_name):
        """Vérifie si un Pokemon peut être reproduit (pour Masuda)."""
        # Liste simplifiée - en réalité il faudrait une base plus complète
        non_breedable = ['ditto', 'legendaire', 'mythique']  # À compléter
        return pokemon_name.lower() not in non_breedable
    
    def extract_generation_number(self, text):
        """Extrait le numéro de génération depuis le texte."""
        import re
        match = re.search(r'(\d+)[èe]?[rm]?e?\s*Génération', text)
        if match:
            return int(match.group(1))
        return 1  # Par défaut

    def detect_shiny_lock(self, soup, pokemon_name):
        """Détecte si un Pokemon est shiny lock."""
        try:
            page_text = soup.get_text().lower()
            
            # Chercher des mentions explicites de shiny lock
            explicit_shiny_lock = any(phrase in page_text for phrase in [
                'shiny lock', 'shiny-lock', 'impossible à obtenir en chromatique',
                'aucune méthode de shasse', 'non shassable', 'shasse impossible'
            ])
            
            # Si on trouve "shiny lock" mais aussi des méthodes de shasse, 
            # c'est probablement dans une section générale, pas spécifique à ce Pokemon
            if explicit_shiny_lock:
                # Vérifier si c'est dans le contexte de ce Pokemon ou général
                shiny_context_lines = []
                for line in page_text.split('\n'):
                    if 'shiny lock' in line or 'shiny-lock' in line:
                        shiny_context_lines.append(line.strip())
                
                # Si les lignes contiennent le nom du Pokemon ou parlent spécifiquement de lui
                pokemon_specific_lock = any(
                    pokemon_name.lower() in line or 
                    'ce pokemon' in line or 
                    'impossible' in line and 'chromatique' in line
                    for line in shiny_context_lines
                )
                
                if pokemon_specific_lock:
                    return True
            
            # Chercher des indices très positifs de disponibilité shiny
            positive_shiny_indicators = [
                'méthode de shasse', 'taux de shiny', 'probabilité de shiny',
                'combo capture', 'masuda', 'charme chroma', 'shassable',
                'obtenir en chromatique', 'capturer en chromatique'
            ]
            
            has_strong_positive = any(indicator in page_text for indicator in positive_shiny_indicators)
            
            if has_strong_positive:
                return False
            
            # Par défaut, considérer comme non shiny lock
            return False
            
        except Exception as e:
            print(f"    ⚠️ Erreur détection shiny lock: {e}")
            return False

    def save_pokemon_to_database_v2(self, pokemon_info, sprite_path, details, is_shiny_lock=False):
        """Sauvegarde un Pokemon avec le nouveau modèle V2 - VERSION AVEC DÉDUPLICATION."""
        try:
            # Insérer le Pokemon principal
            pokemon_id = self.db.insert_pokemon(
                name=pokemon_info['name'],
                number=pokemon_info['number'],
                sprite_url=sprite_path,
                generation=pokemon_info['generation'],
                is_shiny_lock=is_shiny_lock,
                high_quality_image=pokemon_info.get('high_quality_image')
            )
            
            print(f"    💾 Pokemon sauvegardé avec ID: {pokemon_id}")
            
            # Insérer les jeux
            game_ids = {}
            for game_data in details['games']:
                try:
                    game_id = self.db.insert_game(
                        name=game_data['name'],
                        generation=game_data['generation']
                    )
                    game_ids[game_data['name']] = game_id
                    print(f"      🎮 Jeu sauvegardé: {game_data['name']} (Gen {game_data['generation']})")
                except Exception as e:
                    print(f"      ⚠️ Erreur sauvegarde jeu {game_data['name']}: {e}")
            
            # ✅ NOUVEAU : Sauvegarder les méthodes GÉNÉRALES
            for method_data in details['general_methods']:
                try:
                    method_id = self.db.insert_hunt_method(
                        name=method_data['name'],
                        description=method_data['description'],
                        is_general=True,
                        category=method_data['category']
                    )
                    
                    # Lier à la table des méthodes générales
                    self.db.link_pokemon_general_method(
                        pokemon_id, method_id, 
                        conditions=method_data.get('conditions')
                    )
                    
                    print(f"      🌍 Méthode générale sauvegardée: {method_data['name']}")
                except Exception as e:
                    print(f"      ⚠️ Erreur sauvegarde méthode générale {method_data['name']}: {e}")
            
            # ✅ DÉDUPLICATION : Sauvegarder les méthodes SPÉCIFIQUES sans doublons
            deduplicated_methods = self.deduplicate_specific_methods(details['specific_methods'])
            print(f"      🔧 Déduplication: {len(details['specific_methods'])} -> {len(deduplicated_methods)} méthodes")
            
            for method_data in deduplicated_methods:
                try:
                    method_id = self.db.insert_hunt_method(
                        name=method_data['method'],
                        description=f"Méthode: {method_data['method']}",
                        is_general=False,
                        category=method_data['category']
                    )
                    
                    # Insérer la localisation complète
                    location_id = self.db.insert_location(
                        name=method_data['location'],
                        region=method_data['game'],
                        description=f"Lieu dans {method_data['game']}"
                    )
                    
                    # Lier à la table des méthodes spécifiques
                    game_id = game_ids.get(method_data['game'])
                    if game_id:
                        self.db.link_pokemon_specific_method(
                            pokemon_id, method_id, game_id, location_id,
                            probability=method_data['probability'],
                            conditions=None
                        )
                        
                        print(f"      🎯 Méthode spécifique sauvegardée: {method_data['method']} dans {method_data['game']}")
                    
                except Exception as e:
                    print(f"      ⚠️ Erreur sauvegarde méthode spécifique {method_data['method']}: {e}")
            
            print(f"    ✅ Toutes les données sauvegardées pour {pokemon_info['name']}")
            return True
            
        except Exception as e:
            print(f"    ❌ Erreur sauvegarde Pokemon: {e}")
            return False

    def deduplicate_specific_methods(self, methods):
        """Déduplique les méthodes spécifiques intelligemment."""
        if not methods:
            return []
        
        # ✅ DÉDUPLICATION par clé unique (jeu + méthode + localisation)
        seen_methods = {}
        deduplicated = []
        
        for method in methods:
            # Créer une clé unique pour identifier les doublons
            game = method.get('game', '').strip()
            method_name = method.get('method', '').strip()
            location = method.get('location', '').strip()
            probability = method.get('probability', '').strip()
            
            # Clé composée pour identifier les vrais doublons
            key = f"{game}|{method_name}|{location}"
            
            if key in seen_methods:
                # ✅ LOGIQUE DE PRÉFÉRENCE : Garder la méthode avec le plus d'infos
                existing = seen_methods[key]
                current_score = self.score_method_completeness(method)
                existing_score = self.score_method_completeness(existing)
                
                if current_score > existing_score:
                    # Remplacer par la méthode plus complète
                    seen_methods[key] = method
                    # Remplacer dans la liste dédupliquée
                    for i, dup_method in enumerate(deduplicated):
                        if self.methods_are_same(dup_method, existing):
                            deduplicated[i] = method
                            break
            else:
                # Nouvelle méthode, l'ajouter
                seen_methods[key] = method
                deduplicated.append(method)
        
        return deduplicated

    def score_method_completeness(self, method):
        """Score une méthode selon sa complétude (plus d'infos = score plus élevé)."""
        score = 0
        
        # Points pour chaque champ rempli
        if method.get('game') and len(method['game'].strip()) > 0:
            score += 1
        if method.get('method') and len(method['method'].strip()) > 0:
            score += 2  # Méthode est plus importante
        if method.get('location') and len(method['location'].strip()) > 0:
            score += 1
        if method.get('probability') and len(method['probability'].strip()) > 0:
            score += 1
        
        # Bonus pour les méthodes complexes (plus d'infos = mieux)
        method_text = method.get('method', '')
        if any(keyword in method_text.lower() for keyword in ['repousse', 'niv.', 'blocs', 'sandwich', '2 par 2']):
            score += 2
        
        # Bonus pour les lieux spécifiques
        location_text = method.get('location', '')
        if any(keyword in location_text.lower() for keyword in ['cave', 'grotte', 'route', 'parc', 'zone']):
            score += 1
        
        return score

    def methods_are_same(self, method1, method2):
        """Vérifie si deux méthodes sont identiques."""
        key1 = f"{method1.get('game', '')}|{method1.get('method', '')}|{method1.get('location', '')}"
        key2 = f"{method2.get('game', '')}|{method2.get('method', '')}|{method2.get('location', '')}"
        return key1 == key2

    def scrape_and_process_pokemon(self, pokemon_name, generation, number=None, real_url=None):
        """Scrape complètement un Pokemon avec logging complet."""
        self.stats['total_processed'] += 1
        details_url = real_url
        
        try:
            self.logger.info(f"[{self.stats['total_processed']}] Début scraping: {pokemon_name} (Gen {generation})")
            
            # Étape 1 : Télécharger le sprite
            sprite_filename = self.download_sprite(pokemon_name, generation, number)
            sprite_downloaded = sprite_filename is not None
            
            # Étape 2 : Utiliser l'URL réelle ou la construire en fallback
            if not details_url:
            details_url = self.build_pokemon_details_url(pokemon_name, generation)
                self.logger.warning(f"URL construite en fallback: {details_url}")
            else:
                # Construire l'URL complète si nécessaire
                if details_url.startswith('/'):
                    details_url = self.base_url + details_url
                self.logger.debug(f"URL réelle utilisée: {details_url}")
            
            # Étape 3 : Récupérer la page de détails
            html_content = self.get_page(details_url)
            if not html_content:
                raise Exception("Impossible de récupérer le contenu HTML")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Étape 4 : Parser les détails
            details = self.parse_pokemon_details_v2(soup, pokemon_name)
            methods_count = len(details['general_methods']) + len(details['specific_methods'])
            games_count = len(details['games'])
            
            self.logger.debug(f"Parsing terminé: {methods_count} méthodes, {games_count} jeux")
            
            # Étape 5 : Détecter le shiny lock
            is_shiny_lock = self.detect_shiny_lock(soup, pokemon_name)
            
            # Étape 6 : Télécharger l'image haute qualité
            high_quality_filename = self.download_high_quality_image(soup, pokemon_name, generation, number)
            hq_image_downloaded = high_quality_filename is not None
            
            # Étape 7 : Préparer les informations du Pokemon
            pokemon_info = {
                'name': pokemon_name,
                'number': number or "XXX",
                'generation': generation,
                'sprite_url': sprite_filename,
                'high_quality_image': high_quality_filename
            }
            
            # Étape 8 : Sauvegarder en base de données
            success = self.save_pokemon_to_database_v2(
                pokemon_info, 
                sprite_filename, 
                details, 
                is_shiny_lock
            )
            
            if success:
                # Log du succès avec détails
                self.log_success(pokemon_name, generation, {
                    'sprite_downloaded': sprite_downloaded,
                    'hq_image_downloaded': hq_image_downloaded,
                    'methods_count': methods_count,
                    'games_count': games_count,
                    'is_shiny_lock': is_shiny_lock
                })
                return True
            else:
                raise Exception("Erreur lors de la sauvegarde en base de données")
                
        except requests.exceptions.HTTPError as e:
            self.log_error("HTTP_ERROR", pokemon_name, generation, details_url or "URL inconnue", e, 
                         f"Code HTTP: {e.response.status_code if e.response else 'inconnu'}")
            return False
        except requests.exceptions.Timeout as e:
            self.log_error("TIMEOUT", pokemon_name, generation, details_url or "URL inconnue", e, 
                         "Délai d'attente dépassé")
            return False
        except requests.exceptions.RequestException as e:
            self.log_error("NETWORK_ERROR", pokemon_name, generation, details_url or "URL inconnue", e, 
                         "Erreur réseau")
            return False
        except Exception as e:
            # Déterminer le type d'erreur plus précisément
            if "404" in str(e) or "not found" in str(e).lower():
                error_type = "PAGE_NOT_FOUND"
            elif "parse" in str(e).lower() or "beautifulsoup" in str(e).lower():
                error_type = "PARSING_ERROR"
            elif "database" in str(e).lower() or "sqlite" in str(e).lower():
                error_type = "DATABASE_ERROR"
            else:
                error_type = "UNKNOWN_ERROR"
                
            self.log_error(error_type, pokemon_name, generation, details_url or "URL inconnue", e)
            return False

    def scrape_generation_complete(self, generation):
        """Scrape complètement une génération avec logging détaillé."""
        gen_start_time = datetime.now()
        self.logger.info(f"=== DÉBUT GÉNÉRATION {generation} ===")
        
        # URL de la page de génération
        generation_url = f"{self.base_url}/page/jeuxvideo/dossier_shasse/pokedex_shasse/portail/{generation}g"
        self.logger.info(f"URL génération: {generation_url}")
        
        try:
        # Récupérer la page
        html_content = self.get_page(generation_url)
        if not html_content:
                self.logger.error(f"Impossible de récupérer la page génération {generation}")
            return 0, 0
        
        # Parser la page
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Trouver tous les liens Pokemon
        pokemon_links = soup.find_all('a', href=re.compile(r'/page/jeuxvideo/dossier_shasse/pokedex_shasse/\d+g/'))
        
        if not pokemon_links:
                self.logger.warning(f"Aucun Pokemon trouvé dans la génération {generation}")
            return 0, 0
        
            self.logger.info(f"🎯 {len(pokemon_links)} Pokemon trouvés dans la génération {generation}")
            
            # Traiter chaque Pokemon
            gen_success = 0
            gen_errors = 0
        
        for i, pokemon_link in enumerate(pokemon_links, 1):
                # ✅ CORRECTION : Extraire le VRAI lien au lieu de le reconstruire
                real_url = pokemon_link.get('href')
            
            # Extract number from link text if available
            text = pokemon_link.get_text().strip()
            number = self.extract_pokemon_number_from_text(text)
            if number is None:
                sprite_url = pokemon_link.find('img') and pokemon_link.find('img').get('src')
                number = self.extract_pokemon_number_from_sprite_url(sprite_url)
            
            # Extract Pokemon name from text (remove number)
            pokemon_name = re.sub(r'#\d+\s*', '', text).strip()
            
                self.logger.debug(f"[{i}/{len(pokemon_links)}] Processing: {pokemon_name} (#{number})")
                self.logger.debug(f"URL réelle: {real_url}")
                
                # ✅ CORRECTION : Passer l'URL réelle au scraper
                if self.scrape_and_process_pokemon(pokemon_name, generation, number, real_url):
                    gen_success += 1
            else:
                    gen_errors += 1
            
                # Pause entre chaque Pokemon pour éviter la surcharge
            time.sleep(0.5)
        
                # Log périodique des stats
                if i % 10 == 0:
                    current_rate = (gen_success / i * 100) if i > 0 else 0
                    self.logger.info(f"Progression Gen {generation}: {i}/{len(pokemon_links)} ({current_rate:.1f}% succès)")
            
            # Statistiques finales de la génération
            gen_duration = datetime.now() - gen_start_time
            gen_total = gen_success + gen_errors
            gen_rate = (gen_success / gen_total * 100) if gen_total > 0 else 0
            
            self.logger.info(f"=== FIN GÉNÉRATION {generation} ===")
            self.logger.info(f"Durée: {gen_duration}")
            self.logger.info(f"Traités: {gen_total}")
            self.logger.info(f"Succès: {gen_success} ({gen_rate:.1f}%)")
            self.logger.info(f"Erreurs: {gen_errors}")
            
            return gen_success, gen_errors
            
        except Exception as e:
            self.log_error("GENERATION_ERROR", f"Generation_{generation}", generation, generation_url, e, 
                         "Erreur lors du scraping de la génération")
            return 0, 1

    def scrape_all_complete(self):
        """Scrape complètement toutes les générations avec logging et statistiques finales."""
        self.logger.info("🚀 DÉMARRAGE DU SCRAPING COMPLET V2")
        self.logger.info("=" * 50)
        
        total_success = 0
        total_errors = 0
        
        # Parcourir toutes les générations
        for generation in range(1, 10):  # 1 à 9
            try:
                self.logger.info(f"\n🎯 Traitement génération {generation}/9")
                success, errors = self.scrape_generation_complete(generation)
                total_success += success
                total_errors += errors
                
                # Pause entre les générations
                self.logger.info(f"⏸️ Pause avant génération suivante...")
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"💥 Erreur génération {generation}: {e}")
                total_errors += 1
                continue
        
        # Statistiques finales globales
        self.logger.info(f"\n🎉 SCRAPING TERMINÉ !")
        self.logger.info("=" * 50)
        
        # Utiliser les stats intégrées + totaux
        final_total = self.stats['total_processed']
        final_success = self.stats['success_count']
        final_errors = self.stats['error_count']
        final_rate = (final_success / final_total * 100) if final_total > 0 else 0
        
        self.logger.info(f"✅ Total succès: {final_success}")
        self.logger.info(f"❌ Total erreurs: {final_errors}")
        self.logger.info(f"📊 Taux de réussite: {final_rate:.1f}%")
        
        # Log des statistiques finales détaillées
        self.log_stats()
        
        # Résumé pour la console
        print(f"\n🎉 SCRAPING TERMINÉ !")
        print("=" * 50)
        print(f"✅ Total succès: {final_success}")
        print(f"❌ Total erreurs: {final_errors}")
        print(f"📊 Taux de réussite: {final_rate:.1f}%")
        
        if self.stats['error_types']:
            print(f"\n📋 Top 5 types d'erreurs:")
            sorted_errors = sorted(self.stats['error_types'].items(), key=lambda x: x[1], reverse=True)
            for error_type, count in sorted_errors[:5]:
                percentage = (count / final_errors * 100) if final_errors > 0 else 0
                print(f"  {error_type}: {count} ({percentage:.1f}%)")
        
        print(f"\n📁 Logs détaillés disponibles dans le dossier 'logs/'")
        
        return final_success, final_errors

    def test_single_pokemon(self, pokemon_name, generation):
        """Test sur un seul Pokemon avec logging."""
        self.logger.info(f"🧪 TEST SIMPLE: {pokemon_name} (Gen {generation})")
        
        try:
        # Aller chercher dans la page de génération
        generation_url = f"{self.base_url}/page/jeuxvideo/dossier_shasse/pokedex_shasse/portail/{generation}g"
        html_content = self.get_page(generation_url)
        
        if not html_content:
                self.logger.error("Impossible de récupérer la page de génération")
            return False
        
        soup = BeautifulSoup(html_content, 'html.parser')
        pokemon_links = soup.find_all('a', href=re.compile(r'/page/jeuxvideo/dossier_shasse/pokedex_shasse/\d+g/'))
        
        # Chercher le Pokemon
        for link in pokemon_links:
            text = link.get_text().strip()
            if pokemon_name.lower() in text.lower():
                    # ✅ CORRECTION : Extraire l'URL réelle
                    real_url = link.get('href')
                    
                    self.logger.info(f"🎯 Pokemon trouvé: {text}")
                    self.logger.debug(f"URL réelle: {real_url}")
                    
                # Extract number from link text if available
                number = self.extract_pokemon_number_from_text(text)
                if number is None:
                    sprite_url = link.find('img') and link.find('img').get('src')
                    number = self.extract_pokemon_number_from_sprite_url(sprite_url)
                
                # Extract Pokemon name from text (remove number)
                clean_pokemon_name = re.sub(r'#\d+\s*', '', text).strip()
                
                    # ✅ CORRECTION : Passer l'URL réelle au scraper
                    result = self.scrape_and_process_pokemon(clean_pokemon_name, generation, number, real_url)
                    
                    # Log final du test
                    if result:
                        self.logger.info(f"✅ Test réussi pour {pokemon_name}")
                    else:
                        self.logger.error(f"❌ Test échoué pour {pokemon_name}")
                    
                    # Afficher les statistiques du test
                    self.log_stats()
                    return result
            
            self.logger.warning(f"❌ Pokemon {pokemon_name} non trouvé dans la génération {generation}")
            return False
            
        except Exception as e:
            generation_url = f"{self.base_url}/page/jeuxvideo/dossier_shasse/pokedex_shasse/portail/{generation}g"
            self.log_error("TEST_ERROR", pokemon_name, generation, generation_url, e, "Erreur lors du test")
        return False

if __name__ == "__main__":
    import sys
    
    scraper = PokemonScraperV2()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            # Scraping complet de tout
            scraper.scrape_all_complete()
        elif sys.argv[1] == "gen" and len(sys.argv) >= 3:
            # Scraping d'une génération spécifique
            generation = int(sys.argv[2])
            scraper.scrape_generation_complete(generation)
        elif sys.argv[1] == "test" and len(sys.argv) >= 4:
            # Test sur un Pokemon spécifique
            pokemon_name = sys.argv[2]
            generation = int(sys.argv[3])
            scraper.test_single_pokemon(pokemon_name, generation)
        else:
            print("Usage:")
            print("  python pokemon_scraper_v2.py all                    # Scrape tout")
            print("  python pokemon_scraper_v2.py gen <num>              # Scrape génération")
            print("  python pokemon_scraper_v2.py test <pokemon> <gen>   # Test un Pokemon")
    else:
        # Par défaut: Test avec Bulbizarre
        print("Scraper V2 avec nouveau modèle BDD prêt !")
        print("🧪 Test par défaut avec Bulbizarre...")
        scraper.test_single_pokemon("bulbizarre", 1) 