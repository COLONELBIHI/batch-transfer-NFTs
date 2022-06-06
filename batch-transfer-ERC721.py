import os
import json
import time
from datetime import datetime
from web3 import Web3
#from web3.middleware import geth_poa_middleware
from web3 import exceptions
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

eth_price = float(os.environ['ETH_PRICE'])
max_cost = float(os.environ['MAX_COST_PER_TRANSACTION_IN_DOLLARS'])
chainID = int(os.environ['CHAIN_ID'])
node_provider = os.environ['NODE_PROVIDER']
contract_address = Web3.toChecksumAddress(os.environ['CONTRACT_ADDRESS'])
vault = Web3.toChecksumAddress(os.environ['VAULT_ADDRESS'])
middleman = Account.from_key(os.environ['MIDDLEMAN_PRIVATE_KEY'])

contract_abi = json.loads(open("./abi/abi.json", "r").read())

############################################
# WEB3


def connect():
    global web3
    global contract

    web3 = Web3(Web3.HTTPProvider(node_provider))
    if web3.isConnected():
        print('Connected to Web3 !')
        gas_prices = get_gas_price(gwei=True)
        print(
            f"Gas fees : base ={gas_prices['base']} , priorityFee = {gas_prices['priority']} ; maxFee = {gas_prices['max']} ")
        print("\n --------> STARTING \n")
    else:
        print('---> ERROR while connecting !! Make sure the node provider is accessible.')
        exit()

    contract = web3.eth.contract(
        address=contract_address, abi=contract_abi)


def get_gas_price(gwei=False):
    ''' GasPrice Strategy :
        you can define your own gas strategy strategy in here.
        Simple generally used strategy is as follows :
            priorityFee = int(web3.eth.max_priority_fee * 1.5)
            maxGasFee = int(gas_price * 2 + priorityFee)

    '''
    gas_price = web3.eth.gas_price + Web3.toWei(0.5, 'gwei')
    priorityFee = min(Web3.toWei(2, 'gwei'), int(
        web3.eth.max_priority_fee * 1.2))
    maxGasFee = int(gas_price * 1.4 + priorityFee)
    if gwei:
        return {"base": Web3.fromWei(gas_price, 'gwei'), "max": Web3.fromWei(maxGasFee, 'gwei'), "priority": Web3.fromWei(priorityFee, 'gwei')}
    else:
        return {"base": gas_price, "max": maxGasFee, "priority": priorityFee}

# WEB3                            ###    END
############################################

############################################
# TRANSFER FUNCTION


def send_nft(goal, _from, _to, _id, _name):
    if goal != "execute" and goal != "estimate":
        print("Wrong Goal !! ")
        return False

    tx = {
        'from': middleman.address,
        'chainId': chainID,
    }
    try:
        ''' replace transferFrom() with safeTransferFrom() if you're sending to a smart contract !! '''
        gas_estimate = contract.functions.transferFrom(
            _from, _to, _id).estimateGas(tx)
    except ValueError as ex:
        print(
            f"xx-----Transfer Error for token {_id} : Gas estimation failed: Make sure the vault address is the owner of the token, and the middleman wallet has approavl to transfer it.")
        result = {"time": datetime.now().strftime("d:%d %H:%M:%S"), "name": _name, "address": {_to}, "tokenId": {
            _id}, "success": False, 'gasused': None, 'transfered': None, 'type': "transfer", "error": "Gas estimation failed: Make sure the vault address is the owner of the token, and the middleman wallet has approavl to transfer it."}
        with open("./logs/failed.txt", "a") as file:
            file.write(str(result) + "\n")
        return False
    if goal == "estimate":
        return gas_estimate
    elif goal == "execute":
        nonce = web3.eth.getTransactionCount(middleman.address)
        gas_prices = get_gas_price()
        tx = {
            'from': middleman.address,
            'nonce': nonce,
            'gas': gas_estimate,
            'maxFeePerGas': gas_prices['max'],
            'maxPriorityFeePerGas': gas_prices['priority'],
            'chainId': chainID,
        }
        ''' replace transferFrom() with safeTransferFrom() if you're sending to a smart contract !! '''
        transaction = contract.functions.transferFrom(
            _from, _to, _id).buildTransaction(tx)
        signed_tx = middleman.sign_transaction(transaction)

        cost = float(Web3.fromWei(gas_prices['max'] *
                                  gas_estimate, "ether")) * eth_price
        while cost > max_cost:
            print(f"..high gas ({cost:.2f}$)")
            time.sleep(15)
            gas_prices = get_gas_price()
            cost = float(Web3.fromWei(
                gas_prices['max']*gas_estimate, "ether")) * eth_price

        '''
         Use the following if you'd like to confirm each transaction after seeing the estimated gas fees. 
         Be aware that gas prices might increase if you take too long to confirm :
        '''
        # inp = input(
        #     f"Please confirm transaction : Sending token n° {_id} to {_name}. Max gas estimation: {cost:.2f} $ ")
        # if inp != 'ok' and inp != 'OK':
        #     exit()

        try:
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            result = {"time": datetime.now().strftime("d:%d %H:%M:%S"), "name": _name, "address": {_to}, "tokenId": {
                _id}, "success": True, 'hash': tx_hash, 'gasPrice': gas_prices['max'], 'gasused': receipt.gasUsed, 'maxCost': f'{cost:.2f} $', 'transfered': 1, 'type': "transfer", "error": None}
            with open("./logs/successful.txt", "a") as file:
                file.write(str(result) + "\n")
            return result
        except exceptions.ContractLogicError:
            result = {"time": datetime.now().strftime("d:%d %H:%M:%S"), "name": _name, "address": {_to}, "tokenId": {
                _id}, "success": False, 'gasPrice': gas_prices['max'], 'gasused': None, 'transfered': None, 'type': "transfer", "error": "Reverted : The token might have been just transferred, or the approval have been removed from the middleman wallet ! "}
            with open("./logs/failed.txt", "a") as file:
                file.write(str(result) + "\n")
            print(
                f"xx----- Error while transferring token n°{_id} to {_name}: Contract Logic Error !!")
            return result
        except ValueError:
            result = {"time": datetime.now().strftime("d:%d %H:%M:%S"), "name": _name, "address": {_to}, "tokenId": {
                _id}, "success": False, 'gasPrice': gas_prices['max'], 'gasused': None, 'transfered': None, 'type': "transfer", "error": "Not enought ETH to pay Gas Fees"}
            with open("./logs/failed.txt", "a") as file:
                file.write(str(result) + "\n")
            print(
                f"xx----- Error while transferring token n°{_id} to {_name}: Not enough ETH to pay gas !!")
            return result
        except Exception as exc:
            result = {"time": datetime.now().strftime("d:%d %H:%M:%S"), "name": _name, "address": {_to}, "tokenId": {
                _id}, "success": False, 'gasPrice': gas_prices['max'], 'gasused': None, 'transfered': None, 'type': "transfer", "error": exc}
            print(
                f"xx----- Error while transferring token n°{_id} to {_name}: Unknown Error when sending transaction !!")
            with open("./logs/failed.txt", "a") as file:
                file.write(str(result) + "\n")
            return result

