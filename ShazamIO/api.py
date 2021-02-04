from aiohttp import ClientRequest

from ShazamIO.converter import Converter
from pydub import AudioSegment
from io import BytesIO
import aiohttp
import uuid
import time

from .algorithm import SignatureGenerator
from .signature import DecodedMessage
from .models import Request, ShazamUrl
from .converter import Converter


class Shazam(Converter):

    @staticmethod
    async def request(method: str, url: str, **kwargs) -> aiohttp.ClientRequest:
        async with aiohttp.ClientSession() as session:
            if method.upper() == 'GET':
                async with session.get(url, **kwargs) as resp:
                    return await resp.json()
            elif method.upper() == 'POST':
                async with session.post(url, **kwargs) as resp:
                    return await resp.json()
            else:
                raise Exception('Wrong method (Accept: GET/POST')

    async def recognize_song(self, song_data: bytes) -> ClientRequest:
        audio = self.normalize_audio_data(song_data)
        signature_generator = self.create_signature_generator(audio)
        while True:
            signature = signature_generator.get_next_signature()
            if not signature:
                break

            results = await self.send_recognize_request(signature)
            return results

    async def send_recognize_request(self, sig: DecodedMessage) -> ClientRequest:

        data = Converter.data_search(
            Request.TIME_ZONE,
            sig.encode_to_uri(),
            int(sig.number_samples / sig.sample_rate_hz * 1000),
            int(time.time() * 1000))

        return await self.request('POST',
                                  ShazamUrl.SEARCH_FROM_FILE.format(
                                      str(uuid.uuid4()).upper(),
                                      str(uuid.uuid4()).upper()),
                                  headers=Request.HEADERS, json=data)

    async def top_world_tracks(self, tracks: int = 200, start_from: int = 0) -> ClientRequest:
        return await self.request('GET', ShazamUrl.TOP_WORLD.format(tracks, start_from), headers=Request.HEADERS)

    async def artist_about(self, artist_id: int):
        return await self.request('GET', ShazamUrl.ARTIST_ABOUT.format(artist_id))

    async def artist_top_tracks(self, artist_id: int, start_from: int, tracks: int) -> ClientRequest:
        return await self.request('GET', ShazamUrl.ARTIST_TOP_TRACKS.format(artist_id, start_from, tracks),
                                  headers=Request.HEADERS)
