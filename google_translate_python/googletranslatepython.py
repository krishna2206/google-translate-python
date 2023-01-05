# coding:utf-8
# author lushan88a, improved by krishna2206
# version : 1.2.0

import re
import json
import random
from typing import Union
from dataclasses import dataclass

import logging
import urllib3
from urllib.parse import quote

from requests import Session
from requests.exceptions import ConnectTimeout, HTTPError, RequestException
from .constants import LANGUAGES, DEFAULT_SERVICE_URLS

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL_SUFFIXES = [re.search("translate.google.(.*)", url.strip()).group(1)
                for url in DEFAULT_SERVICE_URLS]
DEFAULT_URL_SUFFIX = "com"


class GoogleTranslateError(Exception):
    """Exception that uses context to present a meaningful error message"""

    def __init__(self, msg=None, **kwargs):
        self.tts = kwargs.pop('tts', None)
        self.rsp = kwargs.pop('response', None)
        if msg:
            self.msg = msg
        elif self.tts is not None:
            self.msg = self.infer_msg(self.tts, self.rsp)
        else:
            self.msg = None
        super(GoogleTranslateError, self).__init__(self.msg)

    def infer_msg(self, tts, rsp=None):
        cause = "Unknown"

        if rsp is None:
            premise = "Failed to connect"

            return "{}. Probable cause: {}".format(premise, "timeout")
            # if tts.tld != 'com':
            #     host = _translate_url(tld=tts.tld)
            #     cause = "Host '{}' is not reachable".format(host)

        else:
            status = rsp.status_code
            reason = rsp.reason

            premise = "{:d} ({}) from TTS API".format(status, reason)

            if status == 403:
                cause = "Bad token or upstream API changes"
            elif status == 200 and not tts.lang_check:
                cause = "No audio stream in response. Unsupported language '%s'" % self.tts.lang
            elif status >= 500:
                cause = "Uptream API error. Try again later."

        return "{}. Probable cause: {}".format(premise, cause)


@dataclass
class TranslatedText:
    """A class to represent a translated text"""

    text: Union[str, list]
    src_lang: str = None
    dest_lang: str = None
    src_pronunciation: str = None
    dest_pronunciation: str = None

    def __str__(self):
        if isinstance(self.text, list):
            # If gender-specific translation is available, return the male translation
            return self.text[1]
        return self.text

    def __repr__(self):
        return "TranslatedText(text={}, src_lang={}, dest_lang={}, src_pronunciation={}, dest_pronunciation={})".format(
            self.text, self.src_lang, self.dest_lang, self.src_pronunciation, self.dest_pronunciation)
    
    def __dict__(self):
        return {
            "text": self.text,
            "src_lang": self.src_lang,
            "dest_lang": self.dest_lang,
            "src_pronunciation": self.src_pronunciation,
            "dest_pronunciation": self.dest_pronunciation
        }


