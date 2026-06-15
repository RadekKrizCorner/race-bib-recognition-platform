# Private Dataset and CVAT Labeling

This guide describes the private dataset workflow for bib detection model training. Private photos, labels, exports, and model weights must stay outside Git.

## Local Paths

Set these local variables before running private dataset commands:

```bash
export RBP_PROJECT_ROOT=/path/to/RaicingBidPhotos
export RBP_PRIVATE_DATA_ROOT=$RBP_PROJECT_ROOT/data/private
export CVAT_HOME=/path/to/local/cvat
```

The working dataset lives under:

```text
data/private/race-bib-v1/
  raw/
  images/train/
  images/val/
  images/test/
  labels/train/
  labels/val/
  labels/test/
  metadata/
  race-bib-v1.yaml
```

CVAT import and export files live under:

```text
data/private/cvat/
  import/
  export/
  backup/
```

These paths are ignored by Git through `data/`.

## Labeling Target

Use one detection class:

```text
bib
```

Rules:

- Draw one tight rectangle around every visible race bib.
- Label every visible bib in each photo.
- Do not label runners, faces, shirts, digits, logos, or background objects.
- If a bib is partly hidden but still recognizable as a bib region, label the visible bib area tightly.
- If the bib is too blurred or too occluded to define a region, skip it.

## CVAT Local Docker

CVAT is installed outside this repository at:

```text
$CVAT_HOME
```

The local override maps CVAT to port `9002` because port `8080` is used by another local service:

```yaml
services:
  traefik:
    ports: !override
      - "9002:8080"
      - "9003:8090"
```

Start CVAT:

```bash
cd $CVAT_HOME
docker compose up -d
```

Open:

```text
http://localhost:9002
```

## Create a CVAT Task

Use the prepared import archive:

```text
data/private/cvat/import/race-bib-v1-raw.zip
```

Task settings:

- Task name: `race-bib-v1`
- Label: `bib`
- Shape type: rectangle
- Source files: upload the prepared ZIP archive

After labeling, export annotations as YOLO format.

## Import a CVAT YOLO Export

Place the downloaded CVAT export ZIP in:

```text
data/private/cvat/export/
```

For the current dataset, the export was processed from:

```text
$HOME/Downloads/bibrunners.zip
```

The extracted YOLO labels are stored at:

```text
data/private/cvat/export/bibrunners-yolo/obj_train_data/
```

The current private split is:

- Train: `5` images, `5` labels, `9` boxes
- Validation: `1` image, `1` label, `2` boxes
- Test: `1` image, `1` label, `1` box

This split is useful for validating the workflow. It is too small for a reliable production detector.

## YOLO Dataset YAML

Use this config for Ultralytics training:

```yaml
path: $RBP_PRIVATE_DATA_ROOT/race-bib-v1
train: images/train
val: images/val
test: images/test

names:
  0: bib
```

## Train a First Detector

Install computer vision dependencies:

```bash
uv sync --extra cv
```

Train a smoke-test detector:

```bash
uv run yolo detect train \
  model=yolo11n.pt \
  data=$RBP_PRIVATE_DATA_ROOT/race-bib-v1/race-bib-v1.yaml \
  epochs=100 \
  imgsz=1280 \
  batch=2 \
  project=$RBP_PRIVATE_DATA_ROOT/runs/yolo \
  name=bib-yolo-v1
```

Expected output model:

```text
data/private/runs/yolo/bib-yolo-v1/weights/best.pt
```

Configure the application to use it:

```bash
RBP_DETECTOR_ADAPTER=yolo
RBP_YOLO_MODEL_PATH=$RBP_PRIVATE_DATA_ROOT/runs/yolo/bib-yolo-v1/weights/best.pt
RBP_IMAGE_PROCESSOR=opencv
RBP_OCR_ADAPTER=paddle
```

## Current Local Detector

The current selected private detector for local integration work is:

```text
$RBP_PRIVATE_DATA_ROOT/runs/yolo/bib-yolo-v3-mps-2/weights/best.pt
```

Use it when running bib detection before crop generation and OCR evaluation:

```bash
RBP_DETECTOR_ADAPTER=yolo
RBP_YOLO_MODEL_PATH=$RBP_PRIVATE_DATA_ROOT/runs/yolo/bib-yolo-v3-mps-2/weights/best.pt
RBP_IMAGE_PROCESSOR=opencv
RBP_OCR_ADAPTER=paddle
```

