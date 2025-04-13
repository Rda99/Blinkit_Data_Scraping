import requests
import json
import csv
import datetime
import os

# Read category data from CSV
categories = []
print("Reading categories from blinkit_categories.csv...")
with open('blinkit_categories.csv', 'r', newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Convert category names to URL format (lowercase, replace spaces with hyphens)
        l1_category_url = row['l1_category'].lower().replace(' ', '-')
        l2_category_url = row['l2_category'].lower().replace(' ', '-')
        
        categories.append({
            'l1_category': row['l1_category'],
            'l1_category_id': row['l1_category_id'],
            'l2_category': row['l2_category'],
            'l2_category_id': row['l2_category_id'],
            'l1_category_url': l1_category_url,
            'l2_category_url': l2_category_url
        })

# Read location data from CSV
locations = []
print("Reading locations from blinkit_locations.csv...")
with open('blinkit_locations.csv', 'r', newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        locations.append({
            'lat': row['latitude'],
            'lon': row['longitude']
        })

# API configuration
apikey = '6d056d198265a4901b8815323212cf94829fc705'

# Function to find products in snippets
def find_products_in_feeddata(data):
    if not isinstance(data, list) or len(data) == 0:
        return []
    
    for item in data:
        if isinstance(item, dict) and 'ui' in item:
            ui = item.get('ui', {})
            plpContainer = ui.get('plpContainer', {})
            feedData = plpContainer.get('feedData', {})
            
            if not feedData:
                continue
                
            print("Found feedData. Extracting products...")
            products = []
            snippets = feedData.get('snippets', [])
            
            # Debug: Print number of snippets found
            print(f"Found {len(snippets)} snippets")
            
            for snippet in snippets:
                if 'data' in snippet:
                    # If this is a product item (has product id in identity)
                    if 'identity' in snippet['data'] and 'id' in snippet['data']['identity']:
                        products.append(snippet['data'])
                        print(f"Found product: {snippet['data'].get('name', {}).get('text', 'Unknown')}")
            
            # Debug: Print number of products found
            print(f"Total products found: {len(products)}")
            return products
    
    return []

# Get current date for timestamp
current_date = datetime.datetime.now().strftime("%Y-%m-%d")

csv_file = "blinkit_products_full.csv"
existing_data = {}

# Check if CSV file exists and read existing data
if os.path.exists(csv_file):
    print("Found existing CSV file, will update it with new information")
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            product_id = row.get('product_id', '')
            if product_id:
                existing_data[product_id] = row

# Process all locations and categories
all_extracted_products = []

print(f"Processing {len(locations)} locations and {len(categories)} categories...")

for location in locations:
    print(f"\n--- Processing location: {location['lat']}, {location['lon']} ---")
    
    for category in categories:
        print(f"\n=== Processing category: {category['l1_category']} > {category['l2_category']} ===")
        
        # Build the URL for this category
        url = f"https://blinkit.com/cn/{category['l1_category_url']}/{category['l2_category_url']}/cid/{category['l1_category_id']}/{category['l2_category_id']}"
        print(f"URL: {url}")
        
        # Set up API parameters
        params = {
            'url': url,
            'apikey': apikey,
            'custom_headers': 'true',
            'autoparse': 'true',
        }
        
        headers = {
            'lat': location['lat'],
            'lon': location['lon'],
        }
        
        data = {
            'l0_cat': category['l1_category_id'],
            'l1_cat': category['l2_category_id'],
        }
        
        # Make the API request
        print("Making API request...")
        try:
            response = requests.post('https://api.zenrows.com/v1/', params=params, headers=headers, data=data)
            print(f"Response status code: {response.status_code}")
            
            # Parse the JSON response
            result = response.json()
            
            # Try to find products in the response
            products = find_products_in_feeddata(result)
            
            if not products or len(products) == 0:
                print("Could not find products in this category+location combination")
                continue
            
            print(f"\nFound {len(products)} products to process")
            
            # Process extracted products
            for product in products:
                # Debug: Print the type of product
                print(f"Processing product: {type(product)}")
                
                # Check if product is a dict before processing
                if isinstance(product, dict):
                    # Get product ID from identity field
                    product_id = ""
                    if 'identity' in product and 'id' in product['identity']:
                        product_id = product['identity']['id']
                    
                    # Debug: Show product ID
                    print(f"Product ID: {product_id}")
                    
                    # Extract name
                    name = ""
                    if 'name' in product and isinstance(product['name'], dict) and 'text' in product['name']:
                        name = product['name']['text']
                    
                    # Extract store_id (merchant_id in Blinkit data)
                    store_id = None
                    if 'merchant_id' in product:
                        store_id = product.get('merchant_id', None)
                    # Check in atc_action for merchant_id
                    elif 'atc_action' in product and 'add_to_cart' in product['atc_action']:
                        cart_item = product['atc_action']['add_to_cart'].get('cart_item', {})
                        if 'merchant_id' in cart_item:
                            store_id = cart_item.get('merchant_id', None)
                    # Check in meta for merchant_id
                    elif 'meta' in product and product['meta'] and 'merchant_id' in product['meta']:
                        store_id = product['meta'].get('merchant_id', None)
                    
                    # Extract brand info
                    brand = ""
                    brand_id = None
                    if 'brand_name' in product and isinstance(product['brand_name'], dict) and 'text' in product['brand_name']:
                        brand = product['brand_name']['text']
                    elif 'atc_action' in product and 'add_to_cart' in product['atc_action']:
                        cart_item = product['atc_action']['add_to_cart'].get('cart_item', {})
                        if 'brand' in cart_item:
                            brand = cart_item.get('brand', '')
                    
                    # Extract inventory
                    inventory = ""
                    if 'inventory' in product and not isinstance(product['inventory'], dict):
                        inventory = str(product.get('inventory', ''))
                    
                    # Extract price info
                    selling_price = ""
                    mrp = ""
                    if 'normal_price' in product and isinstance(product['normal_price'], dict) and 'text' in product['normal_price']:
                        selling_price = product['normal_price']['text'].replace('₹', '')
                    if 'mrp' in product and isinstance(product['mrp'], dict) and 'text' in product['mrp']:
                        mrp = product['mrp']['text'].replace('₹', '')
                    
                    # Extract image URL (try multiple possible locations)
                    image_url = ""
                    # Try in atc_action first as requested
                    if 'atc_action' in product and 'add_to_cart' in product['atc_action']:
                        cart_item = product['atc_action']['add_to_cart'].get('cart_item', {})
                        if 'image_url' in cart_item:
                            image_url = cart_item.get('image_url', '')
                    
                    # If not found in atc_action, try the image field
                    if not image_url and 'image' in product and isinstance(product['image'], dict):
                        image_url = product['image'].get('url', '')
                    
                    # If still not found, check media_container
                    if not image_url and 'media_container' in product:
                        media_items = product['media_container'].get('items', [])
                        if media_items and len(media_items) > 0 and 'image' in media_items[0]:
                            image_url = media_items[0]['image'].get('url', '')
                    
                    # Debug: Print extracted values
                    print(f"Extracted - Name: {name}, Brand: {brand}, Inventory: {inventory}, Price: {selling_price}, MRP: {mrp}")
                    print(f"Image URL: {image_url}")
                    print(f"Store ID: {store_id}, Brand ID: {brand_id}")
                    
                    # Start with existing data if available
                    if product_id in existing_data:
                        extracted = existing_data[product_id].copy()
                        print(f"Updating existing product: {name}")
                    else:
                        # Create new record
                        extracted = {
                            'date': current_date,
                            'product_id': product_id,
                            'l1_category': category['l1_category'],
                            'l1_category_id': category['l1_category_id'],
                            'l2_category': category['l2_category'],
                            'l2_category_id': category['l2_category_id'],
                            'store_id': store_id,
                            'variant_id': product_id,
                            'variant_name': name,
                            'group_id': product.get('group_id', ''),
                            'selling_price': selling_price,
                            'mrp': mrp,
                            'in_stock': 'true',  # Assuming all products shown are in stock
                            'inventory': inventory,
                            'is_sponsored': '',
                            'image_url': image_url,
                            'brand_id': brand_id,
                            'brand': brand,
                        }
                    
                    # Always update the image_url in existing records
                    if image_url:
                        extracted['image_url'] = image_url
                    
                    # Update store_id and brand_id in existing records
                    extracted['store_id'] = store_id
                    extracted['brand_id'] = brand_id
                    
                    # Add location information
                    extracted['latitude'] = location['lat']
                    extracted['longitude'] = location['lon']
                    
                    # Add to collection - using location+product_id as unique key
                    location_product_key = f"{location['lat']}_{location['lon']}_{product_id}"
                    existing_data[location_product_key] = extracted
                    all_extracted_products.append(extracted)
            
        except Exception as e:
            print(f"Error processing category {category['l1_category']} > {category['l2_category']} at location {location['lat']}, {location['lon']}: {str(e)}")
            continue

# Save all the extracted data to CSV
if all_extracted_products:
    fieldnames = [
        'date', 'l1_category', 'l1_category_id', 'l2_category', 'l2_category_id',
        'store_id', 'variant_id', 'variant_name', 'group_id', 'product_id', 'selling_price',
        'mrp', 'in_stock', 'inventory', 'is_sponsored', 'image_url', 'brand_id', 'brand',
        'latitude', 'longitude'
    ]
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_extracted_products)
    
    print(f"Successfully saved {len(all_extracted_products)} products to {csv_file}")
else:
    print("No products were extracted")

# Save a sample product for debugging if any were found
if all_extracted_products:
    print("Saving a sample product to sample_product.json for debugging")
    with open('sample_product.json', 'w', encoding='utf-8') as f:
        json.dump(all_extracted_products[0], f, indent=2)
