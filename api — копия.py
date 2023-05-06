import requests
import base64
from time import sleep
import aiohttp
import asyncio
import aiofiles

class rudalleClient:
    def __init__(self):
        self.headers = {
            # Your headers
        }

    async def async_ask(self, prompt='cat', style=''):
        data = \
f'''------WebKitFormBoundaryb6ZrB1LvoGELHGVQ\r
Content-Disposition: form-data; name="queueType"\r
\r
generate\r
------WebKitFormBoundaryb6ZrB1LvoGELHGVQ\r
Content-Disposition: form-data; name="query"\r
\r
{prompt.strip()}
\r
------WebKitFormBoundaryb6ZrB1LvoGELHGVQ\r
Content-Disposition: form-data; name="preset"\r
\r
1
\r
------WebKitFormBoundaryb6ZrB1LvoGELHGVQ\r
Content-Disposition: form-data; name="style"\r
\r
{style.strip()}
\r
------WebKitFormBoundaryb6ZrB1LvoGELHGVQ--\r
    '''
        data = data.encode("utf-8")
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://fusionbrain.ai/api/v1/text2image/run', headers=self.headers, data=data) as resp:
                print("Response status:", resp.status)  # Print the response status for debugging
                json = await resp.json()
                print("Received JSON:", json)  # Print the received JSON for debugging
                success = json.get('success', False)  # Use the get() method and provide a default value
                if success:  # Simplified boolean check
                    print("succeeded to ask")
                    return True, json['result']['pocketId']
                print("failed to ask")
                return False, ''
        
    async def async_check(self, id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://fusionbrain.ai/api/v1/text2image/generate/pockets/{id}/status', headers=self.headers) as response:
                response_json = await response.json()
                if response_json['success'] != True:
                    return False, False
                if response_json['result'] in ['INITIAL', 'PROCESSING']:
                    return False, True
                if response_json['result'] == 'SUCCESS':
                    return True, True
        
    async def async_load(self, id, path):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://fusionbrain.ai/api/v1/text2image/generate/pockets/{id}/entities', headers=self.headers) as result:
                result_json = await result.json()
                print("Response JSON:", result_json)  # Print the response JSON for debugging
                newjpgtxt = result_json.get('result', [{}])[0].get('response', [None])[0]
                
                if newjpgtxt:
                    print("Saving image...")  # Print when saving the image
                    image_64_decode = base64.b64decode(newjpgtxt)
                    async with aiofiles.open(f'{path}', 'wb') as image_result:
                        await image_result.write(image_64_decode)
                        print(f"Image saved at {path}")  # Print the saved image path
                        return True


'''async def generate(prompt, path='', style=''):
    print ("starting")
    client = rudalleClient()
    status, id = client.ask(prompt,style)
    if status != True:return False
    x = client.check(id)[0]
    while x != True:
        sleep(0.5)
        print ("checking...")
        x = client.check(id)[0]
    print ("generation done!")
    return client.load(id,path)'''
    

async def generate(prompt, path='', style=''):
    print ("starting")
    client = rudalleClient()
    status, id = await client.async_ask(prompt, style)  # Assuming there's an async version of the ask method
    if status != True:
        return False

    x = await client.async_check(id)[0]  # Assuming there's an async version of the check method
    while x != True:
        await asyncio.sleep(0.5)
        print ("checking...")
        x = await client.async_check(id)[0]
    print ("generation done!")
    return await client.async_load(id, path)  # Assuming there's an async version of the load method