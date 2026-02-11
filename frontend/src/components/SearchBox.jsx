/**
 * SearchBox Component
 * Header search with dropdown results for jobs
 * Enhanced: Shows customer/vendor jobs with export option
 */

import { useState, useRef, useEffect } from 'react';
import './SearchBox.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Get current month in YYYY-MM format
const getCurrentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
};

export default function SearchBox({ onJobSelect }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [entityMatch, setEntityMatch] = useState(null); // Customer/vendor match
  const [entityJobs, setEntityJobs] = useState([]); // All jobs for entity
  const [showEntityPanel, setShowEntityPanel] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  // Date filter state
  const [filterMonth, setFilterMonth] = useState(getCurrentMonth());
  // Custom template info
  const [templateInfo, setTemplateInfo] = useState(null);
  const inputRef = useRef(null);
  const containerRef = useRef(null);
  const debounceRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard shortcut: Ctrl/Cmd + K to focus search
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
        inputRef.current?.blur();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const searchJobs = async (searchQuery) => {
    if (searchQuery.length < 2) {
      setResults([]);
      setEntityMatch(null);
      return;
    }

    setLoading(true);
    try {
      // Search jobs
      const response = await fetch(
        `${API_URL}/api/search/jobs?q=${encodeURIComponent(searchQuery)}&limit=10`
      );
      const data = await response.json();
      setResults(data.results || []);

      // Also check for customer/vendor match
      const [custRes, vendorRes] = await Promise.all([
        fetch(`${API_URL}/api/search/customers?q=${encodeURIComponent(searchQuery)}&limit=1`),
        fetch(`${API_URL}/api/search/vendors?q=${encodeURIComponent(searchQuery)}&limit=1`)
      ]);

      const custData = await custRes.json();
      const vendorData = await vendorRes.json();

      // Prefer exact code match
      const custMatch = custData.results?.find(c =>
        c.code?.toLowerCase() === searchQuery.toLowerCase()
      ) || custData.results?.[0];

      const vendorMatch = vendorData.results?.find(v =>
        v.code?.toLowerCase() === searchQuery.toLowerCase()
      ) || vendorData.results?.[0];

      if (custMatch) {
        setEntityMatch({ type: 'customer', ...custMatch });
      } else if (vendorMatch) {
        setEntityMatch({ type: 'vendor', ...vendorMatch });
      } else {
        setEntityMatch(null);
      }
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
      setEntityMatch(null);
    } finally {
      setLoading(false);
    }
  };

  // Check if customer has custom export template
  const checkCustomTemplate = async (customerCode) => {
    try {
      const res = await fetch(`${API_URL}/api/exports/templates/${customerCode}`);
      const data = await res.json();
      setTemplateInfo(data.has_template ? data : null);
    } catch (error) {
      console.error('Check template failed:', error);
      setTemplateInfo(null);
    }
  };

  // Load all jobs for entity with date filter
  const loadEntityJobs = async (entity, month = filterMonth) => {
    setLoading(true);
    try {
      let url = `${API_URL}/api/search/jobs-by-entity?entity_type=${entity.type}&entity_id=${entity.id}`;
      if (month) url += `&month=${month}`;

      const res = await fetch(url);
      const data = await res.json();
      setEntityJobs(data.results || []);
      setShowEntityPanel(true);

      // Check for custom template if customer
      if (entity.type === 'customer' && entity.code) {
        checkCustomTemplate(entity.code);
      }
    } catch (error) {
      console.error('Load entity jobs failed:', error);
    } finally {
      setLoading(false);
    }
  };

  // Export jobs to Excel - use custom template if available
  const exportEntityJobs = async (useCustomTemplate = false) => {
    if (!entityMatch) return;

    setExporting(true);
    try {
      let url;
      let filename;

      if (useCustomTemplate && templateInfo && entityMatch.type === 'customer') {
        // Use customer-specific template
        url = `${API_URL}/api/exports/customer/${entityMatch.code}?month=${filterMonth}`;
        filename = `${entityMatch.code}_${filterMonth}_${templateInfo.name || 'export'}.xlsx`;
      } else {
        // Use generic export
        url = `${API_URL}/api/jobs/exports/entity?entity_type=${entityMatch.type}&entity_id=${entityMatch.id}`;
        if (filterMonth) url += `&month=${filterMonth}`;
        filename = `${entityMatch.type}_${entityMatch.code}_${filterMonth || 'all'}_export.xlsx`;
      }

      const response = await fetch(url);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Export failed');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Lỗi xuất Excel: ' + error.message);
    } finally {
      setExporting(false);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);

    // Debounce search
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      searchJobs(value);
    }, 300);
  };

  const handleFocus = () => {
    setIsOpen(true);
    if (query.length >= 2) {
      searchJobs(query);
    }
  };

  const handleSelectJob = (job) => {
    setQuery('');
    setResults([]);
    setIsOpen(false);
    if (onJobSelect) {
      onJobSelect(job);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      PENDING: '#f59e0b',
      CONFIRMED: '#3b82f6',
      DISPATCHED: '#8b5cf6',
      IN_TRANSIT: '#06b6d4',
      COMPLETED: '#22c55e',
      CANCELLED: '#ef4444',
    };
    return colors[status] || '#6b7280';
  };

  const getServiceIcon = (serviceType) => {
    if (!serviceType) return '📋';
    if (serviceType.includes('TRUCKING')) return '🚚';
    if (serviceType.includes('WHS') || serviceType.includes('STORAGE')) return '🏭';
    if (serviceType.includes('CUS')) return '🛃';
    if (serviceType.includes('PACK') || serviceType.includes('SVC')) return '📦';
    if (serviceType.includes('LIFT')) return '🏗️';
    return '📋';
  };

  return (
    <div className="search-box-container" ref={containerRef}>
      <div className="search-input-wrapper">
        <span className="search-icon">🔍</span>
        <input
          ref={inputRef}
          type="text"
          className="search-input"
          placeholder="Tìm job, khách hàng... (Ctrl+K)"
          value={query}
          onChange={handleInputChange}
          onFocus={handleFocus}
        />
        {loading && <span className="search-loading">...</span>}
      </div>

      {isOpen && (query.length >= 2 || results.length > 0) && (
        <div className="search-dropdown">
          {/* Entity match - show option to view all jobs */}
          {entityMatch && (
            <div className="search-entity-match">
              <div className="entity-info">
                <span className="entity-icon">
                  {entityMatch.type === 'customer' ? '🏢' : '🚛'}
                </span>
                <div className="entity-details">
                  <span className="entity-code">{entityMatch.code}</span>
                  <span className="entity-name">{entityMatch.name}</span>
                </div>
              </div>
              <div className="entity-actions">
                <button
                  className="entity-btn view-btn"
                  onClick={() => loadEntityJobs(entityMatch)}
                  disabled={loading}
                >
                  📋 Xem tất cả Jobs
                </button>
                <button
                  className="entity-btn export-btn"
                  onClick={exportEntityJobs}
                  disabled={exporting}
                >
                  {exporting ? '⏳' : '📥'} Xuất Excel
                </button>
              </div>
            </div>
          )}

          {/* Job results */}
          {results.length > 0 ? (
            results.map((job) => (
              <div
                key={job.job_id}
                className="search-result-item"
                onClick={() => handleSelectJob(job)}
              >
                <span className="result-icon">{getServiceIcon(job.service_type)}</span>
                <div className="result-info">
                  <span className="result-job-no">{job.job_no}</span>
                  <span className="result-customer">
                    {job.customer_code} - {job.customer_name}
                  </span>
                </div>
                <span
                  className="result-status"
                  style={{ backgroundColor: getStatusColor(job.status_code) }}
                >
                  {job.status_code}
                </span>
              </div>
            ))
          ) : query.length >= 2 && !loading && !entityMatch ? (
            <div className="search-no-results">Không tìm thấy kết quả</div>
          ) : null}
        </div>
      )}

      {/* Entity jobs panel */}
      {showEntityPanel && entityMatch && (
        <div className="entity-panel-overlay" onClick={() => setShowEntityPanel(false)}>
          <div className="entity-panel" onClick={e => e.stopPropagation()}>
            <div className="entity-panel-header">
              <h3>
                {entityMatch.type === 'customer' ? '🏢' : '🚛'}
                {' '}{entityMatch.code} - {entityMatch.name}
              </h3>
              <button className="close-btn" onClick={() => setShowEntityPanel(false)}>✕</button>
            </div>

            {/* Date filter and export buttons */}
            <div className="entity-panel-toolbar">
              <div className="date-filter">
                <label>Tháng:</label>
                <input
                  type="month"
                  value={filterMonth}
                  onChange={(e) => {
                    setFilterMonth(e.target.value);
                    loadEntityJobs(entityMatch, e.target.value);
                  }}
                  className="month-input"
                />
              </div>
              <div className="export-buttons">
                {/* Custom template export if available */}
                {templateInfo && (
                  <button
                    className="export-btn custom-template"
                    onClick={() => exportEntityJobs(true)}
                    disabled={exporting}
                    title={templateInfo.description}
                  >
                    {exporting ? '⏳' : '📊'} {templateInfo.name ? `Mẫu ${entityMatch.code}` : 'Xuất mẫu riêng'}
                  </button>
                )}
                {/* Generic export */}
                <button
                  className="export-btn"
                  onClick={() => exportEntityJobs(false)}
                  disabled={exporting}
                >
                  {exporting ? '⏳ Đang xuất...' : '📥 Xuất Excel'}
                </button>
              </div>
            </div>

            <div className="entity-panel-stats">
              <span>Tổng: <strong>{entityJobs.length}</strong> jobs trong tháng {filterMonth}</span>
              <span>Doanh thu: <strong>
                {entityJobs.reduce((s, j) => s + (parseFloat(j.total_revenue) || 0), 0).toLocaleString('vi-VN')}đ
              </strong></span>
            </div>
            <div className="entity-panel-body">
              {entityJobs.length > 0 ? (
                <table className="entity-jobs-table">
                  <thead>
                    <tr>
                      <th>Mã Job</th>
                      <th>Ngày</th>
                      <th>Trạng thái</th>
                      <th>Doanh thu</th>
                      <th>Chi phí</th>
                      <th>Lợi nhuận</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entityJobs.map(job => (
                      <tr
                        key={job.job_id}
                        onClick={() => {
                          // Open job detail but keep entity panel visible (acts as "back" destination)
                          // User can close entity panel with X button when done
                          if (onJobSelect) {
                            onJobSelect(job);
                          }
                        }}
                        style={{ cursor: 'pointer' }}
                      >
                        <td className="job-no">{job.job_no}</td>
                        <td>{job.etd || job.created_at?.slice(0, 10)}</td>
                        <td>
                          <span
                            className="status-badge"
                            style={{ backgroundColor: getStatusColor(job.status_code) }}
                          >
                            {job.status_code}
                          </span>
                        </td>
                        <td className="number">{(parseFloat(job.total_revenue) || 0).toLocaleString('vi-VN')}</td>
                        <td className="number">{(parseFloat(job.total_cost) || 0).toLocaleString('vi-VN')}</td>
                        <td className="number profit">
                          {(parseFloat(job.profit) || 0).toLocaleString('vi-VN')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="no-jobs">Không có job nào</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
