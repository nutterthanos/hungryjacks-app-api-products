import requests
import json
import os
import logging
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# URLs and endpoints
list_stores_url = "https://web-api.hungryjacks.com.au/prod/api/v2/stores/"
list_menu_url_pickup = "https://web-api.hungryjacks.com.au/prod/api/v2/menu/{}/pickup"
list_menu_url_delivery = "https://web-api.hungryjacks.com.au/prod/api/v2/menu/{}/delivery"
apikey = "7O5jnagC8V4PwfavmfoRCXAFFEfdhks4pfgh8Kbj"

# File to store ETags
etag_file = "etags.json"

def load_etags():
    if os.path.exists(etag_file):
        with open(etag_file, 'r') as f:
            return json.load(f)
    return {}

def save_etags(etags):
    with open(etag_file, 'w') as f:
        json.dump(etags, f, indent=4)

def fetch_stores():
    etags = load_etags()
    headers = {
        'X-Api-Key': apikey,
        'Accept-Encoding': 'br'
    }
    
    if 'stores' in etags:
        headers['If-None-Match'] = etags['stores']
        logging.debug(f"Using ETag for stores: {etags['stores']}")

    logging.debug(f"Sending request to {list_stores_url} with headers: {headers}")
    response = requests.get(list_stores_url, headers=headers)

    if response.status_code == 304:
        logging.debug("No changes in stores data (304 Not Modified).")
        return []

    logging.debug(f"Response status code: {response.status_code}")
    logging.debug(f"Response headers: {response.headers}")

    if response.status_code == 200:
        etag = response.headers.get('ETag')
        if etag:
            logging.debug(f"Storing ETag for stores: {etag}")
            etags['stores'] = etag
            save_etags(etags)

        data = response.json()
        file_name = "stores.json"
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)

        return [store['store_id'] for store in data if 'store_id' in store]
    else:
        logging.error(f"Failed to fetch stores data: {response.status_code}")
        return []

def fetch_menu(store_id):
    etags = load_etags()
    menu_types = ['pickup', 'delivery']
    headers = {
        'x-cf-api-key': cfapikey,
        'Accept-Encoding': 'br'
    }
    
    for menu_type in menu_types:
        url = list_menu_url_pickup.format(store_id) if menu_type == 'pickup' else list_menu_url_delivery.format(store_id)

        etag_key = f"{store_id}_{menu_type}"
        if etag_key in etags:
            headers['If-None-Match'] = etags[etag_key]
            logging.debug(f"Using ETag for {menu_type} menu of store {store_id}: {etags[etag_key]}")

        logging.debug(f"Sending request to {url} with headers: {headers}")
        response = requests.get(url, headers=headers)

        if response.status_code == 304:
            logging.debug(f"No changes in {menu_type} menu data for store {store_id} (304 Not Modified).")
            time.sleep(3)
            continue

        logging.debug(f"Response status code: {response.status_code}")
        logging.debug(f"Response headers: {response.headers}")

        if response.status_code == 200:
            etag = response.headers.get('ETag')
            if etag:
                logging.debug(f"Storing ETag for {menu_type} menu of store {store_id}: {etag}")
                etags[etag_key] = etag
                save_etags(etags)

            data = response.json()
            file_name = f"menu_{store_id}_{menu_type}.json"
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
        else:
            logging.error(f"Failed to fetch {menu_type} menu data for store {store_id}: {response.status_code}")

def main():
    store_ids = fetch_stores()
    if store_ids:
        for store_id in store_ids:
            fetch_menu(store_id)

if __name__ == "__main__":
    main()