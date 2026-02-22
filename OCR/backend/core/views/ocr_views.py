import json
import os
import logging
import re
from typing import Optional, Dict

from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from openai import OpenAI

from consts.responses import Responses
from services import OCRCore
from core.serializers import MultipleFileUploadSerializer
from core.models import Batch, Document, Field, DocumentField

logger = logging.getLogger(__name__)


SITE_ID_ASCO = 'asco'

# Domain-specific dictionaries for better OCR recognition
PERSIAN_COMPANIES = {
    'شرکت سیلیس', 'شرکت بلور', 'شرکت وحدت', 'شرکت آکو', 'شرکت تجاری الف',
    'شرکت صنایع', 'شرکت تولیدی', 'موسسه', 'سازمان'
}

PERSIAN_CITIES = {
    'اصفهان', 'تهران', 'مشهد', 'شیراز', 'تبریز', 'کرمان', 'اصفهان',
    'اصفی ها ن', 'اص فی ان', 'اص فه ان', 'اصفهان', 'اصفیان'
}

PERSIAN_PORTS = {
    'بندر عباس', 'بندر انزلی', 'بندر امام', 'بندر خمینی',
    'بندر شهید رجایی', 'بندر چابهار', 'بندر لنگه'
}

# ISO 4217 currency codes
VALID_CURRENCIES = {'IRR', 'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'SAR', 'AED'}


@method_decorator(csrf_exempt, name='dispatch')
class OCRProcessView(APIView):

    parser_classes = (MultiPartParser, FormParser)
    serializer_class = MultipleFileUploadSerializer  # Use the new serializer


    def post(self, request, format=None):
        # return Responses.get_response(Responses.GENERAL.OK, {
        #     "result": [
        #         {
        #             "document_id": 7,
        #             "data": [
        #                 {
        #                     "id": 40,
        #                     "group": "general",
        #                     "name": "DATE OF ISSUE",
        #                     "value": "2026-01-07"
        #                 },
        #                 {
        #                     "id": 41,
        #                     "group": "general",
        #                     "name": "DATE OF INSPECTION",
        #                     "value": "2025-10-21"
        #                 },
        #                 {
        #                     "id": 42,
        #                     "group": "general",
        #                     "name": "PLACE OF INSPECTION",
        #                     "value": "CHINA"
        #                 },
        #                 {
        #                     "id": 43,
        #                     "group": "general",
        #                     "name": "NOTIFY PARTY",
        #                     "value": "PETRO SAMAN AZAR TETIS COMPANY, NO.125, KHAZRA INDUSTRIAL ZONE, KERMAN, IRAN"
        #                 },
        #                 {
        #                     "id": 44,
        #                     "group": "general",
        #                     "name": "CONSIGNEE",
        #                     "value": "ESFAHAN'S MOBARAKEH STEEL COMPANY (MSC), 7KM SOUTHWEST OF MOBARAKE, P.O. BOX: 161, ESFAHAN, IRAN"
        #                 },
        #                 {
        #                     "id": 45,
        #                     "group": "general",
        #                     "name": "SHIPPER / CONSIGNOR",
        #                     "value": "TAIZHOU KAIRI TRADING COMPANY. LTD"
        #                 },
        #                 {
        #                     "id": 48,
        #                     "group": "general",
        #                     "name": "DESCRIPTION OF GOODS AS PER P/L",
        #                     "value": "AS UHP GRAPHITE ELECTRODES DIA UHP 700MM X 2700MM (+/-100MM) WITH 4TPIL UHP PER B/L NIPPLES PRESET"
        #                 },
        #                 {
        #                     "id": 50,
        #                     "group": "general",
        #                     "name": "PACKING",
        #                     "value": "120 CASES"
        #                 },
        #                 {
        #                     "id": 51,
        #                     "group": "general",
        #                     "name": "ORIGIN",
        #                     "value": "CHINA"
        #                 },
        #                 {
        #                     "id": 52,
        #                     "group": "general",
        #                     "name": "PORT OF LOADING",
        #                     "value": "TIANJIN, CHINA"
        #                 },
        #                 {
        #                     "id": 53,
        #                     "group": "general",
        #                     "name": "PORT OF DISCHARGE",
        #                     "value": "BANDAR ABBAS, PERSIAN GULF, IRAN"
        #                 },
        #                 {
        #                     "id": 54,
        #                     "group": "general",
        #                     "name": "REGISTRATION NO",
        #                     "value": "66317555"
        #                 },
        #                 {
        #                     "id": 55,
        #                     "group": "general",
        #                     "name": "IRANIAN CUSTOMS TARIFF NO",
        #                     "value": "85451100"
        #                 },
        #                 {
        #                     "id": 56,
        #                     "group": "general",
        #                     "name": "INSURANCE",
        #                     "value": "ASIA INSURANCE CO, UNDER POLICY NO. 1132033/04/000189"
        #                 },
        #                 {
        #                     "id": 39,
        #                     "group": "general",
        #                     "name": "REFERENCE NO.",
        #                     "value": "EL25-0266"
        #                 },
        #                 {
        #                     "id": 46,
        #                     "group": "general",
        #                     "name": "P/I NO.DATE",
        #                     "value": "FCPS-250470 - 2025-04-19"
        #                 },
        #                 {
        #                     "id": 47,
        #                     "group": "general",
        #                     "name": "C/I NO.DATE",
        #                     "value": "FCPS-251270-02 - 2025-12-15"
        #                 },
        #                 {
        #                     "id": 49,
        #                     "group": "general",
        #                     "name": "B/L NO. & DATE",
        #                     "value": "SSOW/ZSS/3SS2 - 2025-12-14"
        #                 }
        #             ]
        #         }
        #     ]
        # })
        """
        Process multiple uploaded documents with OCR.

        Expected POST data:
        - files: List of document files to process
        - language_hint: Optional language hint ('fa', 'en')
        - document_type: Optional document type for context
        """
        try:
            serializer = MultipleFileUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Responses.get_response(Responses.GENERAL.WRONG_INPUTS)

            site_id = request.headers.get('X-Site-ID')
            uploaded_files = serializer.validated_data['files']

            results = []
            upload_dir = getattr(settings, 'OCR_UPLOAD_DIR', 'ocr_uploads')

            batch = Batch.objects.create(
                user=request.user,
                docs_path=json.dumps({}),
            )
            # Process each file
            ocr_core = OCRCore()
            for uploaded_file in uploaded_files:

                started_at = timezone.now()
                ocr_data = ocr_core.process_doc(uploaded_file)
                raw_text = ocr_data['raw_text']
                normalized_text = ocr_data['normalized_text']
                confidence = ocr_data['confidence']
                method = ocr_data['method']
                bounding_boxes = ocr_data['bounding_boxes']
                file_path = ocr_data['file_path']

                with transaction.atomic():
                    document = Document.objects.create(
                        user=request.user,
                        batch=batch,
                        ocr_raw=raw_text,
                        ocr_bounding_boxes=bounding_boxes,
                        ocr_confidence=confidence,
                        ocr_method=method,
                        ocr_started_at=started_at,
                        ocr_finished_at=timezone.now(),
                    )
                    docs_path = json.loads(batch.docs_path)
                    batch.docs_path = json.dumps(docs_path | {str(document.id): file_path})
                    batch.save()

                print(f"Starting normalization for document {document.id}")
                print(f"Raw OCR text length: {len(normalized_text)}")

                normalized_json = self._normalize_raw_text(normalized_text, site_id)
                print(f"Normalization result: {normalized_json}")

                if normalized_json:
                    print(f"Saving normalized data for document {document.id}")
                    with transaction.atomic():
                        document.normalized_json = normalized_json
                        document.normalized_method = 'hybrid_anchoring'
                        document.normalized_finished_at = timezone.now()
                        document.save()

                        # Recursive function to handle any depth of nesting
                        def save_fields(data_dict, parent_group=""):
                            for key, value in data_dict.items():
                                current_group = f"{parent_group}.{key}" if parent_group else key

                                if isinstance(value, dict):
                                    # Recurse deeper
                                    save_fields(value, current_group)
                                elif value is not None:
                                    # It's a value, save it
                                    # Split group and name (e.g., "seller.address" -> group="seller", name="address")
                                    if site_id != SITE_ID_ASCO and "." in current_group:
                                        group, name = current_group.rsplit(".", 1)
                                    else:
                                        group = "general"
                                        name = key

                                    print(f"  Saving: Group='{group}', Name='{name}', Value='{value}'")
                                    field_obj, _ = Field.objects.get_or_create(
                                        group=group,
                                        name=name
                                    )
                                    DocumentField.objects.create(
                                        document=document,
                                        field=field_obj,
                                        normalized_value=value,
                                    )

                        save_fields(normalized_json)
                else:
                    print(f"No normalization results for document {document.id}")

                # get flat key, values for front
                doc_fields = DocumentField.objects.filter(document_id=document.id).select_related('field')
                result = []
                for df in doc_fields:
                    result.append({
                        "id": df.id,
                        "group": df.field.group,
                        "name": df.field.name,
                        "value": df.hitl_value if df.hitl_value is not None else df.normalized_value
                    })
                results.append({
                    "document_id": document.id,
                    "data": result
                })

            return Responses.get_response(Responses.GENERAL.OK, {'result': results})

        except Exception as e:
            logger.error(f"OCR view error: {str(e)}", exc_info=True)
            return Responses.get_response(Responses.GENERAL.SERVER_ERROR)

    def _normalize_raw_text(self, raw_text: str, site_id: Optional[str]) -> Optional[Dict]:
        """
        Two-Stage Normalization System with Post-Processing:
        Stage 1: Recall-Optimized Detector - finds possible fields with high tolerance
        Stage 2: Schema Gatekeeper - validates and normalizes with strict schema
        Post-Process: Sanitize and validate with domain-specific rules
        Returns a Python dict parsed from the model's JSON output.
        """

        # First normalize Persian text spacing
        processed_text = self._normalize_persian_spacing(raw_text)
        print(f"Original text length: {len(raw_text)}")
        print(f"Processed text length: {len(processed_text)}")
        print(f"First 200 chars of processed text: {processed_text[:200]}")

        # Stage 1: Recall-Optimized Detector
        print("\n=== Stage 1: Recall-Optimized Detector ===")
        stage1_result = self._stage1_detect_possible_fields(processed_text)
        if not stage1_result:
            print("Stage 1 failed to detect any fields")
            return None

        print(f"Stage 1 detected {len(stage1_result)} possible fields")
        for key, value in stage1_result.items():
            print(f"  {key}: {value}")

        # Stage 2: Schema Gatekeeper
        print("\n=== Stage 2: Schema Gatekeeper ===")
        if site_id == SITE_ID_ASCO:
            final_result = self._stage2_normalize_fields_asco(stage1_result, processed_text)
        else:
            final_result = self._stage2_normalize_fields(stage1_result, processed_text)

        if not final_result:
            print("Stage 2 failed to normalize fields")
            return None

        print(f"Stage 2 normalized {len(final_result)} fields")
        for key, value in final_result.items():
            print(f"  {key}: {value}")

        # Post-Process: Sanitize and validate
        print("\n=== Post-Process: Sanitize & Validate ===")
        sanitized_result = self._post_process_validation(final_result)
        if not sanitized_result:
            print("Post-processing failed")
            return None

        print(f"Post-processed {len(sanitized_result)} fields")
        for key, value in sanitized_result.items():
            print(f"  {key}: {value}")
        print("=== Two-Stage Normalization with Post-Processing Complete ===\n")

        return sanitized_result

    def _clean_common_ocr_artifacts(self, text: str) -> str:
        """
        Pre-LLM cleaning for common Tesseract/OCR artifacts.
        Replaces specific leetspeak patterns only when safe.
        """
        if not text:
            return ""

        # 1. Fix broken numbers/dates (e.g., "2 0 2 4" -> "2024")
        # Look for digits separated by single spaces
        text = re.sub(r'(?<=\d)\s+(?=\d)', '', text)

        # 2. Fix spaced-out slashes in dates (e.g., "2024 / 01 / 05")
        text = re.sub(r'\s*/\s*', '/', text)

        # 3. Fix common "1" vs "I" or "l" in obvious numeric contexts (optional, risky if not careful)
        # Better to let LLM handle complex leetspeak contextually.

        return text

    def _post_process_validation(self, result: Dict) -> Dict:
        """Apply post-LLM sanitization and validation rules."""
        if not result:
            return result

        sanitized = {}

        # Apply field-specific validation
        for key, value in result.items():
            if key == 'document_date':
                sanitized[key] = self._validate_date(value)
            elif key == 'currency':
                sanitized[key] = self._validate_currency(value)
            elif key in ['port_of_loading', 'port_of_discharge', 'country_of_origin']:
                sanitized[key] = self._validate_port_address(value)
            elif key == 'document_number':
                sanitized[key] = self._validate_document_number(value)
            elif key == 'weight' and isinstance(value, dict):
                # Handle nested weight object
                sanitized[key] = {}
                for weight_key, weight_value in value.items():
                    sanitized[key][weight_key] = self._sanitize_value(weight_value)
            else:
                # General sanitization for other fields
                sanitized[key] = self._sanitize_value(value)

        return sanitized

    def _stage1_detect_possible_fields(self, processed_text: str) -> Optional[Dict]:
        """
        Stage 1: Contextual Extraction with repair capabilities
        Purpose: "Detect and REPAIR business fields"
        Higher tolerance, allows ambiguity, but attempts repairs
        """
        # Apply the new cleaner first
        cleaned_text = self._clean_common_ocr_artifacts(processed_text)

        system_instruction = """You are a Forensic Document Analyst specialized in repairing OCR-damaged business text.

Your Goal: Detect business fields and REPAIR OCR artifacts based on context.

CRITICAL INSTRUCTIONS:
1. **Contextual Repair:** If you see "Hefei 8ocen" in a company header, you MUST output "Hefei Bocen". If you see "202 5/ 0I", output "2025/01".
2. **Leetspeak Correction:** Fix common OCR swaps:
   - '8' → 'B' (in text)
   - '5' → 'S' (in text)
   - '7' → 'T' (in text)
   - '1' or 'I' or 'l' → '1' (in numbers)
3. **Output Format:** JSON with "possible_" prefix.
4. **Confidence Scoring:**
   - "high": Value is clear OR was successfully repaired using strong context.
   - "medium": Value found but ambiguous even after repair attempts.
   - "low": Text is too fragmented to make sense.

Structure:
{
  "raw": "The corrected/repaired text",
  "original_fragment": "The actual damaged text found in source",
  "confidence": "high|medium|low"
}

Field types to detect:
- Document numbers, Dates, Amounts (Total/Tax), Weights, Company Names (Seller/Buyer).
- Ports, Addresses, Descriptions, Payment Terms, Container Numbers, Seal Numbers
- HS Codes, Tariff Rates, Countries of Origin, Incoterms"""

        user_prompt = f"""
OCR Text (Noisy):
{cleaned_text}

Detect and REPAIR fields.
Each field must be structured with raw (corrected), original_fragment, and confidence.
Be tolerant of OCR errors and attempt contextual repairs.
"""

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                temperature=0.3,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ]
            )

            output_text = response.choices[0].message.content.strip()
            print(f"Stage 1 raw output: {output_text}")

            # Parse JSON defensively
            try:
                return json.loads(output_text)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                match = re.search(r'\{.*\}', output_text, flags=re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except json.JSONDecodeError:
                        print('Model returned invalid JSON')
                        print(output_text)
                print("Stage 1: Failed to parse JSON")
                return None

        except Exception as e:
            print(f"Stage 1 error: {str(e)}")
            return None

    def _stage2_normalize_fields(self, stage1_result: Dict, processed_text: str) -> Optional[Dict]:
        """
        Stage 2: Intelligent Validator
        Purpose: "Validate, Standardize, and Format data"
        """
        system_instruction = """You are a SCHEMA GATEKEEPER.

Your job is to Validate, Standardize, and Format data into the final JSON structure.

INPUT CONTEXT:
You will receive "possible fields" that may have been repaired by the previous stage.

NORMALIZATION RULES:
Map all extracted fields to a fixed canonical schema using the following normalization rules:
- SELLER: {Seller, Shipper, Exporter, Consignor, Supplier, Vendor}
- BUYER: {Buyer, Consignee, Importer, Receiver, Customer}
- NOTIFY_PARTY: {Notify, Third Party Notify}
- DOCUMENT_NUMBER: {Document No, Invoice No, BL No, AWB No, Reference}
- DOCUMENT_DATE: {Date, Invoice Date, Issue Date, Shipping Date}
- CURRENCY: {Currency, CUR, Curr}
- TOTAL_AMOUNT: {Total Amount, Invoice Amount, Grand Total, Amount Payable}
- TAX_AMOUNT: {Tax, VAT, GST, Duty, Tariff Amount}
- INCOTERMS: {Incoterms, Delivery Terms, FOB, CIF, EXW, DDP}
- WEIGHT: {Net Weight, Gross Weight, Total Weight}
- QUANTITY: {Qty, Quantity, Pieces, Units}
- DESCRIPTION_OF_GOODS: {Description, Goods Description, Description of Product, Items, Product Description, Commodity Description}
- HS_CODE: {HS Code, Tariff Code, Customs Code, Harmonized Code, Commodity Code}
- TARIFF_RATE: {Tariff, Duty Rate, Customs Tariff, Import Duty Rate}
- PORT_OF_LOADING: {POL, Port of Loading}
- PORT_OF_DISCHARGE: {POD, Port of Discharge}
- COUNTRY_OF_ORIGIN: {COO, Country of Origin, Origin}
- PO_NUMBER: {PO Number, Purchase Order}
- CONTAINER_NUMBER: {Container No, CNTR}
- SEAL_NUMBER: {Seal No}
- PAYMENT_TERMS: {Payment Terms, NET30, NET45, Advanced Payment, Credit Terms}
- ISO_CURRENCY_CODE: {ISO Currency Code}
- ISO_COUNTRY_CODE: {ISO Country Code}

RULES:
1. **Validation:** Check if the value makes sense for the field type.
2. **Standardization:**
   - Convert all dates to YYYY-MM-DD.
   - Convert amounts to clean numeric strings.
   - Convert currency codes to ISO.
3. **Completeness:** Do NOT drop high-confidence fields just because they are contact details. Map them to the schema below.

Canonical Lexicon (Persian/English):
- SELLER: {فروشنده, فروش, شرکت, موسسه}
- BUYER: {خریدار, خرید, مشتری}
- ADDRESS: {نشانی, آدرس, محل, خیابان}
- CONTACT: {تلفن, فکس, ایمیل, تماس, نام مخاطب}
- DOCUMENT_NUMBER: {شماره, فاکتور, بارنامه, رسید, شناسه, کد}
- WEIGHT: {وزن, وزن خالص, وزن ناخالص, وزن کل, کیلوگرم}
- PORT: {بندر, مبدأ, مقصد, بارگیری, تخلیه}
- AMOUNT: {مبلغ, قیمت, ارزش, هزینه, کرایه}

OUTPUT SCHEMA (Strict JSON):
{
  "seller": {
    "name": "String or null",
    "address": "String or null",
    "tax_id": "String or null",
    "phone": "String or null",
    "email": "String or null"
  },
  "buyer": {
    "name": "String or null",
    "address": "String or null",
    "tax_id": "String or null",
    "zip_code": "String or null",
    "phone": "String or null",
    "email": "String or null"
  },
  "notify_party": {
    "name": "String or null",
    "address": "String or null",
    "phone": "String or null",
    "email": "String or null"
  },
  "consignee": {
    "name": "String or null",
    "address": "String or null",
    "phone": "String or null"
  },
  "shipper": {
    "name": "String or null",
    "address": "String or null",
    "phone": "String or null"
  },
  "contact_details": {
    "person_name": "String or null",
    "phone": "String or null",
    "fax": "String or null",
    "email": "String or null"
  },
  "document_info": {
    "document_number": "String or null",
    "document_date": "YYYY-MM-DD or null",
    "po_number": "String or null",
    "payment_terms": "String or null",
    "document_type": "String or null"
  },
  "financials": {
    "currency": "ISO Code or null",
    "iso_currency_code": "ISO Code or null",
    "total_amount": "Number or null",
    "tax_amount": "Number or null",
    "insurance_amount": "Number or null",
    "freight_amount": "Number or null",
    "other_fees": "Number or null"
  },
  "shipping": {
    "incoterms": "String or null",
    "net_weight_kg": "Number or null",
    "gross_weight_kg": "Number or null",
    "total_weight_kg": "Number or null",
    "quantity": "Number or null",
    "package_count": "Number or null",
    "port_of_loading": "String or null",
    "port_of_discharge": "String or null",
    "country_of_origin": "String or null",
    "iso_country_code": "ISO Code or null",
    "container_number": "String or null",
    "seal_number": "String or null",
    "vessel_name": "String or null",
    "voyage_number": "String or null"
  },
  "goods_description": "String or null",
  "hs_code": "String or null",
  "tariff_rate": "Number or null",
  "customs_value": "Number or null"
}

FIELD MAPPING GUIDE:
- possible_seller_name -> seller.name
- possible_buyer_name -> buyer.name
- possible_notify_party -> notify_party.name
- possible_address -> seller.address or buyer.address or notify_party.address (based on context)
- possible_phone -> contact_details.phone or seller.phone/buyer.phone/notify_party.phone
- possible_email -> contact_details.email or seller.email/buyer.email/notify_party.email
- possible_telephone -> contact_details.phone
- possible_fax -> contact_details.fax
- possible_zip_code -> buyer.zip_code
- possible_tax_id -> seller.tax_id or buyer.tax_id
- possible_document_number -> document_info.document_number
- possible_date -> document_info.document_date
- possible_po_number -> document_info.po_number
- possible_payment_terms -> document_info.payment_terms
- possible_currency -> financials.currency
- possible_iso_currency_code -> financials.iso_currency_code
- possible_total_amount -> financials.total_amount
- possible_tax_amount -> financials.tax_amount
- possible_insurance_amount -> financials.insurance_amount
- possible_freight_amount -> financials.freight_amount
- possible_weight -> shipping.net_weight_kg/gross_weight_kg (based on context)
- possible_quantity -> shipping.quantity
- possible_package_count -> shipping.package_count
- possible_port_of_loading -> shipping.port_of_loading
- possible_port_of_discharge -> shipping.port_of_discharge
- possible_country_of_origin -> shipping.country_of_origin
- possible_iso_country_code -> shipping.iso_country_code
- possible_container_number -> shipping.container_number
- possible_seal_number -> shipping.seal_number
- possible_vessel_name -> shipping.vessel_name
- possible_description -> goods_description
- possible_hs_code -> hs_code
- possible_tariff_rate -> tariff_rate
- possible_customs_value -> customs_value

VALIDATION PRINCIPLES:
- Better to return null than bad data
- Medium confidence fields that pass validation are acceptable
- Low confidence fields should be rejected unless clearly correct
- Apply canonical mappings exactly as specified
- Extract ALL available data that meets validation criteria"""

        user_prompt = f"""
Detected possible fields from Stage 1:
{json.dumps(stage1_result, indent=2)}

Original OCR text for context:
{processed_text}

As SCHEMA GATEKEEPER, map these fields to the new schema.
- Use the field mapping guide to place data correctly
- Keep all valid data that passes validation
- Apply Persian canonical mappings
- Standardize formats (dates, amounts, currency codes)
- Remember: Quality over quantity - prefer null over incorrect data
"""

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model="gpt-4o",  # Use gpt-4o for complex schema mapping
                temperature=0,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ]
            )

            output_text = response.choices[0].message.content.strip()
            print(f"Stage 2 raw output: {output_text}")

            try:
                return json.loads(output_text)
            except json.JSONDecodeError:
                match = re.search(r'\{.*\}', output_text, flags=re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except json.JSONDecodeError:
                        pass
                return None

        except Exception as e:
            print(f"Stage 2 error: {str(e)}")
            return None

    def _stage2_normalize_fields_asco(self, stage1_result: Dict, processed_text: str) -> Optional[Dict]:
        """
        Stage 2: Strict Transformer
        Purpose: Map Stage 1 repairs to a specific 19-field enterprise schema.
        """
        system_instruction = """You are a DATA TRANSFORMER for Trade Documents.
Your goal is to extract and standardize exactly 19 specific fields from the provided OCR context.

REQUIRED OUTPUT FIELDS & MAPPING RULES:
1.  REFERENCE NO.: The main file or document reference number.
2.  DATE OF ISSUE: Date the document was created (Standardize to YYYY-MM-DD).
3.  DATE OF INSPECTION: Specific date of inspection if mentioned.
4.  PLACE OF INSPECTION: Physical location/city/facility of inspection.
5.  NOTIFY PARTY: Full name and address of the party to be notified.
6.  CONSIGNEE: Full name and address of the receiver.
7.  SHIPPER / CONSIGNOR: Full name and address of the sender/exporter.
8.  P/I NO.DATE: Proforma Invoice number and its date (e.g., "PI123 - 2025/01/01").
9.  C/I NO.DATE: Commercial Invoice number and its date.
10. DESCRIPTION OF GOODS AS PER P/L: Full description of items (Packing List context).
11. NAME OF VESSEL / VOY NO: Vessel name and the voyage number.
12. B/L NO. & DATE: Bill of Lading number and its date.
13. PACKING: Details on packaging (e.g., "Pallets", "Loose", "20ft Container").
14. ORIGIN: Country of origin (Standardize to ISO or Full Name).
15. PORT OF LOADING: Departure port.
16. PORT_OF_DISCHARGE: Arrival port.
17. REGISTRATION NO: Any official company or vehicle registration number mentioned.
18. IRANIAN CUSTOMS TARIFF NO: The HS Code or Tariff code specifically for Iran Customs.
19. INSURANCE: Insurance policy details, amounts, or terms.

RULES:
- Use 'null' if a field is absolutely not found.
- Always prefer corrected 'raw' values from Stage 1.
- Standardize all dates to YYYY-MM-DD.
- If multiple values exist, provide the most relevant one for the field header.

OUTPUT FORMAT:
Return a JSON object with these EXACT keys in uppercase."""

        user_prompt = f"""
STAGE 1 REPAIRED DATA:
{json.dumps(stage1_result, indent=2)}

FULL OCR TEXT FOR CONTEXT:
{processed_text}

Transform the data into the following JSON structure and keep the order:
{{
  "REFERENCE NO.": "",
  "DATE OF ISSUE": "",
  "DATE OF INSPECTION": "",
  "PLACE OF INSPECTION": "",
  "NOTIFY PARTY": "",
  "CONSIGNEE": "",
  "SHIPPER / CONSIGNOR": "",
  "P/I NO.DATE": "",
  "C/I NO.DATE": "",
  "DESCRIPTION OF GOODS AS PER P/L": "",
  "NAME OF VESSEL / VOY NO": "",
  "B/L NO. & DATE": "",
  "PACKING": "",
  "ORIGIN": "",
  "PORT OF LOADING": "",
  "PORT OF DISCHARGE": "",
  "REGISTRATION NO": "",
  "IRANIAN CUSTOMS TARIFF NO": "",
  "INSURANCE": ""
}}
"""

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ]
            )

            output_text = response.choices[0].message.content.strip()
            return json.loads(output_text)

        except Exception as e:
            print(f"Stage 2 error: {str(e)}")
            return None

    def _normalize_persian_spacing(self, text: str) -> str:
        """Normalize Persian text using aggressive normalization for OCR fragments."""
        return self._aggressive_persian_normalization(text)

    def _sanitize_value(self, value: str) -> str:
        """Post-LLM sanitization to remove placeholders and artifacts."""
        if not value:
            return None
        if isinstance(value, str):
            v = value.strip().replace("\n", "")
            if not v or v in {"-", "--", "null", "N/A", "نامشخص"}:
                return None
            return v
        return value

    def _validate_date(self, date_str: str) -> Optional[str]:
        """Validate date format - reject Persian OCR strings, require ISO format."""
        if not date_str:
            return None

        date_str = self._sanitize_value(date_str)
        if not date_str:
            return None

        # Reject Persian date patterns
        persian_patterns = [
            r'^\d{4}/\d{1,2}/\d{1,2}$',  # Persian format
            r'^\d{1,2}/\d{1,2}/\d{4}$',  # Another Persian format
            r'^[۰-۹]{4}/[۰-۹]{1,2}/[۰-۹]{1,2}$',  # Persian numerals
        ]

        for pattern in persian_patterns:
            if re.match(pattern, date_str):
                return None

        # Accept only ISO format YYYY-MM-DD
        iso_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if re.match(iso_pattern, date_str):
            return date_str

        return None

    def _validate_currency(self, currency_str: str) -> Optional[str]:
        """Validate currency - ISO 4217 only."""
        if not currency_str:
            return None

        currency_str = self._sanitize_value(currency_str)
        if not currency_str:
            return None

        # Map common Persian terms to ISO codes
        currency_mapping = {
            'ریال': 'IRR',
            'تومان': 'IRR',
            'دلار': 'USD',
            'یورو': 'EUR',
            'پوند': 'GBP'
        }

        # Direct ISO code
        if currency_str.upper() in VALID_CURRENCIES:
            return currency_str.upper()

        # Persian term mapping
        if currency_str in currency_mapping:
            return currency_mapping[currency_str]

        return None

    def _validate_port_address(self, address_str: str) -> Optional[str]:
        """Validate ports/addresses - reject fragmented tokens."""
        if not address_str:
            return None

        address_str = self._sanitize_value(address_str)
        if not address_str:
            return None

        # Reject if contains excessive spacing between letters (fragmentation)
        if re.search(r'[ا-ی]\s{2,}[ا-ی]', address_str):
            return None

        # Check against known cities/ports
        normalized = address_str.replace(' ', '').replace('\u200c', '')
        for city in PERSIAN_CITIES:
            if normalized in city.replace(' ', ''):
                return city

        for port in PERSIAN_PORTS:
            if normalized in port.replace(' ', ''):
                return port

        return address_str

    def _validate_document_number(self, doc_number: str) -> Optional[str]:
        """Validate document numbers - clean multiple hyphens/spaces."""
        if not doc_number:
            return None

        doc_number = self._sanitize_value(doc_number)
        if not doc_number:
            return None

        # Clean multiple hyphens and spaces
        cleaned = re.sub(r'[-\s]{2,}', '-', doc_number)
        cleaned = re.sub(r'^[-\s]+|[-\s]+$', '', cleaned)

        # Basic validation - should contain at least some alphanumeric
        if not re.search(r'[A-Za-z0-9]', cleaned):
            return None

        return cleaned

    def _aggressive_persian_normalization(self, text: str) -> str:
        """Aggressive Persian text normalization for OCR fragments."""
        if not text:
            return text

        try:
            # First apply basic spacing normalization
            normalized = re.sub(r'([ا-ی])\s+([ا-ی])', r'\1\2', text)

            # Aggressive character merging for common city/port fragments
            city_mappings = {
                'اص فی ان': 'اصفهان',
                'اص فه ان': 'اصفهان',
                'اصفی ها ن': 'اصفهان',
                'اصفیها ن': 'اصفهان',
                'اص فیها ن': 'اصفهان',
                'اص فهان': 'اصفهان',
                'اصفه ان': 'اصفهان',
                'ته را ن': 'تهران',
                'تهرا ن': 'تهران',
                'مش هد': 'مشهد',
                'مشهد': 'مشهد',
                'شیرا ز': 'شیراز',
                'شیراز': 'شیراز',
                'تبر یز': 'تبریز',
                'تبریز': 'تبریز'
            }

            for fragment, correct in city_mappings.items():
                normalized = normalized.replace(fragment, correct)

            # Company name normalization
            company_mappings = {
                'شرکت سیلی س': 'شرکت سیلیس',
                'شرکت بلور': 'شرکت بلور',
                'شرکت وحدت': 'شرکت وحدت',
                'شرکت آکو': 'شرکت آکو',
                'شرکت تجاری الف': 'شرکت تجاری الف'
            }

            for fragment, correct in company_mappings.items():
                normalized = normalized.replace(fragment, correct)

            # Remove excessive spaces
            normalized = re.sub(r'\s{3,}', '  ', normalized)

            return normalized

        except Exception as e:
            print(f"Error in aggressive Persian normalization: {str(e)}")
            return text
