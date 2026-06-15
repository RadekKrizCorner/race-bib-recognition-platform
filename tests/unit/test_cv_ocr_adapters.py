from rbp_pipeline.adapters import (
    ByteImageProcessor,
    PaddleOcrCompatibleAdapter,
    YoloCompatibleBibDetector,
)


class FakeScalar:
    """Provide a scalar with a tolist method."""

    def __init__(self, value: float) -> None:
        """Store the scalar value."""
        self.value = value

    def tolist(self) -> float:
        """Return the scalar as a plain value."""
        return self.value


class FakeVector:
    """Provide a vector with a tolist method."""

    def __init__(self, values: list[float]) -> None:
        """Store vector values."""
        self.values = values

    def tolist(self) -> list[float]:
        """Return vector values."""
        return self.values


class FakeBox:
    """Provide a fake YOLO box."""

    xyxy = [FakeVector([10.2, 20.8, 110.1, 160.9])]
    conf = [FakeScalar(0.93)]


class FakeResult:
    """Provide a fake YOLO result."""

    boxes = [FakeBox()]


class FakeYoloModel:
    """Provide a fake YOLO callable model."""

    def __call__(self, image_path: str) -> list[FakeResult]:
        """Return fake detections for an image path."""
        assert image_path.endswith("photo.jpg")
        return [FakeResult()]


class FakePaddleEngine:
    """Provide a fake PaddleOCR engine."""

    def ocr(self, image_uri: str) -> list[list[tuple[list[list[int]], tuple[str, float]]]]:
        """Return fake OCR text for an image URI."""
        assert image_uri.endswith("norm-1.jpg")
        return [[([[0, 0], [1, 0], [1, 1], [0, 1]], ("BIB 1258", 0.91))]]


def test_yolo_detector_maps_boxes_to_detections() -> None:
    """Verify YOLO-compatible results map to detection contracts."""
    detector = YoloCompatibleBibDetector(model=FakeYoloModel())

    detections = detector.detect("file://artifacts/jobs/job-1/raw/photo.jpg")

    assert detections[0].bbox == [10, 20, 110, 160]
    assert detections[0].confidence == 0.93


def test_paddle_ocr_adapter_extracts_bib_digits() -> None:
    """Verify PaddleOCR-compatible results map to OCR contracts."""
    adapter = PaddleOcrCompatibleAdapter(engine=FakePaddleEngine())

    results = adapter.recognize_uri_pairs([("norm-1", "file://artifacts/jobs/job-1/normalized/norm-1.jpg")])

    assert results[0].bibNumber == "1258"
    assert results[0].confidence == 0.91


def test_byte_image_processor_preserves_artifact_bytes_with_stage_markers() -> None:
    """Verify byte processor keeps deterministic fallback behavior."""
    processor = ByteImageProcessor()

    crop = processor.crop(b"image", [1, 2, 3, 4], "det-1")
    normalized = processor.normalize(crop, "default-v1")

    assert b"CROP:det-1" in crop
    assert b"NORMALIZED:default-v1" in normalized
