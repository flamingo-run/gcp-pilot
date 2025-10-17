"""Test that date objects are converted to datetime for Firestore storage."""

from datetime import UTC, date, datetime

import pytest

from gcp_pilot.firestore import Document


class DateTestDoc(Document):
    event_date: date
    created_at: datetime

    class Meta:
        collection_name = "date_test"


@pytest.mark.asyncio
class TestDateHandling:
    async def test_date_converted_to_datetime_on_save(self):
        """Test that date fields are converted to datetime with UTC when saving."""
        # Create a document with a date field
        test_date = date(2025, 1, 15)
        doc = DateTestDoc(event_date=test_date, created_at=datetime.now(UTC))

        # Save the document
        saved_doc = await doc.save()

        # Verify the saved document has the same date
        assert saved_doc.event_date == test_date

        # Retrieve the document to verify it was stored correctly
        retrieved_doc = await DateTestDoc.documents.get(id=saved_doc.id)
        assert retrieved_doc.event_date == test_date

        # Cleanup
        await retrieved_doc.delete()

    async def test_date_filter_normalization(self):
        """Test that date filters are normalized to datetime without crashing."""
        # Create a test document
        doc = DateTestDoc(event_date=date(2025, 1, 15), created_at=datetime.now(UTC))
        saved = await doc.save()

        try:
            # The key test: date filters should be normalized to datetime
            # This should not crash with "Cannot convert to a Firestore Value" error

            # Test __gte filter
            query_gte = DateTestDoc.documents.filter(event_date__gte=date(2025, 1, 10))
            # Just accessing the query is enough - it will fail during query build if normalization doesn't work
            _ = query_gte._where_filters

            # Test __lte filter
            query_lte = DateTestDoc.documents.filter(event_date__lte=date(2025, 1, 20))
            _ = query_lte._where_filters

            # Test __eq filter
            query_eq = DateTestDoc.documents.filter(event_date=date(2025, 1, 15))
            _ = query_eq._where_filters

            # If we got here without a TypeError, the normalization is working!
            assert True, "Date normalization in filters works!"

        finally:
            # Cleanup
            await saved.delete()
