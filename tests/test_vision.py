"""Contract and rejection tests using mocked provider responses, not accuracy evaluations."""
import copy
import json
from io import BytesIO
from urllib.error import HTTPError, URLError
import pytest
from server import vision

IMAGE = 'data:image/jpeg;base64,/9h0ZXN0LXNuaW1lay//2Q=='
PRODUCT = {'name': 'Test bottle'}
FRAME = {'bottle_count': 1, 'matches_product': True, 'level_visible': True,
         'bottle_fully_visible': True, 'constant_section': True,
         'full_y': .2, 'level_y': .5, 'bottom_y': .8}


def result():
    return {'frames': [copy.deepcopy(FRAME), copy.deepcopy(FRAME)]}


def test_disabled_does_not_call_provider(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('BAROMETR_AUTO_LEVEL_ENABLED', '1')
    monkeypatch.setattr(vision, 'urlopen', lambda *a, **k: pytest.fail('No provider call when disabled'))
    assert vision.configuration()['enabled'] is False
    with pytest.raises(vision.VisionError):
        vision.analyze([IMAGE, IMAGE], PRODUCT, 700)


def test_two_frame_validation_and_rejections():
    accepted = vision.validate_result(result(), 700)
    assert accepted['detected'] is True and accepted['ml'] == 350
    assert accepted['calibrated'] is False and accepted['method'] == 'vision-estimate'
    for field, value in [('matches_product', False), ('bottle_count', 2), ('level_visible', False),
                         ('bottle_fully_visible', False), ('constant_section', False), ('level_y', .1)]:
        data = result(); data['frames'][0][field] = value
        assert vision.validate_result(data, 700)['detected'] is False
    inconsistent = result(); inconsistent['frames'][1]['level_y'] = .62
    assert vision.validate_result(inconsistent, 700)['detected'] is False
    for bad in (None, float('nan'), float('inf'), '0.5', True, 1.1):
        data = result(); data['frames'][0]['level_y'] = bad
        with pytest.raises(vision.VisionError):
            vision.validate_result(data, 700)
    for bad in ({}, {'frames': []}, {'frames': [FRAME]}, {'frames': [None, FRAME]}):
        with pytest.raises(vision.VisionError):
            vision.validate_result(bad, 700)


def test_image_validation():
    for image in ('https://example.com/a.jpg', 'data:image/png;base64,eA==', 'data:image/jpeg;base64,wrong', 3):
        with pytest.raises(vision.VisionError):
            vision.validate_image(image)


def test_provider_request_contract(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'unit-test-placeholder')
    monkeypatch.setenv('BAROMETR_AUTO_LEVEL_ENABLED', '1')
    seen = []
    def call(req, timeout):
        data = json.loads(req.data)
        seen.append(data)
        assert req.full_url == 'https://api.openai.com/v1/responses'
        assert timeout == 40 and data['store'] is False
        assert data['text']['format']['strict'] is True
        assert len([i for i in data['input'][1]['content'] if i['type'] == 'input_image']) == 2
        return BytesIO(json.dumps({'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': json.dumps(result())}]}]}).encode())
    monkeypatch.setattr(vision, 'urlopen', call)
    value = vision.analyze([IMAGE, IMAGE], PRODUCT, 700)
    assert value['ml'] == 350 and len(seen) == 1
    assert 'unit-test-placeholder' not in json.dumps(seen)


def test_provider_failures_are_sanitized(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'unit-test-placeholder')
    monkeypatch.setenv('BAROMETR_AUTO_LEVEL_ENABLED', '1')
    for error in (URLError('unit-test-placeholder'), TimeoutError(),
                  HTTPError('https://api.openai.com', 401, 'unit-test-placeholder', {}, None)):
        def call(*args, **kwargs): raise error
        monkeypatch.setattr(vision, 'urlopen', call)
        with pytest.raises(vision.VisionError) as caught:
            vision.analyze([IMAGE, IMAGE], PRODUCT, 700)
        assert 'unit-test-placeholder' not in str(caught.value)
    monkeypatch.setattr(vision, 'urlopen', lambda *a, **kw: BytesIO(b'{"status":"incomplete"}'))
    with pytest.raises(vision.VisionError):
        vision.analyze([IMAGE, IMAGE], PRODUCT, 700)
