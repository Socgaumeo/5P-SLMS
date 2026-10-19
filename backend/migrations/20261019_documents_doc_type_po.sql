-- 19/10/2026 (Khánh): thêm loại chứng từ PO (đơn đặt hàng / purchase order), trước đây xếp vào OTHER.
alter table documents drop constraint if exists documents_doc_type_check;
alter table documents add constraint documents_doc_type_check check (doc_type = any (array[
  'AN','DEBIT','DO','CD','CO','INVOICE','AWB','BL','PACKING_LIST','BBGH','PO',
  'BOOKING','WEIGHT_SLIP','PHOTO_PICKUP','PHOTO_DELIVERY','SERVICE_CONFIRM','QUOTATION','OTHER']));
