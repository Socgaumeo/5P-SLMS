// frontend/src/components/chat/EntityCard.jsx
import React, { useState } from 'react'
import './EntityCard.css'
import SearchDropdown from './SearchDropdown'

// Simplify service codes for display
const simplifyServiceCode = (code) => {
    if (!code) return ''
    const map = {
        // Road Transport
        'TRUCKING_DOM': 'VẬN TẢI NỘI ĐỊA',
        'BORDER_IMP': 'NHẬP KẨU ĐƯỜNG BỘ',
        // Air Freight
        'AIR_IMP': 'HÀNG KHÔNG NHẬP',
        'AIR_EXP': 'HÀNG KHÔNG XUẤT',
        // Sea Freight
        'SEA_IMP': 'ĐƯỜNG BIỂN NHẬP',
        'SEA_EXP': 'ĐƯỜNG BIỂN XUẤT',
        // Legacy codes (for backward compatibility)
        'TRUCKING_SHORT': 'VẬN TẢI NỘI ĐỊA',
        'TRUCKING_LONG': 'VẬN TẢI NỘI ĐỊA',
        'TRUCKING_CONT': 'VẬN TẢI NỘI ĐỊA',
        // Packing
        'SVC_PACK': 'ĐÓNG GÓI',
        'SVC_FUMI': 'HUN TRÙNG',
        'SVC_VACUUM': 'HÚT CHÂN KHÔNG',
        'SVC_SHRINK': 'MÀNG CO',
        'SVC_LASHING': 'CHẰNG BUỘC',
        'SVC_LASHING_TRUCK': 'CHẰNG BUỘC',
        'SVC_LASHING_CONT': 'CHẰNG BUỘC',
        // Warehouse
        'WHS_STORAGE': 'LƯU KHO',
        'WHS_HANDLE': 'BỐC XẾP',
        // Customs
        'CUS_IMPORT': 'KHAI QUAN NHẬP',
        'CUS_EXPORT': 'KHAI QUAN XUẤT',
    }
    const upper = code.toUpperCase()
    return map[upper] || upper
}

/**
 * EntityCard - Display and edit extracted entities from AI
 *
 * Props:
 * - entities: Object containing extracted data
 * - intent: The detected intent (create_booking, assign_vehicle, etc.)
 * - onConfirm: Callback when user confirms
 * - onCancel: Callback when user cancels
 * - onEdit: Callback when user edits a field
 * - isLoading: Whether action is in progress
 */
