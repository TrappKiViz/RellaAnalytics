import React, { useState, useCallback, useEffect } from 'react';
import './DataUploadWidget.css';

// Simplified API call function - replace with your actual service if needed
const validateUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('/api/v1/data/upload/validate_transactions', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
        // Use error message from backend if available, otherwise provide default
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
    }
    return data; // { validation_status: 'success' or 'error', message: '...', ... }
  } catch (error) {
    console.error("Upload validation failed:", error);
    // Re-throw a user-friendly error message
    throw new Error(`Upload failed: ${error.message}`);
  }
};

const processDataAPI = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    // **IMPORTANT**: Use a new endpoint for processing
    const response = await fetch('/api/v1/data/upload/process_transactions', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
    }
    return data; // { status: 'success', message: '...' }
  } catch (error) {
    console.error("Data processing failed:", error);
    throw new Error(`Processing failed: ${error.message}`);
  }
};

const DataUploadWidget = ({ onProcessSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [validatedFile, setValidatedFile] = useState(null); // Store file reference after validation
  const [uploadStatus, setUploadStatus] = useState(''); // '', 'validating', 'success', 'error'
  const [processStatus, setProcessStatus] = useState(''); // '', 'processing', 'success', 'error'
  const [message, setMessage] = useState('');
  const [processMessage, setProcessMessage] = useState('');

  // Reset validated file if selection changes
  useEffect(() => {
     if(selectedFile) {
         setValidatedFile(null); // Clear validation if file changes
         setUploadStatus('');
         setMessage('');
         setProcessStatus('');
         setProcessMessage('');
     }
  }, [selectedFile]);

  const handleFileChange = (event) => {
    if (event.target.files && event.target.files.length > 0) {
        setSelectedFile(event.target.files[0]);
    } else {
        setSelectedFile(null);
    }
  };

  const handleValidate = async () => {
    if (!selectedFile) {
      setMessage('Please select a file first.');
      setUploadStatus('error');
      setValidatedFile(null);
      return;
    }

    setUploadStatus('validating');
    setMessage('Validating file structure...');
    setProcessStatus('');
    setProcessMessage('');
    setValidatedFile(null); // Clear previous validation

    try {
      const result = await validateUpload(selectedFile);
      setUploadStatus(result.validation_status); 
      setMessage(result.message);
      if (result.validation_status === 'success') {
          setValidatedFile(selectedFile); // Store reference to validated file
      }
    } catch (error) {
      setUploadStatus('error');
      setMessage(error.message); 
    }
  };

  const handleProcess = async () => {
      if (!validatedFile) {
          setProcessMessage('File not validated or validation failed.');
          setProcessStatus('error');
          return;
      }
      
      // Confirmation dialog
      const isConfirmed = window.confirm(
          'WARNING: Processing this file will PERMANENTLY DELETE existing transaction data and replace it with the contents of the uploaded file. Are you absolutely sure you want to proceed?'
      );

      if (!isConfirmed) {
          setProcessMessage('Data processing cancelled by user.');
          setProcessStatus('');
          return;
      }

      setProcessStatus('processing');
      setProcessMessage('Processing file and updating database... This may take a moment.');

      try {
          const result = await processDataAPI(validatedFile);
          setProcessStatus('success');
          setProcessMessage(result.message);
          setValidatedFile(null); // Clear validated file after processing
          setUploadStatus(''); // Reset validation status
          setMessage('');
          if (onProcessSuccess) {
            onProcessSuccess(); // Trigger dashboard refresh
          }
      } catch (error) {
          setProcessStatus('error');
          setProcessMessage(error.message);
      }
  };

  return (
    <div className="data-upload-widget-container">
      <h4>Upload & Process Transaction Data (CSV)</h4>
      {/* Validation Area */}
      <div className="upload-step">
        <h5>Step 1: Validate File Structure</h5>
        <div className="upload-area">
          <input type="file" accept=".csv" onChange={handleFileChange} />
          <button onClick={handleValidate} disabled={!selectedFile || uploadStatus === 'validating'}>
            {uploadStatus === 'validating' ? 'Validating...' : 'Validate File'}
          </button>
        </div>
        {message && (
          <div className={`message-area status-${uploadStatus}`}>
            <p>{message}</p>
          </div>
        )}
      </div>

      {/* Processing Area - Only shown after successful validation */}
      {uploadStatus === 'success' && validatedFile && (
        <div className="upload-step process-step">
          <h5>Step 2: Process Validated Data</h5>
          <p>File <strong>{validatedFile.name}</strong> passed validation.</p>
          <button onClick={handleProcess} disabled={processStatus === 'processing'}>
            {processStatus === 'processing' ? 'Processing...' : 'Process & Replace Data'}
          </button>
          {processMessage && (
            <div className={`message-area status-${processStatus}`}>
              <p>{processMessage}</p>
            </div>
          )}
        </div>
      )}

       <div className="upload-instructions">
        <p>Required columns:</p>
        <code>transaction_time, location_name, item_type, item_identifier, quantity, net_price</code>
      </div>
    </div>
  );
};

export default DataUploadWidget; 