from django.db import models
from django.contrib.auth.models import User


# ---------------------------------------------------------
# Customer
# ---------------------------------------------------------
class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------
# Document Type
# ---------------------------------------------------------
class DocumentType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------
# Batch
# ---------------------------------------------------------
class Batch(models.Model):
    STATUS_PENDING = 'p'
    STATUS_DONE = 'd'
    STATUS_CHOICES = [(STATUS_PENDING, 'Pending'), (STATUS_DONE, 'Done')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    docs_path = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Batch {self.id}"


# ---------------------------------------------------------
# Document
# ---------------------------------------------------------
class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, null=True, blank=True)
    type = models.ForeignKey(DocumentType, on_delete=models.SET_NULL, null=True, blank=True)

    # OCR fields
    ocr_raw = models.TextField(null=True, blank=True)
    ocr_normalized = models.TextField(null=True, blank=True)
    ocr_bounding_boxes = models.TextField(null=True, blank=True)
    ocr_confidence = models.FloatField(null=True, blank=True)
    ocr_method = models.CharField(max_length=100, null=True, blank=True)
    ocr_started_at = models.DateTimeField(null=True, blank=True)
    ocr_finished_at = models.DateTimeField(null=True, blank=True)

    # Normalization fields
    normalized_json = models.JSONField(null=True, blank=True)
    normalized_method = models.CharField(max_length=100, null=True, blank=True)
    normalized_finished_at = models.DateTimeField(null=True, blank=True)

    # HITL fields
    hitl_json = models.JSONField(null=True, blank=True)
    hitl_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True, related_name='hitl_by'
    )
    hitl_finished_at = models.DateTimeField(null=True, blank=True)

    # Document status
    status = models.CharField(max_length=50, default="uploaded")

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document {self.id}"


# ---------------------------------------------------------
# Field (schema definition for a document type)
# ---------------------------------------------------------
class Field(models.Model):
    group = models.CharField(max_length=255, blank=True, null=True, default=None)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("group", "name")
        verbose_name = "Field"
        verbose_name_plural = "Fields"

    def __str__(self):
        return f"{self.group} - {self.name}"


# ---------------------------------------------------------
# Document Field (actual values per document)
# ---------------------------------------------------------
class DocumentField(models.Model):
    document = models.ForeignKey(Document, on_delete=models.PROTECT)
    field = models.ForeignKey(Field, on_delete=models.PROTECT)
    normalized_value = models.TextField(null=True, blank=True)
    hitl_value = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("document", "field")

    def __str__(self):
        return f"{self.document.id} - {self.field.name}"
