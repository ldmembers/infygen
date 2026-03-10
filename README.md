# CAPE: Context-Aware Personal Executive

CAPE is a high-performance, AI-driven personal knowledge assistant that aggregates your professional and personal data from Google Workspace (Gmail, Drive, Sheets) and local file uploads into a unified, searchable, and time-aware intelligence hub.

## 🚀 Key Features

- **Google Workspace Integration**: Seamlessly sync and index your Gmail threads, Google Drive documents (PDF, CSV, TXT), and Google Sheets data via a secure OAuth flow.
- **Semantic & Keyword Search**: A hybrid retrieval engine combining FAISS-based vector similarity with exact keyword boosting to ensure ultra-precise answers.
- **Automatic Timeline Reconstruction**: The AI extracts date references from your documents to build a chronological narrative of events.
- **Persistent Chat History**: Intelligent session management that stores your past conversations locally, allowing you to resume research across tabs or logouts.
- **Enhanced Anti-Hallucination**: Optimized system prompts and high-density retrieval (Top-K 15) prevent the AI from "inventing" facts, ensuring answers are 100% grounded in your actual data.
- **Private & Secure**: Embeddings are computed locally, and data is isolated per-user via Firebase Authentication.

## 🛠️ Technology Stack

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS (Premium Glassmorphic Design)
- **State Management**: React Hooks + LocalStorage Persistence
- **Auth**: Firebase Authentication (Google Login)

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite (Metadata) + FAISS (Vector Store/Embeddings)
- **AI/LLM**: OpenAI-compatible API (Supports local models like Qwen 2.5 via Ollama/OpenRouter)
- **Embeddings**: Sentence-Transformers (`all-MiniLM-L6-v2`)

## 📦 Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Google Cloud Project (for Gmail/Drive API credentials)
- Firebase Project (for Authentication)

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your `.env` file (see `.env.example` for required keys: `LLM_API_KEY`, `FIREBASE_CONFIG`, `GMAIL_CLIENT_ID`, etc.).
4. Run the FastAPI server:
   ```bash
   uvicorn main:app --port 8000 --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Configure your `.env` file with Firebase keys and API Base URL.
4. Run the development server:
   ```bash
   npm run dev
   ```

## 📖 Usage
1. **Login**: Use your Google account to log in via Firebase.
2. **Connect Google**: Navigate to the Gmail page and click "Connect with Google" to grant read-only access to your documents.
3. **Index Data**: Wait for the background worker to compute embeddings for your files.
4. **Chat**: Ask the assistant questions like "What are the technical skills in my resume?" or "List the recent emails from Internshala."

## 🔒 Security
- **OAuth 2.0**: Uses PKCE and state verification for secure Google authorization.
- **Data Isolation**: FAISS indices are partitioned by User ID; one user cannot query another's data.
- **Read-Only**: The app only requests `readonly` scopes from Google, ensuring your data cannot be modified or deleted.

---
*Built with ❤️ for advanced agentic productivity.*
