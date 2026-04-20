/**
 * SearchBox Component
 * Header search with dropdown results for jobs
 * Enhanced: Shows customer/vendor jobs with export option
 */

import { useState, useRef, useEffect } from 'react';
import './SearchBox.css';
import { authFetch, API_URL } from '../utils/auth-fetch';

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
  // Date filter state - supports both month and date range
  const [filterMonth, setFilterMonth] = useState(getCurrentMonth());
  const [filterMode, setFilterMode] = useState('month'); // 'month' or 'range'
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  // Custom template info
  const [templateInfo, setTemplateInfo] = useState(null);
  // Multi-select and service type filter
  const [selectedJobIds, setSelectedJobIds] = useState(new Set());
  const [serviceTypeFilter, setServiceTypeFilter] = useState('');
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
        authFetch(`${API_URL}/api/search/customers?q=${encodeURIComponent(searchQuery)}&limit=1`),
        authFetch(`${API_URL}/api/search/vendors?q=${encodeURIComponent(searchQuery)}&limit=1`)
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
      const res = await authFetch(`${API_URL}/api/exports/templates/${customerCode}`);
      const data = await res.json();
      setTemplateInfo(data.has_template ? data : null);
    } catch (error) {
      console.error('Check template failed:', error);
      setTemplateInfo(null);
    }
  };

  // Load all jobs for entity with date + service-type filter.
  // `opts.serviceType` falls back to current `serviceTypeFilter` so dropdown
  // changes can trigger a reload that immediately filters the displayed list.
  const loadEntityJobs = async (entity, opts = {}) => {
    setLoading(true);
    try {
      let url = `${API_URL}/api/search/jobs-by-entity?entity_type=${entity.type}&entity_id=${entity.id}`;
      const mode = opts.mode || filterMode;
      if (mode === 'range') {
        const fd = opts.fromDate || fromDate;
        const td = opts.toDate || toDate;
        if (fd) url += `&from_date=${fd}`;
        if (td) url += `&to_date=${td}`;
      } else {
        const month = opts.month || filterMonth;
        if (month) url += `&month=${month}`;
      }
      const svcType = opts.serviceType !== undefined ? opts.serviceType : serviceTypeFilter;
      if (svcType) url += `&service_type=${svcType}`;

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
  // `templateKey` is optional - used when the customer has multiple templates
  // (e.g. DAINESE) and the user picked a specific Bảng kê variant.
  const exportEntityJobs = async (useCustomTemplate = false, templateKey = null) => {
    if (!entityMatch) return;

    setExporting(true);
    try {
      let url;
      let filename;

      if (useCustomTemplate && templateInfo && entityMatch.type === 'customer') {
        // Use customer-specific template — pass date range / month / service type
        // so the export honors all filters the user has selected in this panel.
        url = `${API_URL}/api/exports/customer/${entityMatch.code}?`;
        const params = [];
        if (filterMode === 'range') {
          if (fromDate) params.push(`start_date=${fromDate}`);
          if (toDate) params.push(`end_date=${toDate}`);
        } else {
          if (filterMonth) params.push(`month=${filterMonth}`);
        }
        if (templateKey) params.push(`template=${templateKey}`);
        if (serviceTypeFilter) params.push(`service_type=${serviceTypeFilter}`);
        url += params.join('&');

        const tplLabel = templateKey || templateInfo.name || 'export';
        const periodTag = filterMode === 'range'
          ? `${fromDate || ''}_${toDate || ''}`
          : (filterMonth || 'all');
        filename = `${entityMatch.code}_${periodTag}_${tplLabel}.xlsx`;
      } else {
        // Use generic export
        url = `${API_URL}/api/jobs/exports/entity?entity_type=${entityMatch.type}&entity_id=${entityMatch.id}`;
        if (filterMode === 'range') {
          if (fromDate) url += `&from_date=${fromDate}`;
          if (toDate) url += `&to_date=${toDate}`;
          filename = `${entityMatch.type}_${entityMatch.code}_${fromDate || ''}_${toDate || ''}_export.xlsx`;
        } else {
          if (filterMonth) url += `&month=${filterMonth}`;
          filename = `${entityMatch.type}_${entityMatch.code}_${filterMonth || 'all'}_export.xlsx`;
        }
        // Multi-select: pass selected job_ids
        if (selectedJobIds.size > 0) {
          url += `&job_ids=${[...selectedJobIds].join(',')}`;
        }
        // Service type filter
        if (serviceTypeFilter) {
          url += `&service_type=${serviceTypeFilter}`;
        }
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
          placeholder="Tìm job, khách hàng, tờ khai, BL, CO, invoice... (Ctrl+K)"
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
                  {/* Show matched document info */}
                  {(job.cd_no || job.bl_awb_no || job.co_no || job.invoice_numbers) && (
                    <span className="result-docs">
                      {job.cd_no && `TK: ${job.cd_no}`}
                      {job.bl_awb_no && `${job.cd_no ? ' • ' : ''}BL: ${job.bl_awb_no}`}
                      {job.co_no && ` • CO: ${job.co_no}`}
                      {job.invoice_numbers && ` • INV: ${job.invoice_numbers}`}
                    </span>
                  )}
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
                {/* Filter mode toggle */}
                <div className="filter-mode-toggle">
                  <button
                    className={`mode-btn ${filterMode === 'month' ? 'active' : ''}`}
                    onClick={() => { setFilterMode('month'); loadEntityJobs(entityMatch, { mode: 'month' }); }}
                  >Tháng</button>
                  <button
                    className={`mode-btn ${filterMode === 'range' ? 'active' : ''}`}
                    onClick={() => { setFilterMode('range'); loadEntityJobs(entityMatch, { mode: 'range' }); }}
                  >Khoảng ngày</button>
                </div>

                {filterMode === 'month' ? (
                  <input
                    type="month"
                    value={filterMonth}
                    onChange={(e) => {
                      setFilterMonth(e.target.value);
                      loadEntityJobs(entityMatch, { mode: 'month', month: e.target.value });
                    }}
                    className="month-input"
                  />
                ) : (
                  <div className="date-range-inputs">
                    <input
                      type="date"
                      value={fromDate}
                      onChange={(e) => {
                        setFromDate(e.target.value);
                        if (toDate) loadEntityJobs(entityMatch, { mode: 'range', fromDate: e.target.value, toDate });
                      }}
                      className="date-input"
                      placeholder="Từ ngày"
                    />
                    <span className="date-separator">→</span>
                    <input
                      type="date"
                      value={toDate}
                      onChange={(e) => {
                        setToDate(e.target.value);
                        if (fromDate) loadEntityJobs(entityMatch, { mode: 'range', fromDate, toDate: e.target.value });
                      }}
                      className="date-input"
                      placeholder="Đến ngày"
                    />
                  </div>
                )}
              </div>
              <div className="export-buttons">
                {/* Service type filter — also reloads list to apply server-side filter */}
                <select
                  className="service-type-filter"
                  value={serviceTypeFilter}
                  onChange={(e) => {
                    const newVal = e.target.value;
                    setServiceTypeFilter(newVal);
                    if (entityMatch) {
                      loadEntityJobs(entityMatch, { serviceType: newVal });
                    }
                  }}
                >
                  <option value="">Tất cả loại DV</option>
                  <option value="TRUCKING_DOM">Trucking nội địa</option>
                  <option value="SEA_IMP">Nhập đường biển</option>
                  <option value="SEA_EXP">Xuất đường biển</option>
                  <option value="SEA_DOM">Biển nội địa</option>
                  <option value="AIR_IMP">Nhập hàng không</option>
                  <option value="AIR_DOM">Air nội địa</option>
                  <option value="BORDER_IMP">Nhập cửa khẩu</option>
                  <option value="BORDER_EXP">Xuất cửa khẩu</option>
                  <option value="CUS_EXPORT">HQ xuất khẩu</option>
                  <option value="CUS_IMPORT">HQ nhập khẩu</option>
                  <option value="CUS_CO">C/O</option>
                  <option value="CUS">Hải quan</option>
                </select>
                {templateInfo && Array.isArray(templateInfo.templates) && templateInfo.templates.length > 0 ? (
                  // Customer has multiple sub-templates (e.g. DAINESE) → render one button per template
                  templateInfo.templates.map((tpl) => (
                    <button
                      key={tpl.key}
                      className="export-btn custom-template"
                      onClick={() => exportEntityJobs(true, tpl.key)}
                      disabled={exporting || tpl.implemented === false}
                      title={tpl.implemented === false
                        ? `${tpl.description} (chưa làm xong)`
                        : tpl.description}
                    >
                      {exporting ? '⏳' : (tpl.icon || '📊')} {tpl.label}
                      {tpl.implemented === false ? ' (WIP)' : ''}
                    </button>
                  ))
                ) : templateInfo && (
                  <button
                    className="export-btn custom-template"
                    onClick={() => exportEntityJobs(true)}
                    disabled={exporting}
                    title={templateInfo.description}
                  >
                    {exporting ? '⏳' : '📊'} {templateInfo.name ? `Mẫu ${entityMatch.code}` : 'Xuất mẫu riêng'}
                  </button>
                )}
                <button
                  className="export-btn"
                  onClick={() => exportEntityJobs(false)}
                  disabled={exporting}
                >
                  {exporting ? '⏳ Đang xuất...' : '📥 Xuất Excel'}
                  {selectedJobIds.size > 0 && ` (${selectedJobIds.size})`}
                </button>
              </div>
            </div>

            <div className="entity-panel-stats">
              <span>Tổng: <strong>{entityJobs.length}</strong> jobs
                {filterMode === 'month' ? ` tháng ${filterMonth}` : fromDate && toDate ? ` từ ${fromDate} → ${toDate}` : ''}
              </span>
              {selectedJobIds.size > 0 && (
                <span style={{ color: '#2563EB' }}>Đã chọn: <strong>{selectedJobIds.size}</strong>
                  <button
                    onClick={() => setSelectedJobIds(new Set())}
                    style={{ marginLeft: 6, cursor: 'pointer', color: '#EF4444', background: 'none', border: 'none', fontSize: 12 }}
                  >Bỏ chọn</button>
                </span>
              )}
              <span>Doanh thu: <strong>
                {entityJobs.reduce((s, j) =>
                  s + (parseFloat(j.net_revenue ?? j.total_revenue) || 0), 0
                ).toLocaleString('vi-VN')}đ
              </strong></span>
              {entityJobs.some(j => (parseFloat(j.reimbursement_total) || 0) > 0) && (
                <span style={{ color: '#F59E0B' }}>Chi hộ: <strong>
                  {entityJobs.reduce((s, j) => s + (parseFloat(j.reimbursement_total) || 0), 0).toLocaleString('vi-VN')}đ
                </strong></span>
              )}
              <span style={{ color: '#EF4444' }}>Chi phí: <strong>
                {entityJobs.reduce((s, j) =>
                  s + (parseFloat(j.net_cost ?? j.total_cost) || 0), 0
                ).toLocaleString('vi-VN')}đ
              </strong></span>
              <span style={{ color: '#059669' }}>Lợi nhuận: <strong>
                {entityJobs.reduce((s, j) => s + (parseFloat(j.profit) || 0), 0).toLocaleString('vi-VN')}đ
              </strong></span>
            </div>
            <div className="entity-panel-body">
              {entityJobs.length > 0 ? (
                <table className="entity-jobs-table">
                  <thead>
                    <tr>
                      <th style={{ width: 36 }}>
                        <input
                          type="checkbox"
                          checked={entityJobs.length > 0 && selectedJobIds.size === entityJobs.length}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedJobIds(new Set(entityJobs.map(j => j.job_id)));
                            } else {
                              setSelectedJobIds(new Set());
                            }
                          }}
                          title="Chọn tất cả"
                        />
                      </th>
                      <th>Mã Job</th>
                      <th>Ngày</th>
                      <th>Trạng thái</th>
                      <th>Doanh thu</th>
                      <th>Chi hộ</th>
                      <th>Chi phí</th>
                      <th>Lợi nhuận</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entityJobs.map(job => {
                      // jobs.total_revenue / total_cost from DB already exclude chi hộ.
                      const netRev = parseFloat(job.net_revenue ?? job.total_revenue) || 0;
                      const netCost = parseFloat(job.net_cost ?? job.total_cost) || 0;
                      const profit = job.profit != null ? parseFloat(job.profit) || 0 : netRev - netCost;
                      const reimb = parseFloat(job.reimbursement_total) || 0;
                      return (
                      <tr
                        key={job.job_id}
                        onClick={() => {
                          if (onJobSelect) {
                            onJobSelect(job);
                          }
                        }}
                        style={{ cursor: 'pointer' }}
                        className={selectedJobIds.has(job.job_id) ? 'selected-row' : ''}
                      >
                        <td onClick={(e) => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={selectedJobIds.has(job.job_id)}
                            onChange={(e) => {
                              const next = new Set(selectedJobIds);
                              if (e.target.checked) {
                                next.add(job.job_id);
                              } else {
                                next.delete(job.job_id);
                              }
                              setSelectedJobIds(next);
                            }}
                          />
                        </td>
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
                        <td className="number">{netRev.toLocaleString('vi-VN')}</td>
                        <td className="number reimb">{reimb > 0 ? reimb.toLocaleString('vi-VN') : '-'}</td>
                        <td className="number cost">{netCost > 0 ? netCost.toLocaleString('vi-VN') : '-'}</td>
                        {/* Profit shown as "—" when cost is missing, since it
                            would equal revenue and falsely imply 100% margin. */}
                        <td className="number profit">
                          {netCost > 0
                            ? profit.toLocaleString('vi-VN')
                            : <span title="Chưa nhập chi phí" style={{ color: '#94a3b8' }}>—</span>}
                        </td>
                      </tr>
                      );
                    })}
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
