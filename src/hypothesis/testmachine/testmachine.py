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
from hypothesis.internal.utils.fixers import nice_string
from hypothesis.testmachine.languages import (
    LanguageTable, EmptyLanguage, SingleFunctionLanguage)
from hypothesis.internal.specmapper import MissingSpecification
from functools import reduce
from operator import or_
from inspect import getmembers
from hypothesis.conventions import not_set


class LabelledValue(object):
    def __init__(self, description, varname, value):
        self.description = description
        self.varname = varname
        self.value = value

    def __repr__(self):
        return "LabelledValue(%s, %s, %s)" % (
            nice_string(self.description), nice_string(self.varname),
            nice_string(self.value),
        )


class VarStack(object):
    def __init__(self, description):
        self.description = description
        self.next_label = 1
        self.stack = []

    def __len__(self):
        return len(self.stack)

    def push(self, value):
        self.stack.append(LabelledValue(
            self.description, self.next_label, value
        ))
        self.next_label += 1

    def read(self, index):
        if index >= len(self.stack):
            raise IndexError(
                "Index %d out of range for stack height %d" % (
                    index, len(self.stack)
                ))
        return self.stack[-1 - index]


class ValidationError(Exception):
    pass


class RunContext(object):
    def __init__(self, varstacks):
        self.varstacks = EverythingDict()
        for v in varstacks:
            self.varstacks[v] = VarStack(v)

    def height(self, description):
        return len(self.varstacks[description])

    def push(self, description, value):
        self.varstacks[description].push(value)

    def read(self, argspec):
        heights = EverythingDict()

        def read_single(v):
            stack = self.varstacks[v]
            last_height = heights.setdefault(v, -1)
            height = last_height + 1
            heights[v] = height
            return stack.read(height)

        args = []
        kwargs = {}
        for v in argspec.args:
            args.append(read_single(v))
        for k, v in argspec.kwargs.items():
            kwargs[k] = read_single(v)
        return tuple(args), kwargs

    def could_read(self, argspec):
        try:
            self.read(argspec)
            return True
        except IndexError:
            return False


class MachineDefinition(object):
    def __init__(self, language_table=None):
        self.language_table = language_table or LanguageTable.default()
        self.targetting_languages = EverythingDict()
        self.extra_languages = []

    def install_varstack(self, description):
        if description not in self.targetting_languages:
            try:
                language = self.language_table.specification_for(description)
            except MissingSpecification:
                self.targetting_languages[description] = EmptyLanguage()
                return

            self.targetting_languages[description] = language
            language.install(self)

    def varstack_names(self):
        for k in self.targetting_languages:
            yield k

    def new_run_context(self):
        return RunContext(self.varstack_names())

    def build_language(self):
        self.validate()
        empty = EmptyLanguage()
        result = reduce(
            or_, self.targetting_languages.values(), empty
        ) | reduce(
            or_, self.extra_languages, empty
        )
        assert not result.empty()
        return result

    def build_program(self, random):
        language = self.build_language()
        context = self.new_run_context()
        parameter = language.draw_parameter(random)
        while True:
            op = language.draw_operation(
                random=random, runcontext=context, parameter_value=parameter
            )
            op.simulate(context)
            yield op

    def run_program(self, program):
        context = self.new_run_context()
        for p in program:
            p.run(context)
        return context

    def language(self, description):
        return self.targetting_languages.setdefault(
            description, EmptyLanguage())

    def add_targetting_language(self, description, language):
        self.targetting_languages[description] = (
            self.language(description) | language)

    def add_language(self, language):
        self.extra_languages.append(language)

    def validate(self):
        if not (self.targetting_languages or self.extra_languages):
            raise ValidationError("Empty machine")

        missing_varstacks = [
            k
            for k in self.targetting_languages
            if self.language(k).empty()
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


def produces(target):
    def accept(f):
        f.hypothesis_produces = target
        f.is_hypothesis = True
        return f
    return accept


class TestMachine(TestCase):
    def build_machine_definition(self):
        md = MachineDefinition()
        for name, value in getmembers(self):
            unbound = unbind_function(value)
            target = getattr(unbound, 'hypothesis_produces', not_set)
            given = getattr(unbound, 'hypothesis_given', ((), ()))
            if hasattr(value, 'hypothesis_given'):
                md.install_varstack(value.hypothesis_given[0])
                md.install_varstack(value.hypothesis_given[1])
                language = SingleFunctionLanguage(
                    target=target,
                    function=apply,
                )
                md.add_targetting_language()
                    
        return md

    def validate(self):
        self.build_machine_definition().validate()

    @classmethod
    def add_rule(self, rule):
        pass
