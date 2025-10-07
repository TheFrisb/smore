.PHONY: ruff

up:
	sudo docker compose up -d

down:
	sudo docker compose down

clean-volumes:
	sudo docker compose down -v

ngrok:
	ngrok http --domain magical-rat-merely.ngrok-free.app 8000


ruff:
	ruff check . --select I,F401 --fix