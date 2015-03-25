# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals

from hypothesis.extra.django import TestCase
from hypothesis.extra.django.models import ModelNotSupported
from hypothesis import given
from toystore.models import Company, Customer, CouldBeCharming, Charming, \
    Shop, ConstrainedChoices

from django.contrib.auth.models import User


class TestGetsBasicModels(TestCase):

    @given(User)
    def test_can_user(self, user):
        assert isinstance(user, User)

    @given(ConstrainedChoices)
    def test_genre(self, choices):
        self.assertIn(choices.genre, ('', 'c', 'w'))
        self.assertIn(choices.stuff, ('so', 'wat'))

    @given(Company)
    def test_is_company(self, company):
        self.assertIsInstance(company, Company)
        self.assertIsNotNone(company.pk)

    @given(Customer)
    def test_is_customer(self, customer):
        self.assertIsInstance(customer, Customer)
        self.assertIsNotNone(customer.pk)
        self.assertIsNotNone(customer.email)
        assert customer.age >= 0

    @given(Shop)
    def test_can_create_dependent_models(self, shop):
        self.assertIsInstance(shop, Shop)
        self.assertIsInstance(shop.company, Company)

    @given(CouldBeCharming)
    def test_is_not_charming(self, not_charming):
        self.assertIsInstance(not_charming, CouldBeCharming)
        self.assertIsNotNone(not_charming.pk)
        self.assertIsNone(not_charming.charm)

    @given(Charming)
    def charm_me(self, charm):
        pass

    def test_given_unsupported_errors(self):
        with self.assertRaises(ModelNotSupported):
            TestGetsBasicModels('charm_me').charm_me()
