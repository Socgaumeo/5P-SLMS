#!/usr/bin/env python3
"""
Create Realistic Test Jobs for All Service Types
=================================================

Creates sample jobs with complete, realistic data for each service type.

Service Types with required fields:
- TRUCKING: driver_name, license_plate, pickup/delivery addresses
- CUSTOMS: declaration_no, hs_code, customs dates
- PACKING: cargo dimensions, weight, volume
- WAREHOUSE: storage details, handling instructions
- CONTAINER: container_no, seal_no, container size

Run: python3 tests/test-create-realistic-jobs-for-all-service-types.py
"""

import os
import sys
from datetime import date, datetime, timedelta
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

# Initialize Supabase
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
client = create_client(url, key)

# Test date
TODAY = date.today().isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()

# Track sequences per prefix to avoid duplicates within same run
SEQUENCE_TRACKER = {}


def get_customer_id(customer_code: str) -> int:
    """Get customer ID by code"""
    result = client.table('customers').select('customer_id').eq(
        'customer_code', customer_code
    ).limit(1).execute()
    if result.data:
        return result.data[0]['customer_id']
    # Create if not exists
    insert = client.table('customers').insert({
        'customer_code': customer_code,
        'company_name': f'{customer_code} Test Company',
        'short_name': customer_code,
        'is_active': True
    }).execute()
    return insert.data[0]['customer_id']


def get_vendor_id(vendor_code: str) -> int:
    """Get vendor ID by code"""
    result = client.table('vendors').select('vendor_id').eq(
        'vendor_code', vendor_code
    ).limit(1).execute()
    if result.data:
        return result.data[0]['vendor_id']
    # Create if not exists
    insert = client.table('vendors').insert({
        'vendor_code': vendor_code,
        'company_name': f'{vendor_code} Logistics',
        'short_name': vendor_code,
        'is_active': True
    }).execute()
    return insert.data[0]['vendor_id']


def create_job(customer_id: int, service_type: str, scheduled_date: str) -> Dict:
    """Create a job and return job info"""
    global SEQUENCE_TRACKER

    # Generate job number based on service type
    prefix_map = {
        'TRUCKING': 'TRK',
        'WHS': 'WHS',
        'CUS': 'CUS',
        'SVC': 'PKG',
        'LIFT': 'TRK',
    }
    prefix = 'TRK'
    for key, val in prefix_map.items():
        if service_type.startswith(key):
            prefix = val
            break

    month = datetime.now().strftime('%m%d')
    tracker_key = f'{prefix}-{month}'

    # Get next sequence from DB if not tracked yet
    if tracker_key not in SEQUENCE_TRACKER:
        result = client.table('jobs').select('job_no').like(
            'job_no', f'{tracker_key}-%'
        ).order('job_no', desc=True).limit(1).execute()

        if result.data:
            last_no = result.data[0]['job_no']
            SEQUENCE_TRACKER[tracker_key] = int(last_no.split('-')[-1])
        else:
            SEQUENCE_TRACKER[tracker_key] = 0

    # Increment and use tracked sequence
    SEQUENCE_TRACKER[tracker_key] += 1
    seq = SEQUENCE_TRACKER[tracker_key]

    job_no = f'{prefix}-{month}-{seq:04d}'

    job_data = {
        'job_no': job_no,
        'customer_id': customer_id,
        'etd': scheduled_date,  # Use etd instead of booking_date
        'status_code': 'PENDING',
        'created_at': datetime.now().isoformat(),
    }

    result = client.table('jobs').insert(job_data).execute()
    return result.data[0]


def create_service(job_id: int, service_type: str, service_details: Dict) -> Dict:
    """Create a service for a job"""
    service_data = {
        'job_id': job_id,
        'service_type_code': service_type,
        'status_code': 'PENDING',
        'scheduled_date': service_details.get('scheduled_date', TODAY),
        'origin_address': service_details.get('origin_address'),
        'dest_address': service_details.get('dest_address'),
        'cargo_type': service_details.get('cargo_type'),
        'package_quantity': service_details.get('package_quantity'),
        'package_unit': service_details.get('package_unit'),
        'weight_kg': service_details.get('weight_kg'),
        'special_requirements': service_details.get('special_requirements'),
        'service_details': service_details.get('details'),  # JSON field
        'vendor_id': service_details.get('vendor_id'),
        'created_at': datetime.now().isoformat(),
    }

    result = client.table('job_services').insert(service_data).execute()
    return result.data[0]


# ============ Sample Data for Each Service Type ============

