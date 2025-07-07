#!/usr/bin/env python3
"""
Fichier de référence pour les formes régionales Pokémon
Basé sur les sources officielles : Pokémon Wiki, Game8, et Pokébip

Les formes régionales sont des variants d'espèces Pokémon adaptés à des régions spécifiques.
Ils diffèrent des formes normales par leur type, apparence, et parfois leurs évolutions.
"""

# ================================
# FORMES RÉGIONALES OFFICIELLES
# ================================

# Formes d'Alola (18 formes)
# Introduites en Gen 7, uniquement des Pokémon de Gen 1
ALOLAN_FORMS = {
    '019': 'rattata',      # Rattata d'Alola (Dark/Normal)
    '020': 'raticate',     # Raticate d'Alola (Dark/Normal)  
    '026': 'raichu',       # Raichu d'Alola (Electric/Psychic)
    '027': 'sandshrew',    # Sabelette d'Alola (Ice/Steel)
    '028': 'sandslash',    # Sablaireau d'Alola (Ice/Steel)
    '037': 'vulpix',       # Goupix d'Alola (Ice)
    '038': 'ninetales',    # Feunard d'Alola (Ice/Fairy)
    '050': 'diglett',      # Taupiqueur d'Alola (Ground/Steel)
    '051': 'dugtrio',      # Triopikeur d'Alola (Ground/Steel)
    '052': 'meowth',       # Miaouss d'Alola (Dark)
    '053': 'persian',      # Persian d'Alola (Dark)
    '074': 'geodude',      # Racaillou d'Alola (Rock/Electric)
    '075': 'graveler',     # Gravalanch d'Alola (Rock/Electric)
    '076': 'golem',        # Grolem d'Alola (Rock/Electric)
    '088': 'grimer',       # Tadmorv d'Alola (Poison/Dark)
    '089': 'muk',          # Grotadmorv d'Alola (Poison/Dark)
    '103': 'exeggutor',    # Noadkoko d'Alola (Grass/Dragon)
    '105': 'marowak'       # Ossatueur d'Alola (Fire/Ghost)
}

# Formes de Galar (19 formes + évolutions exclusives)
# Introduites en Gen 8, diverses générations
GALARIAN_FORMS = {
    '052': 'meowth',       # Miaouss de Galar (Steel)
    '077': 'ponyta',       # Ponyta de Galar (Psychic)
    '078': 'rapidash',     # Galopa de Galar (Psychic/Fairy)
    '079': 'slowpoke',     # Ramoloss de Galar (Psychic)
    '080': 'slowbro',      # Flagadoss de Galar (Poison/Psychic)
    '083': "farfetch'd",   # Canarticho de Galar (Fighting)
    '110': 'weezing',      # Smogogo de Galar (Poison/Fairy)
    '122': 'mr. mime',     # M. Mime de Galar (Ice/Psychic)
    '144': 'articuno',     # Artikodin de Galar (Psychic/Flying)
    '145': 'zapdos',       # Électhor de Galar (Fighting/Flying)
    '146': 'moltres',      # Sulfura de Galar (Dark/Flying)
    '199': 'slowking',     # Roigada de Galar (Poison/Psychic)
    '222': 'corsola',      # Corayon de Galar (Ghost)
    '263': 'zigzagoon',    # Zigzaton de Galar (Dark/Normal)
    '264': 'linoone',      # Linéon de Galar (Dark/Normal)
    '554': 'darumaka',     # Darumarond de Galar (Ice)
    '555': 'darmanitan',   # Darumacho de Galar (Ice ou Ice/Fire en mode Zen)
    '562': 'yamask',       # Tutafeh de Galar (Ground/Ghost)
    '618': 'stunfisk'      # Limonde de Galar (Ground/Steel)
}

# Évolutions exclusives de Galar
GALARIAN_EVOLUTIONS = {
    '863': 'perrserker',   # Berserkatt (évolution de Miaouss de Galar)
    '864': 'cursola',      # Corayôme (évolution de Corayon de Galar)
    '865': "sirfetch'd",   # Palarticho (évolution de Canarticho de Galar)
    '866': 'mr. rime',     # M. Glaquette (évolution de M. Mime de Galar)
    '862': 'obstagoon',    # Ixon (évolution de Linéon de Galar)
    '867': 'runerigus'     # Tutankafer (évolution de Tutafeh de Galar)
}

