import asyncio
import os

import aiohttp
from bs4 import BeautifulSoup


async def main():
    os.makedirs("gutenberg", exist_ok=True)
    next_page_link = "http://www.gutenberg.org/robot/harvest?filetypes[]=txt&langs[]=en"
    page = 1
    file_count = 0
    metadata = {"bytes downloaded": 0}

    async with aiohttp.ClientSession() as session:
        while next_page_link is not None:
            response = await session.get(next_page_link)
            soup = BeautifulSoup(await response.text(), "html.parser")
            links = soup.find_all("a")

            print(f"On Page: {page}, ({len(links)}), link ref: {next_page_link}")
            print(f"Data downloaded: {metadata['bytes downloaded'] / 1024 // 1024} MB")
            tasks = []
            for link in links:
                file_url = link["href"]
                if not file_url.endswith(".zip"):
                    continue
                file_count += 1
                local_path = os.path.join("gutenberg", f"b{file_count}" + ".zip")
                tasks.append(download_file(session, file_url, local_path, metadata))
            await asyncio.gather(*tasks)

            page += 1
            next_page_link = get_next_page_link(soup)

    print(f"Data downloaded: {metadata['bytes downloaded'] / 1024 // 1024} MB")


async def download_file(session, file_url, local_path, metadata):
    async with session.get(file_url) as response:
        with open(local_path, "wb") as f:
            file_size = int(response.headers["Content-Length"])
            metadata["bytes downloaded"] += file_size
            f.write(await response.read())
            print(".", end="", flush=True)


def get_next_page_link(soup: BeautifulSoup):
    next_page_link = soup.find("a", text="Next Page")
    if next_page_link is None:
        return None

    next_page_link = next_page_link.get("href")
    if not next_page_link.startswith("http"):
        next_page_link = "http://www.gutenberg.org/robot/" + next_page_link
    return next_page_link


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(main())
