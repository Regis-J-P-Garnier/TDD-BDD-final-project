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

# pylint: disable=too-few-public-methods
# pylint: disable=too many leading '#' for block comment

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory

### ADDED ###
import copy

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

logger = logging.getLogger("test_models")   # remove ambiguity 
                                            # and allow filtering with NOSE option --debug=
logger.setLevel(logging.DEBUG)                                            


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)
        
    ### ADDED TEST CASES ###
    def test_read_a_product(self):
        """It should read a product from the database   [EX2]"""
        # Set the ID of the product object to None and then call the create() method on the product.
        p_faked = ProductFactory()
        p_faked.id = None
        p_faked.create()
        # Assert that the ID of the product object is not None after calling the create() method.
        self.assertIsNotNone(p_faked.id)
        # Fetch the product back from the system using the product ID and store it in found_product
        p_found = Product.find(p_faked.id)
        # Assert that the properties of the found_product match with the properties of the original product object, such as id, name, description and price.        
        self.assertEqual(p_found.id,          p_faked.id)
        self.assertEqual(p_found.name,        p_faked.name)
        self.assertEqual(p_found.description, p_faked.description)
        self.assertEqual(p_found.price,       p_faked.price)
    
    def test_update_a_product(self):
        """It should update a product from the database   [EX2]"""
        ### CREATE THE PRODUCT (from test_add_a_product) ###
        p_origin = ProductFactory() # [1]
        logger.info(f"original created product : {str(p_origin)}") # [2]
        p_origin.id = None # [3]
        p_origin.create()
        self.assertIsNotNone(p_origin.id)
        p_found_origin = Product.find(p_origin.id) # different object
        self.assertEqual(p_found_origin, p_origin) # EXPECT unchanged = same object in the ORM
        logger.info(f"original found product : {str(p_found_origin)}") # [4]
        
        ### UPDATE THE PRODUCT ###
        description_origin = copy.copy(p_found_origin.description)
        description_fake = copy.copy(ProductFactory().description) # new description value produced (P(X) -> 0 same desc. string than previous fake object)
        # update description only
        p_found_origin.description = description_fake
        p_found_origin.update() # [5]
        # search again
        p_found_updated = Product.find(p_found_origin.id)
        # compare before/after update
        
        # EXPECT unchanged
        self.assertEqual(   p_found_updated.id,      p_origin.id) # [8]
        self.assertEqual(   p_found_updated.name,    p_origin.name)
        self.assertEqual(   p_found_updated.price,   p_origin.price)
        
        # EXPECT changed
        self.assertNotEqual(p_found_updated.description,     description_origin) # [8]
        self.assertEqual(   p_found_updated.description,     description_fake) # [8]
        
        # EXPECT update and not add
        products = Product.all()
        self.assertEqual(len(products), 1) # [7]        
        self.assertEqual(products[0].id, p_found_origin.id)
        self.assertEqual(products[0].description, description_fake)
        
    def test_delete_a_product(self):
        """It should delete a product from the database   [EX2]"""
        # CREATE AN OBJECT & EXPECT 1 OBJECT IN DB
        product = ProductFactory()                        # [1]
        product.create()                                  # [1]
        products_after_created = Product.all()            # [2] 
        self.assertEqual(len(products_after_created), 1)  # [2]           
        # DELETE AN OBJECT & EXPECT 0 OBJECT IN DB         
        product.delete()                                  # [3]
        products_after_deleted = Product.all()            # [4] 
        self.assertEqual(len(products_after_deleted), 0)  # [4]

    def test_list_all_products(self):
        """It should list all products from the database   [EX2]"""
        NUMB_CREATE = 5
        # EXPECT 0 OBJECT IN DB         
        products_origin = Product.all()                      # [1]
        self.assertEqual(len(products_origin), 0)            # [1]
        # ADD PRODUCTS
        for _ in range(NUMB_CREATE):                         # [2]
            ProductFactory().create()                        # [2]
        # VALID CREATION    
        products_created = Product.all()                     # [3]
        self.assertEqual(len(products_created), NUMB_CREATE) # [3]
    
    def test_find_a_product_by_name(self):
        """It should find a product by name from the database   [EX2]"""
        NUMB_CREATE = 5
        # EXPECT 0 OBJECT IN DB         
        products_origin = Product.all()                      
        self.assertEqual(len(products_origin), 0)            
        # ADD PRODUCTS & VALID CREATION
        products_created = list()
        for _ in range(NUMB_CREATE):                            # [1]
            products_created.append(ProductFactory().create())  # [1]
        products_created = Product.all()
        self.assertEqual(len(Product.all()), NUMB_CREATE)
        self.assertEqual(len(products_created), NUMB_CREATE)
        # RETRIEVE FIRST PRODUCT
        p0_name = products_created[0].name      # [2]
        # RETRIEVE BY NAME and COUNT
        counter_p0_name = 0                     # [3]
        for p in products_created:              # [3]
            if p.name == p0_name:               # [3]
               counter_p0_name += 1             # [3]
        products_by_name =  Product.find_by_name(p0_name)           # [4]
        self.assertEqual(products_by_name.count(), counter_p0_name) # [5]
        # EXPECT ALL SAME NAME and ONLY SAME NAME 
        product_by_name_ids = list()
        for p in products_by_name: # all same   # [6]
            self.assertEqual(p.name, p0_name)   # [6]
            product_by_name_ids.append(p.id)
        for p in products_created: # only same             
            if p.id not in product_by_name_ids:
                self.assertNotEqual(p.name, p0_name)
                            
     
    def test_find_a_product_by_category(self):
        """It should find a product by category from the database   [EX2]"""
        NUMB_CREATE = 10
        # EXPECT 0 OBJECT IN DB         
        products_origin = Product.all()                      
        self.assertEqual(len(products_origin), 0)            
        # ADD PRODUCTS & VALID CREATION
        products_created = list()
        for _ in range(NUMB_CREATE):                            # [1]
            products_created.append(ProductFactory().create())  # [1]
        products_created = Product.all()
        self.assertEqual(len(Product.all()), NUMB_CREATE)
        self.assertEqual(len(products_created), NUMB_CREATE)
        # RETRIEVE FIRST PRODUCT
        p0_category = products_created[0].category  # [2]
        # RETRIEVE BY CATEGORY and COUNT
        counter_p0_category = 0                     # [3]
        for p in products_created:                  # [3]
            if p.category == p0_category:           # [3]
               counter_p0_category += 1             # [3]
        products_by_category =  Product.find_by_category(p0_category)           # [4]
        self.assertEqual(products_by_category.count(), counter_p0_category)     # [5]
        # EXPECT ALL SAME CATEGORY and ONLY SAME CATEGORY 
        product_by_category_ids = list()
        for p in products_by_category: # all same   # [6]
            self.assertEqual(p.category, p0_category)   # [6]
            product_by_category_ids.append(p.id)
        for p in products_created: # only same             
            if p.id not in product_by_category_ids:
                self.assertNotEqual(p.category, p0_category)