The `bib-yolo-v3-mps-2` detector was trained from the private active-learning workflow and is considered good enough to detect bib regions for number-recognition experiments. Keep the artifact private and local unless it is published through a dedicated artifact store or model registry.

## Model Artifact Versioning Policy

Do not commit trained model weights to Git.

Model artifacts are generated binary files and can be large. They also come from private race photos, so they may indirectly encode private dataset information. Keep them under ignored local paths such as:

```text
data/private/runs/yolo/
models/
```

The repository already ignores `data/`, `models/`, and common model weight formats such as `*.pt`, `*.onnx`, and `*.engine`.

If a model must be shared between environments, store it outside Git and document:

- model name and version
- training dataset version
- evaluation metrics
- checksum
- artifact storage URL or registry reference

## GitHub Release Model Asset Workflow

Use GitHub Release assets for sharing private model binaries without committing weights to Git.

The current registry entry is:

```text
models/registry/bib-yolo-v3-mps-2.yaml
```

The registry entry stores the selected release tag, asset names, local source path, model metrics, file size, and SHA-256 checksum. It does not store model bytes.

The selected release tag is:

```text
model-bib-yolo-v3-mps-2
```

Prepare the release asset and checksum:

```bash
cd $RBP_PROJECT_ROOT

MODEL_PATH=$RBP_PRIVATE_DATA_ROOT/runs/yolo/bib-yolo-v3-mps-2/weights/best.pt
ASSET_DIR=/tmp/rbp-model-release-bib-yolo-v3-mps-2
ASSET_NAME=bib-yolo-v3-mps-2-best.pt

rm -rf "$ASSET_DIR"
mkdir -p "$ASSET_DIR"
cp "$MODEL_PATH" "$ASSET_DIR/$ASSET_NAME"
shasum -a 256 "$ASSET_DIR/$ASSET_NAME" > "$ASSET_DIR/$ASSET_NAME.sha256"
cat "$ASSET_DIR/$ASSET_NAME.sha256"
```

The checksum must match the registry value:

```text
e47ad22e64278286e140afb1ddee9290d628c144b5afc8b9d33de40e57fa49b6
```

Create the GitHub Release and upload both files:

```bash
REPO=OWNER/REPOSITORY
RELEASE_TAG=model-bib-yolo-v3-mps-2

gh auth login
gh release create "$RELEASE_TAG" \
  "$ASSET_DIR/$ASSET_NAME" \
  "$ASSET_DIR/$ASSET_NAME.sha256" \
  --repo "$REPO" \
  --title "Model bib-yolo-v3-mps-2" \
  --notes "YOLO bib detector selected for local OCR integration. See models/registry/bib-yolo-v3-mps-2.yaml for metrics and checksum."
```

If the release already exists and the asset must be replaced, upload with `--clobber`:

```bash
gh release upload "$RELEASE_TAG" \
  "$ASSET_DIR/$ASSET_NAME" \
  "$ASSET_DIR/$ASSET_NAME.sha256" \
  --repo "$REPO" \
  --clobber
```

Download and verify the model on another machine:

```bash
REPO=OWNER/REPOSITORY
RELEASE_TAG=model-bib-yolo-v3-mps-2
MODEL_DIR=$RBP_PROJECT_ROOT/models/downloaded/bib-yolo-v3-mps-2

mkdir -p "$MODEL_DIR"
gh release download "$RELEASE_TAG" \
  --repo "$REPO" \
  --pattern "bib-yolo-v3-mps-2-best.pt*" \
  --dir "$MODEL_DIR"

cd "$MODEL_DIR"
shasum -a 256 -c bib-yolo-v3-mps-2-best.pt.sha256
```

Configure the detector with the downloaded file:

```bash
RBP_DETECTOR_ADAPTER=yolo
RBP_YOLO_MODEL_PATH=$RBP_PROJECT_ROOT/models/downloaded/bib-yolo-v3-mps-2/bib-yolo-v3-mps-2-best.pt
```

## Automatic Annotation Options

CVAT can help with automatic annotation, but the default local Docker startup does not automatically know how to detect race bibs.

Practical options:

