"""Detection, image processing, and OCR adapters."""

import re
import tempfile
from pathlib import Path
from typing import Any, Protocol

from rbp_contracts.ids import new_detection_id, new_ocr_result_id
from rbp_contracts.models import Detection, NormalizedImage, OCRResult


class DetectorAdapter(Protocol):
    """Define a bib detector adapter."""

    def detect(self, image_uri: str) -> list[Detection]:
        """Detect bib regions from an image URI."""


class OcrAdapter(Protocol):
    """Define an OCR adapter."""

    def recognize(self, normalized_images: list[NormalizedImage]) -> list[OCRResult]:
        """Recognize bib numbers from normalized image artifacts."""


class ImageProcessor(Protocol):
    """Define crop and normalization image operations."""

    def crop(self, image_bytes: bytes, bbox: list[int], detection_id: str) -> bytes:
        """Crop a detected bib region from source image bytes."""

    def normalize(self, image_bytes: bytes, transform_profile: str) -> bytes:
        """Normalize image bytes for OCR."""


def local_artifact_uri_to_path(uri: str) -> str:
    """Convert a local artifact URI to a filesystem path."""
    if uri.startswith("file://artifacts/"):
        return uri.removeprefix("file://")
    if uri.startswith("file://"):
        return uri.removeprefix("file://")
    return uri


class HeuristicBibDetector:
    """Provide a lightweight placeholder detector for local demos."""

    def detect(self, image_uri: str) -> list[Detection]:
        """Return deterministic candidate bib boxes for an image."""
        return [
            Detection(detectionId=new_detection_id(1), bbox=[80, 120, 260, 210], confidence=0.88),
            Detection(detectionId=new_detection_id(2), bbox=[300, 130, 470, 220], confidence=0.81),
        ]


class YoloCompatibleBibDetector:
    """Detect bib regions with a YOLO-compatible model."""

    def __init__(self, model_path: str | None = None, model: Any | None = None) -> None:
        """Initialize the YOLO model."""
        if model is None:
            if model_path is None:
                raise ValueError("model_path is required when model is not provided")
            from ultralytics import YOLO

            model = YOLO(model_path)
        self.model = model

    def detect(self, image_uri: str) -> list[Detection]:
        """Run YOLO detection and map boxes to contracts."""
        image_path = local_artifact_uri_to_path(image_uri)
        detections: list[Detection] = []
        for result in self.model(image_path):
            for index, box in enumerate(result.boxes, start=len(detections) + 1):
                bbox_values = [int(value) for value in box.xyxy[0].tolist()]
                confidence = round(float(box.conf[0].tolist()), 4)
                detections.append(
                    Detection(
                        detectionId=new_detection_id(index),
                        bbox=bbox_values,
                        confidence=confidence,
                    )
                )
        return detections


class ByteImageProcessor:
    """Provide deterministic byte-based image processing fallback."""

    def crop(self, image_bytes: bytes, bbox: list[int], detection_id: str) -> bytes:
        """Append deterministic crop metadata to bytes."""
        return image_bytes + f"\nCROP:{detection_id}:{bbox}".encode()

    def normalize(self, image_bytes: bytes, transform_profile: str) -> bytes:
        """Append deterministic normalization metadata to bytes."""
        return image_bytes + f"\nNORMALIZED:{transform_profile}".encode()


