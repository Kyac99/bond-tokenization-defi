// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./BondToken.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title SecondaryMarket
 * @dev Marché secondaire pour l'échange d'obligations tokenisées
 * Permet aux investisseurs d'acheter/vendre des obligations sur un marché ouvert
 */
contract SecondaryMarket is Ownable, ReentrancyGuard {
    // Structure pour un ordre
    struct Order {
        address trader;          // Adresse du trader
        address bondAddress;     // Adresse du contrat d'obligation
        uint256 amount;          // Quantité de tokens d'obligation
        uint256 price;           // Prix par token (en wei)
        uint256 timestamp;       // Timestamp de création de l'ordre
        bool isBuyOrder;         // true si ordre d'achat, false si ordre de vente
        bool fulfilled;          // true si l'ordre a été exécuté
        bool cancelled;          // true si l'ordre a été annulé
    }
    
    // ID de l'ordre suivant
    uint256 private nextOrderId = 1;
    
    // Mapping des ordres par ID
    mapping(uint256 => Order) public orders;
    
    // Mapping des obligations enregistrées
    mapping(address => bool) public registeredBonds;
    
    // Frais de marché en pourcentage (multiplié par 100, ex: 25 = 0.25%)
    uint256 public marketFeePercentage;
    
    // Adresse pour collecter les frais
    address public feeCollector;
    
    // Événements
    event BondRegistered(address indexed bondAddress);
    event BondUnregistered(address indexed bondAddress);
    event OrderCreated(uint256 indexed orderId, address indexed trader, address indexed bondAddress, uint256 amount, uint256 price, bool isBuyOrder);
    event OrderFulfilled(uint256 indexed orderId, address indexed buyer, address indexed seller, uint256 amount, uint256 price);
    event OrderCancelled(uint256 indexed orderId, address indexed trader);
    event MarketFeeUpdated(uint256 newFeePercentage);
    event FeeCollectorUpdated(address indexed newFeeCollector);

    /**
     * @dev Constructeur du marché secondaire
     * @param _feePercentage Pourcentage des frais de marché (multiplié par 100)
     * @param _feeCollector Adresse pour collecter les frais
     */
    constructor(uint256 _feePercentage, address _feeCollector) Ownable(msg.sender) {
        require(_feePercentage <= 1000, "Fee percentage too high"); // Max 10%
        require(_feeCollector != address(0), "Invalid fee collector address");
        
        marketFeePercentage = _feePercentage;
        feeCollector = _feeCollector;
    }
    
    /**
     * @dev Modifie le pourcentage des frais de marché
     * @param _feePercentage Nouveau pourcentage des frais (multiplié par 100)
     */
    function setMarketFeePercentage(uint256 _feePercentage) external onlyOwner {
        require(_feePercentage <= 1000, "Fee percentage too high"); // Max 10%
        
        marketFeePercentage = _feePercentage;
        emit MarketFeeUpdated(_feePercentage);
    }
    
    /**
     * @dev Modifie l'adresse du collecteur de frais
     * @param _feeCollector Nouvelle adresse pour collecter les frais
     */
    function setFeeCollector(address _feeCollector) external onlyOwner {
        require(_feeCollector != address(0), "Invalid fee collector address");
        
        feeCollector = _feeCollector;
        emit FeeCollectorUpdated(_feeCollector);
    }
    
    /**
     * @dev Enregistre une obligation sur le marché
     * @param bondAddress Adresse du contrat d'obligation
     */
    function registerBond(address bondAddress) external onlyOwner {
        require(bondAddress != address(0), "Invalid bond address");
        require(!registeredBonds[bondAddress], "Bond already registered");
        
        registeredBonds[bondAddress] = true;
        emit BondRegistered(bondAddress);
    }
    
    /**
     * @dev Désenregistre une obligation du marché
     * @param bondAddress Adresse du contrat d'obligation
     */
    function unregisterBond(address bondAddress) external onlyOwner {
        require(registeredBonds[bondAddress], "Bond not registered");
        
        registeredBonds[bondAddress] = false;
        emit BondUnregistered(bondAddress);
    }
    
    /**
     * @dev Crée un ordre d'achat
     * @param bondAddress Adresse du contrat d'obligation
     * @param amount Quantité de tokens d'obligation à acheter
     * @param price Prix par token (en wei)
     * @return orderId ID de l'ordre créé
     */
    function createBuyOrder(address bondAddress, uint256 amount, uint256 price) external payable nonReentrant returns (uint256) {
        require(registeredBonds[bondAddress], "Bond not registered");
        require(amount > 0, "Amount must be greater than 0");
        require(price > 0, "Price must be greater than 0");
        require(msg.value >= amount * price, "Insufficient funds sent");
        
        // Crée un nouvel ordre d'achat
        uint256 orderId = nextOrderId++;
        orders[orderId] = Order({
            trader: msg.sender,
            bondAddress: bondAddress,
            amount: amount,
            price: price,
            timestamp: block.timestamp,
            isBuyOrder: true,
            fulfilled: false,
            cancelled: false
        });
        
        emit OrderCreated(orderId, msg.sender, bondAddress, amount, price, true);
        
        // Retourne l'excédent de fonds
        uint256 requiredFunds = amount * price;
        if (msg.value > requiredFunds) {
            payable(msg.sender).transfer(msg.value - requiredFunds);
        }
        
        return orderId;
    }
    
    /**
     * @dev Crée un ordre de vente
     * @param bondAddress Adresse du contrat d'obligation
     * @param amount Quantité de tokens d'obligation à vendre
     * @param price Prix par token (en wei)
     * @return orderId ID de l'ordre créé
     */
    function createSellOrder(address bondAddress, uint256 amount, uint256 price) external nonReentrant returns (uint256) {
        require(registeredBonds[bondAddress], "Bond not registered");
        require(amount > 0, "Amount must be greater than 0");
        require(price > 0, "Price must be greater than 0");
        
        IERC20 bondToken = IERC20(bondAddress);
        require(bondToken.balanceOf(msg.sender) >= amount, "Insufficient token balance");
        require(bondToken.allowance(msg.sender, address(this)) >= amount, "Insufficient token allowance");
        
        // Crée un nouvel ordre de vente
        uint256 orderId = nextOrderId++;
        orders[orderId] = Order({
            trader: msg.sender,
            bondAddress: bondAddress,
            amount: amount,
            price: price,
            timestamp: block.timestamp,
            isBuyOrder: false,
            fulfilled: false,
            cancelled: false
        });
        
        emit OrderCreated(orderId, msg.sender, bondAddress, amount, price, false);
        
        return orderId;
    }
    
    /**
     * @dev Annule un ordre existant
     * @param orderId ID de l'ordre à annuler
     */
    function cancelOrder(uint256 orderId) external nonReentrant {
        Order storage order = orders[orderId];
        require(order.trader == msg.sender, "Not the order owner");
        require(!order.fulfilled, "Order already fulfilled");
        require(!order.cancelled, "Order already cancelled");
        
        order.cancelled = true;
        
        // Rembourse les fonds si c'est un ordre d'achat
        if (order.isBuyOrder) {
            uint256 refundAmount = order.amount * order.price;
            payable(msg.sender).transfer(refundAmount);
        }
        
        emit OrderCancelled(orderId, msg.sender);
    }
    
    /**
     * @dev Exécute un ordre d'achat existant en vendant des obligations
     * @param buyOrderId ID de l'ordre d'achat à exécuter
     * @param amount Quantité de tokens d'obligation à vendre (doit être <= à la quantité de l'ordre)
     */
    function fulfillBuyOrder(uint256 buyOrderId, uint256 amount) external nonReentrant {
        Order storage buyOrder = orders[buyOrderId];
        require(!buyOrder.fulfilled, "Order already fulfilled");
        require(!buyOrder.cancelled, "Order cancelled");
        require(buyOrder.isBuyOrder, "Not a buy order");
        require(amount > 0 && amount <= buyOrder.amount, "Invalid amount");
        
        IERC20 bondToken = IERC20(buyOrder.bondAddress);
        require(bondToken.balanceOf(msg.sender) >= amount, "Insufficient token balance");
        require(bondToken.allowance(msg.sender, address(this)) >= amount, "Insufficient token allowance");
        
        // Calcule le montant total et les frais
        uint256 totalAmount = amount * buyOrder.price;
        uint256 fee = (totalAmount * marketFeePercentage) / 10000;
        uint256 sellerAmount = totalAmount - fee;
        
        // Met à jour l'ordre
        buyOrder.amount -= amount;
        if (buyOrder.amount == 0) {
            buyOrder.fulfilled = true;
        }
        
        // Transfère les tokens du vendeur à l'acheteur
        require(bondToken.transferFrom(msg.sender, buyOrder.trader, amount), "Token transfer failed");
        
        // Paie le vendeur
        payable(msg.sender).transfer(sellerAmount);
        
        // Paie les frais
        if (fee > 0) {
            payable(feeCollector).transfer(fee);
        }
        
        emit OrderFulfilled(buyOrderId, buyOrder.trader, msg.sender, amount, buyOrder.price);
    }
    
    /**
     * @dev Exécute un ordre de vente existant en achetant des obligations
     * @param sellOrderId ID de l'ordre de vente à exécuter
     * @param amount Quantité de tokens d'obligation à acheter (doit être <= à la quantité de l'ordre)
     */
    function fulfillSellOrder(uint256 sellOrderId, uint256 amount) external payable nonReentrant {
        Order storage sellOrder = orders[sellOrderId];
        require(!sellOrder.fulfilled, "Order already fulfilled");
        require(!sellOrder.cancelled, "Order cancelled");
        require(!sellOrder.isBuyOrder, "Not a sell order");
        require(amount > 0 && amount <= sellOrder.amount, "Invalid amount");
        
        // Calcule le montant total et les frais
        uint256 totalAmount = amount * sellOrder.price;
        uint256 fee = (totalAmount * marketFeePercentage) / 10000;
        uint256 totalRequired = totalAmount + fee;
        require(msg.value >= totalRequired, "Insufficient funds sent");
        
        IERC20 bondToken = IERC20(sellOrder.bondAddress);
        
        // Met à jour l'ordre
        sellOrder.amount -= amount;
        if (sellOrder.amount == 0) {
            sellOrder.fulfilled = true;
        }
        
        // Transfère les tokens du vendeur à l'acheteur
        require(bondToken.transferFrom(sellOrder.trader, msg.sender, amount), "Token transfer failed");
        
        // Paie le vendeur
        payable(sellOrder.trader).transfer(totalAmount);
        
        // Paie les frais
        if (fee > 0) {
            payable(feeCollector).transfer(fee);
        }
        
        // Retourne l'excédent de fonds
        if (msg.value > totalRequired) {
            payable(msg.sender).transfer(msg.value - totalRequired);
        }
        
        emit OrderFulfilled(sellOrderId, msg.sender, sellOrder.trader, amount, sellOrder.price);
    }
    
    /**
     * @dev Récupère tous les ordres actifs pour une obligation spécifique
     * @param bondAddress Adresse du contrat d'obligation
     * @param isBuyOrder true pour les ordres d'achat, false pour les ordres de vente
     * @return activeOrderIds Liste des IDs d'ordres actifs
     */
    function getActiveOrders(address bondAddress, bool isBuyOrder) external view returns (uint256[] memory) {
        uint256 count = 0;
        
        // Compte d'abord le nombre d'ordres actifs
        for (uint256 i = 1; i < nextOrderId; i++) {
            Order storage order = orders[i];
            if (order.bondAddress == bondAddress && 
                order.isBuyOrder == isBuyOrder && 
                !order.fulfilled && 
                !order.cancelled) {
                count++;
            }
        }
        
        // Crée et remplit le tableau des IDs d'ordres
        uint256[] memory activeOrderIds = new uint256[](count);
        uint256 index = 0;
        
        for (uint256 i = 1; i < nextOrderId; i++) {
            Order storage order = orders[i];
            if (order.bondAddress == bondAddress && 
                order.isBuyOrder == isBuyOrder && 
                !order.fulfilled && 
                !order.cancelled) {
                activeOrderIds[index++] = i;
            }
        }
        
        return activeOrderIds;
    }
    
    /**
     * @dev Récupère le meilleur prix d'achat pour une obligation spécifique
     * @param bondAddress Adresse du contrat d'obligation
     * @return bestPrice Meilleur prix d'achat (le plus élevé), 0 si aucun ordre
     */
    function getBestBuyPrice(address bondAddress) external view returns (uint256) {
        uint256 bestPrice = 0;
        
        for (uint256 i = 1; i < nextOrderId; i++) {
            Order storage order = orders[i];
            if (order.bondAddress == bondAddress && 
                order.isBuyOrder && 
                !order.fulfilled && 
                !order.cancelled && 
                order.price > bestPrice) {
                bestPrice = order.price;
            }
        }
        
        return bestPrice;
    }
    
    /**
     * @dev Récupère le meilleur prix de vente pour une obligation spécifique
     * @param bondAddress Adresse du contrat d'obligation
     * @return bestPrice Meilleur prix de vente (le plus bas), 0 si aucun ordre
     */
    function getBestSellPrice(address bondAddress) external view returns (uint256) {
        uint256 bestPrice = type(uint256).max;
        bool foundOrder = false;
        
        for (uint256 i = 1; i < nextOrderId; i++) {
            Order storage order = orders[i];
            if (order.bondAddress == bondAddress && 
                !order.isBuyOrder && 
                !order.fulfilled && 
                !order.cancelled && 
                order.price < bestPrice) {
                bestPrice = order.price;
                foundOrder = true;
            }
        }
        
        return foundOrder ? bestPrice : 0;
    }
    
    /**
     * @dev Permet au contrat de recevoir des ETH
     */
    receive() external payable {}
}