1. Train the first YOLO bib detector manually on a small labeled seed set.
2. Run that detector on new private photos to generate YOLO label files.
3. Import the generated labels into CVAT.
4. Review and correct predictions manually.
5. Retrain with the corrected dataset.

This active-learning loop is usually faster and more reliable than fully manual labeling once the first detector exists.

CVAT also supports serverless automatic annotation functions. For local self-hosted use, that means running the CVAT serverless setup and deploying a model function.

Official CVAT references:

- [Automatic annotation overview](https://docs.cvat.ai/docs/annotation/auto-annotation/automatic-annotation/)
- [Self-hosted automatic annotation installation](https://docs.cvat.ai/docs/administration/community/advanced/installation_automatic_annotation/)
- [Serverless function tutorial](https://docs.cvat.ai/docs/guides/serverless-tutorial/)

To start CVAT with serverless support and keep the local `9002` port override:

```bash
cd $CVAT_HOME
docker compose \
  -f docker-compose.yml \
  -f docker-compose.override.yml \
  -f components/serverless/docker-compose.serverless.yml \
  up -d
```

To stop that stack:

```bash
cd $CVAT_HOME
docker compose \
  -f docker-compose.yml \
  -f docker-compose.override.yml \
  -f components/serverless/docker-compose.serverless.yml \
  down
```

Use serverless auto-annotation after the first bib detector exists, not before. Generic pretrained detectors usually do not include a dedicated race bib class, so they are unlikely to find race bibs reliably.

Preferred local automation path:

1. Train `bib-yolo-v1` from the manually labeled seed set.
2. Run `bib-yolo-v1` on the next batch of private photos.
3. Save predictions as YOLO `.txt` labels.
4. Import images and predicted labels into CVAT.
5. Correct missed, oversized, or false-positive boxes.
6. Retrain as `bib-yolo-v2`.

## Import YOLO Predictions into an Existing CVAT Task

When importing annotations into an existing CVAT task, use an annotations-only ZIP. Do not include image files in that ZIP.

Correct archive shape:

```text
obj.data
obj.names
train.txt
obj_train_data/
  photo-1.txt
  photo-2.txt
```

Incorrect archive shape for annotation upload:

```text
obj_train_data/
  photo-1.jpg
  photo-1.txt
```

Use a ZIP that contains photos only when creating a new CVAT task. Use a metadata-only ZIP when uploading annotations to a task that already has frames.

CVAT matches YOLO label file names to task frame names. For example, this label:

```text
obj_train_data/vokolo trail (226).txt
```

must match an existing task frame:

```text
vokolo trail (226).jpg
```

If the task contains different frame names, CVAT raises an error similar to:

```text
Could not match item id with any task frame
```

## Remove YOLO Confidence Before CVAT Import

Ultralytics predictions created with `save_conf=True` write six YOLO columns:

```text
class x_center y_center width height confidence
```

CVAT YOLO import expects five columns:

```text
class x_center y_center width height
```

If the confidence column is present, CVAT can fail through Datumaro with:

```text
Unexpected field count 6 in the bbox description. Expected 5 fields (label, xc, yc, w, h).
datumaro.components.contexts.importer._ImportFail
```

Preferred prediction command for CVAT import:

```bash
uv run yolo detect predict \
  model=$RBP_PRIVATE_DATA_ROOT/runs/yolo/bib-yolo-v1/weights/best.pt \
  source=$RBP_PRIVATE_DATA_ROOT/race-bib-v2/raw \
  imgsz=1280 \
  conf=0.20 \
  save=True \
  save_txt=True \
  project=$RBP_PRIVATE_DATA_ROOT/race-bib-v2/auto-labels \
  name=yolo-v1
```

If predictions were already generated with `save_conf=True`, strip the sixth column before creating the CVAT annotations ZIP.

For the current `race-bib-v2` batch, the corrected annotations-only ZIP is:

```text
data/private/race-bib-v2/cvat/import/yolo-v1-annotations-only-cvat.zip
```

Expected properties:

- No images in the ZIP.
- One `.txt` file per task frame.
- Empty `.txt` files are allowed for photos with no detected bib.
- Every non-empty annotation row has exactly five fields.

## Privacy Rules

- Do not commit private photos.
- Do not commit CVAT exports.
- Do not commit YOLO labels if they identify private photos.
- Do not commit model weights.
- Keep Kafka events metadata-only.
- Keep public docs in English and avoid exposing private race details.
