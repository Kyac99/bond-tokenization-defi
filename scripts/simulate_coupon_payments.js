// Script pour simuler les paiements de coupons des obligations tokenisées
const hre = require("hardhat");
const fs = require("fs");

async function main() {
  // Récupération des informations de déploiement
  let deploymentInfo;
  try {
    deploymentInfo = JSON.parse(fs.readFileSync("deployment-info.json"));
  } catch (error) {
    console.error("Fichier deployment-info.json introuvable. Exécutez d'abord le script de déploiement.");
    process.exit(1);
  }

  const [owner, trader1, trader2, trader3] = await hre.ethers.getSigners();
  
  console.log("Simulation des paiements de coupons avec les comptes :");
  console.log("- Owner:", owner.address);
  console.log("- Trader1:", trader1.address);
  console.log("- Trader2:", trader2.address);
  console.log("- Trader3:", trader3.address);

  // Chargement des contrats
  const BondToken = await hre.ethers.getContractFactory("BondToken");
  const bondToken = BondToken.attach(deploymentInfo.bondToken);
  
  const CouponPayment = await hre.ethers.getContractFactory("CouponPayment");
  const couponPayment = CouponPayment.attach(deploymentInfo.couponPayment);

  console.log("Contrats chargés :");
  console.log("- BondToken:", await bondToken.getAddress());
  console.log("- CouponPayment:", await couponPayment.getAddress());

  // Distribution initiale des tokens (si ce n'est pas déjà fait)
  const initialDistribution = async () => {
    console.log("\n--- Vérification de la distribution des tokens ---");
    
    const trader1Balance = await bondToken.balanceOf(trader1.address);
    const trader2Balance = await bondToken.balanceOf(trader2.address);
    const trader3Balance = await bondToken.balanceOf(trader3.address);
    
    // Si les traders n'ont pas encore de tokens, effectuer une distribution
    if (trader1Balance.isZero() && trader2Balance.isZero() && trader3Balance.isZero()) {
      console.log("Distribution initiale des tokens...");
      
      // Transfert de tokens aux traders
      const tokensForTrader1 = hre.ethers.parseUnits("300", 18);
      const tokensForTrader2 = hre.ethers.parseUnits("200", 18);
      const tokensForTrader3 = hre.ethers.parseUnits("100", 18);
      
      await bondToken.transfer(trader1.address, tokensForTrader1);
      console.log(`Transféré ${hre.ethers.formatUnits(tokensForTrader1, 18)} tokens à Trader1`);
      
      await bondToken.transfer(trader2.address, tokensForTrader2);
      console.log(`Transféré ${hre.ethers.formatUnits(tokensForTrader2, 18)} tokens à Trader2`);
      
      await bondToken.transfer(trader3.address, tokensForTrader3);
      console.log(`Transféré ${hre.ethers.formatUnits(tokensForTrader3, 18)} tokens à Trader3`);
    } else {
      console.log("Les traders possèdent déjà des tokens.");
    }
    
    // Affichage des soldes actuels
    const ownerBalance = await bondToken.balanceOf(owner.address);
    const updatedTrader1Balance = await bondToken.balanceOf(trader1.address);
    const updatedTrader2Balance = await bondToken.balanceOf(trader2.address);
    const updatedTrader3Balance = await bondToken.balanceOf(trader3.address);
    
    console.log("\nSoldes de tokens :");
    console.log(`- Owner: ${hre.ethers.formatUnits(ownerBalance, 18)} tokens`);
    console.log(`- Trader1: ${hre.ethers.formatUnits(updatedTrader1Balance, 18)} tokens`);
    console.log(`- Trader2: ${hre.ethers.formatUnits(updatedTrader2Balance, 18)} tokens`);
    console.log(`- Trader3: ${hre.ethers.formatUnits(updatedTrader3Balance, 18)} tokens`);
  };

  // Planification du paiement de coupon
  const scheduleCouponPayment = async () => {
    console.log("\n--- Planification du paiement de coupon ---");
    
    // Vérification des informations de l'obligation
    const faceValue = await bondToken.faceValue();
    const couponRate = await bondToken.couponRate();
    const maturityDate = await bondToken.maturityDate();
    const couponFrequency = await bondToken.couponFrequency();
    
    console.log("Informations de l'obligation :");
    console.log(`- Valeur nominale: ${hre.ethers.formatEther(faceValue)} ETH`);
    console.log(`- Taux du coupon: ${couponRate / 100}%`);
    console.log(`- Date d'échéance: ${new Date(maturityDate * 1000).toLocaleString()}`);
    console.log(`- Fréquence des coupons: ${couponFrequency / 86400} jours`);
    
    // Calcul de la date du prochain coupon
    const currentTime = Math.floor(Date.now() / 1000);
    const nextCouponDate = currentTime + 60; // Pour la simulation, nous utilisons 60 secondes au lieu de la fréquence réelle
    
    // Ajout de fonds au contrat de paiement
    const depositAmount = hre.ethers.parseEther("0.5"); // 0.5 ETH pour les paiements
    await couponPayment.depositForCouponPayment(await bondToken.getAddress(), { value: depositAmount });
    console.log(`Déposé ${hre.ethers.formatEther(depositAmount)} ETH dans le contrat de paiement de coupon`);
    
    // Planification du paiement
    await couponPayment.scheduleCouponPayment(await bondToken.getAddress(), nextCouponDate);
    console.log(`Paiement de coupon planifié pour: ${new Date(nextCouponDate * 1000).toLocaleString()}`);
    
    return nextCouponDate;
  };

  // Simulation des paiements de coupons aux détenteurs
  const payCoupons = async (couponDate) => {
    console.log("\n--- Paiement des coupons aux détenteurs ---");
    
    // Attente jusqu'à la date du coupon
    const currentTime = Math.floor(Date.now() / 1000);
    const timeToWait = couponDate - currentTime;
    
    if (timeToWait > 0) {
      console.log(`Attente de ${timeToWait} secondes jusqu'à la date du coupon...`);
      await new Promise(resolve => setTimeout(resolve, timeToWait * 1000 + 2000)); // Ajout de 2 secondes pour être sûr
    }
    
    // Récupération des soldes ETH avant les paiements
    const trader1EthBefore = await hre.ethers.provider.getBalance(trader1.address);
    const trader2EthBefore = await hre.ethers.provider.getBalance(trader2.address);
    const trader3EthBefore = await hre.ethers.provider.getBalance(trader3.address);
    
    console.log("Soldes ETH avant paiement des coupons :");
    console.log(`- Trader1: ${hre.ethers.formatEther(trader1EthBefore)} ETH`);
    console.log(`- Trader2: ${hre.ethers.formatEther(trader2EthBefore)} ETH`);
    console.log(`- Trader3: ${hre.ethers.formatEther(trader3EthBefore)} ETH`);
    
    // Calcul des montants de coupons attendus
    const trader1TokenBalance = await bondToken.balanceOf(trader1.address);
    const trader2TokenBalance = await bondToken.balanceOf(trader2.address);
    const trader3TokenBalance = await bondToken.balanceOf(trader3.address);
    
    const trader1CouponAmount = await bondToken.calculateCouponAmount(trader1.address);
    const trader2CouponAmount = await bondToken.calculateCouponAmount(trader2.address);
    const trader3CouponAmount = await bondToken.calculateCouponAmount(trader3.address);
    
    console.log("\nMontants de coupons calculés :");
    console.log(`- Trader1: ${hre.ethers.formatEther(trader1CouponAmount)} ETH (pour ${hre.ethers.formatUnits(trader1TokenBalance, 18)} tokens)`);
    console.log(`- Trader2: ${hre.ethers.formatEther(trader2CouponAmount)} ETH (pour ${hre.ethers.formatUnits(trader2TokenBalance, 18)} tokens)`);
    console.log(`- Trader3: ${hre.ethers.formatEther(trader3CouponAmount)} ETH (pour ${hre.ethers.formatUnits(trader3TokenBalance, 18)} tokens)`);
    
    // Paiement des coupons
    console.log("\nPaiement des coupons...");
    await couponPayment.payCouponToHolder(await bondToken.getAddress(), trader1.address, couponDate);
    console.log(`Coupon payé à Trader1`);
    
    await couponPayment.payCouponToHolder(await bondToken.getAddress(), trader2.address, couponDate);
    console.log(`Coupon payé à Trader2`);
    
    await couponPayment.payCouponToHolder(await bondToken.getAddress(), trader3.address, couponDate);
    console.log(`Coupon payé à Trader3`);
    
    // Marquer le paiement comme complet
    await couponPayment.completeCouponPayment(await bondToken.getAddress(), couponDate);
    console.log("Paiement de coupon marqué comme complet");
    
    // Vérification des soldes ETH après les paiements
    const trader1EthAfter = await hre.ethers.provider.getBalance(trader1.address);
    const trader2EthAfter = await hre.ethers.provider.getBalance(trader2.address);
    const trader3EthAfter = await hre.ethers.provider.getBalance(trader3.address);
    
    console.log("\nSoldes ETH après paiement des coupons :");
    console.log(`- Trader1: ${hre.ethers.formatEther(trader1EthAfter)} ETH (différence: +${hre.ethers.formatEther(trader1EthAfter - trader1EthBefore)} ETH)`);
    console.log(`- Trader2: ${hre.ethers.formatEther(trader2EthAfter)} ETH (différence: +${hre.ethers.formatEther(trader2EthAfter - trader2EthBefore)} ETH)`);
    console.log(`- Trader3: ${hre.ethers.formatEther(trader3EthAfter)} ETH (différence: +${hre.ethers.formatEther(trader3EthAfter - trader3EthBefore)} ETH)`);
    
    // Vérification de l'état du paiement
    const paymentCompleted = await couponPayment.areCouponsPaidForDate(await bondToken.getAddress(), couponDate);
    console.log(`\nStatut du paiement pour la date ${new Date(couponDate * 1000).toLocaleString()}: ${paymentCompleted ? "Complété" : "En attente"}`);
  };

  // Simulation de la maturité de l'obligation
  const simulateMaturity = async () => {
    console.log("\n--- Simulation de la maturité de l'obligation ---");
    
    // Dans une simulation réelle, nous attendrions jusqu'à la date de maturité
    // Pour cette simulation, nous allons simplement marquer l'obligation comme arrivée à maturité
    
    console.log("Marquage de l'obligation comme arrivée à maturité...");
    
    // Vérifier si l'obligation est déjà arrivée à maturité
    const isMatured = await bondToken.isMatured();
    
    if (isMatured) {
      console.log("L'obligation est déjà arrivée à maturité.");
    } else {
      // Pour les besoins de la simulation, nous allons forcer la maturité de l'obligation
      // Note: Dans un environnement réel, la fonction matureBond() ne serait pas appelée avant la date de maturité
      try {
        await bondToken.matureBond();
        console.log("L'obligation a été marquée comme arrivée à maturité.");
      } catch (error) {
        console.error("Erreur lors de la maturité de l'obligation:", error.message);
        console.log("Note: Dans un environnement réel, la maturité ne serait possible qu'après la date d'échéance.");
      }
    }
    
    // Vérification de l'état de l'obligation
    const maturedStatus = await bondToken.isMatured();
    const closedStatus = await bondToken.isClosed();
    
    console.log(`\nStatut de l'obligation :`);
    console.log(`- Arrivée à maturité: ${maturedStatus}`);
    console.log(`- Clôturée: ${closedStatus}`);
  };

  // Exécution de la simulation
  try {
    await initialDistribution();
    const couponDate = await scheduleCouponPayment();
    await payCoupons(couponDate);
    await simulateMaturity();
    
    console.log("\nSimulation des paiements de coupons terminée avec succès!");
  } catch (error) {
    console.error("Erreur lors de la simulation:", error);
  }
}

// Exécution du script de simulation
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });