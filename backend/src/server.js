/**
 * Mood Sentinel - Google Sheets Integration Server
 * Node.js Express server that implements POST /api/submit endpoint
 * to write health data to Google Sheets using Sheets API
 */

const express = require('express');
const cors = require('cors');
const { google } = require('googleapis');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files from public directory
app.use(express.static(path.join(__dirname, '../../public')));

// Google Sheets configuration
const SPREADSHEET_ID = process.env.SHEETS_SPREADSHEET_ID;
const SERVICE_ACCOUNT_KEY_PATH = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH || './service-account-key.json';

// Initialize Google Sheets API
let sheets;

async function initializeGoogleSheets() {
  try {
    // Load service account credentials
    let credentials;
    
    if (process.env.GOOGLE_SERVICE_ACCOUNT_KEY) {
      // If credentials are provided as environment variable (JSON string)
      credentials = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_KEY);
    } else {
      // If credentials are provided as file path
      credentials = require(SERVICE_ACCOUNT_KEY_PATH);
    }

    // Create JWT client
    const jwtClient = new google.auth.JWT(
      credentials.client_email,
      null,
      credentials.private_key,
      ['https://www.googleapis.com/auth/spreadsheets']
    );

    // Authenticate
    await jwtClient.authorize();

    // Initialize Sheets API
    sheets = google.sheets({ version: 'v4', auth: jwtClient });
    
    console.log('✅ Google Sheets API initialized successfully');
  } catch (error) {
    console.error('❌ Failed to initialize Google Sheets API:', error.message);
    throw error;
  }
}

// Helper function to format datetime for Sheets
function formatDateTime(dateString) {
  if (!dateString) return '';
  try {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  } catch (error) {
    return dateString;
  }
}

// POST /api/submit - Main endpoint for Google Sheets integration
app.post('/api/submit', async (req, res) => {
  try {
    // Validate required environment variables
    if (!SPREADSHEET_ID) {
      return res.status(500).json({
        error: 'Server configuration error',
        message: 'SHEETS_SPREADSHEET_ID environment variable is not set'
      });
    }

    if (!sheets) {
      return res.status(500).json({
        error: 'Google Sheets API not initialized',
        message: 'Server failed to connect to Google Sheets API'
      });
    }

    const data = req.body;
    console.log('📝 Received data for Google Sheets:', data);

    // Prepare row data for Google Sheets
    // Columns: Timestamp, Heart_Rate, HRV, Sleep_Score, Steps, Stress_Level, SpO2, 
    //          Resting_HR, Sleep_Start, Sleep_End, Activity_Minutes, Notes, Data_Source
    const rowData = [
      data.timestamp || new Date().toISOString(),
      data.heart_rate || '',
      data.hrv || '',
      data.sleep_score || '',
      data.steps || '',
      data.stress_level || '',
      data.spo2 || '',
      data.resting_hr || '',
      formatDateTime(data.sleep_start) || '',
      formatDateTime(data.sleep_end) || '',
      data.activity_minutes || '',
      data.notes || '',
      data.data_source || 'manual'
    ];

    // Write to Google Sheets
    const request = {
      spreadsheetId: SPREADSHEET_ID,
      range: 'Raw_Data!A:M', // Columns A through M
      valueInputOption: 'USER_ENTERED',
      insertDataOption: 'INSERT_ROWS',
      resource: {
        values: [rowData]
      }
    };

    console.log('📊 Writing to Google Sheets...', {
      spreadsheetId: SPREADSHEET_ID,
      range: 'Raw_Data!A:M',
      rowData: rowData
    });

    const response = await sheets.spreadsheets.values.append(request);
    
    console.log('✅ Successfully wrote to Google Sheets:', {
      updatedCells: response.data.updates?.updatedCells,
      updatedRange: response.data.updates?.updatedRange
    });

    // Return success response
    res.status(200).json({
      success: true,
      message: 'Data successfully submitted to Google Sheets',
      timestamp: new Date().toISOString(),
      updatedCells: response.data.updates?.updatedCells,
      updatedRange: response.data.updates?.updatedRange
    });

  } catch (error) {
    console.error('❌ Error submitting to Google Sheets:', error);
    
    // Return detailed error information
    res.status(500).json({
      error: 'Failed to submit data to Google Sheets',
      message: error.message,
      details: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'mood-sentinel-sheets-api',
    version: '1.0.0',
    googleSheetsConfigured: !!SPREADSHEET_ID && !!sheets
  });
});

// Root endpoint - serve the frontend
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/index.html'));
});

