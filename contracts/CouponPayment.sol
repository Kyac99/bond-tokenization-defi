// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./BondToken.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title CouponPayment
 * @dev Contrat pour gérer automatiquement les paiements de coupons
 * sur les obligations tokenisées
 */
contract CouponPayment is Ownable {
    // Mapping des obligations enregistrées
    mapping(address => bool) public registeredBonds;
    
    // Structure pour stocker les informations sur les paiements de coupons
    struct CouponPaymentInfo {
        uint256 couponDate;
        uint256 totalAmount;
        uint256 paidAmount;
        bool completed;
    }
    
    // Mapping des paiements de coupons par obligation et date
    mapping(address => mapping(uint256 => CouponPaymentInfo)) public couponPayments;
    
    // Événements
    event BondRegistered(address indexed bondAddress);
    event BondUnregistered(address indexed bondAddress);
    event CouponPaymentScheduled(address indexed bondAddress, uint256 couponDate, uint256 totalAmount);
    event CouponPaymentCompleted(address indexed bondAddress, uint256 couponDate);
    event CouponPaidToHolder(address indexed bondAddress, address indexed holder, uint256 amount, uint256 couponDate);

    /**
     * @dev Constructeur du contrat de paiement de coupons
     */
    constructor() Ownable(msg.sender) {}
    
    /**
     * @dev Enregistre une obligation pour la gestion des paiements de coupons
     * @param bondAddress Adresse du contrat d'obligation tokenisée
     */
    function registerBond(address bondAddress) external onlyOwner {
        require(bondAddress != address(0), "Invalid bond address");
        require(!registeredBonds[bondAddress], "Bond already registered");
        
        registeredBonds[bondAddress] = true;
        emit BondRegistered(bondAddress);
    }
    
    /**
     * @dev Désenregistre une obligation
     * @param bondAddress Adresse du contrat d'obligation tokenisée
     */
    function unregisterBond(address bondAddress) external onlyOwner {
        require(registeredBonds[bondAddress], "Bond not registered");
        
        registeredBonds[bondAddress] = false;
        emit BondUnregistered(bondAddress);
    }
    
    /**
     * @dev Planifie un paiement de coupon pour une obligation spécifique
     * @param bondAddress Adresse du contrat d'obligation
     * @param couponDate Date du coupon à payer
     */
    function scheduleCouponPayment(address bondAddress, uint256 couponDate) external onlyOwner {
        require(registeredBonds[bondAddress], "Bond not registered");
        require(couponDate > 0, "Invalid coupon date");
        require(couponPayments[bondAddress][couponDate].couponDate == 0, "Coupon payment already scheduled");
        
        BondToken bond = BondToken(bondAddress);
        uint256 totalSupply = bond.totalSupply();
        uint256 faceValue = bond.faceValue();
        uint256 couponRate = bond.couponRate();
        
        // Calcul du montant total du coupon
        uint256 totalAmount = (totalSupply * faceValue * couponRate) / (100 * 10000);
        
        // Enregistrement du paiement de coupon
        couponPayments[bondAddress][couponDate] = CouponPaymentInfo({
            couponDate: couponDate,
            totalAmount: totalAmount,
            paidAmount: 0,
            completed: false
        });
        
        emit CouponPaymentScheduled(bondAddress, couponDate, totalAmount);
    }
    
    /**
     * @dev Exécute le paiement de coupon à un détenteur spécifique
     * @param bondAddress Adresse du contrat d'obligation
     * @param holder Adresse du détenteur
     * @param couponDate Date du coupon
     */
    function payCouponToHolder(address bondAddress, address holder, uint256 couponDate) external {
        require(registeredBonds[bondAddress], "Bond not registered");
        require(couponPayments[bondAddress][couponDate].couponDate > 0, "Coupon payment not scheduled");
        require(!couponPayments[bondAddress][couponDate].completed, "Coupon payment already completed");
        
        BondToken bond = BondToken(bondAddress);
        require(bond.canClaimCoupon(holder, couponDate), "Holder cannot claim this coupon");
        
        uint256 amount = bond.calculateCouponAmount(holder);
        require(amount > 0, "Coupon amount must be greater than 0");
        
        // Mise à jour des montants payés
        couponPayments[bondAddress][couponDate].paidAmount += amount;
        
        // Paiement au détenteur
        payable(holder).transfer(amount);
        
        emit CouponPaidToHolder(bondAddress, holder, amount, couponDate);
    }
    
    /**
     * @dev Marque un paiement de coupon comme complété
     * @param bondAddress Adresse du contrat d'obligation
     * @param couponDate Date du coupon
     */
    function completeCouponPayment(address bondAddress, uint256 couponDate) external onlyOwner {
        require(registeredBonds[bondAddress], "Bond not registered");
        require(couponPayments[bondAddress][couponDate].couponDate > 0, "Coupon payment not scheduled");
        require(!couponPayments[bondAddress][couponDate].completed, "Coupon payment already completed");
        
        couponPayments[bondAddress][couponDate].completed = true;
        
        emit CouponPaymentCompleted(bondAddress, couponDate);
    }
    
    /**
     * @dev Vérifie si tous les coupons ont été payés pour une obligation à une date spécifique
     * @param bondAddress Adresse du contrat d'obligation
     * @param couponDate Date du coupon
     * @return bool Indique si tous les coupons ont été payés
     */
    function areCouponsPaidForDate(address bondAddress, uint256 couponDate) public view returns (bool) {
        if (!registeredBonds[bondAddress]) {
            return false;
        }
        
        return couponPayments[bondAddress][couponDate].completed;
    }
    
    /**
     * @dev Permet au contrat de recevoir des ETH pour les paiements de coupons
     */
    receive() external payable {}
    
    /**
     * @dev Permet au propriétaire de déposer des fonds pour les paiements de coupons
     * @param bondAddress Adresse du contrat d'obligation
     */
    function depositForCouponPayment(address bondAddress) external payable onlyOwner {
        require(registeredBonds[bondAddress], "Bond not registered");
        // Fonds ajoutés au solde du contrat
    }
    
    /**
     * @dev Permet au propriétaire de retirer les fonds excédentaires
     * @param amount Montant à retirer
     */
    function withdrawExcessFunds(uint256 amount) external onlyOwner {
        require(amount <= address(this).balance, "Insufficient balance");
        payable(owner()).transfer(amount);
    }
}