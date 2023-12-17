
import requests

UUID = '685b1c0a-8cd7-4bc2-ae5a-6c62a97e8c25'
VERSION_URL = f"https://fms.drivingsimulator.ir/api/{UUID}/version"
HEADERS = {
            "Authorization": "Bearer 1|kAEypoKd8oDrGpOQqJPY5yZDt6FC8scgFgRHRlkv"
        }

def get_version_from_site(url:str , headers:dict) -> requests:
        connection = requests.get(url, headers=headers, timeout = (3, 5))
        return connection

if __name__ == "__main__":
        context = get_version_from_site(VERSION_URL , HEADERS)
        print(context.__dict__)
        # print(f'data : {context}\ntext : {context.text}\n\n\n\n status code: {context.status_code}')



    