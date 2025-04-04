# Simulation du Marché Obligataire Tokenisé

Ce module contient les outils de simulation et d'analyse pour modéliser les impacts de la tokenisation sur le marché obligataire.

## Objectifs de la simulation

La simulation a pour but de comparer les marchés obligataires traditionnels et tokenisés en termes de :

1. **Liquidité** : volume de transactions, profondeur de marché, fréquence des échanges
2. **Coûts de transaction** : réduction des spreads bid-ask, frais de marché
3. **Accessibilité** : seuil d'investissement minimum, diversité des investisseurs
4. **Transparence** : visibilité des prix et des transactions
5. **Volatilité** : stabilité des prix dans le temps

## Structure du code

- `market_model.py` : Classe principale de simulation et fonctions d'analyse
- `run_simulation.py` : Script simplifié pour exécuter la simulation avec des paramètres par défaut
- `requirements.txt` : Dépendances Python nécessaires

## Installation

```bash
# Installation des dépendances
pip install -r requirements.txt
```

## Utilisation

### Exécution simple

```bash
# Exécution avec les paramètres par défaut
python run_simulation.py
```

### Options avancées

```bash
# Exécution avec des paramètres personnalisés
python market_model.py --bonds 200 --investors 2000 --days 730 --trad-min 20000 --token-min 50
```

Options disponibles :
- `--bonds` : Nombre d'obligations à simuler (défaut: 100)
- `--investors` : Nombre d'investisseurs (défaut: 1000) 
- `--days` : Nombre de jours de simulation (défaut: 365)
- `--trad-min` : Montant minimum d'investissement sur le marché traditionnel (défaut: 10000)
- `--token-min` : Montant minimum d'investissement sur le marché tokenisé (défaut: 100)
- `--no-analysis` : Désactive l'analyse automatique des résultats

## Résultats

Les résultats de la simulation sont stockés dans le répertoire `results/` et comprennent :

- Graphiques comparatifs (liquidité, spreads, volumes, etc.)
- Données brutes au format CSV pour une analyse ultérieure
- Rapport de synthèse avec statistiques clés

## Méthode de simulation

La simulation utilise une méthode d'agent-based modeling (ABM) avec deux types d'agents :

1. **Obligations** : Titres traditionnels ou tokenisés avec différentes caractéristiques (maturité, coupon, notation)
2. **Investisseurs** : Agents avec différents profils (retail, institutionnel, corporate) et préférences 

La simulation s'exécute sur une base journalière en suivant ces étapes :

1. Mise à jour des conditions de marché (taux d'intérêt, sentiment, volatilité)
2. Simulation des activités de trading sur le marché traditionnel
3. Simulation parallèle sur le marché tokenisé
4. Collecte des métriques de performance pour les deux marchés
5. Analyse comparative des résultats

## Paramètres du modèle

Les paramètres clés qui différencient les deux marchés sont :

- **Montant minimum d'investissement** : Beaucoup plus faible pour le marché tokenisé (100 vs 10000)
- **Spreads bid-ask** : Plus faibles sur le marché tokenisé
- **Profondeur de marché** : Plus importante sur le marché tokenisé
- **Fréquence des transactions** : Plus élevée sur le marché tokenisé

## Exemple de résultats

Voici un exemple de résultats typiques obtenus après une simulation d'un an :

| Métrique | Marché traditionnel | Marché tokenisé | Amélioration |
|----------|---------------------|-----------------|--------------|
| Transactions totales | 25,000 | 75,000 | 3.00x |
| Volume total | 500M | 750M | 1.50x |
| Spread bid-ask moyen | 0.950% | 0.350% | -63.2% |
| Profondeur de marché | 15.2 | 65.8 | 4.33x |
| Volatilité annualisée | 12.5% | 9.8% | -21.6% |

## Limites de la simulation

- Modèle simplifié par rapport à la complexité des marchés réels
- Ne prend pas en compte tous les aspects réglementaires
- Focalisation sur les aspects de liquidité plus que sur les risques
- Hypothèse d'adoption immédiate de la technologie blockchain

## Références

- "The Economics of Tokenization" (Deloitte, 2023)
- "Blockchain in Capital Markets" (McKinsey, 2022)
- "Bond Market Liquidity in a Rising Rate Environment" (BlackRock, 2023)