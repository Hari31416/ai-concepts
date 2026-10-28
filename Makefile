FILE ?=
SCENE ?=
QUALITY ?= h
OUTPUT_DIR ?= $(patsubst %/,%,$(dir $(FILE)))
MEDIA ?= $(OUTPUT_DIR)/media
VERBOSE ?= 0
OPEN ?= 0
MANIM = uv run --locked manim
FLAGS = --media_dir "$(MEDIA)"
ifeq ($(VERBOSE),1)
FLAGS += --verbosity DEBUG
endif
ifeq ($(OPEN),1)
FLAGS += --preview
endif

.PHONY: help setup hooks pre-commit check format preview render frame list clean require-file require-scene

help:
	@echo 'setup       Install locked dependencies and Git hooks'
	@echo 'preview     Render 480p video; FILE and SCENE required'
	@echo 'render      Save OUTPUT_DIR/SCENE.mp4; QUALITY=h by default'
	@echo 'frame       Save the last frame as OUTPUT_DIR/SCENE.png'
	@echo 'list        List scene classes in FILE'
	@echo 'clean       Remove only this scene partial movie caches; FILE and SCENE required'
	@echo 'Options: OUTPUT_DIR defaults to the source folder; MEDIA overrides the cache folder'
	@echo '         VERBOSE=1 enables debug logs; OPEN=1 opens rendered output'
	@echo '         QUALITY=l/m/h/p/k selects 480p/720p/1080p/1440p/2160p'
	@echo 'check       Run formatting and repository checks'
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

check: pre-commit
	uv run --locked python -m unittest discover -s tests -v

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
	@mkdir -p "$(OUTPUT_DIR)"
	$(MANIM) -q$(QUALITY) $(FLAGS) -o "$$(cd "$(OUTPUT_DIR)" && pwd)/$(SCENE).mp4" "$(FILE)" "$(SCENE)"

frame: require-scene
	@mkdir -p "$(OUTPUT_DIR)"
	$(MANIM) -q$(QUALITY) -s $(FLAGS) -o "$$(cd "$(OUTPUT_DIR)" && pwd)/$(SCENE).png" "$(FILE)" "$(SCENE)"

clean: require-scene
	uv run --locked python scripts/clean_animation.py "$(FILE)" "$(SCENE)" --media "$(MEDIA)"
