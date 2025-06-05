# Effibot-mcp-server
python3 -m venv venv
source venv/bin/activate

pip install "uvicorn[standard]" fastapi httpx
uvicorn server:app --reload --port 8000
uvicorn server:app --reload --port 4321