class GoogleTranslate:
    """
    You can use 108 languages as the target or source. For a list of languages, see LANGUAGES.

    Args:
    url_suffix: The source text(s) to be translated. Batch translation is supported via sequence input.
                The value should be one of the url_suffix listed in DEFAULT_SERVICE_URLS.
                (str or unicode, or a sequence of these)
    timeout: Timeout for each request. (numeric)
    proxies: Proxies to use for each request. (dict) Example: {'http': 'http:171.112.169.47:19934/', 'https': 'https:171.112.169.47:19934/'}

    """

    def __init__(self, url_suffix: str = "com", timeout: int = 5, proxies: dict = None):
        self.url_suffix = DEFAULT_URL_SUFFIX if url_suffix not in URL_SUFFIXES else url_suffix
        url_base = f"https://translate.google.{self.url_suffix}"
        self.url = url_base + "/_/TranslateWebserverUi/data/batchexecute"
        self.timeout = timeout
        self.proxies = proxies

        self.session = Session()
        self.session.headers.update({
            "Referer": f"{url_base}/",
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/47.0.2526.106 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
        })
        self.session.proxies = proxies

    def __package_rpc(self, text: str, lang_src: str = "auto", lang_tgt: str = "auto"):
        GOOGLE_TTS_RPC = ["MkEWBc"]
        parameter = [[text.strip(), lang_src, lang_tgt, True], [1]]
        escaped_parameter = json.dumps(parameter, separators=(",", ":"))
        rpc = [
            [[random.choice(GOOGLE_TTS_RPC), escaped_parameter,
              None, "generic"]]
        ]
        espaced_rpc = json.dumps(rpc, separators=(",", ":"))
        freq_initial = f"f.req={quote(espaced_rpc)}&"
        freq = freq_initial
        return freq

    def translate(self, text: str, src_lang: str = "auto", dest_lang: str = "en") -> TranslatedText:
        """
        Translate text from one language to another.

        Args:
            text: The source text(s) to be translated. (str or unicode, or a sequence of these)
            src_lang: The language of the source text. The value should be one of the language codes listed in LANGUAGES. If a language is not specified, the system will attempt to identify the source language automatically. (str or unicode)
            dest_lang: The language to translate the source text into. The value should be one of the language codes listed in LANGUAGES. (str or unicode)

        Returns:
            A TranslatedText object containing the translated text, source language, destination language, source pronunciation and destination pronunciation.
        """
        if src_lang != "auto" and src_lang not in LANGUAGES.keys():
            raise ValueError("Invalid source language")
        if dest_lang not in LANGUAGES.keys():
            raise ValueError("Invalid target language")

        text = str(text)
        if len(text) >= 5000:
            raise GoogleTranslateError(
                "The text to be translated must be less than 5000 characters")
        if len(text.strip()) == 0:
            return TranslatedText(text="", src_lang=src_lang, dest_lang=dest_lang, src_pronunciation="", dest_pronunciation="")

        freq = self.__package_rpc(text, src_lang, dest_lang)

        try:
            response = self.session.post(
                self.url,
                data=freq,
                verify=False,
                timeout=self.timeout)

            for line in response.iter_lines(chunk_size=1024):
                decoded_line = line.decode("utf-8")
                if "MkEWBc" in decoded_line:
                    try:
                        res_data = decoded_line
                        res_data = json.loads(res_data)
                        res_data = list(res_data)
                        res_data = json.loads(res_data[0][2])
                        response_ = list(res_data)
                        detect_lang = response_[0][2]
                        res_data = response_[1][0]

                        if len(res_data) == 1:
                            if len(res_data[0]) > 5:
                                sentences = res_data[0][5]
                            else: # only url
                                sentences = res_data[0][0]
                                return TranslatedText(
                                    text=sentences,
                                    src_lang=[detect_lang, LANGUAGES[detect_lang.lower()]],
                                    dest_lang=[dest_lang, LANGUAGES[dest_lang]],
                                    src_pronunciation=None,
                                    dest_pronunciation=None)

                            translated_text = ""
                            for sentence in sentences:
                                sentence = sentence[0]
                                translated_text += sentence.strip() + " "
                            translated_text = translated_text
                            pronounce_src = (response_[0][0])
                            pronounce_tgt = (response_[1][0][0][1])
                            return TranslatedText(
                                text=translated_text,
                                src_lang=[detect_lang, LANGUAGES[detect_lang.lower()]],
                                dest_lang=[dest_lang, LANGUAGES[dest_lang]],
                                src_pronunciation=pronounce_src,
                                dest_pronunciation=pronounce_tgt)

                        elif len(res_data) == 2:
                            sentences = []
                            for i in res_data:
                                sentences.append(i[0])
                            pronounce_src = (response_[0][0])
                            pronounce_tgt = (response_[1][0][0][1])
                            return TranslatedText(
                                text=sentences,
                                src_lang=[detect_lang, LANGUAGES[detect_lang.lower()]],
                                dest_lang=[dest_lang, LANGUAGES[dest_lang]],
                                src_pronunciation=pronounce_src,
                                dest_pronunciation=pronounce_tgt)
                    except Exception as error:
                        log.debug(str(error))
                        raise error
            response.raise_for_status()

        except ConnectTimeout as error:
            log.debug(str(error))
            raise error

        except HTTPError as error:
            # Request successful, bad response
            log.debug(str(error))
            raise GoogleTranslateError(tts=self, response=response)

        except RequestException as error:
            # Request failed
            log.debug(str(error))
            raise GoogleTranslateError(tts=self)
