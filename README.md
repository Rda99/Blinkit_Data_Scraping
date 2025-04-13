# Blinkit Data Scraping

This repository contains a Python script for scraping product data from the Blinkit website. The script extracts data based on categories and locations, saving the results to a CSV file.

## Features

- Scrapes product data for multiple categories from Blinkit
- Supports multiple locations using latitude and longitude coordinates
- Extracts comprehensive product details including:
  - Product name, ID, and variant information
  - Pricing (selling price and MRP)
  - Brand information
  - Inventory status
  - Category relationships
  - Image URLs
- Saves extracted data to a CSV file for easy analysis
- Handles error recovery and multiple API requests
- Debug features for tracking extraction progress

## Requirements

- Python 3.x
- Requests library
- CSV module (built-in)
- JSON module (built-in)
- Datetime module (built-in)
- OS module (built-in)

## Usage

1. Prepare your data files:
   - `blinkit_categories.csv`: Contains category information with columns `l1_category`, `l1_category_id`, `l2_category`, and `l2_category_id`
   - `blinkit_locations.csv`: Contains location information with columns `latitude` and `longitude`

2. Run the script:
   ```bash
   python scraper.py
   ```

3. The script will:
   - Read categories and locations from the CSV files
   - Process each location/category combination
   - Extract product data from the Blinkit website
   - Save the results to `blinkit_products_full.csv`
   - Save a sample product to `sample_product.json` for debugging

## Output Format

The script produces a CSV file with the following columns:
- date
- l1_category
- l1_category_id
- l2_category
- l2_category_id
- store_id
- variant_id
- variant_name
- group_id
- product_id
- selling_price
- mrp
- in_stock
- inventory
- is_sponsored
- image_url
- brand_id
- brand
- latitude
- longitude

## License

This project is licensed under the MIT License.
