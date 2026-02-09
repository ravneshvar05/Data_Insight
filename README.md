# Automated Data Insight System

A production-ready automated data insight system that performs deep data profiling, generates business-relevant visualizations, and produces high-quality insights using LLMs.

## 🎯 Features

- **📁 Dataset Upload**: Support for CSV files with comprehensive validation
- **🔍 Deep Data Profiling**: Statistical analysis using pandas/numpy (no LLM)
  - Automatic column classification (numeric, categorical, datetime, ID detection)
  - Comprehensive statistics (mean, median, std, quartiles, skewness, kurtosis, outliers)
  - Correlation analysis with strong relationship detection
  - Data quality checks (duplicates, missing values, constant columns)
- **📈 AI-Powered Visualizations**: LLM-based visualization planning
  - Intelligent chart selection (5-8 plots per dataset)
  - Business-relevant plots only
  - Automatic ID/index column exclusion
  - Support for bar, line, histogram, box, scatter, and heatmap charts
- **💡 Business Insights**: LLM-generated comprehensive insights
  - 800-1200 words of detailed analysis
  - Executive summary, key insights, risks, opportunities, recommendations
  - Fact-based, no fabricated numbers
- **📄 PDF Reports**: Downloadable comprehensive reports
  - Dataset overview, statistics, visualizations, insights
  - Professional formatting with embedded charts

## 🏗️ Architecture

```
project_root/
├── app/                        # Streamlit frontend
│   ├── main.py                 # Main entry point
│   └── pages/                  # Individual pages
│       ├── upload.py
│       ├── profiling.py
│       ├── visualizations.py
│       ├── insights.py
│       └── report.py
├── src/                        # Backend modules
│   ├── profiling/              # Data profiling (pandas/numpy)
│   ├── visualization/          # LLM planner + Plotly generator
│   ├── insights/               # LLM-based insight engine
│   ├── report/                 # PDF generation
│   ├── llm/                    # Groq API client
│   └── utils/                  # Logger, config, validators
├── config/                     # Configuration files
│   └── config.yaml
├── logs/                       # Application logs
├── requirements.txt            # Dependencies
├── .env.example                # Environment template
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Groq API key ([Get one here](https://console.groq.com/keys))

### Installation

1. **Clone or download the project**

```bash
cd "d:\Intership Projects\Project"
```

2. **Create a virtual environment**

```bash
python -m venv venv
```

3. **Activate the virtual environment**

Windows:
```bash
venv\Scripts\activate
```

Linux/Mac:
```bash
source venv/bin/activate
```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

5. **Set up environment variables**

Copy `.env.example` to `.env` and add your Groq API key:

```bash
copy .env.example .env
```

Edit `.env` and replace `your_groq_api_key_here` with your actual API key.

6. **Run the application**

```bash
streamlit run app/main.py
```

The application will open in your default browser at `http://localhost:8501`

## ☁️ Deployment

