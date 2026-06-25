# 🤖 FlowDesk AI FAQ Chatbot

An AI-powered FAQ chatbot built using **React, Flask, Google Gemini, FAISS, and Sentence Transformers**. It uses **Retrieval-Augmented Generation (RAG)** to retrieve relevant information before generating responses, reducing hallucinations and improving answer accuracy.

## 🚀 Live Demo

**Frontend:** https://flowdesk-faq-chatbot.vercel.app

**Backend:** https://flowdesk-faq-chatbot.onrender.com

---

## ✨ Features

- AI-powered FAQ assistant
- Retrieval-Augmented Generation (RAG)
- Semantic search using FAISS
- Google Gemini integration
- Confidence score & source citations
- User feedback system
- Query logging with SQLite
- Responsive React UI

---

## 🛠️ Tech Stack

**Frontend**
- React
- Vite
- CSS

**Backend**
- Flask
- Flask-CORS
- SQLite

**AI/ML**
- Google Gemini API
- Sentence Transformers
- FAISS

**Deployment**
- Render
- Vercel
- GitHub

---

## 📂 Project Structure

```text
FlowDesk-FAQ-Chatbot/
├── app.py
├── build_index.py
├── faq_dataset.json
├── requirements_backend.txt
├── frontend/
└── README.md
```

---

## ⚙️ Installation

### Backend

```bash
pip install -r requirements_backend.txt
python build_index.py
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🔑 Environment Variables

Backend

```env
GEMINI_API_KEY=YOUR_API_KEY
```

Frontend

```env
VITE_API_BASE=http://localhost:5000
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Generate AI response |
| POST | `/feedback` | Store user feedback |
| GET | `/health` | Health check |

---

## 📌 Future Improvements

- User Authentication
- Voice Support
- Multi-language Support
- Admin Dashboard
- PDF Knowledge Base Upload

---

## 👨‍💻 Author

**Dhruv Gherwada**

GitHub: https://github.com/Dhruv220605

---

## 📄 License

Developed as part of the **Elevate Labs Virtual Internship Program**.
