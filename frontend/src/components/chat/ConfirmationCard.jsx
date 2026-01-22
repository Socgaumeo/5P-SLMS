// frontend/src/components/chat/ConfirmationCard.jsx
import React from 'react'

const ConfirmationCard = ({ data, intent, onConfirm, onCancel, onChange }) => {
    const getLabel = (key) => {
        const labels = {
            customer_code: 'Khách hàng',
            date: 'Ngày',
            time: 'Giờ',
            destination: 'Giao tại',
            origin: 'Lấy tại',
            vehicle_type: 'Loại xe',
            cargo: 'Hàng hóa',
            quantity: 'Số lượng',
            notes: 'Ghi chú',
            job_id: 'Mã Job',
            license_plate: 'Biển số',
            driver_name: 'Tài xế'
        }
        return labels[key] || key
    }

    const formatValue = (key, value) => {
        if (!value) return '-'
        return value
    }

    // Filter out internal keys
    const displayEntries = Object.entries(data).filter(([key]) =>
        !['confidence', 'intent', 'status', 'matched'].includes(key)
    )

    return (
        <div className="confirmation-card">
            <div className="confirmation-header">
                <div className="confirmation-icon">📋</div>
                <div className="confirmation-title">
                    {intent === 'create_booking' ? 'Xác nhận Booking' :
                        intent === 'assign_vehicle' ? 'Xác nhận Gán xe' : 'Xác nhận thông tin'}
                </div>
            </div>

            <div className="confirmation-body">
                {displayEntries.map(([key, value]) => (
                    <div key={key} className="conf-row">
                        <span className="conf-label">{getLabel(key)}:</span>
                        <span className="conf-value">{formatValue(key, value)}</span>
                    </div>
                ))}
            </div>

            <div className="confirmation-actions">
                <button className="btn-cancel" onClick={onCancel}>
                    ✕ Hủy bỏ
                </button>
                <button className="btn-confirm" onClick={onConfirm}>
                    ✓ Xác nhận thực hiện
                </button>
            </div>

            <div className="confirmation-footer">
                <small>Bạn có thể gõ nội dung để sửa lại thông tin trên</small>
            </div>

            <style jsx>{`
        .confirmation-card {
          background: #fff;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          overflow: hidden;
          margin: 8px 0;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          max-width: 100%;
        }
        .confirmation-header {
          background: #3b82f6;
          color: white;
          padding: 8px 12px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .confirmation-title {
          font-weight: 600;
          font-size: 0.95rem;
        }
        .confirmation-body {
          padding: 12px;
        }
        .conf-row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 6px;
          font-size: 0.9rem;
          border-bottom: 1px dashed #f1f5f9;
          padding-bottom: 4px;
        }
        .conf-row:last-child {
          border-bottom: none;
        }
        .conf-label {
          color: #64748b;
          font-weight: 500;
        }
        .conf-value {
          color: #1e293b;
          font-weight: 600;
          text-align: right;
        }
        .confirmation-actions {
          padding: 8px 12px;
          background: #f8fafc;
          display: flex;
          gap: 8px;
          justify-content: flex-end;
          border-top: 1px solid #e2e8f0;
        }
        .btn-confirm {
          background: #10b981;
          color: white;
          border: none;
          padding: 6px 12px;
          border-radius: 6px;
          font-weight: 500;
          cursor: pointer;
          font-size: 0.9rem;
        }
        .btn-cancel {
          background: #ef4444;
          color: white;
          border: none;
          padding: 6px 12px;
          border-radius: 6px;
          font-weight: 500;
          cursor: pointer;
          font-size: 0.9rem;
        }
        .confirmation-footer {
          padding: 4px 12px 8px;
          background: #f8fafc;
          color: #94a3b8;
          font-size: 0.8rem;
          text-align: center;
        }
      `}</style>
        </div>
    )
}

export default ConfirmationCard
