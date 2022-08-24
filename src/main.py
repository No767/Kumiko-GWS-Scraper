import asyncio
import logging
import os
import re
import uuid
from pathlib import Path

import aiohttp
import orjson
import uvloop
import wget
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from genshin_wish_sim_utils.wish import KumikoWSUtils

load_dotenv()

POSTGRES_PASSWORD = os.getenv("Postgres_Password_Dev")
POSTGRES_SERVER_IP = os.getenv("Postgres_Server_IP_Dev")
POSTGRES_WS_DATABASE = os.getenv("Postgres_Wish_Sim_Database")
POSTGRES_USERNAME = os.getenv("Postgres_Username_Dev")
POSTGRES_PORT = os.getenv("Postgres_Port_Dev")
WS_CONNECTION_URI = f"postgresql+asyncpg://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER_IP}:{POSTGRES_PORT}/{POSTGRES_WS_DATABASE}"

listOfCharacters = [
    "zhongli",
    "venti",
    "lumine",
    "albedo",
    "yelan",
    "ganyu",
    "xiao",
    "klee",
    "aether",
    "shenhe",
]
listOfCharactersManual = ["hu-tao", "raiden", "yae-miko", "ayaka", "yoimiya"]

listOfWeapons = ["mistsplitter-reforged"]


wsUtils = KumikoWSUtils()

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] | %(asctime)s >> %(message)s",
    datefmt="[%m/%d/%Y] [%I:%M:%S %p %Z]",
)


async def addCharacters():
    for items in listOfCharactersManual:
        await asyncio.sleep(3)
        async with aiohttp.ClientSession(json_serialize=orjson.dumps) as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
            }
            async with session.get(
                f"https://www.gensh.in/characters/{items}", headers=headers
            ) as r:
                data = await r.text()
                soup = BeautifulSoup(data, "lxml")
                findName = soup.find("div", class_="nameblock")
                listOfText = [
                    items for items in soup.find_all("div", class_="card-body")
                ]
                itemDescription = str(listOfText[3].get_text()).strip()
                starRank = str(listOfText[1].li.get_text())
                starRankFiltered = int(re.sub("\D", "", starRank))
                name = str(findName.h2.get_text()).strip()
                await wsUtils.addToWSData(
                    uuid=str(uuid.uuid4()),
                    event_name=None,
                    name=name,
                    description=itemDescription,
                    star_rank=starRankFiltered,
                    type="character",
                    uri=WS_CONNECTION_URI,
                )
                logging.info(f"Inputted Data to DB - {name}")


async def addWeapons():
    for items in listOfWeapons:
        await asyncio.sleep(3)
        async with aiohttp.ClientSession(json_serialize=orjson.dumps) as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
            }
            async with session.get(
                f"https://www.gensh.in/database/weapon/{items}", headers=headers
            ) as r:
                data = await r.text()
                soup = BeautifulSoup(data, "lxml")
                listOfText = [item for item in soup.find_all("div", class_="card-body")]
                itemName = listOfText[0].h2.get_text()
                listOfLists = [
                    listedItem.get_text() for listedItem in listOfText[0].find_all("li")
                ]
                starRank = listOfLists[1]
                parsedItemName = str(itemName).strip()
                starRankFiltered = int(re.sub("\D", "", starRank))
                for ul in listOfText[0].ul:
                    for li in ul.find_all("li"):
                        itemDesc = li.get_text()
                        parsedItemDesc = str(itemDesc).strip()
                await wsUtils.addToWSData(
                    uuid=str(uuid.uuid4()),
                    event_name=None,
                    name=parsedItemName,
                    description=parsedItemDesc,
                    star_rank=starRankFiltered,
                    type="weapon",
                    uri=WS_CONNECTION_URI,
                )
                logging.info(
                    f"Inputted Data to DB - {parsedItemName}, {starRankFiltered}"
                )


async def scrapAssets():
    mainRes = await wsUtils.getListOfCharacters(type="character", uri=WS_CONNECTION_URI)
    for items in mainRes:
        characterItem = str(items).lower().strip()
        await asyncio.sleep(3)
        async with aiohttp.ClientSession(json_serialize=orjson.dumps) as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
            }
            async with session.get(
                f"https://www.gensh.in/characters/{characterItem}", headers=headers
            ) as r:
                data = await r.text()
                soup = BeautifulSoup(data, "lxml")
                assets = soup.find("img", class_="img-fluid")
                actualAsset = f'https://www.gensh.in{assets["src"]}'
                findName = soup.find("div", class_="nameblock")
                name = str(findName.h2.get_text()).strip()
                getPath = Path(__file__).parents[1]
                mainRes = await wsUtils.getSingleWSItemName(
                    name=str(items), uri=WS_CONNECTION_URI
                )
                itemUUID = dict(mainRes)["uuid"]
                wget.download(
                    actualAsset,
                    out=os.path.join(getPath, "assets", f"{itemUUID}.png"),
                    bar=None,
                )
                logging.info(f"Downloaded Asset - {name}, {itemUUID}")


