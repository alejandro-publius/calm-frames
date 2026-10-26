"""Bounded MP4 protection checks, independent of any decoder or DRM service."""

import pytest

from pipeline import local_intake as intake


def box(kind, payload=b""):
    return (len(payload) + 8).to_bytes(4, "big") + kind + payload


def mp4(*boxes):
    return box(b"ftyp", b"isom\x00\x00\x00\x00mp42") + b"".join(boxes)


def descriptions(*entries):
    payload = box(b"stsd", b"\x00" * 4 + len(entries).to_bytes(4, "big") + b"".join(entries))
    for kind in (b"stbl", b"minf", b"mdia", b"trak", b"moov"):
        payload = box(kind, payload)
    return payload


@pytest.mark.parametrize("tag", [b"encv", b"enca", b"drms", b"drmi"])
def test_encrypted_sample_description_refused_before_analysis(tmp_path, tag):
    source = tmp_path / "encrypted.mp4"
    source.write_bytes(mp4(descriptions(box(tag, b"\x00" * 80))))
    with pytest.raises(intake.IntakeError, match="DRM|encrypted"):
        intake.validate_container(source)


@pytest.mark.parametrize("tag", [b"pssh", b"senc"])
def test_protection_metadata_refused(tmp_path, tag):
    source = tmp_path / "protected.mp4"
    source.write_bytes(mp4(box(b"moov", box(tag, b"\x00" * 16))))
    with pytest.raises(intake.IntakeError, match="DRM|encrypted"):
        intake.validate_container(source)


def test_protection_inside_clear_sample_entry_refused(tmp_path):
    source = tmp_path / "protected.mp4"
    source.write_bytes(mp4(descriptions(box(b"avc1", b"\x00" * 78 + box(b"sinf")))))
    with pytest.raises(intake.IntakeError, match="DRM|encrypted"):
        intake.validate_container(source)


@pytest.mark.parametrize("tag", [b"sgpd", b"sbgp"])
def test_encrypted_sample_group_refused(tmp_path, tag):
    source = tmp_path / "grouped.mp4"
    source.write_bytes(mp4(box(b"moov", box(tag, b"\x00" * 4 + b"seig"))))
    with pytest.raises(intake.IntakeError, match="Encrypted"):
        intake.validate_container(source)


def test_media_bytes_that_resemble_a_protection_marker_are_not_metadata(tmp_path):
    source = tmp_path / "clear.mp4"
    source.write_bytes(mp4(box(b"mdat", b"not a box: pssh encv enca")))
    intake.validate_container(source)


@pytest.mark.parametrize(
    "payload",
    [
        b"\x00\x00\x00\x04moov",
        b"\x00\x00\xff\xffmoov",
        b"\x00\x00\x00\x01moov\x00",
        box(b"moov", b"short"),
        descriptions(box(b"avc1", b"short")),
    ],
)
def test_truncated_or_out_of_bounds_box_is_not_treated_as_clear(tmp_path, payload):
    source = tmp_path / "broken.mp4"
    source.write_bytes(mp4(payload))
    with pytest.raises(intake.IntakeError, match="MP4"):
        intake.validate_container(source)


def test_empty_or_excessive_sample_description_count_is_refused(tmp_path):
    source = tmp_path / "broken.mp4"
    for count in (0, 4294967295):
        source.write_bytes(mp4(box(b"moov", box(b"stsd", b"\x00" * 4 + count.to_bytes(4, "big")))))
        with pytest.raises(intake.IntakeError, match="MP4"):
            intake.validate_container(source)


def test_nesting_is_bounded(tmp_path):
    payload = box(b"free")
    for _ in range(40):
        payload = box(b"moov", payload)
    source = tmp_path / "nested.mp4"
    source.write_bytes(mp4(payload))
    with pytest.raises(intake.IntakeError, match="MP4"):
        intake.validate_container(source)


def test_box_count_is_bounded(tmp_path):
    source = tmp_path / "many-boxes.mp4"
    source.write_bytes(mp4(box(b"free") * 5000))
    with pytest.raises(intake.IntakeError, match="MP4"):
        intake.validate_container(source)


def test_extended_and_to_end_sizes_are_supported(tmp_path):
    source = tmp_path / "clear.mp4"
    extended = b"\x00\x00\x00\x01free" + (20).to_bytes(8, "big") + b"data"
    source.write_bytes(mp4(extended, b"\x00\x00\x00\x00mdat" + b"last media"))
    intake.validate_container(source)
