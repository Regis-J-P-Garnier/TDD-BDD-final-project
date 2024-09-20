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
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import copy
import logging
from decimal import Decimal
from unittest import TestCase
from urllib.parse import quote_plus
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"

logger = logging.getLogger("test_routes")  # remove ambiguity
# and allow filtering with NOSE option --debug=
logger.setLevel(logging.DEBUG)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        
    ######################################################################
    # R E A D   A   P R O D U C T
    ######################################################################
    def test_get_product(self):
        """It should read a Product [EX3-T1]"""
        test_product = self._create_products()[0]  # [1]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")  # [2]
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # [3]
        response_product = response.get_json()  # [4]
        print(response_product)
        print(test_product)
        self.assertEqual(response_product["name"], test_product.name)  # [5]
        self.assertEqual(response_product["description"], test_product.description)  # [5]
        self.assertEqual(Decimal(response_product["price"]), test_product.price)  # [5]
        self.assertEqual(response_product["available"], test_product.available)  # [5]
        self.assertEqual(response_product["category"], test_product.category.name)  # [5]
        
    def test_get_product_not_found(self):
        """It should fail in getting a not existent Product (by id) [EX3-T2]"""
        invalid_product_id = 0   # [1]
        response = self.client.get(f"{BASE_URL}/{invalid_product_id}")  # [1]
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # [2]
    
    ######################################################################
    # U P D A T E   A   P R O D U C T
    ######################################################################        
    def test_put_update_product(self):
        """It should update a Product [EX3]"""
        # CREATE a PRODUCT (from dedicated test)
        product = ProductFactory()
        response = self.client.post(BASE_URL, json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product.id=response.get_json()["id"]
        # UPDATE a PRODUCT
        product_origin_description = copy.copy(product.description)
        product_fake_description = copy.copy(ProductFactory().description)
        self.assertNotEqual(product_fake_description, product_origin_description)
        product.description = product_fake_description
        response = self.client.put(f"{BASE_URL}/{product.id}", json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # COMPARE : all except DESCRIPTIONS equal origin product
        response_product = response.get_json()
        self.assertEqual(response_product["name"], product.name)
        self.assertEqual(Decimal(response_product["price"]), product.price)
        self.assertEqual(response_product["available"], product.available)
        self.assertEqual(response_product["category"], product.category.name)
        # COMPARE : DESCRIPTIONS equal updated product
        self.assertNotEqual(response_product["description"], product_origin_description)
        self.assertEqual(response_product["description"], product_fake_description)
    
    def test_put_update_not_found(self):
        """It should fail in updating a not existent Product [EX3]"""
        invalid_product_id = 0
        product = ProductFactory()
        product.id = invalid_product_id
        response = self.client.put(f"{BASE_URL}/{invalid_product_id}", json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)   
    
    ######################################################################
    # D E L E T E   A   P R O D U C T
    ######################################################################
    def test_delete_product(self):
        """It should delete a Product [EX3]"""
        # CREATE some PRODUCTS
        number_to_create = 5  # >0
        product_created_ids = []
        for _ in range(number_to_create):  # for number of Products to create
            product = ProductFactory()
            response = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            product_created_ids.append(response.get_json()["id"]) 
        # DELETE a PRODUCT
        for id in product_created_ids: # for all created Products
            response = self.client.get(f"{BASE_URL}/{id}")  # not deleted Product id
            self.assertEqual(response.status_code, status.HTTP_200_OK)  # should exist  
        response = self.client.delete(f"{BASE_URL}/{str(product_created_ids[-1])}") # TODO : better a random to select an id
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # EXPECT number_to_create-1 Products REMAINING in DB
        for id in product_created_ids[:-1]: # for all created Products except deleted
            response = self.client.get(f"{BASE_URL}/{id}")  # not deleted Product id
            self.assertEqual(response.status_code, status.HTTP_200_OK)  # should exist
        for id in product_created_ids[-1:]: # for deleted Product
            response = self.client.get(f"{BASE_URL}/{id}")  # deleted Product id
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # should not exist                
    
    def test_delete_not_found(self):
        """It should fail in deleting a not existent Product [EX3]"""
        invalid_product_id = 0
        product = ProductFactory()
        product.id = invalid_product_id
        response = self.client.delete(f"{BASE_URL}/{invalid_product_id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)       
    
    ######################################################################
    # L I S T   P R O D U C T S
    ######################################################################
    def test_list_all_products(self):
        """It should list all Products [EX3]"""
        # CREATE some PRODUCTS
        number_to_create = 5  # >0
        for _ in range(number_to_create):  # for number of Products to create
            product = ProductFactory()
            response = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # COUNT PRODUCTS
        response = self.client.get(BASE_URL)
        self.assertEqual(len(response.get_json()), 5)

    def test_list_by_name_products(self):
        """It should list Products by name [EX3]"""
        # CREATE some PRODUCTS
        number_to_create = 5  # >0
        product_names = []
        for _ in range(number_to_create):  # for number of Products to create
            product = ProductFactory()
            response = self.client.post(BASE_URL, json=product.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            product_names.append(product.name)
        # COUNT PRODUCTS with SAME NAME    
        p0_name = product_names[0]
        p0_name_counter=0   
        for product_name in product_names:
            if product_name == p0_name:
               p0_name_counter +=1
        # RETRIEVE PRODUCTS with SAME NAME
        query_string_quoted=f"name={quote_plus(p0_name)}"
        response = self.client.get(BASE_URL, query_string=query_string_quoted)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # COMPARE COUNT PRODUCTS with SAME NAME 
        logger.error(response.get_json())
        logger.error(len(response.get_json()))
        self.assertEqual(len(response.get_json()), p0_name_counter)
    
    def test_list_by_unknown_name_products(self):
        """It should list but with no Product of the name, return empty data [EX3]"""
        product = ProductFactory()
        response = self.client.post(BASE_URL, json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
         # RETRIEVE PRODUCTS with NOT EXISTING NAME
        query_attribute_string_raw="name=DUMMY_NAME"
        query_string_quoted=f"name={quote_plus(query_attribute_string_raw)}"
        response = self.client.get(BASE_URL, query_string=query_string_quoted)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # COMPARE COUNT PRODUCTS with NOT EXISTING NAME 
        self.assertEqual(len(response.get_json()), 0)

    def test_list_by_name_in_empty_db(self):
        """It should list but with no Product of the name, return empty data [EX3]"""
         # RETRIEVE PRODUCTS with NOT EXISTING NAME
        query_attribute_string_raw="name=DUMMY_NAME"
        query_string_quoted=f"name={quote_plus(query_attribute_string_raw)}"
        response = self.client.get(BASE_URL, query_string=query_string_quoted)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # COMPARE COUNT PRODUCTS with NOT EXISTING NAME 
        self.assertEqual(len(response.get_json()), 0)
            
    def test_future(self):
        pass
        if(False):
            def test_list_by_category_products(self):
                """It should list Products by category [EX3]"""
                # CREATE some PRODUCTS
                number_to_create = 5  # >0
                product_categories = []
                for _ in range(number_to_create):  # for number of Products to create
                    product = ProductFactory()
                    response = self.client.post(BASE_URL, json=product.serialize())
                    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                    product_categories.append(product.category)
                # COUNT PRODUCTS with SAME CATEGORIES    
                p0_category = product_categories[0]
                p0_category_counter=0   
                for product_category in product_categories:
                    if product_category == p0_category:
                        p0_category_counter +=1
                # RETRIEVE PRODUCTS with SAME CATEGORIES
                query_string_quoted=f"category={quote_plus(p0_category)}"
                response = self.client.get(BASE_URL, query_string=query_string_quoted)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                # COMPARE COUNT PRODUCTS with SAME CATEGORIES 
                self.assertEqual(len(response.get_json()), p0_category_counter)

            def test_list_by_unknown_category_products(self):
                """It should list but with no Product of the category, return empty data [EX3]"""
                product = ProductFactory()
                response = self.client.post(BASE_URL, json=product.serialize())
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                # RETRIEVE PRODUCTS with NOT EXISTING CATEGORY
                query_attribute_string_raw="category=DUMMY_CATEGORY"
                query_string_quoted=f"category={quote_plus(query_attribute_string_raw)}"
                response = self.client.get(BASE_URL, query_string=query_string_quoted)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                # COMPARE COUNT PRODUCTS with NOT EXISTING CATEGORY 
                self.assertEqual(len(response.get_json()), 0)

            def test_list_by_category_in_empty_db(self):
                """It should list but with no Product of the category, return empty data [EX3]"""
                # RETRIEVE PRODUCTS with NOT EXISTING CATEGORY
                query_attribute_string_raw="category=DUMMY_CATEGORY"
                query_string_quoted=f"category={quote_plus(query_attribute_string_raw)}"
                response = self.client.get(BASE_URL, query_string=query_string_quoted)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                # COMPARE COUNT PRODUCTS with NOT EXISTING CATEGORY 
                self.assertEqual(len(response.get_json()), 0)  
    
    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
