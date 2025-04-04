#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simulateur de marché obligataire tokenisé

Ce script simule les impacts de la tokenisation sur la liquidité du marché obligataire
et compare les marchés obligataires traditionnels et tokenisés.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm
import random
from datetime import datetime, timedelta
import os
import argparse

# Configuration du style des graphiques
sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

class BondMarketSimulator:
    """
    Simulateur pour comparer les marchés obligataires traditionnels et tokenisés
    """
    
    def __init__(self, num_bonds=100, num_investors=1000, simulation_days=365, 
                 traditional_min_amount=10000, tokenized_min_amount=100):
        """
        Initialise le simulateur avec les paramètres du marché
        
        Args:
            num_bonds: Nombre d'obligations dans la simulation
            num_investors: Nombre d'investisseurs dans la simulation
            simulation_days: Nombre de jours à simuler
            traditional_min_amount: Montant minimum d'investissement dans les obligations traditionnelles
            tokenized_min_amount: Montant minimum d'investissement dans les obligations tokenisées
        """
        self.num_bonds = num_bonds
        self.num_investors = num_investors
        self.simulation_days = simulation_days
        self.traditional_min_amount = traditional_min_amount
        self.tokenized_min_amount = tokenized_min_amount
        
        # Initialisation des données de simulation
        self.bonds = None
        self.investors = None
        self.traditional_market = None
        self.tokenized_market = None
        self.traditional_transactions = []
        self.tokenized_transactions = []
        self.results = {}
        
        # Création du répertoire pour les résultats si nécessaire
        os.makedirs("results", exist_ok=True)
    
    def generate_bonds(self):
        """
        Génère un ensemble d'obligations avec des caractéristiques aléatoires
        """
        # Caractéristiques des obligations
        face_values = np.random.choice([1000, 5000, 10000, 50000, 100000], self.num_bonds)
        coupon_rates = np.random.uniform(0.01, 0.08, self.num_bonds)  # 1% à 8%
        maturities = np.random.choice([1, 2, 3, 5, 7, 10, 15, 20, 30], self.num_bonds)  # en années
        credit_ratings = np.random.choice(['AAA', 'AA', 'A', 'BBB', 'BB', 'B'], self.num_bonds, 
                                        p=[0.05, 0.15, 0.25, 0.30, 0.15, 0.10])
        
        # Création du DataFrame des obligations
        self.bonds = pd.DataFrame({
            'bond_id': range(1, self.num_bonds + 1),
            'face_value': face_values,
            'coupon_rate': coupon_rates,
            'maturity_years': maturities,
            'credit_rating': credit_ratings,
            'issue_date': pd.Timestamp('2024-01-01'),
            'is_tokenized': [False] * self.num_bonds
        })
        
        # Calcul des dates d'échéance
        self.bonds['maturity_date'] = self.bonds.apply(
            lambda x: x['issue_date'] + pd.DateOffset(years=x['maturity_years']), axis=1
        )
        
        # Création d'obligations tokenisées (duplicata avec statut tokenisé)
        tokenized_bonds = self.bonds.copy()
        tokenized_bonds['is_tokenized'] = True
        tokenized_bonds['bond_id'] = tokenized_bonds['bond_id'] + self.num_bonds
        
        # Combinaison des obligations traditionnelles et tokenisées
        self.bonds = pd.concat([self.bonds, tokenized_bonds], ignore_index=True)
        
        print(f"Généré {len(self.bonds)} obligations (dont {len(tokenized_bonds)} tokenisées)")
    
    def generate_investors(self):
        """
        Génère un ensemble d'investisseurs avec différents profils
        """
        # Profils des investisseurs
        investor_types = np.random.choice(['Retail', 'Institutional', 'Corporate'], self.num_investors, 
                                         p=[0.6, 0.3, 0.1])
        
        # Distribution log-normale des actifs pour simuler l'inégalité de richesse
        assets = np.random.lognormal(mean=10, sigma=2, size=self.num_investors)
        assets = assets * 10000  # Mise à l'échelle
        
        # Préférence pour les technologies blockchain (plus élevée chez les petits investisseurs)
        blockchain_preference = np.random.beta(2, 5, self.num_investors)
        
        # Aversion au risque
        risk_aversion = np.random.normal(0.5, 0.15, self.num_investors)
        risk_aversion = np.clip(risk_aversion, 0.1, 0.9)  # Limitation entre 0.1 et 0.9
        
        # Horizons d'investissement en années
        investment_horizons = np.random.choice([1, 2, 3, 5, 7, 10, 15], self.num_investors,
                                              p=[0.15, 0.20, 0.25, 0.15, 0.10, 0.10, 0.05])
        
        # Création du DataFrame des investisseurs
        self.investors = pd.DataFrame({
            'investor_id': range(1, self.num_investors + 1),
            'type': investor_types,
            'assets': assets,
            'blockchain_preference': blockchain_preference,
            'risk_aversion': risk_aversion,
            'investment_horizon': investment_horizons
        })
        
        print(f"Généré {len(self.investors)} investisseurs")
    
    def initialize_markets(self):
        """
        Initialise les marchés obligataires traditionnels et tokenisés
        """
        # Sélection des obligations traditionnelles et tokenisées
        self.traditional_market = self.bonds[self.bonds['is_tokenized'] == False].copy()
        self.tokenized_market = self.bonds[self.bonds['is_tokenized'] == True].copy()
        
        # Initialisation des prix et de la liquidité
        for market in [self.traditional_market, self.tokenized_market]:
            # Prix initial = valeur nominale ajustée selon le taux du coupon par rapport à un taux de référence
            reference_rate = 0.03  # Taux de référence de 3%
            market['price'] = market.apply(
                lambda x: x['face_value'] * (1 + (x['coupon_rate'] - reference_rate) * x['maturity_years']), 
                axis=1
            )
            
            # Volume quotidien initial (plus élevé pour les obligations tokenisées)
            base_volume = market['face_value'] * 0.01  # 1% de la valeur nominale
            if market.iloc[0]['is_tokenized']:
                market['daily_volume'] = base_volume * 5  # 5 fois plus de volume pour les tokenisées
            else:
                market['daily_volume'] = base_volume
            
            # Spread bid-ask (plus faible pour les obligations tokenisées)
            if market.iloc[0]['is_tokenized']:
                market['bid_ask_spread'] = 0.001 + 0.001 * market['maturity_years']  # 0.1% + 0.1% par année de maturité
            else:
                market['bid_ask_spread'] = 0.005 + 0.002 * market['maturity_years']  # 0.5% + 0.2% par année de maturité
            
            # Profondeur du marché (nombre d'ordres)
            if market.iloc[0]['is_tokenized']:
                market['market_depth'] = 50 + np.random.poisson(50, len(market))
            else:
                market['market_depth'] = 10 + np.random.poisson(10, len(market))
    
    def run_simulation(self):
        """
        Exécute la simulation du marché sur la période spécifiée
        """
        # Générer les obligations et les investisseurs si ce n'est pas déjà fait
        if self.bonds is None:
            self.generate_bonds()
        if self.investors is None:
            self.generate_investors()
        if self.traditional_market is None or self.tokenized_market is None:
            self.initialize_markets()
        
        # Historique des métriques de marché
        traditional_metrics = []
        tokenized_metrics = []
        
        # Simulation jour par jour
        start_date = pd.Timestamp('2024-01-01')
        
        for day in range(self.simulation_days):
            current_date = start_date + pd.DateOffset(days=day)
            
            # Mise à jour des conditions de marché (taux d'intérêt, sentiment, etc.)
            market_conditions = self._update_market_conditions(day)
            
            # Simulation du marché traditionnel
            traditional_daily_metrics, traditional_daily_trades = self._simulate_daily_trading(
                self.traditional_market, 
                current_date, 
                market_conditions, 
                is_tokenized=False
            )
            traditional_metrics.append(traditional_daily_metrics)
            self.traditional_transactions.extend(traditional_daily_trades)
            
            # Simulation du marché tokenisé
            tokenized_daily_metrics, tokenized_daily_trades = self._simulate_daily_trading(
                self.tokenized_market, 
                current_date, 
                market_conditions, 
                is_tokenized=True
            )
            tokenized_metrics.append(tokenized_daily_metrics)
            self.tokenized_transactions.extend(tokenized_daily_trades)
            
            # Affichage de la progression
            if (day + 1) % 30 == 0:
                print(f"Simulation: {day + 1}/{self.simulation_days} jours complétés")
        
        # Conversion des métriques en DataFrames
        self.traditional_metrics_df = pd.DataFrame(traditional_metrics)
        self.tokenized_metrics_df = pd.DataFrame(tokenized_metrics)
        
        # Conversion des transactions en DataFrames
        self.traditional_transactions_df = pd.DataFrame(self.traditional_transactions)
        self.tokenized_transactions_df = pd.DataFrame(self.tokenized_transactions)
        
        print("Simulation terminée")
    
    def _update_market_conditions(self, day):
        """
        Met à jour les conditions de marché pour le jour spécifié
        
        Args:
            day: Jour de la simulation
        
        Returns:
            dict: Conditions de marché pour le jour
        """
        # Taux d'intérêt de référence (légère tendance à la hausse sur l'année)
        base_rate = 0.03
        rate_trend = day / self.simulation_days * 0.01  # +1% sur l'année
        daily_noise = np.random.normal(0, 0.0005)  # Bruit quotidien
        reference_rate = base_rate + rate_trend + daily_noise
        
        # Sentiment du marché (-1 à 1)
        if day == 0:
            self.market_sentiment = 0
        else:
            # Le sentiment évolue avec une certaine autocorrélation
            sentiment_change = np.random.normal(0, 0.1)
            self.market_sentiment = 0.8 * self.market_sentiment + 0.2 * sentiment_change
            self.market_sentiment = np.clip(self.market_sentiment, -1, 1)
        
        # Volatilité du marché
        base_volatility = 0.01
        volatility = base_volatility * (1 + 0.5 * abs(self.market_sentiment))
        
        # Événements aléatoires (crises, nouvelles, etc.)
        event_probability = 0.01  # 1% de chance d'un événement significatif par jour
        event_impact = 0
        if np.random.random() < event_probability:
            event_impact = np.random.normal(0, 0.03)  # Impact de l'événement
        
        return {
            'reference_rate': reference_rate,
            'market_sentiment': self.market_sentiment,
            'volatility': volatility,
            'event_impact': event_impact
        }
    
    def _simulate_daily_trading(self, market, current_date, market_conditions, is_tokenized):
        """
        Simule les activités de trading pour un jour spécifique
        
        Args:
            market: DataFrame du marché (traditionnel ou tokenisé)
            current_date: Date actuelle de la simulation
            market_conditions: Conditions de marché du jour
            is_tokenized: Indique s'il s'agit du marché tokenisé
        
        Returns:
            tuple: (métriques quotidiennes, transactions du jour)
        """
        # Copie du marché pour la mise à jour
        updated_market = market.copy()
        
        # Ajustement des prix en fonction des conditions de marché
        price_change_factor = 1 + market_conditions['event_impact']
        price_change_factor += market_conditions['market_sentiment'] * 0.01
        
        # Ajustement des prix en fonction des taux d'intérêt
        for idx, bond in updated_market.iterrows():
            rate_sensitivity = bond['maturity_years'] * 0.05  # Sensibilité aux taux (duration simplifiée)
            price_impact = -rate_sensitivity * (market_conditions['reference_rate'] - 0.03)
            
            # Prix mis à jour
            updated_market.at[idx, 'price'] = bond['price'] * (1 + price_impact) * price_change_factor
            
            # Ajout d'un bruit spécifique à l'obligation
            specific_noise = np.random.normal(0, market_conditions['volatility'])
            updated_market.at[idx, 'price'] *= (1 + specific_noise)
        
        # Générer les transactions du jour
        daily_transactions = []
        
        # Nombre de transactions (plus élevé pour le marché tokenisé)
        base_transactions = len(updated_market) * 2
        if is_tokenized:
            num_transactions = int(base_transactions * (1.5 + market_conditions['market_sentiment']))
        else:
            num_transactions = int(base_transactions * (0.5 + 0.5 * market_conditions['market_sentiment']))
        
        # Minimum 1 transaction
        num_transactions = max(1, num_transactions)
        
        # Générer les transactions
        for _ in range(num_transactions):
            # Sélection aléatoire d'une obligation
            bond_idx = np.random.randint(0, len(updated_market))
            bond = updated_market.iloc[bond_idx]
            
            # Sélection aléatoire d'un investisseur
            investor_idx = np.random.randint(0, len(self.investors))
            investor = self.investors.iloc[investor_idx]
            
            # Montant de la transaction (dépend du type de marché)
            if is_tokenized:
                # Pour les obligations tokenisées, peut être une fraction de la valeur nominale
                min_amount = self.tokenized_min_amount
                max_amount = min(bond['face_value'], investor['assets'] * 0.1)
            else:
                # Pour les obligations traditionnelles, généralement par multiple de la valeur nominale
                min_amount = self.traditional_min_amount
                max_amount = min(bond['face_value'] * 5, investor['assets'] * 0.1)
            
            # Si l'investisseur ne peut pas se permettre le minimum, passer à un autre
            if min_amount > investor['assets'] * 0.1:
                continue
            
            transaction_amount = min_amount * (1 + np.random.exponential(2))
            transaction_amount = min(transaction_amount, max_amount)
            
            # Prix de transaction (avec spread)
            spread = bond['bid_ask_spread']
            if np.random.random() < 0.5:  # Achat
                transaction_price = bond['price'] * (1 + spread/2)
                transaction_type = 'buy'
            else:  # Vente
                transaction_price = bond['price'] * (1 - spread/2)
                transaction_type = 'sell'
            
            # Enregistrement de la transaction
            transaction = {
                'date': current_date,
                'bond_id': bond['bond_id'],
                'investor_id': investor['investor_id'],
                'price': transaction_price,
                'amount': transaction_amount,
                'type': transaction_type,
                'is_tokenized': is_tokenized
            }
            daily_transactions.append(transaction)
            
            # Mise à jour du volume quotidien
            updated_market.at[bond_idx, 'daily_volume'] += transaction_amount
        
        # Calcul des métriques quotidiennes
        daily_metrics = {
            'date': current_date,
            'avg_price': updated_market['price'].mean(),
            'total_volume': updated_market['daily_volume'].sum(),
            'avg_spread': updated_market['bid_ask_spread'].mean(),
            'num_transactions': len(daily_transactions),
            'market_depth': updated_market['market_depth'].mean()
        }
        
        # Mise à jour du marché pour le jour suivant
        self._update_market_for_next_day(market, updated_market)
        
        return daily_metrics, daily_transactions
    
    def _update_market_for_next_day(self, original_market, updated_market):
        """
        Met à jour le marché pour le jour suivant
        
        Args:
            original_market: Référence au marché original
            updated_market: Marché mis à jour
        """
        # Mise à jour des prix et des volumes
        original_market['price'] = updated_market['price']
        
        # Réinitialisation du volume quotidien (mais garde une mémoire du volume précédent)
        base_volume = original_market['face_value'] * 0.01
        if original_market.iloc[0]['is_tokenized']:
            original_market['daily_volume'] = base_volume * 5 * 0.2 + updated_market['daily_volume'] * 0.8
        else:
            original_market['daily_volume'] = base_volume * 0.2 + updated_market['daily_volume'] * 0.8
        
        # Mise à jour des spreads (ils varient légèrement avec le temps)
        spread_adjustment = np.random.normal(1, 0.05, len(original_market))
        original_market['bid_ask_spread'] = updated_market['bid_ask_spread'] * spread_adjustment
        
        # Mise à jour de la profondeur du marché
        depth_adjustment = np.random.normal(1, 0.1, len(original_market))
        original_market['market_depth'] = updated_market['market_depth'] * depth_adjustment
        original_market['market_depth'] = original_market['market_depth'].astype(int)
    
    def analyze_results(self):
        """
        Analyse les résultats de la simulation et produit des graphiques
        """
        if not hasattr(self, 'traditional_metrics_df') or not hasattr(self, 'tokenized_metrics_df'):
            print("Exécutez d'abord la simulation avec run_simulation()")
            return
        
        print("Analyse des résultats...")
        
        # Création du répertoire pour les résultats
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Analyse de la liquidité
        self._analyze_liquidity(results_dir)
        
        # Analyse des spreads bid-ask
        self._analyze_spreads(results_dir)
        
        # Analyse du volume de transactions
        self._analyze_volumes(results_dir)
        
        # Analyse de la distribution des investisseurs
        self._analyze_investor_distribution(results_dir)
        
        # Analyse de la volatilité des prix
        self._analyze_price_volatility(results_dir)
        
        # Analyse des coûts de transaction
        self._analyze_transaction_costs(results_dir)
        
        # Résumé des statistiques
        self._generate_summary_statistics(results_dir)
        
        print(f"Analyse terminée. Les résultats sont disponibles dans le répertoire '{results_dir}'")
    
    def _analyze_liquidity(self, results_dir):
        """
        Analyse la liquidité des marchés
        
        Args:
            results_dir: Répertoire pour les résultats
        """
        plt.figure(figsize=(12, 8))
        
        # Nombre de transactions quotidiennes
        plt.subplot(2, 1, 1)
        plt.plot(self.traditional_metrics_df['date'], self.traditional_metrics_df['num_transactions'], 
                label='Marché traditionnel', color='blue')
        plt.plot(self.tokenized_metrics_df['date'], self.tokenized_metrics_df['num_transactions'], 
                label='Marché tokenisé', color='green')
        plt.title('Nombre de transactions quotidiennes')
        plt.xlabel('Date')
        plt.ylabel('Nombre de transactions')
        plt.legend()
        plt.grid(True)
        
        # Profondeur du marché
        plt.subplot(2, 1, 2)
        plt.plot(self.traditional_metrics_df['date'], self.traditional_metrics_df['market_depth'], 
                label='Marché traditionnel', color='blue')
        plt.plot(self.tokenized_metrics_df['date'], self.tokenized_metrics_df['market_depth'], 
                label='Marché tokenisé', color='green')
        plt.title('Profondeur du marché (nombre moyen d\'ordres)')
        plt.xlabel('Date')
        plt.ylabel('Profondeur')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, 'liquidity_analysis.png'), dpi=300)
        plt.close()
        
        # Ratio de liquidité (nombre de transactions / valeur totale)
        traditional_liquidity = self.traditional_metrics_df['num_transactions'] / self.traditional_metrics_df['total_volume']
        tokenized_liquidity = self.tokenized_metrics_df['num_transactions'] / self.tokenized_metrics_df['total_volume']
        
        plt.figure(figsize=(10, 6))
        plt.plot(self.traditional_metrics_df['date'], traditional_liquidity, 
                label='Marché traditionnel', color='blue')
        plt.plot(self.tokenized_metrics_df['date'], tokenized_liquidity, 
                label='Marché tokenisé', color='green')
        plt.title('Ratio de liquidité (transactions / volume)')
        plt.xlabel('Date')
        plt.ylabel('Ratio de liquidité')
        plt.legend()
        plt.grid(True)
        
        plt.savefig(os.path.join(results_dir, 'liquidity_ratio.png'), dpi=300)
        plt.close()
    
    def _analyze_spreads(self, results_dir):
        """
        Analyse les spreads bid-ask
        
        Args:
            results_dir: Répertoire pour les résultats
        """
        plt.figure(figsize=(10, 6))
        
        # Évolution des spreads bid-ask moyens
        plt.plot(self.traditional_metrics_df['date'], self.traditional_metrics_df['avg_spread'] * 100, 
                label='Marché traditionnel', color='blue')
        plt.plot(self.tokenized_metrics_df['date'], self.tokenized_metrics_df['avg_spread'] * 100, 
                label='Marché tokenisé', color='green')
        plt.title('Évolution des spreads bid-ask moyens')
        plt.xlabel('Date')
        plt.ylabel('Spread bid-ask moyen (%)')
        plt.legend()
        plt.grid(True)
        
        plt.savefig(os.path.join(results_dir, 'spread_analysis.png'), dpi=300)
        plt.close()
        
        # Distribution des spreads
        plt.figure(figsize=(12, 6))
        
        plt.subplot(1, 2, 1)
        sns.histplot(self.traditional_metrics_df['avg_spread'] * 100, kde=True, color='blue')
        plt.title('Distribution des spreads - Marché traditionnel')
        plt.xlabel('Spread bid-ask (%)')
        plt.ylabel('Fréquence')
        
        plt.subplot(1, 2, 2)
        sns.histplot(self.tokenized_metrics_df['avg_spread'] * 100, kde=True, color='green')
        plt.title('Distribution des spreads - Marché tokenisé')
        plt.xlabel('Spread bid-ask (%)')
        plt.ylabel('Fréquence')
        
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, 'spread_distribution.png'), dpi=300)
        plt.close()
    
    def _analyze_volumes(self, results_dir):
        """
        Analyse les volumes de transactions
        
        Args:
            results_dir: Répertoire pour les résultats
        """
        plt.figure(figsize=(10, 6))
        
        # Évolution du volume total quotidien
        plt.plot(self.traditional_metrics_df['date'], self.traditional_metrics_df['total_volume'] / 1e6, 
                label='Marché traditionnel', color='blue')
        plt.plot(self.tokenized_metrics_df['date'], self.tokenized_metrics_df['total_volume'] / 1e6, 
                label='Marché tokenisé', color='green')
        plt.title('Évolution du volume total quotidien')
        plt.xlabel('Date')
        plt.ylabel('Volume (millions)')
        plt.legend()
        plt.grid(True)
        
        plt.savefig(os.path.join(results_dir, 'volume_analysis.png'), dpi=300)
        plt.close()
        
        # Comparer les volumes cumulés
        trad_cum_volume = self.traditional_metrics_df['total_volume'].cumsum()
        token_cum_volume = self.tokenized_metrics_df['total_volume'].cumsum()
        
        plt.figure(figsize=(10, 6))
        plt.plot(self.traditional_metrics_df['date'], trad_cum_volume / 1e6, 
                label='Marché traditionnel', color='blue')
        plt.plot(self.tokenized_metrics_df['date'], token_cum_volume / 1e6, 
                label='Marché tokenisé', color='green')
        plt.title('Volume cumulé au fil du temps')
        plt.xlabel('Date')
        plt.ylabel('Volume cumulé (millions)')
        plt.legend()
        plt.grid(True)
        
        plt.savefig(os.path.join(results_dir, 'cumulative_volume.png'), dpi=300)
        plt.close()
    
    def _analyze_investor_distribution(self, results_dir):
        """
        Analyse la distribution des investisseurs
        
        Args:
            results_dir: Répertoire pour les résultats
        """
        # Créer les DataFrames des transactions
        if not hasattr(self, 'traditional_transactions_df'):
            self.traditional_transactions_df = pd.DataFrame(self.traditional_transactions)
        if not hasattr(self, 'tokenized_transactions_df'):
            self.tokenized_transactions_df = pd.DataFrame(self.tokenized_transactions)
        
        # Fusionner avec les informations des investisseurs
        trad_investors = self.traditional_transactions_df.merge(
            self.investors, left_on='investor_id', right_on='investor_id'
        )
        token_investors = self.tokenized_transactions_df.merge(
            self.investors, left_on='investor_id', right_on='investor_id'
        )
        
        # Distribution des types d'investisseurs
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        sns.countplot(x='type', data=trad_investors, palette='Blues')
        plt.title('Types d\'investisseurs - Marché traditionnel')
        plt.xlabel('Type d\'investisseur')
        plt.ylabel('Nombre de transactions')
        
        plt.subplot(2, 2, 2)
        sns.countplot(x='type', data=token_investors, palette='Greens')
        plt.title('Types d\'investisseurs - Marché tokenisé')
        plt.xlabel('Type d\'investisseur')
        plt.ylabel('Nombre de transactions')
        
        # Distribution des actifs des investisseurs (échelle log)
        plt.subplot(2, 2, 3)
        sns.histplot(trad_investors['assets'], log_scale=True, kde=True, color='blue')
        plt.title('Distribution des actifs - Marché traditionnel')
        plt.xlabel('Actifs (échelle log)')
        plt.ylabel('Fréquence')
        
        plt.subplot(2, 2, 4)
        sns.histplot(token_investors['assets'], log_scale=True, kde=True, color='green')
        plt.title('Distribution des actifs - Marché tokenisé')
        plt.xlabel('Actifs (échelle log)')
        plt.ylabel('Fréquence')
        
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, 'investor_distribution.png'), dpi=300)
        plt.close()
        
        # Montant moyen des transactions par type d'investisseur
        plt.figure(figsize=(12, 6))
        
        plt.subplot(1, 2, 1)
        sns.barplot(x='type', y='amount', data=trad_investors, estimator=np.mean, palette='Blues')
        plt.title('Montant moyen des transactions - Marché traditionnel')
        plt.xlabel('Type d\'investisseur')
        plt.ylabel('Montant moyen')
        
        plt.subplot(1, 2, 2)
        sns.barplot(x='type', y='amount', data=token_investors, estimator=np.mean, palette='Greens')
        plt.title('Montant moyen des transactions - Marché tokenisé')
        plt.xlabel('Type d\'investisseur')
        plt.ylabel('Montant moyen')
        
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, 'transaction_amount_by_type.png'), dpi=300)
        plt.close()
    
    def _analyze_price_volatility(self, results_dir):
        """
        Analyse la volatilité des prix
        
        Args:
            results_dir: Répertoire pour les résultats
        """
        # Calcul des rendements quotidiens
        traditional_returns = self.traditional_metrics_df['avg_price'].pct_change().dropna()
        tokenized_returns = self.tokenized_metrics_df['avg_price'].pct_change().dropna()
        
        # Volatilité glissante (fenêtre de 30 jours)
        window = 30
        traditional_volatility = traditional_returns.rolling(window=window).std() * np.sqrt(window)
        tokenized_volatility = tokenized_returns.rolling(window=window).std() * np.sqrt(window)
        
        plt.figure(figsize=(10, 6))
        plt.plot(self.traditional_metrics_df['date'].iloc[window:], traditional_volatility.iloc[window-1:], 
                label='Marché traditionnel', color='blue')
        plt.plot(self.tokenized_metrics_df['date'].iloc[window:], tokenized_volatility.iloc[window-1:], 
                label='Marché tokenisé', color='green')
        plt.title(f'Volatilité glissante des prix (fenêtre de {window} jours)')
        plt.xlabel('Date')
        plt.ylabel('Volatilité')
        plt.legend()
        plt.grid(True)
        
        plt.savefig(os.path.join(results_dir, 'price_volatility.png'), dpi=300)
        plt.close()
        
        # Distribution des rendements
        plt.figure(figsize=(12, 6))
        
        plt.subplot(1, 2, 1)
        sns.histplot(traditional_returns * 100, kde=True, color='blue')
        plt.title('Distribution des rendements quotidiens - Marché traditionnel')
        plt.xlabel('Rendement quotidien (%)')
        plt.ylabel('Fréquence')
        
        plt.subplot(1, 2, 2)
        sns.histplot(tokenized_returns * 100, kde=True, color='green')
        plt.title('Distribution des rendements quotidiens - Marché tokenisé')
        plt.xlabel('Rendement quotidien (%)')
        plt.ylabel('Fréquence')
        
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, 'return_distribution.png'), dpi=300)
        plt.close()
    
    def _analyze_transaction_costs(self, results_dir):
        """
        Analyse les coûts de transaction
        
        Args:
            results_dir: Répertoire pour les résultats
        """
        # Calcul des coûts de transaction (approximation simple basée sur les spreads)
        traditional_costs = self.traditional_metrics_df['avg_spread'] * self.traditional_metrics_df['total_volume']
        tokenized_costs = self.tokenized_metrics_df['avg_spread'] * self.tokenized_metrics_df['total_volume']
        
        plt.figure(figsize=(10, 6))
        plt.plot(self.traditional_metrics_df['date'], traditional_costs / 1e3, 
                label='Marché traditionnel', color='blue')
        plt.plot(self.tokenized_metrics_df['date'], tokenized_costs / 1e3, 
                label='Marché tokenisé', color='green')
        plt.title('Coûts de transaction quotidiens')
        plt.xlabel('Date')
        plt.ylabel('Coûts de transaction (milliers)')
        plt.legend()
        plt.grid(True)
        
        plt.savefig(os.path.join(results_dir, 'transaction_costs.png'), dpi=300)
        plt.close()
        
        # Coûts cumulés
        trad_cum_costs = traditional_costs.cumsum()
        token_cum_costs = tokenized_costs.cumsum()
        
        plt.figure(figsize=(10, 6))
        plt.plot(self.traditional_metrics_df['date'], trad_cum_costs / 1e6, 
                label='Marché traditionnel', color='blue')
        plt.plot(self.tokenized_metrics_df['date'], token_cum_costs / 1e6, 
                label='Marché tokenisé', color='green')
        plt.title('Coûts de transaction cumulés')
        plt.xlabel('Date')
        plt.ylabel('Coûts cumulés (millions)')
        plt.legend()
        plt.grid(True)
        
        plt.savefig(os.path.join(results_dir, 'cumulative_costs.png'), dpi=300)
        plt.close()
    
    def _generate_summary_statistics(self, results_dir):
        """
        Génère un résumé des statistiques de la simulation
        
        Args:
            results_dir: Répertoire pour les résultats
        """
        # Calcul des statistiques
        traditional_stats = {
            'transactions_total': self.traditional_metrics_df['num_transactions'].sum(),
            'volume_total': self.traditional_metrics_df['total_volume'].sum(),
            'avg_daily_transactions': self.traditional_metrics_df['num_transactions'].mean(),
            'avg_daily_volume': self.traditional_metrics_df['total_volume'].mean(),
            'avg_spread': self.traditional_metrics_df['avg_spread'].mean() * 100,  # En pourcentage
            'avg_market_depth': self.traditional_metrics_df['market_depth'].mean(),
            'volatility': self.traditional_metrics_df['avg_price'].pct_change().std() * 100 * np.sqrt(252)  # Annualisée
        }
        
        tokenized_stats = {
            'transactions_total': self.tokenized_metrics_df['num_transactions'].sum(),
            'volume_total': self.tokenized_metrics_df['total_volume'].sum(),
            'avg_daily_transactions': self.tokenized_metrics_df['num_transactions'].mean(),
            'avg_daily_volume': self.tokenized_metrics_df['total_volume'].mean(),
            'avg_spread': self.tokenized_metrics_df['avg_spread'].mean() * 100,  # En pourcentage
            'avg_market_depth': self.tokenized_metrics_df['market_depth'].mean(),
            'volatility': self.tokenized_metrics_df['avg_price'].pct_change().std() * 100 * np.sqrt(252)  # Annualisée
        }
        
        # Calcul des ratios d'amélioration
        improvement_ratios = {
            'transactions_ratio': tokenized_stats['transactions_total'] / traditional_stats['transactions_total'],
            'volume_ratio': tokenized_stats['volume_total'] / traditional_stats['volume_total'],
            'spread_reduction': 1 - (tokenized_stats['avg_spread'] / traditional_stats['avg_spread']),
            'depth_improvement': tokenized_stats['avg_market_depth'] / traditional_stats['avg_market_depth'],
            'volatility_ratio': tokenized_stats['volatility'] / traditional_stats['volatility']
        }
        
        # Création d'un tableau récapitulatif
        stats_summary = pd.DataFrame({
            'Métrique': [
                'Nombre total de transactions',
                'Volume total',
                'Transactions quotidiennes moyennes',
                'Volume quotidien moyen',
                'Spread bid-ask moyen (%)',
                'Profondeur de marché moyenne',
                'Volatilité annualisée (%)'
            ],
            'Marché traditionnel': [
                f"{traditional_stats['transactions_total']:,.0f}",
                f"{traditional_stats['volume_total']:,.0f}",
                f"{traditional_stats['avg_daily_transactions']:,.1f}",
                f"{traditional_stats['avg_daily_volume']:,.0f}",
                f"{traditional_stats['avg_spread']:.3f}",
                f"{traditional_stats['avg_market_depth']:.1f}",
                f"{traditional_stats['volatility']:.2f}"
            ],
            'Marché tokenisé': [
                f"{tokenized_stats['transactions_total']:,.0f}",
                f"{tokenized_stats['volume_total']:,.0f}",
                f"{tokenized_stats['avg_daily_transactions']:,.1f}",
                f"{tokenized_stats['avg_daily_volume']:,.0f}",
                f"{tokenized_stats['avg_spread']:.3f}",
                f"{tokenized_stats['avg_market_depth']:.1f}",
                f"{tokenized_stats['volatility']:.2f}"
            ],
            'Amélioration': [
                f"{improvement_ratios['transactions_ratio']:.2f}x",
                f"{improvement_ratios['volume_ratio']:.2f}x",
                f"{improvement_ratios['transactions_ratio']:.2f}x",
                f"{improvement_ratios['volume_ratio']:.2f}x",
                f"{improvement_ratios['spread_reduction']:.1%} réduction",
                f"{improvement_ratios['depth_improvement']:.2f}x",
                f"{1 - improvement_ratios['volatility_ratio']:.1%} {'réduction' if improvement_ratios['volatility_ratio'] < 1 else 'augmentation'}"
            ]
        })
        
        # Enregistrement des statistiques dans un fichier texte
        stats_summary.to_csv(os.path.join(results_dir, 'summary_statistics.csv'), index=False)
        
        # Enregistrement des statistiques dans un fichier texte lisible
        with open(os.path.join(results_dir, 'summary_report.txt'), 'w') as f:
            f.write("RAPPORT DE SIMULATION DU MARCHÉ OBLIGATAIRE TOKENISÉ\n")
            f.write("===================================================\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Obligations: {self.num_bonds * 2} (dont {self.num_bonds} tokenisées)\n")
            f.write(f"Investisseurs: {self.num_investors}\n")
            f.write(f"Période de simulation: {self.simulation_days} jours\n\n")
            
            f.write("RÉSUMÉ DES RÉSULTATS\n")
            f.write("-----------------\n\n")
            f.write(stats_summary.to_string(index=False))
            f.write("\n\n")
            
            f.write("INTERPRÉTATION\n")
            f.write("-------------\n\n")
            f.write("La tokenisation des obligations a montré les impacts suivants sur le marché:\n\n")
            
            # Liquidité
            f.write("1. Liquidité:\n")
            f.write(f"   - Le nombre de transactions a augmenté de {(improvement_ratios['transactions_ratio']-1)*100:.1f}%\n")
            f.write(f"   - Le volume total a augmenté de {(improvement_ratios['volume_ratio']-1)*100:.1f}%\n")
            f.write(f"   - La profondeur du marché a augmenté de {(improvement_ratios['depth_improvement']-1)*100:.1f}%\n\n")
            
            # Coûts de transaction
            f.write("2. Coûts de transaction:\n")
            f.write(f"   - Les spreads bid-ask ont diminué de {improvement_ratios['spread_reduction']*100:.1f}%\n")
            
            # Volatilité
            f.write("3. Volatilité des prix:\n")
            if improvement_ratios['volatility_ratio'] < 1:
                f.write(f"   - La volatilité a diminué de {(1-improvement_ratios['volatility_ratio'])*100:.1f}%\n")
            else:
                f.write(f"   - La volatilité a augmenté de {(improvement_ratios['volatility_ratio']-1)*100:.1f}%\n")
            
            f.write("\nCONCLUSION\n")
            f.write("----------\n\n")
            f.write("Cette simulation démontre que la tokenisation des obligations peut significativement améliorer\n")
            f.write("la liquidité du marché obligataire, réduire les coûts de transaction et potentiellement\n")
            f.write("stabiliser les prix, rendant le marché plus efficace et accessible à un plus large éventail d'investisseurs.\n")
        
        print(f"Résumé des statistiques enregistré dans {os.path.join(results_dir, 'summary_report.txt')}")
        
        # Enregistrement des données brutes pour une analyse ultérieure
        self.traditional_metrics_df.to_csv(os.path.join(results_dir, 'traditional_market_metrics.csv'), index=False)
        self.tokenized_metrics_df.to_csv(os.path.join(results_dir, 'tokenized_market_metrics.csv'), index=False)