// API info endpoint
app.get('/api', (req, res) => {
  res.json({
    name: 'Mood Sentinel Google Sheets API',
    version: '1.0.0',
    endpoints: {
      'POST /api/submit': 'Submit health data to Google Sheets',
      'GET /health': 'Health check',
      'GET /': 'Frontend form interface'
    },
    configuration: {
      spreadsheetConfigured: !!SPREADSHEET_ID,
      googleSheetsApiInitialized: !!sheets
    }
  });
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('❌ Unhandled error:', error);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.method} ${req.path} not found`,
    availableEndpoints: ['/api/submit', '/health', '/api', '/']
  });
});

// Start server
async function startServer() {
  try {
    console.log('🚀 Starting Mood Sentinel Google Sheets Server...');
    
    // Initialize Google Sheets API first
    await initializeGoogleSheets();
    
    // Start listening
    app.listen(PORT, () => {
      console.log(`\n✅ Server running on http://localhost:${PORT}`);
      console.log(`📊 Google Sheets integration ready`);
      console.log(`📝 Frontend form available at http://localhost:${PORT}`);
      console.log(`🔗 Submit endpoint: POST http://localhost:${PORT}/api/submit`);
      console.log(`❤️  Health check: GET http://localhost:${PORT}/health`);
      
      if (!SPREADSHEET_ID) {
        console.warn('⚠️  WARNING: SHEETS_SPREADSHEET_ID not configured');
        console.warn('   Set SHEETS_SPREADSHEET_ID environment variable');
      }
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error.message);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('\n🛑 Received SIGTERM, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('\n🛑 Received SIGINT, shutting down gracefully...');
  process.exit(0);
});

// Start the server
startServer();

/*
 * ENVIRONMENT VARIABLES REQUIRED:
 * 
 * Required:
 * - SHEETS_SPREADSHEET_ID: The Google Sheets spreadsheet ID for "Mood" spreadsheet
 * 
 * Authentication (choose one):
 * - GOOGLE_SERVICE_ACCOUNT_KEY: JSON string of service account credentials
 * - GOOGLE_SERVICE_ACCOUNT_KEY_PATH: Path to service account JSON file (default: ./service-account-key.json)
 * 
 * Optional:
 * - PORT: Server port (default: 3001)
 * - NODE_ENV: Environment (development/production)
 * 
 * SETUP INSTRUCTIONS:
 * 
 * 1. Install dependencies:
 *    npm install express cors googleapis dotenv
 * 
 * 2. Create Google Service Account:
 *    - Go to Google Cloud Console
 *    - Enable Google Sheets API
 *    - Create Service Account
 *    - Download JSON key file
 * 
 * 3. Configure environment variables:
 *    - Copy .env.example to .env
 *    - Set SHEETS_SPREADSHEET_ID to your Google Sheets ID
 *    - Set GOOGLE_SERVICE_ACCOUNT_KEY_PATH to your JSON file path
 *    - Or set GOOGLE_SERVICE_ACCOUNT_KEY to JSON string content
 * 
 * 4. Grant permissions:
 *    - Share your Google Sheet with service account email
 *    - Give "Editor" permissions
 * 
 * 5. Run server:
 *    node backend/src/server.js
 */