async def scrapAnotherAssets():
    listOfCharsAssets = ["hu-tao", "raiden", "yae-miko", "ayaka", "sara", "yoimiya"]
    for items in listOfCharsAssets:
        characterItem = str(items).lower()
        await asyncio.sleep(3)
        async with aiohttp.ClientSession(json_serialize=orjson.dumps) as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
            }
            async with session.get(
                f"https://www.gensh.in/characters/{characterItem}", headers=headers
            ) as r:
                data = await r.text()
                soup = BeautifulSoup(data, "lxml")
                assets = soup.find("img", class_="img-fluid")
                actualAsset = f'https://www.gensh.in{assets["src"]}'
                findName = soup.find("div", class_="nameblock")
                name = str(findName.h2.get_text()).strip()
                getPath = Path(__file__).parents[1]
                mainRes = await wsUtils.getSingleWSItemName(
                    name=str(name), uri=WS_CONNECTION_URI
                )
                itemUUID = dict(mainRes)["uuid"]
                wget.download(
                    actualAsset,
                    out=os.path.join(getPath, "assets", f"{itemUUID}.png"),
                    bar=None,
                )
                logging.info(f"Downloaded Asset - {name}, {itemUUID}")


async def scrapWeaponsAssets():
    mainRes = await wsUtils.getListOfWeapons(type="weapon", uri=WS_CONNECTION_URI)
    for items in mainRes:
        itemPathName = str(items).lower().replace("'", "").replace(" ", "-")
        await asyncio.sleep(3)
        async with aiohttp.ClientSession(json_serialize=orjson.dumps) as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
            }
            async with session.get(
                f"https://www.gensh.in/database/weapon/{itemPathName}", headers=headers
            ) as r:
                data = await r.text()
                soup = BeautifulSoup(data, "lxml")
                assets = soup.find("img", class_="img-fluid")
                actualAsset = f'https://www.gensh.in{assets["src"]}'
                listOfText = [item for item in soup.find_all("div", class_="card-body")]
                itemName = listOfText[0].h2.get_text()
                parsedItemName = str(itemName).strip()
                mainResDB = await wsUtils.getSingleWSItemName(
                    name=str(parsedItemName), uri=WS_CONNECTION_URI
                )
                getPath = Path(__file__).parents[1]
                wget.download(
                    actualAsset,
                    out=os.path.join(
                        getPath, "assets", f"{dict(mainResDB)['uuid']}.png"
                    ),
                    bar=None,
                )
                logging.info(
                    f"Successfully Downloaded Weapons Asset - {parsedItemName}, {dict(mainResDB)['uuid']}"
                )


async def scrapWeaponsAssetList():
    for items in listOfWeapons:
        await asyncio.sleep(3)
        async with aiohttp.ClientSession(json_serialize=orjson.dumps) as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
            }
            async with session.get(
                f"https://www.gensh.in/database/weapon/{items}", headers=headers
            ) as r:
                data = await r.text()
                soup = BeautifulSoup(data, "lxml")
                assets = soup.find("img", class_="img-fluid")
                actualAsset = f'https://www.gensh.in{assets["src"]}'
                listOfText = [item for item in soup.find_all("div", class_="card-body")]
                itemName = listOfText[0].h2.get_text()
                parsedItemName = str(itemName).strip()
                mainResDB = await wsUtils.getSingleWSItemName(
                    name=str(parsedItemName), uri=WS_CONNECTION_URI
                )
                getPath = Path(__file__).parents[1]
                wget.download(
                    actualAsset,
                    out=os.path.join(
                        getPath, "assets", f"{dict(mainResDB)['uuid']}.png"
                    ),
                    bar=None,
                )
                logging.info(
                    f"Successfully Downloaded Weapons Asset - {parsedItemName}, {dict(mainResDB)['uuid']}"
                )


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
asyncio.run(scrapWeaponsAssetList())