const EntityCard = ({
    entities = {},
    intent,
    onConfirm,
    onCancel,
    onEdit,
    isLoading = false
}) => {
    const [editMode, setEditMode] = useState(false)
    const [editedEntities, setEditedEntities] = useState({ ...entities })

    // Field labels for display
    const fieldLabels = {
        customer_code: 'Khách hàng',
        booking_date: 'Ngày booking',
        pickup_date: 'Ngày lấy hàng',
        pickup_time: 'Giờ lấy hàng',
        pickup_address: 'Điểm lấy hàng',
        origin_address: 'Điểm lấy hàng',
        delivery_address: 'Địa chỉ giao',
        dest_address: 'Địa chỉ giao',
        delivery_date: 'Ngày giao',
        delivery_time: 'Giờ giao',
        vehicle_type: 'Loại xe',
        package_quantity: 'Tổng số lượng',
        package_quantity_raw: 'Số lượng chi tiết',
        package_display: 'Số lượng',
        package_unit: 'Đơn vị',
        cargo_type: 'Loại hàng',
        goods_name: 'Tên hàng',
        invoice_number: 'Số Invoice',
        invoices: 'Invoice',
        recipient_name: 'Người nhận',
        recipient_phone: 'SĐT người nhận',
        delivery_company: 'Công ty nhận hàng',
        notes: 'Ghi chú',
        vendor_id: 'Nhà vận chuyển',
        driver_name: 'Tài xế',
        license_plate: 'Biển số xe',
    }

    // Get intent display name
    const getIntentLabel = (intent) => {
        const labels = {
            create_booking: '📦 Tạo Booking',
            assign_vehicle: '🚛 Gán Xe',
            update_job: '✏️ Cập nhật Job',
            query_info: '🔍 Tra cứu',
            general_chat: '💬 Chat',
        }
        return labels[intent] || intent
    }

    const handleFieldChange = (key, value) => {
        setEditedEntities(prev => ({ ...prev, [key]: value }))
    }

    const handleSave = () => {
        if (onEdit) {
            onEdit(editedEntities)
        }
        setEditMode(false)
    }

    const handleConfirm = () => {
        if (onConfirm) {
            onConfirm(editMode ? editedEntities : entities)
        }
    }

    // Format value for display (handle arrays and service types)
    const formatValue = (key, value) => {
        // Simplify service types
        if (key === 'service_type' || key === 'services') {
            if (Array.isArray(value)) {
                return value.map(v => simplifyServiceCode(v)).join(', ')
            }
            return simplifyServiceCode(String(value))
        }
        if (Array.isArray(value)) {
            return value.join(', ')
        }
        return String(value)
    }

    // Get all entity keys (preserve fields even if cleared)
    const allKeys = Object.keys(entities)

    // Skip duplicate fields - services is redundant if service_type exists
    const skipFields = entities.service_type ? ['services'] : []

    // In edit mode, show all fields. In view mode, filter empty values.
    const displayEntities = editMode
        ? allKeys.filter(k => !skipFields.includes(k)).map(key => [key, editedEntities[key]])
        : Object.entries(entities).filter(([k, v]) =>
            !skipFields.includes(k) &&
            v !== null && v !== undefined && v !== '' &&
            !(Array.isArray(v) && v.length === 0))

    if (displayEntities.length === 0) {
        return null
    }

    return (
        <div className="entity-card">
            <div className="entity-card-header">
                <span className="entity-intent">{getIntentLabel(intent)}</span>
                {!editMode && (
                    <button
                        className="btn-edit-toggle"
                        onClick={() => setEditMode(true)}
                        title="Chỉnh sửa"
                    >
                        ✏️
                    </button>
                )}
            </div>

            <div className="entity-card-body">
                {displayEntities.map(([key, value]) => (
                    <div key={key} className="entity-field">
                        <label className="entity-label">
                            {fieldLabels[key] || key}
                        </label>
                        {editMode ? (
                            // Use SearchDropdown for customer and vendor fields
                            key === 'customer_code' ? (
                                <SearchDropdown
                                    value={editedEntities[key] || ''}
                                    onChange={(val) => handleFieldChange(key, val)}
                                    type="customer"
                                    placeholder="Tìm khách hàng..."
                                />
                            ) : key === 'vendor_id' || key === 'vendor_code' ? (
                                <SearchDropdown
                                    value={editedEntities[key] || ''}
                                    onChange={(val) => handleFieldChange(key, val)}
                                    type="vendor"
                                    placeholder="Tìm nhà vận chuyển..."
                                />
                            ) : key === 'license_plate' ? (
                                <SearchDropdown
                                    value={editedEntities[key] || ''}
                                    onChange={(val) => handleFieldChange(key, val)}
                                    type="vehicle"
                                    placeholder="Tìm biển số xe..."
                                />
                            ) : (
                                <input
                                    type="text"
                                    className="entity-input"
                                    value={Array.isArray(editedEntities[key]) ? editedEntities[key].join(', ') : (editedEntities[key] || '')}
                                    onChange={(e) => handleFieldChange(key, e.target.value)}
                                />
                            )
                        ) : (
                            <span className="entity-value">{formatValue(key, value)}</span>
                        )}
                    </div>
                ))}
            </div>

            <div className="entity-card-actions">
                {editMode ? (
                    <>
                        <button
                            className="btn-save"
                            onClick={handleSave}
                        >
                            ✓ Lưu
                        </button>
                        <button
                            className="btn-cancel-edit"
                            onClick={() => {
                                setEditedEntities({ ...entities })
                                setEditMode(false)
                            }}
                        >
                            Hủy sửa
                        </button>
                    </>
                ) : (
                    <>
                        <button
                            className="btn-confirm"
                            onClick={handleConfirm}
                            disabled={isLoading}
                        >
                            {isLoading ? '⏳' : '✓'} Xác nhận thực hiện
                        </button>
                        <button
                            className="btn-cancel"
                            onClick={onCancel}
                            disabled={isLoading}
                        >
                            ✕ Hủy bỏ
                        </button>
                    </>
                )}
            </div>

            {!editMode && (
                <p className="entity-card-hint">
                    Bạn có thể gõ nội dung để sửa lại thông tin trên
                </p>
            )}
        </div>
    )
}

export default EntityCard
