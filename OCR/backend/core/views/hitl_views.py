from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from consts.responses import Responses
from core.models import DocumentField, Document, Batch


class HITLView(APIView):
    """
    Update HITL values for one or more documents.
    Only allowed if:
        - request.user == document.user
        - document.batch.status == 'pending'
    """

    def post(self, request, format=None):
        """
        {
            "documents": [
                {
                    "document_id": "id-1",
                    "data": [
                        {"id": "document_field_id", "value": "new value"},
                        ...
                    ]
                },
                {
                    "document_id": "id-2",
                    "data": [
                        {"id": "document_field_id", "value": "new value"},
                        ...
                    ]
                }
            ]
        }
        """
        documents = request.data.get("documents", [])

        if not documents:
            return Responses.get_response(Responses.GENERAL.WRONG_INPUTS)

        with transaction.atomic():
            for doc_data in documents:
                document_id = doc_data.get("document_id")
                data = doc_data.get("data", [])

                if not data:
                    return Responses.get_response(Responses.GENERAL.WRONG_INPUTS)

                document = get_object_or_404(Document, id=document_id)

                # Check permissions and batch status
                if document.user != request.user:
                    return Responses.get_response(Responses.GENERAL.FORBIDDEN)
                if document.batch.status != Batch.STATUS_PENDING:
                    return Responses.get_response(Responses.GENERAL.FORBIDDEN)

                # Preload valid document_field ids
                valid_fields = set(DocumentField.objects.filter(document=document)
                                   .values_list('id', flat=True))

                # Save HITL meta info
                document.hitl_json = data
                document.hitl_by = request.user
                document.hitl_finished_at = timezone.now()
                document.save()

                # Update each field
                for field in data:
                    value_id = field['id']
                    new_value = field['value']

                    if value_id not in valid_fields:
                        return Responses.get_response(Responses.GENERAL.WRONG_INPUTS)

                    DocumentField.objects.filter(id=value_id).update(hitl_value=new_value)

        return Responses.get_response(Responses.GENERAL.OK, {
            "batch": document.batch.id,
            "checks": [
                {
                    "name": "Standard Goods Validation ",
                    "value": "standard_validation",
                    "description": "Checks whether the HS Code is subject to mandatory Iranian standards and validates standard certificates against national compliance requirements."
                },
                {
                    "name": "Weight & Quantity Validation",
                    "value": "weight_quantity",
                    "description": "Cross-checks net and gross weight, packaging details, units of measure, and item quantities across invoice, packing list, and shipping documents to detect inconsistencies."
                },
                {
                    "name": "Shipping Data Validation",
                    "value": "shipping_validation",
                    "description": "Validates Bill of Lading details, container and seal numbers, ports of loading and discharge, and vessel/voyage information across all logistics documents."
                }
            ]
        })