def run_simulation(num_bonds=100, num_investors=1000, simulation_days=365, 
                  traditional_min=10000, tokenized_min=100, analyze=True):
    """
    Exécute une simulation complète du marché obligataire tokenisé
    
    Args:
        num_bonds: Nombre d'obligations dans la simulation
        num_investors: Nombre d'investisseurs dans la simulation
        simulation_days: Nombre de jours à simuler
        traditional_min: Montant minimum d'investissement dans les obligations traditionnelles
        tokenized_min: Montant minimum d'investissement dans les obligations tokenisées
        analyze: Si True, analyse les résultats après la simulation
    """
    # Création et exécution du simulateur
    simulator = BondMarketSimulator(
        num_bonds=num_bonds,
        num_investors=num_investors,
        simulation_days=simulation_days,
        traditional_min_amount=traditional_min,
        tokenized_min_amount=tokenized_min
    )
    
    # Exécution de la simulation
    simulator.run_simulation()
    
    # Analyse des résultats
    if analyze:
        simulator.analyze_results()
    
    return simulator


if __name__ == "__main__":
    # Configuration des arguments en ligne de commande
    parser = argparse.ArgumentParser(description='Simulateur de marché obligataire tokenisé')
    parser.add_argument('--bonds', type=int, default=100, help='Nombre d\'obligations (défaut: 100)')
    parser.add_argument('--investors', type=int, default=1000, help='Nombre d\'investisseurs (défaut: 1000)')
    parser.add_argument('--days', type=int, default=365, help='Jours de simulation (défaut: 365)')
    parser.add_argument('--trad-min', type=int, default=10000, help='Montant minimum traditionnel (défaut: 10000)')
    parser.add_argument('--token-min', type=int, default=100, help='Montant minimum tokenisé (défaut: 100)')
    parser.add_argument('--no-analysis', action='store_true', help='Désactiver l\'analyse automatique')
    
    args = parser.parse_args()
    
    # Exécution de la simulation
    simulator = run_simulation(
        num_bonds=args.bonds,
        num_investors=args.investors,
        simulation_days=args.days,
        traditional_min=args.trad_min,
        tokenized_min=args.token_min,
        analyze=not args.no_analysis
    )