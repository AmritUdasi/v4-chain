#!/usr/bin/env python3
import os
import json
import subprocess
import random
from time import sleep
from datetime import datetime

def recover_bob_account():
    """Recover Bob's account using the mnemonic"""
    # Check if bob's account already exists
    check_cmd = ["dydxprotocold", "keys", "list", "--keyring-backend", "test"]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    if "bob" in result.stdout:
        print("Bob's account already exists")
        return

    # Bob's actual mnemonic from local.sh
    mnemonic = "color habit donor nurse dinosaur stable wonder process post perfect raven gold census inside worth inquiry mammal panic olive toss shadow strong name drum"
    
    cmd = [
        "dydxprotocold", "keys", "add", "bob", 
        "--recover", 
        "--keyring-backend", "test"
    ]
    
    process = subprocess.Popen(
        cmd, 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    out, err = process.communicate(input=mnemonic.encode())
    if process.returncode != 0:
        raise Exception(f"Error recovering Bob's account: {err.decode()}")
    
    print("Successfully recovered Bob's account")

def get_market_price(market_id):
    """Get current market price from dYdX node"""
    try:
        cmd = ["dydxprotocold", "q", "prices", "market-price", str(market_id), "--output", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            price_data = json.loads(result.stdout)
            price = int(price_data['price']) / 1e6  # Convert from 6 decimal places
            print(f"Found price for market {market_id}: {price}")
            return price
    except Exception as e:
        print(f"Error getting price for {market_id}: {e}")
        print(f"Command output: {result.stdout}")
        print(f"Command error: {result.stderr}")
    
    # Default prices if query fails
    defaults = {
        "0": 10000000,  # BTC-USD
        "1": 10000000    # ETH-USD
    }
    return defaults.get(str(market_id), 20000)

def get_current_block():
    """Get current block height"""
    try:
        cmd = ["dydxprotocold", "status"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            status_data = json.loads(result.stdout)
            current_height = int(status_data['sync_info']['latest_block_height'])  # Fixed path
            print(f"Current block height: {current_height}")
            return current_height
    except Exception as e:
        print(f"Error getting block height: {e}")
        print(f"Command output: {result.stdout}")
        print(f"Command error: {result.stderr}")
        return None

def query_tx(txhash):
    """Query transaction details by hash"""
    try:
        # Wait a bit for the transaction to be included in a block
        sleep(3)
        
        cmd = ["dydxprotocold", "q", "tx", txhash, "--output", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            tx_data = json.loads(result.stdout)
            print(f"\nTransaction details for {txhash}:")
            print(json.dumps(tx_data, indent=2))
            
            # Check if transaction was successful
            if tx_data.get('code', 0) == 0:
                print("Transaction successful!")
            else:
                print(f"Transaction failed with code: {tx_data.get('code')}")
                print(f"Raw log: {tx_data.get('raw_log')}")
            return tx_data
    except Exception as e:
        print(f"Error querying transaction {txhash}: {e}")
    return None

def check_orderbook_and_fills(market_id):
    """Check orderbook and fills for a market"""
    print(f"\nChecking orderbook for market {market_id}...")
    
    # Check orderbook
    cmd_orderbook = ["dydxprotocold", "q", "clob", "orderbook", str(market_id), "--output", "json"]
    result = subprocess.run(cmd_orderbook, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout:
        try:
            orderbook = json.loads(result.stdout)
            print("\nOrderbook:")
            print(json.dumps(orderbook, indent=2))
        except json.JSONDecodeError:
            print("Could not parse orderbook response")
    
    # Check fills
    cmd_fills = ["dydxprotocold", "q", "clob", "fills", str(market_id), "--output", "json"]
    result = subprocess.run(cmd_fills, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout:
        try:
            fills = json.loads(result.stdout)
            print("\nFills:")
            print(json.dumps(fills, indent=2))
        except json.JSONDecodeError:
            print("Could not parse fills response")

def place_order_and_get_response(cmd, side_str):
    """Place order and parse the response"""
    print(f"\nExecuting {side_str} order command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"\n{side_str} Order Raw Output:")
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    
    try:
        # Try to parse as JSON first
        response = json.loads(result.stdout)
        print(f"\n{side_str} Order Response (JSON):")
        print(json.dumps(response, indent=2))
        return response
    except json.JSONDecodeError:
        # If not JSON, look for txhash in plain text
        if "txhash" in result.stdout:
            txhash = result.stdout.split("txhash: ")[1].strip()
            print(f"\n{side_str} Order txhash: {txhash}")
            
            # Query the transaction details
            sleep(2)  # Wait for transaction to be included
            tx_cmd = ["dydxprotocold", "q", "tx", txhash, "--output", "json"]
            tx_result = subprocess.run(tx_cmd, capture_output=True, text=True)
            if tx_result.returncode == 0 and tx_result.stdout:
                try:
                    tx_data = json.loads(tx_result.stdout)
                    print(f"\n{side_str} Order Transaction Details:")
                    print(json.dumps(tx_data, indent=2))
                    return tx_data
                except json.JSONDecodeError:
                    print("Could not parse transaction response")
    
    return None

def check_balance():
    """Check Bob's balance"""
    cmd = ["dydxprotocold", "q", "bank", "balances", "dydx10fx7sy6ywd5senxae9dwytf8jxek3t2gcen2vs", "--output", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout:
        try:
            balance = json.loads(result.stdout)
            print("\nBob's balance:")
            print(json.dumps(balance, indent=2))
            return balance
        except json.JSONDecodeError:
            print("Could not parse balance response")
    return None

def deposit_to_subaccount():
    """Deposit USDC to Bob's subaccount for trading"""
    bob_address = "dydx10fx7sy6ywd5senxae9dwytf8jxek3t2gcen2vs"
    
    # First check Bob's initial balance
    print("\nChecking initial balance...")
    check_balance()
    
    # Deposit larger amount to subaccount (100,000 USDC)
    cmd_deposit = [
        "dydxprotocold", "tx", "sending", "deposit-to-subaccount",
        "bob",           # sender key
        bob_address,     # recipient address
        "0",            # Changed subaccount number from 0 to 1
        "100000000000",   # quantums (100.0 USDC)
        "--from", "bob",
        "--chain-id", "localdydxprotocol",
        "--keyring-backend", "test",
        "--fees", "5000000000000000adv4tnt",
        "-y"
    ]
    
    print("\nDepositing to subaccount...")
    print(f"Executing command: {' '.join(cmd_deposit)}")
    result = subprocess.run(cmd_deposit, capture_output=True, text=True)
    print("Deposit output:", result.stdout)
    print("Deposit error (if any):", result.stderr)
    sleep(2)
    
    # Check subaccount balance after deposit
    check_subaccount_balance()

def check_subaccount_balance():
    """Check subaccount balance and return USDC balance"""
    cmd_subaccount = ["dydxprotocold", "q", "subaccounts", "list-subaccount", "--output", "json"]
    result = subprocess.run(cmd_subaccount, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout:
        try:
            subaccount = json.loads(result.stdout)
            print("\nSubaccount balance:")
            print(json.dumps(subaccount, indent=2))
            
            total_balance = 0
            # Check both subaccount 0 and 1
            for acc in subaccount.get("subaccount", []):
                if acc.get("id", {}).get("owner") == "dydx10fx7sy6wd5senxae9dwytf8jxek3t2gcen2vs":
                    print(f"Found subaccount: {acc.get('id')}")
                    for pos in acc.get("asset_positions", []):
                        if pos.get("asset_id") == 0:  # USDC
                            balance = int(pos.get("quantums", "0"))
                            total_balance += balance
                            print(f"Subaccount {acc.get('id').get('number')} balance: {balance}")
            return total_balance
        except json.JSONDecodeError:
            print("Could not parse subaccount response")
            return 0
    return 0

def enable_margin(address):
    """Enable margin for the subaccount"""
    cmd = [
        "dydxprotocold", "tx", "clob", "update-margin-enabled",
        address,
        "0",  # subaccount number
        "true",  # enable margin
        "--from", "bob",
        "--chain-id", "localdydxprotocol",
        "--keyring-backend", "test",
        "--fees", "5000000000000000adv4tnt",
        "-y"
    ]
    print("\nEnabling margin...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("Margin enable output:", result.stdout)
    sleep(2)

def place_orders(market_id, base_price):
    """Place multiple orders for market making with proper spreads"""
    bob_address = "dydx10fx7sy6ywd5senxae9dwytf8jxek3t2gcen2vs"
    alice_address = "dydx199tqg4wdlnu4qjlxchpd7seg454937hjrknju4"
    
    current_block = get_current_block()
    if current_block is None:
        print("Error: Could not get current block height. Exiting.")
        return
    
    blocks_ahead = 10
    good_til_block = str(current_block + blocks_ahead)
    base_quantity = 20000000000  # 2.0 units
    
    # Calculate prices that are multiples of tick_size (100000)
    tick_size = 100000
    
    # Market Making Parameters
    bob_price = base_price - (2 * tick_size)    # Bob buys at 9.8
    alice_price = base_price + (2 * tick_size)  # Alice sells at 10.2
    
    print(f"\nPlacing orders for market {market_id}")
    print(f"Base price: {base_price} (${base_price/1000000})")
    print(f"Bob buy price: {bob_price} (${bob_price/1000000})")
    print(f"Alice sell price: {alice_price} (${alice_price/1000000})")
    
    # Place Bob's BUY order
    cmd_buy = [
        "dydxprotocold", "tx", "clob", "place-order",
        bob_address,
        str(market_id),
        "0",  # order flag
        "0",  # BUY
        "1",  # limit order
        str(base_quantity),
        str(bob_price),
        good_til_block,
        "--from", "bob",
        "--chain-id", "localdydxprotocol",
        "--keyring-backend", "test",
        "--fees", "5000000000000000adv4tnt",
        "-y"
    ]
    buy_response = place_order_and_get_response(cmd_buy, f"BOB BUY at {bob_price}")
    sleep(2)
    
    # Place Alice's SELL order
    cmd_sell = [
        "dydxprotocold", "tx", "clob", "place-order",
        alice_address,
        str(market_id),
        "0",  # order flag
        "1",  # SELL
        "1",  # limit order
        str(base_quantity),
        str(alice_price),
        good_til_block,
        "--from", "alice",
        "--chain-id", "localdydxprotocol",
        "--keyring-backend", "test",
        "--fees", "5000000000000000adv4tnt",
        "-y"
    ]
    sell_response = place_order_and_get_response(cmd_sell, f"ALICE SELL at {alice_price}")
    sleep(2)
    
    # Now place a matching order from Alice at Bob's price to create a fill
    cmd_match = [
        "dydxprotocold", "tx", "clob", "place-order",
        alice_address,
        str(market_id),
        "1",  # different order flag
        "1",  # SELL
        "1",  # limit order
        str(base_quantity),
        str(bob_price),  # Match Bob's price
        good_til_block,
        "--from", "alice",
        "--chain-id", "localdydxprotocol",
        "--keyring-backend", "test",
        "--fees", "5000000000000000adv4tnt",
        "-y"
    ]
    match_response = place_order_and_get_response(cmd_match, f"ALICE MATCHING SELL at {bob_price}")
    sleep(2)
    
    check_orderbook_and_fills(market_id)

def cancel_old_orders(market_id, current_block):
    """Cancel existing orders to prevent accumulation"""
    bob_address = "dydx10fx7sy6ywd5senxae9dwytf8jxek3t2gcen2vs"
    
    cmd = [
        "dydxprotocold", "tx", "clob", "cancel-order",
        bob_address,      # owner address
        str(market_id),   # market id (CLOB pair ID)
        "0",             # order flags
        "0",             # order number
        str(current_block),  # good til block
        "--from", "bob",
        "--keyring-backend", "test",
        "--chain-id", "localdydxprotocol",
        "--fees", "5000000000000000adv4tnt",
        "-y"
    ]
    
    print(f"Executing cancel command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error canceling orders: {result.stderr}")
    else:
        print(f"Successfully canceled orders for market {market_id}")

def check_orders(market_id):
    """Check existing orders"""
    cmd = ["dydxprotocold", "q", "clob", "orders", str(market_id), "--output", "json"]
    print(f"Checking orders for market {market_id}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout:
        orders = json.loads(result.stdout)
        print(f"Current orders: {json.dumps(orders, indent=2)}")
        return orders
    return None

def deposit_for_alice():
    """Deposit USDC to Alice's subaccount for trading"""
    alice_address = "dydx199tqg4wdlnu4qjlxchpd7seg454937hjrknju4"
    
    cmd_deposit = [
        "dydxprotocold", "tx", "sending", "deposit-to-subaccount",
        "alice",
        alice_address,
        "0",
        "100000000000",   # 100,000 USDC
        "--from", "alice",
        "--chain-id", "localdydxprotocol",
        "--keyring-backend", "test",
        "--fees", "5000000000000000adv4tnt",
        "-y"
    ]
    
    print("\nDepositing to Alice's subaccount...")
    result = subprocess.run(cmd_deposit, capture_output=True, text=True)
    print("Deposit output:", result.stdout)
    print("Deposit error (if any):", result.stderr)
    sleep(2)

def recover_alice_account():
    """Recover Alice's account using the mnemonic"""
    # Check if alice's account already exists
    check_cmd = ["dydxprotocold", "keys", "list", "--keyring-backend", "test"]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    if "alice" in result.stdout:
        print("Alice's account already exists")
        return

    # Alice's actual mnemonic from local.sh
    mnemonic = "merge panther lobster crazy road hollow amused security before critic about cliff exhibit cause coyote talent happy where lion river tobacco option coconut small"
    
    cmd = [
        "dydxprotocold", "keys", "add", "alice", 
        "--recover", 
        "--keyring-backend", "test"
    ]
    
    process = subprocess.Popen(
        cmd, 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    out, err = process.communicate(input=mnemonic.encode())
    if process.returncode != 0:
        raise Exception(f"Error recovering Alice's account: {err.decode()}")
    
    print("Successfully recovered Alice's account")

def continuous_trading():
    """Continuously provide liquidity in the markets"""
    markets = ["0", "1"]  # BTC-USD and ETH-USD
    
    while True:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n=== Trading Cycle Start: {current_time} ===")
            
            for market_id in markets:
                print(f"\nProviding Liquidity for Market ID: {market_id}")
                
                # Check existing orders
                check_orders(market_id)
                
                # Get current market price
                price = get_market_price(market_id)
                print(f"Using price for market {market_id}: {price}")
                
                # Cancel old orders before placing new ones
                current_block = get_current_block()
                if current_block:
                    cancel_old_orders(market_id, current_block)
                sleep(5)
                
                # Place new orders
                place_orders(market_id, price)
                
                # Verify orders were placed
                check_orders(market_id)
                
                print(f"Completed liquidity provision for market {market_id}")
                sleep(10)
            
            print("\nWaiting for next cycle...")
            sleep(60)
            
        except Exception as e:
            print(f"Error in trading cycle: {e}")
            sleep(30)

def main():
    try:
        recover_bob_account()
        recover_alice_account()
        # Deposit funds for both accounts
        deposit_to_subaccount()  # For Bob
        deposit_for_alice()      # For Alice
        # Enable margin for both accounts
        enable_margin("dydx10fx7sy6ywd5senxae9dwytf8jxek3t2gcen2vs")  # Bob
        enable_margin("dydx199tqg4wdlnu4qjlxchpd7seg454937hjrknju4")  # Alice
        print("Starting continuous trading...")
        continuous_trading()
    except KeyboardInterrupt:
        print("\nTrading stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")

if __name__ == "__main__":
    main() 