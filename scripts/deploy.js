// Script de déploiement des contrats intelligents
const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  
  console.log("Déploiement des contrats avec le compte:", deployer.address);
  console.log("Solde du compte:", (await deployer.getBalance()).toString());

  // Déploiement de BondToken
  const BondToken = await hre.ethers.getContractFactory("BondToken");
  const bondParams = {
    name: "Corporate Bond Token",
    symbol: "CBT",
    faceValue: hre.ethers.parseEther("0.1"), // 0.1 ETH par obligation
    couponRate: 500, // 5% (multiplié par 100)
    maturityPeriod: 31536000, // 1 an en secondes
    couponFrequency: 7776000, // 90 jours en secondes
    totalSupply: hre.ethers.parseUnits("1000", 18) // 1000 tokens
  };
  
  const bondToken = await BondToken.deploy(
    bondParams.name,
    bondParams.symbol,
    bondParams.faceValue,
    bondParams.couponRate,
    bondParams.maturityPeriod,
    bondParams.couponFrequency,
    bondParams.totalSupply
  );
  
  await bondToken.waitForDeployment();
  console.log("BondToken déployé à l'adresse:", await bondToken.getAddress());

  // Déploiement de CouponPayment
  const CouponPayment = await hre.ethers.getContractFactory("CouponPayment");
  const couponPayment = await CouponPayment.deploy();
  
  await couponPayment.waitForDeployment();
  console.log("CouponPayment déployé à l'adresse:", await couponPayment.getAddress());

  // Déploiement de SecondaryMarket
  const SecondaryMarket = await hre.ethers.getContractFactory("SecondaryMarket");
  const marketFeePercentage = 25; // 0.25% frais de marché
  const feeCollector = deployer.address; // Adresse pour collecter les frais
  
  const secondaryMarket = await SecondaryMarket.deploy(marketFeePercentage, feeCollector);
  
  await secondaryMarket.waitForDeployment();
  console.log("SecondaryMarket déployé à l'adresse:", await secondaryMarket.getAddress());

  // Configurations post-déploiement
  
  // Enregistrement du BondToken dans CouponPayment
  const bondTokenAddress = await bondToken.getAddress();
  await couponPayment.registerBond(bondTokenAddress);
  console.log("BondToken enregistré dans CouponPayment");
  
  // Enregistrement du BondToken dans SecondaryMarket
  await secondaryMarket.registerBond(bondTokenAddress);
  console.log("BondToken enregistré dans SecondaryMarket");
  
  // Transfert de fonds au contrat CouponPayment pour les paiements de coupons
  const initialFunding = hre.ethers.parseEther("1.0"); // 1 ETH pour les paiements de coupons
  await couponPayment.depositForCouponPayment(bondTokenAddress, { value: initialFunding });
  console.log("Fonds déposés dans CouponPayment:", hre.ethers.formatEther(initialFunding), "ETH");
  
  // Planification du premier paiement de coupon
  const currentTime = Math.floor(Date.now() / 1000);
  const firstCouponDate = currentTime + bondParams.couponFrequency;
  await couponPayment.scheduleCouponPayment(bondTokenAddress, firstCouponDate);
  console.log("Premier paiement de coupon planifié pour:", new Date(firstCouponDate * 1000).toLocaleString());

  console.log("Déploiement terminé avec succès!");
  
  // Sauvegarde des adresses dans un fichier pour référence
  const fs = require("fs");
  const deploymentInfo = {
    network: hre.network.name,
    bondToken: bondTokenAddress,
    couponPayment: await couponPayment.getAddress(),
    secondaryMarket: await secondaryMarket.getAddress(),
    deployer: deployer.address,
    timestamp: new Date().toISOString()
  };
  
  fs.writeFileSync(
    "deployment-info.json",
    JSON.stringify(deploymentInfo, null, 2)
  );
  console.log("Informations de déploiement sauvegardées dans deployment-info.json");
}

// Exécution du script de déploiement
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });