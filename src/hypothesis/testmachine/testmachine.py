# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, unicode_literals

from unittest import TestCase
from hypothesis.internal.utils.hashitanyway import EverythingDict
from hypothesis.conventions import UniqueIdentifier
from hypothesis.internal.utils.fixers import nice_string
from hypothesis.testmachine.languages import LanguageTable
from hypothesis.internal.specmapper import MissingSpecification


class VarStack(object):
    pass


NoLanguage = UniqueIdentifier('NoLanguage')


class ValidationError(Exception):
    pass


class MachineDefinition(object):
    def __init__(self, language_table=None):
        self.language_table = language_table or LanguageTable.default()
        self.varstacks = EverythingDict()
        self.targetting_languages = EverythingDict()
        self.extra_languages = []

    def install_varstack(self, description):
        if description not in self.varstacks:
            self.varstacks[description] = VarStack()
            try:
                language = self.language_table.specification_for(description)
            except MissingSpecification:
                language = NoLanguage

            if language != NoLanguage:
                self.targetting_languages[description] = language
                language.install(self)
        return self.varstacks[description]

    def varstack_names(self):
        for k in self.varstacks:
            yield k

    def language(self, description):
        return self.targetting_languages.setdefault(description, NoLanguage)

    def add_targetting_language(self, description, language):
        if self.language(description) == NoLanguage:
            self.targetting_languages[description] = language
        else:
            self.targetting_languages[description] |= language

    def add_language(self, language):
        self.extra_languages.append(language)

    def validate(self):
        missing_varstacks = [
            k
            for k in self.varstacks
            if self.language(k) == NoLanguage
        ]

        if missing_varstacks:
            if len(missing_varstacks) > 1:
                raise ValidationError(
                    "No language defined for descriptions %s" % ', '.join(
                        map(nice_string, missing_varstacks)
                    ))
            else:
                raise ValidationError(
                    "No language defined for description %s" % (
                        nice_string(missing_varstacks[0])
                    ))


def produces(*args, **kwargs):
    return lambda f: f


class TestMachine(TestCase):
    @classmethod
    def validate(self):
        pass

    @classmethod
    def add_rule(self):
        pass
