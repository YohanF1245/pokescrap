import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
from urllib.parse import urljoin, urlparse
from database_v2 import DatabaseManagerV2

class PokemonScraperV2:
    def __init__(self):
        self.base_url = "https://www.pokebip.com"
        self.db = DatabaseManagerV2("pokemon_shasse.db")  # ✅ Utiliser V2 avec nom standard
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Créer le dossier assets si il n'existe pas
        os.makedirs("assets", exist_ok=True)
        for gen in range(1, 10):
            os.makedirs(f"assets/gen_{gen}", exist_ok=True)
    
    def get_page(self, url):
        """Récupère le contenu d'une page web avec gestion des erreurs."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération de {url}: {e}")
            return None
    
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
        """Télécharge le sprite d'un Pokemon."""
        try:
            # Construire l'URL du sprite
            sprite_url = self.build_sprite_url(pokemon_name, generation, pokemon_number)
            if not sprite_url:
                print(f"    ❌ Impossible de construire l'URL du sprite pour {pokemon_name}")
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
            
            # Télécharger le sprite
            print(f"    🖼️ Téléchargement sprite: {sprite_url}")
            response = self.session.get(sprite_url)
            if response.status_code == 200:
                with open(sprite_path, 'wb') as f:
                    f.write(response.content)
                print(f"    ✅ Sprite sauvegardé: {sprite_path}")
                return sprite_path
            else:
                print(f"    ❌ Erreur téléchargement sprite: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    ❌ Erreur téléchargement sprite: {e}")
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
        """Parse un tableau de méthodes avec gestion des cellules complexes - VERSION AMÉLIORÉE."""
        methods = []
        rows = table.find_all('tr')[1:]  # Skip header
        
        current_game = None
        
        for row in rows:
            cols = row.find_all(['th', 'td'])
            
            # ✅ NOUVEAU : Reconstruction intelligente des colonnes
            normalized_data = self.normalize_row_data(cols)
            
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
                    
                    # Construire les conditions complètes
                    conditions_parts = []
                    if method_data.get('level'):
                        conditions_parts.append(f"Niveau {method_data['level']}")
                    if method_data.get('conditions'):
                        conditions_parts.append(method_data['conditions'])
                    
                    full_conditions = " | ".join(conditions_parts) if conditions_parts else None
                    
                    details['specific_methods'].append({
                        'name': method_data['method'],
                        'game': method_data['game'],
                        'location': method_data['location'],
                        'probability': method_data['probability'],
                        'category': method_category['category'],
                        'description': method_category['description'],
                        'conditions': full_conditions
                    })
                    
                    methods.append(method_data)
                    
                    # Update current game only if we found a valid one
                    if method_data['game']:
                        current_game = method_data['game']
        
        return methods
    
    def normalize_row_data(self, cols):
        """Normalise les données d'une ligne en détectant le contenu réel."""
        if len(cols) < 2:
            return None
        
        # Extraire tout le texte disponible
        all_texts = [col.get_text(strip=True) for col in cols]
        all_html = [str(col) for col in cols]
        
        # ✅ NOUVEAU : Détecter les patterns pour réorganiser les données
        result = {'game': '', 'method': '', 'location': '', 'probability': '', 'sprites': []}
        
        # Analyser chaque cellule pour détecter son type de contenu
        for i, (text, html) in enumerate(zip(all_texts, all_html)):
            content_type = self.detect_content_type(text, html)
            
            if content_type == 'game' and not result['game']:
                result['game'] = text
            elif content_type == 'method' and not result['method']:
                result['method'] = text
            elif content_type == 'location' and not result['location']:
                result['location'] = text
                # Extraire les sprites Pokemon de cette cellule
                result['sprites'] = self.extract_pokemon_sprites_from_html(html)
            elif content_type == 'probability' and not result['probability']:
                result['probability'] = text
        
        # ✅ NOUVEAU : Si pas de répartition claire, utiliser l'ordre par défaut
        if not any([result['game'], result['method'], result['location']]):
            if len(all_texts) >= 3:
                # Essayer de détecter si le premier élément est composite
                first_text = all_texts[0]
                if self.is_composite_method_game(first_text):
                    # C'est probablement "JeuMéthode" collés
                    game, method = self.split_composite_method_game(first_text)
                    result['game'] = game
                    result['method'] = method
                    result['location'] = all_texts[1] if len(all_texts) > 1 else ''
                    result['probability'] = all_texts[2] if len(all_texts) > 2 else ''
                else:
                    result['game'] = all_texts[0]
                    result['method'] = all_texts[1]
                    result['location'] = all_texts[2]
                    result['probability'] = all_texts[3] if len(all_texts) > 3 else ''
        
        return result if any([result['game'], result['method'], result['location']]) else None
    
    def detect_content_type(self, text: str, html: str) -> str:
        """Détecte le type de contenu d'une cellule."""
        text_lower = text.lower()
        
        # Probabilité (contient % ou des ratios)
        if re.search(r'\d+%|tc\s*=|\d+/\d+', text_lower):
            return 'probability'
        
        # Jeu (noms connus)
        known_games = ['rouge', 'bleu', 'jaune', 'or', 'argent', 'cristal', 'rubis', 'saphir', 'émeraude',
                      'diamant', 'perle', 'platine', 'heartgold', 'soulsilver', 'noir', 'blanc',
                      'écarlate', 'violet', 'épée', 'bouclier']
        if any(game in text_lower for game in known_games):
            return 'game'
        
        # Méthode (contient des mots-clés de méthodes)
        method_keywords = ['rencontre', 'reset', 'surf', 'pêche', 'sandwich', 'repousse', 'scanner']
        if any(keyword in text_lower for keyword in method_keywords):
            return 'method'
        
        # Localisation (contient des images Pokemon ou des noms de lieux)
        if '<img' in html or any(loc in text_lower for loc in ['route', 'chemin', 'mont', 'tour', 'manoir', 'val']):
            return 'location'
        
        return 'unknown'
    
    def is_composite_method_game(self, text: str) -> bool:
        """Détecte si le texte contient jeu+méthode collés."""
        # Patterns typiques : "RougeRencontre", "RencontreRepousse niv. 28"
        method_patterns = [
            r'[A-Za-z]+(?:Rencontre|Reset|Surf|Pêche|Sandwich)',
            r'(?:Rencontre|Reset|Surf|Pêche|Sandwich)[A-Za-z\s]+niv\.\s*\d+',
            r'[A-Za-z]+(?:Repousse|Scanner)',
        ]
        
        return any(re.search(pattern, text) for pattern in method_patterns)
    
    def split_composite_method_game(self, text: str) -> tuple:
        """Sépare un texte composite jeu+méthode."""
        # Essayer différents patterns de séparation
        
        # Pattern 1: "GameMethod" -> chercher où commence la méthode
        method_starts = ['Rencontre', 'Reset', 'Surf', 'Pêche', 'Sandwich', 'Scanner']
        for method_start in method_starts:
            if method_start in text:
                parts = text.split(method_start, 1)
                if len(parts) == 2:
                    return parts[0].strip(), (method_start + parts[1]).strip()
        
        # Pattern 2: "MethodGame" avec niveau -> "RencontreRepousse niv. X"
        if 'niv.' in text:
            # Prendre tout comme méthode, pas de jeu
            return '', text.strip()
        
        # Fallback: tout dans méthode
        return '', text.strip()
    
    def extract_pokemon_sprites_from_html(self, html: str) -> list:
        """Extrait les noms des Pokemon depuis les sprites dans le HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        sprites = soup.find_all('img')
        
        pokemon_names = []
        for sprite in sprites:
            alt_text = sprite.get('alt', '')
            if alt_text and alt_text not in pokemon_names:
                pokemon_names.append(alt_text)
        
        return pokemon_names
    
    def parse_single_method_improved(self, data: dict, current_game: str):
        """Parse une méthode depuis les données normalisées - VERSION AMÉLIORÉE."""
        game = data['game'] or current_game
        method = data['method']
        location = data['location']
        probability = data['probability']
        sprites = data.get('sprites', [])
        
        if not game and not method:
            return None
        
        # ✅ NOUVEAU : Parser la méthode pour extraire niveau et conditions
        level, conditions = self.parse_method_details_improved(method)
        
        # Nettoyer les noms
        game = self.clean_game_name(game)
        method = self.clean_method_name_improved(method)
        location = self.clean_location_name_improved(location)
        probability = self.clean_probability_improved(probability)
        
        return {
            'game': game,
            'method': method,
            'location': location,
            'probability': probability,
            'level': level,
            'conditions': conditions,
            'pokemon_sprites': sprites
        }
    
    def parse_method_details_improved(self, method_text: str) -> tuple:
        """Extrait niveau et conditions d'une méthode."""
        level = None
        conditions = None
        
        # Extraire niveau
        level_match = re.search(r'niv\.\s*(\d+)', method_text)
        if level_match:
            level = int(level_match.group(1))
        
        # Extraire conditions spéciales
        if 'Aura Porte-Bonheur' in method_text:
            conditions = 'Aura Porte-Bonheur'
        elif 'Sandwich' in method_text:
            sandwich_match = re.search(r'Sandwich\s+(\w+)\s+N\.(\d+)', method_text)
            if sandwich_match:
                conditions = f"Sandwich {sandwich_match.group(1)} Niveau {sandwich_match.group(2)}"
        elif 'Repousse' in method_text:
            conditions = 'Avec Repousse'
        
        return level, conditions
    
    def clean_method_name_improved(self, method: str) -> str:
        """Nettoie le nom de la méthode - VERSION AMÉLIORÉE."""
        if not method:
            return ''
        
        # Supprimer les détails pour garder la méthode de base
        method = re.sub(r'\s*niv\.\s*\d+.*', '', method)
        method = re.sub(r'\s*N\.\d+.*', '', method)
        method = re.sub(r'\s*Aura.*', '', method)
        method = re.sub(r'\s*Repousse.*', '', method)
        method = re.sub(r'Durant\s*l\'aventure', '', method)
        
        return method.strip()
    
    def clean_location_name_improved(self, location: str) -> str:
        """Nettoie le nom de la localisation - VERSION AMÉLIORÉE."""
        if not location:
            return ''
        
        # Supprimer les infos de TC si présentes
        location = re.sub(r'TC\s*=.*', '', location)
        location = re.sub(r'\d+%.*', '', location)
        return location.strip()
    
    def clean_probability_improved(self, prob: str) -> str:
        """Nettoie la probabilité - VERSION AMÉLIORÉE."""
        if not prob:
            return ''
        
        # Extraire seulement le pourcentage principal
        prob_match = re.search(r'(\d+(?:\.\d+)?%)', prob)
        return prob_match.group(1) if prob_match else prob.strip()

    def clean_game_name(self, game_name):
        """Nettoie le nom du jeu extrait du HTML."""
        if not game_name:
            return ""
        
        # Supprimer les éléments HTML restants
        game_name = game_name.strip()
        
        # Mappage des noms courts vers les noms complets
        game_mapping = {
            'R': 'Rouge',
            'B': 'Bleu',
            'J': 'Jaune',
            'O': 'Or',
            'A': 'Argent',
            'C': 'Cristal',
            'RF': 'Rouge Feu',
            'VF': 'Vert Feuille',
            'D': 'Diamant',
            'P': 'Perle',
            'Pl': 'Platine',
            'HG': 'HeartGold',
            'SS': 'SoulSilver',
            'N': 'Noir',
            'B2': 'Blanc 2',
            'N2': 'Noir 2',
            'RO': 'Rubis Oméga',
            'SA': 'Saphir Alpha',
            'So': 'Soleil',
            'Lu': 'Lune',
            'US': 'Ultra-Soleil',
            'UL': 'Ultra-Lune',
            'LGP': 'LG: Pikachu',
            'LGE': 'LG: Évoli',
            'Ep': 'Épée',
            'Bo': 'Bouclier',
            'DE': 'Diamant Étincelant',
            'PE': 'Perle Scintillante',
            'LéA': 'Légendes Pokémon: Arceus',
            'Ec': 'Écarlate',
            'Vi': 'Violet',
            'EV': 'Écarlate/Violet'
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
        """Détecte la génération à partir du nom du jeu."""
        generation_map = {
            # 1G
            'Rouge': 1, 'Bleu': 1, 'Jaune': 1,
            # 2G
            'Or': 2, 'Argent': 2, 'Cristal': 2,
            # 3G
            'Rubis': 3, 'Saphir': 3, 'Émeraude': 3, 'Rouge Feu': 3, 'Vert Feuille': 3,
            # 4G
            'Diamant': 4, 'Perle': 4, 'Platine': 4, 'HeartGold': 4, 'SoulSilver': 4,
            # 5G
            'Noir': 5, 'Blanc': 5, 'Noir 2': 5, 'Blanc 2': 5,
            # 6G
            'X': 6, 'Y': 6, 'Rubis Oméga': 6, 'Saphir Alpha': 6,
            # 7G
            'Soleil': 7, 'Lune': 7, 'Ultra-Soleil': 7, 'Ultra-Lune': 7,
            'LG: Pikachu': 7, 'LG: Évoli': 7,
            # 8G
            'Épée': 8, 'Bouclier': 8, 'Diamant Étincelant': 8, 'Perle Scintillante': 8,
            'Légendes Pokémon: Arceus': 8,
            # 9G
            'Écarlate': 9, 'Violet': 9, 'EV': 9
        }
        
        for game, gen in generation_map.items():
            if game.lower() in game_name.lower():
                return gen
        
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
        """Sauvegarde un Pokemon avec le nouveau modèle V2."""
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
            
            # ✅ NOUVEAU : Sauvegarder les méthodes SPÉCIFIQUES
            for method_data in details['specific_methods']:
                try:
                    method_id = self.db.insert_hunt_method(
                        name=method_data['name'],
                        description=method_data['description'],
                        is_general=False,
                        category=method_data['category']
                    )
                    
                    # Insérer la localisation
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
                            conditions=method_data.get('conditions')
                        )
                        
                        print(f"      🎯 Méthode spécifique sauvegardée: {method_data['name']} dans {method_data['game']}")
                    
                except Exception as e:
                    print(f"      ⚠️ Erreur sauvegarde méthode spécifique {method_data['name']}: {e}")
            
            print(f"    ✅ Toutes les données sauvegardées pour {pokemon_info['name']}")
            return True
            
        except Exception as e:
            print(f"    ❌ Erreur sauvegarde Pokemon: {e}")
            return False

    def scrape_and_process_pokemon(self, pokemon_name, generation, number=None):
        """Scrape complètement un Pokemon : sprite, image HQ, détails et sauvegarde."""
        try:
            print(f"\n🔍 Scraping {pokemon_name} (Gen {generation})")
            
            # Étape 1 : Télécharger le sprite
            sprite_filename = self.download_sprite(pokemon_name, generation, number)
            if not sprite_filename:
                print(f"    ❌ Impossible de télécharger le sprite pour {pokemon_name}")
                return False
            
            # Étape 2 : Scraper les détails depuis la page
            details_url = self.build_pokemon_details_url(pokemon_name, generation)
            print(f"    🌐 URL détails: {details_url}")
            
            response = self.session.get(details_url)
            if response.status_code != 200:
                print(f"    ❌ Erreur HTTP {response.status_code} pour {details_url}")
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Étape 3 : Parser les détails avec le nouveau modèle V2
            details = self.parse_pokemon_details_v2(soup, pokemon_name)
            
            # Étape 4 : Détecter le shiny lock
            is_shiny_lock = self.detect_shiny_lock(soup, pokemon_name)
            print(f"    🔒 Shiny lock: {is_shiny_lock}")
            
            # Étape 5 : Télécharger l'image haute qualité
            high_quality_filename = self.download_high_quality_image(soup, pokemon_name, generation, number)
            if high_quality_filename:
                print(f"    🖼️ Image HQ téléchargée: {high_quality_filename}")
            
            # Étape 6 : Préparer les informations du Pokemon
            pokemon_info = {
                'name': pokemon_name,
                'number': number or "XXX",
                'generation': generation,
                'sprite_url': sprite_filename,
                'high_quality_image': high_quality_filename
            }
            
            # Étape 7 : Sauvegarder en base de données avec le nouveau modèle
            success = self.save_pokemon_to_database_v2(
                pokemon_info, 
                sprite_filename, 
                details, 
                is_shiny_lock
            )
            
            if success:
                print(f"    ✅ {pokemon_name} complètement processé!")
                return True
            else:
                print(f"    ❌ Erreur sauvegarde pour {pokemon_name}")
                return False
                
        except Exception as e:
            print(f"    ❌ Erreur scraping {pokemon_name}: {e}")
            return False

    def scrape_generation_complete(self, generation):
        """Scrape complètement une génération : liste + détails + sprites."""
        print(f"\n🎯 === GÉNÉRATION {generation} ===")
        
        # URL de la page de génération
        generation_url = f"{self.base_url}/page/jeuxvideo/dossier_shasse/pokedex_shasse/portail/{generation}g"
        print(f"📄 Page: {generation_url}")
        
        # Récupérer la page
        html_content = self.get_page(generation_url)
        if not html_content:
            print(f"❌ Impossible de récupérer la page génération {generation}")
            return 0, 0
        
        # Parser la page
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Trouver tous les liens Pokemon
        pokemon_links = soup.find_all('a', href=re.compile(r'/page/jeuxvideo/dossier_shasse/pokedex_shasse/\d+g/'))
        
        if not pokemon_links:
            print(f"❌ Aucun Pokemon trouvé dans la génération {generation}")
            return 0, 0
        
        print(f"📊 {len(pokemon_links)} Pokemon trouvés")
        
        # Traiter chaque Pokemon IMMÉDIATEMENT
        success_count = 0
        error_count = 0
        
        for i, pokemon_link in enumerate(pokemon_links, 1):
            print(f"\n[{i}/{len(pokemon_links)}]", end=" ")
            
            # Extract number from link text if available
            text = pokemon_link.get_text().strip()
            number = self.extract_pokemon_number_from_text(text)
            if number is None:
                sprite_url = pokemon_link.find('img') and pokemon_link.find('img').get('src')
                number = self.extract_pokemon_number_from_sprite_url(sprite_url)
            
            # Extract Pokemon name from text (remove number)
            pokemon_name = re.sub(r'#\d+\s*', '', text).strip()
            
            # Pass name and number to scrape_and_process_pokemon
            if self.scrape_and_process_pokemon(pokemon_name, generation, number):
                success_count += 1
            else:
                error_count += 1
            
            # Pause entre chaque Pokemon
            time.sleep(0.5)
        
        print(f"\n📈 Génération {generation} terminée:")
        print(f"  ✅ Succès: {success_count}")
        print(f"  ❌ Erreurs: {error_count}")
        
        return success_count, error_count

    def scrape_all_complete(self):
        """Scrape complètement toutes les générations."""
        print("🚀 DÉMARRAGE DU SCRAPING COMPLET V2")
        print("="*50)
        
        total_success = 0
        total_errors = 0
        
        # Parcourir toutes les générations
        for generation in range(1, 10):  # 1 à 9
            try:
                success, errors = self.scrape_generation_complete(generation)
                total_success += success
                total_errors += errors
                
                # Pause entre les générations
                print(f"\n⏸️ Pause avant génération suivante...")
                time.sleep(2)
                
            except Exception as e:
                print(f"💥 Erreur génération {generation}: {e}")
                total_errors += 1
                continue
        
        print(f"\n🎉 SCRAPING TERMINÉ !")
        print("="*50)
        print(f"✅ Total succès: {total_success}")
        print(f"❌ Total erreurs: {total_errors}")
        if total_success + total_errors > 0:
            print(f"📊 Taux de réussite: {total_success/(total_success+total_errors)*100:.1f}%")

    def test_single_pokemon(self, pokemon_name, generation):
        """Test sur un seul Pokemon pour vérifier que tout fonctionne."""
        print(f"🧪 TEST V2: {pokemon_name} (Gen {generation})")
        
        # Aller chercher dans la page de génération
        generation_url = f"{self.base_url}/page/jeuxvideo/dossier_shasse/pokedex_shasse/portail/{generation}g"
        html_content = self.get_page(generation_url)
        
        if not html_content:
            print("❌ Impossible de récupérer la page de génération")
            return False
        
        soup = BeautifulSoup(html_content, 'html.parser')
        pokemon_links = soup.find_all('a', href=re.compile(r'/page/jeuxvideo/dossier_shasse/pokedex_shasse/\d+g/'))
        
        # Chercher le Pokemon
        for link in pokemon_links:
            text = link.get_text().strip()
            if pokemon_name.lower() in text.lower():
                print(f"🎯 Pokemon trouvé: {text}")
                # Extract number from link text if available
                number = self.extract_pokemon_number_from_text(text)
                if number is None:
                    sprite_url = link.find('img') and link.find('img').get('src')
                    number = self.extract_pokemon_number_from_sprite_url(sprite_url)
                
                # Extract Pokemon name from text (remove number)
                clean_pokemon_name = re.sub(r'#\d+\s*', '', text).strip()
                
                return self.scrape_and_process_pokemon(clean_pokemon_name, generation, number)
        
        print(f"❌ Pokemon {pokemon_name} non trouvé dans la génération {generation}")
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