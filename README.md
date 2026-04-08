❄️ Shared Fridge — AI Smart Assistant
Shared Fridge is an intelligent grocery management system featuring a unique "fridge-view" interface. It allows users to manage their food supplies manually or via AI, which parses natural language to automatically stock the digital shelves.

🚀 Key Features
Multi-Device Support: Access and manage your fridge from any device (phone, tablet, or PC) within your network. Perfect for shared households!

Fridge-Door Interface: A modern UI/UX mimicking the interior of an open refrigerator with "glass shelves."

AI Magic Add: Extract grocery items from raw text (recipes, messy chat messages, etc.) using the Llama 3.3 model via the Groq LPU™ platform.

Priority Tracking: Support for marking essential items as "Extra Cold" (Important), highlighting them with a "glacial" blue glow to ensure they stay at the top of the list.

Dockerized Stack: Fully containerized Backend and Frontend, ready to deploy with a single command.

🛠 Tech Stack
Frontend: HTML5, Tailwind CSS (Modern UI).

Backend: FastAPI (Python), SQLAlchemy (SQLite).

AI: Groq API (Llama 3.3 70B model).

Infrastructure: Docker & Docker Compose.

📦 Getting Started
1. Clone the Repository
Bash
git clone https://github.com/your-username/shared-fridge.git
cd shared-fridge
2. Configure Environment Variables
Create a .env file in the project root and add your API key from the Groq Console:

Plaintext
GROQ_API_KEY=gsk_your_secret_key_here
3. Run via Docker
Execute the following command in your terminal:

Bash
docker compose up --build -d
4. Usage
Frontend Interface: Open http://localhost:8080 (or your VM IP) in your browser.

Interactive API Documentation (Swagger): Available at http://localhost:8000/docs.

📝 Remote Deployment (VM)
If running on a Virtual Machine, remember to update the API address in index.html:

JavaScript
const API_URL = 'http://YOUR_VM_IP:8000/items/';
🤝 Project Info
Author: Maksim Beketov

Developed for the Software Engineering Toolkit Hackathon 2026.