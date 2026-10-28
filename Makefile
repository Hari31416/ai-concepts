FILE ?=
SCENE ?=
QUALITY ?= h
OUTPUT_DIR ?= $(patsubst %/,%,$(dir $(FILE)))
VIDEO_DIR ?= $(OUTPUT_DIR)/video
IMAGES_DIR ?= $(OUTPUT_DIR)/images
MEDIA ?= $(OUTPUT_DIR)/media
VERBOSE ?= 0
OPEN ?= 0
MANIM = uv run --locked python -m manim
FLAGS = --media_dir "$(MEDIA)"
ifeq ($(VERBOSE),1)
FLAGS += --verbosity DEBUG
endif
ifeq ($(OPEN),1)
FLAGS += --preview
endif

.PHONY: help setup hooks pre-commit check test typecheck format preview render frame list clean require-file require-scene

help:
	@echo 'setup       Install locked dependencies and Git hooks'
	@echo 'preview     Render 480p video; FILE and SCENE required'
	@echo 'render      Save VIDEO_DIR/SCENE.mp4; QUALITY=h by default'
	@echo 'frame       Save the last frame as IMAGES_DIR/SCENE.png'
	@echo 'list        List scene classes in FILE'
	@echo 'clean       Remove only this scene partial movie caches; FILE and SCENE required'
	@echo 'Options: OUTPUT_DIR defaults to the source folder; VIDEO_DIR defaults to OUTPUT_DIR/video'
	@echo '         IMAGES_DIR defaults to OUTPUT_DIR/images; MEDIA overrides the cache folder'
	@echo '         VERBOSE=1 enables debug logs; OPEN=1 opens rendered output'
	@echo '         QUALITY=l/m/h/p/k selects 480p/720p/1080p/1440p/2160p'
	@echo 'check       Run pre-commit, type checks, and tests'
	@echo 'test        Run pytest test suite'
	@echo 'typecheck   Run mypy static type analysis'
	@echo 'format      Format project Python files'
	@echo 'hooks       Install Git hooks'
	@echo 'pre-commit  Run hooks on all tracked files'
	@echo 'Example: make preview FILE=topics/2026/10/attention/animation.py SCENE=Attention'

setup:
	uv sync --locked
	$(MAKE) hooks

hooks:
	uv run --locked pre-commit install

pre-commit:
	uv run --locked pre-commit run --all-files

test:
	uv run --locked pytest

typecheck:
	uv run --locked mypy scripts shared tests

check: pre-commit typecheck test

format:
	uv run --locked black .

require-file:
	@test -n "$(FILE)" && test -f "$(FILE)" || (echo 'Set FILE to an existing Python scene file.'; exit 1)

require-scene: require-file
	@test -n "$(SCENE)" || (echo 'Set SCENE to a class name. Use make list FILE=... to see available scenes.'; exit 1)

list: require-file
	@uv run --locked python -c 'import sys; from pathlib import Path; from manim.utils.module_ops import get_module, get_scene_classes_from_module; print("\n".join(scene.__name__ for scene in get_scene_classes_from_module(get_module(Path(sys.argv[1])))))' "$(FILE)"

preview: require-scene
	$(MANIM) -ql $(FLAGS) "$(FILE)" "$(SCENE)"

render: require-scene
	@mkdir -p "$(VIDEO_DIR)"
	$(MANIM) -q$(QUALITY) $(FLAGS) -o "$$(cd "$(VIDEO_DIR)" && pwd)/$(SCENE).mp4" "$(FILE)" "$(SCENE)"

frame: require-scene
	@mkdir -p "$(IMAGES_DIR)"
	$(MANIM) -q$(QUALITY) -s $(FLAGS) -o "$$(cd "$(IMAGES_DIR)" && pwd)/$(SCENE).png" "$(FILE)" "$(SCENE)"

clean: require-scene
	uv run --locked python scripts/clean_animation.py "$(FILE)" "$(SCENE)" --media "$(MEDIA)"
