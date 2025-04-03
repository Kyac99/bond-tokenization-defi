# Modélisation d'un Marché Obligataire Tokenisé

## 📝 Description du Projet
Ce projet a pour objectif de modéliser un marché obligataire tokenisé en utilisant les technologies blockchain et finance décentralisée (DeFi). Nous étudions l'impact de la tokenisation sur la liquidité et la transparence du marché obligataire, tout en simulant un marché secondaire digitalisé pour les obligations tokenisées.

## 🎯 Objectifs
- Étudier le processus de tokenisation des obligations traditionnelles
- Évaluer l'impact sur la liquidité et la transparence du marché
- Simuler un marché secondaire digitalisé pour l'échange d'obligations tokenisées
- Analyser l'utilisation des contrats intelligents pour la gestion automatisée des flux de paiements

## 🔧 Technologies
- **Blockchain**: Ethereum
- **Smart Contracts**: Solidity
- **Framework de développement**: Hardhat/Truffle
- **Frontend**: Web3.js/Ethers.js, React
- **Base de données**: PostgreSQL/MongoDB
- **Simulation du marché**: Python/Flask

## 📂 Structure du Projet

```
bond-tokenization-defi/
│
├── contracts/              # Contrats intelligents Solidity
│   ├── BondToken.sol       # Contrat d'émission d'obligations tokenisées
│   ├── CouponPayment.sol   # Contrat pour la gestion des paiements de coupons
│   └── SecondaryMarket.sol # Contrat pour le marché secondaire des obligations
│
├── scripts/                # Scripts de déploiement et tests
│   ├── deploy.js           # Script de déploiement des contrats
│   └── simulation.js       # Scripts de simulation du marché
│
├── frontend/               # Interface utilisateur
│   ├── src/                # Code source du frontend
│   └── public/             # Ressources publiques
│
├── simulation/             # Code de simulation du marché secondaire
│   ├── market_model.py     # Modèle de marché
│   └── data_analysis.py    # Analyse des données et résultats
│
├── tests/                  # Tests des contrats et simulations
│
├── docs/                   # Documentation
│   └── architecture.md     # Architecture technique du projet
│
└── cahier_des_charges.md   # Cahier des charges détaillé
```

## 🚀 Installation et déploiement

### Prérequis
- Node.js (v16+)
- Python (v3.8+)
- npm ou yarn
- Compte et clé privée sur le réseau Ethereum (ou testnet)

### Installation
```bash
# Cloner le dépôt
git clone https://github.com/Kyac99/bond-tokenization-defi.git
cd bond-tokenization-defi

# Installer les dépendances pour les smart contracts
npm install

# Installer les dépendances pour la simulation
cd simulation
pip install -r requirements.txt
```

### Déploiement des contrats
```bash
# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos clés et configuration

# Déployer sur le réseau de test (Goerli)
npx hardhat run scripts/deploy.js --network goerli
```

## 📊 Simulation du marché
```bash
# Lancer la simulation
cd simulation
python market_model.py
```

## 📈 Résultats et analyses
Les résultats des simulations seront disponibles dans le dossier `simulation/results/`. Une interface web permettra également de visualiser les résultats.

## 📚 Documentation
- [Cahier des charges](cahier_des_charges.md)
- [Architecture technique](docs/architecture.md) (à venir)
- [Guide d'utilisation](docs/user_guide.md) (à venir)

## 👥 Contributeurs
- [Votre nom](https://github.com/Kyac99)

## 📄 Licence
Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.