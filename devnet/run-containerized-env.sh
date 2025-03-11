cd ../protocol
make devnet-build-image
cd ../devnet
docker compose -f docker-compose-devnet.yml up
