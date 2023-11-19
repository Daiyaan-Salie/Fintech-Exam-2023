from algosdk.v2client import algod
from algosdk import account, mnemonic, transaction
from math import log10

def accountGen():
    '''Account creation function that will generate a new account key pair with mnemonic'''
    privateKey, publicAdress = account.generate_account() # Generate account key pair
    mnemon=mnemonic.from_private_key(privateKey)  # Obtain mnemonic to use the same account later  
    return {"privateKey": privateKey,"publicAdress": publicAdress,"mnemon": mnemon }

def loadAccount(mnemon):
    '''Load the accounts for recovery purposes and loading accounts with a positive balance via dispensory'''
    try:
        privateKey = mnemonic.to_private_key(mnemon)
        publicAdress = account.address_from_private_key(privateKey)  
        return {"privateKey": privateKey, "publicAdress": publicAdress, "mnemon": mnemon}
    except Exception as e:
        print(f"error loading account: {e}")
        return None

def accountBalance(accountName, algodClient): 
    '''Obtain account balance'''
    try:
        accountInfo = algodClient.account_info(accountName["publicAdress"])
        accountBalance = accountInfo["amount"]
        return accountBalance
    except Exception as e:
        print(f"Error fetching account balance: {e}")
        return None
    
def assetBalanceCheck(algodClient, accountName, assetId) :
    '''Check asset balance for accounts'''
    try : 
        accountInfo  = algodClient.account_info(accountName["publicAdress"])
        assetHoldings = accountInfo.get("assets", [])
        for asset in assetHoldings:
            if asset["asset-id"] == assetId:
                assetBalance = asset["amount"]
                break 
        return assetBalance
    
    except Exception as e:
        
        print(f"Error checking asset balance: {e}")
        return None

def optIn(algodClient, accountName, assetId):
    try:
        param = algodClient.suggested_params()
        param.fee = 1000
        param.flatFee = True

        optinTxn = transaction.AssetOptInTxn(sender=accountName["publicAdress"], sp=param, index=assetId)
        signedOptinTxn = optinTxn.sign(accountName["privateKey"])
        txId = algodClient.send_transaction(signedOptinTxn)
        print(f"Sent opt in transaction with txid: {txId}")

        results = transaction.wait_for_confirmation(algodClient, txId, 4)
        print(f"Result confirmed in round: {results['confirmed-round']}")
        
    except Exception as e:
        print(f"Error issuing ASA: {e}")
    
def FracNft(algodClient, accountName, name, totalUnitAmount):
    '''Issue Fractional NFT'''

    """To create a fractional NFT, the total units must be a power of base 10, 
       that is greater than 1, and the number of decimals must be equal to 
       the logarithm of base 10 of the total number of units. The fractional NFT standard 
       is defined as part of ARC-0003. From(https://developer.algorand.org/docs/get-started/tokenization/nft/)
       
       
       The FracNft function is designed to issue a fractional NFT (Non-Fungible Token) on the Algorand blockchain, 
       adhering to the standards outlined in ARC-0003.This function takes as input the instance of the Algorand client (algod_client), 
       the account details for the sender, in this case, account B (accountName), a name for the NFT (name), and the total number of units for the NFT (totalUnitAmount).
       The function begins by checking if the account has sufficient funds to cover the transaction fee. If not, it prints an error message and exits. The function then 
       calculates the number of decimals required for the fractional NFT based on the logarithm in base 10 of the total number of units following the standards for the NFT.
       Using the Algorand Python SDK,  the function creates an asset configuration transaction (txn) with specified parameters such as the total units, unit name, asset name,
       manager, reserve, freeze, clawback addresses, and decimals. The transaction is signed with the account's private key and sent to the Algorand network. 
       The function waits for confirmation and prints the transaction details, including the resulting fractional NFT's asset ID.If any exception occurs during the process,
       an error message is printed, and the function returns None. Overall, the function streamlines the issuance of fractional NFTs on the Algorand blockchain.
    
       """
    try:
        param = algodClient.suggested_params()
        param.fee = 1000
        param.flat_fee = True

        accountInfo  = algodClient.account_info(accountName["publicAdress"])
        balance = accountInfo["amount"]
    
        if balance < param.fee:
            print("Insufficient funds in the account.")
            return

        total_units = totalUnitAmount
        decimals = int(log10(total_units))

        txn = transaction.AssetConfigTxn(
            sender=accountName["publicAdress"],
            sp=param,
            total=total_units,
            default_frozen=False,
            unit_name=name.upper(),
            asset_name=name.lower(),
            manager=accountName["publicAdress"],
            reserve=accountName["publicAdress"],
            freeze=accountName["publicAdress"],
            clawback=accountName["publicAdress"],
            decimals=decimals)

        stxn = txn.sign(accountName["privateKey"])
        txid = algodClient.send_transaction(stxn)
        print(f"Sent fractional NFT created transaction with txid: {txid}")

        results = transaction.wait_for_confirmation(algodClient, txid, 4)  # 4 rounds for verification
        print(f"Result confirmed in round: {results['confirmed-round']}")
        
        assetId = results["asset-index"]
        print(f"Fractional NFT Asset ID for {name.upper()}: {assetId}")
        
        return assetId

    except Exception as e:
        print(f"Error issuing fractional NFT: {e}")
        return None

