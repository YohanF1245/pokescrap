// Variables globales
let currentCategory = null;
let currentTab = null;
let statsData = {};
let spriteData = {};
let updateInterval;

// Variables pour le modal des Pokemon manquants
let currentMissingGeneration = null;
let allMissingPokemon = [];
let currentMissingTab = 'all';

// Animation des nombres
function animateNumber(element, start, end, duration = 1000) {
    const startTime = performance.now();
    const startValue = parseInt(start) || 0;
    const endValue = parseInt(end) || 0;
    const difference = endValue - startValue;
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Utiliser une fonction d'easing pour une animation plus fluide
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const currentValue = Math.floor(startValue + (difference * easeOutQuart));
        
        element.textContent = currentValue.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Animation du pourcentage
function animatePercentage(element, start, end, duration = 1000) {
    const startTime = performance.now();
    const startValue = parseFloat(start) || 0;
    const endValue = parseFloat(end) || 0;
    const difference = endValue - startValue;
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const currentValue = startValue + (difference * easeOutQuart);
        
        element.textContent = currentValue.toFixed(1) + '%';
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Mise à jour des statistiques
function updateStats(data) {
    const elements = {
        totalPokemon: document.getElementById('total-pokemon'),
        spritesDownloaded: document.getElementById('sprites-downloaded'),
        downloadPercentage: document.getElementById('download-percentage'),
        totalForms: document.getElementById('total-forms'),
        progressFill: document.getElementById('progress-fill')
    };
    
    // Animer les nombres
    animateNumber(elements.totalPokemon, 
        elements.totalPokemon.textContent.replace(/,/g, ''), 
        data.total_pokemon);
    
    animateNumber(elements.spritesDownloaded, 
        elements.spritesDownloaded.textContent.replace(/,/g, ''), 
        data.sprites_downloaded);
    
    animatePercentage(elements.downloadPercentage, 
        elements.downloadPercentage.textContent.replace('%', ''), 
        data.download_percentage);
    
    animateNumber(elements.totalForms, 
        elements.totalForms.textContent.replace(/,/g, ''), 
        data.total_forms);
    
    // Mettre à jour la barre de progression
    setTimeout(() => {
        elements.progressFill.style.width = data.download_percentage + '%';
    }, 500);
    
    // Mettre à jour les statistiques par génération
    updateGenerationStats(data.generation_stats);
    
    // Mettre à jour les top formes
    updateTopForms(data.top_forms);
    
    // Mettre à jour les Pokemon récents
    updateRecentPokemon(data.recent_pokemon);
}

// Mise à jour des statistiques par génération
function updateGenerationStats(generationStats) {
    const container = document.getElementById('generation-stats');
    container.innerHTML = '';
    
    generationStats.forEach(stat => {
        const [generation, total, withSprites] = stat;
        const percentage = total > 0 ? (withSprites / total * 100).toFixed(1) : 0;
        
        const statElement = document.createElement('div');
        statElement.className = 'generation-stat fade-in';
        statElement.style.cursor = 'pointer';
        statElement.onclick = () => showMissingPokemon(generation);
        statElement.innerHTML = `
            <div class="gen-info">
                <div class="generation-badge">${generation}</div>
                <div>
                    <div style="font-weight: 500;">Génération ${generation}</div>
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">
                        ${withSprites}/${total} sprites (${percentage}%)
                    </div>
                </div>
            </div>
            <div class="generation-progress">
                <div class="generation-progress-bar">
                    <div class="generation-progress-fill" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
        
        container.appendChild(statElement);
    });
}

// Mise à jour des top formes
function updateTopForms(topForms) {
    const container = document.getElementById('top-forms');
    container.innerHTML = '';
    
    if (topForms.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 1rem;">Aucune forme trouvée</p>';
        return;
    }
    
    topForms.forEach(form => {
        const [formName, count] = form;
        
        const formElement = document.createElement('div');
        formElement.className = 'form-item fade-in';
        formElement.innerHTML = `
            <div style="font-weight: 500;">${formName}</div>
            <div class="form-badge">${count}</div>
        `;
        
        container.appendChild(formElement);
    });
}

// Mise à jour des Pokemon récents
function updateRecentPokemon(recentPokemon) {
    const container = document.getElementById('recent-pokemon');
    container.innerHTML = '';
    
    if (recentPokemon.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 1rem;">Aucun Pokemon récent</p>';
        return;
    }
    
    recentPokemon.forEach(pokemon => {
        const [name, generation, spritePath] = pokemon;
        
        const pokemonElement = document.createElement('div');
        pokemonElement.className = 'recent-item fade-in';
        pokemonElement.innerHTML = `
            <div class="recent-sprite">
                ${spritePath ? `<img src="/assets/${spritePath}" alt="${name}" onerror="this.style.display='none'">` : ''}
            </div>
            <div>
                <div style="font-weight: 500;">${name}</div>
                <div style="color: var(--text-secondary); font-size: 0.875rem;">Gen ${generation}</div>
            </div>
        `;
        
        container.appendChild(pokemonElement);
    });
}

// Mise à jour des onglets avec les nouvelles catégories
function updateGenerationTabs(spriteData) {
    const container = document.getElementById('generation-tabs');
    container.innerHTML = '';
    
    if (!spriteData || typeof spriteData !== 'object') {
        console.error('Invalid sprite data:', spriteData);
        return;
    }
    
    let tabIndex = 0;
    
    // Ajouter les onglets des générations
    if (spriteData.generations && Object.keys(spriteData.generations).length > 0) {
        const sortedGens = Object.keys(spriteData.generations).sort((a, b) => parseInt(a) - parseInt(b));
        sortedGens.forEach(genNum => {
            const genData = spriteData.generations[genNum];
            if (genData && genData.sprites && genData.sprites.length > 0) {
                const tab = document.createElement('div');
                tab.className = 'generation-tab';
                const spriteCount = genData.sprites.length;
                
                tab.innerHTML = `${genData.name} <span style="opacity: 0.7;">(${spriteCount})</span>`;
                tab.onclick = () => selectCategory(genData);
                
                // Sélectionner le premier onglet par défaut
                if (tabIndex === 0 && !currentCategory) {
                    currentCategory = genData;
                    tab.classList.add('active');
                }
                
                container.appendChild(tab);
                tabIndex++;
            }
        });
    }
    
    // Ajouter les onglets des formes régionales
    if (spriteData.regional_forms && Object.keys(spriteData.regional_forms).length > 0) {
        Object.keys(spriteData.regional_forms).forEach(regionKey => {
            const regionData = spriteData.regional_forms[regionKey];
            if (regionData && regionData.sprites && regionData.sprites.length > 0) {
                const tab = document.createElement('div');
                tab.className = 'generation-tab regional-tab';
                const spriteCount = regionData.sprites.length;
                
                tab.innerHTML = `${regionData.name} <span style="opacity: 0.7;">(${spriteCount})</span>`;
                tab.onclick = () => selectCategory(regionData);
                
                container.appendChild(tab);
            }
        });
    }
    
    // Ajouter l'onglet des autres formes
    if (spriteData.other_forms && Object.keys(spriteData.other_forms).length > 0) {
        Object.keys(spriteData.other_forms).forEach(formKey => {
            const formData = spriteData.other_forms[formKey];
            if (formData && formData.sprites && formData.sprites.length > 0) {
                const tab = document.createElement('div');
                tab.className = 'generation-tab special-tab';
                const spriteCount = formData.sprites.length;
                
                tab.innerHTML = `${formData.name} <span style="opacity: 0.7;">(${spriteCount})</span>`;
                tab.onclick = () => selectCategory(formData);
                
                container.appendChild(tab);
            }
        });
    }
    
    // Afficher la galerie pour la catégorie sélectionnée
    if (currentCategory) {
        updateSpriteGallery(currentCategory);
    }
}

// Sélection d'une catégorie (génération, forme régionale, ou forme spéciale)
function selectCategory(categoryData) {
    currentCategory = categoryData;
    
    // Mettre à jour l'état actif des onglets
    document.querySelectorAll('.generation-tab').forEach(tab => {
        tab.classList.remove('active');
        // Vérifier si l'onglet correspond à la catégorie sélectionnée
        if (tab.innerHTML.includes(categoryData.name)) {
            tab.classList.add('active');
        }
    });
    
    // Mettre à jour la galerie de sprites
    updateSpriteGallery(categoryData);
}

// Mise à jour de la galerie de sprites avec la nouvelle structure
function updateSpriteGallery(categoryData) {
    const container = document.getElementById('sprite-grid');
    container.innerHTML = '';
    
    if (!categoryData || categoryData.sprites.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 2rem; grid-column: 1/-1;">Aucun sprite disponible pour cette catégorie</p>';
        return;
    }
    
    categoryData.sprites.forEach((sprite, index) => {
        // Ignorer les sprites sans URL valide
        if (!sprite.sprite_url || sprite.sprite_url === 'undefined' || sprite.sprite_url === '') {
            return;
        }
        
        const spriteElement = document.createElement('div');
        spriteElement.className = 'sprite-item fade-in';
        spriteElement.style.animationDelay = `${index * 0.05}s`;
        spriteElement.style.cursor = 'pointer';
        spriteElement.innerHTML = `
            <div class="sprite-image">
                <img src="/assets/${sprite.sprite_url}" alt="${sprite.name}" onerror="this.parentElement.innerHTML='<i class=\\"fas fa-image\\" style=\\"color: var(--text-muted);\\"></i>'">
            </div>
            <div class="sprite-name">${sprite.name}</div>
            <div class="sprite-actions">
                <button onclick="event.stopPropagation(); window.open('/poke/${encodeURIComponent(sprite.name)}', '_blank')" class="sprite-btn-detail" title="Voir les détails">
                    <i class="fas fa-eye"></i>
                </button>
                <button onclick="event.stopPropagation(); showPokemonDetails('${sprite.name}', ${sprite.generation || 1})" class="sprite-btn-modal" title="Détails rapides">
                    <i class="fas fa-info-circle"></i>
                </button>
            </div>
        `;
        
        // MODIFICATION : Rediriger vers la page de détail au clic principal
        spriteElement.onclick = () => {
            // Rediriger vers la page de détail du Pokémon
            window.location.href = `/poke/${encodeURIComponent(sprite.name)}`;
        };
        
        container.appendChild(spriteElement);
    });
}

// Affichage du modal de détails complets
async function showPokemonDetails(pokemonName, generation) {
    const modal = document.getElementById('pokemon-details-modal');
    const loadingMessage = document.createElement('div');
    
    // Afficher un message de chargement
    modal.style.display = 'block';
    loadingMessage.style.cssText = `
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: var(--text-primary);
        font-family: 'Orbitron', monospace;
        z-index: 1001;
    `;
    loadingMessage.innerHTML = 'Chargement des détails...';
    modal.appendChild(loadingMessage);
    
    try {
        // Récupérer les détails depuis l'API
        const response = await fetch(`/api/pokemon/details/${encodeURIComponent(pokemonName)}/${generation}`);
        
        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: Pokemon non trouvé`);
        }
        
        const data = await response.json();
        
        // Supprimer le message de chargement
        loadingMessage.remove();
        
        // Remplir le modal avec les données
        populatePokemonDetailsModal(data);
        
    } catch (error) {
        console.error('Erreur lors du chargement des détails:', error);
        loadingMessage.innerHTML = `Erreur: ${error.message}`;
        
        setTimeout(() => {
            modal.style.display = 'none';
            loadingMessage.remove();
        }, 3000);
    }
}

// Affichage du modal des Pokemon manquants
async function showMissingPokemon(generation) {
    const modal = document.getElementById('missing-pokemon-modal');
    const loadingMessage = document.createElement('div');
    
    // Afficher un message de chargement
    modal.style.display = 'block';
    loadingMessage.style.cssText = `
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: var(--text-primary);
        font-family: 'Orbitron', monospace;
        z-index: 1001;
    `;
    loadingMessage.innerHTML = 'Chargement des Pokemon manquants...';
    modal.appendChild(loadingMessage);
    
    try {
        currentMissingGeneration = generation;
        
        // Récupérer les Pokemon manquants depuis l'API
        const response = await fetch(`/api/missing/${generation}`);
        
        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: Impossible de récupérer les données`);
        }
        
        const data = await response.json();
        allMissingPokemon = data;
        
        // Supprimer le message de chargement
        loadingMessage.remove();
        
        // Remplir le modal avec les données
        populateMissingPokemonModal(generation, data);
        
    } catch (error) {
        console.error('Erreur lors du chargement des Pokemon manquants:', error);
        loadingMessage.innerHTML = `Erreur: ${error.message}`;
        
        setTimeout(() => {
            modal.style.display = 'none';
            loadingMessage.remove();
        }, 3000);
    }
}

// Remplir le modal de détails avec les données
function populatePokemonDetailsModal(data) {
    const pokemon = data.pokemon;
    
    // Informations de base
    document.getElementById('details-pokemon-name').textContent = pokemon.name;
    document.getElementById('details-pokemon-number').textContent = pokemon.number || 'N/A';
    document.getElementById('details-pokemon-generation').textContent = pokemon.generation;
    
    // Images
    const sprite = document.getElementById('details-sprite');
    const hqImage = document.getElementById('details-hq-image');
    
    if (pokemon.sprite_path) {
        sprite.src = `/assets/${pokemon.sprite_path}`;
        sprite.style.display = 'block';
    } else {
        sprite.style.display = 'none';
    }
    
    if (pokemon.high_quality_image) {
        hqImage.src = `/assets/${pokemon.high_quality_image}`;
        hqImage.style.display = 'block';
    } else {
        hqImage.style.display = 'none';
    }
    
    // Formes
    const formsContainer = document.getElementById('details-pokemon-forms');
    if (pokemon.forms && pokemon.forms.length > 0 && pokemon.forms[0]) {
        formsContainer.innerHTML = pokemon.forms.map(form => 
            `<span class="form-tag">${form}</span>`
        ).join('');
    } else {
        formsContainer.innerHTML = '';
    }
    
    // Shiny lock
    const shinyLockIndicator = document.getElementById('details-shiny-lock');
    if (pokemon.is_shiny_lock) {
        shinyLockIndicator.className = 'shiny-lock-indicator locked';
        shinyLockIndicator.innerHTML = '<i class="fas fa-lock"></i> Shiny Lock Actif';
    } else {
        shinyLockIndicator.className = 'shiny-lock-indicator unlocked';
        shinyLockIndicator.innerHTML = '<i class="fas fa-unlock"></i> Shiny disponible';
    }
    
    // Description
    const descriptionEl = document.getElementById('details-pokemon-description');
    if (pokemon.description) {
        descriptionEl.textContent = pokemon.description;
        descriptionEl.parentElement.style.display = 'block';
    } else {
        descriptionEl.parentElement.style.display = 'none';
    }
    
    // Jeux
    const gamesContainer = document.getElementById('details-games');
    if (data.games && data.games.length > 0) {
        gamesContainer.innerHTML = data.games.map(game => `
            <div class="detail-item">
                <div class="detail-item-name">${game.name}</div>
                <div class="detail-item-info">Génération ${game.generation}</div>
            </div>
        `).join('');
    } else {
        gamesContainer.innerHTML = '<div class="empty-state">Aucun jeu disponible</div>';
    }
    
    // Méthodes de chasse
    const methodsContainer = document.getElementById('details-hunt-methods');
    if (data.hunt_methods && data.hunt_methods.length > 0) {
        methodsContainer.innerHTML = data.hunt_methods.map(method => `
            <div class="detail-item">
                <div class="detail-item-name">${method.name}</div>
                <div class="detail-item-info">
                    ${method.game_name ? `Jeu: ${method.game_name}` : ''}
                    ${method.location_name ? `<span class="detail-badge">${method.location_name}</span>` : ''}
                    ${method.probability ? `<br>Probabilité: ${method.probability}` : ''}
                    ${method.conditions ? `<br>Conditions: ${method.conditions}` : ''}
                </div>
            </div>
        `).join('');
    } else {
        methodsContainer.innerHTML = '<div class="empty-state">Aucune méthode de chasse disponible</div>';
    }
    
    // Localisations
    const locationsContainer = document.getElementById('details-locations');
    if (data.locations && data.locations.length > 0) {
        locationsContainer.innerHTML = data.locations.map(location => `
            <div class="detail-item">
                <div class="detail-item-name">${location.name}</div>
                <div class="detail-item-info">
                    ${location.region ? `Région: ${location.region}` : ''}
                    ${location.game_name ? `<span class="detail-badge">${location.game_name}</span>` : ''}
                    ${location.method ? `<br>Méthode: ${location.method}` : ''}
                    ${location.rarity ? `<br>Rareté: ${location.rarity}` : ''}
                </div>
            </div>
        `).join('');
    } else {
        locationsContainer.innerHTML = '<div class="empty-state">Aucune localisation disponible</div>';
    }
}

// Remplir le modal des Pokemon manquants
function populateMissingPokemonModal(generation, missingPokemon) {
    // Titre
    document.getElementById('missing-generation').textContent = `${generation}`;
    
    // Afficher la grille
    displayMissingPokemon(missingPokemon);
}

// Afficher la grille des Pokemon manquants
function displayMissingPokemon(pokemonList) {
    const container = document.getElementById('missing-pokemon-list');
    container.innerHTML = '';
    
    if (pokemonList.length === 0) {
        container.innerHTML = `
            <div class="empty-missing">
                <i class="fas fa-check-circle"></i>
                <h3>Aucun Pokemon manquant !</h3>
                <p>Tous les Pokemon de cette génération sont complets.</p>
            </div>
        `;
        return;
    }
    
    pokemonList.forEach((pokemon, index) => {
        const pokemonElement = document.createElement('div');
        let cssClass = 'missing-pokemon-item';
        
        if (!pokemon.has_sprite && !pokemon.has_details) {
            cssClass += ' missing-both';
        } else if (!pokemon.has_sprite) {
            cssClass += ' missing-sprite';
        } else if (!pokemon.has_details) {
            cssClass += ' missing-details';
        }
        
        pokemonElement.className = cssClass + ' fade-in';
        pokemonElement.style.animationDelay = `${index * 0.05}s`;
        
        // Badges de statut
        let badges = [];
        if (!pokemon.has_sprite) {
            badges.push('<span class="missing-badge sprite">Sprite manquant</span>');
        }
        if (!pokemon.has_details) {
            badges.push('<span class="missing-badge details">Détails manquants</span>');
        }
        if (pokemon.has_sprite && pokemon.has_details) {
            badges.push('<span class="missing-badge complete">Complet</span>');
        }
        
        pokemonElement.innerHTML = `
            <div class="missing-pokemon-info">
                <div class="missing-pokemon-name">${pokemon.name}</div>
                <div class="missing-pokemon-number">#${pokemon.number || 'N/A'}</div>
                <div class="missing-status">
                    ${badges.join('')}
                </div>
            </div>
            <div class="missing-pokemon-actions">
                ${!pokemon.has_sprite ? '<button class="missing-action-btn primary" onclick="scrapePokemonSprite(\'' + pokemon.name + '\', ' + currentMissingGeneration + ')">Récupérer sprite</button>' : ''}
                ${!pokemon.has_details ? '<button class="missing-action-btn secondary" onclick="scrapePokemonDetails(\'' + pokemon.name + '\', ' + currentMissingGeneration + ')">Récupérer détails</button>' : ''}
                ${(pokemon.has_sprite && pokemon.has_details) ? '<button class="missing-action-btn primary" onclick="showPokemonDetails(\'' + pokemon.name + '\', ' + currentMissingGeneration + ')">Voir détails</button>' : ''}
            </div>
        `;
        
        container.appendChild(pokemonElement);
    });
}

// Fonctions pour scraper un Pokemon spécifique (à implémenter côté serveur)
async function scrapePokemonSprite(pokemonName, generation) {
    console.log(`Scraping sprite pour ${pokemonName} gen ${generation}`);
    // TODO: Implémenter l'appel API pour scraper un Pokemon spécifique
    alert(`Fonctionnalité à venir: Scraping du sprite de ${pokemonName}`);
}

async function scrapePokemonDetails(pokemonName, generation) {
    console.log(`Scraping détails pour ${pokemonName} gen ${generation}`);
    // TODO: Implémenter l'appel API pour scraper les détails d'un Pokemon spécifique
    alert(`Fonctionnalité à venir: Scraping des détails de ${pokemonName}`);
}

// Chargement des données depuis l'API
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        statsData = data;
        updateStats(data);
        
        // Mettre à jour l'heure de dernière mise à jour
        const now = new Date();
        const timeString = now.toLocaleTimeString('fr-FR', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
        document.getElementById('last-update').textContent = `Dernière mise à jour: ${timeString}`;
        
    } catch (error) {
        console.error('Erreur lors du chargement des statistiques:', error);
        document.getElementById('last-update').textContent = 'Erreur de chargement';
    }
}

// Chargement des sprites depuis l'API
async function loadSprites() {
    try {
        console.log('Chargement des sprites...');
        const response = await fetch('/api/sprites');
        const data = await response.json();
        
        console.log('Données reçues:', data);
        
        spriteData = data;
        
        if (data && (data.generations || data.regional_forms || data.other_forms)) {
            updateGenerationTabs(data);
            
            // Sélectionner automatiquement le premier onglet s'il n'y en a pas déjà un de sélectionné
            if (!currentCategory && data.generations && Object.keys(data.generations).length > 0) {
                const firstGenKey = Object.keys(data.generations).sort((a, b) => parseInt(a) - parseInt(b))[0];
                const firstGen = data.generations[firstGenKey];
                if (firstGen && firstGen.sprites && firstGen.sprites.length > 0) {
                    selectCategory(firstGen);
                    console.log('Premier onglet sélectionné:', firstGen.name);
                }
            }
        } else {
            console.warn('Aucune donnée de sprites trouvée');
        }
        
    } catch (error) {
        console.error('Erreur lors du chargement des sprites:', error);
    }
}

// Actualisation des données
function refreshData() {
    const refreshIcon = document.getElementById('refresh-icon');
    refreshIcon.style.transform = 'rotate(360deg)';
    
    Promise.all([loadStats(), loadSprites()]).then(() => {
        setTimeout(() => {
            refreshIcon.style.transform = 'rotate(0deg)';
        }, 500);
    });
}

// Démarrage automatique des mises à jour
function startAutoRefresh() {
    // Mise à jour toutes les 30 secondes
    // updateInterval = setInterval(refreshData, 30000);
    console.log('Auto-refresh désactivé pour éviter le stress');
}

// Arrêt des mises à jour automatiques
function stopAutoRefresh() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
}

// Gestion de la visibilité de la page
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        // startAutoRefresh();
        // refreshData(); // Mise à jour immédiate au retour
        console.log('Auto-refresh désactivé');
    }
});

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    // Chargement initial des données
    refreshData();
    
    // Démarrage des mises à jour automatiques
    // startAutoRefresh();
    console.log('Auto-refresh désactivé au démarrage');
    
    // Gestion du bouton de rafraîchissement
    document.getElementById('refresh-icon').onclick = refreshData;
    
    // Gestion du modal
    document.getElementById('modal-close').onclick = () => {
        document.getElementById('sprite-modal').style.display = 'none';
    };
    
    // Gestion du modal de détails
    document.getElementById('details-modal-close').onclick = () => {
        document.getElementById('pokemon-details-modal').style.display = 'none';
    };
    
    // Gestion du modal des Pokemon manquants
    document.getElementById('missing-modal-close').onclick = () => {
        document.getElementById('missing-pokemon-modal').style.display = 'none';
    };
    
    // Fermer les modals avec Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.getElementById('sprite-modal').style.display = 'none';
            document.getElementById('pokemon-details-modal').style.display = 'none';
            document.getElementById('missing-pokemon-modal').style.display = 'none';
        }
    });
    
    // Fermer les modals en cliquant à l'extérieur
    document.getElementById('pokemon-details-modal').onclick = (e) => {
        if (e.target === document.getElementById('pokemon-details-modal')) {
            document.getElementById('pokemon-details-modal').style.display = 'none';
        }
    };
    
    document.getElementById('missing-pokemon-modal').onclick = (e) => {
        if (e.target === document.getElementById('missing-pokemon-modal')) {
            document.getElementById('missing-pokemon-modal').style.display = 'none';
        }
    };
    
    // Ajouter une animation de chargement
    const loadingMessage = document.createElement('div');
    loadingMessage.id = 'loading-message';
    loadingMessage.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: var(--dark-card);
        border: 1px solid var(--dark-border);
        border-radius: 12px;
        padding: 2rem;
        color: var(--text-primary);
        font-family: 'Orbitron', monospace;
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 1rem;
    `;
    loadingMessage.innerHTML = `
        <div style="width: 20px; height: 20px; border: 2px solid var(--primary-color); border-top: 2px solid transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        <span>Chargement des données Pokemon...</span>
    `;
    
    // Ajouter l'animation CSS pour le spinner
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(loadingMessage);
    
    // Retirer le message de chargement après 3 secondes
    setTimeout(() => {
        if (loadingMessage.parentNode) {
            loadingMessage.remove();
        }
    }, 3000);
});

// Gestion des erreurs globales
window.addEventListener('error', (e) => {
    console.error('Erreur JavaScript:', e.error);
});

// Gestion des erreurs de fetch
window.addEventListener('unhandledrejection', (e) => {
    console.error('Erreur de promesse non gérée:', e.reason);
});

// Fonctions utilitaires
function formatNumber(num) {
    return num.toLocaleString('fr-FR');
}

function formatPercentage(num) {
    return num.toFixed(1) + '%';
}

// Export des fonctions pour utilisation externe
window.PokemonDashboard = {
    refreshData,
    selectCategory,
    startAutoRefresh,
    stopAutoRefresh,
    showMissingPokemon,
    showMissingTab
}; 