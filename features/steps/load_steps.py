######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
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
######################################################################

"""
Product Steps

Steps file for products.feature

For information on Waiting until elements are present in the HTML see:
    https://selenium-python.readthedocs.io/waits.html
"""

import requests
from behave import given, when, then
import os
import copy
import logging
from decimal import Decimal
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

# HTTP Return Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204

API_ROOT_URL = "/products"

logger = logging.getLogger("test_routes")  # remove ambiguity
# and allow filtering with NOSE option --debug=
logger.setLevel(logging.DEBUG)

@given('the following products')
def step_impl(context):
    """ Delete all Products and load new ones """
    #
    # List all of the products and delete them one by one
    #
    rest_endpoint = f"{context.base_url}{API_ROOT_URL}"
    logger.info(f"endpoint: {rest_endpoint}")
    context.response = requests.get(rest_endpoint)
    assert(context.response.status_code == HTTP_200_OK)
    for product in context.response.json():
        context.response = requests.delete(f"{rest_endpoint}/{product['id']}")
        assert(context.response.status_code == HTTP_204_NO_CONTENT)
    #
    # load the database with new products
    #
    for row in context.table:
        #
        # ADD YOUR CODE HERE TO CREATE PRODUCTS VIA THE REST API
        #
        tuple_product = {
            "name": row['name'],
            "description": row['description'],
            "price": row['price'],
            "available": row['available'] in ['True', 'true', '1'],
            "category": row['category']
        }
        logging.debug("Test Product: %s", tuple_product)
        response = requests.post(rest_endpoint, json=tuple_product)
        assert response.status_code == status.HTTP_201_CREATED