### Streamlit Cloud
1. Push your code to GitHub.
2. Login to [Streamlit Cloud](https://streamlit.io/cloud).
3. Connect your account and deploy the repository.
4. Add your secrets (`GROQ_API_KEY`) in the "Advanced Settings" secrets management.

### Hugging Face Spaces
1. Create a new Space (SDK: Streamlit).
2. Upload your files (or connect GitHub).
3. Set `GROQ_API_KEY` in the "Settings" -> "Variables and secrets" tab.
4. **Note**: The `packages.txt` file (if present) ensures system dependencies are installed. `requirements.txt` handles Python libraries.

### Docker (Optional)
A `Dockerfile` can be added for containerized deployment. Ensure `kaleido` dependencies are met in the base image.

## 📖 Usage Guide

### 1. Upload Dataset
- Navigate to "Upload Dataset" page
- Upload a CSV file (max 100MB)
- Preview dataset and column information

### 2. Data Profiling
- Navigate to "Data Profiling" page
- Click "Run Data Profiling"
- Explore:
  - Dataset overview (rows, columns, memory)
  - Numeric column statistics
  - Categorical column analysis
  - Correlation matrix
  - Data quality report

### 3. Generate Visualizations
- Navigate to "Visualizations" page
- Click "Generate AI-Powered Visualizations"
- LLM will select 5-8 business-relevant charts
- View interactive Plotly visualizations

### 4. Generate Insights
- Navigate to "Insights" page
- Click "Generate AI-Powered Insights"
- Wait for LLM to generate 800-1200 words of analysis
- Read structured insights with sections:
  - Executive Summary
  - Key Insights
  - Risks & Anomalies
  - Opportunities
  - Actionable Recommendations

### 5. Generate Report
- Navigate to "Generate Report" page
- Click "Generate PDF Report"
- Download comprehensive PDF with all analysis

## ⚙️ Configuration

Edit `config/config.yaml` to customize:

- **Profiling settings**: ID column patterns, correlation threshold, outlier detection
- **LLM settings**: Models, temperature, timeout, max tokens
- **Visualization settings**: Number of plots, theme, color palette
- **Insights settings**: Word count, output format, sections
- **Report settings**: Font sizes, margins

## 🔧 Technical Details

### LLM Usage

The system uses LLMs for **ONLY**:
1. **Visualization Planning**: Deciding which plots to create (not computing data)
2. **Insight Generation**: Writing business narratives (using pre-computed statistics)

All calculations and statistics are done using **pandas/numpy**.

### Models Used (Groq)

- **Visualization Planning**: `llama-3.1-8b-instant` (faster)
- **Insight Generation**: `llama-3.3-70b-versatile` (stronger)

You can override these in `.env`:
```
VISUALIZATION_MODEL=llama-3.1-8b-instant
INSIGHT_MODEL=llama-3.3-70b-versatile
```

### ID Column Detection

The system automatically detects and excludes ID/index columns using:
- Pattern matching (id, index, key, uuid, guid)
- High cardinality threshold (>95% unique values)

This prevents meaningless insights about identifiers.

## 📊 Example Workflow

1. Upload `sales_data.csv`
2. System profiles data:
   - Detects numeric columns: revenue, quantity, price
   - Detects categorical columns: product, region, category
   - Detects ID columns: order_id, customer_id (excluded)
   - Finds correlations: revenue ↔ quantity (0.82)
3. LLM plans visualizations:
   - Revenue distribution histogram
   - Revenue by region bar chart
   - Revenue vs quantity scatter plot
   - Category contribution pie chart
   - Time series line chart
4. LLM generates insights:
   - "Revenue is heavily concentrated in Region A (45%)..."
   - "Strong correlation between quantity and revenue suggests..."
   - "Risk: High missing values in customer_demographics..."
5. Generate PDF report with all findings

## 🛠️ Development

### Project Structure

- **app/**: Streamlit multi-page application
- **src/profiling/**: DataProfiler class (pure pandas/numpy)
- **src/visualization/**: VisualizationPlanner (LLM) + PlotGenerator (Plotly)
- **src/insights/**: InsightEngine (LLM)
- **src/report/**: PDFReportGenerator (ReportLab)
- **src/llm/**: GroqClient wrapper with retry logic
- **src/utils/**: Logger, Config, Validators

### Adding New Features

To add a new chart type:
1. Add to `plot_generator.py`: Create `_create_[type]_plot()` method
2. Update `planner.py`: Add type to `valid_plot_types`
3. Update LLM prompt in `groq_client.py`

## 🐛 Troubleshooting

### "GROQ_API_KEY not found"
- Ensure `.env` file exists
- Check that API key is set correctly
- Restart the application

### "Failed to generate visualizations"
- Check internet connection
- Verify Groq API key is valid
- Check logs in `logs/app.log`

### "Error loading CSV"
- Ensure file encoding is UTF-8 or Latin-1
- Check for corrupted CSV data
- Verify file size < 100MB

### PDF generation fails
- Install `kaleido` for Plotly image export: `pip install kaleido`
- Check write permissions in temp directory

## 📝 Logging

Logs are saved to `logs/app.log` with rotation (10MB × 5 files).

View logs:
```bash
tail -f logs/app.log  # Linux/Mac
type logs\app.log     # Windows
```

## 🔒 Security Notes

- Datasets are stored in session state only (not persisted to disk)
- No data is sent to external services except Groq API for LLM calls
- API keys are loaded from environment variables
- Add `.env` to `.gitignore` (already configured)

## 📄 License

This project is for educational and commercial use.

## 🤝 Contributing

This is a production-ready template. Customize as needed for your use case.

## 📧 Support

For issues or questions:
1. Check `logs/app.log` for error details
2. Review configuration in `config/config.yaml`
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

## 🎓 Credits

Built with:
- Streamlit (Frontend)
- Pandas & NumPy (Data processing)
- Plotly (Visualizations)
- Groq API (LLM inference)
- ReportLab (PDF generation)
- SciPy & Scikit-learn (Statistics)

---

**Version**: 1.0.0  
**Last Updated**: February 2026