# Formes de Hisui (16 formes + évolutions exclusives)
# Introduites en Légendes Arceus, diverses générations
HISUIAN_FORMS = {
    '058': 'growlithe',    # Caninos de Hisui (Fire/Rock)
    '059': 'arcanine',     # Arcanin de Hisui (Fire/Rock)
    '100': 'voltorb',      # Voltorbe de Hisui (Electric/Grass)
    '101': 'electrode',    # Électrode de Hisui (Electric/Grass)
    '157': 'typhlosion',   # Typhlosion de Hisui (Fire/Ghost)
    '211': 'qwilfish',     # Qwilfish de Hisui (Dark/Poison)
    '215': 'sneasel',      # Farfuret de Hisui (Fighting/Poison)
    '503': 'samurott',     # Clamiral de Hisui (Water/Dark)
    '549': 'lilligant',    # Fragilady de Hisui (Grass/Fighting)
    '570': 'zorua',        # Zorua de Hisui (Normal/Ghost)
    '571': 'zoroark',      # Zoroark de Hisui (Normal/Ghost)
    '628': 'braviary',     # Gueriaigle de Hisui (Psychic/Flying)
    '705': 'sliggoo',      # Colimucus de Hisui (Steel/Dragon)
    '706': 'goodra',       # Muplodocus de Hisui (Steel/Dragon)
    '713': 'avalugg',      # Séracrawl de Hisui (Ice/Rock)
    '724': 'decidueye'     # Archéduc de Hisui (Grass/Fighting)
}

# Évolutions exclusives de Hisui
HISUIAN_EVOLUTIONS = {
    '899': 'wyrdeer',      # Cerbyllin (évolution de Cerfrousse de Hisui)
    '900': 'kleavor',      # Hachécateur (évolution de Insécateur avec Roche Noire)
    '901': 'ursaluna',     # Ursaros (évolution d'Ursaring de Hisui)
    '902': 'basculegion',  # Paragruel (évolution de Bargantua à rayures blanches)
    '903': 'sneasler',     # Farfurex (évolution de Farfuret de Hisui)
    '904': 'overqwil'      # Qwilpik (évolution de Qwilfish de Hisui)
}

# Formes de Paldea (2 espèces, Tauros ayant 3 variants)
# Introduites en Gen 9
PALDEAN_FORMS = {
    '128': 'tauros',       # Tauros de Paldea (3 formes : Combat, Combat/Feu, Combat/Eau)
    '194': 'wooper'        # Axoloto de Paldea (Poison/Ground)
}

# Évolution exclusive de Paldea
PALDEAN_EVOLUTIONS = {
    '980': 'clodsire'      # Toxtricity (évolution d'Axoloto de Paldea)
}

# ================================
# FORMES NON-RÉGIONALES
# ================================

# Formes alternatives normales (PAS des formes régionales)
NORMAL_FORMS = {
    # Différences de genre
    'nidoran_m': 'nidoran♂',
    'nidoran_f': 'nidoran♀',
    'meowstic_m': 'mistigrix mâle',
    'meowstic_f': 'mistigrix femelle',
    'indeedee_m': 'wimessir mâle', 
    'indeedee_f': 'wimessir femelle',
    
    # Variations géographiques (pas régionales)
    'vivillon': 'prismillon (motifs selon région du joueur)',
    'shellos_west': 'sancoki ouest',
    'shellos_east': 'sancoki est',
    'gastrodon_west': 'tritosor ouest',
    'gastrodon_east': 'tritosor est',
    
    # Formes alphabétiques
    'unown': 'zarbi (lettres A-Z + ! et ?)',
    
    # Formes saisonnières/météo
    'castform': 'morphéo (normale, solaire, pluviale, neigeuse)',
    'cherrim': 'ceriflor (forme bourgeon et forme floraison)',
    
    # Formes de combat
    'darmanitan_zen': 'darumacho mode transe',
    'wishiwashi_school': 'froussardine forme banc',
    'minior_core': 'météno noyau',
    
    # Rotom (appareils)
    'rotom_heat': 'motisma thermique',
    'rotom_wash': 'motisma lavage',
    'rotom_frost': 'motisma froid',
    'rotom_fan': 'motisma hélice',
    'rotom_mow': 'motisma tonte',
    
    # Formes spéciales mais pas régionales
    'oricorio_baile': 'plumeline flamenco',
    'oricorio_pom_pom': 'plumeline pom-pom', 
    'oricorio_pau': "plumeline hula",
    'oricorio_sensu': 'plumeline buyō'
}

