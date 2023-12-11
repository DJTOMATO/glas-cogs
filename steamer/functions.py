import aiohttp
import asyncio
# Dictionary mapping region codes to flag image URLs
region_flags = {
    'TR': 'https://flagcdn.com/32x24/tr.png',
    'DE': 'https://flagcdn.com/32x24/eu.png',
    'US': 'https://flagcdn.com/32x24/us.png',
    'UK': 'https://flagcdn.com/32x24/gb.png',
    'RU': 'https://flagcdn.com/32x24/ru.png',
    'UA': 'https://flagcdn.com/32x24/ua.png',
    'CL': 'https://flagcdn.com/32x24/cl.png',
    'PE': 'https://flagcdn.com/32x24/pe.png',
    'AR': 'https://flagcdn.com/32x24/ar.png'
}

async def get_steam_app_list(api_key):
    key = api_key.get('api_key')
    api_url = f'https://api.steampowered.com/IStoreService/GetAppList/v1/?key={key}&max_results=50000'

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            # Check if the request was successful (status code 200)
            if response.status == 200:
                # Parse the JSON response and extract the list of apps
                data = await response.json()
                return data.get('response', {}).get('apps', [])
            else:
                print(f"Error: {response.status} - {response.reason}")

    # If the request was not successful, return an empty list
    return []

async def get_game_prices(ctx, appid, regions):
    prices_info = []

    # Iterate through regions and fetch prices
    for region in regions:
        # Make a request to the Steam API for each region
        #response = requests.get(f'https://store.steampowered.com/api/appdetails?appids={appid}&cc={region}&l=english&v=1&filters=price_overview')
        url = f'https://store.steampowered.com/api/appdetails?appids={appid}&cc={region}&l=english&v=1&filters=price_overview'

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Check if the request was successful (status code 200)
                if response.status == 200:
                    data = await response.json()
                    # Process the data as needed
                                # Check if the game is free to play
            if str(appid) in data and 'success' in data[str(appid)] and data[str(appid)]['success']:
                if not data[str(appid)]['data']:
                    prices_info.append(f"![Flag]({region_flags.get(region, '')})  Game is free to play")
                else:
                    # Extract and append prices if available
                    price_info = data[str(appid)]['data']['price_overview']
                    currency = price_info['currency']
                    final_price = price_info['final_formatted']
                    prices_info.append(f"![Flag]({region_flags.get(region, '')})  {final_price} {currency}")
            else:
                await ctx.send(f"No price information available for region ![Flag]({region_flags.get(region, '')})")

    else:
            # If the request was not successful
        await ctx.send(f"Error: Unable to retrieve price data for region ![Flag]({region_flags.get(region, '')}) (Status Code: {response.status})")

    return prices_info

def get_app_id(app_name, app_list):
    # Iterate through the list of apps
    for app in app_list:
        # Check if the app name matches the provided name (case-sensitive)
        if app_name == app.get('name'):
            # Return the appid if found
            return app.get('appid')

    # If the app is not found
    return None

