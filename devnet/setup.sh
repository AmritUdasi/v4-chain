#!/bin/bash
set -eo pipefail

# Function to check if validator node is ready
wait_for_validator() {
    echo "Waiting for validator node to be ready..."
    while true; do
        if curl -s http://dydxprotocold0:26657/status > /dev/null; then
            echo "Validator node is ready!"
            break
        fi
        echo "Validator node not ready yet, waiting..."
        sleep 5
    done
}

# The mnemonic for alice from local.sh
ALICE_MNEMONIC="merge panther lobster crazy road hollow amused security before critic about cliff exhibit cause coyote talent happy where lion river tobacco option coconut small"

# The target address to send funds to
TARGET_ADDRESS="dydx1m6jt7uy2znc2uvcskkrmncye49e8e5qgynmtgr"

# Wait for validator to be ready
wait_for_validator

# Recover alice account
echo "$ALICE_MNEMONIC" | dydxprotocold keys add alice --recover --keyring-backend test

# Send funds
dydxprotocold tx bank send \
    alice \
    $TARGET_ADDRESS \
    10000000000000ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5 \
    --chain-id localdydxprotocol \
    --keyring-backend test \
    --fees 5000000000000000adv4tnt \
    --home /dydxprotocol/chain/.alice \
    --node http://dydxprotocold0:26657 \
    -y

echo "Setup completed successfully!" 