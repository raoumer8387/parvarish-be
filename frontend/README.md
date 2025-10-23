# Parvarish AI Frontend

A clean, modern chat interface for interacting with Parvarish AI - your Islamic parenting assistant.

## Features

- 🌙 Beautiful gradient UI with Islamic theme
- 💬 Real-time chat interface
- 📱 Responsive design (works on mobile and desktop)
- ⚡ Fast and lightweight (pure HTML/CSS/JavaScript)
- 🔄 Loading indicators and error handling

## Setup

### Option 1: Serve via FastAPI (Recommended)

The frontend is automatically served by FastAPI when you run the backend:

```bash
# Start the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open your browser to:
```
http://localhost:8000
```

### Option 2: Serve Independently

You can also serve the frontend files independently using any static file server:

```bash
# Using Python's built-in server
cd frontend
python -m http.server 8080
```

Then open: `http://localhost:8080`

**Note:** If serving independently, make sure to update the `API_BASE_URL` in `script.js` to point to your backend server.

## Usage

1. Type your parenting question in the text area
2. Press Enter or click the send button
3. Wait for Parvarish AI to retrieve relevant Islamic references and respond
4. Continue the conversation!

## Example Questions

- "My kid is five years old and often gets angry if we don't fulfill his requirements"
- "How do I teach my children about prayer?"
- "What does Islam say about disciplining children?"
- "How can I be a better parent according to Islamic teachings?"

## Configuration

### Backend URL

If your backend is running on a different port or host, update the `API_BASE_URL` in `script.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';  // Change this
```

### Styling

Feel free to customize the colors and styling in `style.css` to match your preferences.

## Troubleshooting

### "Error: Failed to fetch"
- Make sure the backend server is running on the correct port
- Check that CORS is properly configured in the backend
- Verify the `API_BASE_URL` in `script.js` matches your backend URL

### Backend not responding
- Ensure all required dependencies are installed: `pip install fastapi uvicorn sentence-transformers chromadb fastapi_poe`
- Check that the POE_API_KEY is set in your `.env` file
- Verify the vector database is properly initialized

## Technologies Used

- HTML5
- CSS3 (with animations and gradients)
- Vanilla JavaScript (no frameworks needed!)
- Fetch API for backend communication

## Browser Support

Works on all modern browsers:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Opera

---

Made with ❤️ for Islamic parenting
