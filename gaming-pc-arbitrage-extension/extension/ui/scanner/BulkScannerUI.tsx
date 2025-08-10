/**
 * Bulk Scanner UI Component
 * Interface for batch scanning multiple marketplace URLs
 */

import React, { useState, useEffect, useRef } from 'react';
import { bulkScanner } from '@arbitrage/core';
import type { 
  ScanJob, 
  ScanResult, 
  ScanOptions, 
  ScanProgress,
  ScanFilters 
} from '@arbitrage/core';

export const BulkScannerUI: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'new' | 'jobs'>('new');
  const [jobs, setJobs] = useState<ScanJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<ScanJob | null>(null);
  const [urls, setUrls] = useState<string[]>([]);
  const [urlInput, setUrlInput] = useState('');
  const [scanOptions, setScanOptions] = useState<Partial<ScanOptions>>({
    parallel: true,
    maxConcurrent: 3,
    timeout: 30000,
    retryFailed: true,
    analyzeComponents: true,
    calculateROI: true,
    checkRisks: true
  });
  const [filters, setFilters] = useState<ScanFilters>({});
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadJobs = () => {
    const allJobs = bulkScanner.getAllJobs();
    setJobs(allJobs);
  };

  const handleAddUrls = async () => {
    const extractedUrls = await bulkScanner.extractUrlsFromText(urlInput);
    if (extractedUrls.length > 0) {
      setUrls([...urls, ...extractedUrls]);
      setUrlInput('');
    }
  };

  const handleFileImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const importedUrls = await bulkScanner.importUrlsFromFile(file);
      setUrls([...urls, ...importedUrls]);
    } catch (error) {
      console.error('Failed to import URLs:', error);
    }
  };

  const handleStartScan = async () => {
    if (urls.length === 0) {
      alert('Please add some URLs to scan');
      return;
    }

    try {
      const job = await bulkScanner.createScanJob(urls, {
        ...scanOptions,
        filters: Object.keys(filters).length > 0 ? filters : undefined
      });

      setUrls([]);
      setActiveTab('jobs');
      
      // Start the scan with progress tracking
      bulkScanner.startScan(job.id, (progress) => {
        setProgress(progress);
      });

      loadJobs();
    } catch (error) {
      console.error('Failed to start scan:', error);
    }
  };

  const handleCancelScan = async (jobId: string) => {
    await bulkScanner.cancelScan(jobId);
    setProgress(null);
    loadJobs();
  };

  const handleDeleteJob = async (jobId: string) => {
    if (confirm('Are you sure you want to delete this scan job?')) {
      await bulkScanner.deleteJob(jobId);
      if (selectedJob?.id === jobId) {
        setSelectedJob(null);
      }
      loadJobs();
    }
  };

  const handleExportResults = (jobId: string, format: 'json' | 'csv') => {
    try {
      const data = bulkScanner.exportResults(jobId, format);
      const blob = new Blob([data], { 
        type: format === 'json' ? 'application/json' : 'text/csv' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scan_results_${jobId}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export results:', error);
    }
  };

  const removeUrl = (index: number) => {
    setUrls(urls.filter((_, i) => i !== index));
  };

  const getSummary = (job: ScanJob) => {
    return bulkScanner.getScanSummary(job.id);
  };

  const formatDuration = (start?: Date, end?: Date) => {
    if (!start) return '';
    const endTime = end || new Date();
    const duration = endTime.getTime() - start.getTime();
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  return (
    <div className="bulk-scanner">
      <div className="scanner-header">
        <h2>Bulk URL Scanner</h2>
        <p>Batch process multiple marketplace listings to find the best deals</p>
      </div>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'new' ? 'active' : ''}`}
          onClick={() => setActiveTab('new')}
        >
          New Scan
        </button>
        <button 
          className={`tab ${activeTab === 'jobs' ? 'active' : ''}`}
          onClick={() => setActiveTab('jobs')}
        >
          Scan Jobs ({jobs.length})
        </button>
      </div>

      {activeTab === 'new' && (
        <div className="new-scan">
          {/* URL Input Section */}
          <div className="url-input-section">
            <h3>Add URLs to Scan</h3>
            <div className="input-methods">
              <div className="manual-input">
                <textarea
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="Paste marketplace URLs here (one per line)..."
                  rows={5}
                />
                <button onClick={handleAddUrls} className="add-btn">
                  Add URLs
                </button>
              </div>
              
              <div className="file-import">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.json,.csv"
                  onChange={handleFileImport}
                  style={{ display: 'none' }}
                />
                <button 
                  className="import-btn"
                  onClick={() => fileInputRef.current?.click()}
                >
                  📁 Import from File
                </button>
              </div>
            </div>
          </div>

          {/* URL List */}
          {urls.length > 0 && (
            <div className="url-list">
              <h4>URLs to Scan ({urls.length})</h4>
              <div className="url-items">
                {urls.map((url, index) => (
                  <div key={index} className="url-item">
                    <span className="url-text">{url}</span>
                    <button 
                      className="remove-btn"
                      onClick={() => removeUrl(index)}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scan Options */}
          <div className="scan-options">
            <h3>Scan Options</h3>
            <div className="options-grid">
              <label className="option">
                <input
                  type="checkbox"
                  checked={scanOptions.parallel}
                  onChange={(e) => setScanOptions({
                    ...scanOptions,
                    parallel: e.target.checked
                  })}
                />
                <span>Parallel Processing</span>
              </label>

              {scanOptions.parallel && (
                <label className="option">
                  <span>Max Concurrent:</span>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={scanOptions.maxConcurrent}
                    onChange={(e) => setScanOptions({
                      ...scanOptions,
                      maxConcurrent: parseInt(e.target.value)
                    })}
                  />
                </label>
              )}

              <label className="option">
                <input
                  type="checkbox"
                  checked={scanOptions.analyzeComponents}
                  onChange={(e) => setScanOptions({
                    ...scanOptions,
                    analyzeComponents: e.target.checked
                  })}
                />
                <span>Analyze Components</span>
              </label>

              <label className="option">
                <input
                  type="checkbox"
                  checked={scanOptions.calculateROI}
                  onChange={(e) => setScanOptions({
                    ...scanOptions,
                    calculateROI: e.target.checked
                  })}
                />
                <span>Calculate ROI</span>
              </label>

              <label className="option">
                <input
                  type="checkbox"
                  checked={scanOptions.checkRisks}
                  onChange={(e) => setScanOptions({
                    ...scanOptions,
                    checkRisks: e.target.checked
                  })}
                />
                <span>Check Risks</span>
              </label>

              <label className="option">
                <input
                  type="checkbox"
                  checked={scanOptions.retryFailed}
                  onChange={(e) => setScanOptions({
                    ...scanOptions,
                    retryFailed: e.target.checked
                  })}
                />
                <span>Retry Failed URLs</span>
              </label>
            </div>
          </div>

          {/* Filters */}
          <div className="filters-section">
            <button 
              className="toggle-filters"
              onClick={() => setShowFilters(!showFilters)}
            >
              {showFilters ? '▼' : '▶'} Filters
            </button>

            {showFilters && (
              <div className="filters-grid">
                <label>
                  <span>Min Price:</span>
                  <input
                    type="number"
                    value={filters.minPrice || ''}
                    onChange={(e) => setFilters({
                      ...filters,
                      minPrice: e.target.value ? parseInt(e.target.value) : undefined
                    })}
                  />
                </label>

                <label>
                  <span>Max Price:</span>
                  <input
                    type="number"
                    value={filters.maxPrice || ''}
                    onChange={(e) => setFilters({
                      ...filters,
                      maxPrice: e.target.value ? parseInt(e.target.value) : undefined
                    })}
                  />
                </label>

                <label>
                  <input
                    type="checkbox"
                    checked={filters.mustHaveGPU || false}
                    onChange={(e) => setFilters({
                      ...filters,
                      mustHaveGPU: e.target.checked
                    })}
                  />
                  <span>Must Have GPU</span>
                </label>

                <label>
                  <span>Min ROI %:</span>
                  <input
                    type="number"
                    value={filters.minROI || ''}
                    onChange={(e) => setFilters({
                      ...filters,
                      minROI: e.target.value ? parseInt(e.target.value) : undefined
                    })}
                  />
                </label>
              </div>
            )}
          </div>

          {/* Start Button */}
          <div className="scan-actions">
            <button 
              className="start-scan-btn"
              onClick={handleStartScan}
              disabled={urls.length === 0}
            >
              Start Scanning {urls.length} URLs
            </button>
          </div>
        </div>
      )}

      {activeTab === 'jobs' && (
        <div className="scan-jobs">
          {jobs.length === 0 ? (
            <div className="empty-state">
              <p>No scan jobs yet</p>
              <button onClick={() => setActiveTab('new')}>
                Create Your First Scan
              </button>
            </div>
          ) : (
            <div className="jobs-list">
              {jobs.map(job => {
                const summary = getSummary(job);
                const isRunning = job.status === 'running';
                const isCurrentProgress = progress?.jobId === job.id;

                return (
                  <div key={job.id} className={`job-card ${job.status}`}>
                    <div className="job-header">
                      <div className="job-info">
                        <h4>Scan #{job.id.split('_')[1]}</h4>
                        <span className={`status-badge ${job.status}`}>
                          {job.status}
                        </span>
                      </div>
                      <div className="job-meta">
                        <span>{new Date(job.createdAt).toLocaleString()}</span>
                        {job.startedAt && (
                          <span>Duration: {formatDuration(job.startedAt, job.completedAt)}</span>
                        )}
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="progress-section">
                      <div className="progress-bar">
                        <div 
                          className="progress-fill"
                          style={{ 
                            width: `${(job.progress.processed / job.progress.total) * 100}%` 
                          }}
                        />
                      </div>
                      <div className="progress-stats">
                        <span>{job.progress.processed}/{job.progress.total} processed</span>
                        <span className="success">{job.progress.successful} successful</span>
                        <span className="failed">{job.progress.failed} failed</span>
                      </div>
                      {isCurrentProgress && progress && (
                        <div className="current-url">
                          Processing: {progress.currentUrl}
                        </div>
                      )}
                    </div>

                    {/* Summary */}
                    {summary && job.status === 'completed' && (
                      <div className="job-summary">
                        <div className="summary-stats">
                          <div className="stat">
                            <span className="label">Total Deals</span>
                            <span className="value">{summary.totalDeals}</span>
                          </div>
                          <div className="stat">
                            <span className="label">Excellent</span>
                            <span className="value excellent">{summary.excellentDeals}</span>
                          </div>
                          <div className="stat">
                            <span className="label">Good</span>
                            <span className="value good">{summary.goodDeals}</span>
                          </div>
                          <div className="stat">
                            <span className="label">Avg ROI</span>
                            <span className="value">${Math.round(summary.avgROI)}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="job-actions">
                      {isRunning ? (
                        <button 
                          className="cancel-btn"
                          onClick={() => handleCancelScan(job.id)}
                        >
                          Cancel Scan
                        </button>
                      ) : (
                        <>
                          <button 
                            className="view-btn"
                            onClick={() => setSelectedJob(job)}
                          >
                            View Results
                          </button>
                          <button 
                            className="export-btn"
                            onClick={() => handleExportResults(job.id, 'csv')}
                          >
                            Export CSV
                          </button>
                          <button 
                            className="export-btn"
                            onClick={() => handleExportResults(job.id, 'json')}
                          >
                            Export JSON
                          </button>
                          <button 
                            className="delete-btn"
                            onClick={() => handleDeleteJob(job.id)}
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Results Modal */}
      {selectedJob && (
        <div className="modal-overlay" onClick={() => setSelectedJob(null)}>
          <div className="results-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Scan Results</h3>
              <button 
                className="close-btn"
                onClick={() => setSelectedJob(null)}
              >
                ×
              </button>
            </div>

            <div className="results-content">
              {selectedJob.results
                .filter(r => r.status === 'success' && r.analysis)
                .sort((a, b) => (b.analysis?.roi || 0) - (a.analysis?.roi || 0))
                .map((result, index) => (
                  <div key={index} className={`result-card ${result.analysis?.dealQuality}`}>
                    <div className="result-header">
                      <h4>{result.listing?.title}</h4>
                      <span className={`quality-badge ${result.analysis?.dealQuality}`}>
                        {result.analysis?.dealQuality}
                      </span>
                    </div>
                    
                    <div className="result-details">
                      <div className="detail-row">
                        <span>Price:</span>
                        <strong>${result.listing?.price}</strong>
                      </div>
                      <div className="detail-row">
                        <span>FMV:</span>
                        <strong>${result.analysis?.fmv}</strong>
                      </div>
                      <div className="detail-row">
                        <span>Suggested Offer:</span>
                        <strong>${result.analysis?.suggestedOffer}</strong>
                      </div>
                      <div className="detail-row">
                        <span>ROI:</span>
                        <strong className="roi">
                          ${result.analysis?.roi} ({result.analysis?.roiPercentage.toFixed(1)}%)
                        </strong>
                      </div>
                    </div>

                    {result.analysis?.opportunities && result.analysis.opportunities.length > 0 && (
                      <div className="opportunities">
                        <strong>Opportunities:</strong>
                        <ul>
                          {result.analysis.opportunities.map((opp, i) => (
                            <li key={i}>{opp}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="result-actions">
                      <a 
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="view-listing-btn"
                      >
                        View Listing →
                      </a>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .bulk-scanner {
          padding: 20px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .scanner-header {
          margin-bottom: 30px;
        }

        .scanner-header h2 {
          margin: 0 0 8px 0;
          font-size: 28px;
        }

        .scanner-header p {
          margin: 0;
          color: #666;
        }

        .tabs {
          display: flex;
          gap: 0;
          margin-bottom: 24px;
          border-bottom: 2px solid #e0e0e0;
        }

        .tab {
          background: none;
          border: none;
          padding: 12px 24px;
          font-size: 14px;
          cursor: pointer;
          position: relative;
        }

        .tab.active {
          color: #2196f3;
        }

        .tab.active::after {
          content: '';
          position: absolute;
          bottom: -2px;
          left: 0;
          right: 0;
          height: 2px;
          background: #2196f3;
        }

        .url-input-section {
          background: white;
          padding: 24px;
          border-radius: 8px;
          margin-bottom: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .url-input-section h3 {
          margin: 0 0 16px 0;
          font-size: 18px;
        }

        .input-methods {
          display: flex;
          gap: 20px;
          align-items: flex-start;
        }

        .manual-input {
          flex: 1;
        }

        .manual-input textarea {
          width: 100%;
          padding: 12px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-family: monospace;
          font-size: 13px;
          resize: vertical;
        }

        .add-btn {
          margin-top: 12px;
          background: #2196f3;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 6px;
          cursor: pointer;
        }

        .import-btn {
          background: #4caf50;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 6px;
          cursor: pointer;
        }

        .url-list {
          background: white;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .url-list h4 {
          margin: 0 0 16px 0;
        }

        .url-items {
          max-height: 300px;
          overflow-y: auto;
        }

        .url-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 12px;
          background: #f5f5f5;
          margin-bottom: 8px;
          border-radius: 4px;
        }

        .url-text {
          font-size: 13px;
          font-family: monospace;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          flex: 1;
        }

        .remove-btn {
          background: none;
          border: none;
          font-size: 20px;
          cursor: pointer;
          color: #666;
          padding: 0 8px;
        }

        .remove-btn:hover {
          color: #f44336;
        }

        .scan-options {
          background: white;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .scan-options h3 {
          margin: 0 0 16px 0;
          font-size: 18px;
        }

        .options-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }

        .option {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
        }

        .option input[type="number"] {
          width: 60px;
          padding: 4px 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .filters-section {
          background: white;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .toggle-filters {
          background: none;
          border: none;
          font-size: 16px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .filters-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-top: 16px;
        }

        .filters-grid label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
        }

        .filters-grid input[type="number"] {
          width: 100px;
          padding: 6px 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .scan-actions {
          display: flex;
          justify-content: center;
          padding: 20px;
        }

        .start-scan-btn {
          background: #2196f3;
          color: white;
          border: none;
          padding: 14px 32px;
          border-radius: 8px;
          font-size: 16px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .start-scan-btn:hover:not(:disabled) {
          background: #1976d2;
          transform: translateY(-1px);
        }

        .start-scan-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .empty-state {
          text-align: center;
          padding: 80px 20px;
          color: #666;
        }

        .empty-state p {
          margin-bottom: 20px;
          font-size: 18px;
        }

        .empty-state button {
          background: #2196f3;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
        }

        .jobs-list {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .job-card {
          background: white;
          border-radius: 8px;
          padding: 24px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .job-card.running {
          border: 2px solid #2196f3;
        }

        .job-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 20px;
        }

        .job-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .job-info h4 {
          margin: 0;
          font-size: 18px;
        }

        .status-badge {
          font-size: 12px;
          padding: 4px 12px;
          border-radius: 12px;
          text-transform: uppercase;
        }

        .status-badge.pending {
          background: #e0e0e0;
          color: #666;
        }

        .status-badge.running {
          background: #2196f3;
          color: white;
        }

        .status-badge.completed {
          background: #4caf50;
          color: white;
        }

        .status-badge.failed {
          background: #f44336;
          color: white;
        }

        .status-badge.cancelled {
          background: #ff9800;
          color: white;
        }

        .job-meta {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 4px;
          font-size: 13px;
          color: #666;
        }

        .progress-section {
          margin-bottom: 20px;
        }

        .progress-bar {
          height: 8px;
          background: #e0e0e0;
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 8px;
        }

        .progress-fill {
          height: 100%;
          background: #2196f3;
          transition: width 0.3s ease;
        }

        .progress-stats {
          display: flex;
          gap: 20px;
          font-size: 13px;
        }

        .progress-stats .success {
          color: #4caf50;
        }

        .progress-stats .failed {
          color: #f44336;
        }

        .current-url {
          margin-top: 8px;
          font-size: 12px;
          color: #666;
          font-style: italic;
        }

        .job-summary {
          margin-bottom: 20px;
        }

        .summary-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 16px;
        }

        .stat {
          text-align: center;
          padding: 12px;
          background: #f5f5f5;
          border-radius: 6px;
        }

        .stat .label {
          display: block;
          font-size: 12px;
          color: #666;
          margin-bottom: 4px;
        }

        .stat .value {
          display: block;
          font-size: 20px;
          font-weight: 600;
        }

        .stat .value.excellent {
          color: #4caf50;
        }

        .stat .value.good {
          color: #2196f3;
        }

        .job-actions {
          display: flex;
          gap: 12px;
        }

        .view-btn, .export-btn {
          background: #2196f3;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
        }

        .cancel-btn {
          background: #ff9800;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
        }

        .delete-btn {
          background: #f44336;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .results-modal {
          background: white;
          border-radius: 12px;
          width: 90%;
          max-width: 800px;
          max-height: 80vh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .modal-header {
          padding: 20px;
          border-bottom: 1px solid #e0e0e0;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .modal-header h3 {
          margin: 0;
          font-size: 20px;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
        }

        .close-btn:hover {
          background: #f5f5f5;
        }

        .results-content {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
        }

        .result-card {
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 16px;
        }

        .result-card.excellent {
          border-color: #4caf50;
          background: #f1f8e9;
        }

        .result-card.good {
          border-color: #2196f3;
          background: #e3f2fd;
        }

        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 16px;
        }

        .result-header h4 {
          margin: 0;
          font-size: 16px;
          flex: 1;
        }

        .quality-badge {
          font-size: 12px;
          padding: 4px 12px;
          border-radius: 12px;
          text-transform: uppercase;
        }

        .quality-badge.excellent {
          background: #4caf50;
          color: white;
        }

        .quality-badge.good {
          background: #2196f3;
          color: white;
        }

        .quality-badge.fair {
          background: #ff9800;
          color: white;
        }

        .quality-badge.poor {
          background: #f44336;
          color: white;
        }

        .result-details {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
          margin-bottom: 16px;
        }

        .detail-row {
          display: flex;
          justify-content: space-between;
          font-size: 14px;
        }

        .detail-row .roi {
          color: #4caf50;
        }

        .opportunities {
          background: rgba(0,0,0,0.05);
          padding: 12px;
          border-radius: 6px;
          margin-bottom: 16px;
          font-size: 13px;
        }

        .opportunities ul {
          margin: 8px 0 0 20px;
          padding: 0;
        }

        .result-actions {
          display: flex;
          justify-content: flex-end;
        }

        .view-listing-btn {
          background: #2196f3;
          color: white;
          text-decoration: none;
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 14px;
          display: inline-block;
        }

        .view-listing-btn:hover {
          background: #1976d2;
        }
      `}</style>
    </div>
  );
};