TRUCKING_SAMPLES = [
    {
        'service_type': 'TRUCKING_SHORT',
        'customer': 'DRT',
        'data': {
            'scheduled_date': TOMORROW,
            'origin_address': 'Kho Bình Dương - Đường Mỹ Phước Tân Vạn, TX Bến Cát, Bình Dương',
            'dest_address': 'Cảng Cát Lái - Đường Nguyễn Thị Định, TP Thủ Đức, TP.HCM',
            'cargo_type': 'Máy móc công nghiệp',
            'package_quantity': 10,
            'package_unit': 'kiện',
            'weight_kg': 5000,
            'special_requirements': 'Hàng dễ vỡ, không xếp chồng',
            'details': {
                'driver_name': 'Nguyễn Văn Hùng',
                'driver_phone': '0909123456',
                'driver_cccd': '079201012345',
                'license_plate': '51H-12345',
                'vehicle_type': 'Xe tải 5 tấn',
                'pickup_time': '08:00',
                'delivery_time': '14:00',
            }
        }
    },
    {
        'service_type': 'TRUCKING_LONG',
        'customer': 'SEVT',
        'data': {
            'scheduled_date': TOMORROW,
            'origin_address': 'KCN VSIP 2A - Bình Dương',
            'dest_address': 'Cảng Hải Phòng - Đình Vũ, Hải Phòng',
            'cargo_type': 'Linh kiện điện tử',
            'package_quantity': 50,
            'package_unit': 'thùng',
            'weight_kg': 8000,
            'special_requirements': 'Chống sốc, giữ nhiệt độ mát',
            'details': {
                'driver_name': 'Trần Minh Tú',
                'driver_phone': '0918234567',
                'driver_cccd': '036202023456',
                'license_plate': '15C-98765',
                'vehicle_type': 'Xe container 20ft',
                'pickup_time': '06:00',
                'estimated_arrival': '18:00 ngày hôm sau',
                'route': 'QL1A - Cao tốc Bắc Nam',
            }
        }
    },
    {
        'service_type': 'TRUCKING_CONT',
        'customer': 'ACS',
        'data': {
            'scheduled_date': TOMORROW,
            'origin_address': 'Cảng Cát Lái - TP.HCM',
            'dest_address': 'KCN Amata - Đồng Nai',
            'cargo_type': 'Container hàng nhập',
            'package_quantity': 1,
            'package_unit': 'cont 40ft',
            'weight_kg': 25000,
            'special_requirements': 'Rút hàng tại kho khách',
            'details': {
                'driver_name': 'Lê Văn Thành',
                'driver_phone': '0927345678',
                'driver_cccd': '079203034567',
                'license_plate': '51D-11111',
                'container_no': 'MSKU1234567',
                'seal_no': 'VN2024001234',
                'container_size': '40HC',
                'booking_no': 'MAEU123456789',
                'vessel': 'EVER GLORY',
                'voyage': '2401N',
            }
        }
    },
]

CUSTOMS_SAMPLES = [
    {
        'service_type': 'CUS_IMPORT',
        'customer': 'DRT',
        'data': {
            'scheduled_date': TODAY,
            'cargo_type': 'Máy móc công nghiệp nhập khẩu',
            'package_quantity': 20,
            'package_unit': 'kiện',
            'weight_kg': 15000,
            'special_requirements': 'Hàng có hoá đơn thuế',
            'details': {
                'declaration_no': '302-2024-0012345',
                'declaration_date': TODAY,
                'hs_code': '8479.89.90',
                'customs_office': 'Chi cục Hải quan Cát Lái',
                'import_license': 'GP-2024-00123',
                'invoice_no': 'INV-DRT-2024-001',
                'invoice_value': 50000,
                'currency': 'USD',
                'origin_country': 'China',
                'bl_no': 'COSU1234567890',
                'vessel': 'COSCO SHANGHAI',
                'eta': TOMORROW,
            }
        }
    },
    {
        'service_type': 'CUS_EXPORT',
        'customer': 'SEVT',
        'data': {
            'scheduled_date': TODAY,
            'cargo_type': 'Linh kiện điện tử xuất khẩu',
            'package_quantity': 100,
            'package_unit': 'thùng',
            'weight_kg': 5000,
            'special_requirements': 'Hàng xuất theo EPE',
            'details': {
                'declaration_no': '302-2024-E-00456',
                'declaration_date': TODAY,
                'hs_code': '8542.31.00',
                'customs_office': 'Chi cục Hải quan KCN',
                'export_license': 'XK-2024-00789',
                'invoice_no': 'EXP-SEVT-2024-089',
                'invoice_value': 120000,
                'currency': 'USD',
                'destination_country': 'Japan',
                'booking_no': 'NYK2024012345',
                'vessel': 'NYK VENUS',
                'etd': TOMORROW,
            }
        }
    },
    {
        'service_type': 'CUS_CO',
        'customer': 'ACS',
        'data': {
            'scheduled_date': TODAY,
            'cargo_type': 'Hàng xuất cần C/O',
            'special_requirements': 'Cần C/O Form E cho thị trường Trung Quốc',
            'details': {
                'co_type': 'Form E',
                'co_number': 'E-VN-2024-00123',
                'issue_date': TODAY,
                'issuing_authority': 'VCCI Hồ Chí Minh',
                'invoice_no': 'EXP-ACS-2024-045',
                'destination_country': 'China',
                'hs_code': '3926.90.99',
                'product_description': 'Plastic parts for electronics',
                'fob_value': 25000,
                'currency': 'USD',
            }
        }
    },
]

