# BATCH TRANSFER ERC-721 TOKENS

A python script to batch transfer ERC-721 tokens (NFTs) using web3.py

## Disclaimer

This script requires exporting and using a wallet's private key.
It is very dangerous to export a wallet's private key unless you are 100% confident about the security of your machine/network.

## How to use

This method uses the ERC-721 transferFrom() function.
It is recommanded that you use a burner wallet as a 'middleman' to transfer NFTs from your main wallet.
You can grant permission to this middleman wallet to transfer your NFTs using setApprovalForAll() function of the NFTs smart contract. You can use Etherscan for that, and set the middleman wallet as the "operator", and "approved" to 'true'.
You should then create a `.env` with the correct parameters, and add the list of recipients and tokens to the `recipients\recipients.csv` file.
Once you're done, revoke permission to the middleman wallet using setApprovalForAll() function on etherscan by setting "approved" to 'false'.

## Requirements

- Python 3.7

## Installation

1. Create a virtual environment (recommended) and activate it: `python -m venv myvenv`
2. Install requirements: `pip install -r requirements.txt`
3. Copy the `.env.example` file to `.env` and edit the parameters (see Parameters section below)
4. Edit the `recipients\recipients.csv` file to add recipients and tokens to transfer to each of them.
5. Run the script: `python batch-transfer-ERC721.py`
6. The successful and failed transactions will be saved in `\logs`

## Parameters

- _ETH_PRICE_: used to calculate the transaction fee in dollars.
- _MAX_COST_PER_TRANSACTION_IN_DOLLARS_: The maximum transaction fee in Dollars you are willing to pay. If gas fees are higher than this value, the script will wait until the gas price drops.
- _CHAIN_ID_: 1 for Mainnet (you can modify it if you're testing on a testnet)
- _NODE_PROVIDER_: Your node provider endpoint (Infura, Alchemy, etc)
- _CONTRACT_ADDRESS_: The contract of the NFTs to be transferred
- _VAULT_ADDRESS_: The address of the wallet containing the NFTs to be transferred
- _MIDDLEMAN_PRIVATE_KEY_: The private key of wallet that will execute the transfers. This wallet needs to set as an approved opperator by the _VAULT_ADDRESS_ using the setApproavalForAll() function.

- `Recipients.csv` should contain lines structured as follows : `recipient_name;number_of_tokens_to_transfer;token_ids_to_transfer(separated by ',');recipient_address`

## Important

Read comments in the `batch-transfer-ERC721.py` file to further customize the script :

- Edit `lines 54 to 57` to define your own gas price strategy.
- Uncomment `lines 122 to 125` if you want to confirm each transaction before executing it (Keep in mind that gas prices might increase if you take too long to confirm)
- Edit `line 217` to specify a limited list/range of tokens to be transferred

Again, keep in mind that it is **very dangerous** to export and copy a wallet's private key. Do not use this method unless you are confident about the security of your devide and unless you know what you're doing. For more security, you can edit the script to generate the transaction signatures offline before sending them to the blockchain.

I did not spend a lot of time in making proper logging, or adding additional safeguards such as verifying that the token is indeed owned by the _VAULT_ADDRESS_. Feel free to submit your suggestions to improve the script.

---

ColonelBihi
9Tales Team
