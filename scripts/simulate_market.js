// Script pour simuler les interactions sur le marché secondaire
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
  
  console.log("Simulation du marché secondaire avec les comptes :");
  console.log("- Owner:", owner.address);
  console.log("- Trader1:", trader1.address);
  console.log("- Trader2:", trader2.address);
  console.log("- Trader3:", trader3.address);

  // Chargement des contrats
  const BondToken = await hre.ethers.getContractFactory("BondToken");
  const bondToken = BondToken.attach(deploymentInfo.bondToken);
  
  const SecondaryMarket = await hre.ethers.getContractFactory("SecondaryMarket");
  const secondaryMarket = SecondaryMarket.attach(deploymentInfo.secondaryMarket);

  console.log("Contrats chargés :");
  console.log("- BondToken:", await bondToken.getAddress());
  console.log("- SecondaryMarket:", await secondaryMarket.getAddress());

  // Distribution initiale des tokens
  const initialDistribution = async () => {
    console.log("\n--- Distribution initiale des tokens ---");
    
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
    
    // Vérification des soldes
    const ownerBalance = await bondToken.balanceOf(owner.address);
    const trader1Balance = await bondToken.balanceOf(trader1.address);
    const trader2Balance = await bondToken.balanceOf(trader2.address);
    const trader3Balance = await bondToken.balanceOf(trader3.address);
    
    console.log("\nSoldes après distribution :");
    console.log(`- Owner: ${hre.ethers.formatUnits(ownerBalance, 18)} tokens`);
    console.log(`- Trader1: ${hre.ethers.formatUnits(trader1Balance, 18)} tokens`);
    console.log(`- Trader2: ${hre.ethers.formatUnits(trader2Balance, 18)} tokens`);
    console.log(`- Trader3: ${hre.ethers.formatUnits(trader3Balance, 18)} tokens`);
  };

  // Création d'ordres sur le marché secondaire
  const createOrders = async () => {
    console.log("\n--- Création d'ordres sur le marché secondaire ---");
    
    // Approbation des dépenses de tokens pour le marché secondaire
    const approvAmount = hre.ethers.parseUnits("1000", 18);
    await bondToken.connect(trader1).approve(await secondaryMarket.getAddress(), approvAmount);
    await bondToken.connect(trader2).approve(await secondaryMarket.getAddress(), approvAmount);
    await bondToken.connect(trader3).approve(await secondaryMarket.getAddress(), approvAmount);
    console.log("Approbations de dépenses configurées pour tous les traders");
    
    // Trader1 crée un ordre de vente
    const sellAmount1 = hre.ethers.parseUnits("50", 18);
    const sellPrice1 = hre.ethers.parseEther("0.11"); // 0.11 ETH par token (10% de prime)
    const sellOrderId1 = await secondaryMarket.connect(trader1).createSellOrder(
      await bondToken.getAddress(),
      sellAmount1,
      sellPrice1
    );
    const sellOrderTx1 = await sellOrderId1.wait();
    console.log(`Trader1 a créé un ordre de vente pour ${hre.ethers.formatUnits(sellAmount1, 18)} tokens à ${hre.ethers.formatEther(sellPrice1)} ETH/token`);
    
    // Trader2 crée un ordre de vente
    const sellAmount2 = hre.ethers.parseUnits("30", 18);
    const sellPrice2 = hre.ethers.parseEther("0.105"); // 0.105 ETH par token (5% de prime)
    const sellOrderId2 = await secondaryMarket.connect(trader2).createSellOrder(
      await bondToken.getAddress(),
      sellAmount2,
      sellPrice2
    );
    const sellOrderTx2 = await sellOrderId2.wait();
    console.log(`Trader2 a créé un ordre de vente pour ${hre.ethers.formatUnits(sellAmount2, 18)} tokens à ${hre.ethers.formatEther(sellPrice2)} ETH/token`);
    
    // Trader3 crée un ordre d'achat
    const buyAmount = hre.ethers.parseUnits("20", 18);
    const buyPrice = hre.ethers.parseEther("0.095"); // 0.095 ETH par token (5% de réduction)
    const totalBuyValue = hre.ethers.parseEther("1.9"); // 20 * 0.095 = 1.9 ETH
    const buyOrderId = await secondaryMarket.connect(trader3).createBuyOrder(
      await bondToken.getAddress(),
      buyAmount,
      buyPrice,
      { value: totalBuyValue }
    );
    const buyOrderTx = await buyOrderId.wait();
    console.log(`Trader3 a créé un ordre d'achat pour ${hre.ethers.formatUnits(buyAmount, 18)} tokens à ${hre.ethers.formatEther(buyPrice)} ETH/token`);
    
    // Récupération des ordres actifs
    console.log("\nOrdres de vente actifs :");
    const sellOrders = await secondaryMarket.getActiveOrders(await bondToken.getAddress(), false);
    for (let i = 0; i < sellOrders.length; i++) {
      const order = await secondaryMarket.orders(sellOrders[i]);
      console.log(`- Order #${sellOrders[i]}: ${hre.ethers.formatUnits(order.amount, 18)} tokens à ${hre.ethers.formatEther(order.price)} ETH/token (${order.trader})`);
    }
    
    console.log("\nOrdres d'achat actifs :");
    const buyOrders = await secondaryMarket.getActiveOrders(await bondToken.getAddress(), true);
    for (let i = 0; i < buyOrders.length; i++) {
      const order = await secondaryMarket.orders(buyOrders[i]);
      console.log(`- Order #${buyOrders[i]}: ${hre.ethers.formatUnits(order.amount, 18)} tokens à ${hre.ethers.formatEther(order.price)} ETH/token (${order.trader})`);
    }
    
    return { sellOrders, buyOrders };
  };

  // Exécution d'ordres
  const executeOrders = async (orders) => {
    console.log("\n--- Exécution d'ordres ---");
    
    if (orders.sellOrders.length > 0 && orders.buyOrders.length > 0) {
      // Pour la simulation, nous allons exécuter partiellement un ordre de vente
      const sellOrderId = orders.sellOrders[0];
      const buyOrderId = orders.buyOrders[0];
      
      const sellOrder = await secondaryMarket.orders(sellOrderId);
      const buyOrder = await secondaryMarket.orders(buyOrderId);
      
      console.log(`Exécution partielle de l'ordre de vente #${sellOrderId}`);
      console.log(`Trader3 achète auprès de l'ordre de vente de Trader2`);
      
      // Trader3 fulfille partiellement l'ordre de vente de Trader2
      const amountToFulfill = hre.ethers.parseUnits("10", 18);
      const totalCost = amountToFulfill * sellOrder.price / hre.ethers.parseUnits("1", 18);
      const totalWithFee = totalCost * 1.0025; // Ajout de 0.25% de frais
      
      await secondaryMarket.connect(trader3).fulfillSellOrder(
        sellOrderId, 
        amountToFulfill,
        { value: hre.ethers.parseEther(totalWithFee.toString()) }
      );
      
      console.log(`Trader3 a acheté ${hre.ethers.formatUnits(amountToFulfill, 18)} tokens de l'ordre de vente #${sellOrderId}`);
      
      // Vérification des soldes après transaction
      const trader2Balance = await bondToken.balanceOf(trader2.address);
      const trader3Balance = await bondToken.balanceOf(trader3.address);
      
      console.log("\nSoldes après transaction :");
      console.log(`- Trader2: ${hre.ethers.formatUnits(trader2Balance, 18)} tokens`);
      console.log(`- Trader3: ${hre.ethers.formatUnits(trader3Balance, 18)} tokens`);
      
      // Vérification de l'état de l'ordre
      const updatedOrder = await secondaryMarket.orders(sellOrderId);
      console.log(`État de l'ordre #${sellOrderId} après exécution partielle:`);
      console.log(`- Quantité restante: ${hre.ethers.formatUnits(updatedOrder.amount, 18)} tokens`);
      console.log(`- Exécuté: ${updatedOrder.fulfilled}`);
    } else {
      console.log("Pas assez d'ordres pour exécuter des transactions");
    }
  };

  // Annulation d'un ordre
  const cancelOrder = async (orders) => {
    console.log("\n--- Annulation d'ordre ---");
    
    if (orders.buyOrders.length > 0) {
      const buyOrderId = orders.buyOrders[0];
      console.log(`Trader3 annule son ordre d'achat #${buyOrderId}`);
      
      await secondaryMarket.connect(trader3).cancelOrder(buyOrderId);
      
      const updatedOrder = await secondaryMarket.orders(buyOrderId);
      console.log(`État de l'ordre #${buyOrderId} après annulation:`);
      console.log(`- Annulé: ${updatedOrder.cancelled}`);
      
      // Vérification des ordres d'achat actifs après annulation
      const activeBuyOrders = await secondaryMarket.getActiveOrders(await bondToken.getAddress(), true);
      console.log(`Ordres d'achat actifs restants: ${activeBuyOrders.length}`);
    } else {
      console.log("Pas d'ordres d'achat à annuler");
    }
  };

  // Exécution de la simulation
  try {
    await initialDistribution();
    const orders = await createOrders();
    await executeOrders(orders);
    await cancelOrder(orders);
    
    console.log("\nSimulation terminée avec succès!");
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