# ================================
# FONCTIONS UTILITAIRES
# ================================

def is_regional_form(pokemon_name):
    """Vérifie si un Pokémon est une vraie forme régionale"""
    name_lower = pokemon_name.lower()
    
    # ✅ CORRECTION MAJEURE : Les noms Pokemon n'ont pas de préfixe XXX_
    # Le préfixe XXX_ est dans le sprite filename, pas dans le nom Pokemon !
    # Donc on vérifie directement les suffixes régionaux
    
    # Patterns RÉELS utilisés dans la base de données
    regional_suffixes = [
        '-a',     # Alola (ex: Feunard-A, Miaouss-A)
        '-g',     # Galar (ex: Canarticho-G, Galopa-G) 
        '-h',     # Hisui (ex: Arcanin-H, Clamiral-H)
        '-p',     # Paldea (ex: Axoloto-P, Tauros-P)
        '-pa',    # Paldea alternatif
        '-hi',    # Hisui alternatif
    ]
    
    return any(suffix in name_lower for suffix in regional_suffixes)

def is_regional_evolution(pokemon_name):
    """Vérifie si c'est une évolution exclusive régionale"""
    name_lower = pokemon_name.lower()
    
    regional_evos = [
        'perrserker', 'cursola', "sirfetch'd", 'mr. rime', 'obstagoon', 'runerigus',
        'wyrdeer', 'kleavor', 'ursaluna', 'basculegion', 'sneasler', 'overqwil',
        'clodsire'
    ]
    
    return any(evo in name_lower for evo in regional_evos)

def get_region_from_name(pokemon_name):
    """Retourne la région d'une forme régionale"""
    name_lower = pokemon_name.lower()
    
    # ✅ CORRECTION : Plus besoin de vérifier le préfixe XXX_
    if '-a' in name_lower:
        return 'alola'
    elif '-g' in name_lower:
        return 'galar'
    elif '-h' in name_lower or '-hi' in name_lower:
        return 'hisui'
    elif '-p' in name_lower or '-pa' in name_lower:
        return 'paldea'
    
    return None

def should_be_in_pokedex_tab(pokemon_name):
    """Détermine si le Pokémon doit rester dans l'onglet pokédex principal"""
    name_lower = pokemon_name.lower()
    
    # Si c'est une forme régionale (XXX_ avec suffixe), va dans onglet régional
    if is_regional_form(pokemon_name):
        return False
    
    # Si c'est une évolution exclusive régionale, va dans onglet régional
    if is_regional_evolution(pokemon_name):
        return False
    
    # Zarbi forme A reste dans le pokédex principal
    if ('zarbi' in name_lower or 'unown' in name_lower):
        if '_a' in name_lower and not any(x in name_lower for x in ['_b', '_c', '_d', '_e', '_f', '_g', '_h']):
            return True
        else:
            return False
    
    # Toutes les autres formes spéciales vont dans "autres formes"
    if should_be_in_other_forms_tab(pokemon_name):
        return False
    
    # Sprites normaux (format: numero_nom.png) vont dans pokédex principal
    # Exclure les sprites XXX_ qui ne sont pas régionaux
    if name_lower.startswith('xxx_'):
        return False
    
    # Tout le reste (sprites normaux) va dans le pokédex principal
    return True

def should_be_in_regional_tab(pokemon_name):
    """Détermine si le Pokémon doit être dans un onglet forme régionale"""
    # Seules les vraies formes régionales (XXX_ avec suffixes régionaux) vont dans les onglets régionaux
    return is_regional_form(pokemon_name)

