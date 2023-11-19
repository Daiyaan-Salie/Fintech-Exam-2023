from algosdk.v2client import algod
from algosdk import account, mnemonic, transaction

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

def ASAmint(algodClient, accountName, name, totalNumAsset):
    '''Issue ASA called UCTZAR'''
    try:
        param = algodClient.suggested_params()
        param.fee = 1000
        param.flat_fee = True
        
         # check Account balance is enough for the transactions when issuing ASA
        balance = accountBalance(accountName, algodClient)
    
        if balance < param.fee:
            print("Insufficient funds in the account.")
            return

        txn = transaction.AssetConfigTxn(
            sender=accountName["publicAdress"],
            sp=param,
            total=totalNumAsset,
            default_frozen=False,
            unit_name= name.upper(),
            asset_name= name.lower(),
            manager=accountName["publicAdress"],
            reserve=accountName["publicAdress"],
            freeze=accountName["publicAdress"],
            clawback=accountName["publicAdress"],
            decimals=0)


        stxn = txn.sign(accountName["privateKey"])
        txid = algodClient.send_transaction(stxn)
        print(f"Asset has been sent with txid: {txid}")

        results = transaction.wait_for_confirmation(algodClient, txid, 4) # 4 rounds for verifiation
        assetId = results["asset-index"]
        print(f"Asset ID for {name.upper()} : {assetId}")
        
        return assetId

    except Exception as e:
        print(f"Error issuing ASA: {e}")
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
         
def atomicTransfer(algodClient, account1, account2, assetId, assetAmount, microAlgosCost):
    '''Perform atomic transfer'''
    '''The atomic transfer is similar to a normal transfer function, however it creates a group transaction in which the transfer of both algos
    from account A to Account B, and the transfer of UCTZAR from account B to Account A take place together with one transactionID generated. 
        '''
    assetBalance = None
    try:
        param = algodClient.suggested_params()  # Get suggested parameters
        param.fee = 1000
        param.flatFee = True

        algosTxn = transaction.PaymentTxn(account1["publicAdress"], param, account2["publicAdress"], microAlgosCost) # Transfer of algos from accountA to accountB
        assetTxn = transaction.AssetTransferTxn( sender=account2["publicAdress"], sp=param, receiver=account1["publicAdress"], amt=assetAmount, index=assetId) #Transfer of ASA from account2 to account1

        transaction.assign_group_id([algosTxn, assetTxn]) # Assign the group ID to the transaction. This is deterministic based on the order of the transactions in the function; the group ID will change if the two transactions are swapped.

        # Sign transactions
        sTxn1 = algosTxn.sign(account1["privateKey"])
        sTxn2 = assetTxn.sign(account2["privateKey"])

        signedGroup = [sTxn1, sTxn2] # Combine the signed transactions

        txId = algodClient.send_transactions(signedGroup) #This ID id the ID for the grouped transaction i.e. atomic swaps.

        
        results = transaction.wait_for_confirmation(algodClient, txId, 4)  # 4 rounds for verification
        print("Atomic transfer successful.")

    except Exception as e:
        print(f"Error in atomic transfer: {e}")
        
