#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour lancer la simulation du marché obligataire tokenisé
avec des paramètres par défaut.
"""

from market_model import run_simulation
import os

def main():
    """
    Fonction principale pour exécuter la simulation avec
    des paramètres par défaut.
    """
    print("Démarrage de la simulation du marché obligataire tokenisé...")
    
    # Création du répertoire results s'il n'existe pas
    os.makedirs("results", exist_ok=True)
    
    # Exécution de la simulation avec les paramètres par défaut
    simulator = run_simulation(
        num_bonds=100,          # 100 obligations (100 traditionnelles + 100 tokenisées)
        num_investors=1000,     # 1000 investisseurs
        simulation_days=365,    # Simulation sur 1 an
        traditional_min=10000,  # Montant minimum pour les obligations traditionnelles: 10,000
        tokenized_min=100,      # Montant minimum pour les obligations tokenisées: 100
        analyze=True            # Analyser les résultats automatiquement
    )
    
    print("Simulation terminée. Les résultats sont disponibles dans le répertoire 'results'.")
    print("\nPour exécuter la simulation avec des paramètres personnalisés, utilisez:")
    print("python market_model.py --bonds 200 --investors 2000 --days 730")
    
    return simulator

if __name__ == "__main__":
    simulator = main()