WAREHOUSE_SAMPLES = [
    {
        'service_type': 'WHS_STORAGE',
        'customer': 'DRT',
        'data': {
            'scheduled_date': TODAY,
            'dest_address': 'Kho 5P Bình Dương - 123 Đường Mỹ Phước, Bến Cát',
            'cargo_type': 'Máy móc công nghiệp',
            'package_quantity': 30,
            'package_unit': 'pallet',
            'weight_kg': 15000,
            'special_requirements': 'Hàng giữ lạnh 18-22°C',
            'details': {
                'storage_type': 'Kho lạnh',
                'warehouse_zone': 'Zone A - Cold Storage',
                'rack_location': 'A-01 đến A-10',
                'storage_start': TODAY,
                'expected_release': (date.today() + timedelta(days=30)).isoformat(),
                'storage_rate': 50000,
                'rate_unit': 'VND/pallet/ngày',
                'insurance_required': True,
                'insurance_value': 500000000,
            }
        }
    },
    {
        'service_type': 'WHS_HANDLE',
        'customer': 'SEVT',
        'data': {
            'scheduled_date': TOMORROW,
            'origin_address': 'Cảng Cát Lái',
            'dest_address': 'Kho 5P VSIP - Bình Dương',
            'cargo_type': 'Linh kiện điện tử',
            'package_quantity': 200,
            'package_unit': 'thùng',
            'weight_kg': 8000,
            'special_requirements': 'Cần xe nâng điện, không va đập',
            'details': {
                'handling_type': 'Bốc xếp + Sắp xếp kho',
                'forklift_required': True,
                'forklift_type': 'Xe nâng điện 2.5T',
                'workers_count': 4,
                'estimated_hours': 6,
                'handling_rate': 80000,
                'rate_unit': 'VND/tấn',
                'stacking_instructions': 'Xếp tối đa 3 tầng',
            }
        }
    },
]

PACKING_SAMPLES = [
    {
        'service_type': 'SVC_PACK',
        'customer': 'DRT',
        'data': {
            'scheduled_date': TOMORROW,
            'origin_address': 'KCN VSIP 1 - Bình Dương',
            'cargo_type': 'Máy nén khí công nghiệp',
            'package_quantity': 5,
            'package_unit': 'máy',
            'weight_kg': 8000,
            'special_requirements': 'Đóng thùng gỗ xuất khẩu, ISPM15',
            'details': {
                'packing_type': 'Wooden case - ISPM15',
                'dimensions': [
                    {'item': 'Máy 1', 'length_cm': 200, 'width_cm': 150, 'height_cm': 180, 'weight_kg': 1600},
                    {'item': 'Máy 2', 'length_cm': 200, 'width_cm': 150, 'height_cm': 180, 'weight_kg': 1600},
                    {'item': 'Máy 3', 'length_cm': 200, 'width_cm': 150, 'height_cm': 180, 'weight_kg': 1600},
                    {'item': 'Máy 4', 'length_cm': 200, 'width_cm': 150, 'height_cm': 180, 'weight_kg': 1600},
                    {'item': 'Máy 5', 'length_cm': 200, 'width_cm': 150, 'height_cm': 180, 'weight_kg': 1600},
                ],
                'total_cbm': 27.0,
                'material': 'Gỗ thông xử lý nhiệt ISPM15',
                'inner_protection': 'PE foam + VCI paper',
                'marking': 'Fragile, This Side Up, Keep Dry',
            }
        }
    },
    {
        'service_type': 'SVC_FUMI',
        'customer': 'SEVT',
        'data': {
            'scheduled_date': TOMORROW,
            'origin_address': 'Kho 5P Bình Dương',
            'cargo_type': 'Gỗ pallet đóng hàng',
            'package_quantity': 100,
            'package_unit': 'pallet',
            'weight_kg': 3000,
            'special_requirements': 'Hun trùng theo tiêu chuẩn ISPM15',
            'details': {
                'fumigation_type': 'Methyl Bromide',
                'treatment_duration': '24 giờ',
                'temperature_min': 21,
                'certificate_type': 'ISPM15 Certificate',
                'certificate_no': 'FUMI-2024-00123',
                'treatment_date': TOMORROW,
                'inspector': 'Chi cục Kiểm dịch thực vật vùng 2',
            }
        }
    },
    {
        'service_type': 'SVC_VACUUM',
        'customer': 'ACS',
        'data': {
            'scheduled_date': TOMORROW,
            'origin_address': 'KCN Amata - Đồng Nai',
            'cargo_type': 'Thiết bị điện tử cao cấp',
            'package_quantity': 50,
            'package_unit': 'thùng',
            'weight_kg': 2000,
            'special_requirements': 'Hút chân không + silica gel chống ẩm',
            'details': {
                'vacuum_type': 'Màng nhôm hút chân không',
                'bag_size': '2m x 1.5m',
                'silica_gel_qty': '500g/thùng',
                'humidity_indicator': True,
                'oxygen_absorber': True,
                'max_humidity': '30%RH',
            }
        }
    },
]