def distributeNft(algodClient, accountName, assetId, recipients, fractions, totalUnits):
    '''Distribute Fractional NFT to Recipients'''

    '''The function begins by obtaining suggested transaction parameters (param) and setting the transaction fee.
    The function enters a loop to distribute fractional NFTs to each recipient(the list set in the main function). 
    The loop iterates over the recipients and fractions lists simultaneously using zip. For each recipient, 
    it calculates the amount of the fractional NFT to send based on the specified fraction and the total number of units. It creates an 
    asset transfer transaction (txn) for each distribution, specifying the sender, receiver, amount to send, asset ID, and transaction parameters.
    The transaction is signed with the private key of the sender's account (accountName["privateKey"]) and sent to the Algorand network.
    The function waits for confirmation of each transaction and prints the transaction details, including the transaction ID (txid) and the 
    round in which the transaction was confirmed. If any exception occurs during the process, an error message is printed.'''

    try:
        param = algodClient.suggested_params()
        param.fee = 1000
        param.flat_fee = True

        """ Distribute Fractional NFT to recipients"""
        for recipient, fraction in zip(recipients, fractions):
            amountSend = int(fraction * totalUnits)  # Determines how many of the FractionalNFT to send
            txn = transaction.AssetTransferTxn(
                sender=accountName["publicAdress"],
                sp=param,
                receiver=recipient['publicAdress'],
                amt=amountSend,
                index=assetId)

            stxn = txn.sign(accountName["privateKey"])
            txid = algodClient.send_transaction(stxn)
            print(f"Sent {fraction} fractional NFTs to {recipient} with txid: {txid}")

            results = transaction.wait_for_confirmation(algodClient, txid, 4)  # 4 rounds for verification
            print(f"Result confirmed in round: {results['confirmed-round']}")

    except Exception as e:
        print(f"Error distributing fractional NFT: {e}")

def checkNftOwn(algodClient, assetId, recipients):
        '''Check asset balance for accounts'''
        print("\n")
        try : 
            for recipient in recipients:
            
                balAsset = assetBalanceCheck(algodClient,recipient,assetId)
    
                if balAsset > 0 :
                    print(f"Adress: {recipient['publicAdress']} has {balAsset} units of asset ID {assetId}")
                else:
                    print(f"Adress: {recipient['publicAdress']} does not hold any units of the fractional NFT.")
        
        except Exception as e:
            
            print(f"Error checking asset balance: {e}")

