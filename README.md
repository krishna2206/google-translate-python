# google-translate-python
### Version 2.0.0

A free and unlimited python API for google translate, use the reverse engineered Google Translate Ajax API.
  
Installation
====
- Install prerequisites
```bash
pip install -r requirements.txt
```
- Install the package
```bash
pip install git+https://github.com/krishna2206/google-translate-python.git
```  
  
Basic Usage
=====
```python
from google_translate_python import GoogleTranslate

translator = GoogleTranslate()
exp = """
    こんにちは世界
"""

translated_text = translator.translate(exp, dest_lang='en')
print(translated_text)

-> Hello world
```

The translate method returns a ```TranslatedText``` object with the following attributes:
- ```text```: The translated text
- ```src_lang```: The detected source language
- ```dest_lang```: The destination language
- ```src_pronunciation```: The pronunciation of the source text
- ```dest_pronunciation```: The pronunciation of the translated text

If no attribute is specified, the translated text is returned by default.

**NB** : In some languages, you can get *both feminine and masculine translations* for some gender-neutral words, phrases and sentences. In this case, the ```text``` attribute will be a list of strings, each string being a translation.
  
License
====
[MIT License](https://github.com/krishna2206/google-translate-python/blob/main/README.md)