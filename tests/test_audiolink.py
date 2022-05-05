import pytest
import audiolink.audiolink as al
import os
from pathlib import Path
import shutil
import uuid


# Config
version = '0.1.0'
file_types = [
    '.flac',
    '.mp3',
]


# Global Settings
resource_path = Path('tests/resources')
al_id_suffix = '-al'

known_id = {
    'valid': '0' * 32 + al_id_suffix,
    'invalid_hex': 'z' * 32 + al_id_suffix,
    'invalid_suffix': '0' * 32 + '-zz',
}


# Global Functions
def id_parts(val:str) -> str:
    n = len(al_id_suffix)
    return val[:-n], val[-n:]


def uuid_hex(val:str) -> str:
    try:
        uuid.UUID(val).hex
        return val
    except ValueError:
        return None


# Fixtures
@pytest.fixture
def media_file(tmp_path:Path):
    def _file(file_state:str, file_type:str) -> Path:
        fn = file_state + file_type
        src = resource_path / fn
        dest = tmp_path / fn
        shutil.copy(src, dest)
        return dest

    return _file


@pytest.fixture
def media_file_empty(media_file):
    def _file(file_type:str) -> Path:
        return media_file('empty', file_type)

    return _file


@pytest.fixture
def media_file_full(media_file):
    def _file(file_type:str) -> Path:
        return media_file('full', file_type)

    return _file


# Tests
def test_version():
    assert al.__version__ == version


def test_generate_id():
    id = al.generate_id()
    id_hex, id_suffix = id_parts(id)
    assert id_suffix == al_id_suffix    
    assert id_hex == uuid_hex(id_hex)


@pytest.mark.parametrize(
    'val, expected',
    [
        (known_id['valid'], True),
        (known_id['invalid_hex'], False),
        (known_id['invalid_suffix'], False),
        (None, None),
    ]
)
def test_id_is_valid(val:str, expected:bool):
    assert al.id_is_valid(val) is expected


def test_link_is_valid(tmp_path:Path):
    src_fp = tmp_path / 'src_file'
    dest_fp = tmp_path / 'dest_link'
    not_src_fp = tmp_path / 'not_src_file'
    not_dest_fp = tmp_path / 'not_dest_link'
    
    for fp in [src_fp, not_src_fp, not_dest_fp]:
        with open(fp, 'w'):
            pass

    os.link(src_fp, dest_fp)
    #TODO: add test for ino
    assert al.link_is_valid(src_fp, dest_fp) is True
    assert al.link_is_valid(not_src_fp, dest_fp) is False
    assert al.link_is_valid(src_fp, not_dest_fp) is False    


# AudiolinkFile
#TODO test that a non media file is not loaded
@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_init(media_file_empty, file_type:str):
    fp = media_file_empty(file_type)
    file = al.AudiolinkFile(fp)
    assert file is not None
    assert file.path == fp
    assert file._AudiolinkFile__tag is not None


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_id(media_file_full, file_type:str):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    assert file.id == file._AudiolinkFile__tag.audiolink_id
    assert file.id == known_id['valid']


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_link_name(media_file_full, file_type:str):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    link_name = known_id['valid'] + file.path.suffix
    assert file.link_name == link_name


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_set_id(media_file_empty, file_type:str):
    fp = media_file_empty(file_type)
    file = al.AudiolinkFile(fp)
    assert file._AudiolinkFile__tag.audiolink_id is None
    file.set_id(known_id['valid'])
    del file
    file = al.AudiolinkFile(fp)
    assert file._AudiolinkFile__tag.audiolink_id == known_id['valid']
    # TODO: test setting invalid id
    # TODO: test overwrite


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_set_new_id(media_file_empty, file_type:str):
    fp = media_file_empty(file_type)
    file = al.AudiolinkFile(fp)
    assert file._AudiolinkFile__tag.audiolink_id is None
    file.set_new_id()
    assert file._AudiolinkFile__tag.audiolink_id is not None
    id_hex, id_suffix = id_parts(file._AudiolinkFile__tag.audiolink_id)
    assert id_suffix == al_id_suffix
    assert id_hex == uuid_hex(id_hex)
    # TODO: test overwrite


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_delete_id(media_file_full, file_type:str):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    assert file._AudiolinkFile__tag.audiolink_id is not None
    file.delete_id()
    assert file._AudiolinkFile__tag.audiolink_id is None


# set_id_from_link_name


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_create_link(media_file_full, file_type:str, tmp_path:Path):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    dest_fp = tmp_path / file.link_name
    assert dest_fp.exists() is False
    #TODO: validate_id 
    file.create_link(tmp_path)
    assert dest_fp.exists() is True
    assert dest_fp.name == file.id + file.path.suffix
    assert al.link_is_valid(file.path, dest_fp) is True
    #TODO: test that they share the same ino


@pytest.mark.parametrize('file_type', file_types)
def test_audiolinkFile_delete_link(media_file_full, file_type:str, tmp_path:Path):
    fp = media_file_full(file_type)
    file = al.AudiolinkFile(fp)
    dest_fp = tmp_path / file.link_name
    file.create_link(tmp_path)
    assert dest_fp.exists() is True
    file.delete_link(tmp_path)
    assert dest_fp.exists() is False