# TRANSFER FUCNTION               ###    END
############################################


############################################
# RECIPIENT CLASS & OTHER FUNCTIONS
class Recipient():
    def __init__(self, name, number, tokens, address) -> None:
        self.name = name
        self.number = number
        self.tokens = tokens
        self.address = Web3.toChecksumAddress(address)
        self.transferred = []

    def check(self):
        if not self.tokens:
            return False
        if len(self.tokens) > self.number:
            return False
        if self.address != Web3.toChecksumAddress(self.address):
            return False
        return True

    def transfer_nft(self, goal, id):
        if not id in self.tokens:
            print(f"xx---- ERROR : token n° {id} not in {self.name} tokens")
            return False
        if id in self.transferred:
            print(
                f"xx---- ERROR : token n° {id} already transferred to {self.name} ")
            return False
        result = send_nft(goal=goal, _from=vault,
                          _to=self.address, _id=id, _name=self.name)

        if goal == "estimate" and result:
            return True
        if goal == "execute" and result and result["success"]:
            self.transferred.append(id)
            cost = float(Web3.fromWei(
                result['gasPrice']*result['gasused'], "ether"))
            print(
                f"== Successfully transfered token n° {id} to {self.name}. maxCost = {cost:.5f} ETH : {cost*eth_price:.2f} $ \n ")
            return True
        else:
            return False

    def __repr__(self) -> str:
        return f"RECIPIENT: {self.name}, tokens: {self.tokens}, address: {self.address} .... check : {self.check()} "


def import_recipients():
    recips = []
    with open("./recipients/recipients.csv", "r") as file:
        lines = file.readlines()
        for l in lines:
            name = l.replace("\n", "").split(";")[0]
            number = int(l.replace("\n", "").split(";")[1])
            tokens = [int(i) for i in l.replace(
                "\n", "").split(";")[2].split(",")]
            '''
            # You can use the following if you want to limit the transfered tokens to a certain range or a specific list
            limited_list = [10,22,34,99,223] or limited_list = range(16, 99)
            tokens = list(filter(lambda x: x in limited_list, [int(i) for i in l.replace("\n", "").split(
                ";")[2].split(",")]))
            '''
            address = l.replace("\n", "").split(";")[3]
            recips.append(Recipient(name, number, tokens, address))
    return recips


def execute_batch_transfer(accounts):
    total = sum(len(acc.tokens) for acc in accounts)

    print(
        f"Operation BatchTransfer.wtf : Transferring {total} tokens to {len(accounts)} accounts. ")

    inp = input("Proceed ? : ")
    if inp != "ok" and inp != "OK":
        exit()

    print("Initiating transfers .....")
    i = 0
    for acc in accounts:
        print(f"\n - - - - ACCOUNT : {acc.name} - - - - - - ")
        if acc.check():
            for tok in acc.tokens:
                i += 1
                print(f"-- Token n° {tok} ({i}/{total}) :")
                acc.transfer_nft("execute", tok)
                time.sleep(3)
        else:
            print(f'xx---- Problem with account : {acc.name} ')

# OTHER FUCNTIONS                 ###    END
############################################


################# EXECUTION STARTS HERE ############################################

if __name__ == "__main__":

    connect()
    accounts = import_recipients()

    ''' Use this to batch transfer NFTs to the list in recipients.csv '''
    execute_batch_transfer(accounts)

    ''' Use this to make transfers for a specific wallet'''
    # recipient_name = "input name here"
    # recipient_wallet = Web3.toChecksumAddress("input recipient wallet here")
    # tokens_to_transfer = []
    # recipientObject = Recipient(recipient_name, len(tokens_to_transfer), tokens_to_transfer, recipient_wallet)
    # execute_batch_transfer([recipientObject])