class OpenCvImageProcessor:
    """Process crop and normalization operations with OpenCV."""

    def __init__(self, cv2_module: Any | None = None, numpy_module: Any | None = None) -> None:
        """Initialize OpenCV and NumPy modules."""
        if cv2_module is None or numpy_module is None:
            import cv2 as cv2_module
            import numpy as numpy_module

        self.cv2 = cv2_module
        self.numpy = numpy_module

    def crop(self, image_bytes: bytes, bbox: list[int], detection_id: str) -> bytes:
        """Crop a detected bib region using OpenCV."""
        image = self._decode(image_bytes)
        x1, y1, x2, y2 = bbox
        crop = image[max(y1, 0) : max(y2, 0), max(x1, 0) : max(x2, 0)]
        if getattr(crop, "size", 0) == 0:
            raise ValueError(f"Empty crop for detection {detection_id}")
        return self._encode(crop)

    def normalize(self, image_bytes: bytes, transform_profile: str) -> bytes:
        """Normalize a crop for OCR using OpenCV."""
        image = self._decode(image_bytes)
        gray = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2GRAY)
        resized = self.cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=self.cv2.INTER_CUBIC)
        normalized = self.cv2.equalizeHist(resized)
        thresholded = self.cv2.threshold(normalized, 0, 255, self.cv2.THRESH_BINARY + self.cv2.THRESH_OTSU)[1]
        return self._encode(thresholded)

    def _decode(self, image_bytes: bytes) -> Any:
        """Decode image bytes into an OpenCV image."""
        data = self.numpy.frombuffer(image_bytes, dtype=self.numpy.uint8)
        image = self.cv2.imdecode(data, self.cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Image bytes could not be decoded by OpenCV")
        return image

    def _encode(self, image: Any) -> bytes:
        """Encode an OpenCV image as JPEG bytes."""
        success, encoded = self.cv2.imencode(".jpg", image)
        if not success:
            raise ValueError("Image could not be encoded by OpenCV")
        return bytes(encoded)


class FakeOcrAdapter:
    """Provide deterministic OCR output for tests and demos."""

    def __init__(self, default_numbers: list[str] | None = None) -> None:
        """Initialize the fake OCR number sequence."""
        self.default_numbers = default_numbers or ["1258"]

    def recognize(self, normalized_images: list[NormalizedImage]) -> list[OCRResult]:
        """Return deterministic OCR results for normalized artifacts."""
        results: list[OCRResult] = []
        for index, image in enumerate(normalized_images, start=1):
            number = self.default_numbers[(index - 1) % len(self.default_numbers)]
            confidence = max(0.5, 0.98 - ((index - 1) * 0.06))
            results.append(
                OCRResult(
                    ocrResultId=new_ocr_result_id(index),
                    normalizedId=image.normalizedId,
                    bibNumber=number,
                    confidence=round(confidence, 2),
                )
            )
        return results


class PaddleOcrCompatibleAdapter:
    """Recognize bib numbers with a PaddleOCR-compatible engine."""

    def __init__(self, engine: Any | None = None) -> None:
        """Initialize the PaddleOCR engine."""
        if engine is None:
            from paddleocr import PaddleOCR

            engine = PaddleOCR(use_angle_cls=True, lang="en")
        self.engine = engine

    def recognize(self, normalized_images: list[NormalizedImage]) -> list[OCRResult]:
        """Recognize bib numbers from normalized image artifacts."""
        pairs = [(image.normalizedId, image.artifactUri) for image in normalized_images]
        return self.recognize_uri_pairs(pairs)

    def recognize_uri_pairs(self, normalized_images: list[tuple[str, str]]) -> list[OCRResult]:
        """Recognize bib numbers from normalized image URI pairs."""
        results: list[OCRResult] = []
        for index, (normalized_id, artifact_uri) in enumerate(normalized_images, start=1):
            best_text, confidence = self._best_ocr_result(artifact_uri)
            bib_number = self._extract_bib_number(best_text)
            if bib_number:
                results.append(
                    OCRResult(
                        ocrResultId=new_ocr_result_id(index),
                        normalizedId=normalized_id,
                        bibNumber=bib_number,
                        confidence=confidence,
                    )
                )
        return results

    def _best_ocr_result(self, artifact_uri: str) -> tuple[str, float]:
        """Return the highest-confidence OCR text for one artifact."""
        image_path = local_artifact_uri_to_path(artifact_uri)
        output = self.engine.ocr(image_path)
        best_text = ""
        best_confidence = 0.0
        for page in output or []:
            for item in page or []:
                text, confidence = item[1]
                if float(confidence) > best_confidence:
                    best_text = str(text)
                    best_confidence = float(confidence)
        return best_text, round(best_confidence, 4)

    def _extract_bib_number(self, text: str) -> str:
        """Extract the strongest bib-number candidate from OCR text."""
        candidates = re.findall(r"\d{2,6}", text)
        return max(candidates, key=len) if candidates else ""


class LocalFileOcrAdapter(PaddleOcrCompatibleAdapter):
    """Run a URI-based OCR engine against temporary local files."""

    def recognize_from_bytes(self, normalized_id: str, image_bytes: bytes) -> list[OCRResult]:
        """Recognize a bib number from image bytes through a temporary file."""
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            image_file.write(image_bytes)
            image_file.flush()
            return self.recognize_uri_pairs([(normalized_id, str(Path(image_file.name)))])
