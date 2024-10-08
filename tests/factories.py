# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=too-few-public-methods

"""
Test Factory to make fake objects for testing
"""
from random import random
import string
import factory
from factory import Sequence
from factory.fuzzy import FuzzyChoice, FuzzyDecimal, FuzzyText
from service.models import Product, Category


class CONST:
    """Add some parameters to the class"""
    BOOL = [True, False]

    PRODUCT_NAMES = [
        "Hat",      "Pants",    "Shirt",    "Apple",    "Banana",   "Pots",
        "Towels",   "Ford",     "Chevy",    "Hammer",   "Wrench"
    ]

    PRODUCT_CATEGORIES = [
        Category.UNKNOWN,       Category.CLOTHS,        Category.FOOD,
        Category.HOUSEWARES,    Category.AUTOMOTIVE,    Category.TOOLS,
    ]  # TODO: should have a better way from ENUM to LIST


class ProductFactory(factory.Factory):
    """Creates fake products for testing"""

    class Meta:
        """Maps factory to data model"""
        model = Product

    # Add code to create Fake Products
    id = Sequence(lambda n: n)
    name = FuzzyChoice(CONST.PRODUCT_NAMES)  # max 100
    description = FuzzyText(length=int(1+249*random()),
                            chars=string.ascii_letters,
                            prefix='')  # instead of Fake or FakerFactory.create().sentence()[:250]#max 250
    price = FuzzyDecimal(0.5, 2000, precision=2)
    available = FuzzyChoice(CONST.BOOL)  # bool
    category = FuzzyChoice(CONST.PRODUCT_CATEGORIES)  # FuzzyInteger(0,6) ?
