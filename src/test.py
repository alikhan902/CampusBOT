import asyncio
from aiohttp import ClientSession

cookies = {'__RequestVerificationToken': 'rec4EzhmUDXpipQYH9AqGu0zH3AtsbxeysWqILS796aRPM0u4LNNftK_-if7YPLJGBPWdeYbwwU5c2RJDjkbQSCD4Cg1deSPt9740nf150E1', 'captcha': '825518-5016-4732-722866-9e57ef1d-b114-4988-b969-b1b3838a4cfa', 'ecampus': 'LUcAVCysEb8CZu_vmdUXQl1927W4OxwoRYlCzGJfK2KKpOtPanoEwr1Dml2zEbAidh3V2NoFKjzw_Wlo1EqXh89roA1bB_yV96dVX53sxfUoMJe4HHLNnXgioBnd3itkaTMp0DgCrsYeOuuo3RoM6HuVmlQ3d6x_eZmH8oOi0LepawDR9IzYRKcaTruo1flUrp-jL6x74mrp5uIRZxYCSd_APN215z_3CyvqK6U9sgRNyKut-X_e2zYMUqXtDB-re-6j2gvRrMoerrrjqcyUMTduALaJ4HtFN5sIpv4gUS4'}



async def my_async_function():
    async with ClientSession(cookies=cookies) as session:
        response = await session.get('https://ecampus.ncfu.ru/details')
        print(await response.text())
        
asyncio.run(my_async_function())