def main():

    #######################################################################################################
    '''Create a new client, configured to connect to a public node''' 
    
    algod_adress= "http://testnet-api.algonode.cloud"
    algod_token = ""
    algod_client = algod.AlgodClient(algod_token, algod_adress) # instance of client
    
    #######################################################################################################
    ''' Generate accounts A & B '''

    print('Genereate two accounts A & B')
    accountA = accountGen()
    accountB = accountGen()
    
    # #######################################################################################################
    # ''' Load Account A & B for dispensory purpose for test purposes''' in real application, it is assumed that the account aready has a sufficient positive balance
    
    # AccountMnemonA= 'odor fly arch indoor shoe chunk gate ability snack diet sure memory aim lawsuit balcony clutch truck material wrap awkward lawn veteran hub absorb cabin'
    # AccountMnemonB= 'sword month enter cement slam tree mountain silk travel orphan weekend basic dry scout olympic field judge vital energy save conduct auto zebra ability what'

    # accountA = loadAccount(AccountMnemonA)
    # accountB = loadAccount(AccountMnemonB)

    # # # ######################################################################################################
     #'''Print account information for confirmation of creation/loading'''
    
    print("Print account information for confirmation of creation")
    if accountA:
        print("\nAccountA Address:", accountA["publicAdress"])
        print("AccountA Private Key:", accountA["privateKey"])
        print("AccountA mnemonic:", accountA["mnemon"])
    else:
        print("\nFailed to creation AccountA.")

    if accountB:
        print("\nAccountB Address:", accountB["publicAdress"])
        print("AccountB Private Key:", accountB["privateKey"])
        print("AccountB mnemonic:", accountB["mnemon"])
    else:
        print("\nFailed to creation AccountB.")
    
    ########################################################################################################
    ''' Load Account A & B with Algos from the dispensary in https://dispenser.testnet.aws.algodev.network/
        Check Account B balance before issueing ASA''' 
        
    """Account will need:
       Account A: 10 Algos to optin to ASA issued. Additionally the transaction payment will cost 5 algos to transfer 2 units of UCTZAR
       Account B: The amount of the fee to perform the algos for the issuing of the atomic transaction.
                  The dispensary gives an minimum of 5 algos at a time.
       """

    print("\nLoad Account A & B with Algos from the dispensary in https://dispenser.testnet.aws.algodev.network/")
    print(f"Account A Balance : {accountBalance(accountA, algod_client)} microAlgos a minimum of 10 algos must be loaded")
    print(f"Account B Balance : {accountBalance(accountB, algod_client)} microAlgos a minimum of 5 algos must be loaded")

    # ########################################################################################################
    '''Issue ASA "UCTZAR to accountB'''
    
    nameASA =  "UCTZAR"
    totalNumAsset = 10
    assetId = ASAmint(algod_client, accountB, nameASA, totalNumAsset)
    

    #######################################################################################################
    ''' Asset hard coding for the purpose of testing instead of generating a new ASA evrytime '''
    
    # assetId = 480609817 - this must be replaced with new generated asset ID if the asset is not issued in the same session.
    
    """ check asset balance"""
    balAsset = assetBalanceCheck(algod_client,accountB,assetId)
    
    if balAsset is not None:
        print(f"\n{accountB['publicAdress']} has {balAsset} units of asset ID {assetId}")
    else:
        print(f"\nUnable to retrieve asset balance for {accountB['publicAdress']} and asset ID {assetId}.")
    
    ########################################################################################################
    '''Account A needs to optin for the ASA created previously''' 
    
    optIn(algod_client, accountA, assetId)
    
    """ check asset balance"""
    balAsset = assetBalanceCheck(algod_client,accountA,assetId)
    
    if balAsset is not None:
        print(f"{accountA['publicAdress']} has {balAsset} units of asset ID {assetId}")
    else:
        print(f"Unable to retrieve asset balance for {accountA['publicAdress']} and asset ID {assetId}.")

    # #########################################################################################################
    '''perform atomic transfer'''
    
    assetAmount = 2 # 2 units of UCTZAR 
    microAlgosCost = 5*10**6 # 5 Algos 
    
    atomicTransfer(algod_client, accountA, accountB , assetId, assetAmount, microAlgosCost)
    
    # ########################################################################################################
    """ check asset (UCTASA) balance for accounts A & B after atomic transfer"""
    
    balAsset = assetBalanceCheck(algod_client,accountA,assetId)
    if balAsset is not None:
        print(f"\naccountA has {balAsset} units of UCTZAR with asset ID {assetId}")
    else:
        print(f"\nUnable to retrieve asset balance for {accountA['publicAdress']} and asset ID {assetId}.")
     
    balAsset = assetBalanceCheck(algod_client,accountB,assetId)
    if balAsset is not None:
        print(f"\naccountB has {balAsset} units of UCTZAR with asset ID {assetId}")
    else:
        print(f"\nUnable to retrieve asset balance for {accountB['publicAdress']} and asset ID {assetId}.")
        
    '''Check Algos balance for Account A & B after atomic transfer'''   
    print(f"\nAccount A Balance : {accountBalance(accountA, algod_client)} microAlgos")
    print(f"\nAccount B Balance : {accountBalance(accountB, algod_client)} microAlgos")
    
if __name__ == "__main__":
    main()