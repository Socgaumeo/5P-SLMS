# backend/app/ai/excel/booking_form_parser.py
"""
Specialized parser for MEIKO/DREAMTECH style booking forms.
These forms have a fixed structure with metadata in specific cells.
"""

import re
import logging
from datetime import datetime, date, time
from typing import Dict, Any, List, Optional, Tuple
from openpyxl import load_workbook

logger = logging.getLogger(__name__)


class BookingFormParser:
    """
    Parse structured booking forms like "Phiếu book xe DREAMTECH"
    
    Known form layouts:
    - Row 7: Department (Bộ phận book xe)
    - Row 8: Contact person (Người book xe)  
    - Row 9: Company name & address
    - Row 10: Recipient info
    - Row 13: Headers (Ngày book xe, Thời gian, Invoice, etc.)
    - Row 14+: Data rows
    """
    
    # Known cell mappings for MEIKO/DREAMTECH booking forms
    FORM_MAPPINGS = {
        # Metadata cells (fixed positions)
        'department': [('A7', 'G7'), 'G7'],  # Label at A7, value at G7
        'contact_person': [('A8', 'G8'), 'G8'],
        'company_and_address': [('A9', 'G9'), 'G9'],
        'recipient_info': [('A10', 'G10'), 'G10'],
        
        # Header row indicators
        'header_keywords': ['ngày book', 'invoice', 'thời gian', 'số kiện', 'trọng lượng'],
        
        # Data column mappings (column letters)
        'data_columns': {
            'A': 'stt',
            'B': 'booking_date',
            'C': 'pickup_time',
            'D': 'invoice_number',
            'E': 'available_time',
            'F': 'goods_name',
            'G': 'package_quantity',
            'H': 'weight_kg',
            'I': 'delivery_address',
            'J': 'delivery_time',
            'K': 'return_invoice',
            'L': 'return_goods',
            'M': 'return_quantity',
            'N': 'return_weight',
        }
    }
    
    def __init__(self):
        self.workbook = None
        self.sheet = None
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a booking form Excel file.
        
        Returns:
            Dict containing:
            - metadata: Form-level info (company, contact, etc.)
            - bookings: List of booking entries
            - raw_text: Combined text for AI processing
        """
        try:
            self.workbook = load_workbook(file_path, data_only=True)
            self.sheet = self.workbook.active
            
            result = {
                'metadata': self._extract_metadata(),
                'bookings': self._extract_bookings(),
                'raw_text': '',
                'summary': ''
            }
            
            # Build combined text for AI
            result['raw_text'] = self._build_raw_text(result)
            result['summary'] = self._build_summary(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing booking form: {e}")
            import traceback
            traceback.print_exc()
            return {
                'metadata': {},
                'bookings': [],
                'raw_text': f"Error parsing file: {str(e)}",
                'summary': 'Parse error'
            }
    
    def _get_cell_value(self, coord: str) -> Any:
        """Get cell value, handling merged cells"""
        try:
            cell = self.sheet[coord]
            return cell.value
        except:
            return None
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract form-level metadata"""
        metadata = {}
        
        # Department
        dept = self._get_cell_value('G7')
        if dept:
            metadata['department'] = str(dept).strip()
        
        # Contact person
        contact = self._get_cell_value('G8')
        if contact:
            metadata['contact_person'] = str(contact).strip()
            # Try to extract phone
            phone_match = re.search(r'(\d{10,11})', str(contact))
            if phone_match:
                metadata['contact_phone'] = phone_match.group(1)
        
        # Company and address in G9 - This is the DELIVERY destination (customer's customer)
        # MEIKO is the one booking trucks (our customer)
        company_addr = self._get_cell_value('G9')
        if company_addr:
            lines = str(company_addr).split('\n')
            if lines:
                metadata['delivery_company'] = lines[0].strip()  # e.g., "DREAMTECH", "HOSIDEN"
                if len(lines) > 1:
                    # Parse addresses like "Xưởng 1: Số 2 đường..." or full address
                    delivery_addresses = {}
                    full_address_parts = []
                    for line in lines[1:]:
                        line = line.strip()
                        if line:
                            full_address_parts.append(line)
                            # Check if it's like "Xưởng 1: address"
                            if ':' in line:
                                parts = line.split(':', 1)
                                key = parts[0].strip()
                                addr = parts[1].strip() if len(parts) > 1 else ""
                                delivery_addresses[key] = addr
                            else:
                                delivery_addresses[f"Địa chỉ {len(delivery_addresses)+1}"] = line
                    metadata['delivery_addresses_map'] = delivery_addresses
                    # Full list for reference
                    metadata['delivery_addresses'] = [l.strip() for l in lines[1:] if l.strip()]
                    # Single combined address string for export
                    metadata['delivery_full_address'] = ', '.join(full_address_parts)
                else:
                    metadata['delivery_full_address'] = ''
        
        # Recipient info
        recipient = self._get_cell_value('G10')
        if recipient:
            metadata['recipient_info'] = str(recipient).strip()
        
        # The customer booking is MEIKO (the form creator) 
        metadata['customer_code'] = 'MEIKO'  # Fixed - they are our customer
        metadata['pickup_company'] = 'MEIKO'  # Pickup FROM MEIKO
        metadata['pickup_address'] = 'Kho Meiko'  # Pickup from MEIKO warehouse
        metadata['pickup_full_address'] = 'Kho Meiko - Lô CN9, KCN Thạch Thất - Quốc Oai, Hà Nội'
        
        return metadata
    
    def _extract_bookings(self) -> List[Dict[str, Any]]:
        """Extract booking data rows"""
        bookings = []
        
        # Find data rows (usually starting at row 14)
        # Look for rows where column A has a number (STT)
        for row_num in range(14, min(30, self.sheet.max_row + 1)):
            stt = self._get_cell_value(f'A{row_num}')
            
            # Check if this is a data row (STT is a number)
            if stt and isinstance(stt, (int, float)):
                booking = self._extract_booking_row(row_num)
                if booking:
                    bookings.append(booking)
        
        return bookings
    
    def _extract_booking_row(self, row_num: int) -> Optional[Dict[str, Any]]:
        """Extract a single booking row"""
        booking = {}
        
        # Booking date (B)
        booking_date = self._get_cell_value(f'B{row_num}')
        if booking_date:
            if isinstance(booking_date, datetime):
                booking['booking_date'] = booking_date.strftime('%d/%m/%Y')
                booking['pickup_date'] = booking_date.strftime('%d/%m/%Y')
            elif isinstance(booking_date, date):
                booking['booking_date'] = booking_date.strftime('%d/%m/%Y')
                booking['pickup_date'] = booking_date.strftime('%d/%m/%Y')
            else:
                booking['booking_date'] = str(booking_date)
        
        # Pickup time (C)
        pickup_time = self._get_cell_value(f'C{row_num}')
        if pickup_time:
            if isinstance(pickup_time, time):
                booking['pickup_time'] = pickup_time.strftime('%H:%M')
            elif isinstance(pickup_time, datetime):
                booking['pickup_time'] = pickup_time.strftime('%H:%M')
            else:
                booking['pickup_time'] = str(pickup_time)
        
        # Invoice number (D)
        invoice = self._get_cell_value(f'D{row_num}')
        if invoice:
            # Handle multi-line invoices
            booking['invoice_number'] = str(invoice).strip().replace('\n', ', ')
        
        # Available time at warehouse (E)
        avail_time = self._get_cell_value(f'E{row_num}')
        if avail_time:
            booking['available_time'] = str(avail_time)
        
        # Goods name (F)
        goods = self._get_cell_value(f'F{row_num}')
        if goods:
            booking['goods_name'] = str(goods).strip()
        
        # Package quantity (G) - may contain "1 pallet 3thùng" format
        pkg_qty = self._get_cell_value(f'G{row_num}')
        if pkg_qty:
            qty_str = str(pkg_qty).strip()
            booking['package_quantity_raw'] = qty_str
            
            # Parse and preserve unit breakdown
            unit_pattern = r'(\d+)\s*(pallet|thùng|kiện|khay|túi|hộp)?'
            matches = re.findall(unit_pattern, qty_str.lower())
            
            # Build detailed breakdown
            unit_breakdown = []
            total_qty = 0
            for num, unit in matches:
                if num:
                    qty = int(num)
                    total_qty += qty
                    if unit:
                        unit_breakdown.append(f"{qty} {unit}")
                    else:
                        unit_breakdown.append(str(qty))
            
            if total_qty > 0:
                booking['package_quantity'] = total_qty
            
            # Keep the breakdown for display
            if unit_breakdown:
                booking['package_breakdown'] = unit_breakdown
            
            # Set display string preserving both units
            booking['package_display'] = qty_str
        
        # Weight (H)
        weight = self._get_cell_value(f'H{row_num}')
        if weight:
            booking['weight_kg'] = weight
        
        # Delivery location/notes (I)
        delivery = self._get_cell_value(f'I{row_num}')
        if delivery:
            booking['delivery_notes'] = str(delivery).strip()
            # Mark as delivery address if it looks like one
            if any(kw in str(delivery).lower() for kw in ['xưởng', 'kho', 'cổng', 'địa chỉ']):
                booking['delivery_address'] = str(delivery).strip()
        
        # Delivery time (J)
        delivery_time = self._get_cell_value(f'J{row_num}')
        if delivery_time:
            if isinstance(delivery_time, (time, datetime)):
                booking['delivery_time'] = delivery_time.strftime('%H:%M') if hasattr(delivery_time, 'strftime') else str(delivery_time)
            else:
                booking['delivery_time'] = str(delivery_time)
        
        return booking if booking else None
    
    def _build_raw_text(self, result: Dict) -> str:
        """Build combined text for AI processing"""
        lines = []
        
        meta = result.get('metadata', {})
        
        if meta.get('company_name'):
            lines.append(f"Khách hàng: {meta['company_name']}")
        
        if meta.get('contact_person'):
            lines.append(f"Người book: {meta['contact_person']}")
        
        if meta.get('pickup_addresses'):
            lines.append(f"Địa chỉ lấy hàng: {'; '.join(meta['pickup_addresses'])}")
        
        if meta.get('recipient_info'):
            lines.append(f"Thông tin người nhận: {meta['recipient_info']}")
        
        for i, booking in enumerate(result.get('bookings', []), 1):
            lines.append(f"\n--- Booking {i} ---")
            if booking.get('booking_date'):
                lines.append(f"Ngày: {booking['booking_date']}")
            if booking.get('pickup_time'):
                lines.append(f"Giờ lấy hàng: {booking['pickup_time']}")
            if booking.get('invoice_number'):
                lines.append(f"Invoice: {booking['invoice_number']}")
            if booking.get('goods_name'):
                lines.append(f"Hàng hóa: {booking['goods_name']}")
            if booking.get('package_quantity_raw'):
                lines.append(f"Số lượng: {booking['package_quantity_raw']}")
            if booking.get('weight_kg'):
                lines.append(f"Trọng lượng: {booking['weight_kg']} kg")
            if booking.get('delivery_notes'):
                lines.append(f"Ghi chú giao hàng: {booking['delivery_notes']}")
        
        return '\n'.join(lines)
    
    def _build_summary(self, result: Dict) -> str:
        """Build a short summary"""
        meta = result.get('metadata', {})
        bookings = result.get('bookings', [])
        
        parts = []
        if meta.get('company_name'):
            parts.append(meta['company_name'])
        
        if bookings:
            b = bookings[0]
            if b.get('booking_date'):
                parts.append(f"ngày {b['booking_date']}")
            if b.get('pickup_time'):
                parts.append(f"lúc {b['pickup_time']}")
            if b.get('package_quantity_raw'):
                parts.append(f"{b['package_quantity_raw']}")
        
        return ', '.join(parts) if parts else 'Booking form'


def is_booking_form(file_path: str) -> bool:
    """
    Detect if a file is a MEIKO/DREAMTECH style booking form.
    Check for characteristic cells.
    """
    try:
        wb = load_workbook(file_path, data_only=True, read_only=True)
        sheet = wb.active
        
        # Check for booking form indicators
        indicators = [
            sheet['A6'].value and 'BOOKING' in str(sheet['A6'].value).upper(),
            sheet['A7'].value and 'book xe' in str(sheet['A7'].value).lower(),
            sheet['B13'].value and 'ngày' in str(sheet['B13'].value).lower(),
        ]
        
        wb.close()
        return sum(indicators) >= 2
        
    except:
        return False