def main():
    #######################################################################################################
    '''Create a new client, configured to connect to a public node''' 
    
    algod_adress= "http://testnet-api.algonode.cloud"
    algod_token = ""
    algod_client = algod.AlgodClient(algod_token, algod_adress) # instance of client
    
    #######################################################################################################
    ''' Generate accounts A & B & C & D'''
    
    accountA = accountGen()
    accountB = accountGen()
    accountC = accountGen()
    accountD = accountGen()

    # #######################################################################################################
    # ''' Load Account A & B & C & D for dispensory purpose''' Manually insert mnemonic of the new accounts created during every session - for testing purposes
    
    # AccountMnemonA= 'weird school mixed borrow option rural muscle blade close update tape despair vintage parrot fashion dilemma breeze someone exile step length shuffle actress absent ensure'
    # AccountMnemonB= 'cotton snack fold tortoise resist forward recall visual large uphold kiwi south sketch soul vapor vehicle reopen truth crisp empty wire ticket chimney absent social'
    # AccountMnemonC= 'talent alien boat action prison bus rescue way young major critic leader always census bid loan govern awake rich judge first flight surface ability library'
    # AccountMnemonD= 'mass pave fantasy upper visit mail arrange water female method tourist badge input valid large legal stuff crop ship tongue between broken layer abstract canal'
    
    # accountA = loadAccount(AccountMnemonA)
    # accountB = loadAccount(AccountMnemonB)
    # accountC = loadAccount(AccountMnemonC)
    # accountD = loadAccount(AccountMnemonD)
    
    ######################################################################################################
    '''Print account information for confirmation of creation/loading'''
    
    if accountA:
        print("AccountA Address:", accountA["publicAdress"])
        print("AccountA Private Key:", accountA["privateKey"])
        print("AccountA mnemonic:", accountA["mnemon"])
    else:
        print("Failed to load AccountA.")

    if accountB:
        print("AccountB Address:", accountB["publicAdress"])
        print("AccountB Private Key:", accountB["privateKey"])
        print("AccountB mnemonic:", accountB["mnemon"])
    else:
        print("Failed to load AccountB.")
        
    if accountC:
        print("AccountC Address:", accountC["publicAdress"])
        print("AccountC Private Key:", accountC["privateKey"])
        print("AccountC mnemonic:", accountC["mnemon"])
    else:
        print("Failed to load AccountC.")
    
    if accountD:
        print("AccountD Address:", accountD["publicAdress"])
        print("AccountD Private Key:", accountD["privateKey"])
        print("AccountD mnemonic:", accountD["mnemon"])
    else:
        print("Failed to load AccountD.")
    
#     ########################################################################################################
    ''' Load Account A & B & C & D with Algos from the dispensary in https://dispenser.testnet.aws.algodev.network/
        Check Account B balance before issueing Fractional NFT'''   
    
    print("\n")
    print(f"Account A Balance : {accountBalance(accountA, algod_client)} microAlgos")
    print(f"Account B Balance : {accountBalance(accountB, algod_client)} microAlgos")
    print(f"Account C Balance : {accountBalance(accountC, algod_client)} microAlgos")
    print(f"Account D Balance : {accountBalance(accountD, algod_client)} microAlgos")
    
   ########################################################################################################
    '''Issue ASA "NFTFRAC'''
    
    nameASA =  "NFTFRAC"
    totalUnitAmount = 100
    assetId = FracNft(algod_client, accountB, nameASA,totalUnitAmount)
    
#     ########################################################################################################
    ''' Assert hard codiing for the purpose of testing instead of generating a new ASA evrytime '''
    
    # assetId = 480615282 - for testing and is updated with new assett ID everytime a new ASA is issued i.e. every new session.
    
    """ check asset balance"""
    balAsset = assetBalanceCheck(algod_client,accountB,assetId)
    print("\n")
    if balAsset is not None:
        print(f"{accountB['publicAdress']} has {balAsset} units of asset ID {assetId}")
    else:
        print(f"Unable to retrieve asset balance for {accountB['publicAdress']} and asset ID {assetId}.")
    
    # #########################################################################################################
    # '''Account A & C & D needs to opt in for the NFT before transaction'''
    
    optIn(algod_client, accountA, assetId)
    optIn(algod_client, accountC, assetId)
    optIn(algod_client, accountD, assetId)
    
    print("\n")
    """ check asset balance"""
    balAssetA = assetBalanceCheck(algod_client,accountA,assetId)
    balAssetC = assetBalanceCheck(algod_client,accountC,assetId)
    balAssetD = assetBalanceCheck(algod_client,accountD,assetId)
    
    if balAssetA is not None:
        print(f"{accountA['publicAdress']} has {balAssetA} units of asset ID {assetId}")
    else:
        print(f"Unable to retrieve asset balance for {accountA['publicAdress']} and asset ID {assetId}.")
        
    if balAssetC is not None:
        print(f"{accountC['publicAdress']} has {balAssetC} units of asset ID {assetId}")
    else:
        print(f"Unable to retrieve asset balance for {accountC['publicAdress']} and asset ID {assetId}.")
    
    if balAssetD is not None:
        print(f"{accountD['publicAdress']} has {balAssetD} units of asset ID {assetId}")
    else:
        print(f"Unable to retrieve asset balance for {accountD['publicAdress']} and asset ID {assetId}.")

    ########################################################################################################
    recipients = [accountA, accountC, accountD]
    fractions = [0.40, 0.30, 0.20]  #fractions that each account must get plus the remaining fraction from the sender
    distributeNft(algod_client,accountB,assetId,recipients,fractions,totalUnitAmount)

    
    # #######################################################################################################  
    recipients = [accountA, accountB, accountC, accountD]
    checkNftOwn(algod_client, assetId, recipients)  
    
if __name__ == "__main__":
    main()
