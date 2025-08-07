# 🎨 Headless Infographic Generator API

A powerful FastAPI-based service that generates beautiful, interactive infographics from text prompts using AI and D3.js visualization.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

- **🤖 AI-Powered Generation**: Creates infographics from natural language prompts using Google Gemini
- **🎨 Multiple Variants**: Generates 3 different design variants per request
- **📊 D3.js Visualizations**: Uses D3.js for high-quality, interactive graphics
- **🖼️ SVG Output**: Produces scalable vector graphics with proper XML formatting
- **🖥️ Headless Browser**: Automated SVG extraction using Playwright
- **🪟 Windows Compatible**: Solved Windows subprocess limitations with process isolation
- **⚡ RESTful API**: Easy integration with FastAPI and automatic documentation
- **📈 High Success Rate**: 67-83% success rate with graceful error handling

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js (for Playwright browser installation)
- Google Gemini API key
- Windows/Linux/macOS

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/headless-infographic-api.git
   cd headless-infographic-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

5. **Set up environment variables**
   ```bash
   # Create .env file
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

### Running the API

```bash
# Start the development server
cd src
python -m uvicorn api_headless_infographic:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Endpoint**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Usage

### Generate Infographics

**Endpoint**: `POST /generate-infographics`

**Request Body**:
```json
{
  "prompt": "solar energy vs wind energy",
  "style_preference": "creative and modern"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully generated 3/3 infographic variants",
  "variants": [
    {
      "variant_id": 1,
      "success": true,
      "svg_content_base64": "PHN2ZyB3aWR0aD0iODAw...",
      "file_size": 15420,
      "message": "Success: 15420 bytes",
      "svg_file_path": "/path/to/variant_1/infographic.svg"
    }
  ],
  "generation_time": 45.2,
  "output_directory": "/path/to/generated/batch_xxx"
}
```

### Example with cURL

```bash
curl -X POST "http://localhost:8000/generate-infographics" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "machine learning vs deep learning",
       "style_preference": "professional and informative"
     }'
```

### Example with Python

```python
import requests
import base64

# Make API request
response = requests.post(
    "http://localhost:8000/generate-infographics",
    json={
        "prompt": "steps to make coffee",
        "style_preference": "creative and modern"
    }
)

result = response.json()

# Save SVG files locally
for variant in result["variants"]:
    if variant["success"]:
        svg_content = base64.b64decode(variant["svg_content_base64"]).decode('utf-8')
        
        with open(f"infographic_variant_{variant['variant_id']}.svg", 'w') as f:
            f.write(svg_content)
        
        print(f"Saved variant {variant['variant_id']} ({variant['file_size']} bytes)")
```

## Testing

Run the test suite:

```bash
# Start the API first
python start_api.py

# In another terminal, run tests
python tests/test_api_client.py
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Gemini AI      │    │   Playwright    │
│   Endpoint      │───▶│   HTML/D3.js     │───▶│   Headless      │
│                 │    │   Generation     │    │   Browser       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│   Response      │                            │   SVG Files     │
│   JSON + Base64 │◀───────────────────────────│   Generated     │
└─────────────────┘                            └─────────────────┘
```

## 📁 Project Structure

```
headless-infographic-api/
├── src/
│   ├── api_headless_infographic.py    # Main FastAPI application
│   ├── svg_extractor.py               # Headless browser SVG extraction
│   ├── gemini_api_d3_single_frame.py  # AI content generation
│   └── generated/                     # Output directory
├── tests/
│   ├── quick_test.py                  # API testing script
│   └── simple_test.py                 # Simple test cases
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore rules
├── LICENSE                            # MIT License
└── README.md                          # This file
```

## Deployment

### Local Development
```bash
python start_api.py
```

### Production with Gunicorn
```bash
cd src
gunicorn api_headless_infographic:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker (create Dockerfile)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m playwright install chromium

COPY . .
EXPOSE 8000

CMD ["uvicorn", "src.api_headless_infographic:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
LOG_LEVEL=INFO
MAX_VARIANTS=3
EXTRACTION_TIMEOUT=120
```

See `.env.example` for all available configuration options.

## 📊 Performance

- **Generation Time**: ~2-3 minutes per request (3 variants)
- **Success Rate**: 67-83% (typically 2-3 successful variants)
- **File Size**: 2-10KB per SVG file
- **Concurrent Requests**: Supports multiple simultaneous requests

## 🧪 Testing

Run the test suite:

```bash
# Basic functionality test
python quick_test.py

# Simple API test
python simple_test.py
```

## 🐛 Troubleshooting

### Common Issues

1. **Playwright Installation**
   ```bash
   # If browser installation fails
   playwright install --force chromium
   ```

2. **Windows Subprocess Issues**
   - The API automatically handles Windows subprocess limitations
   - Uses separate process isolation for SVG extraction

3. **Memory Issues**
   - Increase system memory if extraction fails frequently
   - Reduce concurrent requests if needed

4. **Network Timeouts**
   - Check internet connection for D3.js CDN access
   - Increase timeout values if needed

5. **API Key Issues**
   - Ensure your `.env` file contains a valid `GEMINI_API_KEY`
   - Get your API key from: https://makersuite.google.com/app/apikey

## 🚀 Deployment

### Production with Gunicorn
```bash
cd src
gunicorn api_headless_infographic:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .
EXPOSE 8000

CMD ["uvicorn", "src.api_headless_infographic:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** for content generation
- **D3.js** for visualization framework
- **Playwright** for headless browser automation
- **FastAPI** for the web framework

## 📞 Support

For support and questions:
- Open an issue on GitHub
- Check the [API documentation](http://localhost:8000/docs) when running locally

---

**Made with ❤️ and AI**