def should_be_in_other_forms_tab(pokemon_name):
    """Détermine si le Pokémon doit être dans l'onglet 'autres formes'"""
    name_lower = pokemon_name.lower()
    
    # Si c'est une forme régionale, ne va pas dans "autres formes"
    if is_regional_form(pokemon_name):
        return False
    
    # Zarbi : toutes les lettres sauf A vont dans "autres formes"
    if ('zarbi' in name_lower or 'unown' in name_lower):
        return not ('_a' in name_lower and not any(x in name_lower for x in ['_b', '_c', '_d', '_e', '_f', '_g', '_h']))
    
    # Sprites avec préfixe XXX_ qui ne sont pas régionaux = autres formes
    if name_lower.startswith('xxx_') and not is_regional_form(pokemon_name):
        return True
    
    # ✅ AJOUT : Détection spécifique des formes alternatives courantes
    
    # Différences de genre avec patterns spécifiques
    if any(pattern in name_lower for pattern in [' mâle', ' femelle', ' male', ' female', ' m', ' f']):
        # Sauf si c'est juste une lettre isolée comme dans "Zarbi M"
        if not ('zarbi' in name_lower and len(pokemon_name.split()[-1]) == 1):
            return True
    
    # Variations géographiques  
    if any(pattern in name_lower for pattern in [' ouest', ' est', ' west', ' east']):
        return True
    
    # Formes saisonnières et variations de couleur
    if any(pattern in name_lower for pattern in [
        ' blanc', ' bleu', ' jaune', ' orange', ' rouge', ' vert', ' violet', ' noir',
        ' white', ' blue', ' yellow', ' orange', ' red', ' green', ' purple', ' black',
        ' été', ' automne', ' hiver', ' printemps',
        ' summer', ' autumn', ' winter', ' spring'
    ]):
        return True
    
    # Formes spéciales avec tailles
    if any(pattern in name_lower for pattern in [' s', ' m', ' l', ' xl', ' petit', ' grand', ' super']):
        # Sauf Zarbi avec une seule lettre
        if not ('zarbi' in name_lower and len(pokemon_name.split()[-1]) == 1):
            return True
    
    # Formes Rotom avec patterns spécifiques
    if any(base in name_lower for base in ['motisma', 'rotom']):
        if any(forme in name_lower for forme in ['thermique', 'lavage', 'froid', 'hélice', 'tonte', 'heat', 'wash', 'frost', 'fan', 'mow']):
            return True
    
    # Formes Oricorio/Plumeline 
    if any(base in name_lower for base in ['oricorio', 'plumeline']):
        if any(forme in name_lower for forme in ['baile', 'pom-pom', 'pau', 'sensu', 'flamenco', 'pom', 'hula', 'buyō']):
            return True
    
    # Formes spéciales diverses
    special_keywords = [
        'cr.', 'no.', 'dé.', 'sa.', 'blc',  # Lougaroc Cr., Cheniselle Dé., Bargantua Blc
        'éternel', 'authentique', 'contrefaçon',
        'temps passé', 'diurne', 'nocturne',
        'zen', 'transe', 'banc', 'noyau',
        'floraison', 'bourgeon'
    ]
    
    if any(keyword in name_lower for keyword in special_keywords):
        return True
    
    # ✅ NOUVEAU : Si aucun pattern spécifique détecté, c'est un Pokemon normal
    return False

# ================================
# RÉSUMÉ DES RÈGLES
# ================================

"""
RÈGLES DE CLASSIFICATION :

1. ONGLET POKÉDEX PRINCIPAL :
   - Formes de base originales
   - Une seule forme par espèce pour l'intégrité
   - Zarbi forme A (garde une lettre)
   - Castform forme normale
   - Rotom forme normale
   - Etc.

2. ONGLETS FORMES RÉGIONALES :
   - Alola : 18 formes + leurs évolutions 
   - Galar : 19 formes + évolutions exclusives (Obstagoon, Cursola, etc.)
   - Hisui : 16 formes + évolutions exclusives (Wyrdeer, Kleavor, etc.)
   - Paldea : 2 formes + Clodsire

3. ONGLET AUTRES FORMES :
   - Différences de genre (garde que la femelle si doublon)
   - Variations géographiques non-régionales (Shellos, Gastrodon) 
   - Formes Rotom appareils
   - Formes Oricorio
   - Zarbi autres lettres
   - Formes saisonnières/combat supplémentaires
   - Tout ce qui ferait doublon sans être régional
""" 