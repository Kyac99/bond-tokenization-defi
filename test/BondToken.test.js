const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("BondToken", function () {
  let BondToken;
  let bondToken;
  let owner;
  let addr1;
  let addr2;
  let addrs;

  const bondParams = {
    name: "Test Bond Token",
    symbol: "TBT",
    faceValue: ethers.parseEther("0.1"), // 0.1 ETH par obligation
    couponRate: 500, // 5% (multiplié par 100)
    maturityPeriod: 31536000, // 1 an en secondes
    couponFrequency: 7776000, // 90 jours en secondes
    totalSupply: ethers.parseUnits("1000", 18) // 1000 tokens
  };

  beforeEach(async function () {
    // Récupération des signataires
    [owner, addr1, addr2, ...addrs] = await ethers.getSigners();

    // Déploiement du contrat BondToken
    BondToken = await ethers.getContractFactory("BondToken");
    bondToken = await BondToken.deploy(
      bondParams.name,
      bondParams.symbol,
      bondParams.faceValue,
      bondParams.couponRate,
      bondParams.maturityPeriod,
      bondParams.couponFrequency,
      bondParams.totalSupply
    );

    // Financement du contrat pour les paiements de coupons
    await owner.sendTransaction({
      to: await bondToken.getAddress(),
      value: ethers.parseEther("1.0") // 1 ETH
    });
  });

  describe("Déploiement", function () {
    it("Doit initialiser correctement les paramètres de l'obligation", async function () {
      expect(await bondToken.name()).to.equal(bondParams.name);
      expect(await bondToken.symbol()).to.equal(bondParams.symbol);
      expect(await bondToken.faceValue()).to.equal(bondParams.faceValue);
      expect(await bondToken.couponRate()).to.equal(bondParams.couponRate);
      expect(await bondToken.couponFrequency()).to.equal(bondParams.couponFrequency);
      expect(await bondToken.totalSupply()).to.equal(bondParams.totalSupply);
      expect(await bondToken.isMatured()).to.equal(false);
      expect(await bondToken.isClosed()).to.equal(false);
    });

    it("Doit attribuer la totalité des tokens au déployeur", async function () {
      const ownerBalance = await bondToken.balanceOf(owner.address);
      expect(await bondToken.totalSupply()).to.equal(ownerBalance);
    });
  });

  describe("Transactions", function () {
    it("Doit permettre le transfert de tokens entre comptes", async function () {
      // Transfert de 50 tokens de owner à addr1
      const transferAmount = ethers.parseUnits("50", 18);
      await bondToken.transfer(addr1.address, transferAmount);
      
      const addr1Balance = await bondToken.balanceOf(addr1.address);
      expect(addr1Balance).to.equal(transferAmount);

      // Transfert de 20 tokens de addr1 à addr2
      const secondTransferAmount = ethers.parseUnits("20", 18);
      await bondToken.connect(addr1).transfer(addr2.address, secondTransferAmount);
      
      const addr2Balance = await bondToken.balanceOf(addr2.address);
      expect(addr2Balance).to.equal(secondTransferAmount);
    });

    it("Doit échouer si l'expéditeur n'a pas assez de tokens", async function () {
      const initialOwnerBalance = await bondToken.balanceOf(owner.address);
      
      // Essayer de transférer plus de tokens que le owner n'en possède
      await expect(
        bondToken.connect(addr1).transfer(owner.address, 1)
      ).to.be.reverted;

      // Le solde du owner ne doit pas être modifié
      expect(await bondToken.balanceOf(owner.address)).to.equal(initialOwnerBalance);
    });
  });

  describe("Paiements de coupons", function () {
    it("Doit calculer correctement le montant du coupon", async function () {
      // Transfert de tokens à addr1
      const transferAmount = ethers.parseUnits("100", 18);
      await bondToken.transfer(addr1.address, transferAmount);
      
      // Calcul du montant du coupon pour addr1
      const couponAmount = await bondToken.calculateCouponAmount(addr1.address);
      
      // Calcul attendu: 100 tokens * 0.1 ETH * 5% = 0.5 ETH
      const expectedCouponAmount = (transferAmount * bondParams.faceValue * bondParams.couponRate) / (100n * 10000n);
      expect(couponAmount).to.equal(expectedCouponAmount);
    });

    it("Doit permettre la réclamation d'un coupon", async function () {
      // Transfert de tokens à addr1
      const transferAmount = ethers.parseUnits("100", 18);
      await bondToken.transfer(addr1.address, transferAmount);
      
      // Avancer dans le temps pour simuler la date du coupon
      const currentBlock = await ethers.provider.getBlock("latest");
      const couponDate = currentBlock.timestamp;
      
      // Vérifier si le coupon peut être réclamé
      const canClaim = await bondToken.canClaimCoupon(addr1.address, couponDate);
      expect(canClaim).to.equal(true);
      
      // Récupérer le solde ETH avant la réclamation
      const balanceBefore = await ethers.provider.getBalance(addr1.address);
      
      // Réclamer le coupon
      await bondToken.connect(addr1).claimCoupon(couponDate);
      
      // Vérifier que le coupon ne peut pas être réclamé deux fois
      await expect(
        bondToken.connect(addr1).claimCoupon(couponDate)
      ).to.be.revertedWith("Cannot claim this coupon");
      
      // Vérifier que le solde ETH a augmenté
      const balanceAfter = await ethers.provider.getBalance(addr1.address);
      expect(balanceAfter).to.be.greaterThan(balanceBefore);
    });
  });

  describe("Maturité et clôture", function () {
    it("Doit permettre la maturité de l'obligation", async function () {
      // Avance rapide jusqu'à après la date de maturité
      await ethers.provider.send("evm_increaseTime", [bondParams.maturityPeriod + 1]);
      await ethers.provider.send("evm_mine");
      
      // Marquer l'obligation comme arrivée à maturité
      await bondToken.matureBond();
      
      expect(await bondToken.isMatured()).to.equal(true);
      expect(await bondToken.isClosed()).to.equal(false);
    });

    it("Doit permettre la clôture de l'obligation après maturité", async function () {
      // Avance rapide jusqu'à après la date de maturité
      await ethers.provider.send("evm_increaseTime", [bondParams.maturityPeriod + 1]);
      await ethers.provider.send("evm_mine");
      
      // Marquer l'obligation comme arrivée à maturité puis la clôturer
      await bondToken.matureBond();
      await bondToken.closeBond();
      
      expect(await bondToken.isMatured()).to.equal(true);
      expect(await bondToken.isClosed()).to.equal(true);
    });

    it("Ne doit pas permettre la clôture avant la maturité", async function () {
      await expect(bondToken.closeBond()).to.be.revertedWith("Bond must be matured before closing");
    });

    it("Doit permettre au propriétaire de retirer les fonds excédentaires après clôture", async function () {
      // Avance rapide jusqu'à après la date de maturité
      await ethers.provider.send("evm_increaseTime", [bondParams.maturityPeriod + 1]);
      await ethers.provider.send("evm_mine");
      
      // Marquer l'obligation comme arrivée à maturité puis la clôturer
      await bondToken.matureBond();
      await bondToken.closeBond();
      
      // Récupérer le solde ETH du propriétaire avant le retrait
      const balanceBefore = await ethers.provider.getBalance(owner.address);
      
      // Retirer les fonds excédentaires
      await bondToken.withdrawExcessFunds();
      
      // Vérifier que le solde ETH du propriétaire a augmenté
      const balanceAfter = await ethers.provider.getBalance(owner.address);
      expect(balanceAfter).to.be.greaterThan(balanceBefore);
    });
  });
});