# Copyright (C) 2014 Linaro Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import types
import unittest

from bson import (
    json_util,
)

from models.base import BaseDocument
from models.subscription import SubscriptionDocument


class TestSubscriptionModel(unittest.TestCase):

    def test_subscription_document_emails_attribute(self):
        sub_doc = SubscriptionDocument('sub', 'job')
        self.assertIsInstance(sub_doc.emails, types.ListType)
        self.assertItemsEqual([], sub_doc.emails)

    def test_subscription_document_emails_attribute_set(self):
        sub_doc = SubscriptionDocument('sub', 'job')

        self.assertIsInstance(sub_doc.emails, types.ListType)
        self.assertNotIsInstance(sub_doc.emails, types.StringTypes)

    def test_subscription_document_emails_extended(self):
        sub_doc = SubscriptionDocument('sub', 'job')
        sub_doc.emails = 'email2'

        self.assertIsInstance(sub_doc.emails, types.ListType)
        self.assertEquals(['email2'], sub_doc.emails)

    def test_subscription_document_emails_setter_str(self):
        sub_doc = SubscriptionDocument('sub', 'job')
        sub_doc.emails = 'an_email'

        self.assertIsInstance(sub_doc.emails, types.ListType)
        self.assertEqual(['an_email'], sub_doc.emails)

    def test_subscription_document_emails_setter_tuple(self):
        sub_doc = SubscriptionDocument('sub', 'job')
        sub_doc.emails = ('an_email', 'another_email')

        self.assertIsInstance(sub_doc.emails, types.ListType)
        self.assertEqual(['an_email', 'another_email'], sub_doc.emails)

    def test_subscription_document_to_dict(self):
        expected = dict(_id='sub', emails=[], job_id='job', created_on=None)
        sub_doc = SubscriptionDocument('sub', 'job')

        self.assertEqual(expected, sub_doc.to_dict())

    def test_subscription_document_to_json(self):
        expected = (
            '{"created_on": null, "_id": "sub", "emails": [], "job_id": "job"}'
        )
        sub_doc = SubscriptionDocument('sub', 'job')
        self.assertEqual(expected, sub_doc.to_json())

    def test_subscription_document_from_json(self):
        json_str = (
            '{"_id": "sub", "emails": [], "job_id": "job"}'
        )
        json_obj = json_util.loads(json_str)

        sub_doc = SubscriptionDocument.from_json(json_obj)

        self.assertIsInstance(sub_doc, SubscriptionDocument)
        self.assertIsInstance(sub_doc, BaseDocument)

        self.assertEqual(sub_doc.name, 'sub')
        self.assertEqual(sub_doc.job_id, 'job')
        self.assertIsInstance(sub_doc.emails, types.ListType)

    def test_subscription_document_from_json_with_emails(self):
        json_obj = dict(
            _id='sub',
            job_id='job',
            emails=['a@example.org', 'b@example.org'],
            created_on=None,
        )

        sub_doc = SubscriptionDocument.from_json(json_obj)

        self.assertIsInstance(sub_doc.emails, types.ListType)
        self.assertEqual(len(sub_doc.emails), 2)

    def test_subscription_doc_from_json_string(self):
        json_obj = dict(
            _id='sub',
            job_id='job',
            emails=['a@example.org', 'b@example.org'],
            created_on=None,
        )

        json_string = json_util.dumps(json_obj)
        sub_doc = SubscriptionDocument.from_json(json_string)

        self.assertIsInstance(sub_doc, SubscriptionDocument)
        self.assertIsInstance(sub_doc.emails, types.ListType)
