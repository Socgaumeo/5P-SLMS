// frontend/src/components/chat/SearchDropdown.jsx
import React, { useState, useEffect, useRef } from 'react'
import './SearchDropdown.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * SearchDropdown - Searchable dropdown for customers/vendors
 * 
 * Props:
 * - value: Current selected value
 * - onChange: Callback when value changes
 * - type: 'customer' | 'vendor' | 'vehicle'
 * - placeholder: Input placeholder
 * - disabled: Whether input is disabled
 */
const SearchDropdown = ({
    value = '',
    onChange,
    type = 'customer',
    placeholder = 'Tìm kiếm...',
    disabled = false
}) => {
    const [searchTerm, setSearchTerm] = useState(value)
    const [results, setResults] = useState([])
    const [isOpen, setIsOpen] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const wrapperRef = useRef(null)
    const debounceRef = useRef(null)

    // Sync with external value
    useEffect(() => {
        setSearchTerm(value)
    }, [value])

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
                setIsOpen(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    // Search API based on type
    const searchAPI = async (term) => {
        if (!term || term.length < 1) {
            setResults([])
            return
        }

        setIsLoading(true)
        try {
            let endpoint = ''
            switch (type) {
                case 'customer':
                    endpoint = `/api/search/customers?q=${encodeURIComponent(term)}`
                    break
                case 'vendor':
                    endpoint = `/api/search/vendors?q=${encodeURIComponent(term)}`
                    break
                case 'vehicle':
                    endpoint = `/api/search/vehicles?q=${encodeURIComponent(term)}`
                    break
                default:
                    endpoint = `/api/search/customers?q=${encodeURIComponent(term)}`
            }

            const res = await fetch(`${API_URL}${endpoint}`)
            if (res.ok) {
                const data = await res.json()
                setResults(data.results || data || [])
            }
        } catch (e) {
            console.error('Search failed:', e)
            setResults([])
        } finally {
            setIsLoading(false)
        }
    }

    // Debounced search
    const handleInputChange = (e) => {
        const term = e.target.value
        setSearchTerm(term)
        setIsOpen(true)

        // Debounce API calls
        if (debounceRef.current) {
            clearTimeout(debounceRef.current)
        }
        debounceRef.current = setTimeout(() => {
            searchAPI(term)
        }, 300)
    }

    // Handle selection
    const handleSelect = (item) => {
        const displayValue = item.code || item.name || item.id
        setSearchTerm(displayValue)
        setIsOpen(false)
        if (onChange) {
            onChange(displayValue, item)
        }
    }

    // Get display text for result item
    const getDisplayText = (item) => {
        if (type === 'customer') {
            return `${item.code || item.customer_code} - ${item.name || item.customer_name || ''}`
        } else if (type === 'vendor') {
            return `${item.code || item.vendor_code} - ${item.name || item.vendor_name || ''}`
        } else if (type === 'vehicle') {
            return `${item.license_plate || item.plate} - ${item.driver_name || ''}`
        }
        return item.name || item.code || String(item)
    }

    return (
        <div className="search-dropdown" ref={wrapperRef}>
            <input
                type="text"
                className="search-dropdown-input"
                value={searchTerm}
                onChange={handleInputChange}
                onFocus={() => {
                    setIsOpen(true)
                    if (searchTerm) searchAPI(searchTerm)
                }}
                placeholder={placeholder}
                disabled={disabled}
            />

            {isLoading && (
                <span className="search-loading">⏳</span>
            )}

            {isOpen && results.length > 0 && (
                <div className="search-dropdown-results">
                    {results.map((item, idx) => (
                        <div
                            key={item.id || item.code || idx}
                            className="search-dropdown-item"
                            onClick={() => handleSelect(item)}
                        >
                            {getDisplayText(item)}
                        </div>
                    ))}
                </div>
            )}

            {isOpen && searchTerm && results.length === 0 && !isLoading && (
                <div className="search-dropdown-results">
                    <div className="search-dropdown-empty">
                        Không tìm thấy kết quả
                    </div>
                </div>
            )}
        </div>
    )
}

export default SearchDropdown
