# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals

from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=100, unique=True)


class Shop(models.Model):
    name = models.CharField(max_length=100)
    company = models.ForeignKey(Company)


class CharmField(models.Field):

    def db_type(self, connection):
        return 'char(1)'


class Customer(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    gender = models.CharField(max_length=50, null=True)
    age = models.PositiveIntegerField()
    birthday = models.DateTimeField()


class Charming(models.Model):
    charm = CharmField()


class CouldBeCharming(models.Model):
    charm = CharmField(null=True)


class ConstrainedChoices(models.Model):
    MUSIC_CHOICE = (('c', 'Country'), ('w', 'Western'))

    WEIRD_CHOICES = (
        ('Useful', (('wat', 'Ever'),)),
        ('Not useful', (('so', 'there'),)),
    )

    genre = models.CharField(choices=MUSIC_CHOICE, max_length=2)
    stuff = models.CharField(choices=WEIRD_CHOICES, max_length=11, blank=False)

    spooniness = models.PositiveSmallIntegerField()
