######################################################################
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
######################################################################

# spell: ignore Rofrano jsonify restx dbname
"""
Product Store Service with UI
"""
from flask import jsonify, request, abort
from flask import url_for  # noqa: F401 pylint: disable=unused-import
from service.models import Product, Category

from service.common import status  # HTTP Status Codes
from . import app


######################################################################
# H E A L T H   C H E C K
######################################################################
@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# H O M E   P A G E
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s",
                     request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# C R E A T E   A   N E W   P R O D U C T
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product = Product()
    product.deserialize(data)
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    message = product.serialize()

    #
    # Uncomment this line of code once you implement READ A PRODUCT
    #
    # location_url = url_for("get_products", product_id=product.id, _external=True)
    location_url = "/"  # delete once READ is implemented
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# R E A D   A   P R O D U C T
######################################################################
# [EX3-T2]
@app.route("/products/<int:product_id>", methods=["GET"])  # [1]
def get_products(product_id):  # [2]
    """Retrieve a product (JSON OUT) by id"""
    product_by_id = Product.find(product_id)  # [3]
    if product_by_id is None:  # [4]
        abort(
            status.HTTP_404_NOT_FOUND, f"can't find <product.id=={product_id}>"
        )  # [4]
    return product_by_id.serialize(), status.HTTP_200_OK  # [5], [6]


######################################################################
# U P D A T E   A   P R O D U C T
######################################################################
# [EX3]
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_products(product_id):
    """Update a product (JSON IN)"""
    check_content_type("application/json")
    product_by_id = Product.find(product_id)
    if product_by_id is None:  # [4]
        abort(status.HTTP_404_NOT_FOUND,
              f"can't find <product.id=={product_id}>")
    product_by_id.deserialize(request.get_json())
    product_by_id.update()
    return product_by_id.serialize(), status.HTTP_200_OK


######################################################################
# D E L E T E   A   P R O D U C T
######################################################################
# [EX3]
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_products(product_id):
    """delete a product (JSON OUT)"""
    app.logger.error("in delete_products")
    product_by_id = Product.find(product_id)
    app.logger.error(product_by_id)
    if product_by_id is None:
        abort(status.HTTP_404_NOT_FOUND,
              f"can't find <product.id=={product_id}>")
    product_by_id.delete()
    return jsonify(""), status.HTTP_204_NO_CONTENT


######################################################################
# LIST PRODUCTS
######################################################################
@app.route("/products", methods=["GET"])
def list_all_products():
    """Returns all Products as a list"""
    products = []
    product_name = request.args.get("name")
    product_category = request.args.get("category")
    available = request.args.get("available")
    undone = True
    # TODO : what are the specs if more than one request un the url ? order ? subset ?
    if undone and product_category:
        # converter
        def converter_to_enum(enum):
            def string_to_enum(name_string):
                return getattr(enum, name_string.upper())

            return string_to_enum

        string_to_category = converter_to_enum(Category)
        # DB response
        undone = False
        try:
            category_enum_element = string_to_category(product_category)
        except AttributeError:
            app.logger.warning("bad category requested, use 'unknown' instead")
            category_enum_element = string_to_category("unknown")
        products = Product.find_by_category(category_enum_element)
    if undone and product_name:
        undone = False
        products = Product.find_by_name(product_name)
    if undone and available:
        undone = False
        products = Product.find_by_availability("true")
    if undone:
        undone = False
        products = Product.all()
    products_serialized = []
    for product in products:
        products_serialized.append(product.serialize())
    return jsonify(products_serialized), status.HTTP_200_OK
