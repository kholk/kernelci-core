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

"""Test common functions for all methods."""

import datetime
import logging
import mock
import types
import unittest

from bson import (
    objectid,
    tz_util
)

from handlers.common import (
    add_created_on_date,
    calculate_date_range,
    get_aggregate_value,
    get_all_query_values,
    get_and_add_date_range,
    get_created_on_date,
    get_query_fields,
    get_query_sort,
    get_query_spec,
    get_skip_and_limit,
    update_id_fields,
    valid_token_bh,
    valid_token_general,
    valid_token_th,
    validate_token
)
from models.token import Token


class TestHandlersCommon(unittest.TestCase):

    def setUp(self):
        super(TestHandlersCommon, self).setUp()

        logging.disable(logging.CRITICAL)

        self.min_time = datetime.time(tzinfo=tz_util.utc)

    def tearDown(self):
        super(TestHandlersCommon, self).tearDown()
        logging.disable(logging.NOTSET)

    def test_update_id_fields(self):
        spec = {
            "job_id": "123344567",
            "_id": "0123456789ab0123456789ab",
            "foo": 1234,
            "defconfig_id": "0123456789ab0123456789ab"
        }
        update_id_fields(spec)
        expected = {
            "_id": objectid.ObjectId("0123456789ab0123456789ab"),
            "foo": 1234,
            "defconfig_id": objectid.ObjectId("0123456789ab0123456789ab")
        }

        self.assertDictEqual(expected, spec)

    def test_calculate_date_range_valid(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 17), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range(15))

    def test_calculate_date_range_zero(self):
        expected = datetime.datetime.combine(
            datetime.date(2014, 1, 1), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range(0))

    def test_calculate_date_range_leap(self):
        expected = datetime.datetime.combine(
            datetime.date(2012, 2, 28), self.min_time)
        start_value = datetime.date(2012, 3, 14)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range(15))

    def test_calculate_date_range_non_leap(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 2, 27), self.min_time)
        start_value = datetime.date(2013, 3, 14)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range(15))

    def test_calculate_date_range_with_string(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 31), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range("1"))

    def test_calculate_date_range_negative(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 31), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range(-1))

    def test_calculate_date_range_negative_string(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 31), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range("-1"))

    def test_calculate_date_range_out_of_range(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 27), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(
            expected,
            calculate_date_range(datetime.timedelta.max.days + 10)
        )

    def test_calculate_date_range_wrong_type(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 27), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(
            expected,
            calculate_date_range("15foo$%^%&^%&")
        )

    def test_get_aggregate_value_empty(self):
        def query_args_func(key):
            return []

        self.assertIsNone(get_aggregate_value(query_args_func))

    def test_get_aggregate_value_valid(self):
        def query_args_func(key):
            if key == "aggregate":
                return ["foo"]
            else:
                return []

        self.assertEqual(get_aggregate_value(query_args_func), "foo")

    def test_get_aggregate_value_no_list(self):
        def query_args_func(key):
            return ""

        self.assertIsNone(get_aggregate_value(query_args_func))

    def test_get_aggregate_value_multi(self):
        def query_args_func(key):
            if key == "aggregate":
                return ["foo", "bar"]
            else:
                return []

        self.assertEqual(get_aggregate_value(query_args_func), "bar")

    def test_get_query_spec(self):
        valid_keys = ["a", "b", "c", "d"]

        def query_args_func(key):
            args = {
                "a": [1, 2],
                "b": [None, 3, None],
                "c": [None, None],
            }
            return args.get(key, [])

        expected = {"a": {"$in": [1, 2]}, "b": 3}
        self.assertEqual(expected, get_query_spec(query_args_func, valid_keys))

    def test_get_query_spec_raises(self):
        valid_keys = ["a", "b"]

        def query_args_func(key):
            args = {
                "a": 1
            }
            return args.get(key, [])

        self.assertRaises(
            TypeError, get_query_spec, query_args_func, valid_keys
        )

    def test_get_query_spec_wrong_keys_list(self):
        def query_args_func(self):
            return ""

        self.assertEqual({}, get_query_spec(query_args_func, []))
        self.assertEqual({}, get_query_spec(query_args_func, ()))
        self.assertEqual({}, get_query_spec(query_args_func, ""))

    def test_get_query_fields_valid_only_field(self):
        def query_args_func(key):
            args = {
                "field": ["a", "a", "b", "c"]
            }
            return args.get(key, [])

        self.assertIsInstance(
            get_query_fields(query_args_func), types.ListType
        )
        self.assertEqual(["a", "c", "b"], get_query_fields(query_args_func))

    def test_get_query_fields_valid_only_nfield(self):
        def query_args_func(key):
            args = {
                "nfield": ["a", "a", "b"]
            }
            return args.get(key, [])

        expected = {
            "a": False,
            "b": False
        }

        self.assertIsInstance(
            get_query_fields(query_args_func), types.DictionaryType
        )
        self.assertEqual(expected, get_query_fields(query_args_func))

    def test_get_query_fields_valid_both(self):
        def query_args_func(key):
            args = {
                "field": ["a", "b", "c"],
                "nfield": ["d", "d", "e"]
            }
            return args.get(key, [])

        expected = {
            "a": True,
            "b": True,
            "c": True,
            "d": False,
            "e": False
        }

        self.assertIsInstance(
            get_query_fields(query_args_func), types.DictionaryType
        )
        self.assertEqual(expected, get_query_fields(query_args_func))

    def test_get_query_fields_both_empty(self):
        def query_args_func(key):
            return []

        self.assertIsNone(get_query_fields(query_args_func))

    def test_get_query_sort_empty(self):
        def query_args_func(key):
            return []

        self.assertIsNone(get_query_sort(query_args_func))

    def test_get_query_sort_not_sort(self):
        def query_args_func(key):
            args = {
                "sort_order": [1]
            }
            return args.get(key, [])

        self.assertIsNone(get_query_sort(query_args_func))

    def test_get_query_sort_wrong_order(self):
        def query_args_func(key):
            args = {
                "sort": ["foo"],
                "sort_order": [-10]
            }
            return args.get(key, [])

        expected = [("foo", -1)]

        self.assertEqual(expected, get_query_sort(query_args_func))

    def test_get_query_sort_wrong_single_order(self):
        def query_args_func(key):
            args = {
                "sort": ["foo"],
                "sort_order": -10
            }
            return args.get(key, [])

        expected = [("foo", -1)]

        self.assertEqual(expected, get_query_sort(query_args_func))

    def test_get_query_sort_multi_order(self):
        def query_args_func(key):
            args = {
                "sort": ["a", "b", "c"],
                "sort_order": [1, -1, 1]
            }
            return args.get(key, [])

        expected = [
            ("a", 1), ("b", 1), ("c", 1)
        ]

        self.assertEqual(expected, get_query_sort(query_args_func))

    def test_get_skip_and_limit_both_empty(self):
        def query_args_func(key):
            return []

        self.assertEqual((0, 0), get_skip_and_limit(query_args_func))

    def test_get_skip_and_limit_only_skip(self):
        def query_args_func(key):
            args = {
                "skip": [1]
            }
            return args.get(key, [])

        self.assertEqual((1, 0), get_skip_and_limit(query_args_func))

    def test_get_skip_and_limit_only_limit(self):
        def query_args_func(key):
            args = {
                "limit": [1]
            }
            return args.get(key, [])

        self.assertEqual((0, 1), get_skip_and_limit(query_args_func))

    def test_get_skip_and_limit_not_list(self):
        def query_args_func(key):
            return 1

        self.assertEqual((0, 0), get_skip_and_limit(query_args_func))

    def test_get_skip_and_limit_valid(self):
        def query_args_func(key):
            args = {
                "limit": [0, 1, 2],
                "skip": [10, 20, 30]
            }
            return args.get(key, [])

            self.assertEqual((2, 30), get_skip_and_limit(query_args_func))

    def test_get_all_query_values(self):
        def query_args_func(key):
            args = {
                "skip": [10, 20, 30],
                "sort": ["job"],
            }
            return args.get(key, [])

        valid_keys = []

        return_value = get_all_query_values(query_args_func, valid_keys)
        self.assertEqual(len(return_value), 6)

    def test_get_and_add_date_range(self):
        def query_args_func(key):
            args = {
                "date_range": 1,
            }
            return args.get(key, [])

        expected = {
            "created_on": {
                "$gte": datetime.datetime(
                    2013, 3, 13, 0, 0, tzinfo=tz_util.utc
                ),
                "$lt": datetime.datetime(
                    2013, 3, 14, 23, 59, 59, tzinfo=tz_util.utc
                )
            }
        }

        start_value = datetime.date(2013, 3, 14)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        spec = {}

        get_and_add_date_range(spec, query_args_func)
        self.assertEqual(expected, spec)

    def test_get_and_add_date_range_with_created_on(self):
        def query_args_func(key):
            args = {
                "date_range": 1,
            }
            return args.get(key, [])

        expected = {
            "created_on": {
                "$gte": datetime.datetime(
                    2014, 12, 7, 0, 0, tzinfo=tz_util.utc
                ),
                "$lt": datetime.datetime(
                    2014, 12, 8, 23, 59, 59, tzinfo=tz_util.utc
                )
            }
        }

        created_on = datetime.date(2014, 12, 8)

        spec = {}

        get_and_add_date_range(spec, query_args_func, created_on)
        self.assertEqual(expected, spec)

    def test_get_created_on_date_missing(self):
        def query_args_func(key):
            args = {}
            return args.get(key, [])

        self.assertIsNone(get_created_on_date(query_args_func))

    def test_get_created_on_date_wrong_type(self):
        def query_args_func(key):
            args = {
                "created_on": 2014
            }
            return args.get(key, [])

        self.assertIsNone(get_created_on_date(query_args_func))

    def test_get_created_on_date_valid_format_1(self):
        def query_args_func(key):
            args = {
                "created_on": "2014-12-12"
            }
            return args.get(key, [])

        expected = datetime.date(2014, 12, 12)
        self.assertEqual(expected, get_created_on_date(query_args_func))

    def test_get_created_on_date_valid_format_2(self):
        def query_args_func(key):
            args = {
                "created_on": "20141212"
            }
            return args.get(key, [])

        expected = datetime.date(2014, 12, 12)
        self.assertEqual(expected, get_created_on_date(query_args_func))

    def test_get_created_on_date_wrong_format(self):
        def query_args_func(key):
            args = {
                "created_on": "201412121243"
            }
            return args.get(key, [])

        self.assertIsNone(get_created_on_date(query_args_func))

    def test_get_created_on_date_multiple(self):
        def query_args_func(key):
            args = {
                "created_on": ["20141211", "20141110"]
            }
            return args.get(key, [])

        expected = datetime.date(2014, 11, 10)
        self.assertEqual(expected, get_created_on_date(query_args_func))

    def test_add_created_on_date_valid(self):
        created_on = datetime.date(2014, 12, 11)
        spec = {"foo": "bar"}

        expected = {
            "foo": "bar",
            "created_on": {
                "$gte": datetime.datetime(
                    2014, 12, 11, 0, 0, tzinfo=tz_util.utc),
                "$lt": datetime.datetime(
                    2014, 12, 11, 23, 59, 59, tzinfo=tz_util.utc)
            }
        }

        add_created_on_date(spec, created_on)
        self.assertDictEqual(expected, spec)

    def test_add_created_on_date_wrong(self):
        spec = {"foo": "bar", "created_on": "foo"}
        expected = {"foo": "bar"}

        add_created_on_date(spec, None)
        self.assertDictEqual(expected, spec)

        add_created_on_date(spec, 12345)
        self.assertDictEqual(expected, spec)

        add_created_on_date(spec, {})
        self.assertDictEqual(expected, spec)

        add_created_on_date(spec, [1234])
        self.assertDictEqual(expected, spec)

    @mock.patch("models.token.Token", spec=True)
    def test_valid_token_general_true(self, mock_class):
        token = mock_class.return_value

        self.assertIsInstance(token, Token)

        token.is_get_token = True
        token.is_post_token = True
        token.is_delete_token = True
        token.is_lab_token = False

        self.assertFalse(token.is_lab_token)
        self.assertTrue(valid_token_general(token, "GET"))
        self.assertTrue(valid_token_general(token, "POST"))
        self.assertTrue(valid_token_general(token, "DELETE"))

    @mock.patch("models.token.Token", spec=True)
    def test_valid_token_general_lab_token(self, mock_class):
        token = mock_class.return_value

        self.assertIsInstance(token, Token)

        token.is_get_token = False
        token.is_post_token = True
        token.is_delete_token = True
        token.is_lab_token = True

        self.assertTrue(token.is_lab_token)
        self.assertFalse(valid_token_general(token, "GET"))
        self.assertTrue(valid_token_general(token, "POST"))
        self.assertFalse(valid_token_general(token, "DELETE"))

    @mock.patch("models.token.Token", spec=True)
    def test_valid_token_general_false(self, mock_class):
        token = mock_class.return_value

        self.assertIsInstance(token, Token)

        token.is_get_token = False
        token.is_post_token = False
        token.is_delete_token = False

        self.assertFalse(valid_token_general(token, "GET"))
        self.assertFalse(valid_token_general(token, "POST"))
        self.assertFalse(valid_token_general(token, "DELETE"))

    @mock.patch("models.token.Token", spec=True)
    def test_valid_token_th_true(self, mock_class):
        token = mock_class.return_value

        self.assertIsInstance(token, Token)

        token.is_admin = True
        token.is_superuser = False

        self.assertTrue(valid_token_th(token, "GET"))
        self.assertTrue(valid_token_th(token, "POST"))
        self.assertTrue(valid_token_th(token, "DELETE"))

        token.is_admin = False
        token.is_superuser = True

        self.assertTrue(valid_token_th(token, "GET"))

    @mock.patch("models.token.Token", spec=True)
    def test_valid_token_th_false(self, mock_class):
        token = mock_class.return_value

        self.assertIsInstance(token, Token)

        token.is_admin = False
        token.is_superuser = False

        self.assertFalse(valid_token_th(token, "GET"))
        self.assertFalse(valid_token_th(token, "POST"))
        self.assertFalse(valid_token_th(token, "DELETE"))

        token.is_admin = False
        token.is_superuser = True

        self.assertFalse(valid_token_th(token, "POST"))
        self.assertFalse(valid_token_th(token, "DELETE"))

    @mock.patch("models.token.Token.from_json")
    def test_validate_token_wrong_class(self, mock_from_json):
        mock_from_json.return_value = mock.Mock()

        self.assertFalse(
            validate_token("foo", "GET", None, None)
        )
        self.assertFalse(
            validate_token(None, "GET", None, None)
        )

    @mock.patch("models.token.Token.from_json")
    def test_validate_token_true(self, mock_from_json):
        token = Token()

        mock_from_json.return_value = token
        validate_func = mock.Mock()
        validate_func.side_effect = [True, True]

        token.is_ip_restricted = False

        self.assertTrue(
            validate_token(token, "GET", None, validate_func)
        )

        token.is_ip_restricted = True
        token.ip_address = "127.0.0.1"

        self.assertTrue(
            validate_token(token, "GET", "127.0.0.1", validate_func)
        )

    @mock.patch("models.token.Token.from_json")
    def test_validate_token_false(self, mock_from_json):
        token = Token()

        mock_from_json.return_value = token
        validate_func = mock.Mock()
        validate_func.side_effect = [False, True, False]

        token.is_ip_restricted = True

        self.assertFalse(
            validate_token(token, "GET", None, validate_func)
        )

        token.is_ip_restricted = True
        token.ip_address = "127.1.1.1"

        self.assertFalse(
            validate_token(token, "GET", "127.0.0.1", validate_func)
        )

        token.is_ip_restricted = False

        self.assertFalse(
            validate_token(token, "GET", None, validate_func)
        )

    @mock.patch("models.token.Token", spec=True)
    def test_valid_token_bh(self, mock_class):
        token = mock_class.return_value

        self.assertIsInstance(token, Token)

        token.is_get_token = True
        token.is_post_token = True
        token.is_delete_token = True

        self.assertTrue(valid_token_bh(token, "GET"))
        self.assertTrue(valid_token_bh(token, "POST"))
        self.assertTrue(valid_token_bh(token, "DELETE"))

        token.is_get_token = False
        token.is_post_token = False
        token.is_delete_token = False

        self.assertFalse(valid_token_bh(token, "GET"))
        self.assertFalse(valid_token_bh(token, "POST"))
        self.assertFalse(valid_token_bh(token, "DELETE"))
