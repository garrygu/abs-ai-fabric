# Contract Reviewer v2

A professional AI-powered contract analysis platform with a modern three-panel interface, designed for legal professionals and enterprise users.

## 🎯 Features

### Professional Three-Panel Layout
- **Left Panel**: Document navigation, upload management, and risk filtering
- **Center Panel**: Analysis results with tabs for Summary, Risks, Recommendations, and Comments
- **Right Panel**: AI chat interface for asking questions about the contract

### AI-Powered Analysis
- Comprehensive contract review using advanced language models
- Risk assessment with Low/Medium/High categorization
- Clause extraction and categorization
- Smart recommendations for contract improvements
- Confidence scoring for analysis results

### Modern User Experience
- Drag-and-drop file upload
- Real-time analysis progress
- Professional color scheme and typography
- Responsive design for all screen sizes
- Dark mode support (optional)

### Gateway Integration
- Seamless integration with ABS Hub Gateway
- Automatic model management and service discovery
- Shared services utilization (Redis, Qdrant, Ollama)
- Policy-based model access control

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- ABS Hub Gateway running
- Required services: Redis, Qdrant, Ollama

### Installation

1. **Clone and navigate to the app directory:**
   ```bash
   cd abs-ai-hub/apps/contract-reviewer-v2
   ```

2. **Start the application:**
   ```bash
   docker compose up -d
   ```

3. **Access the application:**
   Open your browser and navigate to `http://localhost:8080`

### Using the ABS Hub UI

The app is automatically registered in the ABS Hub and can be launched from the Hub UI:

1. Open the ABS Hub UI at `http://localhost:3000`
2. Find "Contract Reviewer v2" in the Legal Apps section
3. Click to launch the application

## 📖 Usage Guide

### 1. Upload Documents
- Drag and drop PDF or DOCX files onto the upload area
- Or click the upload area to browse and select files
- Supported formats: PDF, DOCX
- Maximum file size: 50MB

### 2. Analyze Contracts
- Select a document from the left panel
- Click "Analyze" to start AI-powered contract review
- Choose your preferred AI model from the dropdown
- Wait for analysis to complete (typically 30-60 seconds)

### 3. Review Results
- **Summary Tab**: Executive summary and key points
- **Risks Tab**: Identified risks with severity levels
- **Recommendations Tab**: Suggested improvements and alternatives
- **Comments Tab**: Add your own notes and comments

### 4. Chat with the Contract
- Use the right panel to ask specific questions
- Examples:
  - "What are the termination clauses?"
  - "What is the liability limit?"
  - "Are there any confidentiality requirements?"

### 5. Export Results
- Click the "Export" button in the header
- Choose format: JSON (more formats coming soon)
- Download the analysis report

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_PORT` | 8080 | Application port |
| `HUB_GATEWAY_URL` | http://hub-gateway:8081 | Gateway URL |
| `REDIS_URL` | redis://redis:6379/0 | Redis connection URL |
| `ABS_DATA_DIR` | /data | Data directory path |

### Model Configuration

The app uses the following models by default:
- **Chat Model**: llama3.2:3b
- **Embedding Model**: legal-bert
- **Provider**: Auto (Ollama/HuggingFace)

Models can be changed via the UI dropdown or configured in the catalog.json.

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **File Processing**: PyMuPDF for PDFs, python-docx for DOCX
- **AI Integration**: HTTP client to Hub Gateway
- **Caching**: Redis for session and document caching
- **Storage**: Local file system with Docker volumes

### Frontend (Vanilla JS + Alpine.js)
- **Framework**: Alpine.js for reactivity
- **Styling**: Tailwind CSS for modern design
- **Icons**: Font Awesome
- **Layout**: Three-panel responsive design

### Gateway Integration
- **Service Discovery**: Automatic via Hub Gateway
- **Model Management**: Policy-based access control
- **Auto-wake**: Services start automatically when needed
- **Health Monitoring**: Integrated health checks

## 📁 Project Structure

```
contract-reviewer-v2/
├── app.py                 # FastAPI backend
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Service orchestration
├── app.manifest.json     # App metadata and configuration
├── static/
│   └── index.html        # Frontend application
└── README.md             # This file
```

## 🔌 API Endpoints

### Document Management
- `POST /api/upload` - Upload and process documents
- `GET /api/documents` - List uploaded documents
- `DELETE /api/documents/{id}` - Delete a document

### Analysis
- `POST /api/review` - Perform contract analysis
- `GET /api/sessions` - List analysis sessions
- `GET /api/sessions/{id}` - Get session details
- `DELETE /api/sessions/{id}` - Delete a session

### Chat
- `POST /api/chat` - Chat with document using AI

### Export
- `GET /api/export/{session_id}` - Export analysis results

### System
- `GET /api/models` - Get available AI models
- `GET /healthz` - Health check endpoint

## 🛠️ Development

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8080 --reload
   ```

3. **Access the application:**
   Open `http://localhost:8080`

### Building the Docker Image

```bash
docker build -t contract-reviewer-v2 .
```

### Testing

```bash
# Run tests (when implemented)
pytest tests/

# Test API endpoints
curl http://localhost:8080/healthz
curl http://localhost:8080/api/models
```

## 🔒 Security

- CORS enabled for cross-origin requests
- File type validation (PDF, DOCX only)
- File size limits (50MB max)
- Input sanitization for chat messages
- No authentication required (can be added)

## 📊 Performance

- Async/await for non-blocking operations
- Redis caching for improved response times
- Chunked text processing for large documents
- Background processing for analysis tasks
- Optimized Docker image with minimal dependencies

## 🐛 Troubleshooting

### Common Issues

1. **Gateway Connection Error**
   - Ensure Hub Gateway is running
   - Check `HUB_GATEWAY_URL` environment variable
   - Verify network connectivity

2. **Model Not Available**
   - Check if Ollama service is running
   - Verify model is pulled in Ollama
   - Check catalog.json for model permissions

3. **File Upload Fails**
   - Verify file format (PDF/DOCX only)
   - Check file size (max 50MB)
   - Ensure sufficient disk space

4. **Analysis Takes Too Long**
   - Check Ollama service status
   - Verify model is loaded in memory
   - Consider using smaller models for faster processing

### Logs

View application logs:
```bash
docker logs abs-contract-reviewer-v2
```

View gateway logs:
```bash
docker logs abs-hub-gateway
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section above
- Review the ABS Hub documentation
- Open an issue in the repository
- Contact the development team

## 🔄 Version History

### v2.0.0 (Current)
- Complete redesign with three-panel layout
- Modern UI with Tailwind CSS
- Gateway integration
- Professional styling
- Enhanced chat interface
- Improved analysis capabilities

### v1.x (Legacy)
- Original contract reviewer
- Gradio-based interface
- Basic analysis features