CONTAINER_SAMPLES = [
    {
        'service_type': 'LIFT_ON',
        'customer': 'DRT',
        'data': {
            'scheduled_date': TOMORROW,
            'origin_address': 'Cảng Cát Lái - Bãi container',
            'cargo_type': 'Container 40ft',
            'package_quantity': 1,
            'package_unit': 'cont',
            'weight_kg': 28000,
            'special_requirements': 'Nâng cẩu bằng Reach Stacker',
            'details': {
                'container_no': 'MSKU9876543',
                'container_size': '40HC',
                'gross_weight': 28000,
                'equipment_type': 'Reach Stacker 45T',
                'lifting_time': '08:00',
                'loading_to': 'Trailer 51H-99999',
                'operator': 'Nguyễn Văn Cẩu',
            }
        }
    },
    {
        'service_type': 'LIFT_OFF',
        'customer': 'SEVT',
        'data': {
            'scheduled_date': TOMORROW,
            'dest_address': 'Kho 5P VSIP - Bãi container',
            'cargo_type': 'Container 20ft',
            'package_quantity': 1,
            'package_unit': 'cont',
            'weight_kg': 18000,
            'special_requirements': 'Hạ nhẹ nhàng, hàng dễ vỡ bên trong',
            'details': {
                'container_no': 'OOLU1234567',
                'container_size': '20GP',
                'gross_weight': 18000,
                'equipment_type': 'Forklift 25T',
                'unloading_time': '14:00',
                'from_vehicle': 'Trailer 60H-88888',
                'stack_position': 'Row B, Slot 15',
                'operator': 'Trần Văn Hạ',
            }
        }
    },
]


def create_sample_jobs():
    """Create sample jobs for all service types"""
    print("=" * 60)
    print("Creating Realistic Sample Jobs")
    print("=" * 60)

    all_samples = [
        ('TRUCKING', TRUCKING_SAMPLES),
        ('CUSTOMS', CUSTOMS_SAMPLES),
        ('WAREHOUSE', WAREHOUSE_SAMPLES),
        ('PACKING', PACKING_SAMPLES),
        ('CONTAINER', CONTAINER_SAMPLES),
    ]

    created_jobs = []

    for category, samples in all_samples:
        print(f"\n--- {category} ---")

        for sample in samples:
            service_type = sample['service_type']
            customer_code = sample['customer']
            data = sample['data']

            try:
                # Get customer ID
                customer_id = get_customer_id(customer_code)

                # Get vendor ID if needed
                vendor_id = None
                if service_type.startswith('TRUCKING'):
                    vendor_id = get_vendor_id('AIPAS')
                elif service_type.startswith('SVC'):
                    vendor_id = get_vendor_id('PACKING01')

                data['vendor_id'] = vendor_id

                # Create job
                job = create_job(customer_id, service_type, TODAY)
                job_id = job['job_id']
                job_no = job['job_no']

                # Create service
                service = create_service(job_id, service_type, data)
                svc_id = service['svc_id']

                # Update job status to match
                client.table('jobs').update({
                    'status_code': 'PENDING'
                }).eq('job_id', job_id).execute()

                created_jobs.append({
                    'job_no': job_no,
                    'service_type': service_type,
                    'customer': customer_code,
                })

                print(f"  ✅ {job_no} - {service_type} ({customer_code})")

            except Exception as e:
                print(f"  ❌ Failed {service_type}: {e}")

    print("\n" + "=" * 60)
    print(f"Created {len(created_jobs)} sample jobs")
    print("=" * 60)

    return created_jobs


if __name__ == "__main__":
    jobs = create_sample_jobs()
